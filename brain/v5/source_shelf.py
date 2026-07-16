"""Hash-pinned, disposable source shelf for bounded physics retrieval."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Mapping
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.source_acquisition import (
    SourceAcquisitionResolutionError,
    resolve_source_acquisition_for_source_asset,
)
from brain.v5.source_shelf_extraction import (
    SourceShelfExtractionError,
    extract_source_passages,
)
from brain.v5.source_shelf_models import (
    SOURCE_SHELF_EXTRACTOR_VERSION,
    SOURCE_SHELF_READER_VERSION,
    SOURCE_SHELF_SCHEMA_VERSION,
    SourcePassage,
    SourceShelf,
    SourceShelfBuildReport,
    SourceShelfBuildRequest,
    SourceShelfIntegrityError,
    SourceShelfIssue,
    SourceShelfLocationPin,
    SourceShelfManifest,
    SourceShelfSourcePin,
    SourceShelfStaleError,
    validate_source_shelf_build_request,
)
from brain.v5.source_shelf_storage import (
    hash_json as _hash_json,
    load_source_shelf_generation,
    publish_source_shelf,
    shelf_generation_basis,
    source_passage_id,
)


_RESTRICTED_ACCESS = {
    "forbidden",
    "license_restricted",
    "not_acquired",
    "restricted",
}
_RESTRICTED_STORAGE = {"denied", "forbidden", "metadata_only", "not_allowed", "not_requested"}


@dataclass(frozen=True)
class _ResolvedSource:
    pin: SourceShelfSourcePin
    source_bytes: bytes
    source_suffix: str


def build_source_shelf(
    ws: WorkspacePaths,
    request: SourceShelfBuildRequest,
) -> SourceShelfBuildReport:
    """Build one immutable derived generation from exact acquired source bytes."""

    validate_source_shelf_build_request(request)
    ws.ensure_layout()
    repository = RecordRepository(ws, actor=_reader_actor())
    requested_refs, inventory_issues = _requested_refs(repository, request)
    locations, location_issues = _reference_locations(repository, request.topic_id)
    passages: list[SourcePassage] = []
    issues = [*inventory_issues, *location_issues]
    source_pins: list[SourceShelfSourcePin] = []
    checked_count = 0

    for source_ref in requested_refs:
        checked_count += 1
        location_pins, pin_issues = _location_pins(
            ws,
            locations=locations,
            topic_id=request.topic_id,
            source_ref=source_ref,
        )
        issues.extend(pin_issues)
        result = repository.read(source_ref)
        if result.status != "found" or not isinstance(result.record, SourceAssetRecord):
            issues.append(
                replace(
                    _read_issue(source_ref, result.status),
                    source_location_pins=location_pins,
                )
            )
            continue
        asset = result.record
        if asset.topic_id != request.topic_id:
            issues.append(
                _issue(
                    "source_topic_mismatch",
                    source_ref,
                    "source belongs to another topic",
                    source_location_pins=location_pins,
                )
            )
            continue
        resolved = _resolve_source(ws, asset, source_ref)
        if isinstance(resolved, SourceShelfIssue):
            issues.append(replace(resolved, source_location_pins=location_pins))
            continue
        pin = replace(resolved.pin, source_location_pins=location_pins)
        source_pins.append(pin)
        location_refs = tuple(item.record_ref for item in location_pins)
        if not location_refs:
            issues.append(
                _issue(
                    "missing_source_location",
                    source_ref,
                    "source has no exact ReferenceLocationRecord",
                )
            )
        try:
            extracted = extract_source_passages(
                resolved.source_bytes,
                source_suffix=resolved.source_suffix,
                max_passage_chars=request.max_passage_chars,
            )
        except SourceShelfExtractionError as exc:
            issues.append(_issue(exc.code, source_ref, exc.detail))
            continue
        for ordinal, item in enumerate(extracted, start=1):
            passages.append(
                _source_passage(
                    source_ref=source_ref,
                    pin=pin,
                    location_refs=location_refs,
                    ordinal=ordinal,
                    extracted=item,
                )
            )

    passages.sort(key=lambda passage: passage.passage_id)
    issues = _unique_issues(issues)
    source_pins.sort(key=lambda pin: pin.source_asset_ref)
    passage_rows = [asdict(passage) for passage in passages]
    issue_rows = [asdict(issue) for issue in issues]
    passages_hash = _hash_json(passage_rows)
    issues_hash = _hash_json(issue_rows)
    manifest_basis = shelf_generation_basis(
        topic_id=request.topic_id,
        requested_source_asset_refs=requested_refs,
        source_pins=tuple(source_pins),
        curation_rationale=request.curation_rationale.strip(),
        reader_version=SOURCE_SHELF_READER_VERSION,
        extractor_version=SOURCE_SHELF_EXTRACTOR_VERSION,
        max_passage_chars=request.max_passage_chars,
        incomplete_coverage=bool(issues),
        passages_hash=passages_hash,
        issues_hash=issues_hash,
    )
    generation = _hash_json(manifest_basis)
    manifest = SourceShelfManifest(
        schema_version=SOURCE_SHELF_SCHEMA_VERSION,
        generation=generation,
        topic_id=request.topic_id,
        requested_source_asset_refs=requested_refs,
        source_pins=tuple(source_pins),
        curation_rationale=request.curation_rationale.strip(),
        reader_version=SOURCE_SHELF_READER_VERSION,
        extractor_version=SOURCE_SHELF_EXTRACTOR_VERSION,
        max_passage_chars=request.max_passage_chars,
        passage_count=len(passages),
        issue_count=len(issues),
        incomplete_coverage=bool(issues),
        passages_hash=passages_hash,
        issues_hash=issues_hash,
    )
    shelf = SourceShelf(manifest=manifest, passages=tuple(passages), issues=tuple(issues))
    _require_current_sources(ws, shelf)
    publish_source_shelf(ws, shelf)
    loaded = load_source_shelf(ws, generation)
    return SourceShelfBuildReport(
        manifest=loaded.manifest,
        shelf=loaded,
        checked_count=checked_count,
        indexed_count=len(loaded.passages),
        incomplete_coverage=loaded.manifest.incomplete_coverage,
        issues=loaded.issues,
    )


def load_source_shelf(ws: WorkspacePaths, generation: str) -> SourceShelf:
    """Load and verify one immutable shelf generation."""

    shelf = load_source_shelf_generation(ws, generation)
    _require_current_sources(ws, shelf)
    return shelf


def _resolve_source(
    ws: WorkspacePaths,
    asset: SourceAssetRecord,
    source_ref: str,
) -> _ResolvedSource | SourceShelfIssue:
    if asset.metadata.get("acquisition_state") != "acquired" or asset.metadata.get("shelf_eligible") is not True:
        return _issue(
            "source_not_shelf_eligible",
            source_ref,
            "source is metadata-only, failed, denied, or not shelf eligible",
        )
    receipt_ref = asset.metadata.get("source_acquisition_receipt_ref")
    decision_ref = asset.metadata.get("source_acquisition_decision_ref")
    if not isinstance(receipt_ref, Mapping) or not isinstance(decision_ref, Mapping):
        return _issue("source_acquisition_unverified", source_ref, "exact acquisition pins are missing")
    try:
        resolution = resolve_source_acquisition_for_source_asset(ws, receipt_ref)
    except (SourceAcquisitionResolutionError, TypeError, ValueError) as exc:
        return _issue("source_acquisition_unverified", source_ref, str(exc))
    if asdict(resolution.receipt_ref) != dict(receipt_ref) or asdict(resolution.decision_ref) != dict(decision_ref):
        return _issue("source_acquisition_unverified", source_ref, "source metadata does not retain exact pins")
    decision = resolution.decision
    receipt = resolution.receipt
    if (
        decision.access_disposition.strip().lower() in _RESTRICTED_ACCESS
        or decision.storage_permission.strip().lower() in _RESTRICTED_STORAGE
    ):
        return _issue("source_access_restricted", source_ref, "access or storage policy forbids shelf use")
    if (
        receipt.topic_id != asset.topic_id
        or receipt.claim_id != asset.claim_id
        or receipt.canonical_uri != asset.uri
        or receipt.byte_sha256 != asset.content_hash
        or receipt.hash_algorithm != asset.hash_algorithm
    ):
        return _issue("source_acquisition_unverified", source_ref, "source identity disagrees with receipt")
    path = _path_from_file_uri(receipt.stored_uri)
    if path is None:
        return _issue("source_storage_not_local", source_ref, "receipt does not identify a local file blob")
    try:
        resolved_path = path.resolve(strict=True)
    except FileNotFoundError:
        return _issue("source_blob_missing", source_ref, "receipted local source blob is missing")
    blob_root = (ws.root / "source_blobs").resolve()
    if not resolved_path.is_file() or not resolved_path.is_relative_to(blob_root):
        return _issue("source_storage_not_local", source_ref, "receipted source is outside the source blob store")
    actual_bytes = resolved_path.read_bytes()
    actual_hash = hashlib.sha256(actual_bytes).hexdigest()
    if actual_hash != receipt.byte_sha256 or len(actual_bytes) != receipt.byte_length:
        return _issue(
            "source_bytes_changed",
            source_ref,
            f"receipted bytes changed: expected {receipt.byte_sha256}, observed {actual_hash}",
        )
    local_uri = resolved_path.as_uri()
    if str(asset.metadata.get("local_path") or "").strip() != str(resolved_path) or receipt.stored_uri != local_uri:
        return _issue("source_storage_mismatch", source_ref, "asset path disagrees with receipt storage URI")
    record_pin = pin_current_record(ws, source_ref)
    return _ResolvedSource(
        pin=SourceShelfSourcePin(
            source_asset_ref=source_ref,
            topic_id=asset.topic_id,
            record_content_hash=record_pin.content_hash,
            record_revision=record_pin.revision,
            canonical_uri=asset.uri,
            local_uri=local_uri,
            content_hash=asset.content_hash,
            acquired_at=asset.acquired_at,
            access_disposition=decision.access_disposition,
            storage_permission=decision.storage_permission,
            acquisition_decision_ref=asdict(resolution.decision_ref),
            acquisition_receipt_ref=asdict(resolution.receipt_ref),
            source_location_pins=(),
        ),
        source_bytes=actual_bytes,
        source_suffix=resolved_path.suffix.lower(),
    )


def _source_passage(*, source_ref, pin, location_refs, ordinal, extracted) -> SourcePassage:
    text_hash = hashlib.sha256(extracted.text.encode("utf-8")).hexdigest()
    identity = source_passage_id(
        source_asset_ref=source_ref,
        source_content_hash=pin.content_hash,
        page_start=extracted.page_start,
        page_end=extracted.page_end,
        section=extracted.section,
        ordinal=ordinal,
        text_hash=text_hash,
    )
    return SourcePassage(
        passage_id=identity,
        ordinal=ordinal,
        source_asset_ref=source_ref,
        source_content_hash=pin.content_hash,
        canonical_uri=pin.canonical_uri,
        local_uri=pin.local_uri,
        page_start=extracted.page_start,
        page_end=extracted.page_end,
        section=extracted.section,
        anchor_kinds=extracted.anchor_kinds,
        anchor_labels=extracted.anchor_labels,
        source_location_refs=location_refs,
        text=extracted.text,
        text_hash=text_hash,
    )


def _requested_refs(repository, request):
    supplied = tuple(dict.fromkeys(ref.strip() for ref in request.source_asset_refs if ref.strip()))
    if supplied:
        return supplied, []
    report = repository.list("source_assets")
    refs = tuple(
        sorted(
            f"source_asset:{record.asset_id}"
            for record in report.records
            if isinstance(record, SourceAssetRecord) and record.topic_id == request.topic_id
        )
    )
    issues = [
        _issue("canonical_source_unreadable", "", f"{item.path}: {item.message}")
        for item in report.malformed
    ]
    return refs, issues


def _reference_locations(repository, topic_id):
    report = repository.list("reference_locations")
    records = tuple(
        item
        for item in report.records
        if isinstance(item, ReferenceLocationRecord)
    )
    issues = [
        _issue("canonical_location_unreadable", "", f"{item.path}: {item.message}")
        for item in report.malformed
    ]
    return records, issues


def _location_pins(ws, *, locations, topic_id, source_ref):
    pins = []
    issues = []
    for location in locations:
        if location.source_ref != source_ref:
            continue
        location_ref = f"reference_location:{location.location_id}"
        if location.topic_id != topic_id:
            issues.append(_issue("source_location_topic_mismatch", source_ref, location_ref))
            continue
        try:
            pinned = pin_current_record(ws, location_ref)
        except Exception as exc:  # noqa: BLE001 - every retained location must be exact.
            issues.append(_issue("source_location_unpinned", source_ref, f"{location_ref}: {exc}"))
            continue
        pins.append(
            SourceShelfLocationPin(
                record_ref=pinned.record_ref,
                content_hash=pinned.content_hash,
                revision=pinned.revision,
                topic_id=location.topic_id,
                source_asset_ref=location.source_ref,
            )
        )
    return tuple(sorted(pins, key=lambda item: item.record_ref)), issues


def _require_current_sources(ws, shelf):
    repository = RecordRepository(ws, actor=_reader_actor())
    expected_pins = {
        pin.source_asset_ref: pin for pin in shelf.manifest.source_pins
    }
    locations, location_issues = _reference_locations(repository, shelf.manifest.topic_id)
    expected_location_issues = {
        issue
        for issue in shelf.issues
        if issue.code == "canonical_location_unreadable" and not issue.source_asset_ref
    }
    if set(location_issues) != expected_location_issues:
        raise SourceShelfStaleError("canonical location issue state changed")
    current_refs = set()
    for source_ref in shelf.manifest.requested_source_asset_refs:
        expected_pin = expected_pins.get(source_ref)
        current_location_pins, pin_issues = _location_pins(
            ws,
            locations=locations,
            topic_id=shelf.manifest.topic_id,
            source_ref=source_ref,
        )
        for issue in pin_issues:
            _require_current_issue(shelf, issue)
        result = repository.read(source_ref)
        if result.status != "found" or not isinstance(result.record, SourceAssetRecord):
            _require_current_issue(
                shelf,
                replace(
                    _read_issue(source_ref, result.status),
                    source_location_pins=current_location_pins,
                ),
            )
            continue
        if result.record.topic_id != shelf.manifest.topic_id:
            _require_current_issue(
                shelf,
                _issue(
                    "source_topic_mismatch",
                    source_ref,
                    "source belongs to another topic",
                    source_location_pins=current_location_pins,
                ),
            )
            continue
        resolved = _resolve_source(ws, result.record, source_ref)
        if isinstance(resolved, SourceShelfIssue):
            _require_current_issue(
                shelf,
                replace(resolved, source_location_pins=current_location_pins),
            )
            continue
        if expected_pin is None:
            raise SourceShelfStaleError(f"source issue state changed: {source_ref}")
        if not current_location_pins:
            _require_current_issue(
                shelf,
                _issue(
                    "missing_source_location",
                    source_ref,
                    "source has no exact ReferenceLocationRecord",
                ),
            )
        current_pin = replace(
            resolved.pin,
            source_location_pins=current_location_pins,
        )
        if current_pin != expected_pin:
            raise SourceShelfStaleError(
                f"source_location_or_pin_changed: {source_ref}"
            )
        current_refs.add(source_ref)
    if current_refs != set(expected_pins):
        raise SourceShelfStaleError("source pin or issue state changed")


def _require_current_issue(shelf, issue):
    if issue not in shelf.issues:
        raise SourceShelfStaleError(
            f"{issue.code}: source issue state changed: "
            f"{issue.source_asset_ref or issue.code}"
        )


def _path_from_file_uri(uri: str) -> Path | None:
    parsed = urlparse(str(uri or ""))
    if parsed.scheme.lower() != "file":
        return None
    path_text = url2pathname(unquote(parsed.path))
    if parsed.netloc and parsed.netloc.lower() not in {"", "localhost"}:
        path_text = f"//{parsed.netloc}{path_text}"
    return Path(path_text)


def _read_issue(source_ref, status):
    code = "source_asset_not_found" if status == "not_found" else "source_asset_unreadable"
    return _issue(code, source_ref, f"canonical source asset read status is {status}")


def _issue(code, source_ref, detail, *, source_location_pins=()):
    return SourceShelfIssue(
        code=code,
        source_asset_ref=source_ref,
        detail=detail,
        source_location_pins=source_location_pins,
    )


def _unique_issues(issues):
    seen = set()
    result = []
    for issue in issues:
        key = issue
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _reader_actor():
    return RecordActor(actor_type="tool", actor_id="source_shelf", host="aitp-v5")
