from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def _seed_workspace(tmp_path, *, session_id: str = "s-hs"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-chain", context_id="spin-chains", title="Long-range Heisenberg chain")
    claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="Alpha=2 sector resolution must precede level-statistics conclusions.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="sector convention is not yet authoritative",
    )
    bind_session(
        ws,
        session_id,
        topic_id="hs-chain",
        context_id="spin-chains",
        active_claim=claim.claim_id,
    )
    return ws, claim


def test_context_pack_is_bounded_codex_context_not_memory_or_trust(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_workspace(tmp_path)

    pack = require_valid_public_surface(
        "aitp_context_pack",
        build_aitp_context_pack(ws, "s-hs", max_lines=50, candidate_limit=2),
    )
    same_pack = build_aitp_context_pack(ws, "s-hs", max_lines=50, candidate_limit=2)

    assert pack["kind"] == "aitp_context_pack"
    assert pack["designed_for_host"] == "codex"
    assert pack["requested_task_profile"] == ""
    assert pack["task_profile"] == {}
    assert pack["profile_template_hint"] == {}
    assert pack["fingerprint"] == same_pack["fingerprint"]
    assert pack["pack_id"].startswith("aitp-context-pack-s-hs-")
    assert pack["line_count"] <= 50
    assert pack["orientation_only"] is True
    assert pack["can_update_kernel_state"] is False
    assert pack["can_update_claim_trust"] is False
    assert pack["can_materialize_without_human_review"] is False
    assert pack["materialization_boundary"]["can_create_skill"] is False
    assert pack["materialization_boundary"]["requires_human_review_before_materialization"] is True
    assert pack["injection_policy"]["recommended_hook"] == "TurnInputContributor"
    assert "full relation-map audit" in pack["injection_policy"]["requires_explicit_expand_for"]
    assert "mcp_context_pack" in pack["expand"]
    assert "mcp_full_relation_map" in pack["expand"]
    assert pack["relevant_claims"][0]["claim_id"] == claim.claim_id
    assert pack["distillation_status"]["top_candidates"][0]["can_materialize_without_human_review"] is False
    assert pack["distillation_status"]["top_candidates"][0]["missing_requirements"]


def test_context_pack_accounts_for_candidates_hidden_by_host_limit(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws, _claim = _seed_workspace(tmp_path)
    for index in range(3):
        create_claim(
            ws,
            topic_id="hs-chain",
            statement=f"Alternative sector convention {index} requires comparison.",
            evidence_profile="semi_formal_theory",
            confidence_state="candidate",
            active_uncertainty="The sector map remains unvalidated.",
        )
    build_query_index(ws)

    pack = build_aitp_context_pack(ws, "s-hs", candidate_limit=1, max_lines=12)

    assert len(pack["distillation_status"]["top_candidates"]) == 1
    assert pack["not_shown_count"] >= 3
    assert "context_pack_candidate_limit" in pack["not_shown_reason"]
    candidate = pack["distillation_status"]["top_candidates"][0]
    assert candidate["family"]
    assert candidate["status"] == "hypothesis"
    assert isinstance(candidate["retrieval_rank"], int)
    assert isinstance(candidate["retrieval_score"], int)
    assert pack["partial"] is True
    assert pack["render_truncated"] is True
    assert pack["orientation_only"] is True
    assert pack["can_update_claim_trust"] is False


def test_context_pack_fingerprint_ignores_noop_index_generation(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.query_index import build_query_index

    ws, _claim = _seed_workspace(tmp_path)
    build_query_index(ws)
    first = build_aitp_context_pack(ws, "s-hs", candidate_limit=2)

    build_query_index(ws)
    second = build_aitp_context_pack(ws, "s-hs", candidate_limit=2)

    assert second["source_index_generation"] == first["source_index_generation"] + 1
    assert second["fingerprint"] == first["fingerprint"]
    assert second["pack_id"] == first["pack_id"]


def test_context_pack_can_compile_explicit_task_profile(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _claim = _seed_workspace(tmp_path)

    pack = require_valid_public_surface(
        "aitp_context_pack",
        build_aitp_context_pack(
            ws,
            "s-hs",
            max_lines=55,
            candidate_limit=2,
            task_profile="librpa_run_continuation",
        ),
    )

    assert pack["requested_task_profile"] == "librpa_run_continuation"
    assert pack["task_profile"]["profile_id"] == "librpa_run_continuation"
    assert pack["task_profile"]["truth_policy"]["can_update_claim_trust"] is False
    assert pack["profile_template_hint"]["profile_id"] == "librpa_run_continuation"
    assert pack["profile_template_hint"]["output_shape"] == "continuation_report_template"
    assert "lane_policy" in pack["profile_template_hint"]["required_section_ids"]
    assert "hpc_cockpit" in pack["profile_template_hint"]["read_only_surfaces_to_expand"]
    assert "claim_trust_update" in pack["profile_template_hint"]["forbidden_uses"]
    assert pack["profile_template_hint"]["trust_boundary"]["claim_trust_mutation"] == "none"
    assert pack["profile_template_hint"]["read_only"] is True
    assert pack["profile_template_hint"]["orientation_only"] is True
    assert pack["profile_template_hint"]["can_update_claim_trust"] is False
    assert "task-profile must-verify checks" in pack["injection_policy"]["requires_explicit_expand_for"]
    assert "--task-profile librpa_run_continuation" in pack["expand"]["context_pack_cli"]
    assert "--profile librpa_run_continuation" in pack["expand"]["context_profile_templates_cli"]
    assert pack["expand"]["mcp_context_profile_templates"] == "aitp_v5_get_context_profile_templates"
    assert "context_profile_template_catalog" in pack["source_records"]["derived_surfaces"]
    assert any(line.startswith("Task profile: librpa_run_continuation") for line in pack["context_lines"])
    assert any(line.startswith("Template output shape: continuation_report_template") for line in pack["context_lines"])
    assert any(line.startswith("Template sections:") and "lane_policy" in line for line in pack["context_lines"])


def test_context_pack_cli_and_mcp_return_valid_public_surface(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_get_context_pack

    _seed_workspace(tmp_path, session_id="s-cli")

    cli_pack = _invoke(
        [
            "--base",
            str(tmp_path),
            "status",
            "context-pack",
            "s-cli",
            "--max-lines",
            "45",
            "--candidate-limit",
            "1",
            "--task-profile",
            "paper_learning",
        ],
        capsys,
    )
    mcp_pack = aitp_v5_get_context_pack(
        str(tmp_path),
        session_id="s-cli",
        max_lines=45,
        candidate_limit=1,
        task_profile="paper_learning",
    )

    assert cli_pack["kind"] == "aitp_context_pack"
    assert mcp_pack["kind"] == "aitp_context_pack"
    assert cli_pack["fingerprint"] == mcp_pack["fingerprint"]
    assert cli_pack["task_profile"]["profile_id"] == "paper_learning"
    assert cli_pack["profile_template_hint"]["profile_id"] == "paper_learning"
    assert cli_pack["profile_template_hint"]["trust_boundary"][
        "requires_exact_source_anchors_for_literature_support"
    ] is True
    assert cli_pack["line_count"] <= 45
    assert mcp_pack["injection_policy"]["host"] == "codex"


def test_context_profiles_recommend_paired_and_multi_paper_learning_routes():
    from brain.v5.context_profiles import suggest_context_profiles_for_claim
    from brain.v5.models import ClaimRecord

    paired_claim = ClaimRecord(
        claim_id="claim-paired",
        topic_id="qg-two-paper-reading",
        statement="Compare both papers before synthesizing the wormhole and baby-universe assumptions.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="paired paper source anchors are missing",
    )
    multi_claim = ClaimRecord(
        claim_id="claim-multi",
        topic_id="qft-source-set",
        statement="Build a cross-paper source set before claiming the renormalization convention is shared.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="multi-paper convention conflicts are unresolved",
    )

    paired_profiles = {profile["profile_id"] for profile in suggest_context_profiles_for_claim(paired_claim)}
    multi_profiles = {profile["profile_id"] for profile in suggest_context_profiles_for_claim(multi_claim)}

    assert {"paper_learning", "paired_paper_learning", "closeout"} <= paired_profiles
    assert {"paper_learning", "multi_paper_learning_route", "closeout"} <= multi_profiles


def test_context_profile_template_catalog_covers_all_task_profiles_and_boundaries():
    from brain.v5.context_profile_templates import build_context_profile_template_catalog
    from brain.v5.context_profiles import builtin_context_profiles
    from brain.v5.public_surfaces import require_valid_public_surface

    catalog = require_valid_public_surface(
        "context_profile_template_catalog",
        build_context_profile_template_catalog(),
    )

    assert catalog["kind"] == "context_profile_template_catalog"
    assert catalog["profile_ids"] == list(builtin_context_profiles())
    assert catalog["profile_count"] == 8
    assert catalog["template_count"] == 8
    assert catalog["read_only"] is True
    assert catalog["orientation_only"] is True
    assert catalog["can_update_claim_trust"] is False
    assert catalog["claim_trust_mutation"] == "none"
    assert "claim_trust_update" in catalog["template_policy"]["forbidden_uses"]
    assert "trust_apply" in catalog["template_policy"]["forbidden_uses"]

    for template in catalog["templates"]:
        assert template["kind"] == "context_profile_template"
        assert template["profile_id"] in builtin_context_profiles()
        assert template["required_sections"]
        assert template["can_say"]
        assert template["cannot_say_yet"]
        assert template["must_verify_before_trust_or_promotion"]
        assert template["read_only_surfaces_to_expand"]
        assert template["recommended_next_entrypoints"][0].endswith(
            f"--task-profile {template['profile_id']}"
        )
        assert template["report_template"]["orientation_only"] is True
        assert template["closeout_template"]["orientation_only"] is True
        assert template["read_only"] is True
        assert template["orientation_only"] is True
        assert template["records_validation_result"] is False
        assert template["source_support_result"] is False
        assert template["can_update_kernel_state"] is False
        assert template["can_update_claim_trust"] is False
        assert template["claim_trust_mutation"] == "none"
        assert "validation_result" in template["forbidden_uses"]
        assert "final_gate_satisfaction" in template["forbidden_uses"]


def test_context_profile_template_catalog_cli_and_mcp_can_filter_profiles(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_get_context_profile_templates

    cli_payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "status",
            "context-profile-templates",
            "--profile",
            "closeout",
            "--profile",
            "group_meeting_report",
        ],
        capsys,
    )
    mcp_payload = aitp_v5_get_context_profile_templates(
        str(tmp_path),
        profile_ids=["closeout", "group_meeting_report"],
    )

    assert cli_payload == mcp_payload
    assert cli_payload["profile_ids"] == ["closeout", "group_meeting_report"]
    assert [template["profile_id"] for template in cli_payload["templates"]] == [
        "closeout",
        "group_meeting_report",
    ]
    assert cli_payload["unknown_profile_ids"] == []
