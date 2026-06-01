from __future__ import annotations

import json
from pathlib import Path


def _seed_workspace(tmp_path: Path):
    from brain.v5.evidence import record_evidence
    from brain.v5.operator_checkpoint import request_operator_checkpoint
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW molecular AC error")
    qsgw_claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="Padé analytic continuation may amplify molecular QSGW errors.",
        evidence_profile="code_method",
        confidence_state="partial",
        active_uncertainty="Need a minimal H2O propagation check before trusting the error chain.",
    )
    record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=qsgw_claim.claim_id,
        evidence_type="diagnostic_trace",
        status="mixed",
        summary="Code-path trace identifies the analytic-continuation stage but not the final propagation size.",
        supports_outputs=["diagnostic_trace"],
        source_refs=["note:qsgw-ac"],
    )
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=qsgw_claim.claim_id,
    )
    request_operator_checkpoint(
        ws,
        topic_id="qsgw-ac-error-molecules",
        checkpoint_kind="benchmark_validation_route_choice",
        question="Continue with H2O propagation validation or switch to contour-deformation literature?",
        options=["h2o_validation", "contour_deformation_literature"],
        requested_by="research_cockpit_test",
        claim_id=qsgw_claim.claim_id,
    )

    create_topic(ws, "quantum-gravity-von-neumann", context_id="qg-reading", title="QG von Neumann reading")
    reading_claim = create_claim(
        ws,
        topic_id="quantum-gravity-von-neumann",
        statement="Von Neumann algebra prerequisites need source-grounded reconstruction before reuse.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="Definitions and failure conditions are not yet reconstructed from sources.",
    )
    bind_session(
        ws,
        "reading-session",
        topic_id="quantum-gravity-von-neumann",
        context_id="qg-reading",
        active_claim=reading_claim.claim_id,
    )
    reference = record_reference_location(
        ws,
        topic_id="quantum-gravity-von-neumann",
        claim_id=reading_claim.claim_id,
        connector_id="literature_search",
        location_type="paper",
        uri="https://arxiv.org/abs/2301.00000",
        label="Operator algebras for quantum gravity",
        status="located",
        summary="Candidate reading source for prerequisite reconstruction.",
        metadata={"detected_relevance": "prerequisite_learning_gap"},
    )
    return ws, qsgw_claim, reading_claim, reference


def test_research_cockpit_writes_orientation_surfaces(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_cockpit import write_research_cockpit_surfaces

    ws, qsgw_claim, reading_claim, reference = _seed_workspace(tmp_path)

    bundle = write_research_cockpit_surfaces(ws)
    manifest = json.loads(Path(bundle["files"]["manifest"]).read_text(encoding="utf-8"))
    dashboard = Path(bundle["files"]["dashboard"]).read_text(encoding="utf-8")
    queue = Path(bundle["files"]["queue"]).read_text(encoding="utf-8")

    assert bundle["kind"] == "research_cockpit_bundle"
    assert bundle["orientation_only"] is True
    assert bundle["truth_source"] is False
    assert bundle["summary_inputs_trusted"] is False
    assert bundle["can_update_kernel_state"] is False
    assert bundle["can_update_claim_trust"] is False
    assert manifest["kind"] == "research_cockpit_manifest"
    assert manifest["workspace_summary"]["active_claim_count"] == 2
    assert manifest["today_queue"][0]["topic_id"] == "qsgw-ac-error-molecules"
    assert manifest["today_queue"][0]["recommended_action"] == "answer_operator_checkpoint"
    assert manifest["today_queue"][0]["active_claim_id"] == qsgw_claim.claim_id
    assert manifest["operator_queue"][0]["question_excerpt"].startswith("Continue with H2O")
    assert any(item["claim_id"] == reading_claim.claim_id for item in manifest["learning_gaps"])
    assert manifest["reading_queue"][0]["reference_location_id"] == reference.location_id
    assert "AITP Research Cockpit" in dashboard
    assert "Do Now" in dashboard
    assert "Learning / Literature Gaps" in dashboard
    assert "Operator algebras for quantum gravity" in queue
    assert require_valid_public_surface("research_cockpit_bundle", bundle) == bundle


def test_research_cockpit_cli_mcp_compact_and_runtime_entrypoints(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_write_research_cockpit_surfaces,
        aitp_v5_write_research_cockpit_surfaces_compact,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, _qsgw_claim, _reading_claim, _reference = _seed_workspace(tmp_path)

    assert main(["--base", str(ws.base), "status", "research-cockpit", "--compact"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_research_cockpit_surfaces(str(ws.base))
    compact_payload = aitp_v5_write_research_cockpit_surfaces_compact(str(ws.base))

    assert cli_payload["kind"] == "research_cockpit_bundle_progress"
    assert cli_payload["source_surface"] == "research_cockpit_bundle"
    assert cli_payload["top_recommended_actions"][0] == "answer_operator_checkpoint"
    assert cli_payload["operator_checkpoint_count"] == 1
    assert cli_payload["learning_gap_count"] >= 1
    assert cli_payload["reading_queue_count"] == 1
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["kind"] == "research_cockpit_bundle"
    assert compact_payload["kind"] == "research_cockpit_bundle_progress"
    assert runtime_entrypoints()["research_cockpit"] == {
        "cli": "aitp-v5 status research-cockpit",
        "mcp": "aitp_v5_write_research_cockpit_surfaces",
        "surface": "research_cockpit_bundle",
    }
    assert runtime_entrypoints()["research_cockpit_compact"] == {
        "cli": "aitp-v5 status research-cockpit --compact",
        "mcp": "aitp_v5_write_research_cockpit_surfaces_compact",
        "surface": "research_cockpit_bundle",
    }


def test_research_cockpit_degrades_when_legacy_evidence_is_malformed(tmp_path):
    from brain.v5.markdown import write_md
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_cockpit import compact_research_cockpit_bundle, write_research_cockpit_surfaces

    ws, qsgw_claim, _reading_claim, _reference = _seed_workspace(tmp_path)
    write_md(
        ws.registry_dir("evidence") / "evidence-legacy-missing-claim.md",
        {
            "kind": "evidence",
            "evidence_id": "evidence-legacy-missing-claim",
            "topic_id": "qsgw-ac-error-molecules",
            "evidence_type": "legacy_note",
            "status": "mixed",
            "summary": "Legacy imported record missing claim_id.",
            "supports_outputs": ["diagnostic_trace"],
        },
        "# Legacy malformed evidence\n",
    )

    bundle = write_research_cockpit_surfaces(ws)
    manifest = bundle["manifest"]
    compact = compact_research_cockpit_bundle(bundle)

    assert require_valid_public_surface("research_cockpit_bundle", bundle) == bundle
    assert manifest["degraded_mode"] is True
    assert any("evidence-legacy-missing-claim.md" in item["source"] for item in manifest["read_errors"])
    assert manifest["workspace_summary"]["session_count"] == 2
    assert manifest["today_queue"][0]["topic_id"] == "qsgw-ac-error-molecules"
    assert manifest["today_queue"][0]["active_claim_id"] == qsgw_claim.claim_id
    assert compact["kind"] == "research_cockpit_bundle_progress"
    assert compact["degraded_mode"] is True
    assert compact["read_error_count"] >= 1
