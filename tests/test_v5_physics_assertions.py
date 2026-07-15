from __future__ import annotations

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="physics-knowledge-test", host="pytest")


def test_assertion_contract_requires_asset_and_location_grounding():
    from brain.v5.models import PhysicsAssertionRecord
    from brain.v5.physics_knowledge_contracts import validate_physics_assertion

    assertion = PhysicsAssertionRecord(
        assertion_id="assertion-unresolved",
        object_ref="physics_object:algebra-a",
        topic_id="qg",
        predicate="definition",
        value="A source-specific definition.",
        framework="algebraic QFT",
        regime="continuum",
        review_status="reviewed",
    )

    with pytest.raises(ValueError, match="source asset.*source location"):
        validate_physics_assertion(assertion, require_reviewed_grounding=True)


def test_insight_model_is_explicitly_speculative_and_non_evidence():
    from brain.v5.models import InsightRecord

    insight = InsightRecord(
        insight_id="insight-island-analogy",
        insight_kind="analogy",
        statement="The inclusion pattern may be analogous to an island transition.",
        topic_id="qg",
        grounding_refs=["physics_assertion:assertion-a-definition-haag"],
        inferred_from_refs=["derivation_chain:replica-chain"],
        framework="semiclassical gravity",
        regime="replica saddle comparison",
        speculation_level="exploratory",
        falsifiers=["the inclusion fails after target-side reconstruction"],
        review_status="reviewed",
    )

    assert insight.insight_kind == "analogy"
    assert insight.can_update_claim_trust is False
    assert insight.evidence_role == "forbidden"

    with pytest.raises(ValueError, match="insight_kind"):
        InsightRecord(
            insight_id="insight-invalid",
            insight_kind="established_fact",
            statement="This must not enter the insight lane.",
            topic_id="qg",
        )


def test_procedural_skill_distillation_explicitly_excludes_m3_knowledge_families(tmp_path):
    from brain.v5.skill_distillation import build_procedural_skill_candidates
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")

    report = build_procedural_skill_candidates(ws, topic_id="qg")

    assert {
        "physics_assertion",
        "insight",
        "derivation_chain",
        "derivation_step",
        "derivation_review",
    }.issubset(set(report["excluded_record_kinds"]))


def test_assertion_writer_rejects_unresolved_grounding_before_write(tmp_path):
    from brain.v5.models import PhysicsAssertionRecord
    from brain.v5.physics_assertions import record_physics_assertion
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    assertion = PhysicsAssertionRecord(
        assertion_id="assertion-unresolved",
        object_ref="physics_object:missing",
        topic_id="qg",
        predicate="definition",
        value="An unresolved assertion.",
        source_asset_refs=["source_asset:missing"],
        source_location_refs=["reference_location:missing"],
        review_status="reviewed",
    )

    with pytest.raises(ValueError, match="does not resolve"):
        record_physics_assertion(ws, assertion, actor=_actor())
    assert not (ws.registry_dir("physics_assertions") / "assertion-unresolved.md").exists()


def test_assertion_writer_persists_exact_grounded_v2_record(tmp_path):
    from brain.v5.models import (
        PhysicsAssertionRecord,
        PhysicsObjectRecord,
        ReferenceLocationRecord,
        SourceAssetRecord,
    )
    from brain.v5.physics_assertions import record_physics_assertion
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    repository = RecordRepository(ws, actor=_actor())
    repository.write(
        "physics_objects",
        PhysicsObjectRecord("algebra-a", "qg", "operator_algebra", "A", ""),
    )
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="haag-book",
            topic_id="qg",
            asset_type="book",
            uri="file:///sources/haag.pdf",
            title="Local Quantum Physics",
            content_hash="a" * 64,
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id="haag-local-algebra",
            topic_id="qg",
            connector_id="local-source",
            location_type="page_anchor",
            uri="file:///sources/haag.pdf#page=101",
            label="Local algebra definition",
            source_ref="source_asset:haag-book",
        ),
    )
    assertion = PhysicsAssertionRecord(
        assertion_id="assertion-a-definition-haag",
        object_ref="physics_object:algebra-a",
        topic_id="qg",
        predicate="definition",
        value="The algebra generated by observables localized in O.",
        framework="algebraic QFT",
        regime="continuum",
        source_asset_refs=["source_asset:haag-book"],
        source_location_refs=["reference_location:haag-local-algebra"],
        review_status="reviewed",
    )

    result = record_physics_assertion(ws, assertion, actor=_actor())
    loaded = repository.read(result.record_ref)

    assert result.record_ref == "physics_assertion:assertion-a-definition-haag"
    assert loaded.status == "found"
    assert loaded.frontmatter["schema_version"] == "v2"
    assert loaded.frontmatter["trust_effect"] == "none"
    assert loaded.record == assertion
