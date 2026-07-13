# Compatibility shard 5 for codex_facade.
from __future__ import annotations

def _record_ref_for_slot(slot: str, record: Any) -> str:
    fields = {
        "source_asset": ("source_asset", "asset_id"),
        "reference_location": ("reference_location", "location_id"),
        "artifact": ("artifact", "artifact_id"),
        "evidence": ("evidence", "evidence_id"),
        "physics_object": ("physics_object", "object_id"),
        "object_relation": ("object_relation", "relation_id"),
        "sensemaking_report": ("sensemaking_report", "report_id"),
        "proof_obligation": ("proof_obligation", "obligation_id"),
        "tool_recipe": ("tool_recipe", "recipe_id"),
        "code_state": ("code_state", "code_state_id"),
        "tool_run": ("tool_run", "run_id"),
        "validation_contract": ("validation_contract", "contract_id"),
        "validation_result": ("validation_result", "result_id"),
    }
    prefix, attr = fields[slot]
    return f"{prefix}:{getattr(record, attr)}"

def _pop_required(data: dict[str, Any], key: str) -> str:
    value = str(data.pop(key, "") or "").strip()
    if not value:
        raise ValueError(f"payload.{key} is required")
    return value

def _pop_str(data: dict[str, Any], key: str, default: str) -> str:
    return str(data.pop(key, default) or "")

def _pop_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.pop(key, None)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def _pop_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.pop(key, None)
    return value if isinstance(value, dict) else {}

def _require_claim(claim_id: str, slot: str) -> str:
    if not claim_id:
        raise ValueError(f"{slot} requires an active claim_id")
    return claim_id

def _normalize_artifact_uri(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for prefix in ("local:file:", "path:", "file:"):
        if lowered.startswith(prefix) and not lowered.startswith("file://"):
            rest = text[len(prefix) :].strip()
            if _looks_like_windows_drive_path(rest):
                return "file:///" + rest.replace("\\", "/")
            if rest.startswith(("/", "\\")):
                return "file://" + rest.replace("\\", "/")
            return rest or text
    return text

def _looks_like_windows_drive_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", str(value or "")))

def _enrich_code_state_runtime(
    *,
    worktree_path: str,
    changed_files: list[str],
    runtime_environment: dict[str, Any],
) -> dict[str, Any]:
    runtime = dict(runtime_environment or {})
    runtime.setdefault("changed_files_relevant", changed_files)
    status_lines = _git_status_lines(worktree_path)
    runtime.setdefault("dirty_status_summary", status_lines)
    runtime.setdefault("changed_files_tracking", _changed_file_tracking(worktree_path, changed_files, status_lines))
    runtime.setdefault("clean_reproducibility_anchor", not status_lines)
    if status_lines:
        runtime.setdefault(
            "dirty_reproducibility_note",
            "source tree is dirty; this code_state is not a clean reproducibility anchor",
        )
    return runtime

def _git_status_lines(worktree_path: str) -> list[str]:
    root = _git_root(worktree_path)
    if root is None:
        return []
    result = _run_git(root, ["status", "--porcelain=v1"])
    return [line for line in result.splitlines() if line.strip()]

def _changed_file_tracking(worktree_path: str, changed_files: list[str], status_lines: list[str]) -> list[dict[str, Any]]:
    if not changed_files:
        return []
    root = _git_root(worktree_path)
    status_by_path = _status_by_path(status_lines)
    rows: list[dict[str, Any]] = []
    for value in changed_files:
        rel_path = _relative_git_path(root, value)
        status = status_by_path.get(rel_path, "")
        rows.append(
            {
                "path": value,
                "git_path": rel_path,
                "tracked": _is_tracked(root, rel_path) if root is not None else False,
                "status": status or "clean_or_not_reported_by_git_status",
                "untracked": status.startswith("??"),
            }
        )
    return rows

def _git_root(worktree_path: str) -> Path | None:
    worktree = Path(worktree_path).expanduser()
    result = _run_git(worktree, ["rev-parse", "--show-toplevel"])
    return Path(result) if result else None

def _run_git(cwd: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()

def _status_by_path(status_lines: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in status_lines:
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        mapping[path.replace("\\", "/")] = status
    return mapping

def _relative_git_path(root: Path | None, value: str) -> str:
    text = _normalize_artifact_uri(str(value or "").strip())
    if text.startswith("file:///"):
        text = text[len("file:///") :]
    elif text.startswith("file://"):
        text = text[len("file://") :]
    path = Path(text)
    if root is not None:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except (OSError, ValueError):
            pass
    return text.replace("\\", "/")

def _is_tracked(root: Path | None, git_path: str) -> bool:
    if root is None or not git_path:
        return False
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", git_path],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True
