from __future__ import annotations


def test_teacher_profile_changes_question_style_without_lowering_truth_standard():
    from brain.v5.interaction import resolve_interaction_profile

    plan = resolve_interaction_profile(
        "teacher",
        risk_level="rigorous",
        max_questions=3,
    )

    assert plan.profile.role == "teacher"
    assert plan.profile.question_style == "scaffold_with_prerequisites"
    assert plan.profile.explanation_style == "teach_concepts_before_checks"
    assert plan.truth_standard == "unchanged"
    assert plan.effective_risk_level == "rigorous"
    assert plan.effective_max_questions == 3
    assert plan.policy_bounds["may_lower_truth_standard"] is False


def test_student_profile_prefers_clarifying_questions_and_mirroring():
    from brain.v5.interaction import resolve_interaction_profile

    plan = resolve_interaction_profile(
        "student",
        risk_level="guided",
        max_questions=3,
    )

    assert plan.profile.first_move == "mirror_user_claim"
    assert plan.profile.question_priorities[:2] == ["mirror_user_claim", "clarify_terms"]
    assert "ask_when_unsure" in plan.profile.answer_constraints
    assert plan.truth_standard == "unchanged"


def test_critic_profile_raises_adversarial_priority_only_when_risk_permits():
    from brain.v5.interaction import resolve_interaction_profile

    fluid_plan = resolve_interaction_profile("critic", risk_level="fluid", max_questions=1)
    rigorous_plan = resolve_interaction_profile("critic", risk_level="rigorous", max_questions=3)

    assert fluid_plan.adversarial_priority_enabled is False
    assert fluid_plan.profile.question_priorities[0] != "failure_or_counterexample"
    assert rigorous_plan.adversarial_priority_enabled is True
    assert rigorous_plan.profile.question_priorities[0] == "failure_or_counterexample"
    assert rigorous_plan.effective_risk_level == "rigorous"


def test_user_steering_can_lighten_friction_inside_policy_bounds():
    from brain.v5.interaction import resolve_interaction_profile

    guided_plan = resolve_interaction_profile(
        "collaborator",
        risk_level="guided",
        max_questions=3,
        user_steering="lighter, keep it moving",
    )
    rigorous_plan = resolve_interaction_profile(
        "collaborator",
        risk_level="rigorous",
        max_questions=3,
        user_steering="lighter, keep it moving",
    )

    assert guided_plan.effective_max_questions == 2
    assert guided_plan.policy_bounds["risk_level_changed"] is False
    assert rigorous_plan.effective_max_questions == 3
    assert any("not reduced" in note for note in rigorous_plan.boundary_notes)


def test_interaction_profile_prioritizes_questions_without_mutating_questions():
    from brain.v5.interaction import prioritize_questions, resolve_interaction_profile
    from brain.v5.models import ClaimRecord, FlowDecision
    from brain.v5.question_engine import generate_questions

    claim = ClaimRecord(
        claim_id="claim-code",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )
    flow = FlowDecision(profile="rigorous", reason="code method risk")
    questions = generate_questions(claim, flow)
    plan = resolve_interaction_profile("critic", risk_level="rigorous", max_questions=3)

    prioritized = prioritize_questions(questions, plan)

    assert prioritized[0].question_id in {q.question_id for q in questions}
    assert "wrong" in prioritized[0].question.lower() or "failure" in prioritized[0].question.lower()
    assert {q.question_id for q in prioritized} == {q.question_id for q in questions}


def test_execution_brief_includes_interaction_profile_and_keeps_policy_guards(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        active_claim=claim.claim_id,
        interaction_profile="teacher",
        interaction_steering="lighter",
    )

    brief = build_execution_brief(ws, "s1")

    assert brief["interaction_profile"]["profile"]["role"] == "teacher"
    assert brief["interaction_profile"]["truth_standard"] == "unchanged"
    assert brief["interaction_profile"]["effective_risk_level"] == brief["risk_assessment"]["level"]
    assert len(brief["mandatory_reflection"]) <= brief["interaction_profile"]["effective_max_questions"]
    assert "policy:no_code_method_validation_without_code_state" in brief["forbidden_now"]
