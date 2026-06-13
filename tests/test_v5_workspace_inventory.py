import json

from brain.v5.cli import main
from brain.v5.markdown import write_md
from brain.v5.workspace import create_claim, create_context, create_topic, init_workspace
from brain.v5.workspace_inventory import build_workspace_inventory, render_workspace_inventory_markdown


def test_workspace_inventory_accounts_for_canonical_root_nested_and_legacy_topics(tmp_path):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)

    create_context(ws, "physics", title="Physics")
    create_topic(ws, "qsgw-ac-error-molecules", context_id="physics", title="QSGW AC")
    create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="Ridge Pade reduces AC amplification in the scoped H2O run.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Si is not tested yet.",
    )

    legacy = topics_root / "qsgw-ac-error-molecules"
    (legacy / "L1").mkdir(parents=True)
    write_md(
        legacy / "state.md",
        {"stage": "L3", "lane": "code_method", "status": "active"},
        "# Legacy state\n",
    )
    (legacy / "L1" / "question_contract.md").write_text("legacy question\n", encoding="utf-8")

    root_topic = workspace_root / ".aitp" / "topics" / "root-only-topic"
    root_topic.mkdir(parents=True)
    write_md(root_topic / "topic.md", {"topic_id": "root-only-topic"}, "# Root-local topic\n")

    nested_topic = workspace_root / ".aitp" / ".aitp" / "topics" / "nested-only-topic"
    nested_topic.mkdir(parents=True)
    write_md(nested_topic / "topic.md", {"topic_id": "nested-only-topic"}, "# Nested topic\n")

    payload = build_workspace_inventory(ws, workspace_root=workspace_root)

    assert payload["kind"] == "aitp_workspace_inventory"
    assert payload["summary"]["legacy_topic_count"] == 1
    assert payload["summary"]["canonical_v5_topic_count"] == 1
    assert payload["summary"]["root_only_topics"] == ["root-only-topic"]
    assert payload["summary"]["nested_only_topics"] == ["nested-only-topic"]
    rows = {row["topic_id"]: row for row in payload["topic_migration_rows"]}
    assert rows["qsgw-ac-error-molecules"]["required_action"] == "semantic_review_legacy_vs_v5"
    assert rows["root-only-topic"]["required_action"] == "merge_root_store_topic"
    assert rows["nested-only-topic"]["required_action"] == "merge_root_store_topic"
    assert rows["qsgw-ac-error-molecules"]["canonical_registry_record_count"] >= 1

    rendered = render_workspace_inventory_markdown(payload)
    assert "AITP Workspace Inventory" in rendered
    assert "root-only-topic" in rendered
    assert "semantic_review_legacy_vs_v5" in rendered


def test_workspace_inventory_cli_can_write_readonly_report(tmp_path, capsys):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    init_workspace(topics_root)
    report = workspace_root / "inventory.md"

    exit_code = main(
        [
            "--base",
            str(topics_root),
            "workspace",
            "inventory",
            "--workspace-root",
            str(workspace_root),
            "--write-report",
            str(report),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_path"] == str(report)
    assert payload["can_update_kernel_state"] is False
    assert report.exists()
    assert "read-only structural accounting" in report.read_text(encoding="utf-8")
