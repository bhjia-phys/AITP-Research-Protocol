"""Interaction profiles for AITP v5 sessions.

Profiles change how the agent talks and asks; they do not change physics
truth standards, risk levels, or policy guards.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from brain.v5.models import QuestionRecord


@dataclass
class InteractionProfile:
    role: str
    first_move: str
    question_style: str
    explanation_style: str
    question_priorities: list[str] = field(default_factory=list)
    answer_constraints: list[str] = field(default_factory=list)
    checkpoint_bias: str = "risk_budget"


@dataclass
class InteractionPlan:
    requested_role: str
    profile: InteractionProfile
    truth_standard: str
    effective_risk_level: str
    effective_max_questions: int
    adversarial_priority_enabled: bool
    policy_bounds: dict
    boundary_notes: list[str] = field(default_factory=list)


_PROFILES: dict[str, InteractionProfile] = {
    "collaborator": InteractionProfile(
        role="collaborator",
        first_move="work_from_current_state",
        question_style="balanced_physics_collaboration",
        explanation_style="concise_research_notes",
        question_priorities=[
            "clarify_scope",
            "relation_map",
            "failure_or_counterexample",
            "provenance_or_formula_code",
        ],
        answer_constraints=["state_uncertainty", "respect_policy_bounds"],
    ),
    "teacher": InteractionProfile(
        role="teacher",
        first_move="identify_prerequisites",
        question_style="scaffold_with_prerequisites",
        explanation_style="teach_concepts_before_checks",
        question_priorities=[
            "clarify_scope",
            "prerequisite_check",
            "misconception_check",
            "relation_map",
            "failure_or_counterexample",
            "provenance_or_formula_code",
        ],
        answer_constraints=["name_prerequisites", "separate_intuition_from_evidence", "respect_policy_bounds"],
    ),
    "student": InteractionProfile(
        role="student",
        first_move="mirror_user_claim",
        question_style="clarify_before_asserting",
        explanation_style="reflective_and_unsure_when_needed",
        question_priorities=[
            "mirror_user_claim",
            "clarify_terms",
            "clarify_scope",
            "relation_map",
            "failure_or_counterexample",
        ],
        answer_constraints=["ask_when_unsure", "mirror_claim_before_extending", "respect_policy_bounds"],
    ),
    "critic": InteractionProfile(
        role="critic",
        first_move="look_for_failure_mode",
        question_style="adversarial_but_bounded",
        explanation_style="failure_modes_first",
        question_priorities=[
            "failure_or_counterexample",
            "provenance_or_formula_code",
            "relation_map",
            "clarify_scope",
        ],
        answer_constraints=["criticize_claim_not_user", "name_cheapest_falsifier", "respect_policy_bounds"],
    ),
    "seminar_host": InteractionProfile(
        role="seminar_host",
        first_move="frame_discussion_map",
        question_style="surface_assumptions_and_next_speakers",
        explanation_style="structured_discussion_summary",
        question_priorities=[
            "clarify_scope",
            "relation_map",
            "failure_or_counterexample",
            "open_question",
        ],
        answer_constraints=["summarize_disagreement", "keep_threads_separable", "respect_policy_bounds"],
    ),
    "reproducer": InteractionProfile(
        role="reproducer",
        first_move="ask_for_minimal_reproduction_state",
        question_style="provenance_and_minimal_check_first",
        explanation_style="operational_reproduction_log",
        question_priorities=[
            "provenance_or_formula_code",
            "benchmark_or_comparator",
            "failure_or_counterexample",
            "clarify_scope",
        ],
        answer_constraints=["record_versions", "prefer_minimal_check", "respect_policy_bounds"],
    ),
}

_LIGHTER_TERMS = ("lighter", "light", "fast", "quick", "keep it moving", "顺畅", "轻")
_STRICTER_TERMS = ("stricter", "strict", "rigorous", "careful", "adversarial", "严谨", "重")
_ADVERSARIAL_RISK_LEVELS = {"guided", "rigorous", "adversarial"}


def resolve_interaction_profile(
    role: str = "collaborator",
    *,
    risk_level: str,
    max_questions: int,
    user_steering: str = "",
) -> InteractionPlan:
    """Resolve a user-facing interaction posture inside risk/policy bounds."""

    requested_role = role or "collaborator"
    profile = _PROFILES.get(requested_role, _PROFILES["collaborator"])
    notes: list[str] = []

    adversarial_enabled = profile.role == "critic" and risk_level in _ADVERSARIAL_RISK_LEVELS
    if profile.role == "critic" and not adversarial_enabled:
        profile = replace(
            profile,
            question_priorities=[
                "clarify_scope",
                "relation_map",
                "failure_or_counterexample",
                "provenance_or_formula_code",
            ],
        )
        notes.append("critic adversarial priority not enabled for fluid risk")

    effective_max = max_questions
    steering = user_steering.lower()
    if _contains_any(steering, _LIGHTER_TERMS):
        if risk_level in {"fluid", "guided"}:
            effective_max = max(1, max_questions - 1)
            notes.append("user requested lighter interaction; question budget reduced inside low-risk bounds")
        else:
            notes.append("user requested lighter interaction, but question budget not reduced at rigorous/adversarial risk")
    elif _contains_any(steering, _STRICTER_TERMS):
        notes.append("user requested stricter interaction; risk level unchanged and policy still controls escalation")

    return InteractionPlan(
        requested_role=requested_role,
        profile=profile,
        truth_standard="unchanged",
        effective_risk_level=risk_level,
        effective_max_questions=effective_max,
        adversarial_priority_enabled=adversarial_enabled,
        policy_bounds={
            "may_lower_truth_standard": False,
            "risk_level_changed": False,
            "max_questions_upper_bound": max_questions,
        },
        boundary_notes=notes,
    )


def prioritize_questions(
    questions: list[QuestionRecord],
    plan: InteractionPlan,
) -> list[QuestionRecord]:
    """Return questions ordered for an interaction profile without mutating them."""

    priority_index = {name: index for index, name in enumerate(plan.profile.question_priorities)}

    def score(item: tuple[int, QuestionRecord]) -> tuple[int, int]:
        original_index, question = item
        tags = _question_tags(question)
        best = min((priority_index[tag] for tag in tags if tag in priority_index), default=len(priority_index))
        return best, original_index

    return [question for _, question in sorted(enumerate(questions), key=score)]


def _question_tags(question: QuestionRecord) -> set[str]:
    text = " ".join([question.question, *question.possible_next_actions]).lower()
    tags: set[str] = set()
    if "exactly must be true" in text or "narrow_claim" in text or "clarify" in text:
        tags.add("clarify_scope")
        tags.add("clarify_terms")
        tags.add("mirror_user_claim")
    if "relation" in text or "object" in text:
        tags.add("relation_map")
    if "wrong" in text or "failure" in text or "falsif" in text:
        tags.add("failure_or_counterexample")
    if "formula" in text or "code" in text or "provenance" in text or "record_code_state" in text:
        tags.add("provenance_or_formula_code")
    if "finite-size" in text or "benchmark" in text or "comparator" in text:
        tags.add("benchmark_or_comparator")
    return tags


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
