import json

from brain.v5.cli import main
from brain.v5.markdown import write_md, write_text_atomic
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace
from brain.v5.workspace_file_migration_ledger import (
    build_workspace_file_migration_ledger,
    compact_workspace_file_migration_ledger,
    render_workspace_file_migration_ledger_markdown,
)
from brain.v5.workspace_migration_plan import build_workspace_migration_plan
from brain.v5.workspace_old_store_manifest import build_workspace_old_store_manifest


def _write_workspace_with_old_and_legacy_files(tmp_path):
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
    write_md(root_topic / "topic.md", {"kind": "topic", "topic_id": "root-topic"}, "# Root topic\n")
    root_session = workspace_root / ".aitp" / "runtime" / "sessions" / "s1.md"
    write_md(root_session, {"kind": "session_binding", "session_id": "s1"}, "# Session\n")

    legacy_topic = topics_root / "legacy-topic"
    write_md(
        legacy_topic / "state.md",
        {"title": "Legacy topic", "question": "What survived?", "stage": "L3"},
        "# Legacy state\n",
    )
    write_text_atomic(legacy_topic / "research.md", "# Legacy research\n")

    migration_dir = topics_root / ".aitp" / "migrations" / "legacy-accounting-test"
    migration_dir.mkdir(parents=True)
    file_manifest = [
        {
            "topic": "legacy-topic",
            "path": "state.md",
            "size_bytes": 10,
            "sha256": "a" * 64,
            "accounting_mode": "typed_mapping",
            "mapped_as": "claim_seed",
        },
        {
            "topic": "legacy-topic",
            "path": "research.md",
            "size_bytes": 11,
            "sha256": "b" * 64,
            "accounting_mode": "archive_manifest",
            "mapped_as": "",
        },
    ]
    (migration_dir / "file_manifest.json").write_text(json.dumps(file_manifest), encoding="utf-8")
    (migration_dir / "migration_summary.json").write_text(
        json.dumps({"legacy_root": str(topics_root)}),
        encoding="utf-8",
    )
    return ws, workspace_root, migration_dir


def test_workspace_file_migration_ledger_accounts_old_and_legacy_files(tmp_path):
    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)

    payload = build_workspace_file_migration_ledger(
        ws,
        workspace_root=workspace_root,
        legacy_accounting_dir=migration_dir,
    )

    assert payload["kind"] == "aitp_workspace_file_migration_ledger"
    assert payload["summary"]["expected_old_store_file_count"] == 3
    assert payload["summary"]["expected_legacy_file_count"] == 2
    assert payload["summary"]["file_decision_count"] == 5
    assert payload["summary"]["no_omission_check"] is True
    assert payload["summary"]["blocking_file_count"] >= 4
    assert payload["summary"]["decision_counts"]["typed_import_candidate"] >= 2
    assert payload["summary"]["decision_counts"]["archive_reference"] >= 2
    assert require_valid_public_surface("workspace_file_migration_ledger", payload) == payload

    compact = compact_workspace_file_migration_ledger(payload)
    assert compact["kind"] == "aitp_workspace_file_migration_ledger_progress"
    assert compact["no_omission_check"] is True
    assert require_valid_public_surface("workspace_file_migration_ledger_progress", compact) == compact

    rendered = render_workspace_file_migration_ledger_markdown(payload)
    assert "AITP File Migration Ledger" in rendered
    assert "No old store deletion is safe" in rendered


def test_workspace_file_migration_ledger_flags_root_l2_global_replay_risk(tmp_path):
    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)
    l2_dir = workspace_root / ".aitp" / "memory" / "l2" / "entries"
    for topic in ("ads-topic", "h2o-topic"):
        write_md(
            l2_dir / f"memory-legacy-l2-{topic}-l2-entries-claim-shared-ridge.md",
            {
                "kind": "memory_entry",
                "topic_id": topic,
                "entry_id": f"memory-entry-{topic}",
            },
            "# Shared legacy L2 entry\n",
        )

    payload = build_workspace_file_migration_ledger(
        ws,
        workspace_root=workspace_root,
        legacy_accounting_dir=migration_dir,
    )

    summary = payload["summary"]
    assert summary["root_l2_global_memory_decision_count"] == 2
    assert summary["root_l2_global_memory_topic_count"] == 2
    assert summary["root_l2_global_memory_entries_per_topic"] == 1
    assert summary["root_l2_global_memory_replay_key_count"] == 1
    assert summary["root_l2_global_memory_max_topic_repetition"] == 2
    assert summary["root_l2_global_memory_uniform_topic_copy_pattern"] is True
    assert summary["root_l2_global_memory_risk"] is True
    assert summary["root_l2_global_memory_risk_triggers"] == [
        "replayed_entry_keys",
        "uniform_entries_per_topic",
    ]
    assert "multiple topic prefixes" in summary["root_l2_global_memory_risk_reason"]
    assert payload["retirement_gate"]["root_l2_global_memory_risk"] is True
    assert "cross-topic replay" in payload["retirement_gate"]["why_not_safe_now"]
    assert require_valid_public_surface("workspace_file_migration_ledger", payload) == payload

    compact = compact_workspace_file_migration_ledger(payload)
    assert compact["root_l2_global_memory_risk"] is True
    assert compact["root_l2_global_memory_uniform_topic_copy_pattern"] is True
    assert compact["root_l2_global_memory_risk_triggers"] == [
        "replayed_entry_keys",
        "uniform_entries_per_topic",
    ]
    assert compact["root_l2_global_memory_replay_key_count"] == 1
    assert require_valid_public_surface("workspace_file_migration_ledger_progress", compact) == compact

    rendered = render_workspace_file_migration_ledger_markdown(payload)
    assert "Root L2 Global Memory Risk" in rendered
    assert "Replayed entry-key count: `1`" in rendered


def test_workspace_file_migration_ledger_cli_writes_json_and_report(tmp_path, capsys):
    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)
    report = workspace_root / "ledger.md"
    out_json = workspace_root / "ledger.json"

    exit_code = main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "file-migration-ledger",
            "--workspace-root",
            str(workspace_root),
            "--legacy-accounting-dir",
            str(migration_dir),
            "--write-json",
            str(out_json),
            "--write-report",
            str(report),
            "--compact",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "aitp_workspace_file_migration_ledger_progress"
    assert payload["no_omission_check"] is True
    assert out_json.exists()
    assert report.exists()
    assert "File Migration Ledger" in report.read_text(encoding="utf-8")


def test_workspace_file_migration_ledger_cli_resolves_relative_paths_to_workspace_root(tmp_path, capsys):
    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)
    report = workspace_root / "reports" / "ledger.md"
    out_json = workspace_root / "reports" / "ledger.json"
    relative_migration_dir = migration_dir.relative_to(workspace_root).as_posix()

    exit_code = main(
        [
            "--base",
            str(ws.base),
            "workspace",
            "file-migration-ledger",
            "--workspace-root",
            str(workspace_root),
            "--legacy-accounting-dir",
            relative_migration_dir,
            "--write-json",
            "reports/ledger.json",
            "--write-report",
            "reports/ledger.md",
            "--compact",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "aitp_workspace_file_migration_ledger_progress"
    assert payload["no_omission_check"] is True
    assert out_json.exists()
    assert report.exists()


def test_workspace_file_migration_ledger_mcp_and_runtime_entrypoint(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_build_workspace_file_migration_ledger
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)

    payload = aitp_v5_build_workspace_file_migration_ledger(
        str(ws.base),
        workspace_root=str(workspace_root),
        legacy_accounting_dir=str(migration_dir),
        compact=True,
    )

    assert payload["kind"] == "aitp_workspace_file_migration_ledger_progress"
    assert runtime_entrypoints()["workspace_file_migration_ledger"]["mcp"] == "aitp_v5_build_workspace_file_migration_ledger"
    assert "write_workspace_file_migration_ledger" in runtime_entrypoints()
    assert validate_runtime_entrypoints() == []


def test_workspace_file_migration_ledger_discovers_saved_artifacts(tmp_path):
    ws, workspace_root, migration_dir = _write_workspace_with_old_and_legacy_files(tmp_path)
    saved_dir = ws.root / "migrations" / "workspace-inventory"
    saved_dir.mkdir(parents=True, exist_ok=True)
    saved_plan = saved_dir / "workspace_migration_plan.json"
    saved_manifest = saved_dir / "workspace_old_store_manifest.json"
    saved_plan.write_text(
        json.dumps(build_workspace_migration_plan(ws, workspace_root=workspace_root)),
        encoding="utf-8",
    )
    saved_manifest.write_text(
        json.dumps(build_workspace_old_store_manifest(ws, workspace_root=workspace_root)),
        encoding="utf-8",
    )

    payload = build_workspace_file_migration_ledger(ws, workspace_root=workspace_root)

    assert payload["migration_plan_source"] == str(saved_plan)
    assert payload["old_store_manifest_source"] == str(saved_manifest)
    assert payload["legacy_accounting_source"] == str(migration_dir)
    assert payload["summary"]["no_omission_check"] is True
