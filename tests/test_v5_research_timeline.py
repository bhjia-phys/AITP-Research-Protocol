from __future__ import annotations


def test_research_timeline_surfaces_failed_and_superseded_routes_for_continuation(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.mcp_tools import aitp_v5_get_research_timeline
    from brain.v5.objective_graph import build_compact_brief
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_state import update_claim_status
    from brain.v5.research_timeline import build_research_timeline
    from brain.v5.tools import record_tool_run, register_tool_recipe
    from brain.v5.evidence import record_evidence
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-continuation", context_id="librpa", title="QSGW continuation")
    claim = create_claim(
        ws,
        topic_id="qsgw-continuation",
        statement="Ridge analytic continuation reduces the H2O AC tail error in the scoped replay.",
        evidence_profile="finite_evidence",
        confidence_state="hypothesis",
        active_uncertainty="cross-system Si test has not entered analytic continuation",
    )
    bind_session(ws, "s-qsgw", topic_id="qsgw-continuation", context_id="librpa", active_claim=claim.claim_id)
    register_tool_recipe(
        ws,
        recipe_id="si-ridge-replay",
        tool_family="remote_numerics",
        tool_name="slurm-librpa",
        purpose="Run Si ridge and baseline analytic-continuation replay.",
    )
    failed_run = record_tool_run(
        ws,
        recipe_id="si-ridge-replay",
        tool_family="remote_numerics",
        tool_name="slurm-librpa",
        topic_id="qsgw-continuation",
        claim_id=claim.claim_id,
        outputs={
            "failure_stage": "pre_ac",
            "failure_reason": "ScaLAPACK runtime failure before analytic continuation; does not test algorithm",
        },
        evidence_status="failed",
    )
    failure_evidence = record_evidence(
        ws,
        topic_id="qsgw-continuation",
        claim_id=claim.claim_id,
        evidence_type="runtime_failure",
        status="negative",
        summary=(
            "Si run failed before analytic continuation due to ScaLAPACK setup; "
            "this is runtime/application evidence and does not test the ridge algorithm."
        ),
        tool_run_ids=[failed_run.run_id],
    )
    old_run = record_tool_run(
        ws,
        recipe_id="si-ridge-replay",
        tool_family="remote_numerics",
        tool_name="wrong-pilot-route",
        topic_id="qsgw-continuation",
        claim_id=claim.claim_id,
        outputs={"route": "wrong pilot root"},
        evidence_status="diagnostic",
    )
    record_tool_run(
        ws,
        recipe_id="si-ridge-replay",
        tool_family="remote_numerics",
        tool_name="corrected-route",
        topic_id="qsgw-continuation",
        claim_id=claim.claim_id,
        outputs={"route": "corrected pilot root"},
        evidence_status="diagnostic",
        supersedes=old_run.run_id,
    )
    update_claim_status(
        ws,
        topic_id="qsgw-continuation",
        claim_id=claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="hypothesis_with_runtime_blocker",
        scope="H2O replay is scoped; Si attempt is blocked before AC.",
        risk="runtime failure can be mistaken for algorithm evidence",
        next_action="rerun Si baseline until it enters analytic continuation",
        open_gaps=["Si cross-system route has not tested the algorithm"],
        evidence_refs=[failure_evidence.evidence_id],
    )

    timeline = require_valid_public_surface("research_timeline", build_research_timeline(ws, "s-qsgw"))
    mcp_timeline = aitp_v5_get_research_timeline(str(tmp_path), session_id="s-qsgw")
    brief = build_execution_brief(ws, "s-qsgw")
    compact = require_valid_public_surface("compact_execution_brief", build_compact_brief(ws, "s-qsgw"))
    context_pack = require_valid_public_surface("aitp_context_pack", build_aitp_context_pack(ws, "s-qsgw"))

    failed_refs = {item["record_ref"] for item in timeline["previous_failed_attempts"]}
    assert f"tool_run:{failed_run.run_id}" in failed_refs
    assert f"evidence:{failure_evidence.evidence_id}" in failed_refs
    assert any(
        item["record_ref"] == f"tool_run:{old_run.run_id}"
        and item["classification"] == "superseded_or_duplicate_route"
        for item in timeline["wrong_or_superseded_routes"]
    )
    assert timeline["timeline_policy"]["can_update_claim_trust"] is False
    assert timeline["timeline_policy"]["can_rebind_without_confirmation"] is False
    assert mcp_timeline["kind"] == "research_timeline"

    brief_attempts = brief["known_context"]["previous_failed_attempts"]
    assert any(item["record_id"] == failed_run.run_id for item in brief_attempts)
    assert compact["previous_failed_attempts"]
    assert compact["expand"]["mcp_research_timeline"] == "aitp_v5_get_research_timeline"
    assert context_pack["previous_failed_attempts"]
    assert any("Previous failed or superseded routes" in line for line in context_pack["context_lines"])
