"""Canonical source-asset records for raw research materials."""

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
    write_record(
        ws.registry_dir("source_assets") / f"{asset_id}.md",
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
    copy_to_store: bool = False,
    force_refresh: bool = False,
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

    uri = f"file://{resolved}"
    if copy_to_store:
        asset_id = _source_asset_id(topic_id, claim_id, inferred_type, uri, content_hash, anchors)
        blob_path = _store_acquired_blob(
            ws,
            topic_id=topic_id,
            asset_id=asset_id,
            source_path=resolved,
            suffix=resolved.suffix.lower() or ".bin",
            force_refresh=force_refresh,
        )
        enriched_metadata["original_local_path"] = str(resolved)
        enriched_metadata["local_path"] = str(blob_path.resolve())
        enriched_metadata["blob_path"] = _path_relative_to_store(ws, blob_path)
        enriched_metadata["blob_store"] = str((ws.root / "source_blobs").resolve())
        enriched_metadata["acquisition_status"] = "succeeded"
        enriched_metadata["acquisition_kind"] = "local_copy"
        anchors["original_local_path"] = str(resolved)
        anchors["local_path"] = str(blob_path.resolve())
        anchors["blob_path"] = enriched_metadata["blob_path"]

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
        uri=uri,
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


def _source_asset_id(
    topic_id: str,
    claim_id: str,
    asset_type: str,
    uri: str,
    content_hash: str,
    version_anchor: dict[str, Any] | None,
) -> str:
    return prefixed_id(
        "source-asset",
        f"{topic_id}:{claim_id}:{asset_type}:{uri}:{content_hash}:{version_anchor or {}}",
        max_slug=72,
    )


def _register_pdf_acquisition_failure(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    asset_type: str,
    url: str,
    title: str,
    label: str,
    attempted_at: str,
    failure_reason: str,
    version_anchor: dict[str, Any] | None,
    source_kind: str,
    summary: str,
    source_refs: list[str] | None,
    artifact_ids: list[str] | None,
    code_state_ids: list[str] | None,
    reference_location_ids: list[str] | None,
    derived_from: list[str] | None,
    metadata: dict[str, Any] | None,
    linked_records: dict[str, Any] | None,
) -> SourceAssetRecord:
    anchors = dict(version_anchor or {})
    anchors.setdefault("source_url", url)
    anchors.setdefault("acquisition_status", "failed")

    enriched_metadata = dict(metadata or {})
    acquisition_kind = enriched_metadata.get("acquisition_kind", "pdf")
    enriched_metadata.update(
        {
            "acquisition_status": "failed",
            "acquisition_kind": acquisition_kind,
            "requested_url": url,
            "source_url": url,
            "attempted_at": attempted_at,
            "failure_reason": failure_reason,
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
        uri=url,
        title=title,
        label=label or title,
        content_hash="",
        hash_algorithm="",
        version_anchor=anchors,
        acquired_at=attempted_at,
        source_kind=source_kind,
        summary=summary or f"PDF acquisition failed for source: {title}.",
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=enriched_metadata,
        linked_records=links,
    )


def _normalize_pdf_source_url(ws: WorkspacePaths, url: str) -> tuple[str, dict[str, Any]]:
    raw = str(url or "").strip()
    if not raw:
        raise ValueError("url is required")
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme == "arxiv":
        arxiv_id = _normalize_arxiv_id(parsed.path or parsed.netloc)
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf", {"source_scheme": "arxiv", "arxiv_id": arxiv_id}
    if scheme in {"http", "https"}:
        return raw, {"source_scheme": scheme}
    if scheme == "file":
        local_path = _path_from_file_uri(raw).expanduser().resolve()
        _ensure_file_source_path_allowed(ws, local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"PDF source path does not exist: {local_path}")
        if not local_path.is_file():
            raise ValueError(f"PDF source path must be a file: {local_path}")
        return local_path.as_uri(), {"source_scheme": "file", "source_local_path": str(local_path)}
    raise ValueError("PDF acquisition only supports http, https, file, or arxiv: sources")


def _normalize_arxiv_id(arxiv_id: str, *, version: str = "") -> str:
    raw = str(arxiv_id or "").strip()
    if not raw:
        raise ValueError("arxiv_id is required")
    if raw.startswith("arxiv:"):
        raw = raw.split(":", 1)[1]
    parsed = urlparse(raw)
    if parsed.netloc.endswith("arxiv.org"):
        path = parsed.path.strip("/")
        if path.startswith(("abs/", "pdf/")):
            raw = path.split("/", 1)[1]
    raw = raw.split("?", 1)[0].split("#", 1)[0].strip("/")
    if raw.endswith(".pdf"):
        raw = raw[:-4]
    if version:
        version_text = str(version).strip()
        if version_text and not version_text.startswith("v"):
            version_text = f"v{version_text}"
        raw = re.sub(r"v\d+$", "", raw) + version_text
    if not re.match(r"^[A-Za-z0-9._/-]+v?\d*$", raw):
        raise ValueError(f"invalid arxiv_id: {arxiv_id}")
    return raw


def _fetch_pdf_to_temp(
    ws: WorkspacePaths,
    source_url: str,
    *,
    timeout_seconds: int,
    max_bytes: int,
) -> _PdfFetchResult:
    tmp_dir = ws.root / "source_blobs" / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="aitp-pdf-", suffix=".pdf", dir=tmp_dir, delete=False) as handle:
        tmp_path = Path(handle.name)

    parsed = urlparse(source_url)
    try:
        if parsed.scheme == "file":
            local_path = _path_from_file_uri(source_url).expanduser().resolve()
            shutil.copyfile(local_path, tmp_path)
            mime_type, _ = mimetypes.guess_type(str(local_path))
            return _PdfFetchResult(
                temp_path=tmp_path,
                requested_url=source_url,
                source_url=source_url,
                final_url=source_url,
                mime_type=mime_type or "application/pdf",
            )
        if parsed.scheme in {"http", "https"}:
            return _download_pdf_to_temp(
                source_url,
                tmp_path=tmp_path,
                timeout_seconds=timeout_seconds,
                max_bytes=max_bytes,
            )
        raise ValueError("PDF acquisition only supports http, https, file, or arxiv: sources")
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _download_pdf_to_temp(
    source_url: str,
    *,
    tmp_path: Path,
    timeout_seconds: int,
    max_bytes: int,
) -> _PdfFetchResult:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    request = Request(source_url, headers={"User-Agent": "AITP-v5-source-asset/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValueError(f"PDF download exceeds max_bytes: {content_length} > {max_bytes}")
            total = 0
            with tmp_path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError(f"PDF download exceeds max_bytes: {total} > {max_bytes}")
                    handle.write(chunk)
            return _PdfFetchResult(
                temp_path=tmp_path,
                requested_url=source_url,
                source_url=source_url,
                final_url=response.geturl() or source_url,
                mime_type=response.headers.get_content_type() or "application/pdf",
                http_status=getattr(response, "status", response.getcode()),
            )
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while downloading PDF") from exc
    except URLError as exc:
        raise RuntimeError(f"network error while downloading PDF: {exc.reason}") from exc


def _assert_pdf_bytes(path: Path) -> None:
    with path.open("rb") as handle:
        header = handle.read(5)
    if not header.startswith(b"%PDF-"):
        raise ValueError("acquired source is not a PDF byte stream")


def _store_acquired_blob(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    asset_id: str,
    source_path: Path,
    suffix: str,
    force_refresh: bool,
) -> Path:
    _safe_path_component(topic_id, "topic_id")
    _safe_path_component(asset_id, "asset_id")
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    blob_root = (ws.root / "source_blobs").resolve()
    blob_dir = ws.source_blob_dir(topic_id, asset_id)
    blob_dir.mkdir(parents=True, exist_ok=True)
    destination = (blob_dir / f"original{suffix.lower()}").resolve()
    if not _is_relative_to(destination, blob_root):
        raise ValueError("resolved source blob path escaped the source_blobs store")

    source_resolved = source_path.resolve()
    if destination.exists():
        if _sha256(destination) == _sha256(source_resolved):
            return destination
        if not force_refresh:
            raise FileExistsError(f"source blob already exists with different content: {destination}")

    tmp_path = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        shutil.copyfile(source_resolved, tmp_path)
        os.replace(tmp_path, destination)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
    return destination


def _path_relative_to_store(ws: WorkspacePaths, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ws.root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _safe_path_component(value: str, label: str) -> None:
    text = str(value or "")
    if not text or text in {".", ".."}:
        raise ValueError(f"{label} must be a non-empty path component")
    if Path(text).is_absolute() or Path(text).name != text or "/" in text or "\\" in text:
        raise ValueError(f"{label} must not contain path separators")


def _ensure_file_source_path_allowed(ws: WorkspacePaths, path: Path) -> None:
    resolved = path.resolve()
    topics_root = ws.base.resolve()
    blob_root = (ws.root / "source_blobs").resolve()
    if _is_relative_to(resolved, topics_root) or _is_relative_to(resolved, blob_root):
        return
    raise ValueError("file:// PDF sources must resolve under the topics root or AITP source_blobs store")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


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
        try:
            return _path_from_file_uri(uri)
        except ValueError:
            return Path(uri[7:])
    path = Path(uri)
    if path.exists():
        return path
    return None


def _path_from_file_uri(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise ValueError("expected file:// URI")
    if parsed.netloc in {"", "localhost"}:
        return Path(url2pathname(parsed.path))
    if re.match(r"^[A-Za-z]:$", parsed.netloc):
        return Path(f"{parsed.netloc}{url2pathname(parsed.path)}")
    if parsed.path == "" and re.match(r"^[A-Za-z]:[\\/]", parsed.netloc):
        return Path(parsed.netloc)
    raise ValueError("non-local file:// URI is not supported")


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
