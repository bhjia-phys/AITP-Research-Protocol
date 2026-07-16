from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "v5_retrieval"


def _fixture():
    from brain.v5.knowledge_snapshot import (
        KnowledgeSnapshotLineage,
        knowledge_snapshot_from_rows,
    )

    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    queries = json.loads(
        (FIXTURE_DIR / "qft_qg_queries.json").read_text(encoding="utf-8")
    )["queries"]
    lineage = KnowledgeSnapshotLineage(
        query_index_generation=7,
        query_index_delta_generation=2,
        query_index_content_hash="b" * 64,
        selected_family_state_tokens={"physics_assertions": "c" * 64},
        selected_family_content_watermarks={"physics_assertions": "d" * 64},
        source_shelf_generation="e" * 64,
        source_shelf_passages_hash="f" * 64,
        source_shelf_topic_id="qg",
        scope_fresh=True,
        scope_content_verified=True,
        dirty_families=(),
        errors=(),
    )
    snapshot = knowledge_snapshot_from_rows(manifest["documents"], lineage=lineage)
    return manifest, queries, snapshot


def _query(row):
    from brain.v5.knowledge_retrieval import KnowledgeQuery

    return KnowledgeQuery(
        text=row["text"],
        topic_id=row["topic_id"],
        framework=row.get("framework", ""),
        regime=row.get("regime", ""),
        conventions=tuple(row.get("conventions", [])),
        formula=row.get("formula", ""),
        intent=row.get("intent", "default"),
        seed_refs=tuple(row.get("seed_refs", [])),
        max_results=6,
    )


def test_retrieval_fixture_freezes_policy_and_thresholds_before_ranking_code():
    manifest, queries, snapshot = _fixture()

    assert manifest["schema_version"] == "aitp.v5.knowledge-retrieval-fixture.v1"
    assert manifest["policy"]["lexical"]["version"] == "fielded-bm25.v1"
    assert manifest["policy"]["fusion"]["rrf_k"] == 60
    assert manifest["acceptance_thresholds"]["wrong_framework_contamination"] == 0.0
    assert len(queries) == 4
    assert snapshot.lineage.snapshot_hash
    assert all(item.record_ref and item.record_hash for item in snapshot.items)


def test_knowledge_snapshot_rejects_non_digest_record_identity():
    from brain.v5.knowledge_snapshot import knowledge_snapshot_from_rows

    _manifest, _queries, snapshot = _fixture()
    row = {
        "record_ref": "physics_assertion:qg-invalid-hash",
        "record_hash": "not-a-sha256",
        "revision": 1,
        "family": "physics_assertions",
        "topic_id": "qg",
        "lane": "grounded",
        "fields": {"statement": ["A row without exact identity."]},
    }

    import pytest

    with pytest.raises(ValueError, match="record_hash must be a sha256 digest"):
        knowledge_snapshot_from_rows(
            (row,),
            lineage=replace(snapshot.lineage, snapshot_hash=""),
        )


def test_knowledge_snapshot_lineage_requires_exact_generations_and_watermarks():
    from brain.v5.knowledge_snapshot import KnowledgeSnapshotLineage

    import pytest

    with pytest.raises(ValueError, match="query index content hash"):
        KnowledgeSnapshotLineage(
            query_index_generation=1,
            query_index_delta_generation=0,
            query_index_content_hash="not-a-digest",
            selected_family_state_tokens={"physics_assertions": "b" * 64},
            selected_family_content_watermarks={"physics_assertions": "c" * 64},
            scope_fresh=True,
            scope_content_verified=True,
        )
    with pytest.raises(ValueError, match="selected-family lineage keys"):
        KnowledgeSnapshotLineage(
            query_index_generation=1,
            query_index_delta_generation=0,
            query_index_content_hash="a" * 64,
            selected_family_state_tokens={"physics_assertions": "b" * 64},
            selected_family_content_watermarks={"physics_objects": "c" * 64},
            scope_fresh=True,
            scope_content_verified=True,
        )


def test_fielded_lexical_is_deterministic_and_filters_wrong_framework():
    from brain.v5.knowledge_retrieval import search_fielded_lexical

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    first = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    second = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])

    assert first == second
    assert first.status == "available"
    assert first.hits[0].record_ref == "physics_assertion:qg-generalized-entropy"
    assert first.hits[0].field_scores["canonical_name"] > 0
    assert "physics_assertion:qg-worldsheet-entropy" not in {
        hit.record_ref for hit in first.hits
    }
    assert first.coverage["wrong_framework_excluded"] == 1
    assert first.coverage["corpus_statistics"]["canonical_name"][
        "document_count"
    ] == first.coverage["eligible_items"]
    assert first.coverage["corpus_statistics"]["canonical_name"][
        "average_document_length"
    ] >= 0
    assert first.coverage["tie_handling"] == "score_desc_then_record_ref"
    assert first.deterministic is True
    assert first.can_update_claim_trust is False


def test_formula_normalization_preserves_sign_and_convention():
    from brain.v5.formula_retrieval import normalize_formula, search_formula

    manifest, queries, snapshot = _fixture()
    query = _query(queries[1])
    result = search_formula(snapshot, query, manifest["policy"]["formula"])
    repeated = search_formula(snapshot, query, manifest["policy"]["formula"])

    assert normalize_formula("$ K_ab = h_a^c h_b^d \\nabla_c n_d $") == normalize_formula(
        "K_ab=h_a^c h_b^d \\nabla_c n_d"
    )
    assert normalize_formula("K_ab = - h_a^c h_b^d nabla_c n_d") != normalize_formula(
        "K_ab = h_a^c h_b^d nabla_c n_d"
    )
    assert result.hits[0].record_ref == "physics_assertion:qg-extrinsic-curvature-plus"
    assert "physics_assertion:qg-extrinsic-curvature-minus" not in {
        hit.record_ref for hit in result.hits
    }
    assert result.hits[0].anchors["normalized_formula"]
    assert result.coverage["projection_source"] == "bounded_snapshot_formula_fields"
    assert result.coverage["sidecar_status"] == "not_configured"
    assert repeated == result


def test_formula_retrieval_uses_only_explicit_dummy_and_commutative_declarations():
    from brain.v5.formula_retrieval import normalize_formula, search_formula
    from brain.v5.knowledge_retrieval import KnowledgeQuery
    from brain.v5.knowledge_snapshot import knowledge_snapshot_from_rows

    manifest, _queries, snapshot = _fixture()
    documents = [
        *manifest["documents"],
        {
            "record_ref": "physics_assertion:qg-explicit-formula-equivalence",
            "record_hash": "a1" * 32,
            "revision": 1,
            "family": "physics_assertions",
            "topic_id": "qg",
            "program_id": "qg-program",
            "lane": "grounded",
            "framework": "semiclassical gravity",
            "regime": "formula test",
            "conventions": [],
            "fields": {"formula": ["T_j = B * A_j"]},
            "links": [],
        },
    ]
    formula_snapshot = knowledge_snapshot_from_rows(
        documents,
        lineage=replace(snapshot.lineage, snapshot_hash=""),
    )
    query = KnowledgeQuery(
        text="",
        formula="T_i = A_i * B",
        topic_id="qg",
        framework="semiclassical gravity",
        regime="formula test",
        formula_dummy_symbols=(("i", "dummy"), ("j", "dummy")),
        formula_commutative_product_safe=True,
    )

    result = search_formula(formula_snapshot, query, manifest["policy"]["formula"])

    assert normalize_formula("T_i=A_i", dummy_symbols={"i": "dummy"}) == (
        normalize_formula("T_j=A_j", dummy_symbols={"j": "dummy"})
    )
    assert result.hits[0].record_ref == (
        "physics_assertion:qg-explicit-formula-equivalence"
    )
    assert result.hits[0].field_scores["formula_exact"] == 1.0
    assert result.hits[0].anchors["dummy_symbols"] == {
        "i": "dummy",
        "j": "dummy",
    }
    assert result.hits[0].anchors["commutative_product_safe"] is True


def test_typed_graph_recovers_dependency_with_bounded_paths():
    from brain.v5.graph_retrieval import search_graph

    manifest, queries, snapshot = _fixture()
    query = _query(queries[2])
    result = search_graph(snapshot, query, manifest["policy"]["graph"])
    repeated = search_graph(snapshot, query, manifest["policy"]["graph"])
    refs = [hit.record_ref for hit in result.hits]

    assert refs[:2] == [
        "object_relation:qg-island-extremizes",
        "derivation_step:qg-qes-variation",
    ]
    assert result.hits[0].path == (
        "physics_object:qg-island",
        "object_relation:qg-island-extremizes",
    )
    assert result.hits[0].anchors["edge_path"] == ["object_relation"]
    assert result.hits[1].anchors["edge_path"] == [
        "object_relation",
        "derivation_dependency",
    ]
    assert all(len(hit.path) <= 3 for hit in result.hits)
    assert result.coverage["max_depth"] == 2
    assert result.coverage["truncated"] is False
    assert result.coverage["projection_source"] == "bounded_snapshot_typed_edges"
    assert result.coverage["sidecar_status"] == "not_configured"
    assert repeated == result


def test_fusion_preserves_lanes_lineage_and_repeatability():
    from brain.v5.formula_retrieval import search_formula
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_retrieval import (
        evaluate_ranked_refs,
        search_fielded_lexical,
    )
    from brain.v5.retrieval_fusion import (
        fuse_knowledge_rankings,
        search_dense_optional,
    )

    manifest, queries, snapshot = _fixture()
    row = queries[0]
    query = _query(row)
    components = (
        search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"]),
        search_formula(snapshot, query, manifest["policy"]["formula"]),
        search_graph(snapshot, query, manifest["policy"]["graph"]),
        search_dense_optional(snapshot, query),
    )
    first = fuse_knowledge_rankings(components, query, manifest["policy"]["fusion"])
    second = fuse_knowledge_rankings(components, query, manifest["policy"]["fusion"])
    metrics = evaluate_ranked_refs(
        [hit.record_ref for hit in first.hits],
        row["judgments"],
        k=3,
    )

    assert first == second
    assert first.coverage.snapshot_compatible is True
    assert first.coverage.complete is True
    assert first.coverage.checked_scope["components"]["lexical"][
        "component_hash"
    ] == components[0].component_hash
    assert first.coverage.checked_scope["components"]["lexical"][
        "snapshot_hash"
    ] == snapshot.lineage.snapshot_hash
    assert first.coverage.checked_scope["ordering_policy"] == (
        "scope_lane_then_rrf_score_then_record_ref"
    )
    assert first.coverage.excluded_scope["wrong_framework_excluded"] == 1
    assert first.hits[0].lane == "grounded"
    assert all(hit.lane != "insight" for hit in first.hits)
    assert components[-1].status == "absent"
    assert metrics["recall_at_k"] >= manifest["acceptance_thresholds"]["recall_at_3"]
    assert metrics["mrr"] >= manifest["acceptance_thresholds"]["mrr"]
    assert first.can_claim_no_result is False
    assert first.can_update_claim_trust is False


def test_fusion_marks_incompatible_component_lineage_incomplete():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    lexical = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    incompatible = replace(
        lexical,
        component="formula",
        snapshot_hash="0" * 64,
        component_hash="1" * 64,
        hits=tuple(replace(hit, component="formula") for hit in lexical.hits),
    )
    result = fuse_knowledge_rankings(
        (lexical, incompatible),
        query,
        manifest["policy"]["fusion"],
    )

    assert result.coverage.snapshot_compatible is False
    assert result.coverage.complete is False
    assert "incompatible snapshot lineage" in result.coverage.errors
    assert result.can_claim_no_result is False


def test_versioned_fixture_meets_quality_and_lane_contamination_thresholds():
    from brain.v5.formula_retrieval import search_formula
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_retrieval import (
        evaluate_ranked_refs,
        search_fielded_lexical,
    )
    from brain.v5.retrieval_fusion import (
        fuse_knowledge_rankings,
        search_dense_optional,
    )

    manifest, queries, snapshot = _fixture()
    thresholds = manifest["acceptance_thresholds"]
    wrong_framework_refs = {"physics_assertion:qg-worldsheet-entropy"}
    convention_mismatch_refs = {"physics_assertion:qg-extrinsic-curvature-minus"}
    all_hits = []
    exact_formula_recovered = False
    cross_lane_contamination = 0

    for row in queries:
        query = _query(row)
        components = (
            search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"]),
            search_formula(snapshot, query, manifest["policy"]["formula"]),
            search_graph(snapshot, query, manifest["policy"]["graph"]),
            search_dense_optional(snapshot, query),
        )
        result = fuse_knowledge_rankings(
            components,
            query,
            manifest["policy"]["fusion"],
        )
        metrics = evaluate_ranked_refs(
            [hit.record_ref for hit in result.hits],
            row["judgments"],
            k=3,
        )
        assert metrics["recall_at_k"] >= thresholds["recall_at_3"]
        assert metrics["mrr"] >= thresholds["mrr"]
        assert metrics["ndcg_at_k"] >= thresholds["ndcg_at_3"]
        all_hits.extend(result.hits)
        if row["query_id"] == "outward-extrinsic-curvature":
            exact_formula_recovered = any(
                hit.record_ref == "physics_assertion:qg-extrinsic-curvature-plus"
                and hit.field_scores.get("score:formula", 0) > 0
                for hit in result.hits
            )
        if query.intent == "insight":
            cross_lane_contamination += sum(
                hit.lane != "insight" for hit in result.hits
            )
        else:
            cross_lane_contamination += sum(
                hit.lane == "insight" for hit in result.hits
            )

    wrong_framework_rate = sum(
        hit.record_ref in wrong_framework_refs for hit in all_hits
    ) / max(1, len(all_hits))
    convention_mismatch_rate = sum(
        hit.record_ref in convention_mismatch_refs for hit in all_hits
    ) / max(1, len(all_hits))
    cross_lane_rate = cross_lane_contamination / max(1, len(all_hits))

    assert float(exact_formula_recovered) >= thresholds["exact_anchor_recovery"]
    assert wrong_framework_rate <= thresholds["wrong_framework_contamination"]
    assert convention_mismatch_rate == 0.0
    assert cross_lane_rate <= thresholds["grounded_insight_cross_contamination"]


def test_incomplete_snapshot_cannot_authorize_an_absence_claim():
    from brain.v5.knowledge_retrieval import KnowledgeQuery, search_fielded_lexical
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings

    manifest, _queries, snapshot = _fixture()
    incomplete = replace(
        snapshot,
        lineage=replace(
            snapshot.lineage,
            scope_fresh=False,
            scope_content_verified=False,
            dirty_families=("physics_assertions",),
            errors=("physics_assertions has malformed indexed records",),
        ),
    )
    query = KnowledgeQuery(text="zqxjkv_unseen_token", topic_id="qg")
    lexical = search_fielded_lexical(incomplete, query, manifest["policy"]["lexical"])
    result = fuse_knowledge_rankings((lexical,), query, manifest["policy"]["fusion"])

    assert result.hits == ()
    assert result.coverage.complete is False
    assert result.can_claim_no_result is False
    assert result.coverage.checked_scope["scope_fresh"] is False
    assert result.coverage.checked_scope["scope_content_verified"] is False
    assert result.coverage.checked_scope["dirty_families"] == ["physics_assertions"]
    assert "physics_assertions has malformed indexed records" in result.coverage.errors


def test_workspace_snapshot_binds_query_index_and_exact_source_shelf_read_only(
    tmp_path,
):
    from brain.v5.knowledge_snapshot import build_knowledge_snapshot
    from brain.v5.physics_knowledge_models import PhysicsAssertionRecord
    from brain.v5.query_index import build_query_index, current_canonical_watermark
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from tests.test_v5_curated_rag_source_shelf import _built_shelf

    ws, shelf_report, source_ref, _blob, location = _built_shelf(tmp_path)
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="knowledge-retrieval-test",
            host="pytest",
        ),
    )
    assertion = repository.write(
        "physics_assertions",
        PhysicsAssertionRecord(
            assertion_id="qg-generalized-entropy",
            object_ref="physics_object:qg-island",
            topic_id="qg",
            predicate="defined_by",
            value="area plus bulk entropy",
            expression="S_gen = A/(4 G_N) + S_bulk",
            framework="semiclassical gravity",
            regime="island formula",
            conventions=["hbar-one"],
            assumptions=["semiclassical bulk effective field theory"],
            source_asset_refs=[source_ref],
            source_location_refs=[f"reference_location:{location.location_id}"],
            review_status="reviewed",
        ),
    )
    index_report = build_query_index(ws)
    before = current_canonical_watermark(ws)

    snapshot = build_knowledge_snapshot(
        ws,
        source_shelf_generation=shelf_report.manifest.generation,
        source_shelf_topic_id="qg",
    )

    by_ref = {item.record_ref: item for item in snapshot.items}
    assert by_ref[assertion.record_ref].lane == "grounded"
    assert any(item.family == "source_shelf_passages" for item in snapshot.items)
    assert snapshot.lineage.query_index_generation == index_report.manifest.generation
    assert snapshot.lineage.source_shelf_generation == shelf_report.manifest.generation
    assert snapshot.lineage.scope_fresh is True
    assert snapshot.lineage.scope_content_verified is True
    assert snapshot.can_update_claim_trust is False
    assert current_canonical_watermark(ws) == before
