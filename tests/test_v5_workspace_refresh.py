from __future__ import annotations

import json


def _seed_workspace(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.models import MemoryEntryRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence still needs a replay check.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source reconstruction",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="note",
        status="supports",
        summary="A source note exists.",
        supports_outputs=["evidence_or_provenance"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    memory = MemoryEntryRecord(
        entry_id="memory-fqhe-active",
        topic_id="fqhe",
        source_claim_id=claim.claim_id,
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=["validation-result-fqhe"],
        statement="Counting replay memory.",
    )
    legacy_seed = MemoryEntryRecord(
        entry_id="memory-fqhe-legacy-seed",
        topic_id="fqhe",
        source_claim_id=claim.claim_id,
        evidence_refs=["legacy:evidence"],
        status="legacy_seed",
    )
    write_record(ws.root / "memory" / "l2" / "entries" / f"{memory.entry_id}.md", memory)
    write_record(ws.root / "memory" / "l2" / "entries" / f"{legacy_seed.entry_id}.md", legacy_seed)
    return ws, claim, evidence, memory


def test_workspace_refresh_writes_summary_replay_and_obsidian_views(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace_refresh import refresh_workspace_views

    ws, claim, _, memory = _seed_workspace(tmp_path)

    payload = refresh_workspace_views(ws)

    assert payload["kind"] == "workspace_refresh_bundle"
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert payload["refreshed_surfaces"] == [
        "workspace_summary_bundle",
        "workspace_replay_packet",
        "l2_obsidian_view_bundle",
        "source_reconstruction_obsidian_view_bundle",
        "workspace_interaction_preview_bundle",
        "interaction_recording_worklist",
    ]
    assert payload["source_records"]["sessions"] == ["s1"]
    assert payload["source_records"]["claims"] == [claim.claim_id]
    assert payload["source_records"]["memory_entries"] == [memory.entry_id]
    assert payload["source_records"]["validation_results"] == ["validation-result-fqhe"]
    assert payload["workspace_summary"]["files"]["overview"].endswith("overview.md")
    assert payload["workspace_replay"]["files"]["replay_packet"].endswith("replay_packet.md")
    assert payload["workspace_replay"]["workspace_backlog_summary"]["active_session_count"] == 1
    assert payload["workspace_replay"]["workspace_backlog_summary"]["source_reconstruction"][
        "incomplete_claim_count"
    ] == 1
    assert payload["workspace_replay"]["workspace_backlog_summary"]["source_reconstruction"][
        "top_incomplete_claims"
    ][0]["claim_id"] == claim.claim_id
    assert payload["l2_obsidian_view"]["files"]["overview"].endswith("L2 Memory Overview.md")
    assert payload["l2_obsidian_view"]["memory_entry_count"] == 1
    assert payload["source_reconstruction_obsidian_view"]["files"]["review_worklist"].endswith(
        "Source Reconstruction Review Worklist.md"
    )
    assert payload["workspace_interaction_preview"]["session_count"] == 1
    assert payload["workspace_interaction_preview"]["decision_mode_counts"] == {"guarded_recording": 1}
    assert payload["workspace_interaction_preview"]["can_update_claim_trust"] is False
    assert payload["interaction_recording_worklist"]["work_item_count"] == 1
    assert payload["interaction_recording_worklist"]["items"][0]["action_kind"] == (
        "record_sensemaking_then_evidence_before_trust"
    )
    assert payload["interaction_recording_worklist"]["can_update_kernel_state"] is False
    assert require_valid_public_surface("workspace_refresh_bundle", payload) == payload


def test_workspace_refresh_can_include_legacy_semantic_backlog_in_replay(tmp_path):
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace_refresh import refresh_workspace_views

    ws, _claim, _evidence, _memory = _seed_workspace(tmp_path)
    migration = ws.root / "migrations" / "legacy-run"
    migration.mkdir(parents=True)
    (migration / "migration_summary.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "workspace": str(ws.base),
                "legacy_root": str(ws.base / "research" / "aitp-topics"),
                "v5_root": str(ws.root),
                "totals": {"topic_count": 1, "legacy_file_count": 1, "post_legacy_file_count": 1},
                "topics": [
                    {
                        "topic": "legacy-l2",
                        "status": "ok",
                        "file_count": 1,
                        "accounted_file_count": 1,
                        "can_write_v5_records": False,
                        "active_claim_id": "claim-l2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (migration / "verification_report.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "file_accounting_ok": True,
                "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
                "archive_reference_check": {
                    "archive_records_checked": 0,
                    "archive_records_expected": 0,
                    "registry_archive_reference_count": 0,
                    "problem_count": 0,
                },
                "markdown_readability_check": {"markdown_files_checked": 1, "problem_count": 0},
            }
        ),
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-l2.md",
        ClaimRecord(
            claim_id="claim-l2",
            topic_id="legacy-l2",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy L2 graph needs typed review.",
        ),
    )

    payload = refresh_workspace_views(ws, migration_dir=migration)

    legacy = payload["workspace_replay"]["workspace_backlog_summary"]["legacy_semantic_review"]
    assert payload["refreshed_surfaces"] == [
        "workspace_summary_bundle",
        "workspace_replay_packet",
        "l2_obsidian_view_bundle",
        "source_reconstruction_obsidian_view_bundle",
        "workspace_interaction_preview_bundle",
        "interaction_recording_worklist",
        "legacy_source_reconstruction_obsidian_view_bundle",
        "legacy_semantic_review_obsidian_view_bundle",
        "legacy_human_checkpoint_obsidian_view_bundle",
    ]
    assert payload["legacy_source_reconstruction_obsidian_view"]["files"]["review_worklist"].endswith(
        "Legacy Source Reconstruction Worklist.md"
    )
    assert payload["legacy_source_reconstruction_obsidian_view"]["work_item_count"] == 1
    assert payload["legacy_source_reconstruction_obsidian_view"]["can_update_claim_trust"] is False
    assert payload["legacy_semantic_review_obsidian_view"]["files"]["review_worklist"].endswith(
        "Legacy Semantic Review Worklist.md"
    )
    assert payload["legacy_human_checkpoint_obsidian_view"]["files"]["checkpoint_worklist"].endswith(
        "Legacy Human Checkpoints.md"
    )
    assert payload["workspace_interaction_preview"]["session_count"] == 1
    assert payload["interaction_recording_worklist"]["work_item_count"] == 1
    assert legacy["surface"] == "legacy_semantic_review_manifest"
    assert legacy["review_item_count"] == 1
    assert legacy["semantic_lossless_proven"] is False
    assert payload["can_update_claim_trust"] is False
    assert require_valid_public_surface("workspace_refresh_bundle", payload) == payload


def test_workspace_refresh_cli_mcp_and_runtime(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_refresh_workspace_views
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    _seed_workspace(tmp_path)

    assert main(["--base", str(tmp_path), "summary", "refresh"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_refresh_workspace_views(str(tmp_path))

    assert cli_payload["kind"] == "workspace_refresh_bundle"
    assert mcp_payload["kind"] == "workspace_refresh_bundle"
    assert cli_payload["workspace_interaction_preview"]["session_count"] == 1
    assert mcp_payload["workspace_interaction_preview"]["decision_mode_counts"] == {"guarded_recording": 1}
    assert cli_payload["interaction_recording_worklist"]["work_item_count"] == 1
    assert mcp_payload["interaction_recording_worklist"]["can_update_claim_trust"] is False
    assert runtime_entrypoints()["workspace_refresh"] == {
        "cli": "aitp-v5 summary refresh",
        "mcp": "aitp_v5_refresh_workspace_views",
        "surface": "workspace_refresh_bundle",
    }


def test_workspace_refresh_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main

    _seed_workspace(tmp_path)

    assert main(["--base", str(tmp_path), "summary", "refresh", "--compact"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    assert cli_payload["kind"] == "workspace_refresh_progress"
    assert cli_payload["source_surface"] == "workspace_refresh_bundle"
    assert cli_payload["refreshed_surface_count"] == 6
    assert cli_payload["refreshed_surfaces"] == [
        "workspace_summary_bundle",
        "workspace_replay_packet",
        "l2_obsidian_view_bundle",
        "source_reconstruction_obsidian_view_bundle",
        "workspace_interaction_preview_bundle",
        "interaction_recording_worklist",
    ]
    assert cli_payload["workspace_summary"] == {
        "session_count": 1,
        "active_claim_count": 1,
        "memory_entry_count": 1,
    }
    assert cli_payload["workspace_replay"]["entry_count"] == 1
    assert cli_payload["workspace_replay"]["attention_count"] == 1
    assert cli_payload["l2_typed_graph"] == {
        "memory_entry_count": 1,
        "physics_object_count": 0,
        "object_relation_count": 0,
        "sensemaking_report_count": 0,
    }
    assert cli_payload["workspace_interaction_preview"] == {
        "session_count": 1,
        "decision_mode_counts": {"guarded_recording": 1},
    }
    assert cli_payload["interaction_recording_worklist"] == {
        "work_item_count": 1,
        "required_now_count": 0,
        "decision_mode_counts": {"guarded_recording": 1},
    }
    assert cli_payload["source_reconstruction"]["incomplete_claim_count"] == 1
    assert cli_payload["source_reconstruction_review"] == {
        "claim_count": 1,
        "incomplete_claim_count": 1,
        "review_progress": {
            "passed": 0,
            "needs_revision": 0,
            "inconclusive": 0,
            "pending": 1,
        },
        "next_action_count": 1,
    }
    assert cli_payload["can_update_claim_trust"] is False
    assert "l2_obsidian_view" not in cli_payload
    assert "items" not in cli_payload


def test_workspace_refresh_cli_mcp_accept_migration_dir(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_refresh_workspace_views
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record

    ws, _claim, _evidence, _memory = _seed_workspace(tmp_path)
    migration = ws.root / "migrations" / "legacy-run"
    migration.mkdir(parents=True)
    (migration / "migration_summary.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "workspace": str(ws.base),
                "legacy_root": str(ws.base / "research" / "aitp-topics"),
                "v5_root": str(ws.root),
                "totals": {"topic_count": 1, "legacy_file_count": 1, "post_legacy_file_count": 1},
                "topics": [
                    {
                        "topic": "legacy-l2",
                        "status": "ok",
                        "file_count": 1,
                        "accounted_file_count": 1,
                        "can_write_v5_records": False,
                        "active_claim_id": "claim-l2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (migration / "verification_report.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "file_accounting_ok": True,
                "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
                "archive_reference_check": {
                    "archive_records_checked": 0,
                    "archive_records_expected": 0,
                    "registry_archive_reference_count": 0,
                    "problem_count": 0,
                },
                "markdown_readability_check": {"markdown_files_checked": 1, "problem_count": 0},
            }
        ),
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-l2.md",
        ClaimRecord(
            claim_id="claim-l2",
            topic_id="legacy-l2",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy L2 graph needs typed review.",
        ),
    )

    assert main([
        "--base",
        str(tmp_path),
        "summary",
        "refresh",
        "--migration-dir",
        str(migration),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_refresh_workspace_views(str(tmp_path), migration_dir=str(migration))

    assert cli_payload["workspace_replay"]["workspace_backlog_summary"]["legacy_semantic_review"]["review_item_count"] == 1
    assert cli_payload["workspace_replay"]["workspace_backlog_summary"]["legacy_semantic_repair"]["work_item_count"] == 1
    assert mcp_payload["workspace_replay"]["workspace_backlog_summary"]["legacy_semantic_review"]["migration_dir"] == str(migration)
    assert mcp_payload["workspace_replay"]["workspace_backlog_summary"]["legacy_semantic_repair"]["surface"] == "legacy_semantic_repair_manifest"
    assert cli_payload["legacy_source_reconstruction_obsidian_view"]["work_item_count"] == 1
    assert mcp_payload["legacy_source_reconstruction_obsidian_view"]["derived_from"] == "legacy_source_reconstruction_manifest"
    assert cli_payload["workspace_interaction_preview"]["session_count"] == 1
    assert mcp_payload["workspace_interaction_preview"]["can_update_kernel_state"] is False
    assert cli_payload["interaction_recording_worklist"]["work_item_count"] == 1
    assert mcp_payload["interaction_recording_worklist"]["can_update_claim_trust"] is False
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["can_update_kernel_state"] is False


def test_workspace_refresh_cli_compact_progress_accepts_migration_dir(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record

    ws, _claim, _evidence, _memory = _seed_workspace(tmp_path)
    migration = ws.root / "migrations" / "legacy-run"
    migration.mkdir(parents=True)
    (migration / "migration_summary.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "workspace": str(ws.base),
                "legacy_root": str(ws.base / "research" / "aitp-topics"),
                "v5_root": str(ws.root),
                "totals": {"topic_count": 1, "legacy_file_count": 1, "post_legacy_file_count": 1},
                "topics": [
                    {
                        "topic": "legacy-l2",
                        "status": "ok",
                        "file_count": 1,
                        "accounted_file_count": 1,
                        "can_write_v5_records": False,
                        "active_claim_id": "claim-l2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (migration / "verification_report.json").write_text(
        json.dumps(
            {
                "run_id": "legacy-run",
                "file_accounting_ok": True,
                "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
                "archive_reference_check": {
                    "archive_records_checked": 0,
                    "archive_records_expected": 0,
                    "registry_archive_reference_count": 0,
                    "problem_count": 0,
                },
                "markdown_readability_check": {"markdown_files_checked": 1, "problem_count": 0},
            }
        ),
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-l2.md",
        ClaimRecord(
            claim_id="claim-l2",
            topic_id="legacy-l2",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy L2 graph needs typed review.",
        ),
    )

    assert main([
        "--base",
        str(tmp_path),
        "summary",
        "refresh",
        "--migration-dir",
        str(migration),
        "--compact",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    assert cli_payload["refreshed_surface_count"] == 9
    assert cli_payload["legacy_source_reconstruction"] == {
        "work_item_count": 1,
        "repair_status_counts": {
            "awaiting_needs_revision_review": 1,
            "no_repair_candidates": 0,
            "proposed_repairs": 0,
        },
        "proposed_repair_count": 0,
    }
    assert cli_payload["legacy_semantic_repair"] == {
        "work_item_count": 1,
        "repair_status_counts": {
            "awaiting_needs_revision_review": 1,
            "no_repair_candidates": 0,
            "proposed_repairs": 0,
        },
        "proposed_repair_count": 0,
        "required_action_counts": {
            "keep_semantic_review_blocking_until_typed_review_basis_exists": 1,
            "record_initial_semantic_review_result": 1,
        },
    }
    assert cli_payload["legacy_semantic_review"]["work_item_count"] == 1
    assert cli_payload["source_reconstruction_review"]["claim_count"] == 2
    assert cli_payload["source_reconstruction_review"]["incomplete_claim_count"] == 2
    assert cli_payload["source_reconstruction_review"]["review_progress"]["pending"] == 2
    assert cli_payload["legacy_semantic_review"]["semantic_lossless_proven"] is False
    assert cli_payload["legacy_human_checkpoints"]["open_decision_count"] == 0
    assert cli_payload["can_update_kernel_state"] is False
