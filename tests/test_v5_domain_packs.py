from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_builtin_formal_theory_pack_suggests_derivation_and_counterexample_work():
    from brain.v5.domain_packs import builtin_domain_packs

    packs = builtin_domain_packs()
    pack = packs["formal_theory"]

    assert "claim_scope_check" in pack.suggested_question_intents
    assert "limit_symmetry_dimension_check" in pack.suggested_question_intents
    assert "derivation_trace" in pack.tool_recipes
    assert "counterexample_search" in pack.tool_recipes
    assert pack.workflow_graph["default_routes"][0]["route_id"] == "definition_assumption_audit"
    assert pack.workflow_graph["orientation_only"] is True
    assert any(item["failure_id"] == "derivation_gap" for item in pack.failure_taxonomy)
    assert pack.lane_policy["default_lane"] == "derivation_review"
    assert "heuristic derivation" in pack.lane_policy["forbidden_promotions"]
    assert "derivation_trace" in pack.artifact_schema["required_artifact_roles"]
    assert pack.hpc_interpretation["missing_expected_output_means"] == "formal_gap_still_open"
    assert "derivation_check" in pack.context_profile_refs
    assert any(
        recommendation["executor_id"] == "checklist_consistency_check"
        and recommendation["recipe_id"] == "recipe-formal-theory-checklist"
        for recommendation in pack.tool_executor_recommendations
    )
    assert pack.truth_standard_policy == "global_only"


def test_formal_theory_domain_pack_recommends_checklist_executor_for_claim():
    from brain.v5.domain_packs import suggest_tool_executors_for_claim
    from brain.v5.models import ClaimRecord

    claim = ClaimRecord(
        claim_id="claim-formal",
        topic_id="quantum-gravity",
        statement="The proposed constraint algebra closes under the bracket.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="definition and hidden-assumption audit",
    )

    recommendations = suggest_tool_executors_for_claim(claim)

    assert recommendations
    assert recommendations[0]["pack_id"] == "formal_theory"
    assert recommendations[0]["executor_id"] == "checklist_consistency_check"
    assert recommendations[0]["supports_outputs"] == ["evidence_or_provenance", "minimal_check"]


def test_builtin_qft_and_quantum_gravity_packs_are_literature_experience_packs():
    from brain.v5.domain_packs import builtin_domain_packs

    packs = builtin_domain_packs()
    qft = packs["qft_literature"]
    qg = packs["quantum_gravity_literature"]

    assert qft.workflow_graph["default_routes"][0]["route_id"] == "qft_source_grounded_reading"
    assert qft.workflow_graph["orientation_only"] is True
    assert qft.lane_policy["default_lane"] == "literature_orientation"
    assert "reference_location_table" in qft.artifact_schema["required_artifact_roles"]
    assert any(item["failure_id"] == "renormalization_scheme_mismatch" for item in qft.failure_taxonomy)
    assert qft.skill_refs[0]["connector_id"] == "qft_literature"
    assert qft.skill_refs[0]["orientation_only"] is True
    assert qft.manifest_refs[0]["manifest_id"] == "connector.qft_literature"
    assert "source_reconstruction" in qft.context_profile_refs

    assert qg.workflow_graph["default_routes"][0]["route_id"] == "qg_source_grounded_learning"
    assert qg.lane_policy["default_lane"] == "literature_orientation"
    assert "human checkpoint before promotion" in qg.lane_policy["final_evidence_requires"][3]
    assert any(item["failure_id"] == "speculation_promoted_as_source_result" for item in qg.failure_taxonomy)
    assert qg.skill_refs[0]["connector_id"] == "quantum_gravity_literature"
    assert qg.skill_refs[0]["orientation_only"] is True
    assert qg.manifest_refs[0]["manifest_id"] == "connector.quantum_gravity_literature"
    assert "group_meeting_report" in qg.context_profile_refs


def test_qft_and_qg_domain_pack_suggestions_compose_with_formal_baseline():
    from brain.v5.domain_packs import suggest_domain_packs
    from brain.v5.models import ClaimRecord

    qft_claim = ClaimRecord(
        claim_id="claim-qft",
        topic_id="qft-renormalization",
        statement="The QFT Wilsonian renormalization argument follows from the cited path integral source.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="scheme convention and source anchors need review",
    )
    qg_claim = ClaimRecord(
        claim_id="claim-qg",
        topic_id="quantum-gravity",
        statement="The quantum gravity wormhole source comparison supports the proposed scope boundary.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="speculation boundary is unclear",
    )

    assert [pack.pack_id for pack in suggest_domain_packs(qft_claim)] == [
        "qft_literature",
        "formal_theory",
    ]
    assert [pack.pack_id for pack in suggest_domain_packs(qg_claim)] == [
        "quantum_gravity_literature",
    ]


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
    invariant_recommendation = next(
        recommendation
        for recommendation in pack.tool_executor_recommendations
        if recommendation["recipe_id"] == "recipe-librpa-gw-formula-code-invariant"
    )
    assert invariant_recommendation["executor_id"] == "formula_code_invariant_check"
    assert invariant_recommendation["supports_outputs"] == ["formula_code_invariant", "minimal_check"]
    assert invariant_recommendation["required_context_refs"] == ["code_state_ids", "formula_refs"]
    metadata_recommendation = next(
        recommendation
        for recommendation in pack.tool_executor_recommendations
        if recommendation["recipe_id"] == "recipe-librpa-gw-run-metadata-diagnostic"
    )
    assert metadata_recommendation["executor_id"] == "librpa_gw_run_metadata_check"
    assert metadata_recommendation["supports_outputs"] == ["librpa_gw_run_metadata", "minimal_check"]
    assert metadata_recommendation["required_context_refs"] == ["code_state_ids", "artifact_ids"]
    review_recommendation = next(
        recommendation
        for recommendation in pack.tool_executor_recommendations
        if recommendation["recipe_id"] == "recipe-librpa-gw-failure-mode-review-basis"
    )
    assert review_recommendation["executor_id"] == "failure_mode_basis_check"
    assert review_recommendation["supports_outputs"] == ["failure_mode_review_basis", "minimal_check"]
    assert review_recommendation["required_context_refs"] == ["code_state_ids", "validation_result_ids"]
    assert pack.workflow_graph["default_routes"][0]["route_id"] == "abacus_librpa_molecule_gw"
    assert pack.lane_policy["default_lane"] == "diagnostic"
    assert "passed validation_result" in pack.lane_policy["final_evidence_requires"]
    assert any(item["failure_id"] == "nonfinal_or_diagnostic_data" for item in pack.failure_taxonomy)
    assert "run_report" in pack.artifact_schema["required_artifact_roles"]
    assert pack.hpc_interpretation["runtime_failure_not_algorithmic_evidence"] is True
    assert "librpa_run_continuation" in pack.context_profile_refs
    skill_ids = {ref["skill_id"] for ref in pack.skill_refs}
    assert "oh-my-librpa" in skill_ids
    assert "oh-my-librpa-abacus-librpa" in skill_ids
    assert "oh-my-librpa-fhi-aims-qsgw" in skill_ids
    entrypoint = next(ref for ref in pack.skill_refs if ref["skill_id"] == "oh-my-librpa")
    assert entrypoint["entrypoint"] == "skills/oh-my-librpa/SKILL.md"
    assert entrypoint["orientation_only"] is True
    assert "tool_run" in entrypoint["required_followup_records"]
    assert any(ref["path"] == "registry/domain-manifest.abacus-librpa.json" for ref in pack.manifest_refs)
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


def test_domain_pack_catalog_is_public_orientation_surface():
    from brain.v5.domain_packs import describe_domain_packs
    from brain.v5.public_surfaces import require_valid_public_surface

    catalog = require_valid_public_surface("domain_pack_catalog", describe_domain_packs())

    assert catalog["kind"] == "domain_pack_catalog"
    assert catalog["truth_source"] == "builtin_domain_pack_registry"
    assert catalog["summary_inputs_trusted"] is False
    assert catalog["can_update_kernel_state"] is False
    assert catalog["can_update_claim_trust"] is False
    assert catalog["can_materialize_skills"] is False
    assert catalog["pack_count"] == catalog["known_pack_count"]
    assert {pack["pack_id"] for pack in catalog["packs"]} >= {"formal_theory", "gw_librpa"}
    assert all(pack["orientation_only"] is True for pack in catalog["packs"])
    formal = next(pack for pack in catalog["packs"] if pack["pack_id"] == "formal_theory")
    assert formal["workflow_graph"]["orientation_only"] is True
    assert formal["failure_taxonomy"][0]["failure_id"] == "implicit_definition_shift"


def test_domain_pack_cli_and_mcp_suggest_librpa_pack(tmp_path, capsys):
    from brain.v5.mcp_domain_packs import aitp_v5_list_domain_packs, aitp_v5_suggest_domain_packs_for_claim
    from brain.v5.public_surfaces import require_valid_public_surface

    catalog = _invoke(["--base", str(tmp_path), "domain-pack", "catalog"], capsys)
    suggested = _invoke(
        [
            "--base",
            str(tmp_path),
            "domain-pack",
            "suggest",
            "--topic",
            "librpa-gw",
            "--statement",
            "The LibRPA QSGW self-energy benchmark is reproducible from ABACUS inputs.",
            "--evidence-profile",
            "code_method",
        ],
        capsys,
    )
    mcp_catalog = aitp_v5_list_domain_packs()
    mcp_suggested = aitp_v5_suggest_domain_packs_for_claim(
        topic_id="librpa-gw",
        statement="The LibRPA QSGW self-energy benchmark is reproducible from ABACUS inputs.",
        evidence_profile="code_method",
    )

    assert require_valid_public_surface("domain_pack_catalog", catalog) == catalog
    assert require_valid_public_surface("domain_pack_catalog", suggested) == suggested
    assert require_valid_public_surface("domain_pack_catalog", mcp_catalog) == mcp_catalog
    assert require_valid_public_surface("domain_pack_catalog", mcp_suggested) == mcp_suggested
    assert [pack["pack_id"] for pack in suggested["packs"]] == ["gw_librpa"]
    assert suggested["claim_context"]["evidence_profile"] == "code_method"
    assert mcp_suggested["packs"][0]["skill_refs"][0]["skill_id"] == "oh-my-librpa"
    assert mcp_suggested["packs"][0]["skill_refs"][0]["orientation_only"] is True


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

    domain_packs = brief["known_context"]["domain_packs"]
    assert domain_packs[0]["pack_id"] == "gw_librpa"
    assert domain_packs[0]["orientation_only"] is True
    assert domain_packs[0]["truth_standard_policy"] == "global_only"
    assert domain_packs[0]["lane_policy"]["default_lane"] == "diagnostic"
    assert domain_packs[0]["workflow_graph"]["orientation_only"] is True
    assert any(item["failure_id"] == "hpc_runtime_not_science" for item in domain_packs[0]["failure_taxonomy"])
    assert domain_packs[0]["skill_refs"][0]["skill_id"] == "oh-my-librpa"
    assert domain_packs[0]["skill_refs"][0]["orientation_only"] is True
    assert any(
        ref["path"] == "docs/aitp-integration.md"
        for ref in domain_packs[0]["manifest_refs"]
    )
    profiles = brief["known_context"]["context_compilation_profiles"]
    profile_ids = {profile["profile_id"] for profile in profiles}
    assert "librpa_run_continuation" in profile_ids
    assert "source_reconstruction" in profile_ids
    librpa_profile = next(profile for profile in profiles if profile["profile_id"] == "librpa_run_continuation")
    assert "scheduler success proves scientific correctness" in librpa_profile["cannot_say"][1]
    assert librpa_profile["truth_policy"]["can_update_claim_trust"] is False
    recommendations = brief["known_context"]["recommended_tool_executors"]
    assert recommendations[0]["pack_id"] == "gw_librpa"
    assert recommendations[0]["executor_id"] == "metric_table_check"
    assert recommendations[0]["recipe_id"] == "recipe-librpa-gw-benchmark-table"
    assert any(
        recommendation["executor_id"] == "formula_code_invariant_check"
        and recommendation["recipe_id"] == "recipe-librpa-gw-formula-code-invariant"
        for recommendation in recommendations
    )
    assert any(
        recommendation["executor_id"] == "librpa_gw_run_metadata_check"
        and recommendation["recipe_id"] == "recipe-librpa-gw-run-metadata-diagnostic"
        for recommendation in recommendations
    )
    assert any(
        recommendation["executor_id"] == "failure_mode_basis_check"
        and recommendation["recipe_id"] == "recipe-librpa-gw-failure-mode-review-basis"
        for recommendation in recommendations
    )


def test_execution_brief_promotes_recommended_executor_into_next_action(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The FQHE edge-sector counting table matches the expected sequence.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    action = brief["next_action_candidates"][0]
    assert action["action"] == "execute_recommended_tool"
    assert action["executor_id"] == "metric_table_check"
    assert action["recipe_id"] == "recipe-fqhe-counting-table"
    assert action["supports_outputs"] == ["evidence_or_provenance", "minimal_check"]
    assert action["satisfies_missing_outputs"] == ["evidence_or_provenance", "minimal_check"]
    assert action["input_schema"]["required"] == ["metrics"]
    assert action["rank"] == 1


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
