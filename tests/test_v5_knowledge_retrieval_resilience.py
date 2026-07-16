from __future__ import annotations

from dataclasses import replace
from copy import deepcopy

import pytest


class _NondeterministicDenseAdapter:
    adapter_version = "test-dense.v1"
    model_id = "test-embedding"
    index_version = "fixture-1"
    deterministic = False

    def search(self, snapshot, query, limit):  # pragma: no cover - policy excludes it
        raise AssertionError("nondeterministic adapter must not run")


class _TimeoutDenseAdapter:
    adapter_version = "test-dense.v1"
    model_id = "test-embedding"
    index_version = "fixture-1"
    deterministic = True

    def search(self, snapshot, query, limit):
        raise TimeoutError("fixture timeout")


class _WrongGenerationDenseAdapter:
    adapter_version = "test-dense.v1"
    model_id = "test-embedding"
    index_version = "fixture-stale"
    deterministic = True

    def search(self, snapshot, query, limit):
        from brain.v5.knowledge_retrieval import search_fielded_lexical

        lexical = search_fielded_lexical(snapshot, query)
        return replace(
            lexical,
            component="dense",
            snapshot_hash="0" * 64,
            component_hash="1" * 64,
        )


class _DeterministicDenseAdapter:
    adapter_version = "test-dense.v1"
    model_id = "test-embedding"
    index_version = "fixture-1"
    deterministic = True

    def search(self, snapshot, query, limit):
        from brain.v5.knowledge_retrieval import search_fielded_lexical

        lexical = search_fielded_lexical(snapshot, query)
        hits = tuple(
            replace(
                hit,
                component="dense",
                rank=index,
                score=0.91,
                field_scores={"cosine": 0.91},
            )
            for index, hit in enumerate(lexical.hits[:2], start=1)
        )
        return replace(
            lexical,
            component="dense",
            version=self.adapter_version,
            hits=hits,
            coverage={"candidate_count": 2},
            component_hash="2" * 64,
        )


def test_nondeterministic_dense_is_excluded_without_degrading_lexical_baseline():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import (
        fuse_knowledge_rankings,
        search_dense_optional,
    )
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    lexical = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    dense = search_dense_optional(snapshot, query, _NondeterministicDenseAdapter())
    result = fuse_knowledge_rankings(
        (lexical, dense),
        query,
        manifest["policy"]["fusion"],
    )

    assert dense.status == "excluded"
    assert dense.coverage["reason"] == "nondeterministic_dense_disabled"
    assert dense.hits == ()
    assert result.coverage.component_statuses["dense"] == "excluded"
    assert result.coverage.complete is True
    assert result.deterministic is True


def test_dense_timeout_degrades_visibly_without_losing_lexical_hits():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import (
        fuse_knowledge_rankings,
        search_dense_optional,
    )
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    lexical = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    dense = search_dense_optional(snapshot, query, _TimeoutDenseAdapter())
    result = fuse_knowledge_rankings(
        (lexical, dense),
        query,
        manifest["policy"]["fusion"],
    )

    assert dense.status == "degraded"
    assert dense.coverage["adapter_version"] == "test-dense.v1"
    assert dense.coverage["model_id"] == "test-embedding"
    assert dense.coverage["index_version"] == "fixture-1"
    assert len(dense.coverage["input_hash"]) == 64
    assert dense.coverage["timeout_policy"] == "degrade_to_non_dense_components"
    assert dense.errors == ("dense adapter failed: fixture timeout",)
    assert result.hits == tuple(
        hit for hit in result.hits if hit.component == "fusion"
    )
    assert result.hits
    assert result.coverage.complete is False
    assert "dense adapter failed: fixture timeout" in result.coverage.errors


def test_dense_wrong_snapshot_generation_is_isolated_as_degraded():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import (
        fuse_knowledge_rankings,
        search_dense_optional,
    )
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    lexical = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    dense = search_dense_optional(snapshot, query, _WrongGenerationDenseAdapter())
    result = fuse_knowledge_rankings(
        (lexical, dense),
        query,
        manifest["policy"]["fusion"],
    )

    assert dense.status == "degraded"
    assert dense.hits == ()
    assert dense.coverage["reason"] == "incompatible_dense_component_identity"
    assert dense.coverage["returned_snapshot_hash"] == "0" * 64
    assert "dense adapter returned incompatible component identity" in dense.errors
    assert result.hits
    assert result.coverage.complete is False


def test_dense_success_is_rebound_to_snapshot_scope_and_adapter_lineage():
    from brain.v5.retrieval_fusion import search_dense_optional
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    _manifest, queries, snapshot = _fixture()
    query = _query(queries[0])

    dense = search_dense_optional(snapshot, query, _DeterministicDenseAdapter())
    repeated = search_dense_optional(snapshot, query, _DeterministicDenseAdapter())

    assert dense.status == "available"
    assert dense.version == "test-dense.v1"
    assert dense.coverage["adapter_version"] == "test-dense.v1"
    assert dense.coverage["model_id"] == "test-embedding"
    assert dense.coverage["index_version"] == "fixture-1"
    assert len(dense.coverage["input_hash"]) == 64
    assert dense.coverage["adapter_result_hash"] == "2" * 64
    assert dense.coverage["tie_handling"] == "score_desc_then_record_ref"
    assert dense.component_hash != "2" * 64
    assert [hit.record_ref for hit in dense.hits] == sorted(
        hit.record_ref for hit in dense.hits
    )
    assert dense.hits[0].lane == "grounded"
    assert dense.hits[0].orientation_only is False
    assert dense.can_update_claim_trust is False
    assert repeated == dense


def test_graph_blocks_cross_topic_edges_without_exact_scope_revalidation():
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_snapshot import knowledge_snapshot_from_rows
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    documents = deepcopy(manifest["documents"])
    island = next(
        row
        for row in documents
        if row["record_ref"] == "physics_object:qg-island"
    )
    island["links"].append("physics_assertion:ads-shared-extremization")
    island["link_types"]["physics_assertion:ads-shared-extremization"] = [
        "cross_topic_support"
    ]
    linked_snapshot = knowledge_snapshot_from_rows(
        documents,
        lineage=replace(snapshot.lineage, snapshot_hash=""),
    )
    query = replace(_query(queries[2]), include_discovery=True)

    result = search_graph(
        linked_snapshot,
        query,
        manifest["policy"]["graph"],
    )

    assert "physics_assertion:ads-shared-extremization" not in {
        hit.record_ref for hit in result.hits
    }
    assert result.coverage["cross_topic_edges_blocked"] == 1
    assert result.coverage["cross_topic_edges_authorized"] == 0
    assert result.coverage["scope_policy"] == "exact_target_revalidation_required"


def test_graph_accepts_only_real_exact_target_scope_revalidation(
    tmp_path,
    monkeypatch,
):
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_retrieval import KnowledgeQuery
    from brain.v5.knowledge_snapshot import (
        KnowledgeSnapshotLineage,
        knowledge_snapshot_from_rows,
    )
    from brain.v5.scope_revalidation import record_scope_revalidation
    from tests.test_v5_scope_revalidation import _actor, _seed_scope_proposal

    ws, proposal, requested, decided, now = _seed_scope_proposal(
        tmp_path,
        monkeypatch,
        allowed_operations=("knowledge_graph_traversal",),
    )
    capture = record_scope_revalidation(
        ws,
        proposal,
        binding=requested.binding,
        checkpoint_request_ref=requested.request_ref,
        checkpoint_decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    source_pin = proposal.source_refs[0]
    local_ref = "physics_object:target-seed"
    snapshot = knowledge_snapshot_from_rows(
        (
            {
                "record_ref": local_ref,
                "record_hash": "b" * 64,
                "revision": 1,
                "family": "physics_objects",
                "topic_id": "target-topic",
                "lane": "grounded",
                "fields": {"canonical_name": ["target seed"]},
                "links": [source_pin.record_ref],
                "link_types": {
                    source_pin.record_ref: ["cross_topic_support"]
                },
            },
            {
                "record_ref": source_pin.record_ref,
                "record_hash": source_pin.content_hash,
                "revision": source_pin.revision,
                "family": "claims",
                "topic_id": "source-topic",
                "lane": "grounded",
                "fields": {"statement": ["reviewed source result"]},
                "links": [],
            },
        ),
        lineage=KnowledgeSnapshotLineage(
            query_index_generation=1,
            query_index_delta_generation=0,
            query_index_content_hash="c" * 64,
            selected_family_state_tokens={"claims": "d" * 64},
            selected_family_content_watermarks={"claims": "e" * 64},
            scope_fresh=True,
            scope_content_verified=True,
        ),
    )
    query = KnowledgeQuery(
        text="",
        topic_id="target-topic",
        seed_refs=(local_ref,),
        include_discovery=True,
        revalidation_decision_refs=(capture.pinned_ref,),
    )

    result = search_graph(snapshot, query, workspace=ws)

    assert [hit.record_ref for hit in result.hits] == [source_pin.record_ref]
    assert result.hits[0].lane == "discovery"
    assert result.hits[0].orientation_only is True
    assert result.hits[0].can_update_claim_trust is False
    assert result.coverage["cross_topic_edges_authorized"] == 1
    assert result.coverage["cross_topic_edges_blocked"] == 0


def test_knowledge_query_rejects_bare_scope_revalidation_refs():
    from brain.v5.knowledge_retrieval import KnowledgeQuery

    with pytest.raises(TypeError, match="exact pinned refs"):
        KnowledgeQuery(
            text="cross-topic dependency",
            topic_id="target-topic",
            include_discovery=True,
            revalidation_decision_refs=("scope_revalidation_decision:bare",),
        )


def test_fusion_rejects_component_hit_that_attempts_trust_transfer():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    query = _query(queries[0])
    lexical = search_fielded_lexical(snapshot, query, manifest["policy"]["lexical"])
    tampered = replace(
        lexical,
        hits=(replace(lexical.hits[0], can_update_claim_trust=True),),
    )

    with pytest.raises(ValueError, match="cannot update claim trust"):
        fuse_knowledge_rankings(
            (tampered,),
            query,
            manifest["policy"]["fusion"],
        )


def test_retrieval_components_reject_unversioned_or_nonfinite_policy():
    from brain.v5.formula_retrieval import search_formula
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    lexical_query = _query(queries[0])
    formula_query = _query(queries[1])
    graph_query = _query(queries[2])
    lexical = search_fielded_lexical(
        snapshot,
        lexical_query,
        manifest["policy"]["lexical"],
    )

    with pytest.raises(ValueError, match="unsupported lexical policy version"):
        search_fielded_lexical(snapshot, lexical_query, {"version": "fielded-bm25.v0"})
    with pytest.raises(ValueError, match="formula policy weights"):
        search_formula(snapshot, formula_query, {"exact_weight": float("nan")})
    with pytest.raises(ValueError, match="graph retrieval bounds"):
        search_graph(snapshot, graph_query, {"depth_decay": -0.5})
    with pytest.raises(ValueError, match="fusion component weights"):
        fuse_knowledge_rankings(
            (lexical,),
            lexical_query,
            {"component_weights": {"lexical": float("nan")}},
        )


def test_primary_shared_and_discovery_scope_lanes_remain_ordered_and_isolated():
    from brain.v5.knowledge_retrieval import KnowledgeQuery, search_fielded_lexical
    from brain.v5.knowledge_snapshot import (
        KnowledgeSnapshotLineage,
        knowledge_snapshot_from_rows,
    )
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings

    rows = (
        {
            "record_ref": "physics_assertion:local",
            "record_hash": "1" * 64,
            "family": "physics_assertions",
            "topic_id": "target-topic",
            "program_id": "program-qg",
            "lane": "grounded",
            "fields": {"statement": ["common scope phrase"]},
            "links": [],
        },
        {
            "record_ref": "physics_assertion:shared",
            "record_hash": "2" * 64,
            "family": "physics_assertions",
            "topic_id": "sibling-topic",
            "program_id": "program-qg",
            "lane": "grounded",
            "fields": {"statement": ["common scope phrase"]},
            "links": [],
        },
        {
            "record_ref": "physics_assertion:discovery",
            "record_hash": "3" * 64,
            "family": "physics_assertions",
            "topic_id": "foreign-topic",
            "program_id": "other-program",
            "lane": "grounded",
            "fields": {"statement": ["common scope phrase"]},
            "links": [],
        },
        {
            "record_ref": "insight:foreign",
            "record_hash": "4" * 64,
            "family": "insights",
            "topic_id": "sibling-topic",
            "program_id": "program-qg",
            "lane": "insight",
            "fields": {"statement": ["common scope phrase"]},
            "links": [],
        },
    )
    snapshot = knowledge_snapshot_from_rows(
        rows,
        lineage=KnowledgeSnapshotLineage(
            query_index_generation=1,
            query_index_delta_generation=0,
            query_index_content_hash="5" * 64,
            selected_family_state_tokens={"physics_assertions": "6" * 64},
            selected_family_content_watermarks={"physics_assertions": "7" * 64},
            scope_fresh=True,
            scope_content_verified=True,
        ),
    )
    shared_query = KnowledgeQuery(
        text="common scope phrase",
        topic_id="target-topic",
        program_id="program-qg",
    )
    shared = search_fielded_lexical(snapshot, shared_query)
    shared_fused = fuse_knowledge_rankings((shared,), shared_query)
    discovery_query = replace(shared_query, include_discovery=True)
    discovery = search_fielded_lexical(snapshot, discovery_query)
    discovery_fused = fuse_knowledge_rankings((discovery,), discovery_query)

    assert [hit.record_ref for hit in shared_fused.hits] == [
        "physics_assertion:local",
        "physics_assertion:shared",
    ]
    assert [hit.lane for hit in shared_fused.hits] == ["grounded", "shared"]
    assert shared_fused.hits[1].orientation_only is True
    assert [hit.record_ref for hit in discovery_fused.hits] == [
        "physics_assertion:local",
        "physics_assertion:shared",
        "physics_assertion:discovery",
    ]
    assert [hit.lane for hit in discovery_fused.hits] == [
        "grounded",
        "shared",
        "discovery",
    ]
    assert "insight:foreign" not in {
        hit.record_ref for hit in discovery_fused.hits
    }


def test_fusion_pagination_preserves_global_rank_and_not_shown_semantics():
    from brain.v5.knowledge_retrieval import search_fielded_lexical
    from brain.v5.retrieval_fusion import fuse_knowledge_rankings
    from tests.test_v5_knowledge_retrieval import _fixture, _query

    manifest, queries, snapshot = _fixture()
    base_query = replace(_query(queries[0]), max_results=2)
    first_component = search_fielded_lexical(
        snapshot,
        base_query,
        manifest["policy"]["lexical"],
    )
    first = fuse_knowledge_rankings(
        (first_component,),
        base_query,
        manifest["policy"]["fusion"],
    )
    second_query = replace(base_query, page_offset=2)
    second_component = search_fielded_lexical(
        snapshot,
        second_query,
        manifest["policy"]["lexical"],
    )
    second = fuse_knowledge_rankings(
        (second_component,),
        second_query,
        manifest["policy"]["fusion"],
    )

    assert [hit.rank for hit in first.hits] == [1, 2]
    assert [hit.rank for hit in second.hits] == [3, 4]
    assert not ({hit.record_ref for hit in first.hits} & {
        hit.record_ref for hit in second.hits
    })
    assert first.coverage.pagination == {
        "offset": 0,
        "limit": 2,
        "returned": 2,
        "total_observed": 2,
        "total_exact": False,
        "not_shown_observed": 0,
        "has_more": True,
        "next_offset": 2,
    }
    assert second.coverage.pagination["offset"] == 2
    assert second.coverage.pagination["returned"] == 2
    assert second.coverage.pagination["next_offset"] == 4
    assert first.can_claim_no_result is False


def test_canonical_formula_code_relation_builds_typed_graph_path(
    tmp_path,
):
    from brain.v5.formula_code_map import record_formula_code_relation
    from brain.v5.graph_retrieval import search_graph
    from brain.v5.knowledge_retrieval import KnowledgeQuery
    from brain.v5.knowledge_snapshot import build_knowledge_snapshot
    from brain.v5.query_index import build_query_index
    from tests.test_v5_formula_code_map import (
        _actor as formula_actor,
        _fixture as formula_fixture,
        _relation,
    )

    data = formula_fixture(tmp_path)
    relation = record_formula_code_relation(
        data["ws"],
        _relation(data),
        actor=formula_actor(),
    )
    build_query_index(data["ws"])
    snapshot = build_knowledge_snapshot(data["ws"])
    query = KnowledgeQuery(
        text="",
        topic_id="librpa",
        seed_refs=(data["formula_ref"].record_ref,),
        graph_depth=2,
    )

    result = search_graph(snapshot, query)
    by_ref = {hit.record_ref: hit for hit in result.hits}

    assert relation.record_ref in by_ref
    assert data["code_ref"].record_ref in by_ref
    assert by_ref[relation.record_ref].anchors["edge_path"] == [
        "reverse:formula_code_formula"
    ]
    assert by_ref[data["code_ref"].record_ref].anchors["edge_path"] == [
        "reverse:formula_code_formula",
        "formula_code_code_state",
    ]
    assert by_ref[data["code_ref"].record_ref].orientation_only is True
