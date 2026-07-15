from __future__ import annotations


def _candidate(*kinds: str, **overrides):
    from brain.v5.knowledge_candidates import KnowledgeCandidate

    values = {
        "candidate_id": "candidate-1",
        "content_kinds": kinds,
        "statement": "Candidate statement.",
    }
    values.update(overrides)
    return KnowledgeCandidate(**values)


def _grounding_fixture(tmp_path):
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="knowledge-candidate-test", host="pytest"),
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
    return ws, (
        pin_current_record(ws, "source_asset:haag-book"),
        pin_current_record(ws, "reference_location:haag-local-algebra"),
    )


def test_grounded_physics_content_routes_to_knowledge_not_skill():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    for kind in ("definition", "formula", "convention", "relation", "derivation"):
        route = route_knowledge_candidate(_candidate(kind))
        assert route.lane == "grounded_knowledge"
        assert route.eligible_for_skill is False
        assert route.can_update_claim_trust is False


def test_interpretive_content_routes_to_non_evidence_insight():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    for kind in (
        "interpretation",
        "analogy",
        "conjecture",
        "failed_route_lesson",
        "counterexample_direction",
        "conceptual_bridge",
        "open_research_direction",
    ):
        route = route_knowledge_candidate(_candidate(kind))
        assert route.lane == "speculative_insight"
        assert route.evidence_role == "forbidden"
        assert route.eligible_for_skill is False


def test_only_complete_procedural_workflow_can_route_to_skill_review():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    incomplete = route_knowledge_candidate(_candidate("procedural_workflow"))
    complete = route_knowledge_candidate(
        _candidate(
            "procedural_workflow",
            procedural_steps=("prepare input", "run solver", "validate output"),
            validation_refs=("validation_result:solver-pass",),
            applicability_boundary="LibRPA QSGW run with matching code and environment pins.",
        )
    )

    assert incomplete.lane == "procedural_skill"
    assert incomplete.eligible_for_skill is False
    assert complete.eligible_for_skill is True
    assert complete.requires_human_review is True


def test_mixed_physics_and_workflow_candidate_requires_explicit_split():
    from brain.v5.knowledge_candidates import route_knowledge_candidate

    route = route_knowledge_candidate(
        _candidate(
            "formula",
            "procedural_workflow",
            procedural_steps=("run solver",),
            validation_refs=("validation_result:solver-pass",),
            applicability_boundary="bounded fixture",
        )
    )

    assert route.lane == "mixed_split_required"
    assert route.split_required is True
    assert route.eligible_for_skill is False
    assert set(route.target_lanes) == {"grounded_knowledge", "procedural_skill"}


def test_grounded_candidate_requires_exact_asset_and_location_pins(tmp_path):
    from brain.v5.knowledge_candidates import diagnose_knowledge_candidate

    ws, pins = _grounding_fixture(tmp_path)
    missing = diagnose_knowledge_candidate(
        ws,
        _candidate("definition", topic_id="qg", source_refs=("source_asset:haag-book",)),
    )
    grounded = diagnose_knowledge_candidate(
        ws,
        _candidate("definition", topic_id="qg", grounding_pins=pins),
    )

    assert missing.eligible_for_grounded_review is False
    assert set(missing.missing_requirements) == {
        "exact_source_asset_pin",
        "exact_source_location_pin",
    }
    assert grounded.eligible_for_grounded_review is True
    assert grounded.checked_refs == (
        "source_asset:haag-book",
        "reference_location:haag-local-algebra",
    )


def test_grounded_candidate_rejects_location_bound_to_another_asset(tmp_path):
    from dataclasses import replace

    from brain.v5.knowledge_candidates import diagnose_knowledge_candidate
    from brain.v5.models import ReferenceLocationRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef, pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy

    ws, pins = _grounding_fixture(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="knowledge-candidate-test", host="pytest"),
    )
    old_location = repository.read("reference_location:haag-local-algebra")
    revised = replace(old_location.record, source_ref="source_asset:another-book")
    result = repository.write(
        "reference_locations",
        revised,
        policy=WritePolicy(
            mode="revision",
            expected_hash=old_location.frontmatter["record_content_hash"],
        ),
    )
    revised_pin = PinnedRecordRef(result.record_ref, result.content_hash, result.revision)

    diagnostics = diagnose_knowledge_candidate(
        ws,
        _candidate("definition", topic_id="qg", grounding_pins=(pins[0], revised_pin)),
    )

    assert diagnostics.eligible_for_grounded_review is False
    assert "source_location_asset_mismatch" in diagnostics.errors
