"""Stable Git status, index, and worktree capture for code patch manifests."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from brain.v5.artifact_blobs import (
    ArtifactBlobCapture,
    capture_artifact_bytes,
    capture_artifact_content,
)
from brain.v5.code_patch_manifests import (
    CodePatchManifestCapture,
    PatchEntryRequest,
    _entry_payload,
    _safe_relative_path,
    _write_manifest,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor


@dataclass(frozen=True)
class _GitStatusEntry:
    path: str
    index_status: str
    worktree_status: str


def capture_git_patch_manifest(
    ws: WorkspacePaths,
    *,
    repo_path: str | os.PathLike[str],
    repo_id: str,
    actor: RecordActor,
    source_refs: list[dict],
) -> CodePatchManifestCapture:
    repo = Path(repo_path).expanduser().resolve(strict=True)
    if not repo.is_dir():
        raise ValueError("repo_path must be a Git working tree directory")
    base_commit = _git(repo, "rev-parse", "HEAD").decode("ascii").strip().lower()
    status_before = _git_status(repo)
    status_entries = _parse_status(status_before)
    if not status_entries:
        raise ValueError("Git working tree has no patch state to capture")

    entries: list[dict] = []
    captures: list[ArtifactBlobCapture] = []
    for status in status_entries:
        entry, entry_captures = _capture_status_entry(ws, repo, status, actor)
        entries.append(entry)
        captures.extend(entry_captures)

    status_after = _git_status(repo)
    final_commit = _git(repo, "rev-parse", "HEAD").decode("ascii").strip().lower()
    if status_after != status_before or final_commit != base_commit:
        raise RuntimeError("Git repository changed while the patch manifest was captured")
    for entry in entries:
        if "submodule" not in entry["change_kinds"]:
            continue
        commit, dirty = _submodule_snapshot(repo / Path(entry["path"]))
        if dirty or commit != entry["submodule_commit"]:
            raise RuntimeError("Git submodule changed while the patch manifest was captured")
    observed_paths = sorted(status.path for status in status_entries)
    return _write_manifest(
        ws,
        repo_id=repo_id,
        base_commit=base_commit,
        normalized_entries=entries,
        captures=captures,
        actor=actor,
        source_refs=source_refs,
        coverage_basis="git_status_porcelain_v1_z",
        observed_status_hash=hashlib.sha256(status_before).hexdigest(),
        observed_paths=observed_paths,
    )


def _capture_status_entry(
    ws: WorkspacePaths,
    repo: Path,
    status: _GitStatusEntry,
    actor: RecordActor,
) -> tuple[dict, list[ArtifactBlobCapture]]:
    path = _safe_relative_path(status.path)
    request = PatchEntryRequest(path=path, change_kinds=())
    index_changed = status.index_status not in {" ", "?"}
    worktree_changed = status.worktree_status not in {" ", "?"}
    untracked = status.index_status == "?" and status.worktree_status == "?"
    change_kinds: list[str] = []
    if index_changed:
        change_kinds.append("staged")
    if worktree_changed:
        change_kinds.append("unstaged")
    if untracked:
        change_kinds.append("required_untracked")

    index_mode, index_object = _index_entry(repo, path)
    submodule = index_mode == "160000"
    target = repo / Path(path)
    final_exists = target.exists() or target.is_symlink()
    deleted = not final_exists and not submodule
    before_bytes = _git_optional(repo, "show", f"HEAD:{path}")
    before_sha256 = hashlib.sha256(before_bytes).hexdigest() if before_bytes is not None else ""
    captures: list[ArtifactBlobCapture] = []

    if submodule:
        change_kinds.append("submodule")
        submodule_commit, submodule_dirty = _submodule_snapshot(target)
        if submodule_dirty:
            raise ValueError(
                f"dirty submodule bytes are not captured by a gitlink manifest: {path}"
            )
        submodule_commit = submodule_commit or index_object
        return (
            _entry_payload(
                request,
                path,
                sorted(set(change_kinds)),
                deleted=False,
                before_sha256=before_sha256,
                submodule_commit=submodule_commit,
            ),
            captures,
        )

    index_capture = None
    if index_changed and status.index_status != "D":
        index_bytes = _git(repo, "show", f":{path}")
        index_capture = capture_artifact_content(ws, index_bytes, actor=actor)
        captures.append(index_capture)
        if b"\x00" in index_bytes:
            change_kinds.append("binary")

    worktree_capture = None
    if final_exists:
        if target.is_symlink():
            worktree_bytes = os.readlink(target).encode("utf-8")
            worktree_capture = capture_artifact_content(ws, worktree_bytes, actor=actor)
        else:
            worktree_capture = capture_artifact_bytes(ws, target, actor=actor)
            worktree_bytes = Path(worktree_capture.blob_path).read_bytes()
        captures.append(worktree_capture)
        if b"\x00" in worktree_bytes:
            change_kinds.append("binary")
    else:
        change_kinds.append("deleted")
        if not before_sha256:
            raise ValueError(f"deleted Git path has no base bytes: {path}")

    return (
        _entry_payload(
            request,
            path,
            sorted(set(change_kinds)),
            deleted=deleted,
            before_sha256=before_sha256,
            submodule_commit="",
            blob_receipt_ref=worktree_capture.pinned_ref.record_ref if worktree_capture else "",
            blob_receipt_hash=worktree_capture.pinned_ref.content_hash if worktree_capture else "",
            blob_receipt_revision=worktree_capture.pinned_ref.revision if worktree_capture else 0,
            byte_sha256=worktree_capture.record.byte_sha256 if worktree_capture else "",
            byte_length=worktree_capture.record.byte_length if worktree_capture else 0,
            index_blob_receipt_ref=index_capture.pinned_ref.record_ref if index_capture else "",
            index_blob_receipt_hash=index_capture.pinned_ref.content_hash if index_capture else "",
            index_blob_receipt_revision=index_capture.pinned_ref.revision if index_capture else 0,
            index_byte_sha256=index_capture.record.byte_sha256 if index_capture else "",
            index_byte_length=index_capture.record.byte_length if index_capture else 0,
        ),
        captures,
    )


def _git_status(repo: Path) -> bytes:
    return _git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=none",
    )


def _parse_status(payload: bytes) -> list[_GitStatusEntry]:
    tokens = payload.split(b"\0")
    entries: list[_GitStatusEntry] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        if len(token) < 4 or token[2:3] != b" ":
            raise ValueError("unsupported Git porcelain status record")
        xy = token[:2].decode("ascii")
        if "U" in xy or xy in {"AA", "DD"}:
            raise ValueError("unmerged Git paths cannot form a reproducible patch manifest")
        path = os.fsdecode(token[3:])
        if xy[0] in {"R", "C"}:
            if index >= len(tokens) or not tokens[index]:
                raise ValueError("incomplete Git rename/copy status record")
            index += 1
            raise ValueError("Git rename/copy capture is not yet supported")
        entries.append(
            _GitStatusEntry(
                path=_safe_relative_path(path),
                index_status=xy[0],
                worktree_status=xy[1],
            )
        )
    if len({entry.path for entry in entries}) != len(entries):
        raise ValueError("Git status contains duplicate logical paths")
    return sorted(entries, key=lambda item: item.path)


def _index_entry(repo: Path, path: str) -> tuple[str, str]:
    payload = _git(repo, "ls-files", "--stage", "-z", "--", path)
    if not payload:
        return "", ""
    header = payload.split(b"\t", 1)[0].decode("ascii")
    parts = header.split()
    if len(parts) != 3:
        raise ValueError(f"invalid Git index entry for {path}")
    return parts[0], parts[1]


def _worktree_submodule_commit(path: Path) -> str:
    if not path.is_dir():
        return ""
    try:
        return _git(path, "rev-parse", "HEAD").decode("ascii").strip().lower()
    except subprocess.CalledProcessError:
        return ""


def _submodule_dirty(path: Path) -> bool:
    return _submodule_snapshot(path)[1]


def _submodule_snapshot(path: Path) -> tuple[str, bool]:
    if not path.is_dir():
        return "", False
    try:
        commit = _git(path, "rev-parse", "HEAD").decode("ascii").strip().lower()
        dirty = bool(
            _git(path, "status", "--porcelain=v1", "-z", "--untracked-files=all")
        )
        return commit, dirty
    except subprocess.CalledProcessError:
        return "", True


def _git_optional(repo: Path, *args: str) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode == 0:
        return result.stdout
    return None


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout
