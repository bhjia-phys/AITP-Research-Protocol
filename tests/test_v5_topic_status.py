from __future__ import annotations

import json
import os
from pathlib import Path


def _setup_workspace(tmp_path: Path):
    from brain.v5.evidence import record_evidence
    from brain.v5.operator_checkpoint import request_operator_checkpoint
    from brain.v5.output_stability import record_final_output_profile
    from brain.v5.strategy_memory import record_strategy_memory
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="Final comparison uses only usable_for_final QSGW rows.",
        evidence_profile="code_method",
        confidence_state="partial",
        active_uncertainty="Remote status and final-row freshness still need checks.",
    )
    evidence = record_evidence(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        claim_id=claim.claim_id,
        evidence_type="diagnostic_table",
        status="mixed",
        summary="Diagnostic rows are useful for trends but cannot support final claims.",
        supports_outputs=["diagnostic_nonfinal_qsgw_history"],
        source_refs=["report:qsgw-headwing"],
    )
    bind_session(ws, "qsgw-session", topic_id="qsgw-headwing-update-librpa", context_id="librpa", active_claim=claim.claim_id)
    record_final_output_profile(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        output_version="qsgw-headwing-dual-lane-v1",
        audience="future_agent",
        stable_sections=["current_data_state", "final_lane", "diagnostic_lane", "next_actions"],
        flexible_sections=["open_questions"],
        change_policy="Breaking changes require a new output version.",
    )
    request_operator_checkpoint(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_kind="benchmark_validation_route_choice",
        question="Should the next artifact be final-only or diagnostic?",
        options=["final_only", "diagnostic_appendix"],
        requested_by="runtime",
        claim_id=claim.claim_id,
    )
    record_strategy_memory(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        run_id="run-qsgw",
        strategy_type="scope_control",
        outcome="helped",
        lesson="Keep final and diagnostic lanes separate.",
        next_time_rule="Never mix diagnostic trend plots into final claims.",
        scope="QSGW reporting",
    )
    return ws, claim, evidence


def test_write_topic_status_surfaces_materializes_explainability_files(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim, evidence = _setup_workspace(tmp_path)

    bundle = write_topic_status_surfaces(ws, session_id="qsgw-session")
    runtime_dir = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime"
    topic_state = json.loads((runtime_dir / "topic_state.json").read_text(encoding="utf-8"))
    dashboard = (runtime_dir / "topic_dashboard.md").read_text(encoding="utf-8")
    console = (runtime_dir / "operator_console.md").read_text(encoding="utf-8")

    assert bundle["kind"] == "topic_status_bundle"
    assert bundle["orientation_only"] is True
    assert bundle["can_update_claim_trust"] is False
    assert bundle["files"] == {
        "topic_state": str(runtime_dir / "topic_state.json"),
        "topic_dashboard": str(runtime_dir / "topic_dashboard.md"),
        "operator_console": str(runtime_dir / "operator_console.md"),
        "runtime_protocol": str(runtime_dir / "runtime_protocol.generated.md"),
        "session_start": str(runtime_dir / "session_start.generated.md"),
    }
    assert topic_state["active_claim_id"] == claim.claim_id
    assert topic_state["last_evidence_return"]["evidence_id"] == evidence.evidence_id
    assert topic_state["active_operator_checkpoint"]["question"].startswith("Should the next artifact")
    assert topic_state["final_output_profile"]["output_version"] == "qsgw-headwing-dual-lane-v1"
    assert topic_state["strategy_memory"]["items"][0]["lesson"] == "Keep final and diagnostic lanes separate."
    assert "Last meaningful evidence return" in dashboard
    assert "Should the next artifact" in console
    assert require_valid_public_surface("topic_status_bundle", bundle) == bundle


def test_topic_status_uses_latest_evidence_file_mtime_not_id_order(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim, first_evidence = _setup_workspace(tmp_path)
    latest_evidence = None
    for index in range(128):
        candidate = record_evidence(
            ws,
            topic_id="qsgw-headwing-update-librpa",
            claim_id=claim.claim_id,
            evidence_type=f"freshness_guardrail_{index:03d}",
            status="contradicts",
            summary=f"Latest freshness guardrail candidate {index}.",
            supports_outputs=["freshness_guardrail"],
        )
        if candidate.evidence_id < first_evidence.evidence_id:
            latest_evidence = candidate
            break
    assert latest_evidence is not None
    latest_path = ws.registry_dir("evidence") / f"{latest_evidence.evidence_id}.md"
    for path in ws.registry_dir("evidence").glob("*.md"):
        os.utime(path, (1000, 1000))
    os.utime(latest_path, (2000, 2000))

    bundle = write_topic_status_surfaces(ws, session_id="qsgw-session")

    assert latest_evidence.evidence_id < first_evidence.evidence_id
    assert bundle["topic_state"]["last_evidence_return"]["evidence_id"] == latest_evidence.evidence_id


def test_topic_status_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_topic_status_surfaces
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, _, _ = _setup_workspace(tmp_path)

    assert main(["--base", str(ws.base), "status", "topic", "qsgw-session"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_topic_status_surfaces(str(ws.base), session_id="qsgw-session")

    assert require_valid_public_surface("topic_status_bundle", cli_payload) == cli_payload
    assert require_valid_public_surface("topic_status_bundle", mcp_payload) == mcp_payload
    assert runtime_entrypoints()["topic_status"] == {
        "cli": "aitp-v5 status topic <session-id>",
        "mcp": "aitp_v5_write_topic_status_surfaces",
        "surface": "topic_status_bundle",
    }
