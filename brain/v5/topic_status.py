"""vNext topic status and explainability surfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.evidence import list_evidence_for_claim
from brain.v5.paths import WorkspacePaths


def write_topic_status_surfaces(ws: WorkspacePaths, *, session_id: str) -> dict[str, Any]:
    """Write topic status files that explain the current route without chat history."""

    brief = build_execution_brief(ws, session_id)
    session = brief["session"]
    topic_id = session["topic_id"]
    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    topic_state = _topic_state(ws, brief)
    files = {
        "topic_state": str(runtime_dir / "topic_state.json"),
        "topic_dashboard": str(runtime_dir / "topic_dashboard.md"),
        "operator_console": str(runtime_dir / "operator_console.md"),
        "runtime_protocol": str(runtime_dir / "runtime_protocol.generated.md"),
        "session_start": str(runtime_dir / "session_start.generated.md"),
    }
    _write_json(Path(files["topic_state"]), topic_state)
    Path(files["topic_dashboard"]).write_text(_dashboard(topic_state), encoding="utf-8")
    Path(files["operator_console"]).write_text(_operator_console(topic_state), encoding="utf-8")
    Path(files["runtime_protocol"]).write_text(_runtime_protocol(topic_state), encoding="utf-8")
    Path(files["session_start"]).write_text(_session_start(topic_state), encoding="utf-8")
    return {
        "kind": "topic_status_bundle",
        "topic_id": topic_id,
        "session_id": session_id,
        "files": files,
        "topic_state": topic_state,
        "source_records": _source_records(topic_state),
        "derived_from": "execution_brief",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _topic_state(ws: WorkspacePaths, brief: dict[str, Any]) -> dict[str, Any]:
    session = brief["session"]
    focus = brief["current_focus"]
    active_claim_id = str(focus.get("active_claim") or "")
    known_context = brief["known_context"]
    next_action = (brief.get("next_action_candidates") or [{}])[0]
    flow = brief.get("flow_profile") or {}
    return {
        "kind": "topic_state",
        "topic_id": session["topic_id"],
        "session_id": session["session_id"],
        "context_id": session["context_id"],
        "active_claim_id": active_claim_id,
        "claim_statement": str(focus.get("claim_statement") or ""),
        "confidence_state": str(focus.get("confidence_state") or ""),
        "current_route_choice": str(session.get("active_route") or flow.get("profile") or "guided"),
        "why_here": str(flow.get("reason") or ""),
        "last_evidence_return": _last_evidence_return(ws, active_claim_id),
        "next_bounded_action": next_action,
        "blocker_summary": {
            "missing_outputs": list(brief.get("evidence_coverage", {}).get("missing_outputs") or []),
            "forbidden_now": list(brief.get("forbidden_now") or []),
            "human_checkpoint_needed": bool(brief.get("human_checkpoint", {}).get("needed")),
            "human_checkpoint_reason": str(brief.get("human_checkpoint", {}).get("reason") or ""),
        },
        "active_operator_checkpoint": known_context.get("operator_checkpoint", {}),
        "final_output_profile": known_context.get("final_output_profile", {}),
        "strategy_memory": known_context.get("strategy_memory", {}),
        "run_iterations": known_context.get("run_iterations", {}),
        "lane_exemplars": known_context.get("lane_exemplars", {}),
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _last_evidence_return(ws: WorkspacePaths, claim_id: str) -> dict[str, Any]:
    if not claim_id:
        return {}
    evidence_records = list_evidence_for_claim(ws, claim_id)
    if not evidence_records:
        return {}
    evidence = evidence_records[-1]
    return {
        "evidence_id": evidence.evidence_id,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": evidence.summary,
        "supports_outputs": list(evidence.supports_outputs),
        "source_refs": list(evidence.source_refs),
    }


def _source_records(topic_state: dict[str, Any]) -> dict[str, list[str]]:
    evidence_id = str(topic_state.get("last_evidence_return", {}).get("evidence_id") or "")
    claim_id = str(topic_state.get("active_claim_id") or "")
    return {
        "topics": [str(topic_state["topic_id"])],
        "sessions": [str(topic_state["session_id"])],
        "claims": [claim_id] if claim_id else [],
        "evidence": [evidence_id] if evidence_id else [],
    }


def _dashboard(topic_state: dict[str, Any]) -> str:
    blocker = topic_state["blocker_summary"]
    next_action = topic_state["next_bounded_action"]
    evidence = topic_state["last_evidence_return"]
    return (
        "# Topic Dashboard\n\n"
        f"Topic: {topic_state['topic_id']}\n\n"
        f"Current route choice: {topic_state['current_route_choice']}\n\n"
        f"Why here: {topic_state['why_here']}\n\n"
        f"Last meaningful evidence return: {evidence.get('summary', 'None')}\n\n"
        f"Blockers: {', '.join(blocker['missing_outputs'] + blocker['forbidden_now']) or 'None'}\n\n"
        f"Next bounded action: {next_action.get('action', 'None')}\n"
    )


def _operator_console(topic_state: dict[str, Any]) -> str:
    checkpoint = topic_state.get("active_operator_checkpoint") or {}
    next_action = topic_state.get("next_bounded_action") or {}
    question = checkpoint.get("question") or "No active operator checkpoint."
    options = "\n".join(f"- {option}" for option in checkpoint.get("options", [])) or "- None"
    return (
        "# Operator Console\n\n"
        f"Do now: {next_action.get('action', 'inspect_topic_dashboard')}\n\n"
        f"Human checkpoint: {question}\n\n"
        f"Options:\n{options}\n\n"
        "Do not: promote, update trust, or mix diagnostic outputs into final claims from this surface alone.\n"
    )


def _runtime_protocol(topic_state: dict[str, Any]) -> str:
    return (
        "# Runtime Protocol\n\n"
        "Read `topic_state.json` for machine routing, `operator_console.md` for immediate action, "
        "and refresh typed records before any trust-changing action.\n\n"
        f"Current route: {topic_state['current_route_choice']}\n"
    )


def _session_start(topic_state: dict[str, Any]) -> str:
    return (
        "# Session Start\n\n"
        f"Start from topic `{topic_state['topic_id']}` using the current route "
        f"`{topic_state['current_route_choice']}` and the operator console.\n"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
