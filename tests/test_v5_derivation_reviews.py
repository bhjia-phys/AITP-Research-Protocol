from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="derivation-review-test", host="pytest")


def _write(ws, family, record):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).write(family, record)
    return PinnedRecordRef(result.record_ref, result.content_hash, result.revision)


def _seed_closed(tmp_path):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.execution_models import ArtifactRecord, HumanCheckpointRecord, ValidationResultRecord
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.pinned_record_refs import PinnedRecordRef, pin_current_record
    from brain.v5.research_state import register_source
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The replica derivation has separate structural and review status.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Independent validation remains explicit.",
    )
    source = register_source(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        uri="https://example.invalid/review-source.pdf",
        label="Review source",
    )
    source_ref = pin_current_record(ws, f"reference_location:{source.location_id}")
    formula = record_physics_object(
        ws,
        topic_id="qg",
        object_type="formula",
        name="replica trace",
        definition="The exact source-anchored replica trace.",
        notation="Tr rho^n",
        assumptions=["integer n"],
    )
    formula_ref = pin_current_record(ws, f"physics_object:{formula.object_id}")
    check_ref = _write(
        ws,
        "artifacts",
        ArtifactRecord(
            artifact_id="derivation-local-check",
            topic_id="qg",
            claim_id=claim.claim_id,
            artifact_type="test_report",
            uri="file:///checks/derivation.json",
            summary="Independent local algebra check.",
            content_hash="a" * 64,
            hash_algorithm="sha256",
        ),
    )
    step = DerivationStepRecord(
        step_id="review-step",
        chain_id="review-chain",
        topic_id="qg",
        claim_id=claim.claim_id,
        sequence=1,
        input_expression="Tr rho^n",
        output_expression="Z_n / Z_1^n",
        justification_type="source_anchored_identity",
        invoked_knowledge_refs=[vars(formula_ref)],
        source_anchor_refs=[vars(source_ref)],
        local_check_refs=[vars(check_ref)],
        status="established",
    )
    step_write = record_derivation_step(ws, step, actor=_actor())
    step_ref = PinnedRecordRef(step_write.record_ref, step_write.content_hash, step_write.revision)
    chain = DerivationChainRecord(
        chain_id="review-chain",
        topic_id="qg",
        claim_id=claim.claim_id,
        title="Reviewed replica chain",
        target="Recover the normalized replica trace.",
        assumptions=["integer replica index"],
        conventions=["Euclidean signature"],
        framework="replica path integral",
        regime="bounded semiclassical analysis",
        ordered_step_refs=[vars(step_ref)],
        check_refs=[vars(check_ref)],
        source_refs=[vars(source_ref)],
        status="structurally_closed",
    )
    chain_write = record_derivation_chain(ws, chain, actor=_actor())
    chain_ref = PinnedRecordRef(chain_write.record_ref, chain_write.content_hash, chain_write.revision)
    checkpoint_ref = _write(
        ws,
        "checkpoints",
        HumanCheckpointRecord(
            checkpoint_id="derivation-review-checkpoint",
            topic_id="qg",
            claim_id=claim.claim_id,
            reason="Record the bounded derivation review decision.",
            requested_by="pytest",
            options=["approve", "needs_revision"],
            status="decided",
            decision="approve",
            rationale="The exact chain and step were inspected.",
            decided_by="reviewer",
            action="review_derivation",
        ),
    )
    validation_ref = _write(
        ws,
        "validation_results",
        ValidationResultRecord(
            result_id="derivation-validation",
            topic_id="qg",
            claim_id=claim.claim_id,
            contract_id="derivation-contract",
            tool_run_id="symbolic-check",
            status="passed",
            checked_outputs=["algebra", "source anchors"],
            summary="The bounded derivation checks passed.",
        ),
    )
    return {
        "ws": ws,
        "claim": claim,
        "source_ref": source_ref,
        "check_ref": check_ref,
        "step": step,
        "step_ref": step_ref,
        "chain_ref": chain_ref,
        "checkpoint_ref": checkpoint_ref,
        "validation_ref": validation_ref,
    }


def _review(data, *, review_id="review-1", decision="passed", supersedes=None, validations=None):
    from brain.v5.derivation_models import DerivationReviewRecord

    return DerivationReviewRecord(
        review_id=review_id,
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        chain_ref=vars(data["chain_ref"]),
        step_refs=[vars(data["step_ref"])],
        source_anchor_refs=[vars(data["source_ref"])],
        validation_check_refs=[
            vars(item) for item in (validations if validations is not None else (data["validation_ref"],))
        ],
        tool_run_check_refs=[],
        checkpoint_ref=vars(data["checkpoint_ref"]),
        reviewer_role="adversarial_derivation_reviewer",
        decision=decision,
        reviewed_scope=["structure", "sources", "assumptions", "checks"],
        summary="Exact chain, steps, source anchors, and checks were reviewed.",
        supersedes_review_ref=vars(supersedes) if supersedes else {},
    )


def test_projection_separates_structural_reviewed_and_validated_status(tmp_path):
    from brain.v5.derivation_reviews import project_derivation_status, record_derivation_review

    data = _seed_closed(tmp_path)
    before = project_derivation_status(data["ws"], data["chain_ref"])
    assert before.structurally_closed is True
    assert before.source_complete is True
    assert before.reviewed is False
    assert before.validated is False

    review = record_derivation_review(data["ws"], _review(data), actor=_actor())
    after = project_derivation_status(data["ws"], data["chain_ref"])

    assert after.structurally_closed is True
    assert after.source_complete is True
    assert after.reviewed is True
    assert after.validated is True
    assert after.active_review_ref == review.record_ref
    assert after.can_update_claim_trust is False


def test_review_requires_complete_current_step_hash_coverage(tmp_path):
    from brain.v5.derivation_reviews import record_derivation_review

    data = _seed_closed(tmp_path)
    with pytest.raises(ValueError, match="exactly cover the chain steps"):
        record_derivation_review(
            data["ws"],
            replace(_review(data), step_refs=[]),
            actor=_actor(),
        )


def test_projection_rejects_repository_bypass_review_that_never_passed_validator(tmp_path):
    from brain.v5.derivation_reviews import project_derivation_status

    data = _seed_closed(tmp_path)
    _write(
        data["ws"],
        "derivation_reviews",
        replace(_review(data), step_refs=[]),
    )

    status = project_derivation_status(data["ws"], data["chain_ref"])

    assert status.reviewed is False
    assert status.validated is False
    assert any("exactly cover the chain steps" in reason for reason in status.blocking_reasons)


def test_projection_isolates_unrelated_malformed_supersedes_pin(tmp_path):
    from brain.v5.derivation_reviews import project_derivation_status, record_derivation_review
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _seed_closed(tmp_path)
    valid = record_derivation_review(data["ws"], _review(data), actor=_actor())
    valid_ref = PinnedRecordRef(valid.record_ref, valid.content_hash, valid.revision)
    unrelated_chain_ref = {
        "record_ref": "derivation_chain:unrelated-chain",
        "content_hash": "f" * 64,
        "revision": 1,
    }
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="unrelated-malformed-supersedes",
            chain_ref=unrelated_chain_ref,
            supersedes_review_ref="not-an-exact-pin",
        ),
    )
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="unrelated-validly-shaped-supersedes",
            chain_ref=unrelated_chain_ref,
            supersedes_review_ref=vars(valid_ref),
        ),
    )

    status = project_derivation_status(data["ws"], data["chain_ref"])

    assert status.reviewed is True
    assert status.validated is True


def test_projection_fails_closed_for_same_chain_malformed_supersedes_pin(tmp_path):
    from brain.v5.derivation_reviews import project_derivation_status, record_derivation_review

    data = _seed_closed(tmp_path)
    record_derivation_review(data["ws"], _review(data), actor=_actor())
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="same-chain-malformed-supersedes",
            supersedes_review_ref="not-an-exact-pin",
        ),
    )

    status = project_derivation_status(data["ws"], data["chain_ref"])

    assert status.reviewed is False
    assert status.validated is False
    assert any("invalid supersedes pin" in reason for reason in status.blocking_reasons)


def test_step_revision_makes_prior_review_and_structural_projection_stale(tmp_path):
    from brain.v5.derivation_reviews import project_derivation_status, record_derivation_review
    from brain.v5.derivations import record_derivation_step

    data = _seed_closed(tmp_path)
    record_derivation_review(data["ws"], _review(data), actor=_actor())
    record_derivation_step(
        data["ws"],
        replace(data["step"], output_expression="changed unreviewed expression"),
        actor=_actor(),
        expected_current_hash=data["step_ref"].content_hash,
    )

    status = project_derivation_status(data["ws"], data["chain_ref"])

    assert status.structurally_closed is False
    assert status.reviewed is False
    assert status.validated is False
    assert any("stale" in reason for reason in status.blocking_reasons)


def test_review_supersession_is_exact_and_cannot_branch(tmp_path):
    from brain.v5.derivation_reviews import (
        project_derivation_status,
        record_derivation_review,
        supersede_derivation_review,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _seed_closed(tmp_path)
    prior = record_derivation_review(
        data["ws"],
        _review(data, decision="inconclusive", validations=()),
        actor=_actor(),
    )
    prior_ref = PinnedRecordRef(prior.record_ref, prior.content_hash, prior.revision)
    replacement = _review(
        data,
        review_id="review-2",
        decision="passed",
        supersedes=prior_ref,
    )
    successor = supersede_derivation_review(
        data["ws"],
        prior_ref,
        replacement,
        actor=_actor(),
    )

    status = project_derivation_status(data["ws"], data["chain_ref"])
    assert status.reviewed is True
    assert status.active_review_ref == successor.record_ref

    with pytest.raises(ValueError, match="already has a successor"):
        supersede_derivation_review(
            data["ws"],
            prior_ref,
            replace(replacement, review_id="review-branch"),
            actor=_actor(),
        )


def test_review_supersession_ignores_unrelated_malformed_history(tmp_path):
    from brain.v5.derivation_reviews import supersede_derivation_review

    data = _seed_closed(tmp_path)
    prior = _write(
        data["ws"],
        "derivation_reviews",
        _review(data, decision="inconclusive", validations=()),
    )
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="unrelated-malformed-writer-history",
            chain_ref={
                "record_ref": "derivation_chain:unrelated-chain",
                "content_hash": "e" * 64,
                "revision": 1,
            },
            supersedes_review_ref="not-an-exact-pin",
        ),
    )
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="unrelated-validly-shaped-writer-history",
            chain_ref={
                "record_ref": "derivation_chain:unrelated-chain",
                "content_hash": "d" * 64,
                "revision": 1,
            },
            supersedes_review_ref=vars(prior),
        ),
    )
    replacement = _review(
        data,
        review_id="review-after-unrelated-malformed-history",
        supersedes=prior,
    )

    result = supersede_derivation_review(
        data["ws"],
        prior,
        replacement,
        actor=_actor(),
    )

    assert result.record_ref == "derivation_review:review-after-unrelated-malformed-history"


def test_review_supersession_rejects_same_chain_dangling_predecessor(tmp_path):
    from brain.v5.derivation_reviews import supersede_derivation_review

    data = _seed_closed(tmp_path)
    prior = _write(
        data["ws"],
        "derivation_reviews",
        _review(data, decision="inconclusive", validations=()),
    )
    _write(
        data["ws"],
        "derivation_reviews",
        replace(
            _review(data),
            review_id="same-chain-dangling-history",
            supersedes_review_ref={
                "record_ref": "derivation_review:missing-predecessor",
                "content_hash": "c" * 64,
                "revision": 1,
            },
        ),
    )
    replacement = _review(
        data,
        review_id="review-after-dangling-history",
        supersedes=prior,
    )

    with pytest.raises(ValueError, match="invalid supersedes history"):
        supersede_derivation_review(
            data["ws"],
            prior,
            replacement,
            actor=_actor(),
        )


def test_review_supersession_rejects_cross_revision_chain_pin(tmp_path):
    from brain.v5.derivation_models import DerivationChainRecord
    from brain.v5.derivation_reviews import record_derivation_review, supersede_derivation_review
    from brain.v5.derivations import record_derivation_chain
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version

    data = _seed_closed(tmp_path)
    prior_write = record_derivation_review(
        data["ws"],
        _review(data, decision="inconclusive", validations=()),
        actor=_actor(),
    )
    prior_ref = PinnedRecordRef(
        prior_write.record_ref,
        prior_write.content_hash,
        prior_write.revision,
    )
    chain = get_record_version(data["ws"], data["chain_ref"]).record
    assert isinstance(chain, DerivationChainRecord)
    revised = record_derivation_chain(
        data["ws"],
        replace(chain, title="Revised exact chain pin"),
        actor=_actor(),
        expected_current_hash=data["chain_ref"].content_hash,
    )
    revised_chain_ref = PinnedRecordRef(
        revised.record_ref,
        revised.content_hash,
        revised.revision,
    )
    replacement = replace(
        _review(
            data,
            review_id="cross-revision-review",
            supersedes=prior_ref,
        ),
        chain_ref=vars(revised_chain_ref),
    )

    with pytest.raises(ValueError, match="exact derivation chain revision"):
        supersede_derivation_review(
            data["ws"],
            prior_ref,
            replacement,
            actor=_actor(),
        )


def test_source_reconstruction_reports_derivation_coverage_separately(tmp_path):
    from brain.v5.derivation_reviews import record_derivation_review
    from brain.v5.source_reconstruction import (
        audit_source_reconstruction,
        build_source_reconstruction_review_packet,
    )

    data = _seed_closed(tmp_path)
    before = audit_source_reconstruction(data["ws"], claim_id=data["claim"].claim_id)

    assert before["required_components"] == [
        "definitions",
        "assumptions_or_scope",
        "source_locations",
        "dependency_graph",
        "reconstruction_path",
        "failure_conditions",
    ]
    coverage = before["derivation_coverage"]
    assert coverage["applicable"] is True
    assert coverage["structural_closure"]["status"] == "satisfied"
    assert coverage["source_anchor_completeness"]["status"] == "satisfied"
    assert coverage["review_coverage"]["status"] == "missing"
    assert coverage["validation_coverage"]["status"] == "missing"
    assert coverage["can_render_as_proved"] is False
    assert coverage["can_use_as_evidence_basis"] is False
    packet = build_source_reconstruction_review_packet(
        data["ws"],
        claim_id=data["claim"].claim_id,
    )
    assert "review_derivation" in packet["recommended_actions"]
    assert "validate_derivation" in packet["recommended_actions"]

    record_derivation_review(data["ws"], _review(data), actor=_actor())
    after = audit_source_reconstruction(data["ws"], claim_id=data["claim"].claim_id)
    coverage = after["derivation_coverage"]
    assert coverage["review_coverage"]["status"] == "satisfied"
    assert coverage["validation_coverage"]["status"] == "satisfied"
    assert coverage["can_use_as_evidence_basis"] is True
    assert coverage["can_update_claim_trust"] is False


def test_derivation_coverage_does_not_hide_pending_current_chain(tmp_path):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.derivation_reviews import record_derivation_review
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.source_reconstruction import (
        audit_source_reconstruction,
        build_source_reconstruction_review_packet,
    )

    data = _seed_closed(tmp_path)
    record_derivation_review(data["ws"], _review(data), actor=_actor())
    pending_step = DerivationStepRecord(
        step_id="pending-alternative-step",
        chain_id="pending-alternative-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        sequence=1,
        input_expression="A",
        output_expression="B",
        justification_type="open_alternative",
        status="draft",
    )
    step_write = record_derivation_step(data["ws"], pending_step, actor=_actor())
    step_ref = PinnedRecordRef(step_write.record_ref, step_write.content_hash, step_write.revision)
    pending_chain = DerivationChainRecord(
        chain_id="pending-alternative-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        title="Pending alternative derivation",
        target="Keep an unresolved alternative visible.",
        assumptions=["alternative assumptions remain under review"],
        conventions=["exact pins"],
        framework="alternative formal route",
        regime="unresolved",
        ordered_step_refs=[vars(step_ref)],
        open_gaps=["justify the alternative step"],
        status="in_progress",
    )
    record_derivation_chain(data["ws"], pending_chain, actor=_actor())

    audit = audit_source_reconstruction(data["ws"], claim_id=data["claim"].claim_id)
    packet = build_source_reconstruction_review_packet(
        data["ws"],
        claim_id=data["claim"].claim_id,
    )

    coverage = audit["derivation_coverage"]
    assert coverage["status"] == "incomplete"
    assert coverage["can_use_as_evidence_basis"] is False
    assert "complete_derivation_structure" in packet["recommended_actions"]
    assert "complete_derivation_source_anchors" in packet["recommended_actions"]
    assert "review_derivation" in packet["recommended_actions"]
    assert "validate_derivation" in packet["recommended_actions"]


def test_unattributed_malformed_chain_is_workspace_health_not_claim_completeness(tmp_path):
    from brain.v5.derivation_reviews import record_derivation_review
    from brain.v5.source_reconstruction import audit_source_reconstruction

    data = _seed_closed(tmp_path)
    record_derivation_review(data["ws"], _review(data), actor=_actor())
    malformed = data["ws"].registry_dir("derivation_chains") / "unattributed-broken.md"
    malformed.write_text("---\nkind: derivation_chain\ninvalid: [\n---\n", encoding="utf-8")

    audit = audit_source_reconstruction(data["ws"], claim_id=data["claim"].claim_id)

    coverage = audit["derivation_coverage"]
    assert coverage["status"] == "complete"
    assert coverage["can_use_as_evidence_basis"] is True
    assert coverage["workspace_health"]["status"] == "degraded"
    assert coverage["workspace_health"]["read_errors"]


def test_claim_local_projection_error_marks_all_derivation_actions_missing(tmp_path, monkeypatch):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.derivation_reviews import record_derivation_review
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.source_reconstruction import (
        audit_source_reconstruction,
        build_source_reconstruction_review_packet,
    )
    import brain.v5.derivation_reconstruction as reconstruction

    data = _seed_closed(tmp_path)
    record_derivation_review(data["ws"], _review(data), actor=_actor())
    second_step = DerivationStepRecord(
        step_id="projection-error-step",
        chain_id="projection-error-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        sequence=1,
        input_expression="C",
        output_expression="D",
        justification_type="projection_error_fixture",
        status="draft",
    )
    step_write = record_derivation_step(data["ws"], second_step, actor=_actor())
    step_ref = PinnedRecordRef(step_write.record_ref, step_write.content_hash, step_write.revision)
    second_chain = DerivationChainRecord(
        chain_id="projection-error-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        title="Projection error chain",
        target="Keep projection failures visible.",
        assumptions=["projection may fail"],
        conventions=["exact pins"],
        framework="projection error fixture",
        regime="diagnostic",
        ordered_step_refs=[vars(step_ref)],
        open_gaps=["projection unavailable"],
        status="in_progress",
    )
    record_derivation_chain(data["ws"], second_chain, actor=_actor())
    original = reconstruction.project_derivation_status

    def fail_one_projection(ws, chain_ref):
        if chain_ref.record_ref == "derivation_chain:projection-error-chain":
            raise ValueError("claim-local projection failed")
        return original(ws, chain_ref)

    monkeypatch.setattr(reconstruction, "project_derivation_status", fail_one_projection)

    audit = audit_source_reconstruction(data["ws"], claim_id=data["claim"].claim_id)
    packet = build_source_reconstruction_review_packet(
        data["ws"],
        claim_id=data["claim"].claim_id,
    )

    coverage = audit["derivation_coverage"]
    assert coverage["status"] == "incomplete"
    assert coverage["structural_closure"]["status"] == "missing"
    assert coverage["source_anchor_completeness"]["status"] == "missing"
    assert coverage["review_coverage"]["status"] == "missing"
    assert coverage["validation_coverage"]["status"] == "missing"
    assert set(packet["recommended_actions"]) >= {
        "complete_derivation_structure",
        "complete_derivation_source_anchors",
        "review_derivation",
        "validate_derivation",
    }


def test_non_derivation_claim_keeps_existing_reconstruction_semantics(tmp_path):
    from brain.v5.source_reconstruction import audit_source_reconstruction
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "numeric", context_id="compute", title="Numerical topic")
    claim = create_claim(
        ws,
        topic_id="numeric",
        statement="A numerical convergence claim does not require a derivation DAG.",
        evidence_profile="numerical",
        confidence_state="hypothesis",
        active_uncertainty="Convergence is pending.",
    )

    audit = audit_source_reconstruction(ws, claim_id=claim.claim_id)

    assert audit["derivation_coverage"]["applicable"] is False
    assert audit["derivation_coverage"]["status"] == "not_applicable"
    assert "derivation_structural_closure" not in audit["required_components"]
