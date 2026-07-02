"""Execution brief construction for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.domain_packs import domain_pack_brief_payload, suggest_domain_packs, suggest_tool_executors_for_claim
from brain.v5.evidence import list_evidence_for_claim, required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.interaction import prioritize_questions, resolve_interaction_profile
from brain.v5.knowledge_connectors import suggest_knowledge_connectors_for_claim
from brain.v5.lane_exemplars import load_lane_exemplars
from brain.v5.models import ClaimRecord, ClaimStatusRecord, CodeStateRecord, ProofObligationRecord, ToolRunRecord
from brain.v5.memory import list_memory_entries_for_claim, memory_entry_brief_payload
from brain.v5.operator_checkpoint import load_operator_checkpoint
from brain.v5.policy import evaluate_policy
from brain.v5.question_engine import generate_questions
from brain.v5.physics_objects import list_object_relations_for_claim, object_relation_brief_payload
from brain.v5.references import list_reference_locations_for_claim, reference_location_brief_payload
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.research_state import list_proof_obligations_for_claim
from brain.v5.research_intent import load_innovation_direction, load_research_intent_gate
from brain.v5.output_stability import load_final_output_profile
from brain.v5.risk import action_budget_for_level, assess_claim_risk
from brain.v5.run_iterations import load_run_iterations
from brain.v5.store import list_records, list_valid_records
from brain.v5.strategy_memory import load_strategy_memory
from brain.v5.workspace import get_claim


def build_execution_brief(ws, session_id: str) -> dict[str, Any]:
    """Build the state packet an agent should see before acting."""

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    claim: ClaimRecord | None = None
    flow = None
    risk = None
    questions = []
    evidence_records = []
    domain_packs = []
    recommended_tool_executors = []
    knowledge_connectors = []
    reference_locations = []
    operating_notes = []
    object_relations = []
    memory_entries = []
    proof_obligations = []
    claim_status_records = []
    research_intent_gate = load_research_intent_gate(ws, session.topic_id)
    innovation_direction = load_innovation_direction(ws, session.topic_id)
    final_output_profile = load_final_output_profile(ws, session.topic_id)
    operator_checkpoint = load_operator_checkpoint(ws, session.topic_id)
    strategy_memory = load_strategy_memory(ws, session.topic_id)
    run_iterations = load_run_iterations(ws, session.topic_id)
    lane_exemplars = load_lane_exemplars(ws, session.topic_id)

    if session.active_claim:
        claim = get_claim(ws, session.active_claim)
        risk = assess_claim_risk(claim, code_states=_linked_code_states(ws, claim.claim_id))
        flow = resolve_flow_profile(claim, assessment=risk)
        raw_object_relations = list_object_relations_for_claim(ws, claim.claim_id)
        object_relations = [
            object_relation_brief_payload(relation)
            for relation in raw_object_relations
        ]
        questions = generate_questions(claim, flow, object_relations=object_relations)
        evidence_records = list_evidence_for_claim(ws, claim.claim_id)
        proof_obligations = list_proof_obligations_for_claim(ws, claim.claim_id)
        claim_status_records = _claim_statuses_for_claim(ws, claim.claim_id)
        domain_packs = [domain_pack_brief_payload(pack) for pack in suggest_domain_packs(claim)]
        recommended_tool_executors = suggest_tool_executors_for_claim(claim)
        knowledge_connectors = suggest_knowledge_connectors_for_claim(claim)
        raw_reference_locations = list_reference_locations_for_claim(ws, claim.claim_id)
        reference_locations = [
            reference_location_brief_payload(location)
            for location in raw_reference_locations
        ]
        operating_notes = [
            _operating_note_payload(location)
            for location in raw_reference_locations
            if _is_operating_note(location)
        ]
        memory_entries = [
            memory_entry_brief_payload(
                entry,
                evidence_records=evidence_records,
                tool_run_records=_tool_runs_for_claim(ws, claim.claim_id),
            )
            for entry in list_memory_entries_for_claim(ws, claim.claim_id)
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

    vnext_forbidden = []
    if research_intent_gate.get("present") and not research_intent_gate.get("execution_ready"):
        vnext_forbidden.append("vnext:execute_without_research_intent_approval")
        next_action_candidates.insert(
            0,
            {
                "action": "answer_research_intent_clarification",
                "rank": 1,
                "why": "vNext research-intent gate is not approved for execution",
                "expected_evidence_gain": "materialize novelty target, non-goals, first validation route, and evidence bar before deeper work",
                "clarification_questions": research_intent_gate.get("clarification_questions", []),
            },
        )
    if operator_checkpoint.get("active"):
        vnext_forbidden.append("vnext:continue_without_answering_operator_checkpoint")
        next_action_candidates.insert(
            0,
            {
                "action": "answer_operator_checkpoint",
                "rank": 1,
                "why": "vNext operator checkpoint is active",
                "expected_evidence_gain": "record the human route choice before continuing or branching",
                "checkpoint_id": operator_checkpoint.get("checkpoint_id", ""),
                "question": operator_checkpoint.get("question", ""),
                "options": operator_checkpoint.get("options", []),
            },
        )

    return {
        "session": asdict(session),
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "recovered_focus": {
            "requested_session_id": recovered.requested_session_id,
            "recovery_selection_source": recovered.recovery_selection_source,
            "session_id": session.session_id,
            "topic_id": session.topic_id,
            "context_id": session.context_id,
            "active_claim": session.active_claim,
            "active_route": session.active_route or None,
            "active_cycle": session.active_cycle or None,
            "claim_statement": claim.statement if claim else "",
            "confidence_state": claim.confidence_state if claim else "",
            "evidence_profile": claim.evidence_profile if claim else "",
        },
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
            "domain_packs": domain_packs,
            "recommended_tool_executors": recommended_tool_executors,
            "knowledge_connectors": knowledge_connectors,
            "reference_locations": reference_locations,
            "operating_notes": operating_notes,
            "research_intent_gate": research_intent_gate,
            "innovation_direction": innovation_direction,
            "final_output_profile": final_output_profile,
            "operator_checkpoint": operator_checkpoint,
            "strategy_memory": strategy_memory,
            "run_iterations": run_iterations,
            "lane_exemplars": lane_exemplars,
            "object_relations": object_relations,
            "memory_entries": memory_entries,
            "proof_obligations": [
                _proof_obligation_brief_payload(record)
                for record in proof_obligations
            ],
        },
        "research_gates": _research_gate_payload(
            claim_status_records=claim_status_records,
            proof_obligations=proof_obligations,
            human_checkpoint_needed=action_budget.requires_human_checkpoint or bool(operator_checkpoint.get("active")),
        ),
        "claim_relation_map": build_claim_relation_map(ws, session_id),
        "mandatory_reflection": mandatory_reflection,
        "next_action_candidates": next_action_candidates,
        "forbidden_now": _forbidden_actions(flow.profile if flow else "guided") + policy_forbidden + vnext_forbidden,
        "human_checkpoint": {
            "needed": action_budget.requires_human_checkpoint or bool(operator_checkpoint.get("active")),
            "reason": _human_checkpoint_reason(action_budget.requires_human_checkpoint, operator_checkpoint),
            "semantics": (
                "Immediate runtime checkpoint: if true, the agent must stop and get an explicit human "
                "decision before continuing. This is distinct from record-level human_gate_required flags."
            ),
        },
    }


def _human_checkpoint_reason(risk_requires_checkpoint: bool, operator_checkpoint: dict[str, Any]) -> str | None:
    if operator_checkpoint.get("active"):
        question = str(operator_checkpoint.get("question") or "")
        return f"active operator checkpoint: {question}" if question else "active operator checkpoint"
    if risk_requires_checkpoint:
        return "risk budget requires human checkpoint"
    return None


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
    states = list_valid_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [state for state in states if _record_links_to_claim(state.linked_records, claim_id)]


def _tool_runs_for_claim(ws, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]


def _claim_statuses_for_claim(ws, claim_id: str) -> list[ClaimStatusRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
        if record.claim_id == claim_id
    ]


def _proof_obligation_brief_payload(record: ProofObligationRecord) -> dict[str, Any]:
    return {
        "obligation_id": record.obligation_id,
        "claim_id": record.claim_id,
        "statement": record.statement,
        "obligation_type": record.obligation_type,
        "status": record.status,
        "maturity_level": record.maturity_level,
        "next_action": record.next_action,
        "required_evidence": list(record.required_evidence),
        "proof_strategy": list(record.proof_strategy),
        "failure_modes": list(record.failure_modes),
        "evidence_refs": list(record.evidence_refs),
        "artifact_ids": list(record.artifact_ids),
        "human_gate_required": bool(record.human_gate_required),
        "can_update_claim_trust": bool(record.can_update_claim_trust),
    }


def _research_gate_payload(
    *,
    claim_status_records: list[ClaimStatusRecord],
    proof_obligations: list[ProofObligationRecord],
    human_checkpoint_needed: bool,
) -> dict[str, Any]:
    gated_statuses = [record for record in claim_status_records if record.human_gate_required]
    gated_obligations = [record for record in proof_obligations if record.human_gate_required]
    open_obligations = [
        record
        for record in proof_obligations
        if str(record.status).lower() not in {"closed", "resolved", "passed", "complete"}
    ]
    return {
        "record_level_human_gate_required": bool(gated_statuses or gated_obligations),
        "record_level_human_gate_count": len(gated_statuses) + len(gated_obligations),
        "open_proof_obligation_count": len(open_obligations),
        "open_proof_obligation_ids": [record.obligation_id for record in open_obligations],
        "human_checkpoint_needed": bool(human_checkpoint_needed),
        "semantics": {
            "human_gate_required": (
                "Record-level provenance/trust guard: this record still needs explicit human review "
                "before it can support trust promotion or L2 memory. It does not by itself pause the runtime."
            ),
            "human_checkpoint_needed": (
                "Immediate runtime/operator checkpoint: when true, stop and ask the human before continuing."
            ),
        },
    }


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


def _is_operating_note(location) -> bool:
    if location.orientation_only is not True:
        return False
    linked_records = location.linked_records or {}
    role = str(linked_records.get("artifact_role", "")).lower()
    kind = str(location.location_type).lower()
    status = str(location.status).lower()
    return (
        role in {"agent_operating_strategy", "workflow_runbook", "lane_policy"}
        or kind in {"strategy_note", "workflow_runbook", "lane_policy"}
        or status in {"active_strategy_note", "active_runbook"}
    )


def _operating_note_payload(location) -> dict[str, Any]:
    metadata = location.metadata or {}
    linked_records = location.linked_records or {}
    return {
        "location_id": location.location_id,
        "label": location.label,
        "uri": location.uri,
        "summary": location.summary,
        "status": location.status,
        "location_type": location.location_type,
        "artifact_role": linked_records.get("artifact_role", ""),
        "lane_policy": metadata.get("lane_policy", ""),
        "final_lane_gate": metadata.get("final_lane_gate", ""),
        "diagnostic_lane_labels": metadata.get("diagnostic_lane_labels", []),
        "forbidden_root": metadata.get("forbidden_root", ""),
        "clean_root": metadata.get("clean_mgo_root", metadata.get("clean_root", "")),
        "orientation_only": True,
    }


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
