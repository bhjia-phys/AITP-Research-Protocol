"""Canonical source-asset records for raw research materials."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import SourceAssetRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, write_record


ASSET_TYPES = {
    "paper",
    "lecture",
    "note",
    "book",
    "code_repo",
    "code_snapshot",
    "dataset",
    "generated_artifact",
    "web_page",
    "correspondence",
    "other",
}


def register_source_asset(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    asset_type: str,
    uri: str,
    title: str,
    claim_id: str = "",
    label: str = "",
    content_hash: str = "",
    hash_algorithm: str = "",
    version_anchor: dict[str, Any] | None = None,
    acquired_at: str = "",
    source_kind: str = "manual",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    linked_records: dict[str, Any] | None = None,
) -> SourceAssetRecord:
    """Record a raw paper, lecture, note, repo, dataset, or generated artifact identity."""

    if asset_type not in ASSET_TYPES:
        allowed = ", ".join(sorted(ASSET_TYPES))
        raise ValueError(f"asset_type must be one of: {allowed}")
    if not topic_id:
        raise ValueError("topic_id is required")
    if not uri:
        raise ValueError("uri is required")
    if not title:
        raise ValueError("title is required")

    enriched_metadata = dict(metadata or {})
    local_path = _local_path_from_uri(uri)
    if local_path is not None and local_path.exists() and local_path.is_file():
        content_hash = content_hash or _sha256(local_path)
        hash_algorithm = hash_algorithm or "sha256"
        enriched_metadata.setdefault("size_bytes", local_path.stat().st_size)
        enriched_metadata.setdefault("local_path", str(local_path))

    asset_id = prefixed_id(
        "source-asset",
        f"{topic_id}:{claim_id}:{asset_type}:{uri}:{content_hash}:{version_anchor or {}}",
        max_slug=72,
    )
    if content_hash:
        enriched_metadata.setdefault(
            "duplicate_hash_diagnostics",
            _duplicate_hash_diagnostics(
                ws,
                asset_id=asset_id,
                content_hash=content_hash,
                hash_algorithm=hash_algorithm or "unknown",
            ),
        )
    record = SourceAssetRecord(
        asset_id=asset_id,
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        uri=uri,
        title=title,
        label=label,
        content_hash=content_hash,
        hash_algorithm=hash_algorithm,
        version_anchor=version_anchor or {},
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs or [],
        artifact_ids=artifact_ids or [],
        code_state_ids=code_state_ids or [],
        reference_location_ids=reference_location_ids or [],
        derived_from=derived_from or [],
        metadata=enriched_metadata,
        linked_records=linked_records or {},
        orientation_only=True,
        can_update_claim_trust=False,
    )
    write_record(
        ws.registry_dir("source_assets") / f"{asset_id}.md",
        record,
        body=_body(record),
    )
    return record


def list_source_assets_for_topic(ws: WorkspacePaths, topic_id: str) -> list[SourceAssetRecord]:
    """Return source assets registered for a topic."""

    return [
        record
        for record in list_valid_records(ws.registry_dir("source_assets"), SourceAssetRecord)
        if record.topic_id == topic_id
    ]


def source_asset_payload(record: SourceAssetRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def _body(record: SourceAssetRecord) -> str:
    anchors = "\n".join(f"- `{key}`: {value}" for key, value in record.version_anchor.items()) or "- None"
    derived = "\n".join(f"- {item}" for item in record.derived_from) or "- None"
    return (
        f"# Source Asset: {record.title}\n\n"
        f"Type: `{record.asset_type}`\n\n"
        f"URI: `{record.uri}`\n\n"
        f"Content hash: `{record.content_hash or 'unknown'}`\n\n"
        f"Version anchor:\n{anchors}\n\n"
        f"Summary: {record.summary}\n\n"
        f"Derived from:\n{derived}\n\n"
        "This record is an orientation-only canonical asset identity. It is not evidence by itself.\n"
    )


def _local_path_from_uri(uri: str) -> Path | None:
    if uri.startswith("file://"):
        return Path(uri[7:])
    path = Path(uri)
    if path.exists():
        return path
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _duplicate_hash_diagnostics(
    ws: WorkspacePaths,
    *,
    asset_id: str,
    content_hash: str,
    hash_algorithm: str,
) -> dict[str, Any]:
    duplicates = [
        record.asset_id
        for record in list_valid_records(ws.registry_dir("source_assets"), SourceAssetRecord)
        if record.asset_id != asset_id
        and record.content_hash == content_hash
        and (record.hash_algorithm or "unknown") == hash_algorithm
    ]
    return {
        "hash": content_hash,
        "hash_algorithm": hash_algorithm,
        "duplicate_hash": bool(duplicates),
        "duplicate_asset_ids": duplicates,
        "diagnostic_scope": "registry/source_assets",
    }
