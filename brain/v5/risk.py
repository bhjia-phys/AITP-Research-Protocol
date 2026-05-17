"""Risk-triggered protocol weight for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.models import ClaimRecord, CodeStateRecord


@dataclass
class RiskSignal:
    kind: str
    severity: int
    reason: str
    evidence_ref: str
    suggested_action: str


@dataclass
class ActionBudget:
    level: str
    max_questions: int
    required_outputs: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    requires_human_checkpoint: bool = False


@dataclass
class RiskAssessment:
    level: str
    score: int
    signals: list[RiskSignal] = field(default_factory=list)
    trust_reductions: list[str] = field(default_factory=list)
    action_budget: ActionBudget | None = None
    human_checkpoint_needed: bool = False
    summary: str = ""


_CLAIM_IMPORTANCE_TERMS = (
    "publish",
    "paper",
    "promote",
    "promotion",
    "prove",
    "proof",
    "trusted memory",
    "l2",
)

_CONFLICT_TERMS = (
    "conflict",
    "conflicts",
    "contradiction",
    "contradicts",
    "inconsistent",
    "disagree",
)

_COMPUTE_COST_TERMS = (
    "expensive",
    "hpc",
    "long run",
    "qsgw",
    "gw rerun",
)

_FORMULA_CODE_TERMS = (
    "kernel",
    "self-energy",
    "formula",
    "implementation",
    "patch",
    "modified",
    "code",
)

_NUMERICAL_SENSITIVITY_TERMS = (
    "finite-size",
    "finite size",
    "cutoff",
    "basis",
    "convergence",
    "k mesh",
    "k-mesh",
    "frequency grid",
)

_PHYSICS_ANOMALY_TERMS = (
    "artifact",
    "mimic",
    "anomaly",
    "wrong",
    "symmetry breaking",
    "limit mismatch",
    "dimension mismatch",
)

_ROUTINE_TRUST_TERMS = (
    "routine",
    "rerun",
    "benchmark",
    "trusted",
    "standard",
)


def assess_claim_risk(
    claim: ClaimRecord,
    *,
    code_states: list[CodeStateRecord] | None = None,
) -> RiskAssessment:
    """Assess how much protocol friction a claim-local action needs."""

    states = code_states or []
    text = _claim_text(claim)
    routine_trusted = bool(claim.recipe_id and _contains_any(text, _ROUTINE_TRUST_TERMS))
    signals: list[RiskSignal] = []
    trust_reductions: list[str] = []

    def add(kind: str, severity: int, reason: str, evidence_ref: str, action: str) -> None:
        signals.append(
            RiskSignal(
                kind=kind,
                severity=severity,
                reason=reason,
                evidence_ref=evidence_ref,
                suggested_action=action,
            )
        )

    if _contains_any(text, _CLAIM_IMPORTANCE_TERMS):
        add(
            "claim_importance",
            3,
            "The claim is being positioned for publication, promotion, proof, or long-term memory.",
            f"claim:{claim.claim_id}:active_uncertainty",
            "freeze the claim scope before accepting new evidence",
        )

    if _contains_any(text, _CONFLICT_TERMS):
        add(
            "literature_conflict",
            4,
            "The active uncertainty says the result conflicts with an external or benchmark reference.",
            f"claim:{claim.claim_id}:active_uncertainty",
            "identify the reference and design the cheapest discriminating check",
        )

    if _contains_any(text, _COMPUTE_COST_TERMS):
        add(
            "compute_cost",
            2,
            "Continuing may require expensive or hard-to-repeat computation.",
            f"claim:{claim.claim_id}:active_uncertainty",
            "ask whether the expected information gain justifies the run",
        )

    if claim.confidence_state in {"hypothesis", "coherent", "unverified"}:
        add(
            "evidence_gap",
            2,
            "The claim confidence still marks it as a live hypothesis or unverified statement.",
            f"claim:{claim.claim_id}:confidence_state",
            "keep the statement local until a targeted check changes the evidence profile",
        )

    if claim.evidence_profile == "toy_numeric" or _contains_any(text, _NUMERICAL_SENSITIVITY_TERMS):
        add(
            "numerical_sensitivity",
            2,
            "The evidence can be distorted by finite-size, cutoff, basis, or convergence effects.",
            f"claim:{claim.claim_id}:evidence_profile",
            "choose one high-information finite-size, cutoff, or comparator check",
        )

    if _contains_any(text, _PHYSICS_ANOMALY_TERMS):
        add(
            "physics_anomaly",
            3,
            "The uncertainty mentions a possible physical artifact or sanity-check failure.",
            f"claim:{claim.claim_id}:active_uncertainty",
            "write the failure mechanism and a minimal diagnostic before increasing confidence",
        )

    if claim.evidence_profile == "code_method" and _contains_any(_formula_code_text(claim), _FORMULA_CODE_TERMS):
        add(
            "formula_to_code_risk",
            3,
            "The claim depends on translating a physical formula or kernel into executable code.",
            f"claim:{claim.claim_id}:statement",
            "trace the formula-code map and name a benchmark invariant",
        )

    if any(state.dirty for state in states):
        dirty_ids = ", ".join(state.code_state_id for state in states if state.dirty)
        add(
            "reproducibility_risk",
            3,
            "At least one linked code state is dirty, so the result is not reproducible from a commit alone.",
            f"code_state:{dirty_ids}",
            "record or clean the patch state before treating the output as evidence",
        )
    elif claim.evidence_profile == "code_method" and not states and not routine_trusted:
        add(
            "reproducibility_risk",
            2,
            "The claim uses code-method evidence but no code state was provided to the risk engine.",
            f"claim:{claim.claim_id}:evidence_profile",
            "record repo, worktree, commit, patch, build, and runtime configuration",
        )

    score = sum(signal.severity for signal in signals)

    if routine_trusted and not any(state.dirty for state in states):
        trust_reductions.append("trusted_recipe_covers_routine_clean_workflow")
        score = max(0, score - 2)

    level = _level_for_score(score)
    action_budget = action_budget_for_level(level)
    return RiskAssessment(
        level=level,
        score=score,
        signals=signals,
        trust_reductions=trust_reductions,
        action_budget=action_budget,
        human_checkpoint_needed=action_budget.requires_human_checkpoint,
        summary=_summary(level, score, signals, trust_reductions),
    )


def action_budget_for_level(level: str) -> ActionBudget:
    """Return the bounded action budget for a risk level."""

    if level == "fluid":
        return ActionBudget(
            level=level,
            max_questions=1,
            required_outputs=["session_trace"],
            allowed_actions=["continue_fluid_work", "run_trusted_recipe", "capture_session_trace"],
        )
    if level == "guided":
        return ActionBudget(
            level=level,
            max_questions=3,
            required_outputs=["scoped_claim", "evidence_or_provenance"],
            allowed_actions=["answer_dynamic_physics_questions", "select_high_information_check"],
        )
    if level == "rigorous":
        return ActionBudget(
            level=level,
            max_questions=3,
            required_outputs=["evidence_or_provenance", "failure_mode", "minimal_check"],
            allowed_actions=["record_evidence", "run_minimal_diagnostic", "audit_failure_mode"],
        )
    if level == "adversarial":
        return ActionBudget(
            level=level,
            max_questions=3,
            required_outputs=[
                "counterargument_or_falsification_path",
                "evidence_or_provenance",
                "human_checkpoint_decision",
            ],
            allowed_actions=["design_falsification_check", "request_critic", "request_reproducer"],
            requires_human_checkpoint=True,
        )
    raise ValueError(f"unknown risk level: {level}")


def _level_for_score(score: int) -> str:
    if score <= 1:
        return "fluid"
    if score <= 4:
        return "guided"
    if score <= 8:
        return "rigorous"
    return "adversarial"


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


def _formula_code_text(claim: ClaimRecord) -> str:
    return " ".join(
        [
            claim.statement,
            claim.active_uncertainty,
            claim.scope,
            claim.strongest_failure_mode,
        ]
    ).lower()


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _summary(
    level: str,
    score: int,
    signals: list[RiskSignal],
    trust_reductions: list[str],
) -> str:
    if not signals and trust_reductions:
        return f"{level} protocol: trusted routine workflow with no active risk signal"
    if not signals:
        return f"{level} protocol: no specific risk signal detected"
    kinds = ", ".join(signal.kind for signal in signals)
    return f"{level} protocol: risk score {score} from {kinds}"
