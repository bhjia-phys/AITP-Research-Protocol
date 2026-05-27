from __future__ import annotations

import json


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="Final and diagnostic QSGW lanes must remain separated.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="diagnostic plots may be mistaken for final evidence",
    )
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim


def test_record_run_iteration_materializes_markdown_first_journal(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.run_iterations import load_run_iterations, record_run_iteration

    ws, claim = _seed_workspace(tmp_path)

    record = record_run_iteration(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        run_id="run-20260528-qsgw-dual-lane",
        iteration_id="iter-001",
        plan_summary="Refresh existing BN/MgO/Si status without running numerical work.",
        deliverables=["diagnostic TSV freshness check", "final-lane non-contamination check"],
        checks=["no contaminated MgO root", "final plots unchanged unless final-usable hash changes"],
        stop_rules=["do not run compute on dongfang login node"],
        l4_return_summary="Read-only refresh found no new final-usable rows.",
        l4_artifact_refs=["report:research/librpa/reports/qsgw_status.tsv"],
        l3_synthesis_summary="Continue diagnostic lane only; final lane remains unchanged.",
        decision="continue_diagnostic_lane",
        status="synthesized",
        source_refs=["tool_run:qsgw-refresh-smoke"],
        claim_id=claim.claim_id,
    )

    assert record.kind == "run_iteration"
    assert record.summary_inputs_trusted is False
    assert record.can_update_claim_trust is False
    assert require_valid_public_surface("run_iteration_record", {"ok": True, **record.__dict__})

    run_root = ws.topic_dir("qsgw-headwing-update-librpa") / "L3" / "runs" / "run-20260528-qsgw-dual-lane"
    journal_frontmatter, journal_body = read_md(run_root / "iteration_journal.md")
    journal_json = json.loads((run_root / "iteration_journal.json").read_text(encoding="utf-8"))
    assert journal_frontmatter["kind"] == "run_iteration_journal"
    assert "Markdown is the human review surface" in journal_body
    assert journal_json["human_review_surface"] == "iteration_journal.md"
    assert journal_json["iterations"][0]["iteration_id"] == "iter-001"
    assert journal_json["iterations"][0]["status"] == "synthesized"
    assert journal_json["can_update_claim_trust"] is False

    iteration_dir = run_root / "iterations" / "iter-001"
    plan_frontmatter, plan_body = read_md(iteration_dir / "plan.md")
    l4_frontmatter, l4_body = read_md(iteration_dir / "l4_return.md")
    synthesis_frontmatter, synthesis_body = read_md(iteration_dir / "l3_synthesis.md")
    plan_contract = json.loads((iteration_dir / "plan.contract.json").read_text(encoding="utf-8"))
    l4_contract = json.loads((iteration_dir / "l4_return.json").read_text(encoding="utf-8"))
    synthesis_contract = json.loads((iteration_dir / "l3_synthesis.json").read_text(encoding="utf-8"))

    assert plan_frontmatter["kind"] == "run_iteration_plan"
    assert "no contaminated MgO root" in plan_body
    assert l4_frontmatter["kind"] == "run_iteration_l4_return"
    assert "no new final-usable rows" in l4_body
    assert synthesis_frontmatter["kind"] == "run_iteration_l3_synthesis"
    assert "final lane remains unchanged" in synthesis_body
    assert plan_contract["thin_machine_contract"] is True
    assert l4_contract["artifact_refs"] == ["report:research/librpa/reports/qsgw_status.tsv"]
    assert synthesis_contract["decision"] == "continue_diagnostic_lane"

    loaded = load_run_iterations(ws, "qsgw-headwing-update-librpa")
    assert loaded["present"] is True
    assert loaded["items"][0]["run_id"] == "run-20260528-qsgw-dual-lane"
    assert loaded["items"][0]["last_iteration_id"] == "iter-001"
    assert loaded["items"][0]["orientation_only"] is True
    assert loaded["can_update_claim_trust"] is False


def test_execution_brief_and_topic_status_expose_run_iteration_continuity(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.run_iterations import record_run_iteration
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim = _seed_workspace(tmp_path)
    record_run_iteration(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        run_id="run-20260528-qsgw-dual-lane",
        iteration_id="iter-001",
        plan_summary="Check diagnostic trend plots only.",
        deliverables=["diagnostic plot freshness"],
        checks=["keep final-only figures untouched"],
        stop_rules=["do not promote diagnostic rows"],
        l4_return_summary="Diagnostic plot refreshed from existing TSV.",
        l3_synthesis_summary="Use diagnostic plot for group discussion only.",
        decision="keep_final_lane_closed",
        status="synthesized",
        claim_id=claim.claim_id,
    )

    brief = build_execution_brief(ws, "qsgw-session")
    run_iterations = brief["known_context"]["run_iterations"]
    assert run_iterations["present"] is True
    assert run_iterations["items"][0]["decision"] == "keep_final_lane_closed"
    assert run_iterations["can_update_claim_trust"] is False
    assert require_valid_public_surface("execution_brief", brief) == brief

    topic_status = write_topic_status_surfaces(ws, session_id="qsgw-session")
    assert topic_status["topic_state"]["run_iterations"]["items"][0]["last_iteration_status"] == "synthesized"
    assert topic_status["topic_state"]["run_iterations"]["can_update_claim_trust"] is False
    assert require_valid_public_surface("topic_status_bundle", topic_status) == topic_status


def test_run_iteration_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_record_run_iteration
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, claim = _seed_workspace(tmp_path)

    assert main([
        "--base",
        str(tmp_path),
        "run",
        "iteration",
        "record",
        "--topic",
        "qsgw-headwing-update-librpa",
        "--run",
        "run-20260528-qsgw-dual-lane",
        "--iteration",
        "iter-001",
        "--plan-summary",
        "Refresh existing status.",
        "--deliverable",
        "diagnostic TSV freshness check",
        "--check",
        "final lane unchanged",
        "--stop-rule",
        "read-only remote status",
        "--l4-return-summary",
        "No new final rows.",
        "--l3-synthesis-summary",
        "Continue diagnostic lane.",
        "--decision",
        "continue_diagnostic_lane",
        "--status",
        "synthesized",
        "--claim",
        claim.claim_id,
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_record_run_iteration(
        str(ws.base),
        topic_id="qsgw-headwing-update-librpa",
        run_id="run-20260528-qsgw-dual-lane",
        iteration_id="iter-002",
        plan_summary="Check group-meeting diagnostic figure request.",
        deliverables=["diagnostic figure note"],
        checks=["label diagnostic outputs"],
        stop_rules=["no trust update"],
        l4_return_summary="Figure request classified as diagnostic.",
        l3_synthesis_summary="Record as workflow continuity, not evidence.",
        decision="record_diagnostic_only",
        status="synthesized",
        claim_id=claim.claim_id,
    )

    assert cli_payload["kind"] == "run_iteration"
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["kind"] == "run_iteration"
    assert mcp_payload["iteration_id"] == "iter-002"
    assert mcp_payload["can_update_kernel_state"] is True
    assert runtime_entrypoints()["record_run_iteration"] == {
        "cli": "aitp-v5 run iteration record <args>",
        "mcp": "aitp_v5_record_run_iteration",
        "surface": "run_iteration_record",
    }
