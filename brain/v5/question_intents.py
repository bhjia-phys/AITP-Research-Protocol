"""Deterministic physics question intents for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.ids import prefixed_id
from brain.v5.interaction import InteractionPlan
from brain.v5.models import ClaimRecord, FlowDecision


@dataclass
class QuestionIntent:
    intent_id: str
    intent_type: str
    target_claim: str
    scene: str
    kernel_prompt: str
    rationale: str
    expected_answer_shape: str
    suggested_actions: list[str] = field(default_factory=list)
    target_objects: list[str] = field(default_factory=list)
    target_relations: list[str] = field(default_factory=list)
    target_uncertainty: str = ""
    priority: int = 50
    expansion_boundary: str = (
        "LLM may rephrase the question, but must preserve intent_type, target objects, "
        "target relations, expected answer shape, and suggested actions."
    )


def generate_question_intents(
    claim: ClaimRecord,
    flow: FlowDecision,
    *,
    object_relations: list[str] | None = None,
    interaction: InteractionPlan | None = None,
) -> list[QuestionIntent]:
    """Generate deterministic question intents before any LLM phrasing layer."""

    relations = object_relations or []
    text = _claim_text(claim)
    objects = _target_objects(text)
    intents: list[QuestionIntent] = []

    def add(
        intent_type: str,
        prompt: str,
        rationale: str,
        expected: str,
        actions: list[str],
        *,
        target_objects: list[str] | None = None,
        target_relations: list[str] | None = None,
        priority: int = 50,
    ) -> None:
        intent_id = prefixed_id("qintent", f"{claim.claim_id}:{intent_type}:{len(intents)}", max_slug=54)
        intents.append(
            QuestionIntent(
                intent_id=intent_id,
                intent_type=intent_type,
                target_claim=claim.claim_id,
                scene=flow.profile,
                kernel_prompt=prompt,
                rationale=rationale,
                expected_answer_shape=expected,
                suggested_actions=actions,
                target_objects=target_objects if target_objects is not None else objects,
                target_relations=target_relations if target_relations is not None else relations,
                target_uncertainty=claim.active_uncertainty,
                priority=priority,
            )
        )

    add(
        "claim_scope_check",
        f"What exactly must be true for this claim to hold: {claim.statement}",
        "Claim clarity prevents a broad statement from passing on narrow evidence.",
        "A scoped statement plus non-claims and assumptions.",
        ["narrow_claim", "record_non_claims"],
        priority=10,
    )

    if relations:
        relation_text = ", ".join(relations)
        add(
            "object_relation_check",
            f"Which object relation is load-bearing here, and how does it support the claim? Relations: {relation_text}",
            "The next physics step should inspect relations, not isolated objects.",
            "A relation-level explanation with the weakest edge identified.",
            ["update_relation_graph", "run_relation_check"],
            target_relations=relations,
            priority=20,
        )
    else:
        add(
            "object_relation_check",
            "Which physical objects and object relations would make this claim meaningful?",
            "A claim without object relations is hard to test or falsify.",
            "A list of objects and typed relations.",
            ["create_object_relation_map"],
            priority=20,
        )

    if _needs_failure_mode(claim, flow):
        add(
            "failure_mode_check",
            "If this claim is wrong, what is the most likely failure mechanism?",
            "Non-fluid physics work needs a failure hypothesis before evidence can change trust.",
            "A ranked failure mode with a minimal diagnostic.",
            ["record_failure_hypothesis", "design_minimal_diagnostic"],
            priority=30,
        )

    if relations and _relation_failure_modes_present(relations):
        relation_text = "; ".join(relations)
        add(
            "object_relation_failure_mode_check",
            f"Which recorded object-relation failure mode is most dangerous here: {relation_text}?",
            "Recorded object relations expose mechanisms and failure modes that should guide the next physics check.",
            "Name the relation, the failure mode, and the cheapest check.",
            ["record_evidence", "run_minimal_check", "revise_relation"],
            target_relations=relations,
            priority=25,
        )

    if claim.evidence_profile == "toy_numeric" or _contains_any(text, _FINITE_SIZE_TERMS):
        add(
            "finite_size_or_cutoff_check",
            "Which finite-size, cutoff, convergence, or comparator check would most reduce the active uncertainty?",
            "Toy numerics can look persuasive for the wrong reason.",
            "One cheap high-information numerical check.",
            ["run_toy_numeric_check", "compare_negative_control"],
            priority=35,
        )

    if claim.evidence_profile == "code_method":
        add(
            "formula_code_invariant_check",
            "Which formula-code map, code state, or invariant is most likely to control this result?",
            "Code-method evidence can fail through translation or version drift.",
            "A code object, formula object, and invariant to inspect.",
            ["trace_formula_code_map", "record_code_state"],
            priority=35,
        )
        add(
            "provenance_check",
            "Which repo, commit, patch, build config, and runtime state produced this result?",
            "Computational physics claims need reproducible code provenance.",
            "A linked code state with commit, dirty state, build config, and runtime environment.",
            ["record_code_state", "record_build_runtime"],
            priority=36,
        )

    if "benchmark" in text or "reproduce" in text or "reproduces" in text:
        add(
            "benchmark_consistency_check",
            "Which benchmark value, tolerance, and comparison protocol must this result reproduce?",
            "Benchmark agreement is only meaningful when the comparator and tolerance are explicit.",
            "Benchmark reference, tolerance, and pass/fail comparison rule.",
            ["record_benchmark_reference", "run_benchmark_comparison"],
            priority=37,
        )

    if _contains_any(text, _LIMIT_SYMMETRY_DIMENSION_TERMS):
        add(
            "limit_symmetry_dimension_check",
            "Does the expression or result pass its required limit, symmetry, and dimensional checks?",
            "Many formal and numerical mistakes show up first as sanity-check failures.",
            "A limit, symmetry, or dimensional consistency argument with a failure condition.",
            ["verify_limit_or_symmetry", "record_dimension_check"],
            priority=38,
        )

    if _contains_any(text, _CONFLICT_TERMS):
        add(
            "literature_conflict_check",
            "Which external claim or benchmark conflicts with this, and what discriminating check separates them?",
            "Contradictions should become explicit research objects rather than vague doubt.",
            "A cited conflicting claim plus the cheapest discriminating test.",
            ["record_conflict", "design_discriminating_check"],
            priority=39,
        )

    if interaction and interaction.profile.role == "teacher":
        add(
            "prerequisite_check",
            "Which definitions, examples, and prerequisite facts must be understood before judging this claim?",
            "Teacher mode should scaffold understanding without weakening evidence standards.",
            "Prerequisite list plus the first concept that blocks progress.",
            ["record_prerequisites", "explain_minimal_example"],
            priority=12,
        )
        add(
            "misconception_check",
            "What is the most tempting wrong interpretation of this claim?",
            "Learning mode should identify likely conceptual traps before calculation proceeds.",
            "One misconception, why it is tempting, and the diagnostic that rules it out.",
            ["record_misconception", "design_understanding_check"],
            priority=13,
        )

    return sorted(intents, key=lambda intent: (intent.priority, intent.intent_id))


_FINITE_SIZE_TERMS = (
    "finite-size",
    "finite size",
    "cutoff",
    "convergence",
    "basis",
    "k mesh",
    "k-mesh",
    "counting",
)

_LIMIT_SYMMETRY_DIMENSION_TERMS = (
    "limit",
    "symmetry",
    "dimension",
    "dimensional",
    "gauge",
    "ward",
)

_CONFLICT_TERMS = (
    "conflict",
    "contradiction",
    "contradicts",
    "inconsistent",
    "disagree",
)

_KNOWN_OBJECT_TERMS = (
    "sector",
    "counting",
    "edge",
    "entanglement",
    "self-energy",
    "kernel",
    "benchmark",
    "code state",
    "symmetry",
    "limit",
    "dimension",
)


def _needs_failure_mode(claim: ClaimRecord, flow: FlowDecision) -> bool:
    return flow.profile in {"guided", "rigorous", "adversarial"} or claim.confidence_state in {
        "hypothesis",
        "coherent",
        "unverified",
    }


def _target_objects(text: str) -> list[str]:
    return [term for term in _KNOWN_OBJECT_TERMS if term in text]


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


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _relation_failure_modes_present(relations: list[str]) -> bool:
    for r in relations:
        lower = r.lower()
        idx = lower.find("failure modes:")
        if idx != -1:
            content = lower[idx + len("failure modes:"):].strip()
            if content:
                return True
    return False
