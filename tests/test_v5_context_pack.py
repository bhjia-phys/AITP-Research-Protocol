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
        ],
        capsys,
    )
    mcp_pack = aitp_v5_get_context_pack(str(tmp_path), session_id="s-cli", max_lines=45, candidate_limit=1)

    assert cli_pack["kind"] == "aitp_context_pack"
    assert mcp_pack["kind"] == "aitp_context_pack"
    assert cli_pack["fingerprint"] == mcp_pack["fingerprint"]
    assert cli_pack["line_count"] <= 45
    assert mcp_pack["injection_policy"]["host"] == "codex"
