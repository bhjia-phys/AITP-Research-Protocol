from __future__ import annotations


def test_policy_blocks_code_method_validation_without_code_state():
    from brain.v5.models import ClaimRecord
    from brain.v5.policy import evaluate_policy

    claim = ClaimRecord(
        claim_id="claim-code",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="benchmark sensitivity",
    )

    decision = evaluate_policy(
        action="validate_claim",
        claim=claim,
        code_states=[],
        evidence_refs=["run:benchmark"],
    )

    assert decision.allowed is False
    assert "record_code_state" in decision.required_actions
    assert any(reason.policy_id == "no_code_method_validation_without_code_state" for reason in decision.reasons)


def test_policy_blocks_l2_promotion_without_evidence_ref():
    from brain.v5.models import ClaimRecord
    from brain.v5.policy import evaluate_policy

    claim = ClaimRecord(
        claim_id="claim-fqhe",
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="ready for memory?",
    )

    decision = evaluate_policy(
        action="promote_to_l2",
        claim=claim,
        evidence_refs=[],
    )

    assert decision.allowed is False
    assert "attach_evidence_ref" in decision.required_actions
    assert any(reason.policy_id == "no_l2_promotion_without_evidence_ref" for reason in decision.reasons)


def test_policy_allows_fluid_discussion_without_durable_records():
    from brain.v5.policy import evaluate_policy

    decision = evaluate_policy(
        action="continue_fluid_work",
        risk_level="fluid",
        evidence_refs=[],
        code_states=[],
    )

    assert decision.allowed is True
    assert decision.required_actions == []


def test_policy_blocks_trust_reduction_when_card_invalidated():
    from brain.v5.models import ClaimRecord
    from brain.v5.policy import evaluate_policy
    from brain.v5.risk import RiskAssessment, RiskSignal, action_budget_for_level

    claim = ClaimRecord(
        claim_id="claim-trust",
        topic_id="librpa-gw",
        statement="Modified kernel remains inside trusted recipe.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="routine trusted benchmark",
        recipe_id="librpa-si-g0w0",
    )
    assessment = RiskAssessment(
        level="rigorous",
        score=6,
        signals=[
            RiskSignal(
                kind="trust_card_invalidated",
                severity=3,
                reason="invalidation trigger present: self-energy kernel",
                evidence_ref="trust_card:trust-librpa-si-g0w0",
                suggested_action="rerun validation outside this trust card",
            )
        ],
        trust_reductions=["trust_card:trust-librpa-si-g0w0:3"],
        action_budget=action_budget_for_level("rigorous"),
        summary="rigorous protocol",
    )

    decision = evaluate_policy(
        action="reduce_friction_with_trust_card",
        claim=claim,
        risk_assessment=assessment,
    )

    assert decision.allowed is False
    assert "remove_invalid_trust_reduction" in decision.required_actions
    assert any(reason.policy_id == "no_trust_reduction_when_card_invalidated" for reason in decision.reasons)


def test_policy_blocks_harness_patch_without_test():
    from brain.v5.evolution import EvolutionProposal
    from brain.v5.policy import evaluate_policy

    proposal = EvolutionProposal(
        proposal_id="proposal-no-test",
        title="tighten promotion policy",
        change_direction="tighten",
        incident_count=1,
        target_files=["brain/v5/policy.py"],
        required_tests=[],
        requires_regression_test=True,
        requires_human_review=False,
        approval_level=2,
        rationale="A harness patch needs a regression test.",
    )

    decision = evaluate_policy(
        action="apply_harness_patch",
        evolution_proposal=proposal,
    )

    assert decision.allowed is False
    assert "add_regression_test" in decision.required_actions
    assert any(reason.policy_id == "no_harness_patch_without_test" for reason in decision.reasons)


def test_policy_blocks_trust_changing_action_from_summary_surface():
    from brain.v5.policy import evaluate_policy

    decision = evaluate_policy(
        action="change_claim_confidence",
        context={
            "source_kind": "derived_summary",
            "source_path": ".aitp/surfaces/session_summaries/s1/findings.md",
            "orientation_only": True,
        },
    )

    assert decision.allowed is False
    assert "query_execution_brief_or_typed_record" in decision.required_actions
    assert any(reason.policy_id == "no_summary_surface_as_truth_source" for reason in decision.reasons)
    assert any(reason.severity == "hard_block" for reason in decision.reasons)


def test_policy_allows_trust_changing_action_from_kernel_truth_source():
    from brain.v5.policy import evaluate_policy

    decision = evaluate_policy(
        action="change_claim_confidence",
        context={
            "source_kind": "execution_brief",
            "source_ref": "brief:s1",
        },
    )

    assert decision.allowed is True
    assert decision.required_actions == []


def test_execution_brief_forbidden_now_includes_policy_blocks(tmp_path):
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
        active_uncertainty="benchmark sensitivity",
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        active_claim=claim.claim_id,
    )

    brief = build_execution_brief(ws, "s1")

    assert "policy:no_code_method_validation_without_code_state" in brief["forbidden_now"]
