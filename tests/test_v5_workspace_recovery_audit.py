import json
from pathlib import Path

from brain.v5.cli import main
from brain.v5.evidence import record_evidence
from brain.v5.markdown import write_text_atomic
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_state import update_claim_status
from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace
from brain.v5.workspace_recovery_audit import (
    build_workspace_recovery_audit,
    compact_workspace_recovery_audit,
    render_workspace_recovery_audit_markdown,
)


def _workspace_with_ready_topic(tmp_path: Path):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)

    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC error molecules")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="Ridge-regularized Pade reduces scoped H2O analytic-continuation amplification.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Si same-executable baseline has not completed.",
    )
    evidence = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay",
        status="supports_scoped_claim",
        summary="H2O replay supports the scoped amplification claim.",
        supports_outputs=["h2o_replay"],
    )
    update_claim_status(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="hypothesis",
        scope="H2O one-iteration replay only.",
        risk="Do not treat missing Si baseline as algorithm validation.",
        next_action="Run same-executable Si Thiele baseline before interpreting ridge.",
        open_gaps=["Si baseline has not entered analytic continuation."],
        evidence_refs=[evidence.evidence_id],
    )
    bind_session(
        ws,
        "qsgw-si-recovery",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=claim.claim_id,
    )

    migration_plan = topics_root / ".aitp" / "migrations" / "plan.json"
    write_text_atomic(
        migration_plan,
        json.dumps(
            {
                "topic_rows": [
                    {
                        "topic_id": "qsgw-ac-error-molecules",
                        "plan_action": "no_action",
                    },
                    {
                        "topic_id": "legacy-only-topic",
                        "plan_action": "semantic_review_required",
                    },
                ]
            }
        ),
    )
    return ws, migration_plan


def test_workspace_recovery_audit_marks_ready_and_gap_topics(tmp_path):
    ws, migration_plan = _workspace_with_ready_topic(tmp_path)

    payload = build_workspace_recovery_audit(ws, migration_plan_path=migration_plan)

    assert payload["kind"] == "aitp_workspace_recovery_audit"
    assert payload["summary"]["topic_count"] == 2
    assert payload["summary"]["recovery_ready_count"] == 1
    assert payload["summary"]["recovery_gap_count"] == 1
    assert payload["summary"]["topics_with_active_claim"] == 1
    assert payload["summary"]["topics_with_relation_map"] == 1
    assert payload["summary"]["topics_blocked_by_migration_review"] == 1
    assert require_valid_public_surface("workspace_recovery_audit", payload) == payload

    rows = {row["topic_id"]: row for row in payload["topic_rows"]}
    assert rows["qsgw-ac-error-molecules"]["recovery_status"] == "recovery_ready"
    assert rows["qsgw-ac-error-molecules"]["has_current_conclusion"] is True
    assert "Thiele baseline" in rows["qsgw-ac-error-molecules"]["next_valid_action"]
    assert rows["legacy-only-topic"]["recovery_status"] == "no_session"
    assert rows["legacy-only-topic"]["migration_review_required"] is True

    compact = compact_workspace_recovery_audit(payload)
    assert compact["kind"] == "aitp_workspace_recovery_audit_progress"
    assert compact["top_gap_topics"] == ["legacy-only-topic"]
    compact_rows = {row["topic_id"]: row for row in compact["topic_rows"]}
    assert compact_rows["qsgw-ac-error-molecules"]["session_id"] == "qsgw-si-recovery"
    assert require_valid_public_surface("workspace_recovery_audit_progress", compact) == compact

    rendered = render_workspace_recovery_audit_markdown(payload)
    assert "AITP Workspace Recovery Audit" in rendered
    assert "legacy-only-topic" in rendered


def test_workspace_recovery_audit_prefers_runtime_topic_state_over_legacy_preserve_session(tmp_path):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)
    topic_id = "qsgw-ac-error-molecules"

    create_topic(ws, topic_id, context_id="librpa", title="QSGW AC error molecules")
    legacy_claim = create_claim(
        ws,
        topic_id=topic_id,
        statement="Why does analytic continuation amplify errors in molecule QSGW?",
        evidence_profile="legacy_seed",
        confidence_state="legacy_seed",
        active_uncertainty="needs current-stage reconstruction",
    )
    live_claim = create_claim(
        ws,
        topic_id=topic_id,
        statement="H2O ridge Padé reduces scoped AC amplification, while Si runtime failure does not test the ridge algorithm.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Si same-executable AC comparison is blocked before analytic continuation.",
    )
    support = record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=live_claim.claim_id,
        evidence_type="bounded_numerical_replay",
        status="supports_scoped_claim",
        summary="H2O replay supports the scoped ridge amplification claim.",
        supports_outputs=["h2o_replay"],
    )
    record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=live_claim.claim_id,
        evidence_type="external_run_log",
        status="falsifies_application",
        summary=(
            "Si ridge/Thiele array failed before analytic continuation during ScaLAPACK Wc; "
            "the thiele control failed at the same runtime stage, so this does not test algorithm correctness."
        ),
    )
    update_claim_status(
        ws,
        topic_id=topic_id,
        claim_id=live_claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="supports_with_limitations",
        scope="H2O one-iteration replay; Si AC comparison not completed.",
        risk="Do not treat the Si runtime failure as ridge algorithm evidence.",
        next_action="Fix the executable/ScaLAPACK blocker, then run the same-executable Si Thiele baseline before ridge.",
        open_gaps=["Strong ridge parameters may shift the H2O gap."],
        evidence_refs=[support.evidence_id],
    )
    bind_session(
        ws,
        "codex-20260611-si-g0w0-pade-test",
        topic_id=topic_id,
        context_id="librpa",
        active_claim=live_claim.claim_id,
    )
    bind_session(
        ws,
        "v5-qsgw-ac-error-molecules-legacy-preserve",
        topic_id=topic_id,
        context_id=topic_id,
        active_claim=legacy_claim.claim_id,
    )
    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        runtime_dir / "topic_state.json",
        json.dumps(
            {
                "kind": "topic_state",
                "topic_id": topic_id,
                "session_id": "codex-20260611-si-g0w0-pade-test",
                "active_claim_id": live_claim.claim_id,
            }
        ),
    )
    migration_plan = topics_root / ".aitp" / "migrations" / "plan.json"
    write_text_atomic(
        migration_plan,
        json.dumps({"topic_rows": [{"topic_id": topic_id, "plan_action": "no_action"}]}),
    )

    payload = build_workspace_recovery_audit(ws, migration_plan_path=migration_plan)

    row = payload["topic_rows"][0]
    assert row["recovery_status"] == "recovery_ready"
    assert row["session_id"] == "codex-20260611-si-g0w0-pade-test"
    assert row["active_claim_id"] == live_claim.claim_id
    assert row["recovery_selection_source"] == "runtime_topic_state_session"
    assert row["supported_count"] == 1
    assert row["not_tested_count"] == 1
    assert "same-executable Si Thiele baseline" in row["next_valid_action"]


def test_workspace_recovery_audit_marks_runtime_topic_state_claim_divergence(tmp_path):
    ws, migration_plan = _workspace_with_ready_topic(tmp_path)
    runtime_dir = ws.topic_dir("qsgw-ac-error-molecules") / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        runtime_dir / "topic_state.json",
        json.dumps(
            {
                "kind": "topic_state",
                "topic_id": "qsgw-ac-error-molecules",
                "session_id": "qsgw-si-recovery",
                "active_claim_id": "claim-qsgw-ac-error-molecules-different-live-claim",
            }
        ),
    )

    payload = build_workspace_recovery_audit(ws, migration_plan_path=migration_plan)
    rows = {row["topic_id"]: row for row in payload["topic_rows"]}

    assert rows["qsgw-ac-error-molecules"]["recovery_status"] == "recovery_source_divergence"
    assert "active claim differs" in rows["qsgw-ac-error-molecules"]["recovery_gap"]


def test_workspace_recovery_audit_cli_writes_json_and_report(tmp_path, capsys):
    ws, migration_plan = _workspace_with_ready_topic(tmp_path)
    out_json = tmp_path / "recovery-audit.json"
    report = tmp_path / "recovery-audit.md"

    exit_code = main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "recovery-audit",
            "--migration-plan-json",
            str(migration_plan),
            "--write-json",
            str(out_json),
            "--write-report",
            str(report),
            "--compact",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "aitp_workspace_recovery_audit_progress"
    assert payload["recovery_ready_count"] == 1
    assert out_json.exists()
    assert report.exists()
    assert "Recovery Audit" in report.read_text(encoding="utf-8")


def test_workspace_recovery_audit_mcp_and_runtime_entrypoint(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_build_workspace_recovery_audit
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, migration_plan = _workspace_with_ready_topic(tmp_path)

    payload = aitp_v5_build_workspace_recovery_audit(
        str(ws.base),
        migration_plan_json=str(migration_plan),
        compact=True,
    )

    assert payload["kind"] == "aitp_workspace_recovery_audit_progress"
    assert runtime_entrypoints()["workspace_recovery_audit"]["mcp"] == "aitp_v5_build_workspace_recovery_audit"
    assert "write_workspace_recovery_audit" in runtime_entrypoints()
    assert validate_runtime_entrypoints() == []

    single = aitp_v5_build_workspace_recovery_audit(
        str(ws.base),
        topics=["qsgw-ac-error-molecules"],
        compact=True,
    )
    assert single["topic_count"] == 1
    assert single["recovery_ready_count"] == 1
    assert single["selected_topic"]["session_id"] == "qsgw-si-recovery"
    assert single["selected_topic"]["active_claim_id"]


def test_workspace_recovery_audit_discovers_latest_migration_plan_by_default(tmp_path):
    ws, migration_plan = _workspace_with_ready_topic(tmp_path)
    saved_dir = ws.root / "migrations" / "workspace-inventory"
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_plan = saved_dir / "workspace_migration_plan.json"
    saved_plan.write_text(migration_plan.read_text(encoding="utf-8"), encoding="utf-8")

    payload = build_workspace_recovery_audit(ws)

    assert payload["migration_plan_source"] == str(saved_plan)
    assert payload["summary"]["topic_count"] == 2
    assert payload["summary"]["recovery_ready_count"] == 1


def test_workspace_recovery_audit_prefers_saved_audit_for_full_default(tmp_path):
    ws, migration_plan = _workspace_with_ready_topic(tmp_path)
    saved_dir = ws.root / "migrations" / "workspace-inventory"
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_audit = saved_dir / "workspace_recovery_audit.json"
    full = build_workspace_recovery_audit(ws, migration_plan_path=migration_plan)
    write_text_atomic(saved_audit, json.dumps(full))

    payload = build_workspace_recovery_audit(ws)

    assert payload["recovery_audit_source"] == str(saved_audit)
    assert payload["summary"]["topic_count"] == 2
