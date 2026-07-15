"""Immutable byte receipts for reproducible artifacts and Skill packages."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from brain.v5.models import ArtifactBlobReceiptRecord, ValidationResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ArtifactBlobIntegrityError(RuntimeError):
    """Raised when receipt metadata cannot resolve the promised immutable bytes."""


@dataclass(frozen=True)
class ArtifactBlobCapture:
    record: ArtifactBlobReceiptRecord
    pinned_ref: PinnedRecordRef
    blob_path: str
    write_status: str


def capture_artifact_bytes(
    ws: WorkspacePaths,
    source_path: str | Path,
    *,
    actor: RecordActor,
) -> ArtifactBlobCapture:
    """Copy local bytes into the SHA-256 store and record one path-free receipt."""

    source = Path(source_path).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"artifact source does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"artifact source must be a file: {source}")
    byte_sha256, byte_length, target = _stage_source_blob(ws, source)
    return _record_local_blob(
        ws,
        byte_sha256=byte_sha256,
        byte_length=byte_length,
        target=target,
        actor=actor,
    )


def capture_artifact_content(
    ws: WorkspacePaths,
    content: bytes,
    *,
    actor: RecordActor,
) -> ArtifactBlobCapture:
    """Store an in-memory immutable byte stream using the local receipt form."""

    if not isinstance(content, bytes):
        raise TypeError("artifact content must be bytes")
    byte_sha256 = hashlib.sha256(content).hexdigest()
    byte_length = len(content)
    target = _local_blob_path(ws, byte_sha256)
    _store_blob_content(content, target, byte_sha256, byte_length)
    return _record_local_blob(
        ws,
        byte_sha256=byte_sha256,
        byte_length=byte_length,
        target=target,
        actor=actor,
    )


def _record_local_blob(
    ws: WorkspacePaths,
    *,
    byte_sha256: str,
    byte_length: int,
    target: Path,
    actor: RecordActor,
) -> ArtifactBlobCapture:
    blob_key = target.relative_to(ws.root).as_posix()
    record = ArtifactBlobReceiptRecord(
        receipt_id=f"artifact-blob-sha256-{byte_sha256}",
        storage_kind="local_sha256",
        hash_algorithm="sha256",
        byte_sha256=byte_sha256,
        byte_length=byte_length,
        blob_key=blob_key,
    )
    write = RecordRepository(ws, actor=actor).write(
        "artifact_blob_receipts",
        record,
        body="# Artifact Blob Receipt\n\nContent-addressed local bytes.\n",
    )
    return ArtifactBlobCapture(
        record=record,
        pinned_ref=PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        ),
        blob_path=str(target),
        write_status=write.status,
    )


def record_external_artifact_receipt(
    ws: WorkspacePaths,
    *,
    provider: str,
    object_id: str,
    object_version: str,
    byte_sha256: str,
    byte_length: int,
    retention_policy: str,
    access_policy: str,
    availability_verification_ref: PinnedRecordRef | dict,
    actor: RecordActor,
) -> ArtifactBlobCapture:
    """Record immutable external storage only when identity and availability are exact."""

    required = {
        "provider": provider,
        "object_id": object_id,
        "object_version": object_version,
        "retention_policy": retention_policy,
        "access_policy": access_policy,
    }
    for field, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")
    _require_sha256(byte_sha256)
    if isinstance(byte_length, bool) or not isinstance(byte_length, int) or byte_length < 0:
        raise ValueError("byte_length must be a non-negative integer")
    verification_pin = _coerce_pin(availability_verification_ref)
    try:
        verification = get_record_version(ws, verification_pin)
    except Exception as exc:
        raise ValueError("availability verification ref is not resolvable") from exc
    if not isinstance(verification.record, ValidationResultRecord):
        raise ValueError("availability verification must reference a validation result")
    validation = verification.record
    if validation.status != "passed":
        raise ValueError("availability verification must have status passed")
    if not validation.executor_id or not validation.executor_version or not validation.executor_hash:
        raise ValueError("availability verification must pin its executor")
    object_key = f"{provider}://{object_id}?versionId={object_version}"
    if validation.checked_artifact_hashes.get(object_key) != byte_sha256:
        raise ValueError("availability verification does not check the immutable object hash")
    identity = {
        **required,
        "byte_sha256": byte_sha256,
        "byte_length": byte_length,
        "availability_verified": True,
        "availability_verification": {
            "record_ref": verification_pin.record_ref,
            "content_hash": verification_pin.content_hash,
            "revision": verification_pin.revision,
        },
    }
    identity_hash = hashlib.sha256(_canonical_json(identity)).hexdigest()
    record = ArtifactBlobReceiptRecord(
        receipt_id=f"artifact-blob-external-{identity_hash}",
        storage_kind="external_immutable",
        hash_algorithm="sha256",
        byte_sha256=byte_sha256,
        byte_length=byte_length,
        blob_key="",
        provider=provider,
        object_id=object_id,
        object_version=object_version,
        retention_policy=retention_policy,
        access_policy=access_policy,
        availability_verified=True,
        availability_verification_ref=verification_pin.record_ref,
        availability_verification_hash=verification_pin.content_hash,
        availability_verification_revision=verification_pin.revision,
    )
    write = RecordRepository(ws, actor=actor).write(
        "artifact_blob_receipts",
        record,
        body="# Artifact Blob Receipt\n\nImmutable external object receipt.\n",
    )
    return ArtifactBlobCapture(
        record=record,
        pinned_ref=PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        ),
        blob_path="",
        write_status=write.status,
    )


def resolve_artifact_bytes(
    ws: WorkspacePaths,
    pinned_receipt: PinnedRecordRef | dict,
) -> bytes:
    """Resolve and rehash local bytes from one exact receipt version."""

    version = get_record_version(ws, pinned_receipt)
    if not isinstance(version.record, ArtifactBlobReceiptRecord):
        raise ArtifactBlobIntegrityError("pinned record is not an artifact blob receipt")
    receipt = version.record
    if receipt.storage_kind != "local_sha256":
        raise ArtifactBlobIntegrityError(
            "external immutable receipts require a provider availability adapter"
        )
    _require_sha256(receipt.byte_sha256)
    path = _safe_blob_key_path(ws, receipt.blob_key)
    if not path.exists():
        raise ArtifactBlobIntegrityError(f"missing artifact blob bytes: {receipt.blob_key}")
    content = path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    actual_length = len(content)
    if actual_hash != receipt.byte_sha256 or actual_length != receipt.byte_length:
        raise ArtifactBlobIntegrityError(
            f"corrupt artifact blob bytes: {receipt.blob_key}"
        )
    return content


def _stage_source_blob(ws: WorkspacePaths, source: Path) -> tuple[str, int, Path]:
    staging = ws.root / "blobs" / "sha256" / ".staging"
    staging.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    digest = hashlib.sha256()
    byte_length = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=staging,
            prefix=".capture.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            with source.open("rb") as source_handle:
                for chunk in iter(lambda: source_handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    byte_length += len(chunk)
                    handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        byte_sha256 = digest.hexdigest()
        target = _local_blob_path(ws, byte_sha256)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            _require_blob_matches(target, byte_sha256, byte_length)
            temp_path.unlink(missing_ok=True)
            temp_path = None
            return byte_sha256, byte_length, target
        _require_blob_matches(temp_path, byte_sha256, byte_length)
        os.replace(temp_path, target)
        temp_path = None
        _require_blob_matches(target, byte_sha256, byte_length)
        return byte_sha256, byte_length, target
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _store_blob_content(
    content: bytes,
    target: Path,
    expected_hash: str,
    expected_length: int,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        _require_blob_matches(target, expected_hash, expected_length)
        return
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{expected_hash}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _require_blob_matches(temp_path, expected_hash, expected_length)
        os.replace(temp_path, target)
        temp_path = None
        _require_blob_matches(target, expected_hash, expected_length)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _require_blob_matches(path: Path, expected_hash: str, expected_length: int) -> None:
    actual_hash, actual_length = _hash_file(path)
    if actual_hash != expected_hash or actual_length != expected_length:
        raise ArtifactBlobIntegrityError(f"corrupt artifact blob bytes: {path}")


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_length = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            byte_length += len(chunk)
    return digest.hexdigest(), byte_length


def _local_blob_path(ws: WorkspacePaths, byte_sha256: str) -> Path:
    _require_sha256(byte_sha256)
    return ws.root / "blobs" / "sha256" / byte_sha256[:2] / byte_sha256


def _safe_blob_key_path(ws: WorkspacePaths, blob_key: str) -> Path:
    if not blob_key or Path(blob_key).is_absolute():
        raise ArtifactBlobIntegrityError("artifact blob key must be workspace-relative")
    root = (ws.root / "blobs" / "sha256").resolve(strict=False)
    path = (ws.root / blob_key).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ArtifactBlobIntegrityError("artifact blob key escaped the blob store") from exc
    return path


def _require_sha256(value: str) -> None:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise ValueError("byte_sha256 must be a lowercase SHA-256 hex digest")


def _canonical_json(payload: dict) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _coerce_pin(value: PinnedRecordRef | dict) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, dict):
        raise TypeError("availability verification ref must be pinned")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )
