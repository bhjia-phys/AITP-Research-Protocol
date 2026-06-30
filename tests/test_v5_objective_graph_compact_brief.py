from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_objective_graph_and_compact_brief_are_read_only_phase1_surfaces(tmp_path):
    from brain.v5.objective_graph import build_compact_brief, build_objective_graph
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-chain", context_id="spin-chains", title="Long-range Heisenberg chain")
    active_claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="Alpha=2 sectors should be resolved before level-statistics conclusions.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="sector convention is not yet authoritative",
    )
    sibling_claim = create_claim(
        ws,
        topic_id="hs-chain",
        statement="Generic finite-alpha symmetry has a family-common center.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="all-L proof remains open",
    )
    bind_session(
        ws,
        "s-hs",
        topic_id="hs-chain",
        context_id="spin-chains",
        active_claim=active_claim.claim_id,
    )

    graph = require_valid_public_surface("objective_graph", build_objective_graph(ws, "s-hs"))
    compact = require_valid_public_surface("compact_execution_brief", build_compact_brief(ws, "s-hs"))

    assert graph["orientation_only"] is True
    assert graph["can_update_claim_trust"] is False
    assert graph["current_objective"]["title"] == "Long-range Heisenberg chain"
    assert {claim["claim_id"] for claim in graph["claims"]} == {active_claim.claim_id, sibling_claim.claim_id}
    assert graph["active_work_packages"][0]["claim_ids"] == [active_claim.claim_id]

    assert compact["orientation_only"] is True
    assert compact["can_update_claim_trust"] is False
    assert compact["active_work_package"]["claim_ids"] == [active_claim.claim_id]
    assert compact["relevant_claims"][0]["claim_id"] == active_claim.claim_id
    assert "mcp_full_relation_map" in compact["expand"]
    assert compact["line_count"] <= 40


def test_compact_brief_cli_preserves_existing_full_brief(tmp_path, capsys):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    _invoke(
        [
            "--base",
            str(tmp_path),
            "session",
            "bind",
            "s1",
            "--topic",
            "fqhe",
            "--context",
            "topological-order",
            "--claim",
            claim.claim_id,
        ],
        capsys,
    )

    full_brief = _invoke(["--base", str(tmp_path), "brief", "s1"], capsys)
    compact = _invoke(["--base", str(tmp_path), "status", "compact-brief", "s1"], capsys)

    assert full_brief["current_focus"]["active_claim"] == claim.claim_id
    assert full_brief["risk_assessment"]["level"] in {"guided", "rigorous", "adversarial", "fluid"}
    assert compact["kind"] == "compact_execution_brief"
    assert compact["topic_id"] == "fqhe"
    assert compact["line_count"] <= 40
    assert compact["can_update_claim_trust"] is False


def test_compact_brief_mcp_wrapper_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_get_compact_brief, aitp_v5_get_objective_graph
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW run is diagnostic until final lane provenance is complete.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="runtime provenance",
    )
    bind_session(ws, "s-gw", topic_id="librpa-gw", context_id="gw", active_claim=claim.claim_id)

    graph = aitp_v5_get_objective_graph(str(tmp_path), session_id="s-gw")
    compact = aitp_v5_get_compact_brief(str(tmp_path), session_id="s-gw")

    assert graph["kind"] == "objective_graph"
    assert compact["kind"] == "compact_execution_brief"
    assert compact["summary_inputs_trusted"] is False
    assert compact["can_update_kernel_state"] is False
