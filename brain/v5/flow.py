"""Flow profile resolution for AITP v5."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.models import ClaimRecord, FlowDecision
from brain.v5.risk import RiskAssessment, assess_claim_risk


def resolve_flow_profile(claim: ClaimRecord, *, assessment: RiskAssessment | None = None) -> FlowDecision:
    """Choose protocol weight for a claim-local action."""

    risk = assessment or assess_claim_risk(claim)
    return FlowDecision(
        profile=risk.level,
        reason=risk.summary,
        escalation_triggers=[signal.kind for signal in risk.signals],
        risk_level=risk.level,
        risk_score=risk.score,
        action_budget=asdict(risk.action_budget) if risk.action_budget else {},
    )
