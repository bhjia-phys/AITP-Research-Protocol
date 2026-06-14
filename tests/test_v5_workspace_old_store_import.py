import json
from pathlib import Path

from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.cli import main
from brain.v5.models import ClaimRecord, SessionBinding, TopicRecord
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.store import write_record
from brain.v5.workspace import init_workspace
from brain.v5.workspace_old_store_import import (
    apply_workspace_old_store_import_plan,
    build_workspace_old_store_import_plan,
    render_workspace_old_store_import_markdown,
)
from brain.v5.workspace_old_store_manifest import build_workspace_old_store_manifest


def _workspace_with_root_old_store(tmp_path: Path):
    workspace_root = tmp_path / "Theoretical-Physics"
    ws = init_workspace(workspace_root / "research" / "aitp-topics")
    root_store = workspace_root / ".aitp"

    topic = TopicRecord(
        topic_id="ads-random-boundary-matter-20260612",
        context_id="ads",
        title="Massive matter in AdS with random boundary sink",
    )
    claim = ClaimRecord(
        claim_id="claim-ads-random-boundary-matter",
        topic_id=topic.topic_id,
        statement="Massive matter survival needs a cutoff wall or wavepacket/bath model layer.",
        evidence_profile="theory_orientation",
        confidence_state="hypothesis",
        active_uncertainty="Hitting-time semantics are model-layer dependent.",
    )
    session = SessionBinding(
        session_id="ads-random-boundary-session",
        topic_id=topic.topic_id,
        context_id="ads",
        active_claim=claim.claim_id,
    )
    write_record(root_store / "topics" / topic.topic_id / "topic.md", topic)
    write_record(root_store / "registry" / "claims" / f"{claim.claim_id}.md", claim)
    write_record(root_store / "runtime" / "sessions" / f"{session.session_id}.md", session)
    return ws, workspace_root, topic, claim, session


def test_workspace_old_store_import_plan_and_apply_restore_session(tmp_path):
    ws, workspace_root, topic, claim, session = _workspace_with_root_old_store(tmp_path)

    plan = build_workspace_old_store_import_plan(
        ws,
        workspace_root=workspace_root,
        topics=[topic.topic_id],
    )

    assert plan["kind"] == "aitp_workspace_old_store_import_result"
    assert plan["mode"] == "plan"
    assert plan["summary"]["would_import_count"] == 3
    assert plan["summary"]["safe_to_apply"] is True
    assert require_valid_public_surface("workspace_old_store_import_result", plan) == plan
    assert "Old Store Import Result" in render_workspace_old_store_import_markdown(plan)

    applied = apply_workspace_old_store_import_plan(plan)
    assert applied["mode"] == "apply"
    assert applied["summary"]["imported_count"] == 3
    assert require_valid_public_surface("workspace_old_store_import_result", applied) == applied
    assert (ws.root / "topics" / topic.topic_id / "topic.md").exists()
    assert (ws.root / "registry" / "claims" / f"{claim.claim_id}.md").exists()
    assert (ws.root / "runtime" / "sessions" / f"{session.session_id}.md").exists()

    relation = build_claim_relation_map(ws, session.session_id)
    assert relation["claim_id"] == claim.claim_id
    assert relation["current_conclusion"]["can_say"] == ["active claim remains hypothesis"]

    second = build_workspace_old_store_import_plan(
        ws,
        workspace_root=workspace_root,
        topics=[topic.topic_id],
    )
    assert second["summary"]["already_present_count"] == 3


def test_workspace_old_store_import_apply_preserves_conflicts(tmp_path):
    ws, workspace_root, topic, claim, session = _workspace_with_root_old_store(tmp_path)
    conflicting_claim = ClaimRecord(
        claim_id=claim.claim_id,
        topic_id=topic.topic_id,
        statement="Canonical claim text that must not be overwritten.",
        evidence_profile="theory_orientation",
        confidence_state="hypothesis",
        active_uncertainty="This pre-existing canonical record wins until semantic review.",
    )
    canonical_claim_path = ws.root / "registry" / "claims" / f"{claim.claim_id}.md"
    write_record(canonical_claim_path, conflicting_claim)
    original_text = canonical_claim_path.read_text(encoding="utf-8")

    plan = build_workspace_old_store_import_plan(
        ws,
        workspace_root=workspace_root,
        topics=[topic.topic_id],
    )

    assert plan["apply_policy"] == "copy_would_import_only_never_overwrite_conflicts"
    assert plan["summary"]["would_import_count"] == 2
    assert plan["summary"]["conflict_count"] == 1
    assert plan["summary"]["safe_to_apply"] is False

    applied = apply_workspace_old_store_import_plan(plan)

    assert applied["summary"]["imported_count"] == 2
    assert applied["summary"]["conflict_count"] == 1
    assert canonical_claim_path.read_text(encoding="utf-8") == original_text
    assert (ws.root / "topics" / topic.topic_id / "topic.md").exists()
    assert (ws.root / "runtime" / "sessions" / f"{session.session_id}.md").exists()


def test_workspace_old_store_import_cli_writes_manifest(tmp_path, capsys):
    ws, workspace_root, topic, _claim, _session = _workspace_with_root_old_store(tmp_path)
    out_json = tmp_path / "old-store-import.json"
    out_md = tmp_path / "old-store-import.md"

    exit_code = main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "old-store-import",
            "--workspace-root",
            str(workspace_root),
            "--topic",
            topic.topic_id,
            "--apply",
            "--write-json",
            str(out_json),
            "--write-report",
            str(out_md),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "aitp_workspace_old_store_import_result"
    assert payload["mode"] == "apply"
    assert payload["summary"]["imported_count"] == 3
    assert out_json.exists()
    assert out_md.exists()


def test_workspace_old_store_import_mcp_and_runtime_entrypoint(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_build_workspace_old_store_import_plan
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, workspace_root, topic, _claim, _session = _workspace_with_root_old_store(tmp_path)

    payload = aitp_v5_build_workspace_old_store_import_plan(
        str(ws.base),
        workspace_root=str(workspace_root),
        topics=[topic.topic_id],
    )

    assert payload["summary"]["would_import_count"] == 3
    assert runtime_entrypoints()["workspace_old_store_import_plan"]["mcp"] == "aitp_v5_build_workspace_old_store_import_plan"
    assert "apply_workspace_old_store_import" in runtime_entrypoints()
    assert validate_runtime_entrypoints() == []


def test_workspace_old_store_import_discovers_saved_manifest_by_default(tmp_path):
    ws, workspace_root, topic, _claim, _session = _workspace_with_root_old_store(tmp_path)
    saved_dir = ws.root / "migrations" / "workspace-inventory"
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_manifest = saved_dir / "workspace_old_store_manifest.json"
    saved_manifest.write_text(
        json.dumps(build_workspace_old_store_manifest(ws, workspace_root=workspace_root)),
        encoding="utf-8",
    )

    payload = build_workspace_old_store_import_plan(ws, workspace_root=workspace_root, topics=[topic.topic_id])

    assert payload["old_store_manifest_source"] == str(saved_manifest)
    assert payload["summary"]["would_import_count"] == 3
