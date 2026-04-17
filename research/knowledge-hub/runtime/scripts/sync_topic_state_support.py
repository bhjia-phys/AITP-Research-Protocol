from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def infer_resume_state(
    *,
    valid_resume_stages: set[str],
    intake_status: dict[str, Any] | None,
    feedback_status: dict[str, Any] | None,
    latest_decision: dict[str, Any] | None,
    closed_loop_decision: dict[str, Any] | None,
) -> tuple[str, str, str]:
    if latest_decision:
        verdict = latest_decision.get("verdict", "unknown")
        fallback_targets = latest_decision.get("fallback_targets") or []
        if verdict in {"accepted", "promoted"}:
            return "L2", "L4", "Latest validation promoted material into Layer 2."
        if verdict in {"deferred", "rejected", "needs_revision"}:
            if fallback_targets:
                first_target = fallback_targets[0]
                if str(first_target).startswith("feedback/") or "/L3/" in str(first_target):
                    return "L3", "L4", f"Latest Layer 4 verdict is {verdict}; resume exploratory work in Layer 3."
                if str(first_target).startswith("intake/") or "/L1/" in str(first_target):
                    return "L1", "L4", f"Latest Layer 4 verdict is {verdict}; resume source-bound work in Layer 1."
            return "L4", "L4", f"Latest Layer 4 verdict is {verdict}; inspect the validation record."
    if closed_loop_decision:
        decision = closed_loop_decision.get("decision", "unknown")
        if decision == "keep":
            return "L4", "L4", "Latest closed-loop decision kept the route; inspect the Layer 4 writeback before any promotion."
        if decision in {"revise", "discard", "defer"}:
            return "L3", "L4", f"Latest closed-loop decision is {decision}; resume exploratory work in Layer 3."
        return "L4", "L4", "A Layer 4 closed-loop decision exists; inspect the validation writeback."
    if feedback_status:
        return "L3", "L3", "A Layer 3 run exists without a later decision artifact."
    if intake_status:
        next_stage = intake_status.get("next_stage")
        if next_stage in valid_resume_stages:
            return next_stage, "L1", f"Layer 1 status points next to {next_stage}."
        return "L1", "L1", "Only Layer 1 intake artifacts are currently materialized."
    return "L0", "L0", "No layer artifacts were found for this topic."


def first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def derive_last_evidence_return(
    *,
    feedback_status: dict[str, Any] | None,
    closed_loop: dict[str, Any],
) -> dict[str, str]:
    result_manifest = closed_loop.get("result_manifest") or {}
    closed_loop_paths = closed_loop.get("paths") or {}
    latest_decision = closed_loop.get("latest_decision") or {}
    if result_manifest:
        return {
            "status": "present",
            "kind": "result_manifest",
            "path": str(closed_loop_paths.get("result_manifest_path") or ""),
            "record_id": str(result_manifest.get("result_id") or ""),
            "recorded_at": first_text(result_manifest.get("updated_at"), result_manifest.get("ingested_at"), latest_decision.get("decided_at")),
            "summary": first_text(result_manifest.get("summary"), latest_decision.get("reason"), f"Closed-loop result manifest is `{result_manifest.get('status') or 'present'}`."),
        }
    if feedback_status:
        return {
            "status": "present",
            "kind": "feedback_status",
            "path": str(feedback_status.get("last_result_manifest_path") or ""),
            "record_id": str(feedback_status.get("last_result_id") or feedback_status.get("last_closed_loop_decision_id") or ""),
            "recorded_at": first_text(feedback_status.get("last_updated")),
            "summary": first_text(
                feedback_status.get("summary"),
                f"Feedback stage `{feedback_status.get('stage') or '(missing)'}` with candidate status `{feedback_status.get('candidate_status') or '(missing)'}`.",
            ),
        }
    return {
        "status": "missing",
        "kind": "none",
        "path": "",
        "record_id": "",
        "recorded_at": "",
        "summary": "No durable evidence-return artifact is currently recorded for this topic.",
    }


def derive_status_explainability(
    *,
    topic_slug: str,
    resume_stage: str,
    resume_reason: str,
    pending_actions: list[str],
    topic_runtime_root: Path,
    feedback_status: dict[str, Any] | None,
    closed_loop: dict[str, Any],
    next_action_decision_note_path: Path,
    read_json: Callable[[Path], dict[str, Any] | None],
    relative_path: Callable[[Path | None, Path], str | None],
    now_iso: Callable[[], str],
) -> dict[str, Any]:
    idea_packet = read_json(topic_runtime_root / "idea_packet.json") or {}
    operator_checkpoint = read_json(topic_runtime_root / "operator_checkpoint.active.json") or {}
    last_evidence_return = derive_last_evidence_return(feedback_status=feedback_status, closed_loop=closed_loop)
    next_action_summary = first_text(pending_actions[0] if pending_actions else "")
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        blocker_summary = [str(item).strip() for item in (operator_checkpoint.get("blocker_summary") or []) if str(item).strip()]
        active_human_need = {
            "status": "requested",
            "kind": str(operator_checkpoint.get("checkpoint_kind") or ""),
            "path": relative_path(topic_runtime_root / "operator_checkpoint.active.md", topic_runtime_root.parents[2]) or "",
            "summary": str(operator_checkpoint.get("question") or ""),
        }
        why_this_topic_is_here = first_text(blocker_summary[0] if blocker_summary else "", operator_checkpoint.get("question"), "AITP paused at an active operator checkpoint.")
    elif str(idea_packet.get("status") or "").strip() == "needs_clarification":
        blocker_summary = [str(item).strip() for item in (idea_packet.get("clarification_questions") or []) if str(item).strip()]
        active_human_need = {
            "status": "requested",
            "kind": "idea_packet_clarification",
            "path": relative_path(topic_runtime_root / "idea_packet.md", topic_runtime_root.parents[2]) or "",
            "summary": str(idea_packet.get("status_reason") or ""),
        }
        why_this_topic_is_here = first_text(blocker_summary[0] if blocker_summary else "", idea_packet.get("status_reason"), "AITP is holding at the research-intent gate.")
    else:
        blocker_summary = []
        active_human_need = {
            "status": "none",
            "kind": "none",
            "path": "",
            "summary": "No active human checkpoint is currently blocking the bounded loop.",
        }
        why_this_topic_is_here = first_text(
            f"The topic is currently following `{next_action_summary}` at stage `{resume_stage}`." if next_action_summary else "",
            resume_reason,
            "AITP is holding the current bounded route defined by the runtime state.",
        )
    return {
        "topic_slug": topic_slug,
        "current_status_summary": f"Stage `{resume_stage}`; next `{next_action_summary or 'No bounded action is currently selected.'}`; human need `{active_human_need['kind']}`; last evidence `{last_evidence_return['kind']}`.",
        "why_this_topic_is_here": why_this_topic_is_here,
        "current_route_choice": {
            "resume_stage": resume_stage,
            "selected_route_id": str((closed_loop.get("selected_route") or {}).get("route_id") or ""),
            "execution_task_id": str((closed_loop.get("execution_task") or {}).get("task_id") or ""),
            "next_action_summary": next_action_summary,
            "next_action_decision_note_path": relative_path(next_action_decision_note_path, topic_runtime_root.parents[2]) or "",
            "selected_validation_route_path": str((closed_loop.get("paths") or {}).get("selected_route_path") or ""),
        },
        "last_evidence_return": last_evidence_return,
        "active_human_need": active_human_need,
        "blocker_summary": blocker_summary,
        "next_bounded_action": {
            "status": "selected" if next_action_summary else "missing",
            "summary": next_action_summary or "No bounded action is currently selected.",
        },
        "updated_at": now_iso(),
    }


def build_resume_markdown(state: dict[str, Any]) -> str:
    pointers = state["pointers"]
    layer_status = state["layer_status"]
    backend_bridges = state.get("backend_bridges") or []
    promotion_gate = state.get("promotion_gate") or {}
    closed_loop = state.get("closed_loop") or {}
    research_mode_profile = state.get("research_mode_profile") or {}
    status_explainability = state.get("status_explainability") or {}
    current_route_choice = status_explainability.get("current_route_choice") or {}
    last_evidence_return = status_explainability.get("last_evidence_return") or {}
    active_human_need = status_explainability.get("active_human_need") or {}
    blocker_summary = status_explainability.get("blocker_summary") or []
    summary = state.get("summary") or status_explainability.get("why_this_topic_is_here") or state["resume_reason"]
    lines = [
        "# Topic runtime resume",
        "",
        f"- Topic slug: `{state['topic_slug']}`",
        f"- Updated at: `{state['updated_at']}`",
        f"- Updated by: `{state['updated_by']}`",
        f"- Last materialized stage: `{state['last_materialized_stage']}`",
        f"- Resume stage: `{state['resume_stage']}`",
        f"- Latest run id: `{state['latest_run_id'] or '(none)'}`",
        f"- Research mode: `{state.get('research_mode') or '(missing)'}`",
        f"- Active executor kind: `{state.get('active_executor_kind') or '(missing)'}`",
        f"- Active reasoning profile: `{state.get('active_reasoning_profile') or '(missing)'}`",
        "",
        "## Resume reason",
        "",
        f"- {state['resume_reason']}",
        "",
        "## Why this topic is here",
        "",
        f"- {status_explainability.get('why_this_topic_is_here') or state['resume_reason']}",
        "",
        "## Research-mode governance",
        "",
        f"- Profile path: `{research_mode_profile.get('profile_path') or '(missing)'}`",
        f"- Label: `{research_mode_profile.get('label') or '(missing)'}`",
        f"- Description: {research_mode_profile.get('description') or '(missing)'}",
        "",
        "### Reproducibility expectations",
        "",
    ]
    for item in research_mode_profile.get("reproducibility_expectations") or ["No explicit reproducibility expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(["", "### Human-readable notes", ""])
    for item in research_mode_profile.get("note_expectations") or ["No explicit note expectation recorded."]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Layer snapshot",
            "",
            f"- L0: `{layer_status['L0']['status']}` ({state['source_count']} sources)",
            f"- L1: `{layer_status['L1']['status']}`",
            f"- L3: `{layer_status['L3']['status']}`",
            f"- L4: `{layer_status['L4']['status']}`",
            f"- Closed loop: `{closed_loop.get('status', 'missing')}`",
            "",
            "## L0 backend bridges",
            "",
        ]
    )
    if backend_bridges:
        for bridge in backend_bridges:
            lines.extend(
                [
                    f"- `{bridge.get('backend_id') or '(missing)'}` title=`{bridge.get('title') or '(missing)'}` type=`{bridge.get('backend_type') or '(missing)'}` status=`{bridge.get('status') or '(missing)'}` card_status=`{bridge.get('card_status') or '(missing)'}` sources=`{bridge.get('source_count', 0)}`",
                    f"  card_path=`{bridge.get('card_path') or '(missing)'}`",
                    f"  backend_root=`{bridge.get('backend_root') or '(missing)'}`",
                    f"  artifact_granularity=`{bridge.get('artifact_granularity') or '(missing)'}`",
                    f"  artifact_kinds=`{', '.join(bridge.get('artifact_kinds') or []) or '(missing)'}`",
                    f"  canonical_targets=`{', '.join(bridge.get('canonical_targets') or []) or '(missing)'}`",
                    f"  l0_registration_script=`{bridge.get('l0_registration_script') or '(missing)'}`",
                ]
            )
    else:
        lines.append("- None registered.")
    lines.extend(
        [
            "",
            "## L2 promotion gate",
            "",
            f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
            f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
            f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
            f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
            f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
            f"- Review mode: `{promotion_gate.get('review_mode') or '(missing)'}`",
            f"- Canonical layer: `{promotion_gate.get('canonical_layer') or '(missing)'}`",
            f"- Coverage status: `{promotion_gate.get('coverage_status') or '(missing)'}`",
            f"- Consensus status: `{promotion_gate.get('consensus_status') or '(missing)'}`",
            f"- Merge outcome: `{promotion_gate.get('merge_outcome') or '(missing)'}`",
            f"- Gate JSON: `{pointers.get('promotion_gate_path') or '(missing)'}`",
            f"- Gate note: `{pointers.get('promotion_gate_note_path') or '(missing)'}`",
            "",
            "## Closed-loop state",
            "",
            f"- Selected route: `{closed_loop.get('selected_route_id') or '(missing)'}`",
            f"- Execution task: `{closed_loop.get('task_id') or '(missing)'}`",
            f"- Result manifest: `{closed_loop.get('result_id') or '(missing)'}`",
            f"- Latest decision: `{closed_loop.get('latest_decision') or '(missing)'}`",
            f"- Literature follow-ups: `{closed_loop.get('literature_followup_count', 0)}`",
            f"- Follow-up gaps: `{closed_loop.get('followup_gap_count', 0)}`",
            f"- Deferred candidates: `{state.get('deferred_candidate_count', 0)}`",
            f"- Reactivatable deferred entries: `{state.get('reactivable_deferred_count', 0)}`",
            f"- Follow-up subtopics: `{state.get('followup_subtopic_count', 0)}`",
            "",
            "## Current route choice",
            "",
            f"- Selected route: `{current_route_choice.get('selected_route_id') or '(missing)'}`",
            f"- Execution task: `{current_route_choice.get('execution_task_id') or '(missing)'}`",
            f"- Next bounded action: {current_route_choice.get('next_action_summary') or '(none)'}",
            f"- Next-action decision note: `{current_route_choice.get('next_action_decision_note_path') or '(missing)'}`",
            f"- Selected validation route: `{current_route_choice.get('selected_validation_route_path') or '(missing)'}`",
            "",
            "## Last evidence return",
            "",
            f"- Status: `{last_evidence_return.get('status') or '(missing)'}`",
            f"- Kind: `{last_evidence_return.get('kind') or '(missing)'}`",
            f"- Record id: `{last_evidence_return.get('record_id') or '(none)'}`",
            f"- Recorded at: `{last_evidence_return.get('recorded_at') or '(unknown)'}`",
            f"- Path: `{last_evidence_return.get('path') or '(missing)'}`",
            f"- Summary: {last_evidence_return.get('summary') or '(none)'}",
            "",
            "## Active human need",
            "",
            f"- Status: `{active_human_need.get('status') or '(missing)'}`",
            f"- Kind: `{active_human_need.get('kind') or '(missing)'}`",
            f"- Path: `{active_human_need.get('path') or '(missing)'}`",
            f"- Summary: {active_human_need.get('summary') or '(none)'}",
            "",
            "## Blocker summary",
            "",
        ]
    )
    for item in blocker_summary or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Pending actions", ""])
    if state["pending_actions"]:
        for index, action in enumerate(state["pending_actions"], start=1):
            lines.append(f"{index}. {action}")
    else:
        lines.append("- None recorded.")
    lines.extend(
        [
            "",
            "## Key pointers",
            "",
            f"- L0 source index: `{pointers['l0_source_index_path'] or '(missing)'}`",
            f"- Intake status: `{pointers['intake_status_path'] or '(missing)'}`",
            f"- Feedback status: `{pointers['feedback_status_path'] or '(missing)'}`",
            f"- Next actions: `{pointers['next_actions_path'] or '(missing)'}`",
            f"- Next-actions contract: `{pointers.get('next_actions_contract_path') or '(missing)'}`",
            f"- Promotion decision: `{pointers['promotion_decision_path'] or '(missing)'}`",
            f"- Consultation index: `{pointers['consultation_index_path'] or '(missing)'}`",
            f"- L4 control note: `{pointers['control_note_path'] or '(missing)'}`",
            f"- Innovation direction: `{pointers.get('innovation_direction_path') or '(missing)'}`",
            f"- Innovation decisions: `{pointers.get('innovation_decisions_path') or '(missing)'}`",
            f"- Unfinished work index: `{pointers.get('unfinished_work_path') or '(missing)'}`",
            f"- Unfinished work note: `{pointers.get('unfinished_work_note_path') or '(missing)'}`",
            f"- Primary runtime synopsis: `{pointers.get('topic_synopsis_path') or '(missing)'}`",
            f"- Primary runtime dashboard: `{pointers.get('topic_dashboard_path') or '(missing)'}`",
            f"- Next-action decision: `{pointers.get('next_action_decision_path') or '(missing)'}`",
            f"- Next-action decision note: `{pointers.get('next_action_decision_note_path') or '(missing)'}`",
            f"- Next-action decision contract: `{pointers.get('next_action_decision_contract_path') or '(missing)'}`",
            f"- Next-action decision contract note: `{pointers.get('next_action_decision_contract_note_path') or '(missing)'}`",
            f"- Generated queue-contract snapshot: `{pointers.get('action_queue_contract_generated_path') or '(missing)'}`",
            f"- Generated queue-contract note: `{pointers.get('action_queue_contract_generated_note_path') or '(missing)'}`",
            f"- Primary review bundle: `{pointers.get('primary_review_bundle_path') or '(missing)'}`",
            f"- Primary review bundle note: `{pointers.get('primary_review_bundle_note_path') or '(missing)'}`",
            f"- Validation review bundle: `{pointers.get('validation_review_bundle_path') or '(missing)'}`",
            f"- Validation review bundle note: `{pointers.get('validation_review_bundle_note_path') or '(missing)'}`",
            f"- Selected validation route: `{pointers.get('selected_validation_route_path') or '(missing)'}`",
            f"- Execution task: `{pointers.get('execution_task_path') or '(missing)'}`",
            f"- Execution notes: `{pointers.get('execution_notes_path') or '(missing)'}`",
            f"- Returned execution result: `{pointers.get('returned_execution_result_path') or '(missing)'}`",
            f"- Result manifest: `{pointers.get('result_manifest_path') or '(missing)'}`",
            f"- Trajectory log: `{pointers.get('trajectory_log_path') or '(missing)'}`",
            f"- Trajectory note: `{pointers.get('trajectory_note_path') or '(missing)'}`",
            f"- Failure classification: `{pointers.get('failure_classification_path') or '(missing)'}`",
            f"- Failure classification note: `{pointers.get('failure_classification_note_path') or '(missing)'}`",
            f"- Decision ledger: `{pointers.get('decision_ledger_path') or '(missing)'}`",
            f"- Literature follow-ups: `{pointers.get('literature_followup_queries_path') or '(missing)'}`",
            f"- Literature follow-up receipts: `{pointers.get('literature_followup_receipts_path') or '(missing)'}`",
            f"- Follow-up gap writeback: `{pointers.get('followup_gap_writeback_path') or '(missing)'}`",
            f"- Follow-up gap writeback note: `{pointers.get('followup_gap_writeback_note_path') or '(missing)'}`",
            f"- Deferred buffer: `{pointers.get('deferred_buffer_path') or '(missing)'}`",
            f"- Deferred buffer note: `{pointers.get('deferred_buffer_note_path') or '(missing)'}`",
            f"- Follow-up subtopics: `{pointers.get('followup_subtopics_path') or '(missing)'}`",
            f"- Follow-up subtopics note: `{pointers.get('followup_subtopics_note_path') or '(missing)'}`",
            "",
            "## Summary",
            "",
            f"- {summary}",
            "",
        ]
    )
    return "\n".join(lines)
