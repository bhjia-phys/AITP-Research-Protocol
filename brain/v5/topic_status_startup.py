"""Lightweight topic-status handoff for host startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.claim_relation_map import empty_claim_relation_map, render_claim_relation_map_markdown
from brain.v5.compact_context_boundary import render_compact_context_section
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.session_resume import (
    build_session_resume_card,
    compact_context_from_resume,
    render_resume_boundary_section,
)


def write_topic_status_startup_surfaces(
    ws: WorkspacePaths,
    *,
    session_id: str,
) -> dict[str, Any]:
    """Write a current-session handoff without constructing a full execution brief."""

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    resume_card = build_session_resume_card(ws, session.session_id)
    compact = compact_context_from_resume(resume_card)
    boundary = resume_card.get("current_boundary") or {}
    relation_map = empty_claim_relation_map(
        topic_id=session.topic_id,
        session_id=session.session_id,
        requested_session_id=recovered.requested_session_id,
        recovery_selection_source=recovered.recovery_selection_source,
        reason="startup compact context requires exact relation-map expansion",
    )
    relation_map.update(
        {
            "claim_id": str(boundary.get("claim_id") or session.active_claim or ""),
            "claim_statement": str(boundary.get("statement") or ""),
            "confidence_state": str(boundary.get("confidence_state") or "unknown"),
            "current_conclusion": {
                "can_say": ["a bounded startup context is available"],
                "cannot_say": [
                    "cannot infer evidence support, validation, or claim trust before exact expansion"
                ],
            },
            "current_blockers": [
                "exact relation-map expansion is required for trust-sensitive continuation"
            ],
            "next_valid_actions": [
                "call the compact facade context_pack or record_refs expansion"
            ],
            "source_records": {
                **relation_map["source_records"],
                "claims": [str(boundary.get("claim_id") or session.active_claim or "")],
            },
        }
    )
    topic_state = _topic_state(session, boundary, relation_map, compact, resume_card)
    runtime_dir = ws.topic_dir(session.topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    files = _files(runtime_dir)
    Path(files["topic_state"]).write_text(
        json.dumps(topic_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    Path(files["topic_dashboard"]).write_text(_dashboard(topic_state), encoding="utf-8")
    Path(files["operator_console"]).write_text(_operator_console(topic_state), encoding="utf-8")
    Path(files["claim_relation_map"]).write_text(
        render_claim_relation_map_markdown(relation_map),
        encoding="utf-8",
    )
    Path(files["runtime_protocol"]).write_text(_runtime_protocol(), encoding="utf-8")
    Path(files["session_start"]).write_text(_session_start(topic_state), encoding="utf-8")
    claim_id = str(boundary.get("claim_id") or session.active_claim or "")
    return {
        "kind": "topic_status_bundle",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "files": files,
        "topic_state": topic_state,
        "compact_context": compact,
        "resume_card": resume_card,
        "resume_boundary": resume_card["resume_boundary"],
        "resume_boundary_json": resume_card["resume_boundary_json"],
        "source_records": {
            "topics": [session.topic_id],
            "sessions": [session.session_id],
            "claims": [claim_id] if claim_id else [],
            "evidence": [],
        },
        "derived_from": "aitp_context_pack",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _topic_state(session, boundary, relation_map, compact, resume_card) -> dict[str, Any]:
    return {
        "kind": "topic_state",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "context_id": session.context_id,
        "active_claim_id": str(boundary.get("claim_id") or session.active_claim or ""),
        "claim_statement": str(boundary.get("statement") or ""),
        "confidence_state": str(boundary.get("confidence_state") or "unknown"),
        "current_route_choice": str(session.active_route or "startup_compact"),
        "why_here": "bounded current-session startup recall",
        "last_evidence_return": {},
        "next_bounded_action": {"action": "expand_context_pack_or_record_refs"},
        "blocker_summary": {
            "missing_outputs": [],
            "forbidden_now": ["claim_trust_update_from_startup_surface"],
            "human_checkpoint_needed": False,
            "human_checkpoint_reason": "",
        },
        "claim_relation_map": relation_map,
        "active_operator_checkpoint": {},
        "final_output_profile": {},
        "strategy_memory": {"items": []},
        "run_iterations": {"items": []},
        "lane_exemplars": {"items": []},
        "compact_context": compact,
        "resume_boundary": resume_card["resume_boundary"],
        "resume_boundary_json": resume_card["resume_boundary_json"],
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _files(runtime_dir: Path) -> dict[str, str]:
    return {
        "topic_state": str(runtime_dir / "topic_state.json"),
        "topic_dashboard": str(runtime_dir / "topic_dashboard.md"),
        "operator_console": str(runtime_dir / "operator_console.md"),
        "claim_relation_map": str(runtime_dir / "claim_relation_map.generated.md"),
        "runtime_protocol": str(runtime_dir / "runtime_protocol.generated.md"),
        "session_start": str(runtime_dir / "session_start.generated.md"),
    }


def _dashboard(topic_state: dict[str, Any]) -> str:
    return (
        "# Topic Dashboard\n\n"
        f"Topic: {topic_state['topic_id']}\n\n"
        f"Active claim: {topic_state['active_claim_id']}\n\n"
        "This startup dashboard is orientation only; expand typed refs for details.\n"
    )


def _operator_console(topic_state: dict[str, Any]) -> str:
    action = topic_state["next_bounded_action"]["action"]
    return (
        "# Operator Console\n\n"
        f"Do now: {action}\n\n"
        "Do not update evidence, validation, or claim trust from this surface.\n"
    )


def _runtime_protocol() -> str:
    return (
        "# Runtime Protocol\n\n"
        "Use the compact facade first, then exact-expand only the required typed refs.\n"
    )


def _session_start(topic_state: dict[str, Any]) -> str:
    return (
        "# Session Start\n\n"
        f"Topic: `{topic_state['topic_id']}`\n\n"
        f"Active claim: `{topic_state['active_claim_id']}`\n\n"
        + render_resume_boundary_section(topic_state["resume_boundary"])
        + render_compact_context_section(topic_state["compact_context"])
        + "Do not update claim trust from this orientation surface.\n"
    )
