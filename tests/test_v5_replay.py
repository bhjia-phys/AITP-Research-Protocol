from __future__ import annotations

import json


def _seed_replay_workspace(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT in the recorded sector.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
        scope="Fixed sector counting.",
        strongest_failure_mode="wrong sector assignment",
    )
    record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="zotero",
        location_type="paper",
        uri="zotero://select/items/ABC",
        label="Counting reference",
        source_ref="paper:fqhe-counting",
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="counting sequence",
        definition="Degeneracy sequence in the fixed sector.",
        assumptions=["fixed sector"],
        source_refs=["paper:fqhe-counting"],
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate edge conformal field theory.",
        source_refs=["paper:fqhe-counting"],
    )
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting matches the edge CFT character.",
        claim_id=claim.claim_id,
        failure_modes=["wrong sector assignment"],
        source_refs=["paper:fqhe-counting"],
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="The source path reconstructs the definition and counting comparison.",
        supports_outputs=["evidence_or_provenance", "reconstruction_path"],
        source_refs=["paper:fqhe-counting"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    create_topic(ws, "gw", context_id="gw-methods", title="GW")
    gw_claim = create_claim(
        ws,
        topic_id="gw",
        statement="The self-energy code path still needs metadata validation.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="frequency grid mismatch",
    )
    bind_session(ws, "s2", topic_id="gw", context_id="gw-methods", active_claim=gw_claim.claim_id)
    return ws, claim, gw_claim, evidence


def test_workspace_replay_packet_lists_resume_queue_and_source_gaps(tmp_path):
    from dataclasses import asdict

    from brain.v5.contracts import validate_workspace_replay_packet
    from brain.v5.markdown import read_md
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.replay import write_workspace_replay_packet
    from brain.v5.source_reconstruction_review import record_source_reconstruction_review_result

    ws, claim, gw_claim, _ = _seed_replay_workspace(tmp_path)
    record_source_reconstruction_review_result(
        ws,
        claim_id=claim.claim_id,
        status="passed",
        reviewed_components=["definitions", "dependency_graph", "reconstruction_path"],
        basis_refs=["paper:fqhe-counting"],
        summary="The source stack was reviewed for replay context.",
    )

    packet = write_workspace_replay_packet(ws)
    payload = asdict(packet)

    assert validate_workspace_replay_packet(payload).ok is True
    assert require_valid_public_surface("workspace_replay_packet", {"ok": True, **payload})
    assert packet.truth_source is False
    assert packet.orientation_only is True
    assert packet.entry_count == 2
    assert packet.attention_count == 2
    assert packet.source_records["sessions"] == ["s1", "s2"]
    assert packet.source_records["claims"] == [claim.claim_id, gw_claim.claim_id]
    assert packet.workspace_backlog_summary["active_session_count"] == 2
    assert packet.workspace_backlog_summary["active_topic_count"] == 2
    assert packet.workspace_backlog_summary["active_claim_count"] == 2
    assert packet.workspace_backlog_summary["attention_count"] == 2
    coverage_summary = packet.workspace_backlog_summary["source_stack_coverage"]
    assert coverage_summary["surface"] == "source_stack_coverage_manifest"
    assert coverage_summary["claim_count"] == 2
    assert coverage_summary["coverage_status_counts"]["evidence_gap"] == 2
    assert coverage_summary["top_gap_items"][0]["claim_id"] == claim.claim_id
    assert "failure_mode" in coverage_summary["top_gap_items"][0]["missing_required_outputs"]
    assert coverage_summary["can_update_claim_trust"] is False
    source_summary = packet.workspace_backlog_summary["source_reconstruction"]
    assert source_summary["surface"] == "source_reconstruction_manifest"
    assert source_summary["complete_claim_count"] == 1
    assert source_summary["incomplete_claim_count"] == 1
    assert source_summary["review_status_counts"] == {"passed": 1, "pending": 1}
    assert source_summary["missing_component_counts"]["definitions"] == 1
    assert source_summary["top_incomplete_claims"] == [
        {
            "session_id": "s2",
            "topic_id": "gw",
            "claim_id": gw_claim.claim_id,
            "review_status": "pending",
            "missing_components": [
                "definitions",
                "assumptions_or_scope",
                "source_locations",
                "dependency_graph",
                "reconstruction_path",
                "failure_conditions",
            ],
            "next_actions": [
                "collect_required_evidence_or_provenance",
                "complete_source_reconstruction",
                "record_source_reconstruction_review_result",
                "design_falsification_or_counterargument",
            ],
            "review_packet_cli": f"aitp-v5 source reconstruction-review --claim {gw_claim.claim_id}",
            "can_update_claim_trust": False,
        }
    ]
    attention_summary = packet.workspace_backlog_summary["resume_attention"]
    assert attention_summary["attention_count"] == 2
    assert attention_summary["top_items"][0]["session_id"] == "s2"
    assert "missing_source_reconstruction" in attention_summary["top_items"][0]["attention_reasons"]

    complete = next(entry for entry in packet.entries if entry["claim_id"] == claim.claim_id)
    incomplete = next(entry for entry in packet.entries if entry["claim_id"] == gw_claim.claim_id)
    assert complete["source_reconstruction_complete"] is True
    assert complete["source_reconstruction_review_status"] == "passed"
    assert complete["source_reconstruction_review_result_ids"]
    assert "record_source_reconstruction_review_result" not in complete["next_actions"]
    assert complete["missing_source_components"] == []
    assert incomplete["source_reconstruction_complete"] is False
    assert incomplete["source_reconstruction_review_status"] == "pending"
    assert incomplete["source_reconstruction_review_result_ids"] == []
    assert "definitions" in incomplete["missing_source_components"]
    assert "source_reconstruction_review_pending" in incomplete["attention_reasons"]
    assert "record_source_reconstruction_review_result" in incomplete["next_actions"]

    _, body = read_md(packet.files["replay_packet"])
    assert "Workspace Replay Packet" in body
    assert claim.claim_id in body
    assert gw_claim.claim_id in body
    assert "Cross-Topic Backlog" in body
    assert "Source Stack Coverage" in body
    assert f"`{gw_claim.claim_id}`" in body
    assert "Source review: `pending`" in body
    assert "orientation only" in body


def test_workspace_replay_packet_uses_temporal_source_review_order(tmp_path):
    import os

    from brain.v5.models import SourceReconstructionReviewResultRecord
    from brain.v5.replay import write_workspace_replay_packet
    from brain.v5.store import write_record

    ws, claim, _, _ = _seed_replay_workspace(tmp_path)
    review_dir = ws.registry_dir("source_reconstruction_reviews")
    older_path = review_dir / "source-reconstruction-review-z-older.md"
    newer_path = review_dir / "source-reconstruction-review-a-newer.md"
    write_record(
        older_path,
        SourceReconstructionReviewResultRecord(
            result_id=older_path.stem,
            topic_id=claim.topic_id,
            claim_id=claim.claim_id,
            status="passed",
            reviewed_components=["definitions"],
            basis_refs=["paper:fqhe-counting"],
            summary="Older replay review should not win because its id sorts later.",
        ),
    )
    write_record(
        newer_path,
        SourceReconstructionReviewResultRecord(
            result_id=newer_path.stem,
            topic_id=claim.topic_id,
            claim_id=claim.claim_id,
            status="inconclusive",
            reviewed_components=["definitions"],
            basis_refs=["paper:fqhe-counting"],
            remaining_actions=["record_missing_scope_review"],
            summary="Newer replay review should be selected by file mtime for legacy records.",
        ),
    )
    os.utime(older_path, (1_800_000_000, 1_800_000_000))
    os.utime(newer_path, (1_800_000_100, 1_800_000_100))

    packet = write_workspace_replay_packet(ws)

    entry = next(entry for entry in packet.entries if entry["claim_id"] == claim.claim_id)
    assert entry["source_reconstruction_review_status"] == "inconclusive"
    assert entry["source_reconstruction_review_result_ids"] == [
        older_path.stem,
        newer_path.stem,
    ]


def test_workspace_replay_packet_can_include_legacy_semantic_review_backlog(tmp_path):
    from dataclasses import asdict

    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.markdown import read_md
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.replay import write_workspace_replay_packet
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    migration = ws.root / "migrations" / "legacy-run"
    migration.mkdir(parents=True)
    (migration / "migration_summary.json").write_text(
        json.dumps(
            {
                "kind": "legacy_v5_lossless_migration_report",
                "run_id": "legacy-run",
                "workspace": str(ws.base),
                "legacy_root": str(ws.base / "research" / "aitp-topics"),
                "v5_root": str(ws.root),
                "totals": {
                    "topic_count": 1,
                    "legacy_file_count": 1,
                    "post_legacy_file_count": 1,
                    "legacy_manifest_hash_stable": True,
                    "legacy_manifest_change_count": 0,
                    "archive_reference_count": 0,
                    "accounted_file_count": 1,
                    "summary_inputs_trusted": False,
                },
                "topics": [
                    {
                        "topic": "legacy-l2",
                        "status": "ok",
                        "file_count": 1,
                        "audit_mapped_file_count": 1,
                        "structured_file_count": 1,
                        "archive_reference_count": 0,
                        "accounted_file_count": 1,
                        "missing_expected_paths": [],
                        "can_write_v5_records": False,
                        "active_claim_id": "claim-l2",
                        "written_records": {
                            "topics": 1,
                            "claims": 1,
                            "evidence": 1,
                            "reference_locations": 0,
                            "sensemaking_reports": 1,
                            "trace_events": 0,
                            "memory_entries": 1,
                        },
                        "preserved_source_refs": 0,
                        "summary_inputs_trusted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (migration / "verification_report.json").write_text(
        json.dumps(
            {
                "kind": "legacy_v5_lossless_migration_verification",
                "run_id": "legacy-run",
                "file_accounting_ok": True,
                "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
                "archive_reference_check": {
                    "archive_records_checked": 0,
                    "archive_records_expected": 0,
                    "registry_archive_reference_count": 0,
                    "problem_count": 0,
                    "problems": [],
                },
                "markdown_readability_check": {
                    "markdown_files_checked": 1,
                    "problem_count": 0,
                    "problems": [],
                },
                "all_checks_ok": True,
            }
        ),
        encoding="utf-8",
    )
    manifest = migration / "legacy_manifest_pre.jsonl"
    manifest.write_text(
        json.dumps({"topic": "legacy-l2", "path": "state.md", "sha256": "abc"}) + "\n",
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
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=migration,
        topic="legacy-l2",
        status="inconclusive",
        summary="Legacy L2 remains orientation-only until typed review is complete.",
        active_claim_id="claim-l2",
        reviewed_legacy_refs=["legacy_archive:L2/index.md"],
        reviewed_typed_refs=["claim-l2"],
        remaining_actions=[
            "review_legacy_l2_memory_entry_candidates",
            "decide_human_checkpoint_before_promotion",
        ],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="legacy-l2",
        claim_id="claim-l2",
        reason="legacy semantic review promotion decision",
        requested_by="legacy_semantic_review",
        options=["approve_semantic_review", "keep_backlog_blocking"],
    )

    packet = write_workspace_replay_packet(ws, migration_dir=migration)
    payload = asdict(packet)

    assert require_valid_public_surface("workspace_replay_packet", {"ok": True, **payload})["ok"] is True
    legacy = packet.workspace_backlog_summary["legacy_semantic_review"]
    legacy_source = packet.workspace_backlog_summary["legacy_source_reconstruction"]
    legacy_repair = packet.workspace_backlog_summary["legacy_semantic_repair"]
    legacy_checkpoints = packet.workspace_backlog_summary["legacy_human_checkpoints"]
    legacy_executable = packet.workspace_backlog_summary["legacy_executable_evidence"]
    assert legacy == {
        "surface": "legacy_semantic_review_manifest",
        "migration_dir": str(migration),
        "review_item_count": 1,
        "review_progress": {
            "passed": 0,
            "inconclusive": 1,
            "needs_revision": 0,
            "pending": 0,
        },
        "semantic_lossless_proven": False,
        "open_human_checkpoint_count": 1,
        "open_human_checkpoints": [
            {
                "topic": "legacy-l2",
                "active_claim_id": "claim-l2",
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint_ref": f"human-checkpoint:{checkpoint.checkpoint_id}",
                "action": "decide_human_checkpoint_before_promotion",
                "decision_cli": (
                    f"aitp-v5 --base {ws.base} checkpoint decide {checkpoint.checkpoint_id} "
                    "--decision <approve_semantic_review|keep_backlog_blocking> "
                    "--rationale <human rationale> --decided-by <reviewer>"
                ),
                "decision_mcp": "aitp_v5_decide_human_checkpoint",
                "can_update_claim_trust": False,
            }
        ],
        "top_backlog_items": [
            {
                "topic": "legacy-l2",
                "active_claim_id": "claim-l2",
                "review_status": "inconclusive",
                "review_priority": "high",
                "latest_review_id": review.review_id,
                "packet_cli": (
                    f"aitp-v5 --base {ws.base} legacy semantic-review-packet "
                    f"--migration-dir {migration} --topic legacy-l2"
                ),
                "can_update_claim_trust": False,
            }
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert legacy_source == {
        "surface": "legacy_source_reconstruction_manifest",
        "migration_dir": str(migration),
        "work_item_count": 1,
        "repair_status_counts": {
            "awaiting_needs_revision_review": 1,
            "no_repair_candidates": 0,
            "proposed_repairs": 0,
        },
        "proposed_repair_count": 0,
        "top_backlog_items": [
            {
                "topic": "legacy-l2",
                "active_claim_id": "claim-l2",
                "latest_review_id": review.review_id,
                "repair_status": "awaiting_needs_revision_review",
                "missing_components": [
                    "definitions",
                    "assumptions_or_scope",
                    "source_locations",
                    "dependency_graph",
                    "reconstruction_path",
                    "failure_conditions",
                ],
                "required_actions": [
                    "inspect_legacy_refs_for_source_reconstruction_components",
                    "record_source_reconstruction_review_result",
                    "record_needs_revision_review_with_specific_source_reconstruction_basis",
                ],
                "review_packet_cli": (
                    f"aitp-v5 --base {ws.base} legacy source-reconstruction-review "
                    f"--migration-dir {migration} --topic legacy-l2"
                ),
                "can_update_claim_trust": False,
            }
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert legacy_repair == {
        "surface": "legacy_semantic_repair_manifest",
        "migration_dir": str(migration),
        "work_item_count": 1,
        "repair_status_counts": {
            "awaiting_needs_revision_review": 1,
            "no_repair_candidates": 0,
            "proposed_repairs": 0,
        },
        "proposed_repair_count": 0,
        "required_action_counts": {
            "keep_semantic_review_blocking_until_typed_review_basis_exists": 1,
            "record_needs_revision_review_with_specific_repair_basis": 1,
        },
        "top_repair_items": [
            {
                "topic": "legacy-l2",
                "active_claim_id": "claim-l2",
                "latest_review_id": review.review_id,
                "review_status": "inconclusive",
                "repair_status": "awaiting_needs_revision_review",
                "proposed_repair_count": 0,
                "proposed_repair_types": [],
                "required_actions": [
                    "record_needs_revision_review_with_specific_repair_basis",
                    "keep_semantic_review_blocking_until_typed_review_basis_exists",
                ],
                "repair_plan_cli": (
                    f"aitp-v5 --base {ws.base} legacy semantic-repair-plan "
                    f"--migration-dir {migration} --topic legacy-l2"
                ),
                "can_update_claim_trust": False,
            }
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert legacy_checkpoints == {
        "surface": "legacy_human_checkpoint_packet",
        "migration_dir": str(migration),
        "checkpoint_item_count": 1,
        "open_decision_count": 1,
        "pending_request_count": 0,
        "next_action_count": 1,
        "top_checkpoint_items": [
            {
                "topic": "legacy-l2",
                "active_claim_id": "claim-l2",
                "latest_review_id": review.review_id,
                "review_status": "inconclusive",
                "action": "decide_human_checkpoint_before_promotion",
                "mode": "decide_open_checkpoint",
                "checkpoint_id": checkpoint.checkpoint_id,
                "reason": "legacy semantic review promotion decision",
                "options": ["approve_semantic_review", "keep_backlog_blocking"],
                "cli": (
                    f"aitp-v5 --base {ws.base} checkpoint decide {checkpoint.checkpoint_id} "
                    "--decision <approve_semantic_review|keep_backlog_blocking> "
                    "--rationale <human rationale> --decided-by <reviewer>"
                ),
                "mcp": "aitp_v5_decide_human_checkpoint",
                "can_update_claim_trust": False,
            }
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert legacy_executable == {
        "surface": "legacy_executable_evidence_packet",
        "migration_dir": str(migration),
        "evidence_item_count": 0,
        "executable_action_count": 0,
        "top_evidence_items": [],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    _, body = read_md(packet.files["replay_packet"])
    assert "Legacy Semantic Review Backlog" in body
    assert "Legacy Source Reconstruction Backlog" in body
    assert "Legacy Semantic Repair Triage" in body
    assert "Legacy Human Checkpoints" in body
    assert "Legacy Executable Evidence" in body
    assert "Source reconstruction items: 1" in body
    assert "Semantic repair items: 1" in body
    assert "Proposed semantic repairs: 0" in body
    assert "Checkpoint decisions: 1 open, 0 pending request" in body
    assert "Executable evidence items: 0" in body
    assert "Open human checkpoints: 1" in body
    assert checkpoint.checkpoint_id in body
    assert "semantic lossless proven: False" in body
    assert "legacy-l2" in body


def test_workspace_replay_includes_legacy_executable_evidence_blockers(tmp_path):
    from dataclasses import asdict

    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.replay import write_workspace_replay_packet
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
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
                        "topic": "crpa",
                        "status": "ok",
                        "file_count": 1,
                        "accounted_file_count": 1,
                        "can_write_v5_records": False,
                        "active_claim_id": "claim-crpa",
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
        ws.registry_dir("claims") / "claim-crpa.md",
        ClaimRecord(
            claim_id="claim-crpa",
            topic_id="crpa",
            statement="The cRPA benchmark still needs executable validation.",
            evidence_profile="code_method",
            confidence_state="legacy_seed",
            active_uncertainty="Executable SrVO3 benchmark missing.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=migration,
        topic="crpa",
        status="inconclusive",
        summary="Executable evidence remains missing before semantic pass.",
        active_claim_id="claim-crpa",
        reviewed_typed_refs=["claim-crpa", "validation-contract:validation-contract-crpa"],
        remaining_actions=[
            "implement_or_import_executable_SrVO3_t2g_crpa_benchmark_with_Wannier_U_J_outputs"
        ],
    )

    packet = write_workspace_replay_packet(ws, migration_dir=migration)
    payload = asdict(packet)

    assert require_valid_public_surface("workspace_replay_packet", {"ok": True, **payload})["ok"] is True
    executable = packet.workspace_backlog_summary["legacy_executable_evidence"]
    assert executable["surface"] == "legacy_executable_evidence_packet"
    assert executable["evidence_item_count"] == 1
    assert executable["executable_action_count"] == 1
    assert executable["top_evidence_items"][0]["topic"] == "crpa"
    assert executable["top_evidence_items"][0]["latest_review_id"] == review.review_id
    assert executable["top_evidence_items"][0]["executable_actions"] == [
        "implement_or_import_executable_SrVO3_t2g_crpa_benchmark_with_Wannier_U_J_outputs"
    ]
    assert executable["top_evidence_items"][0]["validation_command_count"] == 1
    assert executable["top_evidence_items"][0]["tool_run_command_count"] == 0
    assert executable["can_update_claim_trust"] is False


def test_workspace_replay_packet_cli_mcp_and_runtime(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_workspace_replay_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    _seed_replay_workspace(tmp_path)

    assert main(["--base", str(tmp_path), "summary", "replay"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_workspace_replay_packet(str(tmp_path))

    assert cli_payload["kind"] == "workspace_replay_packet"
    assert cli_payload["truth_source"] is False
    assert mcp_payload["kind"] == "workspace_replay_packet"
    assert runtime_entrypoints()["workspace_replay"] == {
        "cli": "aitp-v5 summary replay",
        "mcp": "aitp_v5_write_workspace_replay_packet",
        "surface": "workspace_replay_packet",
    }


def test_workspace_replay_packet_cli_mcp_accept_migration_dir(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_workspace_replay_packet
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
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
        str(ws.base),
        "summary",
        "replay",
        "--migration-dir",
        str(migration),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_workspace_replay_packet(str(ws.base), migration_dir=str(migration))

    assert cli_payload["kind"] == "workspace_replay_packet"
    assert cli_payload["workspace_backlog_summary"]["legacy_semantic_review"]["review_item_count"] == 1
    assert cli_payload["workspace_backlog_summary"]["legacy_source_reconstruction"]["work_item_count"] == 1
    assert mcp_payload["workspace_backlog_summary"]["legacy_semantic_review"]["migration_dir"] == str(migration)
    assert mcp_payload["workspace_backlog_summary"]["legacy_source_reconstruction"]["surface"] == "legacy_source_reconstruction_manifest"
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["can_update_kernel_state"] is False
