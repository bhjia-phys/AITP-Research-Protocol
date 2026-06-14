import json
from pathlib import Path

from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.cli import main
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace
from brain.v5.workspace_recovery_binding_repair import (
    apply_workspace_recovery_binding_repair,
    build_workspace_recovery_binding_repair,
)


def _workspace_with_binding_gaps(tmp_path: Path):
    ws = init_workspace(tmp_path / "topics")
    create_topic(ws, "single-claim-topic", context_id="ctx", title="Single claim")
    claim = create_claim(
        ws,
        topic_id="single-claim-topic",
        statement="A single active claim can be bound safely.",
        evidence_profile="theory",
        confidence_state="hypothesis",
        active_uncertainty="Recovery binding missing.",
    )
    bind_session(ws, "unbound-session", topic_id="single-claim-topic", context_id="ctx")

    create_topic(ws, "multi-claim-topic", context_id="ctx", title="Multi claim")
    create_claim(
        ws,
        topic_id="multi-claim-topic",
        statement="First possible active claim.",
        evidence_profile="theory",
        confidence_state="hypothesis",
        active_uncertainty="Which claim is active?",
    )
    create_claim(
        ws,
        topic_id="multi-claim-topic",
        statement="Second possible active claim.",
        evidence_profile="theory",
        confidence_state="hypothesis",
        active_uncertainty="Which claim is active?",
    )
    bind_session(ws, "multi-unbound-session", topic_id="multi-claim-topic", context_id="ctx")
    return ws, claim


def test_workspace_recovery_binding_repair_applies_only_single_claim(tmp_path):
    ws, claim = _workspace_with_binding_gaps(tmp_path)

    plan = build_workspace_recovery_binding_repair(
        ws,
        topics=["single-claim-topic", "multi-claim-topic"],
    )

    assert plan["kind"] == "aitp_workspace_recovery_binding_repair"
    assert plan["summary"]["applyable_count"] == 1
    assert plan["summary"]["review_required_count"] == 1
    assert require_valid_public_surface("workspace_recovery_binding_repair", plan) == plan

    by_topic = {action["topic_id"]: action for action in plan["actions"]}
    assert by_topic["single-claim-topic"]["status"] == "planned_bind_existing_session"
    assert by_topic["multi-claim-topic"]["status"] == "review_required_multiple_claims"

    applied = apply_workspace_recovery_binding_repair(plan, ws)
    assert applied["summary"]["status_counts"]["bound_existing_session"] == 1
    assert require_valid_public_surface("workspace_recovery_binding_repair", applied) == applied

    relation = build_claim_relation_map(ws, "unbound-session")
    assert relation["claim_id"] == claim.claim_id


def test_workspace_recovery_binding_repair_cli_and_mcp(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_build_workspace_recovery_binding_repair
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, _claim = _workspace_with_binding_gaps(tmp_path)
    out_json = tmp_path / "binding-repair.json"

    exit_code = main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "recovery-binding-repair",
            "--topic",
            "single-claim-topic",
            "--apply",
            "--write-json",
            str(out_json),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "apply"
    assert payload["summary"]["status_counts"]["bound_existing_session"] == 1
    assert out_json.exists()

    mcp_payload = aitp_v5_build_workspace_recovery_binding_repair(
        str(ws.base),
        topics=["multi-claim-topic"],
    )
    assert mcp_payload["summary"]["review_required_count"] == 1
    assert runtime_entrypoints()["workspace_recovery_binding_repair"]["mcp"] == "aitp_v5_build_workspace_recovery_binding_repair"
    assert "apply_workspace_recovery_binding_repair" in runtime_entrypoints()
    assert validate_runtime_entrypoints() == []
