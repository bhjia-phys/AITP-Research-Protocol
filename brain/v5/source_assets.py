"""Canonical source-asset records for raw research materials."""

from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import asdict
from datetime import UTC, datetime
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


def capture_source_asset_from_local_path(
    ws: WorkspacePaths,
    *,
    path: str,
    topic_id: str,
    claim_id: str = "",
    asset_type: str = "",
    title: str = "",
    label: str = "",
    version_anchor: dict[str, Any] | None = None,
    acquired_at: str = "",
    source_kind: str = "local_file_auto",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    linked_records: dict[str, Any] | None = None,
) -> SourceAssetRecord:
    """Inspect a local file and register it as a canonical source asset."""

    local_path = Path(path).expanduser()
    if not local_path.exists():
        raise FileNotFoundError(f"source asset path does not exist: {path}")
    if not local_path.is_file():
        raise ValueError(f"source asset path must be a file: {path}")

    resolved = local_path.resolve()
    stat = resolved.stat()
    content_hash = _sha256(resolved)
    mime_type, _ = mimetypes.guess_type(str(resolved))
    inferred_type = asset_type or _asset_type_for_path(resolved)
    inferred_title = title or _title_for_path(resolved)
    captured_at = datetime.now(UTC).isoformat()

    enriched_metadata = dict(metadata or {})
    enriched_metadata.setdefault("capture_tool", "aitp_v5_capture_source_asset_auto")
    enriched_metadata.setdefault("captured_at", captured_at)
    enriched_metadata.setdefault("local_path", str(resolved))
    enriched_metadata.setdefault("file_name", resolved.name)
    enriched_metadata.setdefault("file_suffix", resolved.suffix.lower())
    enriched_metadata.setdefault("mime_type", mime_type or "")
    enriched_metadata.setdefault("size_bytes", stat.st_size)
    enriched_metadata.setdefault("mtime_utc", datetime.fromtimestamp(stat.st_mtime, UTC).isoformat())
    enriched_metadata.setdefault("auto_asset_type", inferred_type)
    enriched_metadata.setdefault("content_hash_basis", "local file bytes")

    anchors = dict(version_anchor or {})
    anchors.setdefault("local_path", str(resolved))
    anchors.setdefault("sha256", content_hash)
    anchors.setdefault("mtime_utc", enriched_metadata["mtime_utc"])
    anchors.setdefault("size_bytes", stat.st_size)

    links = dict(linked_records or {})
    if topic_id:
        links.setdefault("topic_id", topic_id)
    if claim_id:
        links.setdefault("claim_id", claim_id)

    return register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=inferred_type,
        uri=f"file://{resolved}",
        title=inferred_title,
        label=label or inferred_title,
        content_hash=content_hash,
        hash_algorithm="sha256",
        version_anchor=anchors,
        acquired_at=acquired_at or captured_at,
        source_kind=source_kind,
        summary=summary or f"Auto-captured local source asset: {resolved.name}.",
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=enriched_metadata,
        linked_records=links,
    )


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


def _asset_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "paper"
    if suffix in {".tex", ".md", ".rst", ".txt", ".ipynb"}:
        return "note"
    if suffix in {".csv", ".json", ".jsonl", ".parquet", ".h5", ".hdf5"}:
        return "dataset"
    if suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".cpp", ".c", ".h", ".hpp", ".f90", ".jl", ".m"}:
        return "code_snapshot"
    return "other"


def _title_for_path(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    return stem or path.name


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
