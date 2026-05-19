"""Execution brief construction for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.domain_packs import suggest_tool_executors_for_claim
from brain.v5.evidence import list_evidence_for_claim, required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.interaction import prioritize_questions, resolve_interaction_profile
from brain.v5.knowledge_connectors import suggest_knowledge_connectors_for_claim
from brain.v5.models import ClaimRecord, CodeStateRecord
from brain.v5.policy import evaluate_policy
from brain.v5.question_engine import generate_questions
from brain.v5.physics_objects import list_object_relations_for_claim, object_relation_brief_payload
from brain.v5.references import list_reference_locations_for_claim, reference_location_brief_payload
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
    recommended_tool_executors = []
    knowledge_connectors = []
    reference_locations = []
    object_relations = []

    if session.active_claim:
        claim = get_claim(ws, session.active_claim)
        risk = assess_claim_risk(claim, code_states=_linked_code_states(ws, claim.claim_id))
        flow = resolve_flow_profile(claim, assessment=risk)
        questions = generate_questions(claim, flow)
        evidence_records = list_evidence_for_claim(ws, claim.claim_id)
        recommended_tool_executors = suggest_tool_executors_for_claim(claim)
        knowledge_connectors = suggest_knowledge_connectors_for_claim(claim)
        reference_locations = [
            reference_location_brief_payload(location)
            for location in list_reference_locations_for_claim(ws, claim.claim_id)
        ]
        object_relations = [
            object_relation_brief_payload(relation)
            for relation in list_object_relations_for_claim(ws, claim.claim_id)
        ]

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
        connector_action = _knowledge_connector_action(
            knowledge_connectors,
            why=flow.reason,
        )
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
            if connector_action:
                next_action_candidates.append(connector_action)
            next_action_candidates.append(
                {
                    "action": "answer_dynamic_physics_questions",
                    "rank": 2 if connector_action else 1,
                    "why": "claim needs object-relation sense-making without a heavy review yet",
                    "expected_evidence_gain": "clarify claim scope, mechanism, and failure mode",
                }
            )
        elif flow.profile == "rigorous":
            executor_action = _recommended_executor_action(
                recommended_tool_executors,
                missing_outputs=evidence_coverage.missing_outputs,
                why=flow.reason,
            )
            if executor_action:
                next_action_candidates.append(executor_action)
            if connector_action:
                connector_action["rank"] = 2 if executor_action else 1
                next_action_candidates.append(connector_action)
            next_action_candidates.append(
                {
                    "action": "collect_required_evidence_or_provenance",
                    "rank": 3 if executor_action and connector_action else 2 if executor_action or connector_action else 1,
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
            "recommended_tool_executors": recommended_tool_executors,
            "knowledge_connectors": knowledge_connectors,
            "reference_locations": reference_locations,
            "object_relations": object_relations,
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


def _recommended_executor_action(
    recommendations: list[dict],
    *,
    missing_outputs: list[str],
    why: str,
) -> dict[str, Any] | None:
    missing = set(missing_outputs)
    for recommendation in recommendations:
        supported = [output for output in recommendation.get("supports_outputs", []) if output in missing]
        if not supported:
            continue
        executor = recommendation.get("executor", {})
        return {
            "action": "execute_recommended_tool",
            "rank": 1,
            "why": f"{why}; domain pack recommends this safe executor for missing evidence outputs",
            "expected_evidence_gain": "create a ToolRunRecord and linked EvidenceRecord for missing required outputs",
            "executor_id": recommendation["executor_id"],
            "recipe_id": recommendation["recipe_id"],
            "pack_id": recommendation["pack_id"],
            "domain": recommendation["domain"],
            "supports_outputs": recommendation.get("supports_outputs", []),
            "satisfies_missing_outputs": supported,
            "evidence_type": recommendation.get("evidence_type", "tool_run"),
            "required_context_refs": recommendation.get("required_context_refs", []),
            "use_when": recommendation.get("use_when", ""),
            "input_schema": executor.get("input_schema", {}),
        }
    return None


def _knowledge_connector_action(
    connectors: list[dict],
    *,
    why: str,
) -> dict[str, Any] | None:
    if not connectors:
        return None
    return {
        "action": "consult_knowledge_connector",
        "rank": 1,
        "why": f"{why}; literature or note context is needed before treating retrieved context as evidence",
        "expected_evidence_gain": "retrieve orientation context while recording source_refs and reference_location_records in typed kernel records",
        "connector_ids": [connector["connector_id"] for connector in connectors],
        "backend_required": any(connector.get("is_required", False) for connector in connectors),
        "retrieval_targets": _dedupe(_flatten(connector.get("expected_retrieval_targets", []) for connector in connectors)),
        "location_ref_targets": _dedupe(_flatten(connector.get("location_ref_targets", []) for connector in connectors)),
        "required_kernel_followup_records": _dedupe(
            _flatten(connector.get("required_kernel_followup_records", []) for connector in connectors)
        ),
    }


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


def _flatten(groups) -> list[str]:
    values: list[str] = []
    for group in groups:
        values.extend(group)
    return values


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
