from __future__ import annotations


def test_builtin_formal_theory_pack_suggests_derivation_and_counterexample_work():
    from brain.v5.domain_packs import builtin_domain_packs

    packs = builtin_domain_packs()
    pack = packs["formal_theory"]

    assert "claim_scope_check" in pack.suggested_question_intents
    assert "limit_symmetry_dimension_check" in pack.suggested_question_intents
    assert "derivation_trace" in pack.tool_recipes
    assert "counterexample_search" in pack.tool_recipes
    assert pack.truth_standard_policy == "global_only"


def test_builtin_gw_librpa_pack_suggests_code_provenance_and_benchmarks():
    from brain.v5.domain_packs import builtin_domain_packs

    pack = builtin_domain_packs()["gw_librpa"]

    assert "formula_code_invariant_check" in pack.suggested_question_intents
    assert "provenance_check" in pack.suggested_question_intents
    assert "benchmark_consistency_check" in pack.suggested_question_intents
    assert "librpa_gw_benchmark_recipe" in pack.tool_recipes
    assert any(
        recommendation["executor_id"] == "metric_table_check"
        and recommendation["recipe_id"] == "recipe-librpa-gw-benchmark-table"
        for recommendation in pack.tool_executor_recommendations
    )
    assert "clean_code_state_trust_card" in pack.trust_card_templates
    assert pack.truth_standard_policy == "global_only"


def test_suggest_domain_packs_matches_claim_without_overriding_global_policy():
    from brain.v5.domain_packs import suggest_domain_packs
    from brain.v5.models import ClaimRecord

    claim = ClaimRecord(
        claim_id="claim-librpa",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the LibRPA GW benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code provenance",
    )

    packs = suggest_domain_packs(claim)

    assert [pack.pack_id for pack in packs] == ["gw_librpa"]
    assert all(pack.truth_standard_policy == "global_only" for pack in packs)


def test_suggest_tool_executors_for_claim_joins_domain_pack_and_catalog():
    from brain.v5.domain_packs import suggest_tool_executors_for_claim
    from brain.v5.models import ClaimRecord

    claim = ClaimRecord(
        claim_id="claim-fqhe",
        topic_id="fqhe",
        statement="The FQHE edge-sector counting table matches the expected sequence.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )

    recommendations = suggest_tool_executors_for_claim(claim)

    assert recommendations
    first = recommendations[0]
    assert first["pack_id"] == "fqhe_topological_order"
    assert first["executor_id"] == "metric_table_check"
    assert first["recipe_id"] == "recipe-fqhe-counting-table"
    assert first["supports_outputs"] == ["evidence_or_provenance", "minimal_check"]
    assert first["executor"]["input_schema"]["required"] == ["metrics"]


def test_execution_brief_exposes_domain_tool_executor_recommendations(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the LibRPA GW benchmark table.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code provenance",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    recommendations = brief["known_context"]["recommended_tool_executors"]
    assert recommendations[0]["pack_id"] == "gw_librpa"
    assert recommendations[0]["executor_id"] == "metric_table_check"
    assert recommendations[0]["recipe_id"] == "recipe-librpa-gw-benchmark-table"


def test_register_domain_pack_writes_record_under_tools_domain_packs(tmp_path):
    from brain.v5.domain_packs import builtin_domain_packs, register_domain_pack
    from brain.v5.markdown import read_md
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    pack = builtin_domain_packs()["toy_numerics"]

    registered = register_domain_pack(ws, pack)
    fm, _ = read_md(ws.root / "tools" / "domain_packs" / f"{pack.pack_id}.md")

    assert registered.pack_id == "toy_numerics"
    assert fm["pack_id"] == "toy_numerics"
    assert fm["truth_standard_policy"] == "global_only"
    assert fm["tool_executor_recommendations"]
