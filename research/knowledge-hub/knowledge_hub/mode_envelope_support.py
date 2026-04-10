from __future__ import annotations

from typing import Any

_MODE_SPECS: dict[str, dict[str, Any]] = {
    "discussion": {
        "local_task": "Clarify direction, shrink ambiguity, and keep the topic inside an honest early-layer envelope.",
        "foreground_layers": ["L0", "L1", "L3"],
        "allowed_backedges": ["L1 -> L0", "L1/L3 -> L2"],
        "required_writeback": ["idea_packet", "operator_checkpoint", "research_question_contract"],
        "forbidden_shortcuts": [
            "Do not treat discussion as validation.",
            "Do not preload heavy L4 or promotion context without a declared trigger.",
        ],
        "human_checkpoint_policy": "Ask only when the ambiguity materially changes route choice or topic direction.",
        "entry_conditions": ["Intent clarification, scope ambiguity, or an unresolved operator checkpoint is active."],
        "exit_conditions": ["Exit when the question is bounded enough for candidate formation or the human redirects the route."],
    },
    "explore": {
        "local_task": "Form or refine a bounded candidate without pretending it is already validated.",
        "foreground_layers": ["L1", "L3"],
        "allowed_backedges": ["L3 -> L0", "L3 -> L2"],
        "required_writeback": ["candidate_packets", "route_choice_notes", "source_recovery_notes"],
        "forbidden_shortcuts": [
            "Do not treat local plausibility as validation.",
            "Do not widen mandatory context beyond the current bounded route.",
        ],
        "human_checkpoint_policy": "Ask only at real route changes, cost changes, or novelty-definition changes.",
        "entry_conditions": ["A bounded research question exists and work is still forming or refining the candidate route."],
        "exit_conditions": ["Exit when the candidate is concrete enough for L4 validation or when an honest backedge is required."],
    },
    "verify": {
        "local_task": "Validate, adjudicate, or inspect proof/execution obligations for the current bounded candidate.",
        "foreground_layers": ["L4"],
        "allowed_backedges": ["L4 -> L0", "L4 -> L2"],
        "required_writeback": ["validation_result_artifacts", "contradiction_artifacts", "decision_or_route_updates"],
        "forbidden_shortcuts": [
            "Do not let style confidence count as validation.",
            "Do not keep iterating locally after a real L0/L2 blocker is known.",
        ],
        "human_checkpoint_policy": "Ask when the execution lane, resource commitment, or adjudication route is materially open.",
        "entry_conditions": ["Current work is in explicit validation, proof review, or route-selection review."],
        "exit_conditions": ["Exit when validation completes, blocks honestly to L0/L2/human, or hands off to promotion."],
    },
    "promote": {
        "local_task": "Inspect gate state and decide whether L4-backed material may cross the L4 -> L2 boundary.",
        "foreground_layers": ["L4", "L2"],
        "allowed_backedges": ["promote -> L4", "promote -> L0", "promote -> L2"],
        "required_writeback": ["promotion_gate", "promotion_decision", "backend_receipt"],
        "forbidden_shortcuts": [
            "Do not treat consultation as promotion.",
            "Do not treat maturity vibes as gate satisfaction.",
        ],
        "human_checkpoint_policy": "Human checkpoints remain legitimate for writeback and expensive trust moves.",
        "entry_conditions": ["The current action is explicitly reviewing or executing Layer 2 writeback."],
        "exit_conditions": ["Exit when gate review completes or the candidate is rejected back to L4/L0 work."],
    },
}

_PROMOTE_ACTION_TYPES = {
    "request_promotion",
    "approve_promotion",
    "promote_candidate",
    "auto_promote_candidate",
}
_VERIFY_ACTION_TYPES = {
    "select_validation_route",
    "materialize_execution_task",
    "dispatch_execution_task",
    "ingest_execution_result",
}
_VERIFY_TRIGGERS = {"verification_route_selection", "proof_completion_review", "contradiction_detected"}


def light_profile_primary_reads(
    *,
    topic_dashboard_path: str,
    research_question_contract_note_path: str,
) -> list[dict[str, str]]:
    return [
        {"path": topic_dashboard_path, "reason": "Primary human runtime surface for the current topic. Read this first for the bounded status, next action, and blockers."},
        {"path": research_question_contract_note_path, "reason": "Active research question, scope, and deliverables for ordinary topic work."},
    ]


def decision_override_read(control_note_path: str) -> dict[str, str]:
    return {"path": control_note_path, "reason": "Human steering or a declared decision override is active. Read this before trusting heuristic queue flow."}


def _select_runtime_mode(
    *,
    resume_stage: str | None,
    idea_packet_status: str,
    operator_checkpoint_status: str,
    selected_action_type: str,
    selected_action_summary: str,
    active_triggers: set[str],
) -> str:
    lowered_summary = selected_action_summary.lower()
    if idea_packet_status == "needs_clarification" or operator_checkpoint_status == "requested":
        return "discussion"
    if selected_action_type in _PROMOTE_ACTION_TYPES or any(token in lowered_summary for token in ("promot", "writeback")):
        return "promote"
    if (
        resume_stage == "L4"
        or selected_action_type in _VERIFY_ACTION_TYPES
        or bool(active_triggers & _VERIFY_TRIGGERS)
        or any(token in lowered_summary for token in ("validation", "verification", "proof", "derivation", "selected route"))
    ):
        return "verify"
    return "explore"


def _transition_posture(
    *,
    runtime_mode: str,
    active_triggers: set[str],
    operator_checkpoint_status: str,
) -> dict[str, Any]:
    if runtime_mode == "promote":
        return {
            "transition_kind": "forward_transition",
            "transition_reason": "The current bounded task is explicitly reviewing or executing the L4 -> L2 boundary.",
            "allowed_targets": ["L2", "L4", "L0"],
            "triggered_by": ["promotion_intent"] if "promotion_intent" in active_triggers else [],
            "requires_human_checkpoint": True,
            "human_checkpoint_reason": "Layer 2 writeback remains an explicit trust boundary.",
        }
    if "non_trivial_consultation" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "Current work needs L2 consultation before further local continuation is honest.",
            "allowed_targets": ["L2"],
            "triggered_by": ["non_trivial_consultation"],
            "requires_human_checkpoint": False,
            "human_checkpoint_reason": None,
        }
    if "capability_gap_blocker" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "A missing capability or workflow is the honest blocker for the next step.",
            "allowed_targets": ["L0", "human_checkpoint"],
            "triggered_by": ["capability_gap_blocker"],
            "requires_human_checkpoint": True,
            "human_checkpoint_reason": "Capability gaps often require operator choice about tooling, lane, or resource commitment.",
        }
    if "contradiction_detected" in active_triggers:
        return {
            "transition_kind": "backedge_transition",
            "transition_reason": "The current validation posture exposes contradiction or regime mismatch that may require earlier-layer recovery.",
            "allowed_targets": ["L0", "L2", "human_checkpoint"],
            "triggered_by": ["contradiction_detected"],
            "requires_human_checkpoint": False,
            "human_checkpoint_reason": None,
        }
    requires_human_checkpoint = operator_checkpoint_status == "requested"
    return {
        "transition_kind": "boundary_hold",
        "transition_reason": f"Current work remains inside the `{runtime_mode}` envelope until a declared trigger or completed artifact changes the layer boundary.",
        "allowed_targets": list(_MODE_SPECS[runtime_mode]["foreground_layers"]),
        "triggered_by": sorted(active_triggers),
        "requires_human_checkpoint": requires_human_checkpoint,
        "human_checkpoint_reason": "An active operator checkpoint is unresolved." if requires_human_checkpoint else None,
    }


def build_runtime_mode_contract(
    *,
    resume_stage: str | None,
    load_profile: str,
    idea_packet_status: str,
    operator_checkpoint_status: str,
    selected_action_type: str,
    selected_action_summary: str,
    must_read_now: list[dict[str, str]],
    may_defer_until_trigger: list[dict[str, str]],
    escalation_triggers: list[dict[str, Any]],
) -> dict[str, Any]:
    active_triggers = {
        str(row.get("trigger") or "").strip()
        for row in escalation_triggers
        if row.get("active") and str(row.get("trigger") or "").strip()
    }
    runtime_mode = _select_runtime_mode(
        resume_stage=resume_stage,
        idea_packet_status=idea_packet_status,
        operator_checkpoint_status=operator_checkpoint_status,
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_summary,
        active_triggers=active_triggers,
    )
    active_submode = "iterative_verify" if runtime_mode == "verify" and bool(active_triggers & _VERIFY_TRIGGERS) else None
    mode_spec = _MODE_SPECS[runtime_mode]
    transition_posture = _transition_posture(
        runtime_mode=runtime_mode,
        active_triggers=active_triggers,
        operator_checkpoint_status=operator_checkpoint_status,
    )
    entry_conditions = list(mode_spec["entry_conditions"])
    if active_submode:
        entry_conditions.append("A bounded L3-L4 loop is active and each failed pass can produce explicit feedback.")
    exit_conditions = list(mode_spec["exit_conditions"])
    if transition_posture["transition_kind"] == "backedge_transition":
        exit_conditions.append("Current work should exit locally once the declared backedge has been materialized.")
    return {
        "runtime_mode": runtime_mode,
        "active_submode": active_submode,
        "mode_envelope": {
            "mode": runtime_mode,
            "active_submode": active_submode,
            "load_profile": load_profile,
            "local_task": mode_spec["local_task"],
            "foreground_layers": list(mode_spec["foreground_layers"]),
            "minimum_mandatory_context": must_read_now,
            "deferred_context": may_defer_until_trigger,
            "allowed_backedges": list(mode_spec["allowed_backedges"]),
            "required_writeback": list(mode_spec["required_writeback"]),
            "forbidden_shortcuts": list(mode_spec["forbidden_shortcuts"]),
            "human_checkpoint_policy": mode_spec["human_checkpoint_policy"],
            "entry_conditions": entry_conditions,
            "exit_conditions": exit_conditions,
        },
        "transition_posture": transition_posture,
    }


def runtime_mode_payload_fragment(**kwargs: Any) -> dict[str, Any]:
    mode_contract = build_runtime_mode_contract(**kwargs)
    return {
        "runtime_mode": mode_contract["runtime_mode"],
        "active_submode": mode_contract["active_submode"],
        "mode_envelope": mode_contract["mode_envelope"],
        "transition_posture": mode_contract["transition_posture"],
    }


def runtime_mode_markdown_lines(payload: dict[str, Any]) -> list[str]:
    runtime_mode = str(payload.get("runtime_mode") or "explore")
    active_submode = payload.get("active_submode")
    mode_envelope = payload.get("mode_envelope") or {}
    transition_posture = payload.get("transition_posture") or {}
    return [
        f"- Runtime mode: `{runtime_mode}`",
        f"- Active submode: `{active_submode or '(none)'}`",
        "",
        "## Mode envelope",
        "",
        f"- Local task: `{mode_envelope.get('local_task') or '(missing)'}`",
        f"- Foreground layers: `{', '.join(mode_envelope.get('foreground_layers') or []) or '(missing)'}`",
        f"- Human checkpoint policy: `{mode_envelope.get('human_checkpoint_policy') or '(missing)'}`",
        "",
        "## Transition posture",
        "",
        f"- Kind: `{transition_posture.get('transition_kind') or '(missing)'}`",
        f"- Allowed targets: `{', '.join(transition_posture.get('allowed_targets') or []) or '(none)'}`",
        f"- Reason: `{transition_posture.get('transition_reason') or '(missing)'}`",
    ]


def dedupe_surface_entries(surfaces: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for surface in surfaces:
        key = f"{surface['surface']}::{surface['path']}"
        if key not in seen:
            seen.add(key)
            deduped.append(surface)
    return deduped
