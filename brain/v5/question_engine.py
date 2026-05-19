"""State-conditioned physics question generation for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import ClaimRecord, FlowDecision, QuestionRecord
from brain.v5.question_intents import QuestionIntent, generate_question_intents


def generate_questions(
    claim: ClaimRecord,
    flow: FlowDecision,
    *,
    object_relations: list[object] | None = None,
    interaction=None,
) -> list[QuestionRecord]:
    """Generate deterministic physics questions for the current state."""

    intents = generate_question_intents(
        claim,
        flow,
        object_relations=object_relations,
        interaction=interaction,
    )
    return [_expand_intent(intent) for intent in intents]


def _expand_intent(intent: QuestionIntent) -> QuestionRecord:
    question_id = prefixed_id("question", f"{intent.intent_id}:{intent.kernel_prompt}", max_slug=54)
    return QuestionRecord(
        question_id=question_id,
        scene=intent.scene,
        target_claim=intent.target_claim,
        question=intent.kernel_prompt,
        why_this_question=intent.rationale,
        expected_answer_shape=intent.expected_answer_shape,
        possible_next_actions=intent.suggested_actions,
        target_objects=intent.target_objects,
        target_relations=intent.target_relations,
        target_uncertainty=intent.target_uncertainty,
        intent_id=intent.intent_id,
        intent_type=intent.intent_type,
        expansion_boundary=intent.expansion_boundary,
        escalation_if_unanswered="move to guided or adversarial review if this blocks claim confidence",
    )
