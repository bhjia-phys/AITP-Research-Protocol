"""Goal continuation and audit packet surfaces.

Write local audit packets so that future agents can read the filesystem
and understand what was done, what passed, what's blocking, and what to
do next — without relying on chat history.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths


def write_goal_continuation(
    ws: WorkspacePaths,
    *,
    objective: str,
    changed_files: list[str] | None = None,
    changed_file_stats: list[dict[str, Any]] | None = None,
    tests_run: list[str] | None = None,
    tests_passed: bool | None = None,
    smoke_commands: list[str] | None = None,
    smoke_passed: bool | None = None,
    readiness_outcome: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
    trust_boundary: str | None = None,
    blocking_backlog: list[str] | None = None,
    notes: str | None = None,
    session_id: str | None = None,
    commit_ref: str | None = None,
    commit_range: str | None = None,
    commits: list[dict[str, Any]] | None = None,
    audit_commands: list[str] | None = None,
) -> dict[str, Any]:
    surface_dir = ws.root / "surfaces" / "goal_continuation"
    surface_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    packet_id = f"goal-continuation-{now.strftime('%Y-%m-%dT%H-%M-%S-%f')}"
    json_path = surface_dir / f"{packet_id}.json"
    md_path = surface_dir / f"{packet_id}.md"
    files = {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(surface_dir / "latest.json"),
        "latest_markdown": str(surface_dir / "latest.md"),
    }
    packet = _build_packet(
        packet_id=packet_id,
        timestamp=now.isoformat(),
        objective=objective,
        changed_files=changed_files or [],
        changed_file_stats=changed_file_stats or [],
        tests_run=tests_run or [],
        tests_passed=tests_passed,
        smoke_commands=smoke_commands or [],
        smoke_passed=smoke_passed,
        readiness_outcome=readiness_outcome,
        next_actions=next_actions or [],
        trust_boundary=trust_boundary or "",
        blocking_backlog=blocking_backlog or [],
        notes=notes or "",
        session_id=session_id or "",
        commit_ref=commit_ref or "",
        commit_range=commit_range or "",
        commits=commits or [],
        audit_commands=audit_commands or [],
        files=files,
    )
    json_path.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_md(packet), encoding="utf-8")
    _update_latest(surface_dir, packet_id, json_path, md_path)
    return packet


def read_latest_goal_continuation(ws: WorkspacePaths) -> dict[str, Any] | None:
    latest_path = ws.root / "surfaces" / "goal_continuation" / "latest.json"
    if not latest_path.exists():
        return None
    return normalize_goal_continuation_packet(json.loads(latest_path.read_text(encoding="utf-8")))


def empty_goal_continuation_packet() -> dict[str, Any]:
    return _build_packet(
        packet_id="goal-continuation-not-found",
        timestamp="not-found",
        objective="No goal continuation packet found.",
        changed_files=[],
        changed_file_stats=[],
        tests_run=[],
        tests_passed=None,
        smoke_commands=[],
        smoke_passed=None,
        readiness_outcome=None,
        next_actions=[],
        trust_boundary="",
        blocking_backlog=[],
        notes="",
        session_id="",
        commit_ref="",
        commit_range="",
        commits=[],
        audit_commands=[],
        files={},
    ) | {"found": False}


def normalize_goal_continuation_packet(payload: dict[str, Any]) -> dict[str, Any]:
    """Coerce older continuation packets to the current read-only contract."""

    if not isinstance(payload, dict):
        payload = {}
    verification = payload.get("verification") if isinstance(payload.get("verification"), dict) else {}
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    readiness = payload.get("readiness_outcome") if isinstance(payload.get("readiness_outcome"), dict) else {}
    packet = _build_packet(
        packet_id=str(payload.get("packet_id") or "goal-continuation-legacy"),
        timestamp=str(payload.get("timestamp") or "unknown"),
        objective=str(payload.get("objective") or payload.get("goal") or "Legacy goal continuation packet."),
        changed_files=_as_list(payload.get("changed_files")),
        changed_file_stats=_as_list(payload.get("changed_file_stats")),
        tests_run=_as_list(verification.get("tests_run") or payload.get("tests_run")),
        tests_passed=_as_optional_bool(verification.get("tests_passed", payload.get("tests_passed"))),
        smoke_commands=_as_list(verification.get("smoke_commands") or payload.get("smoke_commands")),
        smoke_passed=_as_optional_bool(verification.get("smoke_passed", payload.get("smoke_passed"))),
        readiness_outcome=readiness,
        next_actions=_as_list(payload.get("next_actions")),
        trust_boundary=str(payload.get("trust_boundary") or ""),
        blocking_backlog=_as_list(payload.get("blocking_backlog")),
        notes=str(payload.get("notes") or ""),
        session_id=str(payload.get("session_id") or ""),
        commit_ref=str(payload.get("commit_ref") or ""),
        commit_range=str(payload.get("commit_range") or ""),
        commits=_as_list(payload.get("commits")),
        audit_commands=_as_list(payload.get("audit_commands")),
        files={str(k): str(v) for k, v in files.items()},
    )
    packet["found"] = bool(payload.get("found", True))
    return packet


def list_goal_continuations(ws: WorkspacePaths) -> list[dict[str, Any]]:
    surface_dir = ws.root / "surfaces" / "goal_continuation"
    if not surface_dir.exists():
        return []
    packets = []
    for p in sorted(surface_dir.glob("goal-continuation-*.json")):
        try:
            packets.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return packets


def _build_packet(
    *,
    packet_id: str,
    timestamp: str,
    objective: str,
    changed_files: list[str],
    changed_file_stats: list[dict[str, Any]],
    tests_run: list[str],
    tests_passed: bool | None,
    smoke_commands: list[str],
    smoke_passed: bool | None,
    readiness_outcome: dict[str, Any] | None,
    next_actions: list[str],
    trust_boundary: str,
    blocking_backlog: list[str],
    notes: str,
    session_id: str,
    commit_ref: str,
    commit_range: str,
    commits: list[dict[str, Any]],
    audit_commands: list[str],
    files: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "kind": "goal_continuation_packet",
        "packet_id": packet_id,
        "timestamp": timestamp,
        "session_id": session_id,
        "commit_ref": commit_ref,
        "commit_range": commit_range,
        "commits": [_normalize_commit(c) for c in commits],
        "objective": objective,
        "changed_files": changed_files,
        "changed_file_stats": [_normalize_file_stat(s) for s in changed_file_stats],
        "verification": {
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "smoke_commands": smoke_commands,
            "smoke_passed": smoke_passed,
        },
        "audit_commands": audit_commands,
        "readiness_outcome": _compact_readiness(readiness_outcome),
        "next_actions": next_actions,
        "trust_boundary": trust_boundary,
        "blocking_backlog": blocking_backlog,
        "notes": notes,
        "files": files,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "truth_source": False,
    }


def _compact_readiness(outcome: dict[str, Any] | None) -> dict[str, Any]:
    if not outcome:
        return {}
    return {
        "completion_status": str(outcome.get("completion_status") or ""),
        "blocking_gaps": list(outcome.get("blocking_gaps") or []),
        "can_update_claim_trust": bool(outcome.get("can_update_claim_trust") is True),
        "can_update_kernel_state": bool(outcome.get("can_update_kernel_state") is True),
        "semantic_lossless_proven": bool(outcome.get("semantic_lossless_proven") is True),
    }


def _render_md(packet: dict[str, Any]) -> str:
    lines = [
        f"# Goal Continuation: {packet['packet_id']}",
        "",
        f"**Timestamp:** {packet['timestamp']}",
        f"**Session:** {packet['session_id'] or 'unknown'}",
        f"**Commit:** {packet['commit_ref'] or 'unknown'}",
    ]
    if packet.get("commit_range"):
        lines.append(f"**Commit range:** {packet['commit_range']}")
    lines.extend(["", "## Objective", "", str(packet["objective"]), ""])
    commits = packet.get("commits") or []
    if commits:
        lines.extend(["## Commits", ""])
        for commit in commits:
            stat = _commit_stat_text(commit)
            lines.append(f"- `{commit.get('hash', '')}` {commit.get('subject', '')}{stat}")
        lines.append("")
    changed = packet.get("changed_files") or []
    if changed:
        lines.extend(["## Changed Files", ""])
        for f in changed:
            lines.append(f"- `{f}`")
        lines.append("")
    v = packet.get("verification") or {}
    lines.extend(["## Verification", ""])
    tests = v.get("tests_run") or []
    if tests:
        lines.append("Tests run:")
        for t in tests:
            lines.append(f"- `{t}`")
        lines.append("")
    lines.append(f"Tests passed: `{v.get('tests_passed')}`")
    smokes = v.get("smoke_commands") or []
    if smokes:
        lines.append("")
        lines.append("Smoke commands:")
        for s in smokes:
            lines.append(f"- `{s}`")
    lines.append("")
    lines.append(f"Smoke passed: `{v.get('smoke_passed')}`")
    audit_commands = packet.get("audit_commands") or []
    if audit_commands:
        lines.extend(["", "Audit commands:", ""])
        for command in audit_commands:
            lines.append(f"- `{command}`")
    r = packet.get("readiness_outcome") or {}
    if r:
        lines.extend(["", "## Readiness Outcome", ""])
        lines.append(f"- completion_status: `{r.get('completion_status', '')}`")
        lines.append(f"- blocking_gaps: {r.get('blocking_gaps', [])}")
        lines.append(f"- can_update_claim_trust: `{r.get('can_update_claim_trust')}`")
        lines.append(f"- semantic_lossless_proven: `{r.get('semantic_lossless_proven')}`")
    next_acts = packet.get("next_actions") or []
    if next_acts:
        lines.extend(["", "## Next Actions", ""])
        for a in next_acts:
            lines.append(f"- {a}")
        lines.append("")
    trust = packet.get("trust_boundary") or ""
    if trust:
        lines.extend(["## Trust Boundary", "", trust, ""])
    backlog = packet.get("blocking_backlog") or []
    if backlog:
        lines.extend(["## Blocking Backlog", ""])
        for b in backlog:
            lines.append(f"- {b}")
        lines.append("")
    notes = packet.get("notes") or ""
    if notes:
        lines.extend(["## Notes", "", notes, ""])
    lines.extend(["---", "*This is an orientation-only surface. Do not update claim trust or kernel state from it.*", ""])
    return "\n".join(lines)


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _as_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _normalize_commit(commit: dict[str, Any]) -> dict[str, Any]:
    return {
        "hash": str(commit.get("hash") or ""),
        "subject": str(commit.get("subject") or ""),
        "files_changed": int(commit.get("files_changed") or 0),
        "insertions": int(commit.get("insertions") or 0),
        "deletions": int(commit.get("deletions") or 0),
    }


def _normalize_file_stat(stat: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(stat.get("path") or ""),
        "status": str(stat.get("status") or ""),
        "insertions": int(stat.get("insertions") or 0),
        "deletions": int(stat.get("deletions") or 0),
    }


def _commit_stat_text(commit: dict[str, Any]) -> str:
    parts = []
    if commit.get("files_changed"):
        parts.append(f"{commit['files_changed']} files")
    if commit.get("insertions"):
        parts.append(f"+{commit['insertions']}")
    if commit.get("deletions"):
        parts.append(f"-{commit['deletions']}")
    return f" ({', '.join(parts)})" if parts else ""


def _update_latest(
    surface_dir: Path,
    packet_id: str,
    json_path: Path,
    md_path: Path,
) -> None:
    latest_json = surface_dir / "latest.json"
    latest_md = surface_dir / "latest.md"
    if latest_json.exists():
        latest_json.unlink()
    if latest_md.exists():
        latest_md.unlink()
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
