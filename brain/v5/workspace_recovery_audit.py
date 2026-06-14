"""Workspace-level recovery audit for topic/session restore readiness."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from brain.v5.claim_relation_map import build_claim_relation_map, build_claim_relation_registry_index
from brain.v5.markdown import write_text_atomic
from brain.v5.models import SessionBinding
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records
from brain.v5.workspace_migration_discovery import latest_workspace_migration_plan, latest_workspace_recovery_audit


def build_workspace_recovery_audit(
    ws: WorkspacePaths,
    *,
    migration_plan_path: str | Path | None = None,
    topics: list[str] | None = None,
) -> dict[str, Any]:
    """Audit whether topics have enough typed state for restart recovery."""

    selected_topics = {str(topic) for topic in (topics or []) if str(topic)}
    if not migration_plan_path and not selected_topics:
        saved = latest_workspace_recovery_audit(ws)
        if saved:
            payload = _load_json(saved)
            if isinstance(payload, dict) and payload.get("kind") == "aitp_workspace_recovery_audit":
                return {**payload, "recovery_audit_source": str(saved)}

    plan_path = Path(migration_plan_path) if migration_plan_path else latest_workspace_migration_plan(ws)
    plan_topics = _migration_plan_topics(plan_path)
    topic_ids = sorted(selected_topics or (set(_canonical_topic_ids(ws)) | set(plan_topics.keys())))
    sessions_by_topic = _sessions_by_topic(ws)
    relation_index = build_claim_relation_registry_index(ws) if len(topic_ids) > 1 else None
    rows = [
        _topic_recovery_row(
            ws,
            topic,
            sessions_by_topic.get(topic, []),
            plan_topics.get(topic, {}),
            relation_index=relation_index,
        )
        for topic in topic_ids
    ]
    status_counts = Counter(str(row["recovery_status"]) for row in rows)
    action_counts = Counter(str(row.get("topic_plan_action") or "unknown") for row in rows)
    return {
        "kind": "aitp_workspace_recovery_audit",
        "canonical_topics_root": str(ws.base),
        "canonical_store": str(ws.root),
        "migration_plan_source": str(plan_path or ""),
        "topics": sorted(selected_topics),
        "summary": {
            "topic_count": len(rows),
            "recovery_ready_count": status_counts.get("recovery_ready", 0),
            "recovery_gap_count": len(rows) - status_counts.get("recovery_ready", 0),
            "status_counts": dict(sorted(status_counts.items())),
            "topic_plan_action_counts": dict(sorted(action_counts.items())),
            "topics_with_active_claim": sum(1 for row in rows if row.get("active_claim_id")),
            "topics_with_relation_map": sum(1 for row in rows if row.get("has_relation_map")),
            "topics_blocked_by_migration_review": sum(1 for row in rows if row.get("migration_review_required")),
        },
        "topic_rows": rows,
        "truth_source": "typed_session_bindings_and_relation_maps",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def compact_workspace_recovery_audit(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    rows = [row for row in payload.get("topic_rows", []) if isinstance(row, dict)]
    gaps = [row for row in rows if row.get("recovery_status") != "recovery_ready"]
    compact_rows = [_compact_recovery_row(row) for row in rows[:20]]
    result = {
        "kind": "aitp_workspace_recovery_audit_progress",
        "canonical_topics_root": payload.get("canonical_topics_root", ""),
        "topic_count": summary.get("topic_count", 0),
        "recovery_ready_count": summary.get("recovery_ready_count", 0),
        "recovery_gap_count": summary.get("recovery_gap_count", 0),
        "status_counts": summary.get("status_counts", {}),
        "topics_with_active_claim": summary.get("topics_with_active_claim", 0),
        "topics_with_relation_map": summary.get("topics_with_relation_map", 0),
        "topics_blocked_by_migration_review": summary.get("topics_blocked_by_migration_review", 0),
        "top_gap_topics": [str(row.get("topic_id") or "") for row in gaps[:20]],
        "topic_rows": compact_rows,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if len(compact_rows) == 1:
        result["selected_topic"] = compact_rows[0]
    return result


def render_workspace_recovery_audit_markdown(payload: dict[str, Any], *, max_rows: int = 160) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP Workspace Recovery Audit",
        "",
        "This read-only audit checks whether each topic has restartable session, active claim, and relation-map state.",
        "",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Topics: `{summary.get('topic_count', 0)}`",
        f"- Recovery ready: `{summary.get('recovery_ready_count', 0)}`",
        f"- Recovery gaps: `{summary.get('recovery_gap_count', 0)}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in (summary.get("status_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Topic Rows",
            "",
            "| Topic | Status | Selection | Session | Active Claim | Relation Map | Next Action | Migration Action |",
            "|---|---|---|---|---|---:|---|---|",
        ]
    )
    for row in payload.get("topic_rows", [])[:max_rows]:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {topic} | {status} | {selection} | `{session}` | `{claim}` | {relation} | {next_action} | {plan} |".format(
                topic=_cell(row.get("topic_id", "")),
                status=_cell(row.get("recovery_status", "")),
                selection=_cell(row.get("recovery_selection_source", "")),
                session=_cell(row.get("session_id", "")),
                claim=_cell(row.get("active_claim_id", "")),
                relation=str(row.get("has_relation_map", False)).lower(),
                next_action=_cell(row.get("next_valid_action", "")),
                plan=_cell(row.get("topic_plan_action", "")),
            )
        )
    if int(summary.get("topic_count") or 0) > max_rows:
        lines.extend(["", f"Showing first `{max_rows}` rows. Use the JSON audit for the complete topic list."])
    lines.extend(["", "This surface is orientation-only and cannot update claim trust.", ""])
    return "\n".join(lines)


def write_workspace_recovery_audit(
    payload: dict[str, Any],
    *,
    json_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    if json_path:
        path = Path(json_path)
        write_text_atomic(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        result["json_path"] = str(path)
    if report_path:
        path = Path(report_path)
        write_text_atomic(path, render_workspace_recovery_audit_markdown(payload))
        result["report_path"] = str(path)
    return result


def _canonical_topic_ids(ws: WorkspacePaths) -> list[str]:
    out: set[str] = set()
    typed_topics_root = ws.root / "topics"
    if typed_topics_root.exists():
        for child in typed_topics_root.iterdir():
            if child.is_dir():
                out.add(child.name)
    topics_root = ws.base
    if topics_root.exists():
        for child in topics_root.iterdir():
            if child.is_dir() and child.name != ".aitp" and (child / "topic.md").exists():
                out.add(child.name)
    return sorted(out)


def _migration_plan_topics(path: str | Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return {
        str(row.get("topic_id") or ""): row
        for row in payload.get("topic_rows", [])
        if isinstance(row, dict) and str(row.get("topic_id") or "")
    }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _sessions_by_topic(ws: WorkspacePaths) -> dict[str, list[SessionBinding]]:
    rows: dict[str, list[SessionBinding]] = defaultdict(list)
    for session in list_valid_records(ws.root / "runtime" / "sessions", SessionBinding):
        rows[session.topic_id].append(session)
    for sessions in rows.values():
        sessions.sort(key=lambda item: item.session_id)
    return rows


def _topic_recovery_row(
    ws: WorkspacePaths,
    topic_id: str,
    sessions: list[SessionBinding],
    plan_row: dict[str, Any],
    *,
    relation_index: dict[str, dict[str, list[Any]]] | None = None,
) -> dict[str, Any]:
    runtime_focus = _runtime_topic_state_focus(ws, topic_id)
    session, selection = _select_recovery_session(sessions, runtime_focus)
    action = str(plan_row.get("plan_action") or "")
    base = {
        "topic_id": topic_id,
        "topic_plan_action": action,
        "migration_review_required": bool(action and action != "no_action"),
        "session_count": len(sessions),
        "session_id": session.session_id if session else "",
        "active_claim_id": session.active_claim if session else "",
        "runtime_topic_state_path": runtime_focus.get("path", ""),
        "runtime_topic_state_status": runtime_focus.get("status", ""),
        "runtime_topic_state_session_id": runtime_focus.get("session_id", ""),
        "runtime_topic_state_active_claim_id": runtime_focus.get("active_claim_id", ""),
        "recovery_selection_source": selection.get("source", ""),
        "recovery_selection_notes": selection.get("notes", []),
        "has_execution_brief": False,
        "has_relation_map": False,
        "has_current_conclusion": False,
        "has_next_valid_action": False,
        "next_valid_action": "",
        "recovery_status": "no_session",
        "recovery_gap": "",
    }
    if session is None:
        return {**base, "recovery_gap": "no session binding for topic"}
    if not session.active_claim:
        return {**base, "recovery_status": "no_active_claim", "recovery_gap": "latest session has no active claim"}
    try:
        relation = build_claim_relation_map(ws, session.session_id, registry_index=relation_index)
    except Exception as exc:  # pragma: no cover - defensive audit path
        return {
            **base,
            "recovery_status": "brief_or_relation_error",
            "recovery_gap": f"{type(exc).__name__}: {exc}",
        }
    conclusion = relation.get("current_conclusion") if isinstance(relation.get("current_conclusion"), dict) else {}
    next_actions = relation.get("next_valid_actions") if isinstance(relation.get("next_valid_actions"), list) else []
    selection_gap = _selection_gap(session, runtime_focus, selection)
    status = (
        "recovery_source_divergence"
        if selection_gap
        else "recovery_ready"
        if conclusion.get("can_say") and conclusion.get("cannot_say") and next_actions
        else "relation_boundary_gap"
    )
    return {
        **base,
        "has_execution_brief": True,
        "has_relation_map": relation.get("kind") == "claim_relation_map",
        "has_current_conclusion": bool(conclusion.get("can_say") and conclusion.get("cannot_say")),
        "has_next_valid_action": bool(next_actions),
        "next_valid_action": str(next_actions[0]) if next_actions else "",
        "supported_count": len(relation.get("supported_by") or []),
        "limited_count": len(relation.get("limited_by") or []),
        "not_tested_count": len(relation.get("not_tested_by") or []),
        "recovery_status": status,
        "recovery_gap": (
            selection_gap
            if selection_gap
            else "" if status == "recovery_ready" else "missing current conclusion or next valid action"
        ),
    }


def _select_recovery_session(
    sessions: list[SessionBinding],
    runtime_focus: dict[str, str],
) -> tuple[SessionBinding | None, dict[str, Any]]:
    """Choose the session that best represents the recoverable current state.

    Imported legacy sessions can sort after real runtime sessions.  A fresh
    topic_state surface is not a trust source, but it is a useful routing hint
    when it points back to an existing typed session and active claim.
    """

    if not sessions:
        return None, {"source": "no_session", "notes": []}

    notes: list[str] = []
    by_id = {session.session_id: session for session in sessions}
    focus_session_id = str(runtime_focus.get("session_id") or "")
    focus_claim_id = str(runtime_focus.get("active_claim_id") or "")
    if runtime_focus.get("status") == "present":
        if focus_session_id and focus_session_id in by_id:
            candidate = by_id[focus_session_id]
            if focus_claim_id and candidate.active_claim and candidate.active_claim != focus_claim_id:
                notes.append("runtime topic_state active claim differs from typed session active claim")
            return candidate, {"source": "runtime_topic_state_session", "notes": notes}
        if focus_claim_id:
            claim_matches = [session for session in sessions if session.active_claim == focus_claim_id]
            if len(claim_matches) == 1:
                notes.append("runtime topic_state session was not found, but its active claim matched one typed session")
                return claim_matches[0], {"source": "runtime_topic_state_active_claim", "notes": notes}
            if len(claim_matches) > 1:
                notes.append("runtime topic_state active claim matched multiple sessions")
        elif focus_session_id:
            notes.append("runtime topic_state session was not found in typed session bindings")
    elif runtime_focus.get("status"):
        notes.append(f"runtime topic_state ignored: {runtime_focus['status']}")

    with_claim = [session for session in sessions if session.active_claim]
    if with_claim:
        return with_claim[-1], {"source": "session_order_with_active_claim", "notes": notes}
    return sessions[-1], {"source": "session_order_without_active_claim", "notes": notes}


def _runtime_topic_state_focus(ws: WorkspacePaths, topic_id: str) -> dict[str, str]:
    path = ws.topic_dir(topic_id) / "runtime" / "topic_state.json"
    if not path.exists():
        return {"status": "missing", "path": ""}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive audit path
        return {"status": f"unreadable:{type(exc).__name__}", "path": str(path)}
    if not isinstance(payload, dict):
        return {"status": "invalid_payload", "path": str(path)}
    if payload.get("kind") != "topic_state":
        return {"status": "invalid_kind", "path": str(path)}
    payload_topic = str(payload.get("topic_id") or "")
    if payload_topic and payload_topic != topic_id:
        return {
            "status": "topic_mismatch",
            "path": str(path),
            "topic_id": payload_topic,
            "session_id": str(payload.get("session_id") or ""),
            "active_claim_id": str(payload.get("active_claim_id") or ""),
        }
    return {
        "status": "present",
        "path": str(path),
        "topic_id": payload_topic,
        "session_id": str(payload.get("session_id") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
    }


def _selection_gap(
    session: SessionBinding | None,
    runtime_focus: dict[str, str],
    selection: dict[str, Any],
) -> str:
    if session is None:
        return ""
    if runtime_focus.get("status") != "present":
        return ""
    focus_session_id = str(runtime_focus.get("session_id") or "")
    focus_claim_id = str(runtime_focus.get("active_claim_id") or "")
    if focus_session_id and selection.get("source") == "session_order_with_active_claim":
        return "runtime topic_state points to a session that was not recovered from typed session bindings"
    if focus_claim_id and session.active_claim and session.active_claim != focus_claim_id:
        return "runtime topic_state active claim differs from selected typed session active claim"
    return ""


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _compact_recovery_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic_id": str(row.get("topic_id") or ""),
        "recovery_status": str(row.get("recovery_status") or ""),
        "session_id": str(row.get("session_id") or ""),
        "active_claim_id": str(row.get("active_claim_id") or ""),
        "has_relation_map": bool(row.get("has_relation_map")),
        "recovery_selection_source": str(row.get("recovery_selection_source") or ""),
        "next_valid_action": str(row.get("next_valid_action") or ""),
        "recovery_gap": str(row.get("recovery_gap") or ""),
    }
