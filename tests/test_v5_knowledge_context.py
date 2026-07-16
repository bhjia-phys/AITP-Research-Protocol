from __future__ import annotations

from dataclasses import replace

import pytest


def _context_workspace(tmp_path):
    from brain.v5.physics_knowledge_models import InsightRecord, PhysicsAssertionRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from tests.test_v5_curated_rag_source_shelf import _built_shelf

    ws, shelf_report, source_ref, _blob, location = _built_shelf(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="knowledge-context-test",
            host="pytest",
        ),
    )
    assertion = repository.write(
        "physics_assertions",
        PhysicsAssertionRecord(
            assertion_id="qg-generalized-entropy-context",
            object_ref="physics_object:qg-island",
            topic_id="qg",
            predicate="defined_by",
            value="area plus bulk entropy",
            expression="S_gen = A/(4 G_N) + S_bulk",
            framework="semiclassical gravity",
            regime="island formula",
            conventions=["hbar-one"],
            assumptions=["semiclassical bulk effective field theory"],
            non_claims=["not a microscopic entropy formula"],
            source_asset_refs=[source_ref],
            source_location_refs=[f"reference_location:{location.location_id}"],
            review_status="reviewed",
        ),
    )
    insight = repository.write(
        "insights",
        InsightRecord(
            insight_id="qg-generalized-entropy-ensemble-insight",
            insight_kind="analogy",
            statement=(
                "Generalized entropy may organize an ensemble-averaging analogy."
            ),
            topic_id="qg",
            grounding_refs=[assertion.record_ref],
            inferred_from_refs=[assertion.record_ref],
            framework="semiclassical gravity",
            regime="island formula",
            speculation_level="exploratory",
            falsifiers=["a fixed-theory derivation without averaging"],
        ),
    )
    build_query_index(ws)
    return ws, shelf_report, assertion, insight


def test_normal_knowledge_context_separates_grounded_source_and_insight_with_budget(
    tmp_path,
):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )

    ws, shelf_report, assertion, insight = _context_workspace(tmp_path)
    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="generalized entropy area bulk ensemble analogy",
            topic_id="qg",
            framework="semiclassical gravity",
            regime="island formula",
            conventions=("hbar-one",),
            intent="insight",
            mode="normal",
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
            max_results=8,
        ),
    )

    by_ref = {entry.record_ref: entry for entry in result.entries}
    assert assertion.record_ref in by_ref
    assert insight.record_ref in by_ref
    assert by_ref[assertion.record_ref].knowledge_lane == "grounded"
    assert by_ref[assertion.record_ref].scope_lane == "primary"
    assert by_ref[assertion.record_ref].grounding_state == "reviewed_grounded"
    assert by_ref[assertion.record_ref].framework_compatibility == "compatible"
    assert by_ref[assertion.record_ref].exact_expansion["content_hash"]
    assert by_ref[insight.record_ref].knowledge_lane == "insight"
    assert by_ref[insight.record_ref].grounding_state == "speculative_non_evidence"
    assert by_ref[insight.record_ref].speculation_level == "exploratory"
    assert "## Grounded knowledge" in result.markdown
    assert "## Source passages" in result.markdown
    assert "## Speculative insight" in result.markdown
    assert result.snapshot_lineage["scope_content_verified"] is True
    assert result.coverage["component_statuses"]["dense"] == "absent"
    assert result.token_allocation["used_tokens"] == result.estimated_tokens
    assert result.estimated_tokens <= result.max_tokens <= 1500
    assert result.byte_count <= result.max_bytes
    assert result.orientation_only is True
    assert result.can_update_claim_trust is False


def test_startup_knowledge_context_stays_under_800_tokens(tmp_path):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )

    ws, shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="generalized entropy",
            topic_id="qg",
            framework="semiclassical gravity",
            regime="island formula",
            mode="startup",
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    assert result.mode == "startup"
    assert result.estimated_tokens <= result.max_tokens <= 800
    assert result.coverage["pagination"]["limit"] <= 4
    assert result.snapshot_lineage["freshness_mode"] == "orientation"
    assert result.snapshot_lineage["scope_content_verified"] is False
    assert result.coverage["complete"] is False
    assert result.partial is True
    assert result.can_update_claim_trust is False


def test_exact_source_equation_expansion_binds_generation_and_canonical_location(
    tmp_path,
):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )

    ws, shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    equation = next(
        passage
        for passage in shelf_report.shelf.passages
        if "equation" in passage.anchor_kinds
    )
    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="",
            topic_id="qg",
            mode="exact_expansion",
            exact_refs=(equation.passage_id,),
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    assert [entry.record_ref for entry in result.entries] == [equation.passage_id]
    handle = result.entries[0].exact_expansion
    assert handle["kind"] == "source_equation"
    assert handle["source_passage_ref"] == equation.passage_id
    assert handle["source_asset_ref"] == equation.source_asset_ref
    assert handle["source_location_refs"] == list(equation.source_location_refs)
    assert handle["source_shelf_generation"] == shelf_report.manifest.generation
    assert handle["source_shelf_passages_hash"]
    assert handle["text_hash"] == equation.text_hash
    assert result.can_update_claim_trust is False


def test_exact_knowledge_expansion_preserves_requested_order_and_pagination(
    tmp_path,
):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )

    ws, shelf_report, assertion, insight = _context_workspace(tmp_path)
    passage_ref = shelf_report.shelf.passages[0].passage_id
    requested = (passage_ref, assertion.record_ref, insight.record_ref)
    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="",
            topic_id="qg",
            mode="exact_expansion",
            exact_refs=requested,
            page_offset=1,
            max_results=1,
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    assert [entry.record_ref for entry in result.entries] == [assertion.record_ref]
    assert result.entries[0].exact_expansion["kind"] == "physics_assertion"
    assert result.coverage["pagination"] == {
        "offset": 1,
        "limit": 1,
        "returned": 1,
        "total_observed": 3,
        "total_exact": True,
        "not_shown_observed": 1,
        "has_more": True,
        "next_offset": 2,
    }
    assert result.coverage["truncated"] is True
    assert result.partial is True


def test_knowledge_context_exposes_component_failure_quotas_and_render_omissions(
    tmp_path,
):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )
    from brain.v5.physics_knowledge_models import InsightRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from tests.test_v5_knowledge_retrieval_resilience import _TimeoutDenseAdapter

    ws, shelf_report, assertion, _insight = _context_workspace(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="knowledge-context-budget-test",
            host="pytest",
        ),
    )
    candidate_refs = []
    for index in range(5):
        written = repository.write(
            "insights",
            InsightRecord(
                insight_id=f"budget-insight-{index}",
                insight_kind="analogy",
                statement=(
                    "Generalized entropy ensemble analogy budget candidate "
                    f"{index}."
                ),
                topic_id="qg",
                grounding_refs=[assertion.record_ref],
                inferred_from_refs=[assertion.record_ref],
                framework="semiclassical gravity",
                regime="island formula",
                speculation_level="exploratory",
            ),
        )
        candidate_refs.append(written.record_ref)
    build_query_index(ws)

    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="generalized entropy ensemble analogy budget candidate",
            topic_id="qg",
            framework="semiclassical gravity",
            regime="island formula",
            intent="insight",
            mode="normal",
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
            max_tokens=128,
            max_results=12,
        ),
        dense_adapter=_TimeoutDenseAdapter(),
    )

    assert result.coverage["component_statuses"]["dense"] == "degraded"
    assert "dense adapter failed: fixture timeout" in result.coverage["errors"]
    assert result.coverage["lane_quotas"]["insight"] == 2
    assert set(candidate_refs) & set(result.coverage["not_shown_refs"])
    assert result.not_shown_refs
    assert result.coverage["render_not_shown_refs"] == list(result.not_shown_refs)
    assert result.coverage["render_not_shown_count"] == len(result.not_shown_refs)
    assert result.partial is True
    assert result.can_update_claim_trust is False


def test_knowledge_context_contract_rejects_trust_mutation(tmp_path):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )
    from brain.v5.knowledge_context_contracts import require_valid_knowledge_context

    ws, shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="generalized entropy",
            topic_id="qg",
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    assert require_valid_knowledge_context(result) is result
    with pytest.raises(ValueError, match="cannot update claim trust"):
        require_valid_knowledge_context(
            replace(result, can_update_claim_trust=True)
        )
    with pytest.raises(ValueError, match="entry cannot update claim trust"):
        require_valid_knowledge_context(
            replace(
                result,
                entries=(replace(result.entries[0], can_update_claim_trust=True),),
            )
        )


def test_exact_expansion_kinds_cover_typed_knowledge_and_derivation_records(
    tmp_path,
):
    from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )
    from brain.v5.physics_knowledge_models import PhysicsObjectRecord, ObjectRelationRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws, shelf_report, assertion, insight = _context_workspace(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="knowledge-context-kind-test",
            host="pytest",
        ),
    )
    physics_object = repository.write(
        "physics_objects",
        PhysicsObjectRecord(
            object_id="qg-replica-index",
            topic_id="qg",
            object_type="index",
            name="replica index",
            definition="The integer replica number before continuation.",
            notation="n",
            knowledge_role="grounded_knowledge",
            canonical_name="replica index",
            review_status="reviewed",
        ),
    )
    relation = repository.write(
        "object_relations",
        ObjectRelationRecord(
            relation_id="qg-replica-controls-entropy",
            topic_id="qg",
            relation_type="controls",
            subject_id="qg-replica-index",
            object_id="qg-island",
            statement="Replica continuation controls the entropy extraction.",
            subject_ref=physics_object.record_ref,
            object_ref="physics_object:qg-island",
            framework="replica path integral",
            regime="semiclassical saddle",
            review_status="reviewed",
        ),
    )
    step = repository.write(
        "derivation_steps",
        DerivationStepRecord(
            step_id="qg-replica-step",
            chain_id="qg-replica-chain",
            topic_id="qg",
            claim_id="knowledge-context-claim",
            sequence=1,
            input_expression="Z_n",
            output_expression="S = -partial_n log Z_n|_{n=1}",
            justification_type="replica_identity",
            invoked_knowledge_refs=[{"record_ref": physics_object.record_ref}],
            status="established",
        ),
    )
    chain = repository.write(
        "derivation_chains",
        DerivationChainRecord(
            chain_id="qg-replica-chain",
            topic_id="qg",
            claim_id="knowledge-context-claim",
            title="Replica entropy extraction",
            target="Extract entropy from the replica partition function.",
            assumptions=["analytic continuation near n=1"],
            conventions=["Euclidean signature"],
            framework="replica path integral",
            regime="semiclassical saddle",
            ordered_step_refs=[{"record_ref": step.record_ref}],
            status="in_progress",
        ),
    )
    build_query_index(ws)
    source_pin = shelf_report.manifest.source_pins[0]
    location_ref = source_pin.source_location_pins[0].record_ref
    requested = (
        source_pin.source_asset_ref,
        location_ref,
        physics_object.record_ref,
        relation.record_ref,
        chain.record_ref,
        step.record_ref,
        insight.record_ref,
        assertion.record_ref,
    )

    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="",
            topic_id="qg",
            mode="exact_expansion",
            exact_refs=requested,
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    kinds = {
        entry.record_ref: entry.exact_expansion["kind"] for entry in result.entries
    }
    assert kinds == {
        source_pin.source_asset_ref: "source_asset",
        location_ref: "reference_location",
        physics_object.record_ref: "physics_object",
        relation.record_ref: "object_relation",
        chain.record_ref: "derivation_chain",
        step.record_ref: "derivation_step",
        insight.record_ref: "insight",
        assertion.record_ref: "physics_assertion",
    }


def test_exact_expansion_classifies_shared_scope_and_blocks_foreign_insight(
    tmp_path,
):
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )
    from brain.v5.physics_knowledge_models import InsightRecord, PhysicsAssertionRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws, shelf_report, local_assertion, _local_insight = _context_workspace(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="knowledge-context-scope-test",
            host="pytest",
        ),
    )
    source_pin = shelf_report.manifest.source_pins[0]
    location_ref = source_pin.source_location_pins[0].record_ref
    shared = repository.write(
        "physics_assertions",
        PhysicsAssertionRecord(
            assertion_id="shared-reviewed-assertion",
            object_ref="physics_object:foreign-object",
            topic_id="foreign-qg-topic",
            program_id="qg-program",
            predicate="related_to",
            value="reviewed shared result",
            framework="semiclassical gravity",
            regime="island formula",
            source_asset_refs=[source_pin.source_asset_ref],
            source_location_refs=[location_ref],
            review_status="reviewed",
        ),
    )
    foreign_insight = repository.write(
        "insights",
        InsightRecord(
            insight_id="foreign-local-insight",
            insight_kind="analogy",
            statement="Foreign topic-local speculative analogy.",
            topic_id="foreign-qg-topic",
            program_id="qg-program",
            grounding_refs=[shared.record_ref],
            inferred_from_refs=[shared.record_ref],
        ),
    )
    build_query_index(ws)

    result = compile_knowledge_context(
        ws,
        KnowledgeContextRequest(
            query_text="",
            topic_id="qg",
            program_id="qg-program",
            mode="exact_expansion",
            exact_refs=(
                local_assertion.record_ref,
                shared.record_ref,
                foreign_insight.record_ref,
            ),
            source_shelf_generation=shelf_report.manifest.generation,
            source_shelf_topic_id="qg",
        ),
    )

    by_ref = {entry.record_ref: entry for entry in result.entries}
    assert by_ref[local_assertion.record_ref].scope_lane == "primary"
    assert by_ref[shared.record_ref].scope_lane == "shared"
    assert by_ref[shared.record_ref].orientation_only is True
    assert foreign_insight.record_ref not in by_ref
    assert result.coverage["blocked_refs"] == [foreign_insight.record_ref]
    assert result.coverage["excluded_scope"]["foreign_insight_excluded"] == 1
    assert result.partial is True
    assert result.can_update_claim_trust is False


def test_exact_formula_code_expansion_exposes_formula_and_code_state_refs(tmp_path):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.knowledge_context import (
        KnowledgeContextRequest,
        compile_knowledge_context,
    )
    from brain.v5.query_index import build_query_index
    from tests.test_v5_formula_code_map import _actor, _fixture, _relation

    data = _fixture(tmp_path)
    relation = record_formula_code_relation(
        data["ws"],
        _relation(data),
        actor=_actor(),
    )
    build_query_index(data["ws"])

    result = compile_knowledge_context(
        data["ws"],
        KnowledgeContextRequest(
            query_text="",
            topic_id="librpa",
            mode="exact_expansion",
            exact_refs=(relation.record_ref,),
        ),
    )

    handle = result.entries[0].exact_expansion
    assert handle["kind"] == "formula_code_relation"
    assert handle["formula_ref"] == data["formula_ref"].record_ref
    assert handle["code_state_ref"] == data["code_ref"].record_ref
    assert handle["edge_types"][data["formula_ref"].record_ref] == [
        "formula_code_formula"
    ]
    assert handle["edge_types"][data["code_ref"].record_ref] == [
        "formula_code_code_state"
    ]
    assert result.entries[0].orientation_only is True
    assert result.can_update_claim_trust is False


def _bind_knowledge_context_session(ws):
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import bind_session

    bind_session(
        ws,
        "session-qg-knowledge",
        topic_id="qg",
        context_id="formal-theory",
    )
    build_query_index(ws)


def test_unified_context_compiler_skips_knowledge_without_explicit_focus(
    tmp_path,
    monkeypatch,
):
    from brain.v5 import knowledge_context
    from brain.v5.context_compiler import ContextRequest, compile_research_context

    ws, _shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    _bind_knowledge_context_session(ws)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("knowledge retrieval ran without an explicit focus")

    monkeypatch.setattr(
        knowledge_context,
        "compile_knowledge_context",
        fail_if_called,
    )

    bundle = compile_research_context(
        ws,
        ContextRequest(session_id="session-qg-knowledge"),
    )

    assert bundle.knowledge_context == {}
    assert bundle.coverage["knowledge_context_requested"] is False


def test_unified_context_compiler_embeds_requested_bounded_knowledge_slice(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle
    from brain.v5.knowledge_context import KnowledgeContextRequest

    ws, shelf_report, assertion, insight = _context_workspace(tmp_path)
    _bind_knowledge_context_session(ws)
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-qg-knowledge",
            objective_text="Check generalized entropy and its ensemble analogy.",
            knowledge_request=KnowledgeContextRequest(
                query_text="generalized entropy area bulk ensemble analogy",
                topic_id="qg",
                framework="semiclassical gravity",
                regime="island formula",
                conventions=("hbar-one",),
                intent="insight",
                source_shelf_generation=shelf_report.manifest.generation,
                source_shelf_topic_id="qg",
            ),
            max_tokens=1500,
            max_bytes=9000,
        ),
    )

    knowledge = bundle.knowledge_context
    refs = {entry["record_ref"] for entry in knowledge["entries"]}
    assert {assertion.record_ref, insight.record_ref} <= refs
    assert knowledge["estimated_tokens"] <= knowledge["max_tokens"] <= 1500
    assert knowledge["snapshot_lineage"]["scope_content_verified"] is True
    assert bundle.coverage["knowledge_context_requested"] is True
    assert bundle.coverage["knowledge_context_partial"] == knowledge["partial"]
    assert "## Physics knowledge slice" in bundle.markdown
    assert bundle.estimated_tokens <= bundle.max_tokens
    assert bundle.byte_count <= bundle.max_bytes
    assert bundle.orientation_only is True
    assert bundle.can_update_claim_trust is False
    assert validate_context_bundle(bundle) == ()
    tampered = replace(
        bundle,
        knowledge_context={**knowledge, "can_update_claim_trust": True},
    )
    assert "knowledge context cannot update claim trust" in validate_context_bundle(
        tampered
    )


def test_paper_learning_context_pack_requests_knowledge_only_with_objective(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.context_pack_contracts import validate_aitp_context_pack

    ws, shelf_report, assertion, _insight = _context_workspace(tmp_path)
    _bind_knowledge_context_session(ws)
    without_objective = build_aitp_context_pack(
        ws,
        "session-qg-knowledge",
        task_profile="paper_learning",
    )
    with_objective = build_aitp_context_pack(
        ws,
        "session-qg-knowledge",
        task_profile="paper_learning",
        objective_text="Recover the generalized entropy definition and source equation.",
        knowledge_framework="semiclassical gravity",
        knowledge_regime="island formula",
        knowledge_source_shelf_generation=shelf_report.manifest.generation,
        knowledge_source_shelf_topic_id="qg",
    )

    assert without_objective["knowledge_context"] == {}
    assert with_objective["knowledge_context"]["mode"] == "normal"
    assert assertion.record_ref in {
        entry["record_ref"] for entry in with_objective["knowledge_context"]["entries"]
    }
    assert "knowledge_context" in with_objective["source_records"]["derived_surfaces"]
    assert any(
        line.startswith("Physics knowledge:")
        for line in with_objective["context_lines"]
    )
    assert with_objective["estimated_tokens"] <= with_objective["context_budget"][
        "max_tokens"
    ]
    assert with_objective["can_update_claim_trust"] is False
    assert validate_aitp_context_pack(with_objective).ok is True
    tampered = {
        **with_objective,
        "knowledge_context": {
            **with_objective["knowledge_context"],
            "can_update_claim_trust": True,
        },
    }
    validation = validate_aitp_context_pack(tampered)
    assert any(
        issue.path.endswith("knowledge_context.can_update_claim_trust")
        for issue in validation.issues
    )


def test_theory_context_profiles_declare_bounded_knowledge_context_surface():
    from brain.v5.context_profiles import builtin_context_profiles

    profiles = builtin_context_profiles()
    for profile_id in (
        "paper_learning",
        "paired_paper_learning",
        "multi_paper_learning_route",
        "derivation_check",
    ):
        profile = profiles[profile_id]
        assert "physics_knowledge_context" in profile.include_sections
        assert "knowledge_context" in profile.recommended_surfaces
