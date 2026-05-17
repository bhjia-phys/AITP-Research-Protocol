"""Trust-card resolution for reusable AITP v5 workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.models import ClaimRecord, CodeStateRecord


@dataclass
class TrustCard:
    card_id: str
    recipe_id: str
    title: str
    applicability_terms: list[str] = field(default_factory=list)
    required_evidence_profile: str = ""
    allowed_repo_ids: list[str] = field(default_factory=list)
    allowed_upstream_commits: list[str] = field(default_factory=list)
    benchmark_refs: list[str] = field(default_factory=list)
    invalidation_triggers: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    required_clean_code_state: bool = True
    risk_reduction: int = 3


@dataclass
class TrustResolution:
    card_id: str
    recipe_id: str
    applies: bool
    risk_reduction: int = 0
    reasons: list[str] = field(default_factory=list)
    invalidation_reasons: list[str] = field(default_factory=list)
    benchmark_refs: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)


def resolve_trust_cards(
    claim: ClaimRecord,
    trust_cards: list[TrustCard],
    *,
    code_states: list[CodeStateRecord] | None = None,
) -> list[TrustResolution]:
    """Resolve which trust cards apply to the current claim and code state."""

    states = code_states or []
    text = _claim_text(claim)
    resolutions: list[TrustResolution] = []

    for card in trust_cards:
        if card.recipe_id and card.recipe_id != claim.recipe_id:
            continue

        reasons: list[str] = []
        invalidations: list[str] = []
        required_actions: list[str] = []

        if card.required_evidence_profile and card.required_evidence_profile != claim.evidence_profile:
            invalidations.append(
                f"requires evidence_profile={card.required_evidence_profile}, got {claim.evidence_profile}"
            )

        missing_terms = [term for term in card.applicability_terms if term.lower() not in text]
        if missing_terms:
            invalidations.append(f"missing applicability terms: {', '.join(missing_terms)}")
        elif card.applicability_terms:
            reasons.append("claim text matches applicability terms")

        triggered = [trigger for trigger in card.invalidation_triggers if trigger.lower() in text]
        if triggered:
            invalidations.append(f"invalidation trigger present: {', '.join(triggered)}")
            required_actions.append("rerun validation outside this trust card")

        if card.required_clean_code_state and any(state.dirty for state in states):
            dirty_ids = ", ".join(state.code_state_id for state in states if state.dirty)
            invalidations.append(f"dirty code state: {dirty_ids}")
            required_actions.append("record or clean patch state")

        if card.allowed_repo_ids:
            if not states:
                invalidations.append("missing code state for repo-scoped trust card")
                required_actions.append("record code state")
            else:
                unexpected = [state.repo_id for state in states if state.repo_id not in card.allowed_repo_ids]
                if unexpected:
                    invalidations.append(f"repo outside trust scope: {', '.join(sorted(set(unexpected)))}")

        if card.allowed_upstream_commits:
            if not states:
                invalidations.append("missing code state for commit-scoped trust card")
                required_actions.append("record code state")
            elif not any(state.upstream_commit in card.allowed_upstream_commits for state in states):
                invalidations.append("upstream commit outside trust scope")
                required_actions.append("compare against trusted upstream snapshot")
            else:
                reasons.append("code state matches trusted upstream commit")

        applies = not invalidations
        if applies:
            reasons.append("trust card applies inside its recorded scope")

        resolutions.append(
            TrustResolution(
                card_id=card.card_id,
                recipe_id=card.recipe_id,
                applies=applies,
                risk_reduction=card.risk_reduction if applies else 0,
                reasons=reasons,
                invalidation_reasons=invalidations,
                benchmark_refs=card.benchmark_refs,
                required_actions=_dedupe(required_actions),
            )
        )

    return resolutions


def _claim_text(claim: ClaimRecord) -> str:
    return " ".join(
        [
            claim.statement,
            claim.evidence_profile,
            claim.confidence_state,
            claim.active_uncertainty,
            claim.scope,
            claim.non_claims,
            claim.strongest_failure_mode,
            claim.recipe_id,
        ]
    ).lower()


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
