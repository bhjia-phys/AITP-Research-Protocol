import json

from brain.v5.cli import main
from brain.v5.markdown import write_md
from brain.v5.workspace import init_workspace
from brain.v5.workspace_old_store_manifest import (
    build_workspace_old_store_manifest,
    render_workspace_old_store_manifest_markdown,
)


def test_workspace_old_store_manifest_accounts_for_files_by_topic_and_category(tmp_path):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    ws = init_workspace(topics_root)

    root_claim = workspace_root / ".aitp" / "registry" / "claims" / "claim-root.md"
    write_md(
        root_claim,
        {"kind": "claim", "claim_id": "claim-root", "topic_id": "root-topic"},
        "# Root claim\n",
    )
    root_topic = workspace_root / ".aitp" / "topics" / "root-topic"
    root_topic.mkdir(parents=True)
    write_md(root_topic / "topic.md", {"topic_id": "root-topic"}, "# Root topic\n")
    root_session = workspace_root / ".aitp" / "runtime" / "sessions" / "session-root.md"
    write_md(root_session, {"session_id": "session-root"}, "# Session\n")
    root_memory = workspace_root / ".aitp" / "memory" / "l2" / "entries" / "memory-root.md"
    write_md(
        root_memory,
        {"kind": "memory_entry", "entry_id": "memory-root", "topic_id": "root-topic"},
        "# Memory\n",
    )

    nested_claim = workspace_root / ".aitp" / ".aitp" / "registry" / "claims" / "claim-nested.md"
    write_md(
        nested_claim,
        {"kind": "claim", "claim_id": "claim-nested", "topic_id": "nested-topic"},
        "# Nested claim\n",
    )

    payload = build_workspace_old_store_manifest(ws, workspace_root=workspace_root)

    assert payload["kind"] == "aitp_workspace_old_store_manifest"
    assert payload["summary"]["file_count"] == 5
    assert payload["summary"]["old_store_retirement_safe"] is False
    assert payload["summary"]["category_counts"]["registry_record"] == 2
    assert payload["summary"]["category_counts"]["memory_entry"] == 1
    assert payload["summary"]["category_counts"]["topic_shell"] == 1
    assert payload["summary"]["category_counts"]["runtime_session"] == 1
    assert payload["summary"]["topic_file_counts"]["root-topic"] == 3
    assert payload["summary"]["topic_file_counts"]["nested-topic"] == 1
    assert all(file["sha256"] for store in payload["stores"] for file in store["files"])

    rendered = render_workspace_old_store_manifest_markdown(payload)
    assert "AITP Old Store Manifest" in rendered
    assert "root-topic" in rendered
    assert "L2 Memory Entries" in rendered
    assert "Do not delete root-local .aitp stores" in rendered


def test_workspace_old_store_manifest_cli_can_write_report(tmp_path, capsys):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    init_workspace(topics_root)
    report = workspace_root / "old-store.md"

    exit_code = main(
        [
            "--base",
            str(topics_root),
            "workspace",
            "old-store-manifest",
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
    assert "read-only file manifest" in report.read_text(encoding="utf-8")


def test_workspace_old_store_manifest_cli_resolves_relative_write_path_to_workspace_root(tmp_path, capsys):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    init_workspace(topics_root)
    report = workspace_root / "reports" / "old-store.md"

    exit_code = main(
        [
            "--base",
            str(topics_root),
            "workspace",
            "old-store-manifest",
            "--workspace-root",
            str(workspace_root),
            "--write-report",
            "reports/old-store.md",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_path"] == str(report)
    assert report.exists()
