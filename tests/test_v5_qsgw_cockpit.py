from __future__ import annotations

import json
from pathlib import Path


TOPIC_ID = "qsgw-headwing-update-librpa"


def _setup_workspace(tmp_path: Path):
    from brain.v5.evidence import record_evidence
    from brain.v5.lane_exemplars import record_lane_exemplar
    from brain.v5.operator_checkpoint import request_operator_checkpoint
    from brain.v5.output_stability import record_final_output_profile
    from brain.v5.references import record_reference_location
    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.strategy_memory import record_strategy_memory
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, TOPIC_ID, context_id="librpa", title="QSGW head-wing")
    claim = create_claim(
        ws,
        topic_id=TOPIC_ID,
        statement="Final comparison uses only usable_for_final QSGW rows.",
        evidence_profile="code_method",
        confidence_state="partial",
        active_uncertainty="Final/diagnostic boundaries must stay explicit.",
    )
    final_evidence = record_evidence(
        ws,
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        evidence_type="final_lane_table",
        status="supports",
        summary="Final-usable BN row from clean qsgw_status_manifest.json.",
        supports_outputs=["final_comparison_table"],
        source_refs=["report:qsgw_status_manifest.json#usable_for_final"],
    )
    diagnostic_evidence = record_evidence(
        ws,
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        evidence_type="diagnostic_gap_history",
        status="mixed",
        summary="Diagnostic iter20 assumption is useful for trend finding only.",
        supports_outputs=["diagnostic_iter20_trend"],
        source_refs=["report:diagnostic_gap_history.tsv"],
    )
    record_tool_run(
        ws,
        recipe_id="recipe-refresh-qsgw-status",
        tool_family="local_script",
        tool_name="refresh_qsgw_remote_status.py",
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        inputs={"root": "/data/home/df_iopcas_bhj/ai-runs/mgo-qsgw-k999-headonly-kconv-20260523-1210-nohardlink"},
        outputs={"manifest": "research/librpa/reports/qsgw_status_manifest.json"},
        evidence_status="unreviewed",
    )
    record_reference_location(
        ws,
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        connector_id="local_report",
        location_type="report",
        uri="file://research/librpa/reports/qsgw_status_manifest.json",
        label="QSGW status manifest",
        summary="Orientation pointer to refresh output.",
    )
    create_validation_contract(
        ws,
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        required_checks=["clean_root", "final_usable_manifest"],
        failure_modes=["contaminated_root", "diagnostic_row_leak"],
        required_evidence_outputs=["final_comparison_table"],
    )
    record_sensemaking_report(
        ws,
        topic_id=TOPIC_ID,
        claim_id=claim.claim_id,
        title="Dual-lane scope guard",
        summary="Diagnostic plots can guide work but do not support final claim confidence.",
        open_questions=["Which rows are final usable after the next refresh?"],
        next_actions=["Review final allowlist before plotting."],
    )
    bind_session(ws, "qsgw-session", topic_id=TOPIC_ID, context_id="librpa", active_claim=claim.claim_id)
    record_final_output_profile(
        ws,
        topic_id=TOPIC_ID,
        output_version="qsgw-headwing-dual-lane-v1",
        audience="future_agent",
        stable_sections=["current_data_state", "final_lane", "diagnostic_lane", "next_actions"],
        flexible_sections=["open_questions"],
        change_policy="Additive changes only unless the output version changes.",
    )
    record_lane_exemplar(
        ws,
        topic_id=TOPIC_ID,
        lane="code_backed_algorithm",
        title="QSGW final/diagnostic dual-lane workflow",
        summary="Use final-only evidence for paper claims and diagnostic evidence only for trend finding.",
        claim_id=claim.claim_id,
        run_id="run-qsgw",
        gates_demonstrated=["final_lane_gate", "diagnostic_lane_labeling"],
        artifact_refs=["report:research/librpa/reports/dual_lane_strategy.md"],
        trust_boundary="Workflow exemplar only; it must not update claim trust.",
        status="accepted",
    )
    record_strategy_memory(
        ws,
        topic_id=TOPIC_ID,
        run_id="run-qsgw",
        strategy_type="scope_control",
        outcome="helped",
        lesson="Keep final and diagnostic lanes separate.",
        next_time_rule="Never mix diagnostic trend plots into final claims.",
        scope="QSGW reporting",
    )
    request_operator_checkpoint(
        ws,
        topic_id=TOPIC_ID,
        checkpoint_kind="contradiction_adjudication_choice",
        question="Should we revise the active claim before next final plot?",
        options=["revise_active_claim", "leave_claim_unchanged"],
        requested_by="cockpit_test",
        claim_id=claim.claim_id,
    )
    reports = ws.base / "research" / "librpa" / "reports"
    scripts = ws.base / "research" / "librpa" / "scripts"
    reports.mkdir(parents=True)
    scripts.mkdir(parents=True)
    (reports / "qsgw_final_usable_summary.tsv").write_text(
        "material\tusable_for_final\troot\nBN\tTrue\t/data/home/df_iopcas_bhj/ai-runs/mgo-qsgw-k999-headonly-kconv-20260523-1210-nohardlink\n",
        encoding="utf-8",
    )
    (reports / "qsgw_diagnostic_iter20_gap_history.tsv").write_text("diagnostic only\n", encoding="utf-8")
    (scripts / "refresh_qsgw_remote_status.py").write_text("# refresh script\n", encoding="utf-8")
    (scripts / "plot_qsgw_final_comparison.py").write_text("# plot script\n", encoding="utf-8")
    return ws, claim, final_evidence, diagnostic_evidence


def test_qsgw_cockpit_writes_guarded_orientation_surfaces(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.qsgw_cockpit import write_qsgw_cockpit_surfaces

    ws, claim, final_evidence, diagnostic_evidence = _setup_workspace(tmp_path)

    bundle = write_qsgw_cockpit_surfaces(ws)
    manifest_path = Path(bundle["files"]["manifest"])
    dashboard_path = Path(bundle["files"]["dashboard_dry_run"])
    plot_guard_path = Path(bundle["files"]["plot_guard"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dashboard = dashboard_path.read_text(encoding="utf-8")
    plot_guard = plot_guard_path.read_text(encoding="utf-8")

    assert require_valid_public_surface("qsgw_cockpit_bundle", bundle) == bundle
    assert bundle["orientation_only"] is True
    assert bundle["can_update_claim_trust"] is False
    assert manifest["trust_update_forbidden"] is True
    assert manifest["current_records"]["evidence_counts_by_lane"] == {
        "final": 1,
        "diagnostic": 1,
        "unclassified": 0,
    }
    assert final_evidence.evidence_id in bundle["source_records"]["evidence"]
    assert diagnostic_evidence.evidence_id in bundle["source_records"]["evidence"]
    assert claim.claim_id in manifest["current_records"]["evidence_items"][0]["claim_id"]
    assert manifest["lane_manifest"]["forbidden_roots"][0]["status"] == "forbidden"
    assert manifest["plot_guard"]["final_lane"]["requires_explicit_allowlist"] is True
    assert manifest["plot_guard"]["diagnostic_lane"]["requires_explicit_profile"] is True
    assert "usable_for_final=True" in plot_guard
    assert "Diagnostic evidence candidates: 1" in dashboard
    assert "Do not update claim trust" in dashboard


def test_qsgw_cockpit_cli_mcp_compact_and_runtime_entrypoints(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_qsgw_cockpit_surfaces, aitp_v5_write_qsgw_cockpit_surfaces_compact
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, _, _, _ = _setup_workspace(tmp_path)

    assert main(["--base", str(ws.base), "status", "qsgw-cockpit", "--compact"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_qsgw_cockpit_surfaces(str(ws.base))
    compact_payload = aitp_v5_write_qsgw_cockpit_surfaces_compact(str(ws.base))

    assert cli_payload["kind"] == "qsgw_cockpit_bundle_progress"
    assert cli_payload["source_surface"] == "qsgw_cockpit_bundle"
    assert cli_payload["topic_id"] == TOPIC_ID
    assert cli_payload["final_plot_guard_required"] is True
    assert cli_payload["diagnostic_label_required"] is True
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["kind"] == "qsgw_cockpit_bundle"
    assert compact_payload["kind"] == "qsgw_cockpit_bundle_progress"
    assert runtime_entrypoints()["qsgw_cockpit"] == {
        "cli": "aitp-v5 status qsgw-cockpit",
        "mcp": "aitp_v5_write_qsgw_cockpit_surfaces",
        "surface": "qsgw_cockpit_bundle",
    }
    assert runtime_entrypoints()["qsgw_cockpit_compact"] == {
        "cli": "aitp-v5 status qsgw-cockpit --compact",
        "mcp": "aitp_v5_write_qsgw_cockpit_surfaces_compact",
        "surface": "qsgw_cockpit_bundle",
    }
