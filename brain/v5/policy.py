"""Policy-as-code guards for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.evolution import EvolutionProposal
from brain.v5.models import ClaimRecord, CodeStateRecord
from brain.v5.risk import RiskAssessment


_TRUST_CHANGING_ACTIONS = {
    "record_evidence",
    "record_tool_run",
    "execute_tool",
    "ingest_subagent_result",
    "change_claim_confidence",
    "create_validation_contract",
    "create_promotion_packet",
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
    evidence_refs: list[str] | None = None,
    risk_level: str = "",
    risk_assessment: RiskAssessment | None = None,
    evolution_proposal: EvolutionProposal | None = None,
    context: dict[str, Any] | None = None,
) -> PolicyDecision:
    """Evaluate non-negotiable v5 harness policies for an action."""

    states = code_states or []
    refs = evidence_refs or []
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
