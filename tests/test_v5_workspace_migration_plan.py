import json

from brain.v5.cli import main
from brain.v5.markdown import write_md
from brain.v5.workspace import create_claim, create_context, create_topic, init_workspace
from brain.v5.workspace_inventory import build_workspace_inventory
from brain.v5.workspace_migration_plan import (
    build_workspace_migration_plan,
    render_workspace_migration_plan_markdown,
)


def test_workspace_migration_plan_classifies_all_inventory_rows(tmp_path):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)

    create_context(ws, "physics", title="Physics")
    create_topic(ws, "current-topic", context_id="physics", title="Current")
    create_claim(
        ws,
        topic_id="current-topic",
        statement="A current v5 claim exists.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="Needs proof.",
    )

    create_topic(ws, "empty-topic", context_id="physics", title="Empty")

    create_topic(ws, "legacy-topic", context_id="physics", title="Legacy")
    create_claim(
        ws,
        topic_id="legacy-topic",
        statement="Legacy topic has a v5 projection.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Legacy semantics need review.",
    )
    legacy = topics_root / "legacy-topic"
    (legacy / "L0").mkdir(parents=True)
    write_md(legacy / "state.md", {"stage": "L3", "lane": "code_method"}, "# Legacy\n")
    (legacy / "L0" / "note.md").write_text("legacy note\n", encoding="utf-8")

    root_claim = workspace_root / ".aitp" / "registry" / "claims" / "claim-root.md"
    write_md(
        root_claim,
        {"kind": "claim", "claim_id": "claim-root", "topic_id": "root-record-topic"},
        "# Root claim\n",
    )
    root_topic = workspace_root / ".aitp" / "topics" / "root-record-topic"
    root_topic.mkdir(parents=True)
    write_md(root_topic / "topic.md", {"topic_id": "root-record-topic"}, "# Root topic\n")

    shell_topic = workspace_root / ".aitp" / "topics" / "shell-topic"
    shell_topic.mkdir(parents=True)
    write_md(shell_topic / "topic.md", {"topic_id": "shell-topic"}, "# Shell topic\n")

    inventory = build_workspace_inventory(ws, workspace_root=workspace_root)
    plan = build_workspace_migration_plan(ws, inventory=inventory)

    assert plan["kind"] == "aitp_workspace_migration_plan"
    assert plan["summary"]["no_omission_check"] is True
    assert plan["summary"]["old_store_retirement_safe"] is False
    rows = {row["topic_id"]: row for row in plan["topic_rows"]}
    assert rows["current-topic"]["plan_action"] == "no_action"
    assert rows["legacy-topic"]["plan_action"] == "semantic_review_required"
    assert rows["empty-topic"]["plan_action"] == "empty_canonical_topic_review_required"
    assert rows["root-record-topic"]["plan_action"] == "root_store_import_review_required"
    assert rows["shell-topic"]["plan_action"] == "root_store_shell_archive_required"
    assert rows["root-record-topic"]["root_registry_record_count"] == 1
    assert rows["root-record-topic"]["blocks_old_store_retirement"] is True

    rendered = render_workspace_migration_plan_markdown(plan)
    assert "AITP Workspace Migration Plan" in rendered
    assert "root_store_import_review_required" in rendered
    assert "archive_then_disable_entrypoints_not_direct_delete" in rendered


def test_workspace_migration_plan_cli_can_write_report_from_inventory_json(tmp_path, capsys):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)
    inventory = build_workspace_inventory(ws, workspace_root=workspace_root)
    inventory_json = workspace_root / "inventory.json"
    inventory_json.write_text(json.dumps(inventory), encoding="utf-8-sig")
    report = workspace_root / "migration-plan.md"

    exit_code = main(
        [
            "--base",
            str(topics_root),
            "workspace",
            "migration-plan",
            "--inventory-json",
            str(inventory_json),
            "--write-report",
            str(report),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_path"] == str(report)
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert report.exists()
    assert "read-only coordination surface" in report.read_text(encoding="utf-8")
