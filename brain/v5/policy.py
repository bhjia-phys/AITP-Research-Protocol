"""Policy-as-code guards for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.evolution import EvolutionProposal
from brain.v5.models import (
    ClaimRecord,
    CodeStateRecord,
    EvidenceRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.risk import RiskAssessment


_TRUST_CHANGING_ACTIONS = {
    "record_code_state",
    "record_evidence",
    "record_tool_run",
    "execute_tool",
    "register_tool_recipe",
    "record_reference_location",
    "record_physics_object",
    "record_object_relation",
    "record_sensemaking_report",
    "ingest_subagent_result",
    "change_claim_confidence",
    "create_validation_contract",
    "record_validation_result",
    "request_human_checkpoint",
    "decide_human_checkpoint",
    "create_promotion_packet",
    "apply_promotion_packet",
    "validate_claim",
    "promote_to_l2",
}
_SUMMARY_SOURCE_KINDS = {
    "derived_summary",
    "summary_orientation",
    "task_plan",
    "findings",
    "progress",
}


@dataclass
class PolicyReason:
    policy_id: str
    message: str
    severity: str = "block"


@dataclass
class PolicyDecision:
    allowed: bool
    action: str
    reasons: list[PolicyReason] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)

    def add_block(self, policy_id: str, message: str, required_action: str, *, severity: str = "block") -> None:
        self.allowed = False
        self.reasons.append(PolicyReason(policy_id=policy_id, message=message, severity=severity))
        if required_action not in self.required_actions:
            self.required_actions.append(required_action)


def evaluate_policy(
    *,
    action: str,
    claim: ClaimRecord | None = None,
    code_states: list[CodeStateRecord] | None = None,
    evidence_records: list[EvidenceRecord] | None = None,
    evidence_refs: list[str] | None = None,
    validation_contracts: list[ValidationContractRecord] | None = None,
    validation_results: list[ValidationResultRecord] | None = None,
    risk_level: str = "",
    risk_assessment: RiskAssessment | None = None,
    evolution_proposal: EvolutionProposal | None = None,
    context: dict[str, Any] | None = None,
) -> PolicyDecision:
    """Evaluate non-negotiable v5 harness policies for an action."""

    states = code_states or []
    records = evidence_records or []
    refs = evidence_refs or []
    contracts = validation_contracts or []
    results = validation_results or []
    decision = PolicyDecision(allowed=True, action=action)
    ctx = context or {}

    if action == "continue_fluid_work" and risk_level == "fluid":
        return decision

    _guard_summary_surface_cannot_drive_trust_update(decision, action, ctx)
    _guard_adversarial_trust_change_requires_checkpoint(decision, action, risk_level, ctx)

    if action in {"validate_claim", "promote_to_l2"}:
        _guard_code_method_requires_code_state(decision, claim, states)

    if action in {"create_promotion_packet", "promote_to_l2"}:
        _guard_l2_promotion_requires_evidence(decision, refs)
        _guard_high_risk_promotion_requires_validation_result(decision, risk_level, records, results)

    if action in {"execute_tool", "record_tool_run"}:
        _guard_high_risk_tool_requires_validation_contract(decision, action, risk_level, contracts, ctx)

    if action == "record_evidence":
        _guard_high_risk_tool_evidence_requires_validation_result(decision, risk_level, results, ctx)

    if action == "reduce_friction_with_trust_card":
        _guard_invalidated_trust_card_cannot_reduce_friction(decision, risk_assessment)

    if action == "apply_harness_patch":
        _guard_harness_patch_requires_test(decision, evolution_proposal)
        _guard_core_protocol_patch_requires_review(decision, evolution_proposal)

    return decision


def _guard_summary_surface_cannot_drive_trust_update(
    decision: PolicyDecision,
    action: str,
    context: dict[str, Any],
) -> None:
    if action not in _TRUST_CHANGING_ACTIONS:
        return
    source_kind = str(context.get("source_kind", "")).strip().lower()
    orientation_only = context.get("orientation_only")
    if source_kind not in _SUMMARY_SOURCE_KINDS and orientation_only is not True:
        return
    decision.add_block(
        "no_summary_surface_as_truth_source",
        "derived summary surfaces are orientation only and cannot justify trust-changing actions",
        "query_execution_brief_or_typed_record",
        severity="hard_block",
    )


def _guard_adversarial_trust_change_requires_checkpoint(
    decision: PolicyDecision,
    action: str,
    risk_level: str,
    context: dict[str, Any],
) -> None:
    if risk_level != "adversarial" or action not in _TRUST_CHANGING_ACTIONS:
        return
    if context.get("human_checkpoint_approved") is True:
        return
    decision.add_block(
        "adversarial_trust_change_requires_human_checkpoint",
        "adversarial-risk trust-changing actions require an approved human checkpoint",
        "request_human_checkpoint",
        severity="hard_block",
    )


def _guard_code_method_requires_code_state(
    decision: PolicyDecision,
    claim: ClaimRecord | None,
    code_states: list[CodeStateRecord],
) -> None:
    if not claim or claim.evidence_profile != "code_method":
        return
    if code_states:
        return
    decision.add_block(
        "no_code_method_validation_without_code_state",
        "code_method validation requires at least one linked code state",
        "record_code_state",
    )


def _guard_l2_promotion_requires_evidence(decision: PolicyDecision, evidence_refs: list[str]) -> None:
    if evidence_refs:
        return
    decision.add_block(
        "no_l2_promotion_without_evidence_ref",
        "L2 promotion requires at least one evidence reference",
        "attach_evidence_ref",
    )


def _guard_high_risk_promotion_requires_validation_result(
    decision: PolicyDecision,
    risk_level: str,
    evidence_records: list[EvidenceRecord],
    validation_results: list[ValidationResultRecord],
) -> None:
    if risk_level not in {"rigorous", "adversarial"}:
        return
    tool_run_ids = {
        run_id
        for evidence in evidence_records
        for run_id in getattr(evidence, "tool_run_ids", [])
        if run_id
    }
    if not tool_run_ids:
        return
    passed_tool_runs = {
        result.tool_run_id
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    }
    if not passed_tool_runs:
        decision.add_block(
            "high_risk_promotion_requires_validation_result",
            "rigorous or adversarial promotion using tool-derived evidence requires passed validation-result refs",
            "attach_passed_validation_result",
            severity="hard_block",
        )
        return
    if not tool_run_ids.issubset(passed_tool_runs):
        decision.add_block(
            "high_risk_promotion_validation_result_mismatch",
            "provided validation results do not pass every tool-derived evidence run in the promotion packet",
            "attach_matching_validation_result",
            severity="hard_block",
        )


def _guard_high_risk_tool_requires_validation_contract(
    decision: PolicyDecision,
    action: str,
    risk_level: str,
    validation_contracts: list[ValidationContractRecord],
    context: dict[str, Any],
) -> None:
    if risk_level not in {"rigorous", "adversarial"}:
        return
    if not validation_contracts:
        decision.add_block(
            "high_risk_tool_execution_requires_validation_contract",
            "rigorous or adversarial tool execution requires an explicit typed validation contract",
            "create_validation_contract",
            severity="hard_block",
        )
        return
    recipe_id = str(context.get("recipe_id", "")).strip()
    executor_id = str(context.get("executor_id", "")).strip()
    if action == "execute_tool" and (not recipe_id or not executor_id):
        decision.add_block(
            "high_risk_tool_execution_requires_tool_identity",
            "rigorous or adversarial tool execution must name the tool recipe and executor before a validation contract can authorize it",
            "include_tool_recipe_and_executor",
            severity="hard_block",
        )
        return
    if action == "record_tool_run" and not recipe_id:
        decision.add_block(
            "high_risk_tool_execution_requires_tool_identity",
            "rigorous or adversarial tool-run records must name the tool recipe before a validation contract can authorize them",
            "include_tool_recipe",
            severity="hard_block",
        )
        return
    if _validation_contract_matches_tool(action, validation_contracts, recipe_id, executor_id):
        return
    decision.add_block(
        "high_risk_tool_validation_contract_mismatch",
        "provided validation contracts do not bind the current high-risk tool recipe and executor",
        "bind_validation_contract_to_tool",
        severity="hard_block",
    )


def _validation_contract_matches_tool(
    action: str,
    contracts: list[ValidationContractRecord],
    recipe_id: str,
    executor_id: str,
) -> bool:
    for contract in contracts:
        recipe_ids = set(getattr(contract, "tool_recipe_ids", []))
        executor_ids = set(getattr(contract, "executor_ids", []))
        if action == "record_tool_run" and recipe_id in recipe_ids:
            return True
        if action == "execute_tool" and recipe_id in recipe_ids and executor_id in executor_ids:
            return True
    return False


def _guard_high_risk_tool_evidence_requires_validation_result(
    decision: PolicyDecision,
    risk_level: str,
    validation_results: list[ValidationResultRecord],
    context: dict[str, Any],
) -> None:
    if risk_level not in {"rigorous", "adversarial"}:
        return
    tool_run_ids = set(_context_list(context.get("tool_run_ids")))
    if not tool_run_ids:
        return
    passed_results = [
        result
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    ]
    if not passed_results:
        decision.add_block(
            "high_risk_tool_evidence_requires_validation_result",
            "rigorous or adversarial tool-derived evidence requires a passed validation result for the linked tool run",
            "attach_passed_validation_result",
            severity="hard_block",
        )
        return
    passed_tool_runs = {result.tool_run_id for result in passed_results}
    if not tool_run_ids.issubset(passed_tool_runs):
        decision.add_block(
            "high_risk_tool_evidence_validation_result_mismatch",
            "provided validation results do not pass every linked high-risk tool run",
            "attach_matching_validation_result",
            severity="hard_block",
        )


def _context_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []


def _guard_invalidated_trust_card_cannot_reduce_friction(
    decision: PolicyDecision,
    assessment: RiskAssessment | None,
) -> None:
    if not assessment:
        return
    has_invalidated_card = any(signal.kind == "trust_card_invalidated" for signal in assessment.signals)
    has_trust_card_reduction = any(reduction.startswith("trust_card:") for reduction in assessment.trust_reductions)
    if not (has_invalidated_card and has_trust_card_reduction):
        return
    decision.add_block(
        "no_trust_reduction_when_card_invalidated",
        "trust card friction reduction is forbidden when the same assessment has trust_card_invalidated",
        "remove_invalid_trust_reduction",
    )


def _guard_harness_patch_requires_test(
    decision: PolicyDecision,
    proposal: EvolutionProposal | None,
) -> None:
    if not proposal or not proposal.requires_regression_test:
        return
    if proposal.required_tests:
        return
    decision.add_block(
        "no_harness_patch_without_test",
        "harness patches require at least one regression test reference",
        "add_regression_test",
    )


def _guard_core_protocol_patch_requires_review(
    decision: PolicyDecision,
    proposal: EvolutionProposal | None,
) -> None:
    if not proposal or not proposal.requires_human_review:
        return
    decision.add_block(
        "no_core_protocol_patch_without_review",
        "core protocol evolution requires human review before application",
        "request_human_review",
    )
