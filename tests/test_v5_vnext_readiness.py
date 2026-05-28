from __future__ import annotations

import json


def test_vnext_readiness_manifest_reports_control_plane_and_lane_backlog(tmp_path):
    from brain.v5.lane_exemplars import record_lane_exemplar
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.vnext_readiness import build_vnext_readiness_manifest
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    record_lane_exemplar(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        lane="code_backed_algorithm",
        title="QSGW final/diagnostic lane split",
        summary="Code-backed workflow exemplar keeps final and diagnostic lanes separate.",
        gates_demonstrated=["G2", "G3", "G4"],
        artifact_refs=["research/librpa/reports/qsgw_final.tsv"],
        trust_boundary="Workflow exemplar only; not claim evidence.",
        status="accepted",
    )

    payload = build_vnext_readiness_manifest(ws)

    assert payload["kind"] == "vnext_readiness_manifest"
    assert payload["control_plane_status"] == "ready_with_lane_exemplar_backlog"
    assert payload["phase_statuses"] == {
        "phase_1_research_intent_and_steering": "implemented",
        "phase_2_operator_checkpoint": "implemented",
        "phase_3_topic_status_explainability": "implemented",
        "phase_4_strategy_memory": "implemented",
        "phase_5_lane_exemplars": "backlog",
        "adapter_bootstrap_conformance": "priority_hosts_ready_opencode_deferred",
        "human_output_stability": "implemented",
        "literature_intake_assistant": "implemented",
    }
    assert payload["backlog_workstreams"] == ["lane_exemplars"]
    assert payload["missing_workstreams"] == []
    assert payload["lane_exemplar_manifest"]["covered_lanes"] == ["code_backed_algorithm"]
    assert payload["lane_exemplar_manifest"]["missing_lanes"] == ["toy_numeric", "semi_formal_theory"]
    assert payload["stable_output_spine"] == [
        "core_claim_or_current_focus",
        "verified_or_validated_content",
        "hypotheses_uncertainty_and_known_failure_modes",
        "aitp_records_written_or_referenced",
        "next_actions",
        "long_term_memory_candidates_and_non_promotable_content",
    ]
    assert payload["trust_update_forbidden"] is True
    assert payload["can_update_claim_trust"] is False
    assert require_valid_public_surface("vnext_readiness_manifest", payload) == payload


def test_vnext_readiness_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_vnext_readiness_manifest
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    assert main(["--base", str(ws.base), "status", "vnext-readiness"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_vnext_readiness_manifest(str(ws.base))

    assert cli_payload["kind"] == "vnext_readiness_manifest"
    assert mcp_payload["kind"] == "vnext_readiness_manifest"
    assert require_valid_public_surface("vnext_readiness_manifest", cli_payload) == cli_payload
    assert require_valid_public_surface("vnext_readiness_manifest", mcp_payload) == mcp_payload
    assert runtime_entrypoints()["vnext_readiness_manifest"] == {
        "cli": "aitp-v5 status vnext-readiness",
        "mcp": "aitp_v5_build_vnext_readiness_manifest",
        "surface": "vnext_readiness_manifest",
    }


def test_vnext_readiness_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.lane_exemplars import record_lane_exemplar
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record_lane_exemplar(
        ws,
        topic_id="toy-topic",
        lane="toy_numeric",
        title="Toy numeric lane",
        summary="A toy numeric workflow exemplar exists.",
        gates_demonstrated=["G2"],
        artifact_refs=["artifact:toy"],
        trust_boundary="Workflow exemplar only.",
        status="accepted",
    )

    assert main(["--base", str(ws.base), "status", "vnext-readiness", "--compact"]) == 0
    compact_payload = json.loads(capsys.readouterr().out)

    assert compact_payload["kind"] == "vnext_readiness_manifest_progress"
    assert compact_payload["source_surface"] == "vnext_readiness_manifest"
    assert compact_payload["control_plane_status"] == "ready_with_lane_exemplar_backlog"
    assert compact_payload["phase_statuses"]["human_output_stability"] == "implemented"
    assert compact_payload["phase_statuses"]["literature_intake_assistant"] == "implemented"
    assert compact_payload["covered_lanes"] == ["toy_numeric"]
    assert compact_payload["missing_lanes"] == ["semi_formal_theory", "code_backed_algorithm"]
    assert compact_payload["stable_output_spine"] == [
        "core_claim_or_current_focus",
        "verified_or_validated_content",
        "hypotheses_uncertainty_and_known_failure_modes",
        "aitp_records_written_or_referenced",
        "next_actions",
        "long_term_memory_candidates_and_non_promotable_content",
    ]
    assert compact_payload["trust_update_forbidden"] is True
    assert compact_payload["can_update_claim_trust"] is False
    assert "workstreams" not in compact_payload
    assert "lane_exemplar_manifest" not in compact_payload
