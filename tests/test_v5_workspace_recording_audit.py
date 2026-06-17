from __future__ import annotations

import json

from brain.v5.cli import main
from brain.v5.evidence import record_evidence
from brain.v5.markdown import write_text_atomic
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.source_reconstruction_review import record_source_reconstruction_review_result
from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace
from brain.v5.workspace_recording_audit import (
    build_workspace_recording_audit,
    render_workspace_recording_audit_markdown,
)


def _workspace_with_recording_topics(tmp_path):
    ws = init_workspace(tmp_path / "research" / "aitp-topics")
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Sector counting identifies a candidate edge CFT only within a scoped source convention.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="source convention drift and finite-size aliasing",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="A source reconstruction step supports the scoped convention.",
        supports_outputs=["reconstruction_path"],
    )
    record_source_reconstruction_review_result(
        ws,
        claim_id=claim.claim_id,
        status="passed",
        reviewed_components=["reconstruction_path"],
        evidence_refs=[evidence.evidence_id],
        summary="The source reconstruction path was reviewed for the test fixture.",
    )
    bind_session(
        ws,
        "s-fqhe",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )
    migration_plan = ws.root / "migrations" / "plan.json"
    write_text_atomic(
        migration_plan,
        json.dumps(
            {
                "topic_rows": [
                    {"topic_id": "fqhe", "plan_action": "no_action"},
                    {"topic_id": "legacy-only-topic", "plan_action": "semantic_review_required"},
                ]
            }
        ),
    )
    return ws, migration_plan, claim


def test_workspace_recording_audit_surfaces_topic_navigation_and_blockers(tmp_path):
    ws, migration_plan, claim = _workspace_with_recording_topics(tmp_path)

    payload = build_workspace_recording_audit(ws, migration_plan_path=migration_plan)

    assert payload["kind"] == "aitp_workspace_recording_audit"
    assert payload["summary"]["topic_count"] == 2
    assert payload["summary"]["navigable_topic_count"] == 1
    assert payload["summary"]["blocked_topic_count"] == 1
    assert require_valid_public_surface("workspace_recording_audit", payload) == payload

    rows = {row["topic_id"]: row for row in payload["topic_rows"]}
    assert rows["fqhe"]["session_id"] == "s-fqhe"
    assert rows["fqhe"]["active_claim_id"] == claim.claim_id
    assert rows["fqhe"]["recording_status"] in {"navigation_ready", "navigation_ready_with_blockers"}
    assert "source_asset" in rows["fqhe"]["first_level_slot_counts"]
    assert rows["fqhe"]["first_level_slot_counts"]["source_reconstruction_review"] == 1
    assert rows["fqhe"]["next_read_tool"] == "aitp_v5_get_recording_navigation_state"
    assert rows["fqhe"]["can_update_kernel_state"] is False
    assert rows["fqhe"]["can_update_claim_trust"] is False

    selected = build_workspace_recording_audit(ws, migration_plan_path=migration_plan, topics=["fqhe"])
    selected_row = selected["topic_rows"][0]
    assert selected["disclosure_policy"]["deep_navigation_enabled"] is True
    assert selected_row["topic_id"] == "fqhe"
    assert selected_row["next_read_tool"] in {"", "aitp_v5_expand_recording_slot"}

    assert rows["legacy-only-topic"]["recording_status"] == "blocked_by_recovery_gap"
    assert rows["legacy-only-topic"]["human_review_required"] is True
    assert any("no session binding" in reason for reason in rows["legacy-only-topic"]["human_review_reasons"])

    rendered = render_workspace_recording_audit_markdown(payload)
    assert "AITP Workspace Recording Audit" in rendered
    assert "legacy-only-topic" in rendered


def test_workspace_recording_audit_mcp_cli_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.mcp_tools import (
        aitp_v5_build_workspace_recording_audit,
        aitp_v5_write_workspace_recording_audit,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, migration_plan, _claim = _workspace_with_recording_topics(tmp_path)
    out_json = tmp_path / "recording-audit.json"
    out_report = tmp_path / "recording-audit.md"

    mcp_payload = aitp_v5_build_workspace_recording_audit(
        str(ws.base),
        migration_plan_json=str(migration_plan),
        topics=["fqhe"],
    )
    assert mcp_payload["kind"] == "aitp_workspace_recording_audit"
    assert mcp_payload["summary"]["topic_count"] == 1

    written = aitp_v5_write_workspace_recording_audit(
        str(ws.base),
        migration_plan_json=str(migration_plan),
        write_json=str(out_json),
        write_report=str(out_report),
    )
    assert written["ok"] is True
    assert written["kind"] == "aitp_workspace_recording_audit"
    assert out_json.exists()
    assert out_report.exists()

    assert main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "recording-audit",
            "--migration-plan-json",
            str(migration_plan),
            "--topic",
            "fqhe",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["kind"] == "aitp_workspace_recording_audit"
    assert cli_payload["summary"]["topic_count"] == 1

    entrypoints = runtime_entrypoints()
    assert entrypoints["workspace_recording_audit"] == {
        "cli": "aitp-v5 workspace recording-audit <args>",
        "mcp": "aitp_v5_build_workspace_recording_audit",
        "surface": "workspace_recording_audit",
    }
    assert entrypoints["write_workspace_recording_audit"]["mcp"] == "aitp_v5_write_workspace_recording_audit"
    assert validate_runtime_entrypoints() == []
