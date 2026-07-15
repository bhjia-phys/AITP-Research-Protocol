"""Immutable manifests for every byte needed to replay a dirty code state."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Mapping

from brain.v5.artifact_blobs import ArtifactBlobCapture, capture_artifact_bytes
from brain.v5.models import CodePatchManifestRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


_CHANGE_KINDS = frozenset(
    {"staged", "unstaged", "deleted", "binary", "submodule", "required_untracked"}
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


@dataclass(frozen=True)
class PatchEntryRequest:
    path: str
    change_kinds: tuple[str, ...]
    required: bool = True
    source_path: str = ""
    deleted: bool = False
    before_sha256: str = ""
    submodule_commit: str = ""
    excluded_reason: str = ""


@dataclass(frozen=True)
class CodePatchManifestCapture:
    record: CodePatchManifestRecord
    pinned_ref: PinnedRecordRef
    blob_captures: tuple[ArtifactBlobCapture, ...]
    write_status: str


def capture_code_patch_manifest(
    ws: WorkspacePaths,
    *,
    repo_id: str,
    base_commit: str,
    entries: list[PatchEntryRequest],
    actor: RecordActor,
    source_refs: list[PinnedRecordRef | Mapping[str, object]] | None = None,
) -> CodePatchManifestCapture:
    """Capture a replayable final-byte manifest for one dirty code state."""

    if not repo_id.strip():
        raise ValueError("repo_id must be non-empty")
    if not _COMMIT_PATTERN.fullmatch(base_commit):
        raise ValueError("base_commit must be an exact 40- or 64-character commit hash")
    if not entries:
        raise ValueError("patch manifest entries must not be empty")
    normalized_entries: list[dict] = []
    captures: list[ArtifactBlobCapture] = []
    seen_paths: set[str] = set()
    for request in entries:
        normalized_path = _safe_relative_path(request.path)
        if normalized_path in seen_paths:
            raise ValueError(f"duplicate patch manifest path: {normalized_path}")
        seen_paths.add(normalized_path)
        entry, capture = _capture_entry(ws, request, normalized_path, actor)
        normalized_entries.append(entry)
        if capture is not None:
            captures.append(capture)
    return _write_manifest(
        ws,
        repo_id=repo_id,
        base_commit=base_commit,
        normalized_entries=normalized_entries,
        captures=captures,
        actor=actor,
        source_refs=_normalize_source_refs(ws, source_refs or []),
        coverage_basis="declared_entries_only",
        observed_status_hash="",
        observed_paths=[],
    )


def capture_git_code_patch_manifest(
    ws: WorkspacePaths,
    *,
    repo_path: str | PurePosixPath,
    repo_id: str,
    actor: RecordActor,
    source_refs: list[PinnedRecordRef | Mapping[str, object]] | None = None,
) -> CodePatchManifestCapture:
    """Capture a complete stable Git index/worktree snapshot."""

    from brain.v5.git_patch_capture import capture_git_patch_manifest

    return capture_git_patch_manifest(
        ws,
        repo_path=repo_path,
        repo_id=repo_id,
        actor=actor,
        source_refs=_normalize_source_refs(ws, source_refs or []),
    )


def _write_manifest(
    ws: WorkspacePaths,
    *,
    repo_id: str,
    base_commit: str,
    normalized_entries: list[dict],
    captures: list[ArtifactBlobCapture],
    actor: RecordActor,
    source_refs: list[dict],
    coverage_basis: str,
    observed_status_hash: str,
    observed_paths: list[str],
) -> CodePatchManifestCapture:
    normalized_entries.sort(key=lambda item: item["path"])
    excluded_required = sorted(
        entry["path"]
        for entry in normalized_entries
        if entry["required"] and entry["excluded_reason"]
    )
    entry_paths = [entry["path"] for entry in normalized_entries]
    coverage_complete = (
        coverage_basis == "git_status_porcelain_v1_z"
        and entry_paths == sorted(observed_paths)
        and not excluded_required
        and all(
            _entry_is_replayable(entry)
            for entry in normalized_entries
            if entry["required"]
        )
    )
    status_hash = _sha256_json(normalized_entries)
    identity = {
        "repo_id": repo_id,
        "base_commit": base_commit,
        "status_hash": status_hash,
        "entries": normalized_entries,
        "excluded_required_paths": excluded_required,
        "coverage_complete": coverage_complete,
        "source_refs": sorted(source_refs, key=lambda item: (
            item["record_ref"], item["content_hash"], item["revision"]
        )),
        "coverage_basis": coverage_basis,
        "observed_status_hash": observed_status_hash,
        "observed_paths": sorted(observed_paths),
    }
    identity_hash = _sha256_json(identity)
    record = CodePatchManifestRecord(
        manifest_id=f"code-patch-manifest-{identity_hash}",
        repo_id=repo_id,
        base_commit=base_commit,
        status_hash=status_hash,
        entries=normalized_entries,
        excluded_required_paths=excluded_required,
        coverage_complete=coverage_complete,
        source_refs=identity["source_refs"],
        coverage_basis=coverage_basis,
        observed_status_hash=observed_status_hash,
        observed_paths=identity["observed_paths"],
    )
    write = RecordRepository(ws, actor=actor).write(
        "code_patch_manifests",
        record,
        body="# Code Patch Manifest\n\nImmutable replay inputs for a dirty code state.\n",
    )
    return CodePatchManifestCapture(
        record=record,
        pinned_ref=PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        ),
        blob_captures=tuple(captures),
        write_status=write.status,
    )


def _capture_entry(
    ws: WorkspacePaths,
    request: PatchEntryRequest,
    normalized_path: str,
    actor: RecordActor,
) -> tuple[dict, ArtifactBlobCapture | None]:
    change_kinds = sorted(set(request.change_kinds))
    if not change_kinds or not set(change_kinds) <= _CHANGE_KINDS:
        raise ValueError(f"unknown or empty change_kinds for {normalized_path}")
    deleted = bool(request.deleted or "deleted" in change_kinds)
    submodule = "submodule" in change_kinds
    before_sha256 = request.before_sha256.strip().lower()
    submodule_commit = request.submodule_commit.strip().lower()
    excluded_reason = request.excluded_reason.strip()
    if before_sha256 and not _SHA256_PATTERN.fullmatch(before_sha256):
        raise ValueError(f"before_sha256 must be a SHA-256 digest for {normalized_path}")
    if deleted and not before_sha256:
        raise ValueError(f"deleted path requires before_sha256: {normalized_path}")
    if submodule and not _COMMIT_PATTERN.fullmatch(submodule_commit):
        raise ValueError(f"submodule path requires an exact commit: {normalized_path}")
    if excluded_reason:
        return (
            _entry_payload(
                request,
                normalized_path,
                change_kinds,
                deleted=deleted,
                before_sha256=before_sha256,
                submodule_commit=submodule_commit,
                excluded_reason=excluded_reason,
            ),
            None,
        )
    if deleted or submodule:
        return (
            _entry_payload(
                request,
                normalized_path,
                change_kinds,
                deleted=deleted,
                before_sha256=before_sha256,
                submodule_commit=submodule_commit,
            ),
            None,
        )
    if not request.source_path:
        raise ValueError(f"changed path requires source bytes or an exclusion: {normalized_path}")
    capture = capture_artifact_bytes(ws, request.source_path, actor=actor)
    return (
        _entry_payload(
            request,
            normalized_path,
            change_kinds,
            deleted=False,
            before_sha256=before_sha256,
            submodule_commit="",
            blob_receipt_ref=capture.pinned_ref.record_ref,
            blob_receipt_hash=capture.pinned_ref.content_hash,
            blob_receipt_revision=capture.pinned_ref.revision,
            byte_sha256=capture.record.byte_sha256,
            byte_length=capture.record.byte_length,
        ),
        capture,
    )


def _entry_payload(
    request: PatchEntryRequest,
    path: str,
    change_kinds: list[str],
    *,
    deleted: bool,
    before_sha256: str,
    submodule_commit: str,
    excluded_reason: str = "",
    blob_receipt_ref: str = "",
    blob_receipt_hash: str = "",
    blob_receipt_revision: int = 0,
    byte_sha256: str = "",
    byte_length: int = 0,
    index_blob_receipt_ref: str = "",
    index_blob_receipt_hash: str = "",
    index_blob_receipt_revision: int = 0,
    index_byte_sha256: str = "",
    index_byte_length: int = 0,
) -> dict:
    return {
        "path": path,
        "change_kinds": change_kinds,
        "required": bool(request.required),
        "deleted": deleted,
        "before_sha256": before_sha256,
        "submodule_commit": submodule_commit,
        "blob_receipt_ref": blob_receipt_ref,
        "blob_receipt_hash": blob_receipt_hash,
        "blob_receipt_revision": blob_receipt_revision,
        "byte_sha256": byte_sha256,
        "byte_length": byte_length,
        "index_blob_receipt_ref": index_blob_receipt_ref,
        "index_blob_receipt_hash": index_blob_receipt_hash,
        "index_blob_receipt_revision": index_blob_receipt_revision,
        "index_byte_sha256": index_byte_sha256,
        "index_byte_length": index_byte_length,
        "excluded_reason": excluded_reason,
    }


def _entry_is_replayable(entry: dict) -> bool:
    if entry["excluded_reason"]:
        return False
    if entry["deleted"]:
        return bool(entry["before_sha256"])
    if "submodule" in entry["change_kinds"]:
        return bool(entry["submodule_commit"])
    return bool(
        entry["blob_receipt_ref"]
        and entry["blob_receipt_hash"]
        and entry["blob_receipt_revision"] > 0
        and entry["byte_sha256"]
    )


def _safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise ValueError("patch entry path must be a non-empty POSIX relative path")
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts or any(":" in part for part in path.parts):
        raise ValueError(f"patch entry path must stay relative: {value}")
    normalized = path.as_posix()
    if normalized in {".", ""}:
        raise ValueError("patch entry path must name a file")
    return normalized


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_source_refs(
    ws: WorkspacePaths,
    values: list[PinnedRecordRef | Mapping[str, object]],
) -> list[dict]:
    refs: set[PinnedRecordRef] = set()
    for value in values:
        if isinstance(value, PinnedRecordRef):
            pinned = value
        elif isinstance(value, Mapping):
            pinned = PinnedRecordRef(
                record_ref=str(value.get("record_ref") or ""),
                content_hash=str(value.get("content_hash") or ""),
                revision=value.get("revision"),
            )
        else:
            raise TypeError("code patch source refs must be exact pinned refs")
        get_record_version(ws, pinned)
        refs.add(pinned)
    return [asdict(item) for item in sorted(refs)]
