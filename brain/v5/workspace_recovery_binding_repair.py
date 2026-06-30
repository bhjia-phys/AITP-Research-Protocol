"""Conservative repair of topic/session active-claim recovery bindings."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from brain.v5.active_claim_focus import detect_active_claim_focus_drift
from brain.v5.markdown import write_text_atomic
from brain.v5.models import ClaimRecord, SessionBinding, TopicRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, read_record
from brain.v5.workspace import bind_session


def build_workspace_recovery_binding_repair(
    ws: WorkspacePaths,
    *,
    topics: list[str] | None = None,
    session_id: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    """Plan safe active-claim bindings for imported old-store topics."""

    selected = sorted({topic for topic in (topics or []) if topic})
    if not selected:
        selected = sorted(set(_claims_by_topic(ws)) | set(_sessions_by_topic(ws)) | set(_topic_shell_ids(ws)))
    claims_by_topic = _claims_by_topic(ws)
    sessions_by_topic = _sessions_by_topic(ws)
    actions = [
        _repair_action(ws, topic, claims_by_topic.get(topic, []), sessions_by_topic.get(topic, []))
        for topic in selected
    ]
    focus_reconciliation: dict[str, Any] = {}
    if session_id:
        focus_reconciliation = detect_active_claim_focus_drift(
            ws,
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
        if focus_reconciliation.get("not_authoritative_for_current_goal_if_rebind_needed"):
            actions.append(_focus_drift_repair_action(focus_reconciliation))
    counts = Counter(str(action["status"]) for action in actions)
    return {
        "kind": "aitp_workspace_recovery_binding_repair",
        "mode": "plan",
        "canonical_topics_root": str(ws.base),
        "canonical_store": str(ws.root),
        "topics": selected,
        "summary": {
            "action_count": len(actions),
            "applyable_count": sum(1 for action in actions if action.get("applyable")),
            "review_required_count": sum(1 for action in actions if not action.get("applyable")),
            "status_counts": dict(sorted(counts.items())),
        },
        "actions": actions,
        "active_claim_focus_reconciliation": focus_reconciliation,
        "truth_source": "canonical_claims_and_session_bindings",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def apply_workspace_recovery_binding_repair(payload: dict[str, Any], ws: WorkspacePaths) -> dict[str, Any]:
    """Apply only safe single-claim session binding repairs."""

    actions = []
    for action in payload.get("actions", []):
        if not isinstance(action, dict):
            continue
        updated = dict(action)
        if action.get("applyable"):
            existing = _session_by_id(ws, str(action.get("session_id") or ""))
            if existing is not None:
                bind_session(
                    ws,
                    existing.session_id,
                    topic_id=existing.topic_id,
                    context_id=existing.context_id,
                    runtime=existing.runtime,
                    interaction_profile=existing.interaction_profile,
                    interaction_steering=existing.interaction_steering,
                    active_cycle=existing.active_cycle,
                    active_claim=str(action.get("claim_id") or ""),
                    active_route=existing.active_route,
                    write_scope=existing.write_scope,
                    lock_level=existing.lock_level,
                )
                updated["status"] = "bound_existing_session"
            else:
                bind_session(
                    ws,
                    str(action.get("session_id") or ""),
                    topic_id=str(action.get("topic_id") or ""),
                    context_id=str(action.get("context_id") or ""),
                    active_claim=str(action.get("claim_id") or ""),
                    interaction_steering="recovery binding created from canonical single-claim topic",
                )
                updated["status"] = "created_session"
        actions.append(updated)
    counts = Counter(str(action["status"]) for action in actions)
    return {
        **payload,
        "mode": "apply",
        "summary": {
            **(payload.get("summary") if isinstance(payload.get("summary"), dict) else {}),
            "action_count": len(actions),
            "applyable_count": sum(1 for action in actions if action.get("applyable")),
            "review_required_count": sum(1 for action in actions if not action.get("applyable")),
            "status_counts": dict(sorted(counts.items())),
        },
        "actions": actions,
    }


def render_workspace_recovery_binding_repair_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP Recovery Binding Repair",
        "",
        "This surface binds sessions to an active claim only when a topic has exactly one canonical claim.",
        "",
        f"- Mode: `{payload.get('mode', '')}`",
        f"- Actions: `{summary.get('action_count', 0)}`",
        f"- Applyable: `{summary.get('applyable_count', 0)}`",
        f"- Review required: `{summary.get('review_required_count', 0)}`",
        "",
        "## Actions",
        "",
        "| Topic | Status | Session | Claim | Reason |",
        "|---|---|---|---|---|",
    ]
    for action in payload.get("actions", []):
        if not isinstance(action, dict):
            continue
        lines.append(
            "| {topic} | {status} | `{session}` | `{claim}` | {reason} |".format(
                topic=_cell(action.get("topic_id", "")),
                status=_cell(action.get("status", "")),
                session=_cell(action.get("session_id", "")),
                claim=_cell(action.get("claim_id", "")),
                reason=_cell(action.get("reason", "")),
            )
        )
    lines.extend(["", "This repair does not update claim trust.", ""])
    return "\n".join(lines)


def write_workspace_recovery_binding_repair(
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
        write_text_atomic(path, render_workspace_recovery_binding_repair_markdown(payload))
        result["report_path"] = str(path)
    return result


def _repair_action(
    ws: WorkspacePaths,
    topic_id: str,
    claims: list[ClaimRecord],
    sessions: list[SessionBinding],
) -> dict[str, Any]:
    base = {
        "topic_id": topic_id,
        "claim_count": len(claims),
        "session_count": len(sessions),
        "claim_id": claims[0].claim_id if len(claims) == 1 else "",
        "session_id": sessions[-1].session_id if sessions else f"v5-{topic_id}-recovery-binding",
        "context_id": sessions[-1].context_id if sessions else _topic_context_id(ws, topic_id),
        "applyable": False,
        "status": "review_required_no_claim",
        "reason": "topic has no canonical claim to bind",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if len(claims) > 1:
        return {
            **base,
            "status": "review_required_multiple_claims",
            "reason": "topic has multiple canonical claims; active claim must be selected by semantic review",
        }
    if len(claims) == 1 and sessions and sessions[-1].active_claim:
        return {
            **base,
            "claim_id": sessions[-1].active_claim,
            "status": "already_bound",
            "reason": "latest session already has an active claim",
        }
    if len(claims) == 1 and sessions:
        return {
            **base,
            "applyable": True,
            "status": "planned_bind_existing_session",
            "reason": "topic has one canonical claim and an unbound latest session",
        }
    if len(claims) == 1:
        return {
            **base,
            "applyable": True,
            "status": "planned_create_session",
            "reason": "topic has one canonical claim and no session binding",
        }
    return base


def _focus_drift_repair_action(reconciliation: dict[str, Any]) -> dict[str, Any]:
    active = reconciliation.get("active_claim") if isinstance(reconciliation.get("active_claim"), dict) else {}
    candidates = list(reconciliation.get("candidate_sibling_claims") or [])
    return {
        "topic_id": str(reconciliation.get("topic_id") or ""),
        "claim_count": 1 + len(candidates),
        "session_count": 1,
        "claim_id": str(active.get("claim_id") or ""),
        "session_id": str(reconciliation.get("session_id") or ""),
        "context_id": "",
        "applyable": False,
        "status": "review_required_active_claim_focus_drift",
        "reason": "recent typed record focus points to sibling claim(s); explicit active-claim rebind confirmation is required",
        "candidate_claim_ids": [str(candidate.get("claim_id") or "") for candidate in candidates],
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _claims_by_topic(ws: WorkspacePaths) -> dict[str, list[ClaimRecord]]:
    out: dict[str, list[ClaimRecord]] = defaultdict(list)
    for claim in list_valid_records(ws.registry_dir("claims"), ClaimRecord):
        out[claim.topic_id].append(claim)
    for claims in out.values():
        claims.sort(key=lambda claim: claim.claim_id)
    return out


def _sessions_by_topic(ws: WorkspacePaths) -> dict[str, list[SessionBinding]]:
    out: dict[str, list[SessionBinding]] = defaultdict(list)
    for session in list_valid_records(ws.root / "runtime" / "sessions", SessionBinding):
        out[session.topic_id].append(session)
    for sessions in out.values():
        sessions.sort(key=lambda session: session.session_id)
    return out


def _session_by_id(ws: WorkspacePaths, session_id: str) -> SessionBinding | None:
    for session in list_valid_records(ws.root / "runtime" / "sessions", SessionBinding):
        if session.session_id == session_id:
            return session
    return None


def _topic_shell_ids(ws: WorkspacePaths) -> list[str]:
    topics = ws.root / "topics"
    if not topics.exists():
        return []
    return sorted(path.name for path in topics.iterdir() if path.is_dir())


def _topic_context_id(ws: WorkspacePaths, topic_id: str) -> str:
    path = ws.root / "topics" / topic_id / "topic.md"
    if path.exists():
        try:
            return read_record(path, TopicRecord).context_id
        except (TypeError, ValueError):
            pass
    return "recovery-import"


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
