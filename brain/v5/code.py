"""Code workspace and source-state provenance for AITP v5."""

from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from brain.v5.evidence import record_artifact_ref
from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import CodeStateRecord, CodeWorkspaceRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


def record_code_workspace(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    session_id: str,
    repo_id: str,
    worktree_path: str,
    branch_name: str,
    base_commit: str,
    purpose: str,
    upstream_tracking_branch: str = "",
    write_scope: list[str] | None = None,
    active_claim: str = "",
    active_attempt: str = "",
    status: str = "active",
    cleanup_plan: str = "",
) -> CodeWorkspaceRecord:
    """Record an isolated code workspace used by a topic/session."""

    workspace_id = prefixed_id("code-workspace", f"{repo_id}:{topic_id}:{session_id}:{branch_name}")
    record = CodeWorkspaceRecord(
        workspace_id=workspace_id,
        topic_id=topic_id,
        session_id=session_id,
        repo_id=repo_id,
        worktree_path=worktree_path,
        branch_name=branch_name,
        base_commit=base_commit,
        purpose=purpose,
        upstream_tracking_branch=upstream_tracking_branch,
        write_scope=write_scope or [],
        active_claim=active_claim,
        active_attempt=active_attempt,
        status=status,
        cleanup_plan=cleanup_plan,
    )
    write_record(
        ws.registry_dir("code_workspaces") / f"{workspace_id}.md",
        record,
        body=f"# Code Workspace\n\nRepository: `{repo_id}`\n\nPurpose: {purpose}\n",
    )
    return record


def record_code_state(
    ws: WorkspacePaths,
    *,
    repo_id: str,
    upstream_remote: str,
    upstream_branch: str,
    upstream_commit: str,
    local_branch: str,
    worktree_path: str,
    dirty: bool,
    patch_id: str = "",
    diff_hash: str = "",
    build_config: dict | None = None,
    runtime_environment: dict | None = None,
    linked_records: dict | None = None,
    known_divergence: str = "",
) -> CodeStateRecord:
    """Record the exact code state used for a code-dependent result."""

    basis = ":".join(
        [
            repo_id,
            upstream_remote,
            upstream_branch,
            upstream_commit,
            local_branch,
            patch_id,
            diff_hash,
        ]
    )
    suffix = short_hash(basis, 8)
    code_state_id = f"code-state-{repo_id}-{suffix}"
    record = CodeStateRecord(
        code_state_id=code_state_id,
        repo_id=repo_id,
        upstream_remote=upstream_remote,
        upstream_branch=upstream_branch,
        upstream_commit=upstream_commit,
        local_branch=local_branch,
        worktree_path=worktree_path,
        dirty=dirty,
        patch_id=patch_id,
        diff_hash=diff_hash,
        build_config=build_config or {},
        runtime_environment=runtime_environment or {},
        linked_records=linked_records or {},
        known_divergence=known_divergence,
    )
    write_record(
        ws.registry_dir("code_states") / f"{code_state_id}.md",
        record,
        body=(
            "# Code State\n\n"
            f"Repository: `{repo_id}`\n\n"
            f"Upstream: `{upstream_remote}/{upstream_branch}` at `{upstream_commit}`\n"
        ),
    )
    return record


def capture_code_state_from_git(
    ws: WorkspacePaths,
    *,
    worktree_path: str,
    repo_id: str = "",
    topic_id: str = "",
    claim_id: str = "",
    session_id: str = "",
    build_config: dict | None = None,
    runtime_environment: dict | None = None,
    linked_records: dict | None = None,
    known_divergence: str = "",
    write_patch_artifact: bool = False,
) -> CodeStateRecord:
    """Inspect a git worktree and record an orientation-only code-state snapshot."""

    worktree = Path(worktree_path).expanduser()
    if not worktree.exists():
        raise FileNotFoundError(f"worktree_path does not exist: {worktree_path}")
    root = Path(_git(["rev-parse", "--show-toplevel"], cwd=worktree))
    resolved_repo_id = repo_id or root.name
    local_branch = _git_optional(["branch", "--show-current"], cwd=root) or _git(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        cwd=root,
    )
    head_commit = _git(["rev-parse", "HEAD"], cwd=root)
    upstream_ref = _git_optional(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=root)
    upstream_remote, upstream_branch = _split_upstream(upstream_ref, fallback_branch=local_branch)
    remote_url = _git_optional(["remote", "get-url", upstream_remote], cwd=root) if upstream_remote != "local" else ""
    upstream_ref_commit = _git_optional(["rev-parse", upstream_ref], cwd=root) if upstream_ref else ""
    status_porcelain = _git_optional(["status", "--porcelain=v1"], cwd=root) or ""
    diff_text = _git_optional(["diff", "--full-index", "--binary", "HEAD", "--"], cwd=root) or ""
    dirty = bool(status_porcelain.strip())
    diff_hash = _sha256_text(f"{status_porcelain}\0{diff_text}") if dirty else ""
    patch_id = ""

    runtime = dict(runtime_environment or {})
    runtime.setdefault("capture_tool", "aitp_v5_capture_code_state_auto")
    runtime.setdefault("captured_at", datetime.now(UTC).isoformat())
    runtime.setdefault("git_head_commit", head_commit)
    runtime.setdefault("git_upstream_ref", upstream_ref or "")
    runtime.setdefault("git_upstream_commit", upstream_ref_commit or "")
    runtime.setdefault("git_remote_url", remote_url)
    runtime.setdefault("git_status_porcelain", status_porcelain.splitlines())
    runtime.setdefault("diff_hash_algorithm", "sha256" if diff_hash else "")
    runtime.setdefault("diff_basis", "git status --porcelain=v1 + git diff --full-index --binary HEAD --")

    links = dict(linked_records or {})
    if topic_id:
        links.setdefault("topic_id", topic_id)
    if claim_id:
        links.setdefault("claim_id", claim_id)
    if session_id:
        links.setdefault("session_id", session_id)

    if write_patch_artifact and dirty:
        patch_path = _write_patch_artifact_file(
            ws,
            repo_id=resolved_repo_id,
            diff_hash=diff_hash,
            status_porcelain=status_porcelain,
            diff_text=diff_text,
        )
        runtime.setdefault("patch_artifact_uri", str(patch_path))
        if topic_id and claim_id:
            artifact = record_artifact_ref(
                ws,
                topic_id=topic_id,
                claim_id=claim_id,
                artifact_type="git_patch",
                uri=str(patch_path),
                summary=f"Git diff patch artifact for {resolved_repo_id} at {head_commit[:12]}.",
                size_bytes=patch_path.stat().st_size,
                metadata={
                    "repo_id": resolved_repo_id,
                    "worktree_path": str(root),
                    "diff_hash": diff_hash,
                    "diff_hash_algorithm": "sha256",
                    "includes_untracked_content": False,
                    "can_update_claim_trust": False,
                },
            )
            patch_id = artifact.artifact_id
        else:
            patch_id = f"patch:{patch_path}"

    divergence = known_divergence or _divergence_summary(root, upstream_ref)
    return record_code_state(
        ws,
        repo_id=resolved_repo_id,
        upstream_remote=upstream_remote,
        upstream_branch=upstream_ref or upstream_branch or local_branch or "HEAD",
        upstream_commit=head_commit,
        local_branch=local_branch or "HEAD",
        worktree_path=str(root),
        dirty=dirty,
        patch_id=patch_id,
        diff_hash=diff_hash,
        build_config=build_config,
        runtime_environment=runtime,
        linked_records=links,
        known_divergence=divergence,
    )


def _git(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout.strip()


def _git_optional(args: list[str], *, cwd: Path) -> str:
    try:
        return _git(args, cwd=cwd)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def _split_upstream(upstream_ref: str, *, fallback_branch: str) -> tuple[str, str]:
    if not upstream_ref:
        return "local", fallback_branch or "HEAD"
    if "/" not in upstream_ref:
        return "local", upstream_ref
    remote, branch = upstream_ref.split("/", 1)
    return remote or "local", branch or fallback_branch or "HEAD"


def _divergence_summary(root: Path, upstream_ref: str) -> str:
    if not upstream_ref:
        return "no upstream tracking branch"
    counts = _git_optional(["rev-list", "--left-right", "--count", f"{upstream_ref}...HEAD"], cwd=root)
    if not counts:
        return ""
    parts = counts.split()
    if len(parts) != 2:
        return ""
    behind, ahead = parts
    return f"behind {behind}, ahead {ahead} relative to {upstream_ref}"


def _write_patch_artifact_file(
    ws: WorkspacePaths,
    *,
    repo_id: str,
    diff_hash: str,
    status_porcelain: str,
    diff_text: str,
) -> Path:
    patch_dir = ws.root / "artifacts" / "code_patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    suffix = diff_hash[:16] if diff_hash else short_hash(f"{repo_id}:{status_porcelain}", 16)
    patch_path = patch_dir / f"code-patch-{repo_id}-{suffix}.patch"
    patch_path.write_text(
        (
            "# AITP git patch artifact\n"
            "# Includes tracked-file diff plus git status. Untracked file contents are not embedded.\n\n"
            "## git status --porcelain=v1\n\n"
            f"{status_porcelain}\n\n"
            "## git diff --full-index --binary HEAD --\n\n"
            f"{diff_text}"
        ),
        encoding="utf-8",
    )
    return patch_path


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
