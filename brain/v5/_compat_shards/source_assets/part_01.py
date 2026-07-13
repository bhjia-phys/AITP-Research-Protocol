# Compatibility shard 1 for source_assets.
from __future__ import annotations

import hashlib

import mimetypes

import os

import re

import shutil

import tempfile

from dataclasses import asdict, dataclass

from datetime import UTC, datetime

from pathlib import Path

from typing import Any

from urllib.error import HTTPError, URLError

from urllib.parse import urlparse

from urllib.request import Request, url2pathname, urlopen

from brain.v5.ids import prefixed_id

from brain.v5.models import SourceAssetRecord

from brain.v5.paths import WorkspacePaths

from brain.v5.record_envelope import RecordActor

from brain.v5.record_repository import RecordRepository

from brain.v5.store import list_records

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

ASSET_TYPE_ALIASES = {
    "derived_dataset": "dataset",
    "generated_dataset": "dataset",
    "result_dataset": "dataset",
    "numeric_dataset": "dataset",
    "data_product": "dataset",
}

DEFAULT_PDF_TIMEOUT_SECONDS = 120

DEFAULT_PDF_MAX_BYTES = 200 * 1024 * 1024

@dataclass(frozen=True)
class _PdfFetchResult:
    temp_path: Path
    requested_url: str
    source_url: str
    final_url: str
    mime_type: str
    http_status: int | None = None

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

    requested_asset_type = str(asset_type or "").strip()
    asset_type = normalize_asset_type(requested_asset_type)
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
    if requested_asset_type and requested_asset_type != asset_type:
        enriched_metadata.setdefault("requested_asset_type", requested_asset_type)
        enriched_metadata.setdefault("asset_type_normalized_from", requested_asset_type)
    local_path = _local_path_from_uri(uri)
    if (
        enriched_metadata.get("acquisition_status") != "failed"
        and local_path is not None
        and local_path.exists()
        and local_path.is_file()
    ):
        content_hash = content_hash or _sha256(local_path)
        hash_algorithm = hash_algorithm or "sha256"
        enriched_metadata.setdefault("size_bytes", local_path.stat().st_size)
        enriched_metadata.setdefault("local_path", str(local_path))

    asset_id = _source_asset_id(topic_id, claim_id, asset_type, uri, content_hash, version_anchor or {})
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
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="register_source_asset",
            host="aitp",
        ),
    )
    current = repository.read(f"source_asset:{asset_id}")
    if current.status == "found" and isinstance(current.record, SourceAssetRecord):
        return current.record
    repository.write(
        "source_assets",
        record,
        body=_body(record),
    )
    return record

def acquire_pdf_source_asset(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    url: str,
    title: str,
    claim_id: str = "",
    asset_type: str = "paper",
    label: str = "",
    timeout_seconds: int = DEFAULT_PDF_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_PDF_MAX_BYTES,
    force_refresh: bool = False,
    version_anchor: dict[str, Any] | None = None,
    acquired_at: str = "",
    source_kind: str = "literature_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    linked_records: dict[str, Any] | None = None,
) -> SourceAssetRecord:
    """Acquire a PDF into the topic-scoped v5 source blob store and register it."""

    if not topic_id:
        raise ValueError("topic_id is required")
    if not url:
        raise ValueError("url is required")
    if not title:
        raise ValueError("title is required")
    asset_type = normalize_asset_type(asset_type)
    if asset_type not in ASSET_TYPES:
        allowed = ", ".join(sorted(ASSET_TYPES))
        raise ValueError(f"asset_type must be one of: {allowed}")

    attempted_at = datetime.now(UTC).isoformat()
    source_url = str(url).strip()
    fetch_result: _PdfFetchResult | None = None
    try:
        source_url, source_metadata = _normalize_pdf_source_url(ws, source_url)
        fetch_result = _fetch_pdf_to_temp(
            ws,
            source_url,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
        )
        _assert_pdf_bytes(fetch_result.temp_path)
        content_hash = _sha256(fetch_result.temp_path)
        size_bytes = fetch_result.temp_path.stat().st_size
        effective_mime_type = fetch_result.mime_type or "application/pdf"

        anchors = dict(version_anchor or {})
        anchors.setdefault("source_url", source_url)
        anchors.setdefault("final_url", fetch_result.final_url or source_url)
        anchors.setdefault("sha256", content_hash)
        anchors.setdefault("size_bytes", size_bytes)
        anchors.setdefault("mime_type", effective_mime_type)
        anchors.setdefault("acquisition_status", "succeeded")

        asset_id = _source_asset_id(topic_id, claim_id, asset_type, source_url, content_hash, anchors)
        blob_path = _store_acquired_blob(
            ws,
            topic_id=topic_id,
            asset_id=asset_id,
            source_path=fetch_result.temp_path,
            suffix=".pdf",
            force_refresh=force_refresh,
        )

        enriched_metadata = dict(metadata or {})
        acquisition_kind = enriched_metadata.get("acquisition_kind", "pdf")
        enriched_metadata.update(source_metadata)
        enriched_metadata.update(
            {
                "acquisition_status": "succeeded",
                "acquisition_kind": acquisition_kind,
                "requested_url": fetch_result.requested_url,
                "source_url": source_url,
                "final_url": fetch_result.final_url or source_url,
                "local_path": str(blob_path.resolve()),
                "blob_path": _path_relative_to_store(ws, blob_path),
                "blob_store": str((ws.root / "source_blobs").resolve()),
                "file_name": blob_path.name,
                "mime_type": effective_mime_type,
                "size_bytes": size_bytes,
                "http_status": fetch_result.http_status,
                "acquired_at": acquired_at or attempted_at,
                "content_hash_basis": "acquired pdf bytes",
            }
        )

        links = dict(linked_records or {})
        links.setdefault("topic_id", topic_id)
        if claim_id:
            links.setdefault("claim_id", claim_id)

        return register_source_asset(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            asset_type=asset_type,
            uri=source_url,
            title=title,
            label=label or title,
            content_hash=content_hash,
            hash_algorithm="sha256",
            version_anchor=anchors,
            acquired_at=acquired_at or attempted_at,
            source_kind=source_kind,
            summary=summary or f"Acquired local PDF copy for source: {title}.",
            source_refs=source_refs,
            artifact_ids=artifact_ids,
            code_state_ids=code_state_ids,
            reference_location_ids=reference_location_ids,
            derived_from=derived_from,
            metadata=enriched_metadata,
            linked_records=links,
        )
    except Exception as exc:
        return _register_pdf_acquisition_failure(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            asset_type=asset_type,
            url=source_url,
            title=title,
            label=label,
            attempted_at=acquired_at or attempted_at,
            failure_reason=f"{type(exc).__name__}: {exc}",
            version_anchor=version_anchor,
            source_kind=source_kind,
            summary=summary,
            source_refs=source_refs,
            artifact_ids=artifact_ids,
            code_state_ids=code_state_ids,
            reference_location_ids=reference_location_ids,
            derived_from=derived_from,
            metadata=metadata,
            linked_records=linked_records,
        )
    finally:
        if fetch_result is not None:
            try:
                fetch_result.temp_path.unlink(missing_ok=True)
            except OSError:
                pass

def acquire_arxiv_source_asset(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    arxiv_id: str,
    title: str = "",
    claim_id: str = "",
    version: str = "",
    label: str = "",
    timeout_seconds: int = DEFAULT_PDF_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_PDF_MAX_BYTES,
    force_refresh: bool = False,
    version_anchor: dict[str, Any] | None = None,
    source_kind: str = "arxiv_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    linked_records: dict[str, Any] | None = None,
) -> SourceAssetRecord:
    """Acquire an arXiv PDF into the v5 source blob store and register it."""

    normalized_id = _normalize_arxiv_id(arxiv_id, version=version)
    pdf_url = f"https://arxiv.org/pdf/{normalized_id}.pdf"
    anchors = dict(version_anchor or {})
    anchors.setdefault("arxiv_id", normalized_id)
    anchors.setdefault("arxiv_pdf_url", pdf_url)

    enriched_metadata = dict(metadata or {})
    enriched_metadata.setdefault("arxiv_id", normalized_id)
    enriched_metadata.setdefault("acquisition_kind", "arxiv_pdf")

    return acquire_pdf_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type="paper",
        url=pdf_url,
        title=title or f"arXiv {normalized_id} PDF",
        label=label or title or f"arXiv {normalized_id}",
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        force_refresh=force_refresh,
        version_anchor=anchors,
        source_kind=source_kind,
        summary=summary or f"arXiv PDF source asset for {normalized_id}.",
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=enriched_metadata,
        linked_records=linked_records,
    )
