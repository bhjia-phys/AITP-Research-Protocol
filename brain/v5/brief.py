"""Execution brief construction for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.domain_packs import suggest_tool_executors_for_claim
from brain.v5.evidence import list_evidence_for_claim, required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.interaction import prioritize_questions, resolve_interaction_profile
from brain.v5.models import ClaimRecord, CodeStateRecord
from brain.v5.policy import evaluate_policy
from brain.v5.question_engine import generate_questions
from brain.v5.risk import action_budget_for_level, assess_claim_risk
from brain.v5.store import list_records
from brain.v5.workspace import get_claim, get_session_binding


def build_execution_brief(ws, session_id: str) -> dict[str, Any]:
    """Build the state packet an agent should see before acting."""

    session = get_session_binding(ws, session_id)
    claim: ClaimRecord | None = None
    flow = None
    risk = None
    questions = []
    evidence_records = []

    if session.active_claim:
        claim = get_claim(ws, session.active_claim)
        risk = assess_claim_risk(claim, code_states=_linked_code_states(ws, claim.claim_id))
        flow = resolve_flow_profile(claim, assessment=risk)
        questions = generate_questions(claim, flow)
        evidence_records = list_evidence_for_claim(ws, claim.claim_id)

    action_budget = risk.action_budget if risk and risk.action_budget else action_budget_for_level("guided")
    evidence_coverage = required_output_coverage(
        evidence_records,
        required_outputs=action_budget.required_outputs,
    )
    interaction = resolve_interaction_profile(
        session.interaction_profile,
        risk_level=action_budget.level,
        max_questions=action_budget.max_questions,
        user_steering=session.interaction_steering,
    )
    questions = prioritize_questions(questions, interaction)
    mandatory_reflection = [
        asdict(q) for q in questions[: interaction.effective_max_questions]
    ]

    next_action_candidates = []
    policy_forbidden = []
    if claim and flow:
        policy_forbidden = _policy_forbidden_actions(claim, _linked_code_states(ws, claim.claim_id))
        if flow.profile == "fluid":
            next_action_candidates.append(
                {
                    "action": "run_trusted_recipe" if claim.recipe_id else "continue_fluid_work",
                    "rank": 1,
                    "why": flow.reason,
                    "expected_evidence_gain": "preserve flow while capturing a lightweight trace",
                }
            )
        elif flow.profile == "guided":
            next_action_candidates.append(
                {
                    "action": "answer_dynamic_physics_questions",
                    "rank": 1,
                    "why": "claim needs object-relation sense-making without a heavy review yet",
                    "expected_evidence_gain": "clarify claim scope, mechanism, and failure mode",
                }
            )
        elif flow.profile == "rigorous":
            next_action_candidates.append(
                {
                    "action": "collect_required_evidence_or_provenance",
                    "rank": 1,
                    "why": flow.reason,
                    "expected_evidence_gain": "turn a plausible claim into auditable evidence",
                }
            )
        else:
            next_action_candidates.append(
                {
                    "action": "design_falsification_or_counterargument",
                    "rank": 1,
                    "why": flow.reason,
                    "expected_evidence_gain": "find the cheapest way this claim could fail",
                }
            )

    return {
        "session": asdict(session),
        "current_focus": {
            "active_claim": session.active_claim,
            "active_route": session.active_route,
            "active_cycle": session.active_cycle,
            "claim_statement": claim.statement if claim else "",
            "confidence_state": claim.confidence_state if claim else "",
            "evidence_profile": claim.evidence_profile if claim else "",
            "main_uncertainty": claim.active_uncertainty if claim else "",
        },
        "flow_profile": asdict(flow) if flow else {"profile": "guided", "reason": "no active claim", "escalation_triggers": []},
        "risk_assessment": asdict(risk) if risk else _default_risk_assessment_payload(action_budget),
        "action_budget": asdict(action_budget),
        "evidence_coverage": asdict(evidence_coverage),
        "interaction_profile": asdict(interaction),
        "known_context": {
            "topic_id": session.topic_id,
            "context_id": session.context_id,
            "previous_failed_attempts": [],
            "recommended_tool_executors": suggest_tool_executors_for_claim(claim) if claim else [],
        },
        "mandatory_reflection": mandatory_reflection,
        "next_action_candidates": next_action_candidates,
        "forbidden_now": _forbidden_actions(flow.profile if flow else "guided") + policy_forbidden,
        "human_checkpoint": {
            "needed": action_budget.requires_human_checkpoint,
            "reason": "risk budget requires human checkpoint" if action_budget.requires_human_checkpoint else None,
        },
    }


def _forbidden_actions(profile: str) -> list[str]:
    if profile == "fluid":
        return ["promote_new_claim_without_review"]
    if profile == "guided":
        return ["treat_claim_as_validated", "skip_failure_mode_analysis"]
    if profile == "rigorous":
        return ["accept_result_without_evidence_or_provenance", "skip_minimal_check"]
    if profile == "adversarial":
        return ["ignore_counterargument", "promote_without_human_checkpoint"]
    return ["change_claim_confidence_without_evidence"]


def _linked_code_states(ws, claim_id: str) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [state for state in states if _record_links_to_claim(state.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id:
            return True
        if isinstance(value, list) and claim_id in value:
            return True
    return False


def _policy_forbidden_actions(claim: ClaimRecord, code_states: list[CodeStateRecord]) -> list[str]:
    decisions = [
        evaluate_policy(action="validate_claim", claim=claim, code_states=code_states),
        evaluate_policy(action="promote_to_l2", claim=claim, code_states=code_states, evidence_refs=[]),
    ]
    blocked: list[str] = []
    for decision in decisions:
        if decision.allowed:
            continue
        blocked.extend(f"policy:{reason.policy_id}" for reason in decision.reasons)
    return _dedupe(blocked)


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _default_risk_assessment_payload(action_budget) -> dict[str, Any]:
    return {
        "level": action_budget.level,
        "score": 0,
        "signals": [],
        "trust_reductions": [],
        "action_budget": asdict(action_budget),
        "human_checkpoint_needed": action_budget.requires_human_checkpoint,
        "summary": "guided protocol: no active claim",
    }
