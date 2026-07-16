"""Immutable storage and integrity checks for source shelf generations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path

from brain.v5.markdown import write_text_atomic
from brain.v5.source_shelf_models import (
    SOURCE_SHELF_EXTRACTOR_VERSION,
    SOURCE_SHELF_READER_VERSION,
    SOURCE_SHELF_SCHEMA_VERSION,
    SourcePassage,
    SourceShelf,
    SourceShelfIntegrityError,
    SourceShelfIssue,
    SourceShelfLocationPin,
    SourceShelfManifest,
    SourceShelfSourcePin,
)


def shelf_generation_basis(
    *,
    topic_id: str,
    requested_source_asset_refs,
    source_pins,
    curation_rationale: str,
    reader_version: str,
    extractor_version: str,
    max_passage_chars: int,
    incomplete_coverage: bool,
    passages_hash: str,
    issues_hash: str,
) -> dict:
    return {
        "schema_version": SOURCE_SHELF_SCHEMA_VERSION,
        "topic_id": topic_id,
        "requested_source_asset_refs": list(requested_source_asset_refs),
        "source_pins": [asdict(pin) for pin in source_pins],
        "curation_rationale": curation_rationale,
        "reader_version": reader_version,
        "extractor_version": extractor_version,
        "max_passage_chars": max_passage_chars,
        "incomplete_coverage": incomplete_coverage,
        "passages_hash": passages_hash,
        "issues_hash": issues_hash,
    }


def hash_json(value) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def publish_source_shelf(ws, shelf: SourceShelf) -> None:
    root = source_shelf_root(ws)
    generations = root / "generations"
    generations.mkdir(parents=True, exist_ok=True)
    target = generations / shelf.manifest.generation
    if not target.exists():
        staging = Path(tempfile.mkdtemp(prefix=".building-", dir=generations))
        try:
            _write_shelf_files(staging, shelf)
            try:
                os.rename(staging, target)
            except FileExistsError:
                pass
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    if not target.exists():
        raise SourceShelfIntegrityError("source shelf generation publish failed")
    existing = load_source_shelf_generation(ws, shelf.manifest.generation)
    if existing != shelf:
        raise SourceShelfIntegrityError("immutable source shelf generation collision")


def load_source_shelf_generation(ws, generation: str) -> SourceShelf:
    if not _is_digest(generation):
        raise SourceShelfIntegrityError("generation must be a lowercase SHA-256 digest")
    generation_dir = source_shelf_root(ws) / "generations" / generation
    manifest_data = _load_json_object(generation_dir / "manifest.json")
    manifest = _manifest_from_dict(manifest_data)
    _validate_manifest_contract(manifest)
    passage_rows = _load_json_list(generation_dir / manifest.passage_file)
    issue_rows = _load_json_list(generation_dir / manifest.issues_file)
    passages_hash = hash_json(passage_rows)
    issues_hash = hash_json(issue_rows)
    if passages_hash != manifest.passages_hash or issues_hash != manifest.issues_hash:
        raise SourceShelfIntegrityError("source shelf component hash mismatch")
    passages = tuple(_passage_from_dict(row) for row in passage_rows)
    try:
        issues = tuple(_issue_from_dict(row) for row in issue_rows)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf issue is malformed: {exc}") from exc
    if manifest.passage_count != len(passages) or manifest.issue_count != len(issues):
        raise SourceShelfIntegrityError("source shelf component count mismatch")
    _validate_shelf_semantics(manifest, passages, issues)
    expected_generation = hash_json(_basis_from_manifest(manifest))
    if manifest.generation != generation or expected_generation != generation:
        raise SourceShelfIntegrityError("source shelf generation hash mismatch")
    return SourceShelf(manifest=manifest, passages=passages, issues=issues)


def source_shelf_root(ws) -> Path:
    return ws.root / "indexes" / "knowledge" / "source_shelf"


def _basis_from_manifest(manifest):
    return shelf_generation_basis(
        topic_id=manifest.topic_id,
        requested_source_asset_refs=manifest.requested_source_asset_refs,
        source_pins=manifest.source_pins,
        curation_rationale=manifest.curation_rationale,
        reader_version=manifest.reader_version,
        extractor_version=manifest.extractor_version,
        max_passage_chars=manifest.max_passage_chars,
        incomplete_coverage=manifest.incomplete_coverage,
        passages_hash=manifest.passages_hash,
        issues_hash=manifest.issues_hash,
    )


def _validate_manifest_contract(manifest) -> None:
    if (
        isinstance(manifest.schema_version, bool)
        or not isinstance(manifest.schema_version, int)
        or manifest.schema_version != SOURCE_SHELF_SCHEMA_VERSION
    ):
        raise SourceShelfIntegrityError("unsupported source shelf schema version")
    if not _is_digest(manifest.generation):
        raise SourceShelfIntegrityError("source shelf manifest generation is invalid")
    if not _non_empty_string(manifest.topic_id):
        raise SourceShelfIntegrityError("source shelf manifest topic_id is invalid")
    if (
        not isinstance(manifest.requested_source_asset_refs, tuple)
        or any(not _non_empty_string(item) for item in manifest.requested_source_asset_refs)
        or len(set(manifest.requested_source_asset_refs))
        != len(manifest.requested_source_asset_refs)
    ):
        raise SourceShelfIntegrityError("source shelf requested source refs are invalid")
    if not _non_empty_string(manifest.curation_rationale):
        raise SourceShelfIntegrityError("source shelf curation rationale is invalid")
    if (
        manifest.reader_version != SOURCE_SHELF_READER_VERSION
        or manifest.extractor_version != SOURCE_SHELF_EXTRACTOR_VERSION
    ):
        raise SourceShelfIntegrityError("source shelf reader provenance is invalid")
    if not _bounded_int(manifest.max_passage_chars, lower=256, upper=20000):
        raise SourceShelfIntegrityError("source shelf max_passage_chars is invalid")
    if not _bounded_int(manifest.passage_count, lower=0):
        raise SourceShelfIntegrityError("source shelf passage_count is invalid")
    if not _bounded_int(manifest.issue_count, lower=0):
        raise SourceShelfIntegrityError("source shelf issue_count is invalid")
    if not isinstance(manifest.incomplete_coverage, bool):
        raise SourceShelfIntegrityError("source shelf incomplete_coverage is invalid")
    if not _is_digest(manifest.passages_hash) or not _is_digest(manifest.issues_hash):
        raise SourceShelfIntegrityError("source shelf component digest is invalid")
    if manifest.passage_file != "passages.json" or manifest.issues_file != "issues.json":
        raise SourceShelfIntegrityError("source shelf component path is invalid")
    if manifest.orientation_only is not True or manifest.can_update_claim_trust is not False:
        raise SourceShelfIntegrityError("source shelf manifest violates trust boundary")
    if not isinstance(manifest.source_pins, tuple):
        raise SourceShelfIntegrityError("source shelf source pins are invalid")
    for pin in manifest.source_pins:
        _validate_source_pin(pin, manifest.topic_id)


def _validate_source_pin(pin, manifest_topic_id):
    if not isinstance(pin, SourceShelfSourcePin):
        raise SourceShelfIntegrityError("source shelf source pin is malformed")
    if not _typed_ref(pin.source_asset_ref, "source_asset"):
        raise SourceShelfIntegrityError("source shelf source pin ref is invalid")
    if not _non_empty_string(pin.topic_id) or pin.topic_id != manifest_topic_id:
        raise SourceShelfIntegrityError("source shelf source pin topic differs from manifest topic")
    if not _is_digest(pin.record_content_hash) or not _is_digest(pin.content_hash):
        raise SourceShelfIntegrityError("source shelf source pin hash is invalid")
    if pin.record_revision is not None and not _bounded_int(pin.record_revision, lower=1):
        raise SourceShelfIntegrityError("source shelf source pin revision is invalid")
    for value in (
        pin.canonical_uri,
        pin.local_uri,
        pin.acquired_at,
        pin.access_disposition,
        pin.storage_permission,
    ):
        if not _non_empty_string(value):
            raise SourceShelfIntegrityError("source shelf source pin scalar is invalid")
    if not isinstance(pin.acquisition_decision_ref, dict) or not isinstance(
        pin.acquisition_receipt_ref, dict
    ):
        raise SourceShelfIntegrityError("source shelf acquisition pin is invalid")
    if not isinstance(pin.source_location_pins, tuple):
        raise SourceShelfIntegrityError("source shelf location pins are invalid")
    for location in pin.source_location_pins:
        _validate_location_pin(
            location,
            topic_id=pin.topic_id,
            source_asset_ref=pin.source_asset_ref,
        )


def _validate_location_pin(location, *, topic_id, source_asset_ref):
    if not isinstance(location, SourceShelfLocationPin):
        raise SourceShelfIntegrityError("source shelf location pin is malformed")
    if not _typed_ref(location.record_ref, "reference_location") or not _is_digest(
        location.content_hash
    ):
        raise SourceShelfIntegrityError("source shelf location pin identity is invalid")
    if location.revision is not None and not _bounded_int(location.revision, lower=1):
        raise SourceShelfIntegrityError("source shelf location pin revision is invalid")
    if (
        location.topic_id != topic_id
        or location.source_asset_ref != source_asset_ref
    ):
        raise SourceShelfIntegrityError("source shelf location pin topic or source differs")


def _write_shelf_files(directory: Path, shelf: SourceShelf) -> None:
    write_text_atomic(
        directory / shelf.manifest.passage_file,
        json.dumps([asdict(item) for item in shelf.passages], ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    write_text_atomic(
        directory / shelf.manifest.issues_file,
        json.dumps([asdict(item) for item in shelf.issues], ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    write_text_atomic(
        directory / "manifest.json",
        json.dumps(asdict(shelf.manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


def _manifest_from_dict(data):
    try:
        values = dict(data)
        values["requested_source_asset_refs"] = _json_array(
            values.get("requested_source_asset_refs"),
            "requested_source_asset_refs",
        )
        values["source_pins"] = tuple(
            _source_pin_from_dict(row)
            for row in _json_array(values.get("source_pins"), "source_pins")
        )
        return SourceShelfManifest(**values)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf manifest is malformed: {exc}") from exc


def _passage_from_dict(row):
    try:
        values = dict(row)
        for field in ("anchor_kinds", "anchor_labels", "source_location_refs"):
            values[field] = _json_array(values.get(field), field)
        return SourcePassage(**values)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf passage is malformed: {exc}") from exc


def _source_pin_from_dict(row):
    values = dict(row)
    values["source_location_pins"] = tuple(
        SourceShelfLocationPin(**item)
        for item in _json_array(values.get("source_location_pins"), "source_location_pins")
    )
    return SourceShelfSourcePin(**values)


def _issue_from_dict(row):
    values = dict(row)
    values["source_location_pins"] = tuple(
        SourceShelfLocationPin(**item)
        for item in _json_array(values.get("source_location_pins"), "source_location_pins")
    )
    return SourceShelfIssue(**values)


def _json_array(value, field):
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a JSON array")
    return tuple(value)


def source_passage_id(
    *,
    source_asset_ref,
    source_content_hash,
    page_start,
    page_end,
    section,
    ordinal,
    text_hash,
):
    identity = hash_json(
        {
            "source_asset_ref": source_asset_ref,
            "source_content_hash": source_content_hash,
            "page_start": page_start,
            "page_end": page_end,
            "section": section,
            "ordinal": ordinal,
            "text_hash": text_hash,
        }
    )
    return f"source-passage:{identity}"


def _validate_shelf_semantics(manifest, passages, issues):
    pins = {pin.source_asset_ref: pin for pin in manifest.source_pins}
    if len(pins) != len(manifest.source_pins):
        raise SourceShelfIntegrityError("source shelf contains duplicate source pins")
    if manifest.incomplete_coverage is not bool(issues):
        raise SourceShelfIntegrityError("source shelf coverage flag disagrees with issues")
    for issue in issues:
        if not isinstance(issue, SourceShelfIssue) or any(
            not isinstance(value, str)
            for value in (issue.code, issue.source_asset_ref, issue.detail)
        ) or not issue.code.strip() or not issue.detail.strip():
            raise SourceShelfIntegrityError("source shelf issue is malformed")
        if not isinstance(issue.source_location_pins, tuple):
            raise SourceShelfIntegrityError("source shelf issue location pins are malformed")
        if issue.source_location_pins and not issue.source_asset_ref:
            raise SourceShelfIntegrityError("source shelf generic issue cannot carry location pins")
        for location in issue.source_location_pins:
            _validate_location_pin(
                location,
                topic_id=manifest.topic_id,
                source_asset_ref=issue.source_asset_ref,
            )
    for passage in passages:
        _validate_passage_contract(passage)
    requested_refs = set(manifest.requested_source_asset_refs)
    pinned_refs = set(pins)
    passage_refs = {passage.source_asset_ref for passage in passages}
    issue_refs = {issue.source_asset_ref for issue in issues if issue.source_asset_ref}
    if not pinned_refs <= requested_refs or not passage_refs <= requested_refs:
        raise SourceShelfIntegrityError("source shelf contains an unrequested source")
    if not issue_refs <= requested_refs:
        raise SourceShelfIntegrityError("source shelf issue names an unrequested source")
    if requested_refs - (pinned_refs | issue_refs):
        raise SourceShelfIntegrityError("source shelf requested source was silently omitted")
    if any(
        source_ref not in passage_refs and source_ref not in issue_refs
        for source_ref in pinned_refs
    ):
        raise SourceShelfIntegrityError("source shelf pinned source has no passage or issue")
    for passage in passages:
        pin = pins.get(passage.source_asset_ref)
        if pin is None:
            raise SourceShelfIntegrityError("source shelf passage has no manifest source pin")
        if not passage.text or len(passage.text) > manifest.max_passage_chars:
            raise SourceShelfIntegrityError("source shelf passage exceeds bounded text contract")
        actual_text_hash = hashlib.sha256(passage.text.encode("utf-8")).hexdigest()
        if passage.text_hash != actual_text_hash:
            raise SourceShelfIntegrityError("source shelf passage text_hash is invalid")
        expected_id = source_passage_id(
            source_asset_ref=passage.source_asset_ref,
            source_content_hash=passage.source_content_hash,
            page_start=passage.page_start,
            page_end=passage.page_end,
            section=passage.section,
            ordinal=passage.ordinal,
            text_hash=passage.text_hash,
        )
        expected_locations = tuple(item.record_ref for item in pin.source_location_pins)
        if passage.passage_id != expected_id:
            raise SourceShelfIntegrityError("source shelf passage_id is invalid")
        if (
            passage.source_content_hash != pin.content_hash
            or passage.canonical_uri != pin.canonical_uri
            or passage.local_uri != pin.local_uri
            or passage.source_location_refs != expected_locations
        ):
            raise SourceShelfIntegrityError("source shelf passage disagrees with source pin")
        if passage.orientation_only is not True or passage.can_update_claim_trust is not False:
            raise SourceShelfIntegrityError("source shelf passage violates trust boundary")


def _validate_passage_contract(passage):
    if not isinstance(passage, SourcePassage):
        raise SourceShelfIntegrityError("source shelf passage is malformed")
    if not _non_empty_string(passage.passage_id) or not passage.passage_id.startswith(
        "source-passage:"
    ):
        raise SourceShelfIntegrityError("source shelf passage_id is invalid")
    if not _bounded_int(passage.ordinal, lower=1):
        raise SourceShelfIntegrityError("source shelf passage ordinal is invalid")
    for value in (
        passage.source_asset_ref,
        passage.canonical_uri,
        passage.local_uri,
        passage.section,
        passage.text,
    ):
        if not isinstance(value, str):
            raise SourceShelfIntegrityError("source shelf passage scalar is invalid")
    if not passage.source_asset_ref.strip() or not passage.text:
        raise SourceShelfIntegrityError("source shelf passage scalar is invalid")
    if not _is_digest(passage.source_content_hash) or not _is_digest(passage.text_hash):
        raise SourceShelfIntegrityError("source shelf passage hash is invalid")
    for page in (passage.page_start, passage.page_end):
        if page is not None and not _bounded_int(page, lower=1):
            raise SourceShelfIntegrityError("source shelf passage page is invalid")
    if (
        passage.page_start is None
        and passage.page_end is not None
        or passage.page_start is not None
        and passage.page_end is None
        or passage.page_start is not None
        and passage.page_end < passage.page_start
    ):
        raise SourceShelfIntegrityError("source shelf passage page range is invalid")
    for field in (passage.anchor_kinds, passage.anchor_labels, passage.source_location_refs):
        if not isinstance(field, tuple) or any(not isinstance(item, str) for item in field):
            raise SourceShelfIntegrityError("source shelf passage tuple field is invalid")


def _non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _typed_ref(value, family):
    prefix, separator, record_id = str(value or "").partition(":")
    return separator == ":" and prefix == family and bool(record_id.strip())


def _bounded_int(value, *, lower, upper=None):
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and value >= lower
        and (upper is None or value <= upper)
    )


def _is_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _load_json_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceShelfIntegrityError(f"cannot load source shelf manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceShelfIntegrityError("source shelf manifest must be an object")
    return value


def _load_json_list(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceShelfIntegrityError(f"cannot load source shelf component: {exc}") from exc
    if not isinstance(value, list):
        raise SourceShelfIntegrityError("source shelf component must be a list")
    return value
