"""State-conditioned physics question generation for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ClaimRecord, FlowDecision, QuestionRecord


def generate_questions(
    claim: ClaimRecord,
    flow: FlowDecision,
    *,
    object_relations: list[str] | None = None,
) -> list[QuestionRecord]:
    """Generate deterministic physics questions for the current state."""

    relations = object_relations or []
    questions: list[QuestionRecord] = []

    def add(question: str, why: str, expected: str, actions: list[str]) -> None:
        qid = prefixed_id("question", f"{claim.claim_id}:{len(questions)}:{question}", max_slug=40)
        questions.append(
            QuestionRecord(
                question_id=qid,
                scene=flow.profile,
                target_claim=claim.claim_id,
                question=question,
                why_this_question=why,
                expected_answer_shape=expected,
                possible_next_actions=actions,
                target_relations=relations,
                target_uncertainty=claim.active_uncertainty,
                escalation_if_unanswered="move to guided or adversarial review if this blocks claim confidence",
            )
        )

    add(
        f"What exactly must be true for this claim to hold: {claim.statement}",
        "Claim clarity prevents a broad statement from passing on narrow evidence.",
        "A scoped statement plus non-claims and assumptions.",
        ["narrow_claim", "record_non_claims"],
    )

    if relations:
        add(
            f"Which object relation is load-bearing here, and how does it support the claim? Relations: {', '.join(relations)}",
            "The next physics step should inspect relations, not isolated objects.",
            "A relation-level explanation with the weakest edge identified.",
            ["update_relation_graph", "run_relation_check"],
        )
    else:
        add(
            "Which physical objects and object relations would make this claim meaningful?",
            "A claim without object relations is hard to test or falsify.",
            "A list of objects and typed relations.",
            ["create_object_relation_map"],
        )

    if flow.profile in {"guided", "rigorous", "adversarial"} or claim.confidence_state in {"hypothesis", "coherent"}:
        add(
            "If this claim is wrong, what is the most likely failure mechanism?",
            "Non-fluid physics work needs a failure hypothesis before evidence can change trust.",
            "A ranked failure mode with a minimal diagnostic.",
            ["record_failure_hypothesis", "design_minimal_diagnostic"],
        )

    if claim.evidence_profile == "toy_numeric":
        add(
            "Which finite-size, convergence, or comparator check would most reduce the active uncertainty?",
            "Toy numerics can look persuasive for the wrong reason.",
            "One cheap high-information numerical check.",
            ["run_toy_numeric_check", "compare_negative_control"],
        )
    elif claim.evidence_profile == "code_method":
        add(
            "Which formula-code map, code state, or benchmark invariant is most likely to control this result?",
            "Code-method evidence can fail through translation or version drift.",
            "A code object, formula object, and invariant to inspect.",
            ["trace_formula_code_map", "record_code_state"],
        )

    return questions
