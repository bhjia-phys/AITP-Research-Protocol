from __future__ import annotations

from dataclasses import replace


def _seed_context_workspace(tmp_path):
    from brain.v5.models import ClaimStatusRecord
    from brain.v5.paths import WorkspacePaths
    from brain.v5.query_index import build_query_index
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The replica saddle requires an explicit factorization boundary.",
        evidence_profile="semi_formal_theory",
        confidence_state="conditional",
        active_uncertainty="The analytic continuation is not yet controlled.",
    )
    bind_session(
        ws,
        "session-qg",
        topic_id="qg",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )
    status = ClaimStatusRecord(
        status_id="status-qg",
        topic_id="qg",
        claim_id=claim.claim_id,
        maturity_level="derivation_in_progress",
        claim_status="conditional",
        scope="fixed replica number",
        risk="analytic continuation",
        next_action="Check the continuation against an exact finite-n result.",
        open_gaps=["No uniform continuation bound."],
    )
    write_record(ws.registry_dir("claim_statuses") / "status-qg.md", status)
    build_query_index(ws)
    return WorkspacePaths(tmp_path), claim


def test_context_compiler_uses_one_query_plan_and_enforces_budgets(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.research_retrieval import query_records

    ws, claim = _seed_context_workspace(tmp_path)
    calls = []

    def counting_query(workspace, query):
        calls.append(query)
        return query_records(workspace, query)

    request = ContextRequest(
        session_id="session-qg",
        objective_text="continue the replica derivation",
        max_tokens=220,
        max_bytes=1400,
        record_limit=20,
    )
    bundle = compile_research_context(ws, request, query_fn=counting_query)

    assert len(calls) == 1
    assert bundle.topic_id == "qg"
    assert bundle.current_boundary["claim_id"] == claim.claim_id
    assert bundle.byte_count <= request.max_bytes
    assert bundle.estimated_tokens <= request.max_tokens
    assert bundle.record_refs
    assert bundle.expansion["surface"] == "record_refs"
    assert bundle.orientation_only is True
    assert bundle.can_update_kernel_state is False
    assert bundle.can_update_claim_trust is False
    assert bundle.requires_exact_expansion_before_trust_conclusions is True
    assert bundle.source_index_generation >= 1


def test_context_compiler_marks_stale_and_truncated_context_partial(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.workspace import create_claim

    ws, _claim = _seed_context_workspace(tmp_path)
    create_claim(
        ws,
        topic_id="qg",
        statement="A result written after the current index generation.",
        evidence_profile="semi_formal_theory",
        confidence_state="candidate",
        active_uncertainty="The index has not incorporated this record.",
    )

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-qg",
            max_tokens=90,
            max_bytes=560,
            record_limit=20,
        ),
    )

    assert bundle.index_status == "stale"
    assert bundle.coverage["exhaustive"] is False
    assert bundle.coverage["can_claim_no_result"] is False
    assert bundle.can_claim_no_prior_result is False
    assert bundle.truncated is True
    assert bundle.byte_count <= 560
    assert bundle.estimated_tokens <= 90


def test_context_compiler_propagates_scoped_read_errors(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.markdown import write_md
    from brain.v5.query_index import build_query_index

    ws, _claim = _seed_context_workspace(tmp_path)
    write_md(
        ws.registry_dir("claims") / "missing-id.md",
        {"kind": "claim", "topic_id": "qg"},
        "# Missing canonical id\n",
    )
    build_query_index(ws)

    bundle = compile_research_context(
        ws,
        ContextRequest(session_id="session-qg", families=("claims",), record_limit=20),
    )

    assert bundle.coverage["malformed_count"] == 1
    assert bundle.coverage["exhaustive"] is False
    assert bundle.can_claim_no_prior_result is False
    assert bundle.read_errors == ("malformed_records_in_scope:1",)


def test_context_compiler_contract_rejects_trust_mutation(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle

    ws, _claim = _seed_context_workspace(tmp_path)
    bundle = compile_research_context(ws, ContextRequest(session_id="session-qg"))

    assert validate_context_bundle(bundle) == ()
    assert "can_update_claim_trust must be false" in validate_context_bundle(
        replace(bundle, can_update_claim_trust=True)
    )


def test_codex_record_ref_expansion_is_explicit_bounded_and_paginated(tmp_path):
    from brain.v5.codex_facade import codex_expand_context, codex_tool_catalog
    from brain.v5.mcp_tools import aitp_v5_codex_expand

    ws, claim = _seed_context_workspace(tmp_path)
    refs = [f"claim:{claim.claim_id}", "claim_status:status-qg"]

    first = codex_expand_context(
        ws,
        session_id="session-qg",
        expansion="record_refs",
        record_refs=refs,
        offset=0,
        limit=1,
    )
    second = codex_expand_context(
        ws,
        session_id="session-qg",
        expansion="record_refs",
        record_refs=refs,
        offset=1,
        limit=1,
    )
    via_mcp = aitp_v5_codex_expand(
        str(ws.base),
        session_id="session-qg",
        expansion="record_refs",
        record_refs=refs,
        offset=0,
        limit=1,
    )

    assert "record_refs" in codex_tool_catalog("read_expansion")["profile"]["expansions"]
    assert first["surface"]["kind"] == "record_ref_expansion"
    assert first["surface"]["returned_refs"] == [refs[0]]
    assert first["surface"]["next_offset"] == 1
    assert second["surface"]["returned_refs"] == [refs[1]]
    assert second["surface"]["next_offset"] is None
    assert via_mcp["surface"]["returned_refs"] == [refs[0]]
    assert first["surface"]["summary_inputs_trusted"] is False
    assert first["surface"]["can_update_kernel_state"] is False
    assert first["surface"]["can_update_claim_trust"] is False


def test_context_pack_uses_compiler_without_legacy_recursive_builders(tmp_path, monkeypatch):
    from brain.v5 import context_pack

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_legacy_builder(*_args, **_kwargs):
        raise AssertionError("legacy recursive context builder was called")

    monkeypatch.setattr(context_pack, "build_compact_brief", fail_legacy_builder, raising=False)
    monkeypatch.setattr(
        context_pack,
        "build_research_distillation_candidates",
        fail_legacy_builder,
        raising=False,
    )

    pack = context_pack.build_aitp_context_pack(
        ws,
        "session-qg",
        objective_text="continue the replica derivation",
        max_lines=45,
        candidate_limit=2,
    )

    assert pack["relevant_claims"][0]["claim_id"] == claim.claim_id
    assert pack["retrieval_coverage"]["exhaustive"] is True
    assert pack["record_refs"]
    assert pack["expand"]["record_refs"]["surface"] == "record_refs"
    assert "query_index" in pack["source_records"]["derived_surfaces"]


def test_indexed_topic_snapshot_uses_one_query_and_isolates_topics(tmp_path):
    from brain.v5.context_compiler import load_indexed_topic_snapshot
    from brain.v5.query_index import build_query_index
    from brain.v5.research_retrieval import query_records
    from brain.v5.workspace import create_claim, create_topic

    ws, claim = _seed_context_workspace(tmp_path)
    create_topic(ws, "other", context_id="formal-theory", title="Other topic")
    other = create_claim(
        ws,
        topic_id="other",
        statement="This claim must not leak into the qg snapshot.",
        evidence_profile="semi_formal_theory",
        confidence_state="candidate",
        active_uncertainty="unrelated topic",
    )
    build_query_index(ws)
    calls = []

    def counting_query(workspace, query):
        calls.append(query)
        return query_records(workspace, query)

    snapshot = load_indexed_topic_snapshot(
        ws,
        "session-qg",
        families=("claims", "claim_statuses"),
        query_fn=counting_query,
    )

    assert len(calls) == 1
    claim_ids = {record.claim_id for record in snapshot.records_by_family["claims"]}
    assert claim.claim_id in claim_ids
    assert other.claim_id not in claim_ids
    assert snapshot.index_status == "fresh"
    assert snapshot.coverage["exhaustive"] is True


def test_objective_graph_uses_indexed_snapshot_not_family_scans(tmp_path, monkeypatch):
    from brain.v5 import objective_graph

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_family_scan(*_args, **_kwargs):
        raise AssertionError("objective graph performed a family scan")

    monkeypatch.setattr(objective_graph, "list_valid_records", fail_family_scan)

    payload = objective_graph.build_objective_graph(ws, "session-qg")

    assert payload["claims"][0]["claim_id"] == claim.claim_id
    assert payload["retrieval_coverage"]["exhaustive"] is True
    assert payload["source_index_generation"] >= 1


def test_relation_map_uses_indexed_registry_projection(tmp_path, monkeypatch):
    from brain.v5 import claim_relation_map

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_family_scan(*_args, **_kwargs):
        raise AssertionError("relation map performed a family scan")

    for name in (
        "list_evidence_for_claim",
        "_tool_runs_for_claim",
        "_claim_statuses_for_claim",
        "list_proof_obligations_for_claim",
        "list_object_relations_for_claim",
        "_claims_for_topic",
        "_legacy_semantic_reviews_for_topic",
        "_legacy_migration_topics_for_topic",
    ):
        monkeypatch.setattr(claim_relation_map, name, fail_family_scan)

    payload = claim_relation_map.build_claim_relation_map(ws, "session-qg")

    assert payload["claim_id"] == claim.claim_id
    assert payload["latest_claim_status"]["status_id"] == "status-qg"
    assert payload["retrieval_coverage"]["exhaustive"] is True
    assert payload["source_index_generation"] >= 1


def test_active_focus_detector_uses_indexed_snapshot(tmp_path, monkeypatch):
    from brain.v5 import active_claim_focus

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_family_scan(*_args, **_kwargs):
        raise AssertionError("active focus detector performed a family scan")

    monkeypatch.setattr(active_claim_focus, "_topic_claims", fail_family_scan)
    monkeypatch.setattr(active_claim_focus, "_record_observations", fail_family_scan)

    payload = active_claim_focus.detect_active_claim_focus_drift(ws, "session-qg")

    assert payload["active_claim"]["claim_id"] == claim.claim_id
    assert payload["status"] == "no_active_claim_focus_drift"
    assert payload["source_index_generation"] >= 1


def test_research_timeline_uses_indexed_snapshot_not_directory_scans(tmp_path, monkeypatch):
    from brain.v5 import research_timeline

    ws, _claim = _seed_context_workspace(tmp_path)

    def fail_directory_scan(*_args, **_kwargs):
        raise AssertionError("timeline performed a directory scan")

    monkeypatch.setattr(research_timeline, "_records_with_paths", fail_directory_scan, raising=False)

    payload = research_timeline.build_research_timeline(ws, "session-qg")

    assert any(event["record_ref"] == "claim_status:status-qg" for event in payload["events"])
    assert payload["retrieval_coverage"]["exhaustive"] is True
    assert payload["source_index_generation"] >= 1


def test_distillation_uses_shared_snapshot_without_execution_brief(tmp_path, monkeypatch):
    from brain.v5 import research_distillation

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_recursive_brief(*_args, **_kwargs):
        raise AssertionError("distillation built a recursive execution brief")

    monkeypatch.setattr(research_distillation, "build_execution_brief", fail_recursive_brief)

    payload = research_distillation.build_research_distillation_candidates(
        ws,
        "session-qg",
        limit=2,
    )

    assert payload["active_claim_id"] == claim.claim_id
    assert payload["candidates"]
    assert payload["retrieval_coverage"]["exhaustive"] is True
    assert payload["source_index_generation"] >= 1


def test_context_pack_contract_validates_budget_and_coverage_fields(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.context_pack_contracts import validate_aitp_context_pack

    ws, _claim = _seed_context_workspace(tmp_path)
    pack = build_aitp_context_pack(ws, "session-qg", max_lines=45)

    assert validate_aitp_context_pack(pack).ok is True

    tampered = dict(pack)
    tampered["byte_count"] = pack["byte_count"] + 1
    result = validate_aitp_context_pack(tampered)

    assert any(issue.path.endswith("byte_count") for issue in result.issues)


def test_exact_ref_expansion_does_not_load_full_derived_index(tmp_path, monkeypatch):
    from brain.v5 import research_retrieval

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_full_index_load(*_args, **_kwargs):
        raise AssertionError("exact expansion loaded the full derived index")

    monkeypatch.setattr(research_retrieval, "load_query_index", fail_full_index_load)

    result = research_retrieval.exact_expand(ws, [f"claim:{claim.claim_id}"], limit=10)

    assert result.items[0].record_ref == f"claim:{claim.claim_id}"
    assert result.items[0].exact_score == 100
    assert result.index_generation >= 1


def test_indexed_snapshot_reuses_repository_frontmatter_without_second_parse(tmp_path, monkeypatch):
    from brain.v5 import indexed_topic_snapshot

    ws, claim = _seed_context_workspace(tmp_path)

    def fail_second_parse(*_args, **_kwargs):
        raise AssertionError("snapshot parsed an exact record twice")

    monkeypatch.setattr(indexed_topic_snapshot, "read_md", fail_second_parse)

    snapshot = indexed_topic_snapshot.load_indexed_topic_snapshot(
        ws,
        "session-qg",
        families=("claims", "claim_statuses"),
    )

    assert any(record.record_ref == f"claim:{claim.claim_id}" for record in snapshot.indexed_records)


def test_active_focus_materialization_excludes_high_volume_reference_locations():
    from brain.v5.active_claim_focus import active_claim_focus_families

    families = active_claim_focus_families()

    assert "reference_locations" not in families
    assert "source_assets" in families
    assert "evidence" in families
