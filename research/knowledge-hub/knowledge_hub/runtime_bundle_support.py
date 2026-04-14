from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from .collaborator_profile_support import append_collaborator_profile_markdown, collaborator_profile_must_read_entry, normalize_collaborator_profile_for_bundle
from .decision_point_handler import get_all_decision_points, list_pending_decision_points
from .decision_trace_handler import get_decision_traces
from .control_plane_support import build_runtime_bundle_control_plane, control_note_override_active, control_plane_markdown_lines
from .h_plane_support import build_h_plane_payload
from .kernel_templates import render_session_start_note
from .l2_staging import materialize_workspace_staging_manifest
from .mode_envelope_support import decision_override_read, dedupe_surface_entries, filter_escalation_triggers_for_mode, light_profile_primary_reads, refocus_context_for_runtime_mode, runtime_mode_markdown_lines, runtime_mode_payload_fragment
from .paired_backend_support import build_runtime_backend_bridges
from .research_trajectory_support import append_research_trajectory_markdown, normalize_research_trajectory_for_bundle, research_trajectory_must_read_entry
from .mode_learning_support import append_mode_learning_markdown, normalize_mode_learning_for_bundle, mode_learning_must_read_entry
from .research_judgment_runtime_support import append_research_judgment_markdown, decision_surface_snapshot, normalize_research_judgment_for_bundle, research_judgment_must_read_entry
from .research_taste_support import append_research_taste_markdown, normalize_research_taste_for_bundle, research_taste_must_read_entry
from .scratchpad_support import append_scratchpad_markdown, normalize_scratchpad_for_bundle, scratchpad_must_read_entry
from .runtime_read_path_support import append_competing_hypotheses_markdown, append_graph_analysis_markdown, append_l1_source_intake_markdown, append_l1_vault_markdown, append_route_activation_markdown, append_route_choice_markdown, append_route_handoff_markdown, append_route_reentry_markdown, append_route_transition_gate_markdown, append_route_transition_intent_markdown, append_route_transition_receipt_markdown, append_route_transition_resolution_markdown, append_route_transition_discrepancy_markdown, append_route_transition_repair_markdown, append_route_transition_escalation_markdown, append_route_transition_clearance_markdown, append_route_transition_followthrough_markdown, append_route_transition_resumption_markdown, append_route_transition_commitment_markdown, append_route_transition_authority_markdown, append_source_intelligence_markdown, build_active_research_contract_payload, build_route_transition_receipt_payload, build_route_transition_resolution_payload, build_route_transition_discrepancy_payload, build_route_transition_repair_payload, build_route_transition_escalation_payload, build_route_transition_clearance_payload, build_route_transition_followthrough_payload, build_route_transition_resumption_payload, build_route_transition_commitment_payload, build_route_transition_authority_payload, empty_l1_source_intake, empty_source_intelligence, normalized_graph_analysis, normalized_source_intelligence
from .runtime_projection_handler import (
    append_transition_history,
    build_knowledge_packets_from_candidates,
    load_transition_history,
    write_pending_decisions_projection,
    write_promotion_readiness_projection,
    write_promotion_trace,
    write_topic_synopsis,
)
from .theory_context_injection import (
    apply_theory_context_session_dedup,
    build_theory_context_injection,
)
from .loop_detection_support import materialize_loop_detection
from .protocol_manifest import materialize_protocol_manifest, protocol_manifest_must_read_entry
from .validation_review_service import analytical_cross_check_markdown_lines


def _human_interaction_posture_from_bundle(runtime_bundle: dict[str, Any]) -> dict[str, Any]:
    h_plane = runtime_bundle.get("h_plane") or {}
    steering = h_plane.get("steering") or {}
    checkpoint = h_plane.get("checkpoint") or {}
    approval = h_plane.get("approval") or {}
    idea_packet = runtime_bundle.get("idea_packet") or {}

    checkpoint_status = str(checkpoint.get("status") or "").strip()
    approval_status = str(approval.get("status") or "").strip()
    idea_packet_status = str(idea_packet.get("status") or "").strip()
    steering_status = str(steering.get("status") or "").strip()

    if idea_packet_status == "needs_clarification":
        summary = "AITP is waiting on clarification before deeper work continues."
        action = "Answer the idea-packet questions before continuing the bounded loop."
        requires_human = True
    elif checkpoint_status == "requested":
        summary = "AITP is waiting on an active human checkpoint before deeper work continues."
        action = "Answer the active checkpoint instead of continuing the queue."
        requires_human = True
    elif approval_status == "pending_human_approval":
        summary = (
            "AITP is waiting on a human decision about whether this is ready to save as reusable knowledge "
            "before trust can cross into L2."
        )
        action = "Review the promotion gate before any L2 writeback continues."
        requires_human = True
    elif steering_status and steering_status != "none":
        summary = "Human steering is already active and has been translated into durable route state."
        action = "Continue from the redirected chosen approach unless a new checkpoint appears."
        requires_human = False
    else:
        summary = "No active human checkpoint is currently blocking the bounded loop."
        action = "AITP may continue bounded work autonomously until a real checkpoint or blocker appears."
        requires_human = False

    return {
        "overall_status": str(h_plane.get("overall_status") or "steady"),
        "requires_human_input_now": requires_human,
        "steering_status": steering_status or "none",
        "checkpoint_status": checkpoint_status or "missing",
        "approval_status": approval_status or "not_requested",
        "summary": summary,
        "next_action": action,
    }


def _autonomy_posture_from_bundle(
    runtime_bundle: dict[str, Any],
    *,
    requested_max_auto_steps: int | None,
    applied_max_auto_steps: int | None = None,
    budget_reason: str | None = None,
) -> dict[str, Any]:
    human_posture = _human_interaction_posture_from_bundle(runtime_bundle)
    runtime_mode = str(runtime_bundle.get("runtime_mode") or "explore")
    active_submode = str(runtime_bundle.get("active_submode") or "").strip() or None

    if human_posture["requires_human_input_now"]:
        mode = "await_human_checkpoint"
        summary = "Pause bounded execution and wait for the human checkpoint or clarification response."
        stop_conditions = [
            "the human answers or cancels the active checkpoint",
            "the clarification gate is resolved",
        ]
    elif (
        (requested_max_auto_steps == 0 and applied_max_auto_steps == 0)
        or str(budget_reason or "").strip() == "explicit_budget_disabled"
    ):
        mode = "continuous_bounded_loop"
        summary = (
            "No human checkpoint is active, but this invocation disabled auto-step execution, "
            "so continue manually from the current chosen approach."
        )
        stop_conditions = [
            "the operator resumes bounded execution explicitly",
            "a real blocker or backedge is materialized",
            "a human checkpoint becomes active",
        ]
    elif runtime_mode == "verify" and active_submode == "iterative_verify":
        mode = "continuous_iterative_verify"
        summary = (
            "Keep the bounded L3-L4 loop running until validation succeeds, or until a real blocker, contradiction, or "
            "human checkpoint appears."
        )
        stop_conditions = [
            "validation reaches a stable success state",
            "a real contradiction or backedge blocker is materialized",
            "a human checkpoint becomes active",
        ]
    else:
        mode = "continuous_bounded_loop"
        summary = "Continue the bounded AITP loop without pausing for ritual confirmations when no human checkpoint is active."
        stop_conditions = [
            "the current chosen approach completes",
            "a real blocker or backedge is materialized",
            "a human checkpoint becomes active",
        ]

    return {
        "mode": mode,
        "runtime_mode": runtime_mode,
        "active_submode": active_submode,
        "can_continue_without_human": not human_posture["requires_human_input_now"],
        "summary": summary,
        "stop_conditions": stop_conditions,
        "requested_max_auto_steps": requested_max_auto_steps,
        "applied_max_auto_steps": applied_max_auto_steps,
        "budget_reason": str(budget_reason or ""),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"
def runtime_protocol_markdown(payload: dict[str, Any]) -> str:
    load_profile = str(payload.get("load_profile") or "light")
    topic_synopsis = payload.get("topic_synopsis") or {}
    runtime_focus = topic_synopsis.get("runtime_focus") or {}
    l0_source_handoff = runtime_focus.get("l0_source_handoff") or {}
    truth_sources = topic_synopsis.get("truth_sources") or {}
    pending_decisions = payload.get("pending_decisions") or {}
    minimal = payload.get("minimal_execution_brief") or {}
    active_research_contract = payload.get("active_research_contract") or {}
    idea_packet = payload.get("idea_packet") or {}
    operator_checkpoint = payload.get("operator_checkpoint") or {}
    promotion_readiness = payload.get("promotion_readiness") or {}
    validation_review_bundle = payload.get("validation_review_bundle") or {}
    open_gap_summary = payload.get("open_gap_summary") or {}
    strategy_memory = payload.get("strategy_memory") or {}
    collaborator_profile = payload.get("collaborator_profile") or {}; research_trajectory = payload.get("research_trajectory") or {}; mode_learning = payload.get("mode_learning") or {}
    research_judgment = payload.get("research_judgment") or {}; research_taste = payload.get("research_taste") or {}; scratchpad = payload.get("scratchpad") or {}
    source_intelligence = payload.get("source_intelligence") or {}
    graph_analysis = payload.get("graph_analysis") or {}
    theory_context_injection = payload.get("theory_context_injection") or {}
    loop_detection = payload.get("loop_detection") or {}
    protocol_manifest = payload.get("protocol_manifest") or {}
    control_plane = payload.get("control_plane") or {}
    topic_skill_projection = payload.get("topic_skill_projection") or {}
    topic_completion = payload.get("topic_completion") or {}
    statement_compilation = payload.get("statement_compilation") or {}
    lean_bridge = payload.get("lean_bridge") or {}
    must_read_now = payload.get("must_read_now") or []
    active_hard_constraints = payload.get("active_hard_constraints") or []
    escalation_triggers = payload.get("escalation_triggers") or []
    may_defer_until_trigger = payload.get("may_defer_until_trigger") or []
    recommended_protocol_slices = payload.get("recommended_protocol_slices") or []
    human_interaction_posture = payload.get("human_interaction_posture") or _human_interaction_posture_from_bundle(payload)
    autonomy_posture = payload.get("autonomy_posture") or _autonomy_posture_from_bundle(
        payload,
        requested_max_auto_steps=None,
        applied_max_auto_steps=None,
    )
    lines = [
        "# AITP runtime protocol bundle",
        "",
        f"- JSON schema: `{payload.get('$schema') or '(missing)'}`",
        f"- Bundle kind: `{payload.get('bundle_kind') or '(missing)'}`",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Human request: `{payload['human_request'] or '(missing)'}`",
        f"- Resume stage: `{payload['resume_stage'] or '(missing)'}`",
        f"- Last materialized stage: `{payload['last_materialized_stage'] or '(missing)'}`",
        f"- Research mode: `{payload['research_mode'] or '(missing)'}`",
        f"- Load profile: `{load_profile}`",
        "",
        "## Human interaction posture",
        "",
        f"- Overall status: `{human_interaction_posture.get('overall_status') or '(missing)'}`",
        f"- Requires human input now: `{str(bool(human_interaction_posture.get('requires_human_input_now'))).lower()}`",
        f"- Steering status: `{human_interaction_posture.get('steering_status') or '(missing)'}`",
        f"- Checkpoint status: `{human_interaction_posture.get('checkpoint_status') or '(missing)'}`",
        f"- Approval status: `{human_interaction_posture.get('approval_status') or '(missing)'}`",
        "",
        f"{human_interaction_posture.get('summary') or '(missing)'}",
        "",
        f"Next action: {human_interaction_posture.get('next_action') or '(missing)'}",
        "",
        "## Autonomous continuation",
        "",
        f"- Mode: `{autonomy_posture.get('mode') or '(missing)'}`",
        f"- Can continue without human: `{str(bool(autonomy_posture.get('can_continue_without_human'))).lower()}`",
        f"- Requested auto-step budget: `{autonomy_posture.get('requested_max_auto_steps') if autonomy_posture.get('requested_max_auto_steps') is not None else '(none)'}`",
        f"- Applied auto-step budget: `{autonomy_posture.get('applied_max_auto_steps') if autonomy_posture.get('applied_max_auto_steps') is not None else '(none)'}`",
        f"- Budget reason: `{autonomy_posture.get('budget_reason') or '(none)'}`",
        "",
        f"{autonomy_posture.get('summary') or '(missing)'}",
        "",
        "## Topic synopsis",
        "",
        f"- Synopsis path: `{topic_synopsis.get('path') or '(missing)'}`",
        f"- Lane: `{topic_synopsis.get('lane') or '(missing)'}`",
        f"- Pending decisions: `{topic_synopsis.get('pending_decision_count') or 0}`",
        f"- Knowledge packets: `{len(topic_synopsis.get('knowledge_packet_paths') or [])}`",
        "",
        f"{runtime_focus.get('summary') or topic_synopsis.get('next_action_summary') or '(missing)'}",
    ]
    if l0_source_handoff:
        lines.extend(
            [
                "",
                "## L0 source handoff",
                "",
                f"- Status: `{l0_source_handoff.get('status') or '(missing)'}`",
                f"- Summary: {l0_source_handoff.get('summary') or '(missing)'}",
                f"- Primary lane: `{l0_source_handoff.get('primary_path') or '(missing)'}`",
                f"- Use when: {l0_source_handoff.get('primary_when') or '(missing)'}",
                "",
                "### Alternate entries",
                "",
            ]
        )
        for row in l0_source_handoff.get("alternate_entries") or ["(none)"]:
            if isinstance(row, dict):
                lines.append(
                    f"- `{row.get('path') or '(missing)'}`: {row.get('when') or '(missing)'}"
                )
            else:
                lines.append(f"- {row}")
    append_source_intelligence_markdown(lines, source_intelligence)
    append_graph_analysis_markdown(lines, graph_analysis)
    lines.extend(
        [
            "",
            "## Theory context injection",
            "",
            f"- Status: `{theory_context_injection.get('status') or '(missing)'}`",
            f"- Session TTL seconds: `{theory_context_injection.get('session_ttl_seconds') or 0}`",
            f"- Session state path: `{theory_context_injection.get('session_state_path') or '(missing)'}`",
            "",
            "### Active target paths",
            "",
        ]
    )
    for item in theory_context_injection.get("active_target_paths") or ["(none)"]:
        lines.append(f"- `{item}`" if item != "(none)" else "- (none)")
    lines.extend(["", "### Context fragments", ""])
    if theory_context_injection.get("fragments"):
        for row in theory_context_injection.get("fragments") or []:
            lines.append(
                f"- `{row.get('kind') or '(missing)'}` path=`{row.get('path') or '(missing)'}` summary=`{row.get('summary') or '(missing)'}`"
            )
    else:
        lines.append("- (none)")
    lines.extend(
        [
            "",
            "## Loop detection",
            "",
            f"- Status: `{loop_detection.get('status') or '(missing)'}`",
            f"- Retry threshold: `{loop_detection.get('retry_threshold') or 0}`",
            f"- Retry count: `{loop_detection.get('retry_count') or 0}`",
            f"- Candidate id: `{loop_detection.get('candidate_id') or '(none)'}`",
            f"- Source operation kind: `{loop_detection.get('source_operation_kind') or '(none)'}`",
            f"- Suggestion kind: `{loop_detection.get('suggestion_kind') or '(none)'}`",
            f"- Note path: `{loop_detection.get('note_path') or '(missing)'}`",
            "",
            f"{loop_detection.get('summary') or '(missing)'}",
            "",
        ]
    )
    for item in loop_detection.get("recommended_actions") or ["(none)"]:
        if item == (loop_detection.get("recommended_actions") or ["(none)"])[0]:
            lines.extend(["### Recommended actions", ""])
        lines.append(f"- {item}" if item != "(none)" else "- (none)")
    lines.extend(
        [
            "",
            "## Protocol manifest",
            "",
            f"- Declared state: `{protocol_manifest.get('declared_state') or '(missing)'}`",
            f"- Overall status: `{protocol_manifest.get('overall_status') or '(missing)'}`",
            f"- Missing artifact count: `{protocol_manifest.get('missing_artifact_count') or 0}`",
            f"- Manifest note: `{protocol_manifest.get('note_path') or '(missing)'}`",
            "",
            f"{protocol_manifest.get('summary') or '(missing)'}",
            "",
            "### Missing paths",
            "",
        ]
    )
    for item in protocol_manifest.get("missing_paths") or ["(none)"]:
        lines.append(f"- `{item}`" if item != "(none)" else "- (none)")
    lines.extend(
        ["", *control_plane_markdown_lines(control_plane), "## Runtime truth model", ""]
        + [
            f"- Machine synopsis: `{topic_synopsis.get('path') or '(missing)'}`",
            f"- Primary human render: `runtime/topics/{payload['topic_slug']}/topic_dashboard.md`",
            f"- Focus state source: `{truth_sources.get('topic_state_path') or '(missing)'}`",
            f"- Research contract source: `{truth_sources.get('research_question_contract_path') or '(missing)'}`",
            f"- Next-action source: `{truth_sources.get('next_action_surface_path') or '(missing)'}`",
            f"- Human-need source: `{truth_sources.get('human_need_surface_path') or '(none)'}`",
            f"- Dependency source: `{truth_sources.get('dependency_registry_path') or '(missing)'}`",
            f"- Promotion-readiness source: `{truth_sources.get('promotion_readiness_path') or '(missing)'}`",
            f"- Promotion-gate source: `{truth_sources.get('promotion_gate_path') or '(none)'}`",
            "",
            "## Pending decisions",
            "",
            f"- Projection path: `{pending_decisions.get('path') or '(missing)'}`",
            f"- Pending count: `{pending_decisions.get('pending_count') or 0}`",
            f"- Blocking count: `{pending_decisions.get('blocking_count') or 0}`",
            f"- Latest resolved trace: `{pending_decisions.get('latest_resolved_trace_ref') or '(none)'}`",
            "",
            f"{pending_decisions.get('latest_resolved_summary') or '(no resolved decision trace recorded)'}",
            "",
            "## Active research contract",
            "",
            f"- Question id: `{active_research_contract.get('question_id') or '(missing)'}`",
            f"- Title: `{active_research_contract.get('title') or '(missing)'}`",
            f"- Status: `{active_research_contract.get('status') or '(missing)'}`",
            f"- Template mode: `{active_research_contract.get('template_mode') or '(missing)'}`",
            f"- Validation mode: `{active_research_contract.get('validation_mode') or '(missing)'}`",
            f"- Contract JSON: `{active_research_contract.get('path') or '(missing)'}`",
            f"- Contract note: `{active_research_contract.get('note_path') or '(missing)'}`",
            f"- Active branch hypothesis: `{active_research_contract.get('active_branch_hypothesis_id') or '(none recorded)'}`",
            f"- Deferred branch hypotheses: `{', '.join(active_research_contract.get('deferred_branch_hypothesis_ids') or []) or '(none)'}`",
            f"- Follow-up branch hypotheses: `{', '.join(active_research_contract.get('followup_branch_hypothesis_ids') or []) or '(none)'}`",
            "",
            f"{active_research_contract.get('question') or '(missing)'}",
        ]
    )
    append_l1_source_intake_markdown(lines, active_research_contract)
    append_l1_vault_markdown(lines, active_research_contract)
    append_competing_hypotheses_markdown(lines, active_research_contract)
    append_route_activation_markdown(lines, active_research_contract)
    append_route_reentry_markdown(lines, active_research_contract)
    append_route_handoff_markdown(lines, active_research_contract)
    append_route_choice_markdown(lines, active_research_contract)
    append_route_transition_gate_markdown(lines, active_research_contract)
    append_route_transition_intent_markdown(lines, active_research_contract)
    append_route_transition_receipt_markdown(lines, active_research_contract)
    append_route_transition_resolution_markdown(lines, active_research_contract)
    append_route_transition_discrepancy_markdown(lines, active_research_contract)
    append_route_transition_repair_markdown(lines, active_research_contract)
    append_route_transition_escalation_markdown(lines, active_research_contract)
    append_route_transition_clearance_markdown(lines, active_research_contract)
    append_route_transition_followthrough_markdown(lines, active_research_contract)
    append_route_transition_resumption_markdown(lines, active_research_contract)
    append_route_transition_commitment_markdown(lines, active_research_contract)
    append_route_transition_authority_markdown(lines, active_research_contract)
    lines.extend(
        [
            "",
            "## Idea packet",
            "",
            f"- Status: `{idea_packet.get('status') or '(missing)'}`",
            f"- Idea note: `{idea_packet.get('note_path') or '(missing)'}`",
            f"- First validation route: `{idea_packet.get('first_validation_route') or '(missing)'}`",
            f"- Initial evidence bar: `{idea_packet.get('initial_evidence_bar') or '(missing)'}`",
            f"- Missing fields: `{', '.join(idea_packet.get('missing_fields') or []) or '(none)'}`",
            "",
            f"{idea_packet.get('status_reason') or '(missing)'}",
            "",
            "## Operator checkpoint",
            "",
            f"- Status: `{operator_checkpoint.get('status') or '(missing)'}`",
            f"- Kind: `{operator_checkpoint.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint note: `{operator_checkpoint.get('note_path') or '(missing)'}`",
            "",
            f"{operator_checkpoint.get('question') or '(none)'}",
            "",
            "## Validation review bundle",
            "",
            f"- Status: `{validation_review_bundle.get('status') or '(missing)'}`",
            f"- Primary review kind: `{validation_review_bundle.get('primary_review_kind') or '(missing)'}`",
            f"- Bundle JSON: `{validation_review_bundle.get('path') or '(missing)'}`",
            f"- Bundle note: `{validation_review_bundle.get('note_path') or '(missing)'}`",
            "",
            f"{validation_review_bundle.get('summary') or '(missing)'}",
            "",
            *analytical_cross_check_markdown_lines(validation_review_bundle.get("analytical_cross_check_surface") or {}),
            "",
            "## Promotion readiness",
            "",
            f"- Status: `{promotion_readiness.get('status') or '(missing)'}`",
            f"- Gate status: `{promotion_readiness.get('gate_status') or '(missing)'}`",
            f"- Summary note: `{promotion_readiness.get('path') or '(missing)'}`",
            f"- Ready candidates: `{', '.join(promotion_readiness.get('ready_candidate_ids') or []) or '(none)'}`",
            "",
            f"{promotion_readiness.get('summary') or '(missing)'}",
            "",
            "## Transition history",
            "",
            f"- JSON path: `runtime/topics/{payload['topic_slug']}/transition_history.json`",
            f"- Note path: `runtime/topics/{payload['topic_slug']}/transition_history.md`",
            "- Inspect these surfaces when you need the bounded forward/backward layer path instead of only the current stage snapshot.",
            "",
            "## Open gap summary",
            "",
            f"- Status: `{open_gap_summary.get('status') or '(missing)'}`",
            f"- Gap count: `{open_gap_summary.get('gap_count') or 0}`",
            f"- Follow-up gap writeback count: `{open_gap_summary.get('followup_gap_writeback_count') or 0}`",
            f"- Requires L0 return: `{str(bool(open_gap_summary.get('requires_l0_return'))).lower()}`",
            f"- Gap map: `{open_gap_summary.get('path') or '(missing)'}`",
            "",
            f"{open_gap_summary.get('summary') or '(missing)'}",
            "",
            "## Strategy memory",
            "",
            f"- Status: `{strategy_memory.get('status') or '(missing)'}`",
            f"- Lane: `{strategy_memory.get('lane') or '(missing)'}`",
            f"- Row count: `{strategy_memory.get('row_count') or 0}`",
            f"- Relevant count: `{strategy_memory.get('relevant_count') or 0}`",
            f"- Helpful count: `{strategy_memory.get('helpful_count') or 0}`",
            f"- Harmful count: `{strategy_memory.get('harmful_count') or 0}`",
            f"- Latest path: `{strategy_memory.get('latest_path') or '(none)'}`",
            "",
            f"{strategy_memory.get('summary') or '(missing)'}",
            "",
            "## Topic skill projection",
            "",
            f"- Status: `{topic_skill_projection.get('status') or '(missing)'}`",
            f"- Projection id: `{topic_skill_projection.get('id') or '(missing)'}`",
            f"- Candidate id: `{topic_skill_projection.get('candidate_id') or '(none)'}`",
            f"- Note path: `{topic_skill_projection.get('note_path') or '(missing)'}`",
            f"- Intended L2 target: `{topic_skill_projection.get('intended_l2_target') or '(none)'}`",
            "",
            f"{topic_skill_projection.get('summary') or '(missing)'}`",
            "",
            "## Topic completion",
            "",
            f"- Status: `{topic_completion.get('status') or '(missing)'}`",
            f"- Completion note: `{topic_completion.get('path') or '(missing)'}`",
            f"- Promotion-ready candidates: `{', '.join(topic_completion.get('promotion_ready_candidate_ids') or []) or '(none)'}`",
            "",
            f"{topic_completion.get('summary') or '(missing)'}`",
            "",
            "## Statement compilation",
            "",
            f"- Status: `{statement_compilation.get('status') or '(missing)'}`",
            f"- Packet count: `{statement_compilation.get('packet_count') or 0}`",
            f"- Compilation note: `{statement_compilation.get('path') or '(missing)'}`",
            "",
            f"{statement_compilation.get('summary') or '(missing)'}`",
            "",
            "## Lean bridge",
            "",
            f"- Status: `{lean_bridge.get('status') or '(missing)'}`",
            f"- Packet count: `{lean_bridge.get('packet_count') or 0}`",
            f"- Bridge note: `{lean_bridge.get('path') or '(missing)'}`",
            "",
            f"{lean_bridge.get('summary') or '(missing)'}`",
            "",
            "## Minimal execution brief",
            "",
            f"- Current stage: `{minimal.get('current_stage') or payload['resume_stage'] or '(missing)'}`",
            f"- Current bounded action: `{minimal.get('selected_action_summary') or '(no pending action)'}`",
            f"- Selected action id: `{minimal.get('selected_action_id') or '(none)'}`",
            f"- Selected action type: `{minimal.get('selected_action_type') or '(none)'}`",
            f"- Decision source: `{minimal.get('decision_source') or '(missing)'}`",
            f"- Queue source: `{minimal.get('queue_source') or '(missing)'}`",
            f"- Open next: `{minimal.get('open_next') or '(missing)'}`",
            "",
            "### Allowed now",
            "",
        ]
    )
    for item in minimal.get("immediate_allowed_work") or ["Continue bounded work only after reading the required top-level surfaces."]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "### Blocked now",
            "",
        ]
    )
    for item in minimal.get("immediate_blocked_work") or ["Do not treat deferred surfaces as optional once their trigger fires."]:
        lines.append(f"- {item}")
    lines.extend(runtime_mode_markdown_lines(payload))
    if autonomy_posture.get("stop_conditions"):
        lines.extend(["", "## Autonomous stop conditions", ""])
        for item in autonomy_posture.get("stop_conditions") or []:
            lines.append(f"- {item}")
    if strategy_memory.get("guidance"):
        lines.extend(["", "## Strategy guidance", ""])
        for item in strategy_memory.get("guidance") or []:
            lines.append(f"- {item}")
    append_collaborator_profile_markdown(lines, collaborator_profile); append_research_trajectory_markdown(lines, research_trajectory); append_mode_learning_markdown(lines, mode_learning); append_research_judgment_markdown(lines, research_judgment); append_research_taste_markdown(lines, research_taste); append_scratchpad_markdown(lines, scratchpad)
    if topic_skill_projection.get("required_first_routes"):
        lines.extend(["", "## Projection route guidance", ""])
        for item in topic_skill_projection.get("required_first_routes") or []:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Must read now",
            "",
        ]
    )
    for idx, item in enumerate(must_read_now, start=1):
        lines.append(f"{idx}. `{item['path']}` - {item['reason']}")
    lines.extend(
        [
            "",
            "## Active hard constraints",
            "",
        ]
    )
    for item in active_hard_constraints:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Escalate only when triggered",
            "",
        ]
    )
    for item in escalation_triggers:
        status = "active" if item.get("active") else "inactive"
        lines.append(f"- `{item['trigger']}` status=`{status}`: {item['condition']}")
        required_reads = item.get("required_reads") or []
        if required_reads:
            lines.append(f"  required_reads=`{', '.join(required_reads)}`")
    lines.extend(
        [
            "",
            "## Deferred protocol surfaces",
            "",
        ]
    )
    if may_defer_until_trigger:
        for item in may_defer_until_trigger:
            lines.append(
                f"- `{item['path']}` trigger=`{item['trigger']}` reason=`{item['reason']}`"
            )
    else:
        lines.append("- None registered.")
    lines.extend(
        [
            "",
            "## Recommended protocol slices",
            "",
        ]
    )
    if recommended_protocol_slices:
        for item in recommended_protocol_slices:
            trigger = item.get("trigger") or "always"
            lines.append(f"- `{item['slice']}` trigger=`{trigger}`")
            for path in item.get("paths") or []:
                lines.append(f"  - `{path}`")
    else:
        lines.append("- None registered.")
    lines.extend(
        [
            "",
            "## Why this file exists",
            "",
            "- Keep research behavior governed by durable protocol artifacts instead of hidden Python defaults.",
            "- Limit Python to state materialization, audits, and explicit handler execution.",
            f"- Keep ordinary topic work in the `{load_profile}` profile unless a real trigger forces escalation.",
            "",
            "## What Python still does",
            "",
        ]
    )
    for item in payload["python_runtime_scope"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Required read order",
            "",
        ]
    )
    for idx, item in enumerate(payload["agent_required_read_order"], start=1):
        lines.append(f"{idx}. `{item}`")
    lines.extend(
        [
            "",
            "## Decision priority",
            "",
        ]
    )
    for item in payload["priority_rules"]:
        lines.append(f"- [{item['source']}] {item['rule']}")
    lines.extend(
        [
            "",
            "## Reproducibility expectations",
            "",
        ]
    )
    expectations = payload.get("reproducibility_expectations") or ["Persist durable artifacts before claiming progress."]
    for item in expectations:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Human-readable note obligations",
            "",
        ]
    )
    notes = payload.get("note_expectations") or ["Write human-readable notes for every layer you update."]
    for item in notes:
        lines.append(f"- {item}")
    lines.extend(
        [
        "",
        "## L2 backend bridge snapshot",
        "",
    ]
    )
    backend_bridges = payload.get("backend_bridges") or []
    if backend_bridges:
        for bridge in backend_bridges:
            lines.extend(
                [
                    f"- `{bridge['backend_id']}` title=`{bridge['title']}` type=`{bridge['backend_type']}` "
                    f"status=`{bridge['status']}` card_status=`{bridge['card_status']}` sources=`{bridge['source_count']}`",
                    f"  card_path=`{bridge['card_path'] or '(missing)'}`",
                    f"  backend_root=`{bridge['backend_root'] or '(missing)'}`",
                    f"  artifact_kinds=`{', '.join(bridge['artifact_kinds']) or '(missing)'}`",
                    f"  canonical_targets=`{', '.join(bridge['canonical_targets']) or '(missing)'}`",
                    f"  l0_registration_script=`{bridge['l0_registration_script'] or '(missing)'}`",
                ]
            )
    else:
        lines.append("- None registered.")
    promotion_gate = payload.get("promotion_gate") or {}
    lines.extend(
        [
            "",
            "## L2 promotion gate",
            "",
            f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
            f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
            f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
            f"- Gate JSON: `{promotion_gate.get('path') or '(missing)'}`",
            f"- Gate note: `{promotion_gate.get('note_path') or '(missing)'}`",
            f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
            f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
            f"- Review mode: `{promotion_gate.get('review_mode') or '(missing)'}`",
            f"- Canonical layer: `{promotion_gate.get('canonical_layer') or '(missing)'}`",
            f"- Coverage status: `{promotion_gate.get('coverage_status') or '(missing)'}`",
            f"- Consensus status: `{promotion_gate.get('consensus_status') or '(missing)'}`",
            f"- Merge outcome: `{promotion_gate.get('merge_outcome') or '(missing)'}`",
            f"- Approved by: `{promotion_gate.get('approved_by') or '(pending)'}`",
            f"- Promoted units: `{', '.join(promotion_gate.get('promoted_units') or []) or '(none)'}`",
            "",
            "## Delivery rule",
            "",
            f"- {payload['delivery_rule'] or 'Outputs must name exact artifact paths and justify the chosen layer.'}",
            "",
            "## Editable protocol surfaces",
            "",
        ]
    )
    surfaces = payload.get("editable_protocol_surfaces") or []
    if surfaces:
        for surface in surfaces:
            lines.append(f"- [{surface['surface']}] `{surface['path']}` {surface['role']}")
    else:
        lines.append("- No editable protocol surfaces are currently registered.")
    queue_surface = payload.get("action_queue_surface") or {}
    decision_surface = payload.get("decision_surface") or {}
    lines.extend(
        [
            "",
            "## Queue contract snapshot",
            "",
            f"- Queue source: `{queue_surface.get('queue_source') or '(missing)'}`",
            f"- Declared contract path: `{queue_surface.get('declared_contract_path') or '(missing)'}`",
            f"- Generated contract JSON: `{queue_surface.get('generated_contract_path') or '(missing)'}`",
            f"- Generated contract note: `{queue_surface.get('generated_contract_note_path') or '(missing)'}`",
            "",
            "## Decision surface snapshot",
            "",
            f"- Decision mode: `{decision_surface.get('decision_mode') or '(missing)'}`",
            f"- Decision source: `{decision_surface.get('decision_source') or '(missing)'}`",
            f"- Decision contract status: `{decision_surface.get('decision_contract_status') or '(missing)'}`",
            f"- Control note path: `{decision_surface.get('control_note_path') or '(missing)'}`",
            f"- Selected action: `{decision_surface.get('selected_action_id') or '(missing)'}`",
            f"- Momentum: `{decision_surface.get('momentum_status') or '(missing)'}`",
            f"- Stuckness: `{decision_surface.get('stuckness_status') or '(missing)'}`",
            f"- Surprise: `{decision_surface.get('surprise_status') or '(missing)'}`",
            f"- Research judgment note: `{decision_surface.get('research_judgment_note_path') or '(missing)'}`",
            "",
            "## Pending actions snapshot",
            "",
        ]
    )
    pending_actions = payload.get("pending_actions") or []
    if pending_actions:
        for idx, row in enumerate(pending_actions, start=1):
            lines.append(
                f"{idx}. [{row['action_type']}] {row['summary']} "
                f"(auto_runnable={str(row['auto_runnable']).lower()}, queue_source={row['queue_source']})"
            )
    else:
        lines.append("- No pending actions are currently registered.")
    return "\n".join(lines) + "\n"

def materialize_runtime_protocol_bundle(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    human_request: str | None = None,
    load_profile: str | None = None,
    requested_max_auto_steps: int | None = None,
    applied_max_auto_steps: int | None = None,
    auto_step_budget_reason: str | None = None,
) -> dict[str, str]:
    runtime_root = self._ensure_runtime_root(topic_slug)
    topic_state = _read_json(runtime_root / "topic_state.json") or {}
    resolved_load_profile, load_profile_reason = self._resolve_load_profile(
        explicit_load_profile=load_profile,
        human_request=human_request,
        topic_state=topic_state,
    )
    topic_state = self._persist_load_profile_state(
        topic_slug=topic_slug,
        load_profile=resolved_load_profile,
        reason=load_profile_reason,
        updated_by=updated_by,
    )
    interaction_state = _read_json(runtime_root / "interaction_state.json") or {}
    promotion_gate = self._load_promotion_gate(topic_slug) or {}
    promotion_gate_note_path = (
        self._relativize(self._promotion_gate_paths(topic_slug)["note"])
        if self._promotion_gate_paths(topic_slug)["note"].exists()
        else str((promotion_gate or {}).get("note_path") or "")
    )
    queue_rows = _read_jsonl(runtime_root / "action_queue.jsonl")
    queue_surface = interaction_state.get("action_queue_surface") or {}
    decision_surface = interaction_state.get("decision_surface") or {}
    research_mode_profile = topic_state.get("research_mode_profile") or {}
    pending_actions, selected_pending_action = self._pending_action_context(
        queue_rows,
        decision_surface,
    )
    backend_bridges = build_runtime_backend_bridges(self, topic_slug=topic_slug, topic_state=topic_state)
    shell_surfaces = self.ensure_topic_shell_surfaces(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
        topic_state=topic_state,
        interaction_state=interaction_state,
        promotion_gate=promotion_gate,
        queue_rows=queue_rows,
    )
    research_contract = shell_surfaces["research_question_contract"]
    validation_contract = shell_surfaces["validation_contract"]
    idea_packet = dict(shell_surfaces["idea_packet"])
    idea_packet["path"] = self._relativize(Path(shell_surfaces["idea_packet_path"]))
    idea_packet["note_path"] = self._relativize(Path(shell_surfaces["idea_packet_note_path"]))
    operator_checkpoint = dict(shell_surfaces["operator_checkpoint"])
    operator_checkpoint["path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_path"]))
    operator_checkpoint["note_path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_note_path"]))
    operator_checkpoint["ledger_path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_ledger_path"]))
    promotion_readiness = dict(shell_surfaces["promotion_readiness"])
    promotion_readiness["path"] = self._relativize(Path(shell_surfaces["promotion_readiness_path"]))
    validation_review_bundle = dict(shell_surfaces["validation_review_bundle"])
    validation_review_bundle["path"] = self._relativize(Path(shell_surfaces["validation_review_bundle_path"]))
    validation_review_bundle["note_path"] = self._relativize(Path(shell_surfaces["validation_review_bundle_note_path"]))
    source_intelligence = normalized_source_intelligence(
        topic_slug=topic_slug,
        shell_surfaces=shell_surfaces,
        relativize=self._relativize,
    )
    graph_analysis = normalized_graph_analysis(
        topic_slug=topic_slug,
        shell_surfaces=shell_surfaces,
        relativize=self._relativize,
    )
    open_gap_summary = dict(shell_surfaces["open_gap_summary"])
    open_gap_summary["path"] = self._relativize(Path(shell_surfaces["gap_map_path"]))
    strategy_memory = dict(
        shell_surfaces.get("strategy_memory")
        or {
            "topic_slug": topic_slug,
            "latest_run_id": str(topic_state.get("latest_run_id") or ""),
            "status": "absent",
            "lane": self._lane_for_modes(
                template_mode=research_contract.get("template_mode"),
                research_mode=research_contract.get("research_mode"),
            ),
            "row_count": 0,
            "relevant_count": 0,
            "helpful_count": 0,
            "harmful_count": 0,
            "latest_path": None,
            "relevant_paths": [],
            "guidance": [],
            "summary": "No run-local strategy memory is currently recorded for this topic.",
        }
    )
    topic_skill_projection = dict(
        shell_surfaces.get("topic_skill_projection")
        or {
            "id": f"topic_skill_projection:{_slugify(topic_slug)}",
            "topic_slug": topic_slug,
            "source_topic_slug": topic_slug,
            "run_id": str(topic_state.get("latest_run_id") or ""),
            "title": f"{self._topic_display_title(topic_slug)} Topic Skill Projection",
            "summary": "No validated topic-skill projection is currently available for this topic.",
            "lane": self._lane_for_modes(
                template_mode=research_contract.get("template_mode"),
                research_mode=research_contract.get("research_mode"),
            ),
            "status": "not_applicable",
            "status_reason": "No topic-skill projection was materialized for this topic.",
            "candidate_id": None,
            "intended_l2_target": None,
            "entry_signals": [],
            "required_first_reads": [],
            "required_first_routes": [],
            "benchmark_first_rules": [],
            "operator_checkpoint_rules": [],
            "operation_trust_requirements": [],
            "strategy_guidance": [],
            "forbidden_proxies": [],
            "derived_from_artifacts": [],
            "path": None,
            "note_path": None,
            "updated_at": _now_iso(),
            "updated_by": updated_by,
        }
    )
    topic_completion = dict(shell_surfaces["topic_completion"])
    topic_completion["path"] = self._relativize(Path(shell_surfaces["topic_completion_note_path"]))
    statement_compilation = dict(shell_surfaces["statement_compilation"])
    statement_compilation["path"] = self._relativize(Path(shell_surfaces["statement_compilation_note_path"]))
    lean_bridge = dict(shell_surfaces["lean_bridge"])
    lean_bridge["path"] = self._relativize(Path(shell_surfaces["lean_bridge_note_path"]))
    active_research_contract = build_active_research_contract_payload(
        research_contract=research_contract,
        validation_contract=validation_contract,
        shell_surfaces=shell_surfaces,
        relativize=self._relativize,
    )
    active_research_contract["target_layers"] = self._dedupe_strings(active_research_contract.get("target_layers") or [])
    latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
    lane = self._lane_for_modes(
        template_mode=active_research_contract.get("template_mode"),
        research_mode=active_research_contract.get("research_mode"),
    )
    dependency_state = shell_surfaces.get("dependency_state") or self._topic_dependency_state(topic_slug)
    topic_status_explainability = shell_surfaces.get("topic_state_explainability") or {}
    research_judgment = normalize_research_judgment_for_bundle(self, shell_surfaces=shell_surfaces, topic_slug=topic_slug, runtime_root=runtime_root, latest_run_id=latest_run_id, updated_by=updated_by); research_taste = normalize_research_taste_for_bundle(self, shell_surfaces=shell_surfaces, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by); scratchpad = normalize_scratchpad_for_bundle(self, shell_surfaces=shell_surfaces, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by)
    collaborator_profile = normalize_collaborator_profile_for_bundle(self, shell_surfaces=shell_surfaces, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by); research_trajectory = normalize_research_trajectory_for_bundle(self, shell_surfaces=shell_surfaces, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by); mode_learning = normalize_mode_learning_for_bundle(self, shell_surfaces=shell_surfaces, runtime_root=runtime_root, topic_slug=topic_slug, updated_by=updated_by)
    runtime_focus = dict(
        shell_surfaces.get("runtime_focus")
        or self._topic_synopsis_runtime_focus(
            topic_state=topic_state,
            topic_status_explainability=topic_status_explainability,
            dependency_state=dependency_state,
            promotion_readiness=promotion_readiness,
        )
    )
    candidate_rows = self._candidate_rows_for_run(topic_slug, latest_run_id)
    theory_context_injection = build_theory_context_injection(
        self,
        topic_slug=topic_slug,
        latest_run_id=latest_run_id or None,
        lane=lane,
        validation_review_bundle=validation_review_bundle,
        statement_compilation=statement_compilation,
        lean_bridge=lean_bridge,
        topic_skill_projection=topic_skill_projection,
        selected_pending_action=selected_pending_action,
        candidate_rows=candidate_rows,
    )
    loop_detection = materialize_loop_detection(
        self,
        topic_slug=topic_slug,
        updated_by=updated_by,
        lane=lane,
        selected_pending_action=selected_pending_action,
    )
    knowledge_packets = build_knowledge_packets_from_candidates(
        topic_slug,
        candidate_rows,
        lane=lane,
        updated_at=_now_iso(),
        updated_by=updated_by,
        kernel_root=self.kernel_root,
    )
    knowledge_packet_paths = [
        self._relativize(Path(item["path"]))
        for item in knowledge_packets
    ]
    all_decisions = get_all_decision_points(topic_slug, kernel_root=self.kernel_root)
    pending_decisions = list_pending_decision_points(topic_slug, kernel_root=self.kernel_root)
    decision_traces = get_decision_traces(topic_slug, kernel_root=self.kernel_root)
    latest_resolved_trace = decision_traces[-1] if decision_traces else None
    pending_decisions_payload = {
        "topic_slug": topic_slug,
        "pending_count": len(pending_decisions),
        "blocking_count": sum(1 for row in pending_decisions if row.get("blocking")),
        "unresolved_ids": [str(row.get("id") or "") for row in pending_decisions if str(row.get("id") or "").strip()],
        "latest_resolved_trace_ref": str((latest_resolved_trace or {}).get("id") or ""),
        "latest_resolved_summary": str((latest_resolved_trace or {}).get("decision_summary") or ""),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    pending_decisions_written = write_pending_decisions_projection(
        topic_slug,
        pending_decisions_payload,
        kernel_root=self.kernel_root,
    )
    promotion_readiness_written = write_promotion_readiness_projection(
        topic_slug,
        promotion_readiness,
        kernel_root=self.kernel_root,
    )
    topic_synopsis_truth_sources = self._topic_synopsis_truth_sources(
        topic_slug=topic_slug,
        topic_state=topic_state,
        interaction_state=interaction_state,
        idea_packet=idea_packet,
        operator_checkpoint=operator_checkpoint,
        research_question_contract_path=Path(shell_surfaces["research_question_contract_path"]),
        promotion_readiness_path=promotion_readiness_written["path"],
        promotion_gate_path=self._promotion_gate_paths(topic_slug)["json"]
        if self._promotion_gate_paths(topic_slug)["json"].exists()
        else None,
    )
    topic_synopsis_payload = {
        "id": f"topic_synopsis:{topic_slug}",
        "topic_slug": topic_slug,
        "title": str(active_research_contract.get("title") or self._topic_display_title(topic_slug)),
        "question": str(active_research_contract.get("question") or ""),
        "lane": lane,
        "load_profile": resolved_load_profile,
        "status": str(active_research_contract.get("status") or "active"),
        "human_request": human_request or str(interaction_state.get("human_request") or ""),
        "assumptions": self._dedupe_strings(list(research_contract.get("assumptions") or [])),
        "l1_source_intake": research_contract.get("l1_source_intake") or empty_l1_source_intake(),
        "runtime_focus": runtime_focus,
        "truth_sources": topic_synopsis_truth_sources,
        "next_action_summary": str(runtime_focus.get("next_action_summary") or "No bounded action is currently selected."),
        "open_gap_summary": str(open_gap_summary.get("summary") or ""),
        "pending_decision_count": len(pending_decisions),
        "knowledge_packet_paths": knowledge_packet_paths,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    topic_synopsis_written = write_topic_synopsis(
        topic_slug,
        topic_synopsis_payload,
        kernel_root=self.kernel_root,
    )
    promotion_trace_payload = {
        "id": f"promotion_trace:{_slugify(topic_slug)}",
        "topic_slug": topic_slug,
        "trace_scope": "topic_latest",
        "status": str(promotion_readiness.get("status") or "not_ready"),
        "gate_status": str(promotion_readiness.get("gate_status") or ""),
        "human_gate_status": str(promotion_gate.get("status") or "not_requested"),
        "summary": str(promotion_readiness.get("summary") or ""),
        "candidate_refs": self._dedupe_strings(
            list(promotion_readiness.get("ready_candidate_ids") or [])
            + [str(row.get("candidate_id") or "") for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
        ),
        "packet_refs": knowledge_packet_paths,
        "decision_trace_refs": [str(row.get("id") or "") for row in decision_traces[-5:] if str(row.get("id") or "").strip()],
        "audit_refs": self._dedupe_strings(
            [
                self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                self._relativize(Path(shell_surfaces["gap_map_path"])),
                self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
            ]
        ),
        "backend_target": {
            "backend_id": str(promotion_gate.get("backend_id") or ""),
            "target_backend_root": str(promotion_gate.get("target_backend_root") or ""),
            "canonical_layer": str(promotion_gate.get("canonical_layer") or "L2"),
        },
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    promotion_trace_written = write_promotion_trace(
        topic_slug,
        promotion_trace_payload,
        kernel_root=self.kernel_root,
    )
    current_from_layer = str(topic_state.get("last_materialized_stage") or topic_state.get("resume_stage") or "").strip()
    current_to_layer = str(topic_state.get("resume_stage") or current_from_layer).strip()
    transition_history = load_transition_history(topic_slug, kernel_root=self.kernel_root)
    if current_from_layer and current_to_layer:
        transition_history = append_transition_history(
            topic_slug,
            {
                "run_id": str(topic_state.get("latest_run_id") or ""),
                "event_kind": "runtime_resume_state",
                "from_layer": current_from_layer,
                "to_layer": current_to_layer,
                "reason": str(
                    topic_state.get("resume_reason")
                    or runtime_focus.get("why_this_topic_is_here")
                    or open_gap_summary.get("summary")
                    or "Runtime state transition recorded."
                ),
                "evidence_refs": self._dedupe_strings(
                    [
                        self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                        self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                        self._relativize(Path(shell_surfaces["gap_map_path"])),
                        self._relativize(Path(shell_surfaces["validation_review_bundle_note_path"])),
                        self._relativize(Path(promotion_trace_written["path"])),
                    ]
                ),
                "recorded_at": _now_iso(),
                "recorded_by": updated_by,
            },
            kernel_root=self.kernel_root,
        )["transition_history"]
    active_research_contract["route_transition_receipt"] = build_route_transition_receipt_payload(
        topic_slug=topic_slug,
        route_transition_intent=active_research_contract.get("route_transition_intent") or {},
        transition_history=transition_history,
    )
    active_research_contract["route_transition_resolution"] = build_route_transition_resolution_payload(
        topic_slug=topic_slug,
        route_transition_intent=active_research_contract.get("route_transition_intent") or {},
        route_transition_receipt=active_research_contract.get("route_transition_receipt") or {},
        route_activation=active_research_contract.get("route_activation") or {},
    )
    active_research_contract["route_transition_discrepancy"] = build_route_transition_discrepancy_payload(
        topic_slug=topic_slug,
        route_transition_resolution=active_research_contract.get("route_transition_resolution") or {},
        route_transition_receipt=active_research_contract.get("route_transition_receipt") or {},
    )
    active_research_contract["route_transition_repair"] = build_route_transition_repair_payload(
        topic_slug=topic_slug,
        route_transition_discrepancy=active_research_contract.get("route_transition_discrepancy") or {},
        route_transition_resolution=active_research_contract.get("route_transition_resolution") or {},
        route_activation=active_research_contract.get("route_activation") or {},
    )
    active_research_contract["route_transition_escalation"] = build_route_transition_escalation_payload(
        topic_slug=topic_slug,
        route_transition_repair=active_research_contract.get("route_transition_repair") or {},
        operator_checkpoint=operator_checkpoint,
    )
    active_research_contract["route_transition_clearance"] = build_route_transition_clearance_payload(
        topic_slug=topic_slug,
        route_transition_escalation=active_research_contract.get("route_transition_escalation") or {},
        operator_checkpoint=operator_checkpoint,
    )
    active_research_contract["route_transition_followthrough"] = build_route_transition_followthrough_payload(
        topic_slug=topic_slug,
        route_transition_clearance=active_research_contract.get("route_transition_clearance") or {},
    )
    active_research_contract["route_transition_resumption"] = build_route_transition_resumption_payload(
        topic_slug=topic_slug,
        route_transition_followthrough=active_research_contract.get("route_transition_followthrough") or {},
        route_transition_resolution=active_research_contract.get("route_transition_resolution") or {},
        route_activation=active_research_contract.get("route_activation") or {},
        transition_history=transition_history,
    )
    active_research_contract["route_transition_commitment"] = build_route_transition_commitment_payload(
        topic_slug=topic_slug,
        route_transition_resumption=active_research_contract.get("route_transition_resumption") or {},
        route_activation=active_research_contract.get("route_activation") or {},
        competing_hypotheses=active_research_contract.get("competing_hypotheses") or [],
    )
    active_research_contract["route_transition_authority"] = build_route_transition_authority_payload(
        topic_slug=topic_slug,
        route_transition_commitment=active_research_contract.get("route_transition_commitment") or {},
        route_activation=active_research_contract.get("route_activation") or {},
    )
    runtime_protocol_note = self._relativize(runtime_root / "runtime_protocol.generated.md")
    research_guardrails_note = self._relativize(self.kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md")
    formal_theory_upstream_note = self._relativize(
        self.kernel_root / "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md"
    )
    section_formalization_note = self._relativize(
        self.kernel_root / "SECTION_FORMALIZATION_PROTOCOL.md"
    )
    formal_theory_active = str(active_research_contract.get("research_mode") or "").strip() == "formal_derivation" or str(active_research_contract.get("template_mode") or "").strip() == "formal_theory"
    control_note_path = str((topic_state.get("pointers") or {}).get("control_note_path") or self._relativize(runtime_root / "control_note.md"))
    topic_synopsis_path = self._relativize(self._topic_synopsis_path(topic_slug))
    decision_override_active = control_note_override_active(decision_surface)
    research_judgment_read = research_judgment_must_read_entry(research_judgment); research_taste_read = research_taste_must_read_entry(research_taste); scratchpad_read = scratchpad_must_read_entry(scratchpad)
    collaborator_profile_read = collaborator_profile_must_read_entry(collaborator_profile); research_trajectory_read = research_trajectory_must_read_entry(research_trajectory); mode_learning_read = mode_learning_must_read_entry(mode_learning)
    must_read_now: list[dict[str, str]] = []
    if resolved_load_profile == "light":
        must_read_now.extend(
            light_profile_primary_reads(
                topic_dashboard_path=self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                research_question_contract_note_path=self._relativize(
                    Path(shell_surfaces["research_question_contract_note_path"])
                ),
            )
        )
        if decision_override_active and control_note_path:
            must_read_now.insert(0, decision_override_read(control_note_path))
        if strategy_memory.get("relevant_count") and strategy_memory.get("latest_path"):
            must_read_now.append(
                {
                    "path": str(strategy_memory.get("latest_path")),
                    "reason": "Recent strategy memory overlaps with the current route. Consult it before trusting heuristic route selection.",
                }
            )
        if str(topic_skill_projection.get("status") or "") == "available" and topic_skill_projection.get("note_path"):
            must_read_now.append(
                {
                    "path": str(topic_skill_projection.get("note_path")),
                    "reason": self._topic_skill_projection_read_reason(topic_skill_projection),
                }
            )
        if str(graph_analysis.get("note_path") or "").strip():
            must_read_now.append(
                {
                    "path": str(graph_analysis.get("note_path")),
                    "reason": "Current graph-analysis summary for cross-source bridges, question seeds, and recent graph drift.",
                }
            )
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            must_read_now.insert(
                0,
                {
                    "path": str(idea_packet.get("note_path") or ""),
                    "reason": "Clarify the current idea packet before deeper execution.",
                },
            )
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            must_read_now.insert(
                0,
                {
                    "path": str(operator_checkpoint.get("note_path") or ""),
                    "reason": "Resolve the active operator checkpoint before deeper execution.",
                },
            )
    else:
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            must_read_now.append(
                {
                    "path": str(operator_checkpoint.get("note_path") or ""),
                    "reason": "Active operator checkpoint. Resolve this human-decision surface before deeper execution.",
                }
            )
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            must_read_now.append(
                {
                    "path": str(idea_packet.get("note_path") or ""),
                    "reason": "Clarify the idea packet before substantive execution. This is the active intent gate for the topic.",
                }
            )
        must_read_now.extend(
            [
                {
                    "path": self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                    "reason": "Primary human runtime surface for the current topic. Start here before drilling into supporting slices.",
                },
                {
                    "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                    "reason": "Active research question, scope, deliverables, and anti-proxy rules for this topic.",
                },
                {
                    "path": control_note_path,
                    "reason": "Current human steering note for this topic.",
                },
                {
                    "path": topic_synopsis_path,
                    "reason": "Primary machine runtime synopsis behind the dashboard and scheduler/status projections.",
                },
                {
                    "path": self._relativize(Path(shell_surfaces["validation_review_bundle_note_path"])),
                    "reason": "Primary L4 review entry surface before opening promotion-readiness or gap-detail notes.",
                },
                {
                    "path": self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                    "reason": "Topic-completion gate over regression support, follow-up return debt, and blocker honesty.",
                },
                {
                    "path": self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                    "reason": "Current validation route, required checks, and failure modes for this topic.",
                },
            ]
        )
        innovation_direction_path = str((topic_state.get("pointers") or {}).get("innovation_direction_path") or "")
        if innovation_direction_path:
            must_read_now.append(
                {
                    "path": innovation_direction_path,
                    "reason": "Current human innovation target, steering decision, and novelty boundary for this topic.",
                }
            )
        if strategy_memory.get("relevant_count") and strategy_memory.get("latest_path"):
            must_read_now.append(
                {
                    "path": str(strategy_memory.get("latest_path")),
                    "reason": "Recent strategy memory overlaps with the current route. Consult it before trusting heuristic route selection.",
                }
            )
        if str(topic_skill_projection.get("status") or "") == "available" and topic_skill_projection.get("note_path"):
            must_read_now.append(
                {
                    "path": str(topic_skill_projection.get("note_path")),
                    "reason": self._topic_skill_projection_read_reason(topic_skill_projection),
                }
            )
        if str(graph_analysis.get("note_path") or "").strip():
            must_read_now.append(
                {
                    "path": str(graph_analysis.get("note_path")),
                    "reason": "Current graph-analysis summary for cross-source bridges, question seeds, and recent graph drift.",
                }
            )
        must_read_now.append(
            {
                "path": research_guardrails_note,
                "reason": "Global research-contract, bounded-action, and anti-proxy validation guardrails for non-trivial work.",
            }
        )
    for entry in (collaborator_profile_read, research_trajectory_read, mode_learning_read, research_judgment_read, research_taste_read, scratchpad_read):
        if entry is not None: must_read_now.append(entry)
    if str(loop_detection.get("status") or "") == "active" and str(loop_detection.get("note_path") or "").strip():
        must_read_now.append(
            {
                "path": str(loop_detection.get("note_path") or ""),
                "reason": "Repeated theorem-facing retries crossed the loop-detection threshold. Read this intervention note before repeating the same approach.",
            }
        )
    may_defer_until_trigger: list[dict[str, str]] = []
    must_read_paths = {item["path"] for item in must_read_now}
    selected_consultation_candidate_note_path = str(
        (topic_state.get("pointers") or {}).get("selected_consultation_candidate_note_path")
        or ""
    ).strip()
    selected_candidate_route_choice_note_path = str(
        (topic_state.get("pointers") or {}).get("selected_candidate_route_choice_note_path")
        or ""
    ).strip()
    post_promotion_followup_note_path = str(
        (topic_state.get("pointers") or {}).get("post_promotion_followup_note_path")
        or ""
    ).strip()
    post_promotion_blocker_route_choice_note_path = str(
        (topic_state.get("pointers") or {}).get("post_promotion_blocker_route_choice_note_path")
        or ""
    ).strip()
    if (
        str((selected_pending_action or {}).get("action_type") or "").strip()
        == "selected_consultation_candidate_followup"
        and selected_consultation_candidate_note_path
        and selected_consultation_candidate_note_path not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": selected_consultation_candidate_note_path,
                "reason": "Read the durable consultation-followup selection before choosing the next deeper candidate action.",
            },
        )
        must_read_paths.add(selected_consultation_candidate_note_path)
    if (
        str((selected_pending_action or {}).get("action_type") or "").strip()
        in {
            "l2_promotion_review",
            "request_promotion",
            "approve_promotion",
            "promote_candidate",
            "auto_promote_candidate",
            "select_validation_route",
        }
        and selected_candidate_route_choice_note_path
        and selected_candidate_route_choice_note_path not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": selected_candidate_route_choice_note_path,
                "reason": "Read the durable selected-candidate route choice before deeper execution continues.",
            },
        )
        must_read_paths.add(selected_candidate_route_choice_note_path)
    if (
        str((selected_pending_action or {}).get("action_type") or "").strip()
        in {"review_topic_completion_blockers", "inspect_topic_completion"}
        and post_promotion_followup_note_path
        and post_promotion_followup_note_path not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": post_promotion_followup_note_path,
                "reason": "Read the durable post-promotion followup before reopening another bounded route after Layer 2 writeback.",
            },
        )
        must_read_paths.add(post_promotion_followup_note_path)
    if (
        str((selected_pending_action or {}).get("action_type") or "").strip()
        in {"review_statement_compilation", "review_lean_bridge"}
        and post_promotion_blocker_route_choice_note_path
        and post_promotion_blocker_route_choice_note_path not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": post_promotion_blocker_route_choice_note_path,
                "reason": "Read the durable blocker-route choice before opening statement-compilation or Lean-bridge review after post-promotion completion blockers.",
            },
        )
        must_read_paths.add(post_promotion_blocker_route_choice_note_path)
    selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    if (
        selected_action_type == "review_statement_compilation"
        and str(statement_compilation.get("path") or "").strip()
        and str(statement_compilation.get("path") or "").strip() not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": str(statement_compilation.get("path") or "").strip(),
                "reason": "Read the active statement-compilation packet set before reviewing the promoted candidate's proof holes.",
            },
        )
        must_read_paths.add(str(statement_compilation.get("path") or "").strip())
    if (
        selected_action_type == "review_lean_bridge"
        and str(lean_bridge.get("path") or "").strip()
        and str(lean_bridge.get("path") or "").strip() not in must_read_paths
    ):
        must_read_now.insert(
            0,
            {
                "path": str(lean_bridge.get("path") or "").strip(),
                "reason": "Read the active Lean-bridge packet set before reviewing the promoted candidate's remaining proof obligations.",
            },
        )
        must_read_paths.add(str(lean_bridge.get("path") or "").strip())
    for candidate, trigger, reason in (
        (
            "interaction_state.json",
            "decision_override_present",
            "Only open when raw control or contract state is needed.",
        ),
        (
            "next_action_decision.md",
            "decision_override_present",
            "Open when you need the full selected-action rationale rather than the brief summary.",
        ),
        (
            "action_queue_contract.generated.md",
            "decision_override_present",
            "Open when queue-contract details matter more than the brief queue snapshot.",
        ),
        (
            "control_note.md",
            "decision_override_present",
            "Open when declared human steering or a durable decision override is active.",
        ),
        (
            "topic_synopsis.json",
            "runtime_truth_audit",
            "Open when the machine synopsis is needed for status auditing, projection debugging, or runtime-truth inspection beyond the dashboard.",
        ),
        (
            "promotion_gate.md",
            "promotion_intent",
            "Only mandatory when current work could create, approve, or execute writeback.",
        ),
        (
            Path(shell_surfaces["promotion_readiness_path"]).name,
            "promotion_intent",
            "Promotion readiness details become mandatory when writeback or gate routing is active.",
        ),
        (
            Path(shell_surfaces["gap_map_path"]).name,
            "capability_gap_blocker",
            "Gap-map details become mandatory when the topic must return to L0 or resolve explicit blockers.",
        ),
        (
            Path(shell_surfaces["lean_bridge_note_path"]).name,
            "proof_completion_review",
            "Lean-bridge packets become mandatory when proof-heavy work is being decomposed into formal obligations.",
        ),
        (
            Path(shell_surfaces["followup_reintegration_note_path"]).name,
            "non_trivial_consultation",
            "Reintegration receipts matter when child follow-up topics are returning evidence to the parent topic.",
        ),
        (
            Path(shell_surfaces["followup_gap_writeback_note_path"]).name,
            "capability_gap_blocker",
            "Open this when unresolved child follow-up returns have written new parent-side gap debt.",
        ),
        (
            "agent_brief.md",
            "verification_route_selection",
            "Legacy execution brief. Open only when an external execution lane still needs the older stage-specific summary.",
        ),
        (
            "operator_console.md",
            "decision_override_present",
            "Legacy operator view. Open only when you need the older queue/checkpoint-centric surface beyond the primary dashboard.",
        ),
        (
            "conformance_report.md",
            "decision_override_present",
            "Open when you need the detailed audit prose rather than the condensed runtime status surfaces.",
        ),
    ):
        candidate_path = runtime_root / candidate
        if candidate_path.exists():
            relative_candidate_path = self._relativize(candidate_path)
            if relative_candidate_path in must_read_paths:
                continue
            may_defer_until_trigger.append(
                {
                    "path": relative_candidate_path,
                    "trigger": trigger,
                    "reason": reason,
                }
            )
    consultation_index_path = str((topic_state.get("pointers") or {}).get("consultation_index_path") or "")
    innovation_decisions_path = str((topic_state.get("pointers") or {}).get("innovation_decisions_path") or "")
    closed_loop_surface = interaction_state.get("closed_loop") or {}
    latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
    selected_action_handler_args = (selected_pending_action or {}).get("handler_args") or {}
    active_run_id = str(selected_action_handler_args.get("run_id") or latest_run_id or "").strip()
    active_candidate_id = str(
        selected_action_handler_args.get("candidate_id") or promotion_gate.get("candidate_id") or ""
    ).strip()
    active_candidate_type = str(
        selected_action_handler_args.get("candidate_type") or promotion_gate.get("candidate_type") or ""
    ).strip()
    theory_packet_reads: list[str] = []
    if active_run_id and active_candidate_id:
        theory_packet_paths = self._theory_packet_paths(topic_slug, active_run_id, active_candidate_id)
        for key in (
            "structure_map",
            "coverage_ledger",
            "notation_table",
            "derivation_graph",
            "agent_consensus",
        ):
            path = theory_packet_paths[key]
            if path.exists():
                theory_packet_reads.append(self._relativize(path))
    verification_route_reads = [
        path
        for path in (
            str(closed_loop_surface.get("selected_route_path") or ""),
            str(closed_loop_surface.get("execution_task_path") or ""),
            str(closed_loop_surface.get("returned_result_path") or ""),
        )
        if path
    ]
    if consultation_index_path:
        may_defer_until_trigger.append(
            {
                "path": consultation_index_path,
                "trigger": "non_trivial_consultation",
                "reason": "Consultation details are only mandatory when L2 memory materially changes the current work.",
            }
        )
    if innovation_decisions_path:
        may_defer_until_trigger.append(
            {
                "path": innovation_decisions_path,
                "trigger": "decision_override_present",
                "reason": "Open the steering decision log when you need the durable history behind a control-note redirect.",
            }
        )
    capability_report_path = runtime_root / "capability_report.md"
    if capability_report_path.exists():
        may_defer_until_trigger.append(
            {
                "path": self._relativize(capability_report_path),
                "trigger": "capability_gap_blocker",
                "reason": "Capability details are only mandatory when a missing workflow or backend is the honest blocker.",
            }
        )
    if strategy_memory.get("row_count") and strategy_memory.get("latest_path") and not strategy_memory.get("relevant_count"):
        may_defer_until_trigger.append(
            {
                "path": str(strategy_memory.get("latest_path")),
                "trigger": "verification_route_selection",
                "reason": "Consult prior strategy memory when a later route choice starts resembling an earlier lane or guardrail pattern.",
            }
        )
    if str(topic_skill_projection.get("status") or "") != "available" and topic_skill_projection.get("note_path"):
        may_defer_until_trigger.append(
            {
                "path": str(topic_skill_projection.get("note_path")),
                "trigger": "verification_route_selection",
                "reason": self._topic_skill_projection_deferred_reason(topic_skill_projection),
            }
        )
    for path in theory_packet_reads:
        may_defer_until_trigger.append(
            {
                "path": path,
                "trigger": "proof_completion_review",
                "reason": "Theory-packet coverage and derivation surfaces only become mandatory when proof completion is the current concern.",
            }
        )
    for path in verification_route_reads:
        may_defer_until_trigger.append(
            {
                "path": path,
                "trigger": "verification_route_selection",
                "reason": "Closed-loop route and execution details only become mandatory when validation-route selection or execution routing is the current concern.",
            }
        )
    read_order: list[str] = [item["path"] for item in must_read_now]
    if not read_order:
        read_order.append(self._relativize(runtime_root / "topic_state.json"))
    selected_action_summary = str(runtime_focus.get("next_action_summary") or "").strip()
    selected_action_type = str(
        runtime_focus.get("next_action_type") or (selected_pending_action or {}).get("action_type") or ""
    ).strip()
    selected_action_id = str(
        runtime_focus.get("next_action_id") or (selected_pending_action or {}).get("action_id") or ""
    ).strip()
    selected_action_auto_runnable = bool((selected_pending_action or {}).get("auto_runnable"))
    selected_action_label = selected_action_summary or (
        f"{selected_action_type} ({selected_action_id})" if selected_action_type else ""
    )
    immediate_allowed_work = []
    if selected_action_label:
        immediate_allowed_work.append(
            f"Continue bounded `{runtime_focus.get('resume_stage') or topic_state.get('resume_stage') or '(missing)'}` work on `{selected_action_label}`."
        )
    else:
        immediate_allowed_work.append(
            f"Resume bounded `{runtime_focus.get('resume_stage') or topic_state.get('resume_stage') or '(missing)'}` work using the declared decision surface."
        )
    immediate_allowed_work.append(
        "Prefer declared contracts and durable runtime artifacts over ad hoc browsing or memory-only routing."
    )
    if any(str(row.get("action_type") or "") == "skill_discovery" for row in pending_actions):
        immediate_allowed_work.append(
            "Run controlled skill discovery only if the capability gap is the honest blocker for the selected action."
        )
    if not selected_action_auto_runnable and selected_action_label:
        immediate_allowed_work.append(
            "Treat the currently selected action as manual follow-up unless a returned execution artifact proves otherwise."
        )
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        immediate_allowed_work = [
            f"Resolve `{operator_checkpoint.get('note_path') or '(missing)'}` before deeper execution.",
            "Limit the next step to answering the active operator checkpoint and syncing the affected durable artifacts.",
        ]
    if str(idea_packet.get("status") or "").strip() == "needs_clarification":
        immediate_allowed_work = [
            f"Clarify `{idea_packet.get('note_path') or '(missing)'}` and then synchronize the research and validation contracts.",
            "Limit the next step to intent clarification, scope tightening, and first-lane selection.",
        ]

    immediate_blocked_work = [
        "Do not promote or auto-promote material into Layer 2 unless the promotion trigger fires and the gate artifacts allow it.",
        "Do not bypass conformance, declared control notes, or decision contracts with heuristic queue guesses.",
        "Do not treat consultation as promotion or claim heavy execution happened without the corresponding returned result artifacts.",
        "Do not substitute polished prose, memory agreement, or missing execution evidence for the declared acceptance checks.",
    ]
    if str(idea_packet.get("status") or "").strip() == "needs_clarification":
        immediate_blocked_work.append(
            "Do not treat literature intake, benchmark execution, derivation work, or queue advancement as started until the idea packet is clarified."
        )
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        immediate_blocked_work.append(
            "Do not continue deeper research execution until the active operator checkpoint is answered or cancelled."
        )

    promotion_status = str(promotion_gate.get("status") or "not_requested")
    capability_gap_active = any(
        str(row.get("action_type") or "") == "skill_discovery" for row in pending_actions
    )
    contradiction_hint = any(
        needle in selected_action_label.lower()
        for needle in ("contradiction", "conflict", "regime mismatch")
    )
    proof_hint = bool(theory_packet_reads) and (
        active_candidate_type
        in {
            "equation_card",
            "theorem_card",
            "proof_fragment",
            "derivation_step",
            "derivation_object",
        }
        or any(
            needle in selected_action_label.lower()
            for needle in ("proof", "derivation", "theorem", "coverage")
        )
    )
    consultation_hint = any(
        needle in selected_action_label.lower()
        for needle in ("consult", "memory", "terminology", "candidate shape")
    )
    verification_route_hint = bool(verification_route_reads) and (
        selected_action_type in {"select_validation_route", "materialize_execution_task", "dispatch_execution_task"}
        or any(
            needle in selected_action_label.lower()
            for needle in ("validation route", "verification route", "execution task", "selected route")
        )
    )
    trust_hint = any(
        needle in selected_action_label.lower()
        for needle in ("trust", "baseline", "atomize")
    )
    promotion_hint = (
        promotion_status in {"requested", "approved"}
        or any(
            needle in selected_action_label.lower()
            for needle in ("promot", "writeback", "candidate")
        )
    )
    escalation_triggers = [
        {
            "trigger": "decision_override_present",
            "active": decision_override_active,
            "condition": "A control note or decision contract overrides heuristic queue selection.",
            "required_reads": [
                path
                for path in (
                    str(decision_surface.get("control_note_path") or ""),
                    str(decision_surface.get("decision_contract_path") or ""),
                    str(decision_surface.get("next_action_decision_note_path") or ""),
                    str(queue_surface.get("generated_contract_note_path") or ""),
                )
                if path
            ],
        },
        {
            "trigger": "promotion_intent",
            "active": promotion_hint,
            "condition": "The current work could create, approve, or execute Layer 2 or Layer 2_auto writeback.",
            "required_reads": [
                path
                for path in (
                    str(promotion_gate.get("path") or ""),
                    str(promotion_gate.get("note_path") or ""),
                )
                if path
            ],
        },
        {
            "trigger": "non_trivial_consultation",
            "active": consultation_hint,
            "condition": "L2 consultation materially changes terminology, candidate shape, validation route, or writeback intent.",
            "required_reads": [
                path
                for path in (
                    self._relativize(self.kernel_root / "L2_CONSULTATION_PROTOCOL.md"),
                    consultation_index_path,
                )
                if path
            ],
        },
        {
            "trigger": "capability_gap_blocker",
            "active": capability_gap_active,
            "condition": "A missing workflow or backend is the honest blocker for the selected action.",
            "required_reads": [
                path
                for path in (
                    self._relativize(self._research_root() / "adapters" / "openclaw" / "SKILL_ADAPTATION_PROTOCOL.md"),
                    self._relativize(capability_report_path) if capability_report_path.exists() else "",
                )
                if path
            ],
        },
        {
            "trigger": "proof_completion_review",
            "active": proof_hint,
            "condition": "Proof-heavy or derivation-heavy work must open the current theory-packet coverage and derivation surfaces before claiming completion.",
            "required_reads": theory_packet_reads,
        },
        {
            "trigger": "verification_route_selection",
            "active": verification_route_hint,
            "condition": "Closed-loop validation work must open the selected route and execution handoff surfaces before claiming execution or adjudication.",
            "required_reads": verification_route_reads,
        },
        {
            "trigger": "trust_missing",
            "active": trust_hint,
            "condition": "The current work wants to reuse an operation or method whose trust gate may not be satisfied.",
            "required_reads": [],
        },
        {
            "trigger": "contradiction_detected",
            "active": contradiction_hint,
            "condition": "Validation or family fusion exposes an unresolved contradiction or regime conflict.",
            "required_reads": [
                path
                for path in (
                    str((topic_state.get("pointers") or {}).get("promotion_decision_path") or ""),
                    str((topic_state.get("pointers") or {}).get("feedback_status_path") or ""),
                )
                if path
            ],
        },
        {
            "trigger": "formal_theory_upstream_scan",
            "active": formal_theory_active,
            "condition": "Formal-theory topics should periodically consult the living Lean discussion/code upstreams before claiming novelty, choosing Lean target shapes, or exporting bridge packets.",
            "required_reads": [formal_theory_upstream_note],
        },
        {
            "trigger": "runtime_truth_audit",
            "active": False,
            "condition": "The dashboard summary is insufficient and the underlying machine synopsis must be inspected directly.",
            "required_reads": [topic_synopsis_path],
        },
    ]

    recommended_protocol_slices = [
        {
            "slice": "current_execution_lane",
            "trigger": "",
            "paths": [item["path"] for item in must_read_now],
        },
        {
            "slice": "decision_and_queue_details",
            "trigger": "decision_override_present",
            "paths": [
                path
                for path in (
                    str(decision_surface.get("next_action_decision_note_path") or ""),
                    str(queue_surface.get("generated_contract_note_path") or ""),
                    str(queue_surface.get("declared_contract_path") or ""),
                )
                if path
            ],
        },
        {
            "slice": "consultation_memory",
            "trigger": "non_trivial_consultation",
            "paths": [
                path
                for path in (
                    self._relativize(self.kernel_root / "L2_CONSULTATION_PROTOCOL.md"),
                    consultation_index_path,
                )
                if path
            ],
        },
        {
            "slice": "promotion_and_writeback",
            "trigger": "promotion_intent",
            "paths": [
                path
                for path in (
                    str(promotion_gate.get("path") or ""),
                    str(promotion_gate.get("note_path") or ""),
                )
                if path
            ],
        },
        {
            "slice": "capability_and_skill_discovery",
            "trigger": "capability_gap_blocker",
            "paths": [
                path
                for path in (
                    self._relativize(self._research_root() / "adapters" / "openclaw" / "SKILL_ADAPTATION_PROTOCOL.md"),
                    self._relativize(capability_report_path) if capability_report_path.exists() else "",
                )
                if path
            ],
        },
        {
            "slice": "proof_completion_and_coverage",
            "trigger": "proof_completion_review",
            "paths": theory_packet_reads,
        },
        {
            "slice": "verification_route_selection",
            "trigger": "verification_route_selection",
            "paths": verification_route_reads,
        },
        {
            "slice": "formal_theory_living_upstreams",
            "trigger": "formal_theory_upstream_scan",
            "paths": [formal_theory_upstream_note],
        },
        {
            "slice": "formal_theory_section_packets",
            "trigger": "formal_theory_upstream_scan",
            "paths": [section_formalization_note],
        },
        {
            "slice": "runtime_truth_details",
            "trigger": "runtime_truth_audit",
            "paths": [topic_synopsis_path],
        },
    ]

    active_hard_constraints = [
        "Do not let progressive disclosure hide layer semantics, consultation obligations, trust gates, promotion gates, or conformance failures.",
        "Do not let the active research contract drift silently in scope, observables, deliverables, or acceptance tests.",
        "Do not treat heuristic queue rows as higher priority than declared control notes or decision contracts.",
        "Do not perform Layer 2 or Layer 2_auto writeback unless the corresponding gate artifacts say it is allowed.",
        "Do not treat proxy-success signals as validation when the declared execution or proof evidence is still missing.",
        "If definitions, cited derivations, or prior-work comparisons are missing, return to L0 and persist the recovery artifacts before continuing.",
        "When a named trigger becomes active, read its mandatory deeper surfaces before continuing execution.",
        "Do not collapse one compiled section packet into a whole-topic Lean completion claim.",
        "Do not treat live Lean community discussion as theorem truth, and do not cite physlib without recording the consulted commit, path, or declaration surface.",
    ]
    if str(idea_packet.get("status") or "").strip() == "needs_clarification":
        active_hard_constraints.append(
            f"Do not continue substantive execution until `{idea_packet.get('note_path') or '(missing)'}` resolves the missing intent fields."
        )
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        active_hard_constraints.append(
            f"Do not continue deeper execution until `{operator_checkpoint.get('note_path') or '(missing)'}` is answered or cancelled."
        )

    editable_surfaces: list[dict[str, str]] = []
    for surface in interaction_state.get("human_edit_surfaces") or []:
        path = str(surface.get("path") or "").strip()
        if not path or (path.startswith("(") and path.endswith(")")) or re.search(r"/\([^)]*missing[^)]*\)$", path):
            continue
        editable_surfaces.append(
            {
                "surface": str(surface.get("surface") or "unknown"),
                "path": path,
                "role": str(surface.get("role") or "").strip(),
            }
        )
    editable_surfaces.extend(
        [
            {
                "surface": "operator_checkpoint",
                "path": self._relativize(Path(shell_surfaces["operator_checkpoint_note_path"])),
                "role": "Answer the current human-checkpoint question or mark how the checkpoint was resolved.",
            },
            {
                "surface": "idea_packet",
                "path": self._relativize(Path(shell_surfaces["idea_packet_note_path"])),
                "role": "Edit the initial idea, novelty target, first validation route, and evidence bar before deeper execution.",
            },
            {
                "surface": "research_question_contract",
                "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                "role": "Edit the active question, scope, deliverables, and anti-proxy constraints.",
            },
            {
                "surface": "validation_contract",
                "path": self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                "role": "Edit the active validation route, required checks, and failure modes.",
            },
            {
                "surface": "validation_review_bundle",
                "path": self._relativize(Path(shell_surfaces["validation_review_bundle_note_path"])),
                "role": "Review the primary L4 review entry surface before drilling into supporting promotion or gap details.",
            },
            {
                "surface": "topic_dashboard",
                "path": self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                "role": "Human-readable topic summary for operator review and correction.",
            },
            {
                "surface": "topic_skill_projection",
                "path": str(
                    topic_skill_projection.get("note_path")
                    or self._relativize(
                        Path(
                            shell_surfaces.get("topic_skill_projection_note_path")
                            or self._topic_skill_projection_paths(topic_slug)["note"]
                        )
                    )
                ),
                "role": "Review the reusable execution projection derived from this mature topic.",
            },
            {
                "surface": "promotion_readiness",
                "path": self._relativize(Path(shell_surfaces["promotion_readiness_path"])),
                "role": "Review promotion blockers, ready candidates, and gate state.",
            },
            {
                "surface": "gap_map",
                "path": self._relativize(Path(shell_surfaces["gap_map_path"])),
                "role": "Review whether the topic must return to L0 or keep bounded gap packets open.",
            },
            {
                "surface": "topic_completion",
                "path": self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                "role": "Review topic-completion status against regression support and follow-up return debt.",
            },
            {
                "surface": "lean_bridge",
                "path": self._relativize(Path(shell_surfaces["lean_bridge_note_path"])),
                "role": "Review Lean-ready packets, declaration skeletons, and outstanding proof obligations.",
            },
            {
                "surface": "followup_gap_writeback",
                "path": self._relativize(Path(shell_surfaces["followup_gap_writeback_note_path"])),
                "role": "Review unresolved child follow-up returns that were written back into the parent gap surface.",
            },
        ]
    )
    editable_surfaces = dedupe_surface_entries(editable_surfaces)
    runtime_mode_preview = runtime_mode_payload_fragment(
        resume_stage=runtime_focus.get("resume_stage") or topic_state.get("resume_stage"),
        load_profile=resolved_load_profile,
        idea_packet_status=str(idea_packet.get("status") or ""),
        operator_checkpoint_status=str(operator_checkpoint.get("status") or ""),
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_label,
        must_read_now=must_read_now,
        may_defer_until_trigger=may_defer_until_trigger,
        escalation_triggers=escalation_triggers,
        human_request=human_request,
    )
    protocol_manifest = materialize_protocol_manifest(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        runtime_mode=str(runtime_mode_preview.get("runtime_mode") or ""),
        active_submode=str(runtime_mode_preview.get("active_submode") or ""),
        promotion_gate=promotion_gate,
        topic_completion=topic_completion,
        active_research_contract=active_research_contract,
        shell_surfaces=shell_surfaces,
        updated_by=updated_by,
    )
    manifest_read = protocol_manifest_must_read_entry(protocol_manifest)
    if manifest_read is not None:
        must_read_now.append(manifest_read)
    escalation_triggers = filter_escalation_triggers_for_mode(
        runtime_mode=str(runtime_mode_preview.get("runtime_mode") or ""),
        escalation_triggers=escalation_triggers,
    )
    runtime_mode_payload = runtime_mode_payload_fragment(
        resume_stage=runtime_focus.get("resume_stage") or topic_state.get("resume_stage"),
        load_profile=resolved_load_profile,
        idea_packet_status=str(idea_packet.get("status") or ""),
        operator_checkpoint_status=str(operator_checkpoint.get("status") or ""),
        selected_action_type=selected_action_type,
        selected_action_summary=selected_action_label,
        must_read_now=must_read_now,
        may_defer_until_trigger=may_defer_until_trigger,
        escalation_triggers=escalation_triggers,
        human_request=human_request,
    )
    staging_manifest = materialize_workspace_staging_manifest(self.kernel_root)
    refocused_context = refocus_context_for_runtime_mode(
        runtime_mode_payload=runtime_mode_payload,
        must_read_now=must_read_now,
        may_defer_until_trigger=may_defer_until_trigger,
        topic_dashboard_path=self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
        research_question_contract_note_path=self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
        control_note_path=control_note_path,
        topic_synopsis_path=topic_synopsis_path,
        idea_packet_path=str(idea_packet.get("note_path") or ""),
        operator_checkpoint_path=str(operator_checkpoint.get("note_path") or ""),
        validation_contract_path=self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
        validation_review_bundle_path=self._relativize(Path(shell_surfaces["validation_review_bundle_note_path"])),
        promotion_readiness_path=self._relativize(Path(shell_surfaces["promotion_readiness_path"])),
        promotion_gate_path=promotion_gate_note_path,
        topic_completion_path=self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
        verification_route_paths=verification_route_reads,
        l1_vault=active_research_contract.get("l1_vault") or {},
        canonical_index_path=self._relativize(self.kernel_root / "canonical" / "index.jsonl"),
        workspace_staging_manifest_path=self._relativize(Path(staging_manifest["json_path"])),
    )
    runtime_mode_payload = refocused_context["runtime_mode_payload"]
    must_read_now = refocused_context["must_read_now"]
    may_defer_until_trigger = refocused_context["may_defer_until_trigger"]
    read_order = [item["path"] for item in must_read_now]
    if not read_order:
        read_order.append(self._relativize(runtime_root / "topic_state.json"))
    control_plane_payload = build_runtime_bundle_control_plane(
        topic_state=topic_state,
        topic_synopsis=topic_synopsis_written["topic_synopsis"],
        runtime_mode_payload=runtime_mode_payload,
        operator_checkpoint=operator_checkpoint,
        decision_override_active=decision_override_active,
    )
    h_plane_payload = build_h_plane_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        operator_checkpoint=operator_checkpoint,
        promotion_gate=promotion_gate,
        updated_by=updated_by,
    )
    posture_seed = {
        "runtime_mode": runtime_mode_payload.get("runtime_mode"),
        "active_submode": runtime_mode_payload.get("active_submode"),
        "h_plane": h_plane_payload,
        "idea_packet": idea_packet,
    }
    human_interaction_posture = _human_interaction_posture_from_bundle(posture_seed)
    autonomy_posture = _autonomy_posture_from_bundle(
        posture_seed,
        requested_max_auto_steps=requested_max_auto_steps,
        applied_max_auto_steps=applied_max_auto_steps,
        budget_reason=auto_step_budget_reason,
    )

    payload = {
        "$schema": "https://aitp.local/schemas/progressive-disclosure-runtime-bundle.schema.json",
        "bundle_kind": "progressive_disclosure_runtime_bundle",
        "protocol_version": 1,
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "human_request": human_request or str(interaction_state.get("human_request") or ""),
        "resume_stage": topic_state.get("resume_stage"),
        "last_materialized_stage": topic_state.get("last_materialized_stage"),
        "research_mode": topic_state.get("research_mode") or active_research_contract.get("research_mode"),
        "load_profile": resolved_load_profile,
        **runtime_mode_payload,
        "control_plane": control_plane_payload,
        "h_plane": h_plane_payload,
        "human_interaction_posture": human_interaction_posture,
        "autonomy_posture": autonomy_posture,
        "topic_synopsis": {
            **topic_synopsis_written["topic_synopsis"],
            "path": self._relativize(Path(topic_synopsis_written["path"])),
        },
        "pending_decisions": {
            **pending_decisions_written["pending_decisions"],
            "path": self._relativize(Path(pending_decisions_written["path"])),
        },
        "active_research_contract": active_research_contract,
        "idea_packet": idea_packet,
        "operator_checkpoint": operator_checkpoint,
        "promotion_readiness": promotion_readiness,
        "validation_review_bundle": validation_review_bundle,
        "source_intelligence": source_intelligence,
        "graph_analysis": graph_analysis,
        "theory_context_injection": theory_context_injection,
        "loop_detection": loop_detection,
        "protocol_manifest": protocol_manifest,
        "open_gap_summary": open_gap_summary,
        "dependency_state": dependency_state,
        "strategy_memory": strategy_memory,
        "collaborator_profile": collaborator_profile,
        "research_trajectory": research_trajectory, "mode_learning": mode_learning,
        "research_judgment": research_judgment,
        "research_taste": research_taste,
        "scratchpad": scratchpad,
        "topic_skill_projection": topic_skill_projection,
        "topic_completion": topic_completion,
        "statement_compilation": statement_compilation,
        "lean_bridge": lean_bridge,
        "minimal_execution_brief": {
            "current_stage": runtime_focus.get("resume_stage") or topic_state.get("resume_stage"),
            "selected_action_id": selected_action_id,
            "selected_action_type": selected_action_type,
            "selected_action_summary": selected_action_label,
            "decision_source": decision_surface.get("decision_source"),
            "queue_source": queue_surface.get("queue_source")
            or ("declared_contract" if queue_surface.get("declared_contract_path") else "heuristic"),
            "open_next": must_read_now[0]["path"] if must_read_now else runtime_protocol_note,
            "immediate_allowed_work": immediate_allowed_work,
            "immediate_blocked_work": immediate_blocked_work,
        },
        "must_read_now": must_read_now,
        "may_defer_until_trigger": may_defer_until_trigger,
        "escalation_triggers": escalation_triggers,
        "active_hard_constraints": active_hard_constraints,
        "recommended_protocol_slices": recommended_protocol_slices,
        "python_runtime_scope": [
            "Materialize durable runtime state and protocol snapshots on disk.",
            "Run conformance, capability, and trust audits against persisted artifacts.",
            "Execute explicit auto-runnable handlers declared in runtime state.",
            "Block Layer 2 promotion until a durable human approval artifact exists on disk.",
        ],
        "agent_required_read_order": read_order,
        "priority_rules": [
            {
                "source": "control_note_or_decision_contract",
                "rule": "If a control note or decision contract exists, it overrides heuristic next-step selection.",
            },
            {
                "source": "declared_action_contract",
                "rule": "Prefer durable `next_actions.contract.json` over queue synthesis from prose or memory.",
            },
            {
                "source": "generated_queue_contract",
                "rule": "Treat generated queue-contract snapshots as editable protocol surfaces, not hidden implementation detail.",
            },
            {
                "source": "strategy_memory",
                "rule": "When a route resembles a previously recorded helpful or harmful pattern, consult strategy memory before trusting heuristic route selection.",
            },
            {
                "source": "heuristic_queue",
                "rule": "Use heuristic queue rows only as fallback guidance when no durable contract is present.",
            },
        ],
        "reproducibility_expectations": research_mode_profile.get("reproducibility_expectations") or [],
        "note_expectations": research_mode_profile.get("note_expectations") or [],
        "backend_bridges": backend_bridges,
        "promotion_gate": {
            "status": str(promotion_gate.get("status") or "not_requested"),
            "candidate_id": str(promotion_gate.get("candidate_id") or ""),
            "candidate_type": str(promotion_gate.get("candidate_type") or ""),
            "path": self._relativize(self._promotion_gate_paths(topic_slug)["json"])
            if self._promotion_gate_paths(topic_slug)["json"].exists()
            else None,
            "note_path": self._relativize(self._promotion_gate_paths(topic_slug)["note"])
            if self._promotion_gate_paths(topic_slug)["note"].exists()
            else None,
            "backend_id": str(promotion_gate.get("backend_id") or ""),
            "target_backend_root": str(promotion_gate.get("target_backend_root") or ""),
            "review_mode": str(promotion_gate.get("review_mode") or "human"),
            "canonical_layer": str(promotion_gate.get("canonical_layer") or "L2"),
            "coverage_status": str(promotion_gate.get("coverage_status") or "not_audited"),
            "consensus_status": str(promotion_gate.get("consensus_status") or "not_requested"),
            "merge_outcome": str(promotion_gate.get("merge_outcome") or "pending"),
            "approved_by": str(promotion_gate.get("approved_by") or ""),
            "promoted_units": self._dedupe_strings(list(promotion_gate.get("promoted_units") or [])),
        },
        "delivery_rule": str((interaction_state.get("delivery_contract") or {}).get("rule") or ""),
        "editable_protocol_surfaces": editable_surfaces,
        "action_queue_surface": {
            "queue_source": queue_surface.get("queue_source")
            or ("declared_contract" if queue_surface.get("declared_contract_path") else "heuristic"),
            "declared_contract_path": queue_surface.get("declared_contract_path"),
            "generated_contract_path": queue_surface.get("generated_contract_path"),
            "generated_contract_note_path": queue_surface.get("generated_contract_note_path"),
        },
        "decision_surface": decision_surface_snapshot(
            decision_surface,
            runtime_focus,
            research_judgment,
        ),
        "pending_actions": [
            {
                "action_id": str(row.get("action_id") or ""),
                "action_type": str(row.get("action_type") or ""),
                "summary": str(row.get("summary") or ""),
                "auto_runnable": bool(row.get("auto_runnable")),
                "queue_source": str(row.get("queue_source") or queue_surface.get("queue_source") or "heuristic"),
            }
            for row in queue_rows
            if str(row.get("status") or "pending") == "pending"
        ],
    }
    protocol_paths = self._runtime_protocol_paths(topic_slug)
    _write_json(protocol_paths["json"], payload)
    _write_text(protocol_paths["note"], runtime_protocol_markdown(payload))
    return {
        "runtime_protocol_path": str(protocol_paths["json"]),
        "runtime_protocol_note_path": str(protocol_paths["note"]),
    }

def materialize_session_start_contract(
    self,
    *,
    task: str,
    routing: dict[str, Any],
    loop_payload: dict[str, Any],
    updated_by: str,
    pre_route_current_topic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    topic_slug = str(loop_payload.get("topic_slug") or routing.get("topic_slug") or "").strip()
    if not topic_slug:
        raise ValueError("Session-start contract requires a resolved topic slug.")

    runtime_root = self._ensure_runtime_root(topic_slug)
    session_paths = self._session_start_paths(topic_slug)
    runtime_protocol_paths = loop_payload.get("runtime_protocol") or {}
    runtime_protocol_path = self._normalize_artifact_path(runtime_protocol_paths.get("runtime_protocol_path"))
    runtime_protocol_note_path = self._normalize_artifact_path(runtime_protocol_paths.get("runtime_protocol_note_path"))
    runtime_bundle = _read_json(Path(runtime_protocol_paths.get("runtime_protocol_path") or "")) or {}
    loop_state = loop_payload.get("loop_state") or {}
    steering_artifacts = loop_payload.get("steering_artifacts") or {}
    bootstrap = loop_payload.get("bootstrap") or {}
    pointers = (bootstrap.get("topic_state") or {}).get("pointers") or {}

    pre_route_payload = pre_route_current_topic or {}
    pre_route_topic_slug = str(pre_route_payload.get("topic_slug") or "").strip()
    pre_route_current_valid = bool(
        pre_route_topic_slug and (self._runtime_root(pre_route_topic_slug) / "topic_state.json").exists()
    )
    route_name = str(routing.get("route") or "")
    current_topic_first_route = route_name in {
        "explicit_current_topic",
        "request_current_topic_reference",
        "implicit_current_topic",
    }
    latest_only_route = route_name == "explicit_latest_topic"
    explicit_route = route_name in {
        "explicit_topic_slug",
        "explicit_topic_title",
        "request_named_existing_topic",
        "request_new_topic",
    }
    used_current_topic_memory = (
        current_topic_first_route and pre_route_current_valid and pre_route_topic_slug == topic_slug
    )
    used_latest_topic_fallback = (current_topic_first_route and not used_current_topic_memory) or latest_only_route

    if used_current_topic_memory:
        memory_summary = f"Resolved through durable current-topic memory: `{topic_slug}`."
    elif used_latest_topic_fallback:
        memory_summary = (
            f"Current-topic memory was missing or stale, so session-start fell back to the latest topic: `{topic_slug}`."
        )
    elif explicit_route:
        memory_summary = "Resolved from an explicit topic reference in the request or caller flags."
    else:
        memory_summary = "Resolved from the session-start routing layer."

    runtime_autonomy_posture = runtime_bundle.get("autonomy_posture") or {}
    requested_max_auto_steps = runtime_autonomy_posture.get(
        "requested_max_auto_steps",
        loop_state.get("requested_max_auto_steps"),
    )
    applied_max_auto_steps = runtime_autonomy_posture.get(
        "applied_max_auto_steps",
        loop_state.get("applied_max_auto_steps"),
    )
    auto_step_budget_reason = runtime_autonomy_posture.get(
        "budget_reason",
        loop_state.get("auto_step_budget_reason"),
    )
    human_interaction_posture = runtime_bundle.get("human_interaction_posture") or _human_interaction_posture_from_bundle(runtime_bundle)
    autonomy_posture = runtime_bundle.get("autonomy_posture") or _autonomy_posture_from_bundle(
        runtime_bundle,
        requested_max_auto_steps=requested_max_auto_steps,
        applied_max_auto_steps=applied_max_auto_steps,
        budget_reason=auto_step_budget_reason,
    )
    theory_context_injection = apply_theory_context_session_dedup(
        self,
        topic_slug=topic_slug,
        payload=runtime_bundle.get("theory_context_injection") or {},
        updated_by=updated_by,
    )

    must_read_now: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    def _append_read(path_value: str | Path | None, reason: str) -> None:
        normalized = self._normalize_artifact_path(path_value)
        if not normalized or normalized in seen_paths:
            return
        seen_paths.add(normalized)
        must_read_now.append({"path": normalized, "reason": reason})

    _append_read(
        runtime_protocol_note_path,
        "Primary AITP runtime contract for this topic. Open this immediately after the session-start contract.",
    )
    for item in runtime_bundle.get("must_read_now") or []:
        _append_read(item.get("path"), str(item.get("reason") or "").strip())
    for row in theory_context_injection.get("fragments") or []:
        if str(row.get("delivery_status") or "").strip() != "inject_now":
            continue
        _append_read(
            row.get("path"),
            f"Theory context injection ({row.get('kind') or 'theory_context'}) before editing theorem-facing artifacts. {row.get('summary') or ''}".strip(),
        )

    control_note_path = self._normalize_artifact_path(
        steering_artifacts.get("control_note_path") or pointers.get("control_note_path")
    )
    operator_checkpoint_path = self._normalize_artifact_path(
        (runtime_bundle.get("operator_checkpoint") or {}).get("path")
    )
    operator_checkpoint_note_path = self._normalize_artifact_path(
        (runtime_bundle.get("operator_checkpoint") or {}).get("note_path")
    )
    idea_packet_path = self._normalize_artifact_path((runtime_bundle.get("idea_packet") or {}).get("path"))
    idea_packet_note_path = self._normalize_artifact_path((runtime_bundle.get("idea_packet") or {}).get("note_path"))
    collaborator_profile_path = self._normalize_artifact_path((runtime_bundle.get("collaborator_profile") or {}).get("path"))
    collaborator_profile_note_path = self._normalize_artifact_path((runtime_bundle.get("collaborator_profile") or {}).get("note_path"))
    research_trajectory_path = self._normalize_artifact_path((runtime_bundle.get("research_trajectory") or {}).get("path")); research_trajectory_note_path = self._normalize_artifact_path((runtime_bundle.get("research_trajectory") or {}).get("note_path")); mode_learning_path = self._normalize_artifact_path((runtime_bundle.get("mode_learning") or {}).get("path")); mode_learning_note_path = self._normalize_artifact_path((runtime_bundle.get("mode_learning") or {}).get("note_path"))
    innovation_direction_path = self._normalize_artifact_path(
        steering_artifacts.get("innovation_direction_path") or pointers.get("innovation_direction_path")
    )
    innovation_decisions_path = self._normalize_artifact_path(
        steering_artifacts.get("innovation_decisions_path") or pointers.get("innovation_decisions_path")
    )
    operator_checkpoint_status = str(((runtime_bundle.get("operator_checkpoint") or {}).get("status") or "")).strip()
    idea_packet_status = str(((runtime_bundle.get("idea_packet") or {}).get("status") or "")).strip()

    if steering_artifacts.get("detected"):
        _append_read(
            innovation_direction_path,
            "Authoritative translation of the latest human steering into a durable innovation target.",
        )
        _append_read(
            control_note_path,
            "Authoritative translation of the latest human steering into an executable control note.",
        )
        _append_read(
            innovation_decisions_path,
            "Durable steering history for this topic. Open when the redirect history matters.",
        )
    if idea_packet_status == "needs_clarification":
        _append_read(
            idea_packet_note_path,
            "Resolve the active idea-packet clarification gate before substantive execution continues.",
        )
    if operator_checkpoint_status == "requested":
        _append_read(
            operator_checkpoint_note_path,
            "Resolve the active operator checkpoint before deeper execution continues.",
        )

    selected_action = (runtime_bundle.get("minimal_execution_brief") or {})
    selected_action_payload = {
        "action_id": str(selected_action.get("selected_action_id") or ""),
        "action_type": str(selected_action.get("selected_action_type") or ""),
        "summary": str(selected_action.get("selected_action_summary") or ""),
    }

    linear_flow = [
        {
            "step": "Treat the original chat request as already routed; do not ask for a topic again unless durable memory is still ambiguous.",
            "result": memory_summary,
        },
        {
            "step": "Read `session_start.generated.md` first, then `runtime_protocol.generated.md`.",
            "result": "Session-start defines the immediate startup order; the runtime bundle defines the topic contract.",
        },
        {
            "step": "If steering artifacts were auto-updated from the human request, treat `innovation_direction.md` and `control_note.md` as authoritative before continuing.",
            "result": "Natural-language steering becomes durable protocol state before execution.",
        },
        {
            "step": "Only then continue the currently selected bounded action and close with an exit audit when the step is done.",
            "result": selected_action_payload["summary"] or "Continue the bounded topic lane declared in the runtime bundle.",
        },
    ]
    if idea_packet_status == "needs_clarification":
        linear_flow.insert(
            2,
            {
                "step": "Open `idea_packet.md` and answer its clarification questions before touching the queue or claiming substantive execution.",
                "result": "AITP blocks deeper execution until the initial intent, validation route, and evidence bar are explicit.",
            },
        )
    if operator_checkpoint_status == "requested":
        linear_flow.insert(
            2,
            {
                "step": "Open `operator_checkpoint.active.md` and resolve the active human-checkpoint question before the bounded loop continues.",
                "result": "AITP stops at a durable operator checkpoint instead of silently guessing the human decision.",
            },
        )
    linear_flow.insert(
        2 + int(operator_checkpoint_status == "requested") + int(idea_packet_status == "needs_clarification"),
        {
            "step": "Finish the files listed under `Must read now` before touching the queue or giving a substantial research answer.",
            "result": "Current topic state, question scope, validation route, and guardrails are loaded in a fixed order.",
        },
    )

    hard_stops = [
        "Do not skip session-start and jump straight into free-form explanation, browsing, or file editing for AITP-governed research work.",
        "Do not continue if `runtime_protocol.generated.md` is missing.",
        "Do not continue if conformance is not `pass`.",
        "Do not replace durable current-topic routing with a fresh topic guess when session-start already resolved the topic.",
        "Do not ignore `innovation_direction.md` or `control_note.md` after a steering request changed direction, paused work, or opened a branch.",
    ]
    if idea_packet_status == "needs_clarification":
        hard_stops.append(
            "Do not continue substantive execution until `idea_packet.md` resolves the missing intent fields and clarification questions."
        )
    if operator_checkpoint_status == "requested":
        hard_stops.append(
            "Do not continue deeper execution until `operator_checkpoint.active.md` is answered or cancelled."
        )
    if steering_artifacts.get("detected"):
        hard_stops.append(
            "This request carried human steering. `innovation_direction.md` and `control_note.md` must be read before deeper execution."
        )

    payload = {
        "contract_kind": "session_start_contract",
        "protocol_version": 1,
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "task": task,
        "canonical_entry": f'aitp session-start "{task}"',
        "routing": {
            "route": route_name,
            "reason": routing.get("reason"),
            "topic_slug": topic_slug,
            "topic_title": routing.get("topic"),
        },
        "memory_resolution": {
            "current_topic_first": True,
            "pre_route_current_topic_slug": pre_route_topic_slug or None,
            "pre_route_current_topic_valid": pre_route_current_valid,
            "used_current_topic_memory": used_current_topic_memory,
            "used_latest_topic_fallback": used_latest_topic_fallback,
            "summary": memory_summary,
        },
        "artifacts": {
            "session_start_contract_path": self._normalize_artifact_path(session_paths["json"]),
            "session_start_note_path": self._normalize_artifact_path(session_paths["note"]),
            "runtime_protocol_path": runtime_protocol_path,
            "runtime_protocol_note_path": runtime_protocol_note_path,
            "loop_state_path": self._normalize_artifact_path(loop_payload.get("loop_state_path")),
            "current_topic_memory_path": self._normalize_artifact_path(
                (loop_payload.get("current_topic_memory") or {}).get("current_topic_path")
            ),
            "current_topic_note_path": self._normalize_artifact_path(
                (loop_payload.get("current_topic_memory") or {}).get("current_topic_note_path")
            ),
            "collaborator_profile_path": collaborator_profile_path,
            "collaborator_profile_note_path": collaborator_profile_note_path,
            "research_trajectory_path": research_trajectory_path,
            "research_trajectory_note_path": research_trajectory_note_path, "mode_learning_path": mode_learning_path, "mode_learning_note_path": mode_learning_note_path,
            "operator_checkpoint_path": operator_checkpoint_path,
            "operator_checkpoint_note_path": operator_checkpoint_note_path,
            "idea_packet_path": idea_packet_path,
            "idea_packet_note_path": idea_packet_note_path,
            "innovation_direction_path": innovation_direction_path,
            "innovation_decisions_path": innovation_decisions_path,
            "control_note_path": control_note_path,
        },
        "must_read_now": must_read_now,
        "linear_flow": linear_flow,
        "selected_action": selected_action_payload,
        "hard_stops": hard_stops,
        "human_interaction_posture": human_interaction_posture,
        "autonomy_posture": autonomy_posture,
        "loop_state_summary": {
            "entry_conformance": loop_state.get("entry_conformance"),
            "exit_conformance": loop_state.get("exit_conformance"),
            "capability_status": loop_state.get("capability_status"),
            "trust_status": loop_state.get("trust_status"),
            "promotion_gate_status": loop_state.get("promotion_gate_status"),
        },
        "steering": {
            "detected": bool(steering_artifacts.get("detected")),
            "decision": steering_artifacts.get("decision"),
            "direction": steering_artifacts.get("direction"),
            "summary": steering_artifacts.get("summary"),
        },
        "theory_context_injection": theory_context_injection,
    }
    _write_json(session_paths["json"], payload)
    _write_text(session_paths["note"], render_session_start_note(payload))
    return {
        **payload,
        "session_start_contract_path": str(session_paths["json"]),
        "session_start_note_path": str(session_paths["note"]),
        "runtime_root": str(runtime_root),
    }
