from __future__ import annotations


def test_risk_engine_collects_evidence_backed_signals_and_action_budget():
    from brain.v5.models import ClaimRecord, CodeStateRecord
    from brain.v5.risk import assess_claim_risk

    claim = ClaimRecord(
        claim_id="claim-librpa-self-energy",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the Si GW benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="publish claim conflicts with benchmark and needs expensive rerun",
    )
    code_state = CodeStateRecord(
        code_state_id="code-state-librpa-dirty",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=True,
    )

    assessment = assess_claim_risk(claim, code_states=[code_state])

    assert assessment.level == "adversarial"
    assert assessment.score >= 9
    assert assessment.human_checkpoint_needed is True
    assert assessment.action_budget.requires_human_checkpoint is True
    assert "counterargument_or_falsification_path" in assessment.action_budget.required_outputs

    signal_kinds = {signal.kind for signal in assessment.signals}
    assert {
        "claim_importance",
        "literature_conflict",
        "compute_cost",
        "formula_to_code_risk",
        "reproducibility_risk",
    }.issubset(signal_kinds)

    for signal in assessment.signals:
        assert signal.reason
        assert signal.evidence_ref
        assert signal.suggested_action


def test_risk_engine_keeps_trusted_routine_fluid_when_provenance_is_clean():
    from brain.v5.models import ClaimRecord, CodeStateRecord
    from brain.v5.risk import assess_claim_risk

    claim = ClaimRecord(
        claim_id="claim-si-g0w0",
        topic_id="librpa-gw",
        statement="Si G0W0 benchmark stays within trusted tolerance.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="routine benchmark rerun",
        recipe_id="librpa-si-g0w0",
    )
    code_state = CodeStateRecord(
        code_state_id="code-state-librpa-clean",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/benchmark-rerun",
        worktree_path="D:/worktrees/librpa/benchmark-rerun",
        dirty=False,
    )

    assessment = assess_claim_risk(claim, code_states=[code_state])

    assert assessment.level == "fluid"
    assert assessment.action_budget.max_questions == 1
    assert assessment.action_budget.required_outputs == ["session_trace"]
    assert assessment.trust_reductions


def test_execution_brief_exposes_risk_assessment_and_action_budget(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size entanglement counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )

    brief = build_execution_brief(ws, "s1")

    assert brief["risk_assessment"]["level"] in {"guided", "rigorous"}
    assert brief["risk_assessment"]["signals"]
    assert brief["action_budget"]["max_questions"] <= 3
    assert "evidence_or_provenance" in brief["action_budget"]["required_outputs"]
    assert brief["flow_profile"]["risk_level"] == brief["risk_assessment"]["level"]


def test_execution_brief_uses_linked_code_state_for_reproducibility_risk(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.code import record_code_state
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the Si GW benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="benchmark sensitivity",
    )
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=True,
        linked_records={"claim_id": claim.claim_id},
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        active_claim=claim.claim_id,
    )

    brief = build_execution_brief(ws, "s1")

    signal_kinds = {signal["kind"] for signal in brief["risk_assessment"]["signals"]}
    assert "reproducibility_risk" in signal_kinds
    assert any(
        code_state.code_state_id in signal["evidence_ref"]
        for signal in brief["risk_assessment"]["signals"]
        if signal["kind"] == "reproducibility_risk"
    )
    assert brief["risk_assessment"]["level"] in {"rigorous", "adversarial"}
