from __future__ import annotations

import json
from pathlib import Path


def _setup_topic(tmp_path: Path):
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
    )
    return ws


def test_request_operator_checkpoint_writes_active_artifacts_and_ledger(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.operator_checkpoint import request_operator_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface

    ws = _setup_topic(tmp_path)

    checkpoint = request_operator_checkpoint(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_kind="benchmark_validation_route_choice",
        question="Should the next report use final-only rows or include diagnostic trend plots?",
        options=["final_only", "diagnostic_appendix"],
        requested_by="risk_budget",
        claim_id="claim-qsgw",
        human_checkpoint_id="checkpoint-qsgw",
        source_refs=["final_output_profile:qsgw-headwing-dual-lane-v1"],
    )

    runtime_dir = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime"
    fm, body = read_md(runtime_dir / "operator_checkpoint.active.md")
    active_json = json.loads((runtime_dir / "operator_checkpoint.active.json").read_text(encoding="utf-8"))
    ledger = [json.loads(line) for line in (runtime_dir / "operator_checkpoints.jsonl").read_text(encoding="utf-8").splitlines()]

    assert checkpoint.status == "requested"
    assert fm["kind"] == "operator_checkpoint"
    assert active_json["checkpoint_id"] == checkpoint.checkpoint_id
    assert "final-only rows" in body
    assert ledger[-1]["status"] == "requested"
    assert checkpoint.can_update_claim_trust is False
    assert require_valid_public_surface("operator_checkpoint_record", {"ok": True, **checkpoint.__dict__})


def test_answer_operator_checkpoint_updates_active_artifacts_and_ledger(tmp_path):
    from brain.v5.operator_checkpoint import answer_operator_checkpoint, request_operator_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface

    ws = _setup_topic(tmp_path)
    requested = request_operator_checkpoint(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_kind="stop_continue_branch_redirect_decision",
        question="Continue final closure, branch diagnostics, or pause?",
        options=["continue_final_closure", "branch_diagnostics", "pause"],
        requested_by="operator_console",
    )

    answered = answer_operator_checkpoint(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_id=requested.checkpoint_id,
        selected_option="branch_diagnostics",
        rationale="Need diagnostic plot for group meeting, with final lane untouched.",
        answered_by="human",
    )

    runtime_dir = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime"
    active_json = json.loads((runtime_dir / "operator_checkpoint.active.json").read_text(encoding="utf-8"))
    ledger = [json.loads(line) for line in (runtime_dir / "operator_checkpoints.jsonl").read_text(encoding="utf-8").splitlines()]

    assert answered.status == "answered"
    assert active_json["selected_option"] == "branch_diagnostics"
    assert [item["status"] for item in ledger[-2:]] == ["requested", "answered"]
    assert require_valid_public_surface("operator_checkpoint_record", {"ok": True, **answered.__dict__})


def test_execution_brief_surfaces_active_operator_checkpoint(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.operator_checkpoint import request_operator_checkpoint

    ws = _setup_topic(tmp_path)
    request_operator_checkpoint(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_kind="resource_risk_limit_choice",
        question="Is another remote QSGW poll worth the risk right now?",
        options=["poll_read_only", "wait", "switch_to_local_report"],
        requested_by="runtime",
    )

    brief = build_execution_brief(ws, "qsgw-session")
    checkpoint = brief["known_context"]["operator_checkpoint"]

    assert checkpoint["present"] is True
    assert checkpoint["status"] == "requested"
    assert checkpoint["required_next_action"] == "answer_operator_checkpoint"
    assert brief["human_checkpoint"]["needed"] is True
    assert brief["next_action_candidates"][0]["action"] == "answer_operator_checkpoint"
    assert "vnext:continue_without_answering_operator_checkpoint" in brief["forbidden_now"]


def test_operator_checkpoint_cli_mcp_and_runtime_surfaces(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_request_operator_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws = _setup_topic(tmp_path)

    assert main(
        [
            "--base",
            str(ws.base),
            "operator",
            "checkpoint",
            "request",
            "--topic",
            "qsgw-headwing-update-librpa",
            "--kind",
            "promotion_approval",
            "--question",
            "Can this scoped result be promoted?",
            "--option",
            "approve",
            "--option",
            "defer",
            "--requested-by",
            "promotion_preflight",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_request_operator_checkpoint(
        str(ws.base),
        topic_id="qsgw-headwing-update-librpa",
        checkpoint_kind="promotion_approval",
        question="Can this scoped result be promoted?",
        options=["approve", "defer"],
        requested_by="promotion_preflight",
    )

    assert require_valid_public_surface("operator_checkpoint_record", cli_payload) == cli_payload
    assert require_valid_public_surface("operator_checkpoint_record", mcp_payload) == mcp_payload
    assert runtime_entrypoints()["request_operator_checkpoint"] == {
        "cli": "aitp-v5 operator checkpoint request <args>",
        "mcp": "aitp_v5_request_operator_checkpoint",
        "surface": "operator_checkpoint_record",
    }
