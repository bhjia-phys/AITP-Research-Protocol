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
    SOURCE_SHELF_SCHEMA_VERSION,
    SourcePassage,
    SourceShelf,
    SourceShelfIntegrityError,
    SourceShelfIssue,
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
    write_text_atomic(
        root / "manifest.json",
        json.dumps(asdict(shelf.manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


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
    expected_generation = hash_json(_basis_from_manifest(manifest))
    if manifest.generation != generation or expected_generation != generation:
        raise SourceShelfIntegrityError("source shelf generation hash mismatch")
    passages = tuple(_passage_from_dict(row) for row in passage_rows)
    try:
        issues = tuple(SourceShelfIssue(**row) for row in issue_rows)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf issue is malformed: {exc}") from exc
    if manifest.passage_count != len(passages) or manifest.issue_count != len(issues):
        raise SourceShelfIntegrityError("source shelf component count mismatch")
    if any(not item.orientation_only or item.can_update_claim_trust for item in passages):
        raise SourceShelfIntegrityError("source shelf passage violates trust boundary")
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
        passages_hash=manifest.passages_hash,
        issues_hash=manifest.issues_hash,
    )


def _validate_manifest_contract(manifest) -> None:
    if manifest.schema_version != SOURCE_SHELF_SCHEMA_VERSION:
        raise SourceShelfIntegrityError("unsupported source shelf schema version")
    if manifest.passage_file != "passages.json" or manifest.issues_file != "issues.json":
        raise SourceShelfIntegrityError("source shelf component path is invalid")
    if not manifest.orientation_only or manifest.can_update_claim_trust:
        raise SourceShelfIntegrityError("source shelf manifest violates trust boundary")


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
        values["requested_source_asset_refs"] = tuple(values.get("requested_source_asset_refs") or [])
        values["source_pins"] = tuple(
            SourceShelfSourcePin(**row) for row in values.get("source_pins") or []
        )
        return SourceShelfManifest(**values)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf manifest is malformed: {exc}") from exc


def _passage_from_dict(row):
    try:
        values = dict(row)
        for field in ("anchor_kinds", "anchor_labels", "source_location_refs"):
            values[field] = tuple(values.get(field) or [])
        return SourcePassage(**values)
    except (TypeError, ValueError) as exc:
        raise SourceShelfIntegrityError(f"source shelf passage is malformed: {exc}") from exc


def _is_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _load_json_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceShelfIntegrityError(f"cannot load source shelf manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceShelfIntegrityError("source shelf manifest must be an object")
    return value


def _load_json_list(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceShelfIntegrityError(f"cannot load source shelf component: {exc}") from exc
    if not isinstance(value, list):
        raise SourceShelfIntegrityError("source shelf component must be a list")
    return value
