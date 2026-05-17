from __future__ import annotations


def test_trust_card_applies_only_inside_clean_applicability_scope():
    from brain.v5.models import ClaimRecord, CodeStateRecord
    from brain.v5.trust import TrustCard, resolve_trust_cards

    card = TrustCard(
        card_id="trust-librpa-si-g0w0",
        recipe_id="librpa-si-g0w0",
        title="LibRPA Si G0W0 benchmark",
        applicability_terms=["si", "g0w0", "benchmark"],
        required_evidence_profile="code_method",
        allowed_repo_ids=["librpa"],
        allowed_upstream_commits=["abc123"],
        benchmark_refs=["paper:si-g0w0-reference", "run:baseline-si-g0w0"],
        invalidation_triggers=["self-energy kernel", "coulomb singularity"],
    )
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
        code_state_id="code-state-clean",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/rerun",
        worktree_path="D:/worktrees/librpa/rerun",
        dirty=False,
    )

    resolutions = resolve_trust_cards(claim, [card], code_states=[code_state])

    assert len(resolutions) == 1
    assert resolutions[0].applies is True
    assert resolutions[0].risk_reduction == 3
    assert resolutions[0].benchmark_refs == ["paper:si-g0w0-reference", "run:baseline-si-g0w0"]
    assert not resolutions[0].invalidation_reasons


def test_trust_card_invalidation_blocks_risk_reduction_and_adds_signal():
    from brain.v5.models import ClaimRecord, CodeStateRecord
    from brain.v5.risk import assess_claim_risk
    from brain.v5.trust import TrustCard

    card = TrustCard(
        card_id="trust-librpa-si-g0w0",
        recipe_id="librpa-si-g0w0",
        title="LibRPA Si G0W0 benchmark",
        applicability_terms=["si", "g0w0", "benchmark"],
        required_evidence_profile="code_method",
        allowed_repo_ids=["librpa"],
        allowed_upstream_commits=["abc123"],
        benchmark_refs=["paper:si-g0w0-reference"],
        invalidation_triggers=["self-energy kernel"],
    )
    claim = ClaimRecord(
        claim_id="claim-modified-self-energy",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the Si G0W0 benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="routine benchmark rerun",
        recipe_id="librpa-si-g0w0",
    )
    code_state = CodeStateRecord(
        code_state_id="code-state-clean",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=False,
    )

    assessment = assess_claim_risk(claim, code_states=[code_state], trust_cards=[card])

    signal_kinds = {signal.kind for signal in assessment.signals}
    assert "trust_card_invalidated" in signal_kinds
    assert not any(reduction.startswith("trust_card:trust-librpa-si-g0w0") for reduction in assessment.trust_reductions)
    assert assessment.level in {"rigorous", "adversarial"}
