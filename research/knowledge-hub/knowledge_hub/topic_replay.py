from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_read_path_support import active_branch_hypothesis, build_route_activation_payload, build_route_choice_payload, build_route_handoff_payload, build_route_reentry_payload, build_route_transition_gate_payload, build_route_transition_intent_payload, build_route_transition_receipt_payload, build_route_transition_resolution_payload, build_route_transition_discrepancy_payload, build_route_transition_repair_payload, build_route_transition_escalation_payload, build_route_transition_clearance_payload, build_route_transition_followthrough_payload, build_route_transition_resumption_payload, build_route_transition_commitment_payload, build_route_transition_authority_payload, hypotheses_for_route, leading_competing_hypothesis, normalize_competing_hypotheses


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _runtime_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "topics" / topic_slug / "runtime"


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _existing_note(path: Path, *, kernel_root: Path) -> str | None:
    return _rel(path, kernel_root) if path.exists() else None


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def build_topic_replay_bundle(kernel_root: Path, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    topic_root = _runtime_root(kernel_root, topic_slug)
    if not topic_root.exists():
        raise FileNotFoundError(f"Missing runtime topic root: {topic_root}")

    synopsis = read_json(topic_root / "topic_synopsis.json") or {}
    runtime_focus = synopsis.get("runtime_focus") or {}
    l0_source_handoff = runtime_focus.get("l0_source_handoff") or {}
    topic_state = read_json(topic_root / "topic_state.json") or {}
    research_question = read_json(topic_root / "research_question.contract.json") or {}
    review_bundle = read_json(topic_root / "validation_review_bundle.active.json") or {}
    topic_completion = read_json(topic_root / "topic_completion.json") or {}
    projection = read_json(topic_root / "topic_skill_projection.active.json") or {}
    next_action = read_json(topic_root / "next_action_decision.json") or {}
    transition_history = read_json(topic_root / "transition_history.json") or {}
    promotion_gate = read_json(topic_root / "promotion_gate.json") or {}
    latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
    iteration_journal_path = (
        kernel_root / "topics" / topic_slug / "L3" / "runs" / latest_run_id / "iteration_journal.md"
        if latest_run_id
        else None
    )
    operator_checkpoint = dict(read_json(topic_root / "operator_checkpoint.active.json") or {})
    if operator_checkpoint:
        operator_checkpoint.setdefault(
            "path",
            _rel(topic_root / "operator_checkpoint.active.json", kernel_root),
        )
        operator_checkpoint.setdefault(
            "note_path",
            _rel(topic_root / "operator_checkpoint.active.md", kernel_root),
        )
    competing_hypotheses = normalize_competing_hypotheses(
        research_question.get("competing_hypotheses") or [],
        topic_slug=topic_slug,
    )
    leading_hypothesis = leading_competing_hypothesis(competing_hypotheses) or {}
    current_branch_hypothesis = active_branch_hypothesis(competing_hypotheses) or {}
    deferred_branch_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="deferred_buffer")
    followup_branch_hypotheses = hypotheses_for_route(competing_hypotheses, route_kind="followup_subtopic")
    route_activation = build_route_activation_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        topic_status_explainability=topic_state.get("status_explainability") or {},
    )
    route_reentry = build_route_reentry_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        topic_root=topic_root,
    )
    route_handoff = build_route_handoff_payload(
        topic_slug=topic_slug,
        competing_hypotheses=competing_hypotheses,
        route_activation=route_activation,
        route_reentry=route_reentry,
    )
    route_choice = build_route_choice_payload(
        topic_slug=topic_slug,
        topic_status_explainability=topic_state.get("status_explainability") or {},
        route_activation=route_activation,
        route_handoff=route_handoff,
    )
    route_transition_gate = build_route_transition_gate_payload(
        topic_slug=topic_slug,
        route_choice=route_choice,
        operator_checkpoint=operator_checkpoint,
    )
    route_transition_intent = build_route_transition_intent_payload(
        topic_slug=topic_slug,
        route_choice=route_choice,
        route_transition_gate=route_transition_gate,
    )
    route_transition_receipt = build_route_transition_receipt_payload(
        topic_slug=topic_slug,
        route_transition_intent=route_transition_intent,
        transition_history=transition_history,
    )
    route_transition_resolution = build_route_transition_resolution_payload(
        topic_slug=topic_slug,
        route_transition_intent=route_transition_intent,
        route_transition_receipt=route_transition_receipt,
        route_activation=route_activation,
    )
    route_transition_discrepancy = build_route_transition_discrepancy_payload(
        topic_slug=topic_slug,
        route_transition_resolution=route_transition_resolution,
        route_transition_receipt=route_transition_receipt,
    )
    route_transition_repair = build_route_transition_repair_payload(
        topic_slug=topic_slug,
        route_transition_discrepancy=route_transition_discrepancy,
        route_transition_resolution=route_transition_resolution,
        route_activation=route_activation,
    )
    route_transition_escalation = build_route_transition_escalation_payload(
        topic_slug=topic_slug,
        route_transition_repair=route_transition_repair,
        operator_checkpoint=operator_checkpoint,
    )
    route_transition_clearance = build_route_transition_clearance_payload(
        topic_slug=topic_slug,
        route_transition_escalation=route_transition_escalation,
        operator_checkpoint=operator_checkpoint,
    )
    route_transition_followthrough = build_route_transition_followthrough_payload(
        topic_slug=topic_slug,
        route_transition_clearance=route_transition_clearance,
    )
    route_transition_resumption = build_route_transition_resumption_payload(
        topic_slug=topic_slug,
        route_transition_followthrough=route_transition_followthrough,
        route_transition_resolution=route_transition_resolution,
        route_activation=route_activation,
        transition_history=transition_history,
    )
    route_transition_commitment = build_route_transition_commitment_payload(
        topic_slug=topic_slug,
        route_transition_resumption=route_transition_resumption,
        route_activation=route_activation,
        competing_hypotheses=competing_hypotheses,
    )
    route_transition_authority = build_route_transition_authority_payload(
        topic_slug=topic_slug,
        route_transition_commitment=route_transition_commitment,
        route_activation=route_activation,
    )

    overview = {
        "topic_slug": topic_slug,
        "title": _first_text(synopsis.get("title"), research_question.get("title"), topic_slug),
        "question": _first_text(synopsis.get("question"), research_question.get("question")),
        "lane": _first_text(synopsis.get("lane"), topic_state.get("research_mode")),
        "human_request": _first_text(synopsis.get("human_request")),
    }

    human_modifications = [
        row
        for row in (promotion_gate.get("human_modifications") or [])
        if isinstance(row, dict)
    ]

    current_position = {
        "resume_stage": _first_text(topic_state.get("resume_stage")),
        "last_materialized_stage": _first_text(topic_state.get("last_materialized_stage")),
        "latest_run_id": _first_text(topic_state.get("latest_run_id"), topic_completion.get("run_id")),
        "status_summary": _first_text(
            ((topic_state.get("status_explainability") or {}).get("current_status_summary")),
            topic_state.get("summary"),
        ),
        "next_action_summary": _first_text(
            synopsis.get("next_action_summary"),
            ((next_action.get("selected_action") or {}).get("summary")),
            ((topic_state.get("status_explainability") or {}).get("next_bounded_action") or {}).get("summary"),
        ),
        "l0_source_handoff_summary": _first_text(l0_source_handoff.get("summary")),
        "open_gap_summary": _first_text(synopsis.get("open_gap_summary"), topic_completion.get("summary")),
        "latest_transition_reason": _first_text(((transition_history.get("latest_transition") or {}).get("reason"))),
        "latest_demotion_reason": _first_text(((transition_history.get("latest_demotion") or {}).get("reason"))),
        "approval_change_kind": _first_text(promotion_gate.get("approval_change_kind")),
        "latest_human_modification_summary": _first_text(
            f"{human_modifications[0].get('field')}: {human_modifications[0].get('change')}"
            if human_modifications
            else ""
        ),
        "leading_competing_hypothesis_id": _first_text(leading_hypothesis.get("hypothesis_id")),
        "leading_competing_hypothesis_summary": _first_text(
            f"{leading_hypothesis.get('label')}: {leading_hypothesis.get('summary')}"
            if leading_hypothesis
            else ""
        ),
        "active_branch_hypothesis_id": _first_text(current_branch_hypothesis.get("hypothesis_id")),
        "active_branch_hypothesis_summary": _first_text(
            f"{current_branch_hypothesis.get('label')}: {current_branch_hypothesis.get('route_target_summary')}"
            if current_branch_hypothesis
            else ""
        ),
        "active_local_action_summary": _first_text(route_activation.get("active_local_action_summary")),
        "reentry_ready_count": int(route_reentry.get("reentry_ready_count") or 0),
        "primary_handoff_candidate_id": _first_text(route_handoff.get("primary_handoff_candidate_id")),
        "route_choice_status": _first_text(route_choice.get("choice_status")),
        "route_transition_gate_status": _first_text(route_transition_gate.get("transition_status")),
        "route_transition_intent_status": _first_text(route_transition_intent.get("intent_status")),
        "route_transition_receipt_status": _first_text(route_transition_receipt.get("receipt_status")),
        "route_transition_resolution_status": _first_text(route_transition_resolution.get("resolution_status")),
        "route_transition_discrepancy_status": _first_text(route_transition_discrepancy.get("discrepancy_status")),
        "route_transition_repair_status": _first_text(route_transition_repair.get("repair_status")),
        "route_transition_escalation_status": _first_text(route_transition_escalation.get("escalation_status")),
        "route_transition_clearance_status": _first_text(route_transition_clearance.get("clearance_status")),
        "route_transition_followthrough_status": _first_text(route_transition_followthrough.get("followthrough_status")),
        "route_transition_resumption_status": _first_text(route_transition_resumption.get("resumption_status")),
        "route_transition_commitment_status": _first_text(route_transition_commitment.get("commitment_status")),
        "route_transition_authority_status": _first_text(route_transition_authority.get("authority_status")),
    }

    conclusions = {
        "topic_completion_status": _first_text(topic_completion.get("status")),
        "topic_completion_summary": _first_text(topic_completion.get("summary")),
        "validation_review_status": _first_text(review_bundle.get("status")),
        "validation_review_summary": _first_text(review_bundle.get("summary")),
        "projection_status": _first_text(projection.get("status")),
        "projection_summary": _first_text(projection.get("summary")),
        "promoted_units": [str(item) for item in (((topic_state.get("promotion_gate") or {}).get("promoted_units")) or []) if str(item).strip()],
        "promotion_ready_candidate_ids": [str(item) for item in (topic_completion.get("promotion_ready_candidate_ids") or []) if str(item).strip()],
        "blocked_candidate_ids": [str(item) for item in (topic_completion.get("blocked_candidate_ids") or []) if str(item).strip()],
        "open_gap_ids": [str(item) for item in (topic_completion.get("open_gap_ids") or []) if str(item).strip()],
        "blockers": [str(item) for item in (topic_completion.get("blockers") or review_bundle.get("blockers") or []) if str(item).strip()],
        "transition_count": int(transition_history.get("transition_count") or 0),
        "backtrack_count": int(transition_history.get("backtrack_count") or 0),
        "demotion_count": int(transition_history.get("demotion_count") or 0),
        "approval_change_kind": _first_text(promotion_gate.get("approval_change_kind")),
        "human_modification_count": len(human_modifications),
        "competing_hypothesis_count": len(competing_hypotheses),
        "excluded_competing_hypothesis_count": sum(
            1 for row in competing_hypotheses if str(row.get("status") or "").strip() == "excluded"
        ),
        "deferred_branch_hypothesis_count": len(deferred_branch_hypotheses),
        "followup_branch_hypothesis_count": len(followup_branch_hypotheses),
        "parked_route_count": int(route_activation.get("parked_route_count") or 0),
        "reentry_ready_count": int(route_reentry.get("reentry_ready_count") or 0),
        "handoff_candidate_count": int(route_handoff.get("handoff_candidate_count") or 0),
        "route_choice_status": _first_text(route_choice.get("choice_status")),
        "route_transition_gate_status": _first_text(route_transition_gate.get("transition_status")),
        "route_transition_intent_status": _first_text(route_transition_intent.get("intent_status")),
        "route_transition_receipt_status": _first_text(route_transition_receipt.get("receipt_status")),
        "route_transition_resolution_status": _first_text(route_transition_resolution.get("resolution_status")),
        "route_transition_discrepancy_status": _first_text(route_transition_discrepancy.get("discrepancy_status")),
        "route_transition_repair_status": _first_text(route_transition_repair.get("repair_status")),
        "route_transition_escalation_status": _first_text(route_transition_escalation.get("escalation_status")),
        "route_transition_clearance_status": _first_text(route_transition_clearance.get("clearance_status")),
        "route_transition_followthrough_status": _first_text(route_transition_followthrough.get("followthrough_status")),
        "route_transition_resumption_status": _first_text(route_transition_resumption.get("resumption_status")),
        "route_transition_commitment_status": _first_text(route_transition_commitment.get("commitment_status")),
        "route_transition_authority_status": _first_text(route_transition_authority.get("authority_status")),
    }

    reading_path = []

    def add_step(label: str, filename: str, reason: str, *, required: bool = False) -> None:
        path = topic_root / filename
        if path.exists():
            reading_path.append(
                {
                    "label": label,
                    "path": _rel(path, kernel_root),
                    "reason": reason,
                    "required": required,
                }
            )

    add_step("Current dashboard", "topic_dashboard.md", "Start here for the current human-facing topic state.", required=True)
    add_step("Question contract", "research_question.contract.md", "Read the bounded question, competing hypotheses, branch routes, deliverables, and forbidden proxies.", required=True)
    add_step("Deferred buffer", "deferred_candidates.json", "Inspect deferred reactivation conditions for parked hypotheses when a parked local route matters.")
    add_step("Follow-up subtopics", "followup_subtopics.jsonl", "Inspect parked follow-up child routes and their return-packet links when re-entry matters.")
    add_step("Follow-up reintegration", "followup_reintegration.jsonl", "Inspect child follow-up returns that are already ready or returned with unresolved parent-side gaps.")
    add_step("Follow-up gap writeback", "followup_gap_writeback.jsonl", "Inspect unresolved child returns that have already written parent-side gap debt.")
    add_step("Validation review bundle", "validation_review_bundle.active.md", "Review the active L4 evidence and specialist artifacts when present.")
    if iteration_journal_path is not None and iteration_journal_path.exists():
        reading_path.append(
            {
                "label": "Iteration journal",
                "path": _rel(iteration_journal_path, kernel_root),
                "reason": "Review the run-local L3-L4 iteration trail before reconstructing the same round from scattered artifacts.",
                "required": False,
            }
        )
    add_step("Topic completion", "topic_completion.md", "Check what the topic currently claims to have completed or promoted.")
    add_step("Promotion gate", "promotion_gate.md", "Inspect the current human approval gate, including any recorded human modifications.")
    add_step("Reusable projection", "topic_skill_projection.active.md", "Inspect reusable route memory when the topic already yielded a projection.")
    add_step("Transition history", "transition_history.md", "Inspect forward and backward layer moves, including demotion reasons and evidence refs.")
    add_step("Runtime protocol", "runtime_protocol.generated.md", "Use the runtime read-order bundle for deeper protocol navigation.")
    add_step("Resume note", "resume.md", "See the compact resume context and additional pointers.")

    authoritative_artifacts = {
        "topic_synopsis_path": _existing_note(topic_root / "topic_synopsis.json", kernel_root=kernel_root),
        "topic_dashboard_path": _existing_note(topic_root / "topic_dashboard.md", kernel_root=kernel_root),
        "research_question_path": _existing_note(topic_root / "research_question.contract.md", kernel_root=kernel_root),
        "deferred_buffer_path": _existing_note(topic_root / "deferred_candidates.json", kernel_root=kernel_root),
        "followup_subtopics_path": _existing_note(topic_root / "followup_subtopics.jsonl", kernel_root=kernel_root),
        "followup_reintegration_path": _existing_note(topic_root / "followup_reintegration.jsonl", kernel_root=kernel_root),
        "followup_gap_writeback_path": _existing_note(topic_root / "followup_gap_writeback.jsonl", kernel_root=kernel_root),
        "validation_review_bundle_path": _existing_note(topic_root / "validation_review_bundle.active.md", kernel_root=kernel_root),
        "iteration_journal_path": _existing_note(iteration_journal_path, kernel_root=kernel_root) if iteration_journal_path is not None else None,
        "topic_completion_path": _existing_note(topic_root / "topic_completion.md", kernel_root=kernel_root),
        "promotion_gate_path": _existing_note(topic_root / "promotion_gate.md", kernel_root=kernel_root),
        "topic_skill_projection_path": _existing_note(topic_root / "topic_skill_projection.active.md", kernel_root=kernel_root),
        "transition_history_path": _existing_note(topic_root / "transition_history.md", kernel_root=kernel_root),
        "runtime_protocol_path": _existing_note(topic_root / "runtime_protocol.generated.md", kernel_root=kernel_root),
        "resume_path": _existing_note(topic_root / "resume.md", kernel_root=kernel_root),
    }

    missing_artifacts = [name for name, path in authoritative_artifacts.items() if path is None]

    return {
        "kind": "topic_replay_bundle",
        "bundle_version": 1,
        "generated_at": now_iso(),
        "topic_slug": topic_slug,
        "source_contract_path": "TOPIC_REPLAY_PROTOCOL.md",
        "overview": overview,
        "current_position": current_position,
        "conclusions": conclusions,
        "route_activation": route_activation,
        "route_reentry": route_reentry,
        "route_handoff": route_handoff,
        "route_choice": route_choice,
        "route_transition_gate": route_transition_gate,
        "route_transition_intent": route_transition_intent,
        "route_transition_receipt": route_transition_receipt,
        "route_transition_resolution": route_transition_resolution,
        "route_transition_discrepancy": route_transition_discrepancy,
        "route_transition_repair": route_transition_repair,
        "route_transition_escalation": route_transition_escalation,
        "route_transition_clearance": route_transition_clearance,
        "route_transition_followthrough": route_transition_followthrough,
        "route_transition_resumption": route_transition_resumption,
        "route_transition_commitment": route_transition_commitment,
        "route_transition_authority": route_transition_authority,
        "competing_hypotheses": competing_hypotheses,
        "reading_path": reading_path,
        "l0_source_handoff": l0_source_handoff,
        "authoritative_artifacts": authoritative_artifacts,
        "missing_artifacts": missing_artifacts,
    }


def render_topic_replay_bundle_markdown(payload: dict[str, Any]) -> str:
    overview = payload.get("overview") or {}
    current = payload.get("current_position") or {}
    l0_source_handoff = payload.get("l0_source_handoff") or {}
    conclusions = payload.get("conclusions") or {}
    lines = [
        "# Topic Replay Bundle",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        "",
        "## Overview",
        "",
        f"- Title: `{overview.get('title') or '(missing)'}`",
        f"- Question: {overview.get('question') or '(missing)' }",
        f"- Lane / mode: `{overview.get('lane') or '(missing)'}`",
        f"- Human request: {overview.get('human_request') or '(none recorded)' }",
        "",
        "## Current Position",
        "",
        f"- Resume stage: `{current.get('resume_stage') or '(missing)'}`",
        f"- Last materialized stage: `{current.get('last_materialized_stage') or '(missing)'}`",
        f"- Latest run id: `{current.get('latest_run_id') or '(missing)'}`",
        f"- Status summary: {current.get('status_summary') or '(missing)' }",
        f"- Next action summary: {current.get('next_action_summary') or '(missing)' }",
        f"- L0 source handoff summary: {current.get('l0_source_handoff_summary') or '(none recorded)' }",
        f"- Open gap summary: {current.get('open_gap_summary') or '(none recorded)' }",
        f"- Latest transition reason: {current.get('latest_transition_reason') or '(none recorded)' }",
        f"- Latest demotion reason: {current.get('latest_demotion_reason') or '(none recorded)' }",
        f"- Approval change kind: `{current.get('approval_change_kind') or '(none recorded)'}`",
        f"- Latest human modification summary: {current.get('latest_human_modification_summary') or '(none recorded)' }",
        f"- Leading competing hypothesis id: `{current.get('leading_competing_hypothesis_id') or '(none recorded)'}`",
        f"- Leading competing hypothesis summary: {current.get('leading_competing_hypothesis_summary') or '(none recorded)' }",
        f"- Active branch hypothesis id: `{current.get('active_branch_hypothesis_id') or '(none recorded)'}`",
        f"- Active branch hypothesis summary: {current.get('active_branch_hypothesis_summary') or '(none recorded)' }",
        f"- Active local action summary: {current.get('active_local_action_summary') or '(none recorded)' }",
        f"- Re-entry-ready parked routes: `{current.get('reentry_ready_count') or 0}`",
        f"- Primary handoff candidate id: `{current.get('primary_handoff_candidate_id') or '(none recorded)'}`",
        f"- Route choice status: `{current.get('route_choice_status') or '(none recorded)'}`",
        f"- Route transition-gate status: `{current.get('route_transition_gate_status') or '(none recorded)'}`",
        f"- Route transition-intent status: `{current.get('route_transition_intent_status') or '(none recorded)'}`",
        f"- Route transition-receipt status: `{current.get('route_transition_receipt_status') or '(none recorded)'}`",
        f"- Route transition-resolution status: `{current.get('route_transition_resolution_status') or '(none recorded)'}`",
        f"- Route transition-discrepancy status: `{current.get('route_transition_discrepancy_status') or '(none recorded)'}`",
        f"- Route transition-repair status: `{current.get('route_transition_repair_status') or '(none recorded)'}`",
        f"- Route transition-escalation status: `{current.get('route_transition_escalation_status') or '(none recorded)'}`",
        f"- Route transition-clearance status: `{current.get('route_transition_clearance_status') or '(none recorded)'}`",
        f"- Route transition-followthrough status: `{current.get('route_transition_followthrough_status') or '(none recorded)'}`",
        f"- Route transition-resumption status: `{current.get('route_transition_resumption_status') or '(none recorded)'}`",
        f"- Route transition-commitment status: `{current.get('route_transition_commitment_status') or '(none recorded)'}`",
        f"- Route transition-authority status: `{current.get('route_transition_authority_status') or '(none recorded)'}`",
        "",
        "## Competing Hypotheses",
        "",
        f"- Count: `{conclusions.get('competing_hypothesis_count') or 0}`",
        f"- Excluded count: `{conclusions.get('excluded_competing_hypothesis_count') or 0}`",
        f"- Deferred-route count: `{conclusions.get('deferred_branch_hypothesis_count') or 0}`",
        f"- Follow-up-route count: `{conclusions.get('followup_branch_hypothesis_count') or 0}`",
        f"- Parked-route count: `{conclusions.get('parked_route_count') or 0}`",
        f"- Re-entry-ready count: `{conclusions.get('reentry_ready_count') or 0}`",
        f"- Handoff-candidate count: `{conclusions.get('handoff_candidate_count') or 0}`",
        f"- Route-choice status: `{conclusions.get('route_choice_status') or '(none)'}`",
        f"- Route-transition-gate status: `{conclusions.get('route_transition_gate_status') or '(none)'}`",
        f"- Route-transition-intent status: `{conclusions.get('route_transition_intent_status') or '(none)'}`",
        f"- Route-transition-receipt status: `{conclusions.get('route_transition_receipt_status') or '(none)'}`",
        f"- Route-transition-resolution status: `{conclusions.get('route_transition_resolution_status') or '(none)'}`",
        f"- Route-transition-discrepancy status: `{conclusions.get('route_transition_discrepancy_status') or '(none)'}`",
        f"- Route-transition-repair status: `{conclusions.get('route_transition_repair_status') or '(none)'}`",
        f"- Route-transition-escalation status: `{conclusions.get('route_transition_escalation_status') or '(none)'}`",
        f"- Route-transition-clearance status: `{conclusions.get('route_transition_clearance_status') or '(none)'}`",
        f"- Route-transition-followthrough status: `{conclusions.get('route_transition_followthrough_status') or '(none)'}`",
        f"- Route-transition-resumption status: `{conclusions.get('route_transition_resumption_status') or '(none)'}`",
        f"- Route-transition-commitment status: `{conclusions.get('route_transition_commitment_status') or '(none)'}`",
        f"- Route-transition-authority status: `{conclusions.get('route_transition_authority_status') or '(none)'}`",
        "",
    ]
    if l0_source_handoff:
        lines.extend(
            [
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
        lines.append("")

    for row in payload.get("competing_hypotheses") or []:
        lines.append(
            f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or 'active'}` route=`{row.get('route_kind') or 'current_topic'}` evidence_refs=`{row.get('evidence_ref_count') or 0}`"
        )
        lines.append(f"  label: {row.get('label') or '(missing)'}")
        lines.append(f"  summary: {row.get('summary') or '(missing)'}")
        lines.append(f"  route target: {row.get('route_target_summary') or '(none)'}")
        lines.append(f"  route ref: `{row.get('route_target_ref') or '(none)'}`")
        lines.append(f"  evidence refs: `{', '.join(row.get('evidence_refs') or []) or '(none)'}`")
        lines.append(f"  exclusion notes: {', '.join(row.get('exclusion_notes') or []) or '(none)'}")
    if not (payload.get("competing_hypotheses") or []):
        lines.append("- No explicit competing hypotheses are currently recorded.")
    route_activation = payload.get("route_activation") or {}
    lines.extend(
        [
            "",
            "## Route Activation",
            "",
            f"- Active local hypothesis: `{route_activation.get('active_local_hypothesis_id') or '(none recorded)'}`",
            f"- Active local action: {route_activation.get('active_local_action_summary') or '(none recorded)'}",
            f"- Active local action ref: `{route_activation.get('active_local_action_ref') or '(none)'}`",
            f"- Parked route count: `{route_activation.get('parked_route_count') or 0}`",
            "",
            "### Deferred obligations",
            "",
        ]
    )
    for row in route_activation.get("deferred_obligations") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or '(missing)'}`: {row.get('obligation_summary') or '(missing)'}"
            )
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Follow-up obligations", ""])
    for row in route_activation.get("followup_obligations") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` status=`{row.get('status') or '(missing)'}`: {row.get('obligation_summary') or '(missing)'}"
            )
            lines.append(f"  target ref: `{row.get('target_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    route_reentry = payload.get("route_reentry") or {}
    lines.extend(
        [
            "",
            "## Route Re-entry",
            "",
            f"- Re-entry-ready count: `{route_reentry.get('reentry_ready_count') or 0}`",
            "",
            "### Deferred routes",
            "",
        ]
    )
    for row in route_reentry.get("deferred_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('reentry_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Follow-up routes", ""])
    for row in route_reentry.get("followup_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('reentry_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    route_handoff = payload.get("route_handoff") or {}
    lines.extend(
        [
            "",
            "## Route Handoff",
            "",
            f"- Active local hypothesis: `{route_handoff.get('active_local_hypothesis_id') or '(none recorded)'}`",
            f"- Primary handoff candidate: `{route_handoff.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Handoff candidate count: `{route_handoff.get('handoff_candidate_count') or 0}`",
            "",
            "### Handoff candidates",
            "",
        ]
    )
    for row in route_handoff.get("handoff_candidates") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` handoff_status=`{row.get('handoff_status') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('handoff_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "### Keep parked", ""])
    for row in route_handoff.get("keep_parked_routes") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('hypothesis_id') or '(missing)'}` handoff_status=`{row.get('handoff_status') or '(missing)'}` reentry_status=`{row.get('reentry_status') or '(missing)'}`: {row.get('handoff_summary') or '(missing)'}"
            )
            lines.append(f"  conditions: {row.get('condition_summary') or '(missing)'}")
            lines.append(f"  support ref: `{row.get('support_ref') or '(none)'}`")
        else:
            lines.append(f"- {row}")
    route_choice = payload.get("route_choice") or {}
    lines.extend(
        [
            "",
            "## Route Choice",
            "",
            f"- Choice status: `{route_choice.get('choice_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_choice.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Primary handoff candidate: `{route_choice.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Current route-choice ref: `{route_choice.get('current_route_choice_ref') or '(none)'}`",
            "",
            route_choice.get("choice_summary") or "(missing)",
            "",
            "### Stay local",
            "",
        ]
    )
    stay_local = route_choice.get("stay_local_option") or {}
    lines.append(
        f"- `{stay_local.get('hypothesis_id') or '(none)'}` option_kind=`{stay_local.get('option_kind') or '(missing)'}`: {stay_local.get('option_summary') or '(missing)'}"
    )
    lines.append(f"  target ref: `{stay_local.get('target_ref') or '(none)'}`")
    lines.extend(["", "### Yield to handoff", ""])
    yield_option = route_choice.get("yield_to_handoff_option") or {}
    lines.append(
        f"- `{yield_option.get('hypothesis_id') or '(none)'}` option_kind=`{yield_option.get('option_kind') or '(missing)'}`: {yield_option.get('option_summary') or '(missing)'}"
    )
    lines.append(f"  target ref: `{yield_option.get('target_ref') or '(none)'}`")
    route_transition_gate = payload.get("route_transition_gate") or {}
    lines.extend(
        [
            "",
            "## Route Transition Gate",
            "",
            f"- Transition status: `{route_transition_gate.get('transition_status') or '(missing)'}`",
            f"- Choice status: `{route_transition_gate.get('choice_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_gate.get('checkpoint_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_gate.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Primary handoff candidate: `{route_transition_gate.get('primary_handoff_candidate_id') or '(none)'}`",
            f"- Gate kind: `{route_transition_gate.get('gate_kind') or '(missing)'}`",
            f"- Gate artifact ref: `{route_transition_gate.get('gate_artifact_ref') or '(none)'}`",
            f"- Transition target ref: `{route_transition_gate.get('transition_target_ref') or '(none)'}`",
            "",
            route_transition_gate.get("transition_summary") or "(missing)",
        ]
    )
    route_transition_intent = payload.get("route_transition_intent") or {}
    lines.extend(
        [
            "",
            "## Route Transition Intent",
            "",
            f"- Intent status: `{route_transition_intent.get('intent_status') or '(missing)'}`",
            f"- Gate status: `{route_transition_intent.get('gate_status') or '(missing)'}`",
            f"- Source hypothesis: `{route_transition_intent.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_intent.get('target_hypothesis_id') or '(none)'}`",
            f"- Source route ref: `{route_transition_intent.get('source_route_ref') or '(none)'}`",
            f"- Target route ref: `{route_transition_intent.get('target_route_ref') or '(none)'}`",
            f"- Gate artifact ref: `{route_transition_intent.get('gate_artifact_ref') or '(none)'}`",
            "",
            route_transition_intent.get("intent_summary") or "(missing)",
        ]
    )
    route_transition_receipt = payload.get("route_transition_receipt") or {}
    lines.extend(
        [
            "",
            "## Route Transition Receipt",
            "",
            f"- Receipt status: `{route_transition_receipt.get('receipt_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_receipt.get('intent_status') or '(missing)'}`",
            f"- Source hypothesis: `{route_transition_receipt.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_receipt.get('target_hypothesis_id') or '(none)'}`",
            f"- Receipt transition id: `{route_transition_receipt.get('receipt_transition_id') or '(none)'}`",
            f"- Receipt artifact ref: `{route_transition_receipt.get('receipt_artifact_ref') or '(none)'}`",
            f"- Receipt recorded at: `{route_transition_receipt.get('receipt_recorded_at') or '(none)'}`",
            "",
            route_transition_receipt.get("receipt_summary") or "(missing)",
        ]
    )
    route_transition_resolution = payload.get("route_transition_resolution") or {}
    lines.extend(
        [
            "",
            "## Route Transition Resolution",
            "",
            f"- Resolution status: `{route_transition_resolution.get('resolution_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_resolution.get('intent_status') or '(missing)'}`",
            f"- Receipt status: `{route_transition_resolution.get('receipt_status') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_resolution.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Source hypothesis: `{route_transition_resolution.get('source_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_resolution.get('target_hypothesis_id') or '(none)'}`",
            f"- Active-route alignment: `{route_transition_resolution.get('active_route_alignment') or '(missing)'}`",
            f"- Resolution artifact ref: `{route_transition_resolution.get('resolution_artifact_ref') or '(none)'}`",
            "",
            route_transition_resolution.get("resolution_summary") or "(missing)",
        ]
    )
    route_transition_discrepancy = payload.get("route_transition_discrepancy") or {}
    lines.extend(
        [
            "",
            "## Route Transition Discrepancy",
            "",
            f"- Discrepancy status: `{route_transition_discrepancy.get('discrepancy_status') or '(missing)'}`",
            f"- Discrepancy kind: `{route_transition_discrepancy.get('discrepancy_kind') or '(missing)'}`",
            f"- Severity: `{route_transition_discrepancy.get('severity') or '(missing)'}`",
            f"- Resolution status: `{route_transition_discrepancy.get('resolution_status') or '(missing)'}`",
            f"- Intent status: `{route_transition_discrepancy.get('intent_status') or '(missing)'}`",
            f"- Receipt status: `{route_transition_discrepancy.get('receipt_status') or '(missing)'}`",
            f"- Active-route alignment: `{route_transition_discrepancy.get('active_route_alignment') or '(missing)'}`",
            f"- Target hypothesis: `{route_transition_discrepancy.get('target_hypothesis_id') or '(none)'}`",
            f"- Artifact refs: `{', '.join(route_transition_discrepancy.get('discrepancy_artifact_refs') or []) or '(none)'}`",
            "",
            route_transition_discrepancy.get("discrepancy_summary") or "(missing)",
        ]
    )
    route_transition_repair = payload.get("route_transition_repair") or {}
    lines.extend(
        [
            "",
            "## Route Transition Repair",
            "",
            f"- Repair status: `{route_transition_repair.get('repair_status') or '(missing)'}`",
            f"- Discrepancy status: `{route_transition_repair.get('discrepancy_status') or '(missing)'}`",
            f"- Discrepancy kind: `{route_transition_repair.get('discrepancy_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_repair.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_repair.get('target_hypothesis_id') or '(none)'}`",
            f"- Active-route alignment: `{route_transition_repair.get('active_route_alignment') or '(missing)'}`",
            f"- Repair kind: `{route_transition_repair.get('repair_kind') or '(missing)'}`",
            f"- Primary repair ref: `{route_transition_repair.get('primary_repair_ref') or '(none)'}`",
            f"- Repair artifact refs: `{', '.join(route_transition_repair.get('repair_artifact_refs') or []) or '(none)'}`",
            "",
            route_transition_repair.get("repair_summary") or "(missing)",
        ]
    )
    route_transition_escalation = payload.get("route_transition_escalation") or {}
    lines.extend(
        [
            "",
            "## Route Transition Escalation",
            "",
            f"- Escalation status: `{route_transition_escalation.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_escalation.get('repair_status') or '(missing)'}`",
            f"- Repair kind: `{route_transition_escalation.get('repair_kind') or '(missing)'}`",
            f"- Primary repair ref: `{route_transition_escalation.get('primary_repair_ref') or '(none)'}`",
            f"- Checkpoint status: `{route_transition_escalation.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint kind: `{route_transition_escalation.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint ref: `{route_transition_escalation.get('checkpoint_ref') or '(none)'}`",
            "",
            route_transition_escalation.get("escalation_summary") or "(missing)",
        ]
    )
    route_transition_clearance = payload.get("route_transition_clearance") or {}
    lines.extend(
        [
            "",
            "## Route Transition Clearance",
            "",
            f"- Clearance status: `{route_transition_clearance.get('clearance_status') or '(missing)'}`",
            f"- Clearance kind: `{route_transition_clearance.get('clearance_kind') or '(missing)'}`",
            f"- Escalation status: `{route_transition_clearance.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_clearance.get('repair_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_clearance.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint kind: `{route_transition_clearance.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint ref: `{route_transition_clearance.get('checkpoint_ref') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_clearance.get('followthrough_ref') or '(none)'}`",
            "",
            route_transition_clearance.get("clearance_summary") or "(missing)",
        ]
    )
    route_transition_followthrough = payload.get("route_transition_followthrough") or {}
    lines.extend(
        [
            "",
            "## Route Transition Followthrough",
            "",
            f"- Follow-through status: `{route_transition_followthrough.get('followthrough_status') or '(missing)'}`",
            f"- Follow-through kind: `{route_transition_followthrough.get('followthrough_kind') or '(missing)'}`",
            f"- Clearance status: `{route_transition_followthrough.get('clearance_status') or '(missing)'}`",
            f"- Clearance kind: `{route_transition_followthrough.get('clearance_kind') or '(missing)'}`",
            f"- Escalation status: `{route_transition_followthrough.get('escalation_status') or '(missing)'}`",
            f"- Repair status: `{route_transition_followthrough.get('repair_status') or '(missing)'}`",
            f"- Checkpoint status: `{route_transition_followthrough.get('checkpoint_status') or '(missing)'}`",
            f"- Checkpoint ref: `{route_transition_followthrough.get('checkpoint_ref') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_followthrough.get('followthrough_ref') or '(none)'}`",
            "",
            route_transition_followthrough.get("followthrough_summary") or "(missing)",
        ]
    )
    route_transition_resumption = payload.get("route_transition_resumption") or {}
    lines.extend(
        [
            "",
            "## Route Transition Resumption",
            "",
            f"- Resumption status: `{route_transition_resumption.get('resumption_status') or '(missing)'}`",
            f"- Resumption kind: `{route_transition_resumption.get('resumption_kind') or '(missing)'}`",
            f"- Follow-through status: `{route_transition_resumption.get('followthrough_status') or '(missing)'}`",
            f"- Active-route alignment: `{route_transition_resumption.get('active_route_alignment') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_resumption.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Target hypothesis: `{route_transition_resumption.get('target_hypothesis_id') or '(none)'}`",
            f"- Follow-through ref: `{route_transition_resumption.get('followthrough_ref') or '(none)'}`",
            f"- Resumption ref: `{route_transition_resumption.get('resumption_ref') or '(none)'}`",
            "",
            route_transition_resumption.get("resumption_summary") or "(missing)",
        ]
    )
    route_transition_commitment = payload.get("route_transition_commitment") or {}
    lines.extend(
        [
            "",
            "## Route Transition Commitment",
            "",
            f"- Commitment status: `{route_transition_commitment.get('commitment_status') or '(missing)'}`",
            f"- Commitment kind: `{route_transition_commitment.get('commitment_kind') or '(missing)'}`",
            f"- Resumption status: `{route_transition_commitment.get('resumption_status') or '(missing)'}`",
            f"- Resumption kind: `{route_transition_commitment.get('resumption_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_commitment.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Route kind: `{route_transition_commitment.get('route_kind') or '(missing)'}`",
            f"- Resumption ref: `{route_transition_commitment.get('resumption_ref') or '(none)'}`",
            f"- Commitment ref: `{route_transition_commitment.get('commitment_ref') or '(none)'}`",
            "",
            route_transition_commitment.get("commitment_summary") or "(missing)",
        ]
    )
    route_transition_authority = payload.get("route_transition_authority") or {}
    lines.extend(
        [
            "",
            "## Route Transition Authority",
            "",
            f"- Authority status: `{route_transition_authority.get('authority_status') or '(missing)'}`",
            f"- Authority kind: `{route_transition_authority.get('authority_kind') or '(missing)'}`",
            f"- Commitment status: `{route_transition_authority.get('commitment_status') or '(missing)'}`",
            f"- Commitment kind: `{route_transition_authority.get('commitment_kind') or '(missing)'}`",
            f"- Active local hypothesis: `{route_transition_authority.get('active_local_hypothesis_id') or '(none)'}`",
            f"- Route kind: `{route_transition_authority.get('route_kind') or '(missing)'}`",
            f"- Route target ref: `{route_transition_authority.get('route_target_ref') or '(none)'}`",
            f"- Commitment ref: `{route_transition_authority.get('commitment_ref') or '(none)'}`",
            f"- Authority ref: `{route_transition_authority.get('authority_ref') or '(none)'}`",
            "",
            route_transition_authority.get("authority_summary") or "(missing)",
        ]
    )
    lines.extend(
        [
            "",
            "## What This Topic Currently Says",
            "",
            f"- Topic completion status: `{conclusions.get('topic_completion_status') or '(missing)'}`",
            f"- Topic completion summary: {conclusions.get('topic_completion_summary') or '(missing)' }",
            f"- Validation review status: `{conclusions.get('validation_review_status') or '(missing)'}`",
            f"- Validation review summary: {conclusions.get('validation_review_summary') or '(missing)' }",
            f"- Projection status: `{conclusions.get('projection_status') or '(missing)'}`",
            f"- Projection summary: {conclusions.get('projection_summary') or '(missing)' }",
            f"- Transition count: `{conclusions.get('transition_count') or 0}`",
            f"- Backtrack count: `{conclusions.get('backtrack_count') or 0}`",
            f"- Demotion count: `{conclusions.get('demotion_count') or 0}`",
            f"- Approval change kind: `{conclusions.get('approval_change_kind') or '(none recorded)'}`",
            f"- Human modification count: `{conclusions.get('human_modification_count') or 0}`",
            "",
            "## Reusable Outputs",
            "",
            f"- Promoted units: `{', '.join(conclusions.get('promoted_units') or []) or '(none)'}`",
            f"- Promotion-ready candidates: `{', '.join(conclusions.get('promotion_ready_candidate_ids') or []) or '(none)'}`",
            "",
            "## Reading Path",
            "",
        ]
    )

    for idx, step in enumerate(payload.get("reading_path") or [], start=1):
        lines.append(
            f"{idx}. `{step.get('path') or '(missing)'}`"
        )
        lines.append(f"   - {step.get('reason') or '(missing reason)'}")

    if not (payload.get("reading_path") or []):
        lines.append("No reading-path steps could be materialized from the current topic artifacts.")

    lines.extend(["", "## Authoritative Artifacts", ""])
    for key, path in (payload.get("authoritative_artifacts") or {}).items():
        lines.append(f"- `{key}`: `{path or '(missing)'}`")

    lines.extend(["", "## Missing Artifacts", ""])
    missing = payload.get("missing_artifacts") or []
    if missing:
        for item in missing:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `(none)`")

    lines.extend(
        [
            "",
            "## Replay Rule",
            "",
            "This bundle is derived for human study. When it conflicts with the underlying artifact files, the underlying artifacts win.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def materialize_topic_replay_bundle(kernel_root: Path, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    topic_root = _runtime_root(kernel_root, topic_slug)
    payload = build_topic_replay_bundle(kernel_root, topic_slug)
    json_path = topic_root / "topic_replay_bundle.json"
    md_path = topic_root / "topic_replay_bundle.md"
    write_json(json_path, payload)
    write_text(md_path, render_topic_replay_bundle_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }
