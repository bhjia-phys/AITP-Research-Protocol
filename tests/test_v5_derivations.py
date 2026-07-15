from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="derivation-test", host="pytest")


def _pin_write(ws, family, record):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).write(family, record)
    return PinnedRecordRef(result.record_ref, result.content_hash, result.revision)


def _fixture(tmp_path):
    from brain.v5.execution_models import ArtifactRecord
    from brain.v5.physics_objects import record_physics_object
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.research_state import register_source
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The bounded replica derivation has an inspectable logical chain.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="The target-side review remains open.",
    )
    source = register_source(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        uri="https://example.invalid/qg-paper.pdf",
        label="QG source",
    )
    source_ref = pin_current_record(ws, f"reference_location:{source.location_id}")
    formula = record_physics_object(
        ws,
        topic_id="qg",
        object_type="formula",
        name="replica partition function",
        definition="Z_n is the source-anchored replicated partition function.",
        notation="Z_n",
        assumptions=["integer replica index before continuation"],
        source_refs=[source_ref.record_ref],
    )
    formula_ref = pin_current_record(ws, f"physics_object:{formula.object_id}")
    check = ArtifactRecord(
        artifact_id="replica-algebra-check",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_type="test_report",
        uri="file:///checks/replica-algebra.json",
        summary="Local symbolic and limiting-case checks.",
        content_hash="a" * 64,
        hash_algorithm="sha256",
    )
    check_ref = _pin_write(ws, "artifacts", check)
    return {
        "ws": ws,
        "claim": claim,
        "source_ref": source_ref,
        "formula_ref": formula_ref,
        "check_ref": check_ref,
    }


def _step(data, *, step_id, sequence, dependencies=(), unresolved=(), status="established"):
    from brain.v5.derivation_models import DerivationStepRecord

    return DerivationStepRecord(
        step_id=step_id,
        chain_id="replica-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        sequence=sequence,
        input_expression="Z_n",
        output_expression=f"step_{sequence}(Z_n)",
        justification_type="algebraic_rewrite",
        dependency_step_refs=[vars(item) for item in dependencies],
        invoked_knowledge_refs=[vars(data["formula_ref"])],
        source_anchor_refs=[vars(data["source_ref"])],
        local_check_refs=[vars(data["check_ref"])],
        unresolved_conditions=list(unresolved),
        status=status,
    )


def _chain(data, step_refs, *, status="structurally_closed", open_gaps=(), imported=()):
    from brain.v5.derivation_models import DerivationChainRecord

    return DerivationChainRecord(
        chain_id="replica-chain",
        topic_id="qg",
        claim_id=data["claim"].claim_id,
        title="Replica continuation chain",
        target="Derive the bounded continuation relation from pinned conventions.",
        assumptions=["integer n before continuation"],
        conventions=["Euclidean signature", "normalized Z_1 = 1"],
        framework="replica path integral",
        regime="semiclassical bounded saddle analysis",
        ordered_step_refs=[vars(item) for item in step_refs],
        imported_chain_bindings=list(imported),
        open_gaps=list(open_gaps),
        check_refs=[vars(data["check_ref"])],
        source_refs=[vars(data["source_ref"])],
        status=status,
    )


def test_structurally_closed_derivation_is_an_exact_trust_neutral_dag(tmp_path):
    from brain.v5.derivation_models import DerivationChainRecord
    from brain.v5.derivations import (
        record_derivation_chain,
        record_derivation_step,
        validate_derivation_dag,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
    from brain.v5.record_family_registry import spec_for_family

    data = _fixture(tmp_path)
    first = record_derivation_step(data["ws"], _step(data, step_id="replica-s1", sequence=1), actor=_actor())
    first_ref = PinnedRecordRef(first.record_ref, first.content_hash, first.revision)
    second = record_derivation_step(
        data["ws"],
        _step(data, step_id="replica-s2", sequence=2, dependencies=(first_ref,)),
        actor=_actor(),
    )
    second_ref = PinnedRecordRef(second.record_ref, second.content_hash, second.revision)
    result = record_derivation_chain(
        data["ws"],
        _chain(data, (first_ref, second_ref)),
        actor=_actor(),
    )
    chain_ref = PinnedRecordRef(result.record_ref, result.content_hash, result.revision)

    stored = get_record_version(data["ws"], chain_ref).record
    validation = validate_derivation_dag(data["ws"], stored)

    assert isinstance(stored, DerivationChainRecord)
    assert validation.valid is True
    assert validation.ordered_step_ids == ("replica-s1", "replica-s2")
    assert validation.open_gaps == ()
    assert validation.can_update_claim_trust is False
    assert spec_for_family("derivation_chains").trust_effect == "none"
    assert spec_for_family("derivation_steps").trust_effect == "none"


def test_structural_closure_rejects_open_gaps_and_unresolved_step_conditions(tmp_path):
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef

    data = _fixture(tmp_path)
    step = record_derivation_step(
        data["ws"],
        _step(
            data,
            step_id="replica-gap",
            sequence=1,
            unresolved=("analytic continuation uniqueness is unproved",),
            status="blocked",
        ),
        actor=_actor(),
    )
    step_ref = PinnedRecordRef(step.record_ref, step.content_hash, step.revision)

    with pytest.raises(ValueError, match="open gaps|unresolved conditions"):
        record_derivation_chain(
            data["ws"],
            _chain(
                data,
                (step_ref,),
                open_gaps=("analytic continuation uniqueness is unproved",),
            ),
            actor=_actor(),
        )


def test_derivation_dag_rejects_missing_refs_and_self_dependency_cycles(tmp_path):
    from brain.v5.derivation_models import DerivationStepRecord
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository, WritePolicy

    data = _fixture(tmp_path)
    missing = PinnedRecordRef("derivation_step:missing", "b" * 64, 1)
    with pytest.raises(Exception, match="missing|cannot resolve|not found"):
        record_derivation_chain(
            data["ws"],
            _chain(data, (missing,), status="in_progress"),
            actor=_actor(),
        )

    initial = record_derivation_step(
        data["ws"],
        _step(data, step_id="replica-self", sequence=1, status="draft"),
        actor=_actor(),
    )
    initial_ref = PinnedRecordRef(initial.record_ref, initial.content_hash, initial.revision)
    current = _step(
        data,
        step_id="replica-self",
        sequence=1,
        dependencies=(initial_ref,),
        status="draft",
    )
    revised = RecordRepository(data["ws"], actor=_actor()).write(
        "derivation_steps",
        current,
        policy=WritePolicy(mode="revision", expected_hash=initial.content_hash),
    )
    revised_ref = PinnedRecordRef(revised.record_ref, revised.content_hash, revised.revision)

    with pytest.raises(ValueError, match="cycle|self dependency"):
        record_derivation_chain(
            data["ws"],
            _chain(data, (revised_ref,), status="in_progress"),
            actor=_actor(),
        )


def test_cross_chain_dependency_requires_explicit_import_binding(tmp_path):
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.workspace import create_claim, create_topic

    data = _fixture(tmp_path)
    create_topic(data["ws"], "other", context_id="formal-theory", title="Other topic")
    other_claim = create_claim(
        data["ws"],
        topic_id="other",
        statement="A foreign derivation cannot transfer trust.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Target revalidation is absent.",
    )
    foreign = replace(
        _step(data, step_id="foreign-s1", sequence=1),
        chain_id="foreign-chain",
        topic_id="other",
        claim_id=other_claim.claim_id,
        invoked_knowledge_refs=[],
        source_anchor_refs=[],
        local_check_refs=[],
        status="draft",
    )
    foreign_write = record_derivation_step(data["ws"], foreign, actor=_actor())
    foreign_ref = PinnedRecordRef(
        foreign_write.record_ref,
        foreign_write.content_hash,
        foreign_write.revision,
    )
    local = record_derivation_step(
        data["ws"],
        _step(data, step_id="replica-import", sequence=1, dependencies=(foreign_ref,)),
        actor=_actor(),
    )
    local_ref = PinnedRecordRef(local.record_ref, local.content_hash, local.revision)

    with pytest.raises(ValueError, match="imported-chain binding"):
        record_derivation_chain(
            data["ws"],
            _chain(data, (local_ref,), status="in_progress"),
            actor=_actor(),
        )


def test_foreign_step_inputs_are_rejected_but_reviewed_chain_binding_is_orientation_only(
    tmp_path,
    monkeypatch,
):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.execution_models import ScopeRevalidationDecisionRecord
    from brain.v5.execution_scope_policy import ExecutionScopeDecision
    from brain.v5.lifecycle_models import CrossTopicRelationRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef, pin_current_record
    from brain.v5.research_state import register_source
    from brain.v5.workspace import create_claim, create_topic

    data = _fixture(tmp_path)
    create_topic(data["ws"], "other", context_id="formal-theory", title="Other topic")
    other_claim = create_claim(
        data["ws"],
        topic_id="other",
        statement="A foreign derivation remains orientation-only in the target topic.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Target-side revalidation remains mandatory.",
    )
    other_source = register_source(
        data["ws"],
        topic_id="other",
        claim_id=other_claim.claim_id,
        uri="https://example.invalid/foreign.pdf",
        label="Foreign source",
    )
    other_source_ref = pin_current_record(
        data["ws"],
        f"reference_location:{other_source.location_id}",
    )
    local_with_foreign_source = replace(
        _step(data, step_id="local-foreign-anchor", sequence=1),
        source_anchor_refs=[vars(other_source_ref)],
    )
    with pytest.raises(ValueError, match="source_anchor_refs contains a foreign topic ref"):
        record_derivation_step(data["ws"], local_with_foreign_source, actor=_actor())

    foreign_step = DerivationStepRecord(
        step_id="foreign-draft-step",
        chain_id="foreign-chain",
        topic_id="other",
        claim_id=other_claim.claim_id,
        sequence=1,
        input_expression="X",
        output_expression="Y",
        justification_type="legacy_review_candidate",
        status="draft",
    )
    foreign_step_write = record_derivation_step(data["ws"], foreign_step, actor=_actor())
    foreign_step_ref = PinnedRecordRef(
        foreign_step_write.record_ref,
        foreign_step_write.content_hash,
        foreign_step_write.revision,
    )
    foreign_chain = DerivationChainRecord(
        chain_id="foreign-chain",
        topic_id="other",
        claim_id=other_claim.claim_id,
        title="Foreign draft chain",
        target="Expose a reviewed foreign derivation as orientation only.",
        assumptions=["foreign assumption"],
        conventions=["foreign convention"],
        framework="foreign framework",
        regime="foreign regime",
        ordered_step_refs=[vars(foreign_step_ref)],
        status="in_progress",
    )
    foreign_chain_write = record_derivation_chain(data["ws"], foreign_chain, actor=_actor())
    foreign_chain_ref = PinnedRecordRef(
        foreign_chain_write.record_ref,
        foreign_chain_write.content_hash,
        foreign_chain_write.revision,
    )
    bridge_ref = _pin_write(
        data["ws"],
        "cross_topic_relations",
        CrossTopicRelationRecord(
            relation_id="foreign-chain-bridge",
            source_topic_id="other",
            target_topic_id="qg",
            source_ref=foreign_chain_ref.record_ref,
            target_ref=f"claim:{data['claim'].claim_id}",
            relation_kind="derivation_orientation",
            transfer_rationale="The target may inspect but not inherit trust.",
            applicability_boundary="Only the exact pinned source chain.",
            revalidation_requirements=["target derivation review"],
            status="reviewed",
        ),
    )
    decision_ref = _pin_write(
        data["ws"],
        "scope_revalidation_decisions",
        ScopeRevalidationDecisionRecord(
            decision_id="foreign-chain-revalidation",
            bridge_ref=bridge_ref.record_ref,
            bridge_hash=bridge_ref.content_hash,
            bridge_revision=bridge_ref.revision,
            decision="approved",
            topic_id="qg",
            claim_id=data["claim"].claim_id,
            target_scope_refs=["topic:qg", f"claim:{data['claim'].claim_id}"],
            allowed_operations=["use_imported_derivation_chain"],
            source_refs=[vars(foreign_chain_ref)],
            expires_at="2099-01-01T00:00:00+00:00",
        ),
    )
    monkeypatch.setattr(
        "brain.v5.derivations.assess_execution_scope",
        lambda *args, **kwargs: ExecutionScopeDecision(
            operation="use_imported_derivation_chain",
            consumer_scope=("topic:qg", f"claim:{data['claim'].claim_id}"),
            dependency_refs=(foreign_chain_ref,),
            decision="allowed",
            same_scope_dependency_refs=(),
            foreign_dependency_refs=(foreign_chain_ref,),
            accepted_revalidation_refs=(decision_ref,),
            reasons=("exact reviewed import",),
            checked_refs=(foreign_chain_ref.record_ref,),
            read_errors=(),
        ),
    )
    target_step = record_derivation_step(
        data["ws"],
        _step(
            data,
            step_id="target-import-step",
            sequence=1,
            dependencies=(foreign_step_ref,),
        ),
        actor=_actor(),
    )
    target_step_ref = PinnedRecordRef(
        target_step.record_ref,
        target_step.content_hash,
        target_step.revision,
    )
    binding = {
        "chain_ref": vars(foreign_chain_ref),
        "bridge_ref": vars(bridge_ref),
        "revalidation_decision_ref": vars(decision_ref),
    }
    target_chain = _chain(
        data,
        (target_step_ref,),
        status="in_progress",
        imported=(binding,),
    )
    result = record_derivation_chain(
        data["ws"],
        target_chain,
        actor=_actor(),
    )

    assert result.record_ref.startswith("derivation_chain:")
    assert target_chain.can_update_claim_trust is False

    with pytest.raises(ValueError, match="imported chain must be structurally closed"):
        record_derivation_chain(
            data["ws"],
            replace(target_chain, status="structurally_closed"),
            actor=_actor(),
            expected_current_hash=result.content_hash,
        )

    record_derivation_chain(
        data["ws"],
        replace(foreign_chain, title="Revised foreign draft chain"),
        actor=_actor(),
        expected_current_hash=foreign_chain_ref.content_hash,
    )
    with pytest.raises(ValueError, match="imported chain ref is stale"):
        from brain.v5.derivations import validate_derivation_dag

        validate_derivation_dag(data["ws"], target_chain)


def test_same_topic_foreign_claim_chain_requires_target_local_remapping(tmp_path):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.workspace import create_claim

    data = _fixture(tmp_path)
    other_claim = create_claim(
        data["ws"],
        topic_id="qg",
        statement="A same-topic claim still has claim-local derivation trust.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Target-local remapping is pending.",
    )
    imported_step = DerivationStepRecord(
        step_id="same-topic-foreign-step",
        chain_id="same-topic-foreign-chain",
        topic_id="qg",
        claim_id=other_claim.claim_id,
        sequence=1,
        input_expression="X",
        output_expression="Y",
        justification_type="orientation_only",
        status="draft",
    )
    step_write = record_derivation_step(data["ws"], imported_step, actor=_actor())
    imported_step_ref = PinnedRecordRef(
        step_write.record_ref,
        step_write.content_hash,
        step_write.revision,
    )
    imported_chain = DerivationChainRecord(
        chain_id="same-topic-foreign-chain",
        topic_id="qg",
        claim_id=other_claim.claim_id,
        title="Same-topic foreign claim chain",
        target="Remain claim-local.",
        assumptions=["same-topic scope does not transfer claim trust"],
        conventions=["exact pinned references"],
        framework="same-topic import boundary test",
        regime="orientation only",
        ordered_step_refs=[vars(imported_step_ref)],
        status="in_progress",
    )
    chain_write = record_derivation_chain(data["ws"], imported_chain, actor=_actor())
    imported_chain_ref = PinnedRecordRef(
        chain_write.record_ref,
        chain_write.content_hash,
        chain_write.revision,
    )
    local_step_write = record_derivation_step(
        data["ws"],
        _step(
            data,
            step_id="local-step-with-foreign-claim-dependency",
            sequence=1,
            dependencies=(imported_step_ref,),
        ),
        actor=_actor(),
    )
    local_step_ref = PinnedRecordRef(
        local_step_write.record_ref,
        local_step_write.content_hash,
        local_step_write.revision,
    )
    binding = {"chain_ref": vars(imported_chain_ref)}

    with pytest.raises(ValueError, match="target-local chain"):
        record_derivation_chain(
            data["ws"],
            _chain(data, (local_step_ref,), status="in_progress", imported=(binding,)),
            actor=_actor(),
        )
