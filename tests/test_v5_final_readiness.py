from __future__ import annotations

import json


def _seed_claim(ws):
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import create_claim, create_topic

    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The finite-size counting sequence identifies the scoped edge CFT sector.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
        scope="N<=10 fixed sector.",
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
        assumptions=["fixed particle number"],
        source_refs=["paper:fqhe-counting"],
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate chiral edge conformal field theory.",
        source_refs=["paper:fqhe-counting"],
    )
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence matches the edge CFT character.",
        claim_id=claim.claim_id,
        assumptions=["same sector convention"],
        failure_modes=["wrong sector assignment"],
        source_refs=["paper:fqhe-counting"],
    )
    record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="Definition, sector convention, and counting comparison are reconstructable.",
        supports_outputs=["reconstruction_path"],
        source_refs=["paper:fqhe-counting"],
    )
    return claim


def _write_migration_run(ws, *, topic_count=2):
    run = ws.root / "migrations" / "legacy-v5-lossless-test"
    run.mkdir(parents=True)
    topics = [
        {
            "topic": f"legacy-topic-{index}",
            "status": "ok",
            "file_count": 2,
            "audit_mapped_file_count": 2,
            "structured_file_count": 1,
            "archive_reference_count": 1,
            "accounted_file_count": 2,
            "missing_expected_paths": [],
            "can_write_v5_records": True,
            "active_claim_id": f"claim-legacy-{index}",
            "written_records": {"claims": 1, "evidence": 1, "reference_locations": 1},
            "preserved_source_refs": 1,
            "summary_inputs_trusted": False,
        }
        for index in range(topic_count)
    ]
    summary = {
        "kind": "legacy_v5_lossless_migration_report",
        "run_id": "legacy-v5-lossless-test",
        "workspace": str(ws.base),
        "legacy_root": str(ws.base / "research" / "aitp-topics"),
        "v5_root": str(ws.root),
        "output_dir": str(run),
        "totals": {
            "topic_count": topic_count,
            "legacy_file_count": topic_count * 2,
            "post_legacy_file_count": topic_count * 2,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "structured_file_count": topic_count,
            "archive_reference_count": topic_count,
            "accounted_file_count": topic_count * 2,
            "topics_with_errors": 0,
            "missing_archive_record_files": 0,
            "summary_inputs_trusted": False,
        },
        "topics": topics,
    }
    verification = {
        "kind": "legacy_v5_lossless_migration_verification",
        "run_id": "legacy-v5-lossless-test",
        "file_accounting_ok": True,
        "manifest_check": {"pre_count": topic_count * 2, "post_count": topic_count * 2, "missing": 0, "extra": 0, "changed": 0},
        "archive_reference_check": {
            "archive_records_checked": topic_count,
            "archive_records_expected": topic_count,
            "registry_archive_reference_count": topic_count,
            "problem_count": 0,
            "problems": [],
        },
        "markdown_readability_check": {"markdown_files_checked": topic_count * 2, "problem_count": 0, "problems": []},
        "brief_check": [],
        "all_checks_ok": True,
    }
    (run / "migration_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run / "verification_report.json").write_text(json.dumps(verification), encoding="utf-8")
    return run


def test_final_readiness_audit_keeps_kernel_capability_separate_from_content_backlog(tmp_path):
    from brain.v5.final_readiness import audit_final_engineering_readiness
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    claim = _seed_claim(ws)
    run = _write_migration_run(ws, topic_count=2)

    payload = audit_final_engineering_readiness(ws, migration_dir=run)

    assert payload["kind"] == "final_engineering_readiness_audit"
    assert payload["completion_status"] == "kernel_ready_content_backlog"
    assert payload["kernel_capability_status"] == "ready_for_priority_hosts"
    assert payload["content_backlog_status"] == "legacy_semantic_review_backlog"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["kernel_capabilities"]["record_gate_coverage"]["ungated_record_protocols"] == []
    assert payload["kernel_capabilities"]["source_stack"]["active_claim_count"] == 1
    assert payload["kernel_capabilities"]["source_stack"]["complete_claim_count"] == 1
    assert payload["kernel_capabilities"]["source_stack"]["incomplete_claim_ids"] == []
    assert payload["kernel_capabilities"]["knowledge_stack"]["obsidian_view_surface"] == "l2_obsidian_view_bundle"
    assert payload["kernel_capabilities"]["long_term_replay"]["surface"] == "workspace_replay_packet"
    assert payload["kernel_capabilities"]["long_term_replay"]["legacy_semantic_backlog_surface"] == (
        "legacy_semantic_review_manifest"
    )
    assert payload["kernel_capabilities"]["long_term_replay"]["migration_dir_argument"] == "--migration-dir"
    assert payload["kernel_capabilities"]["natural_interaction"]["surface"] == "interaction_recording_preview"
    assert payload["kernel_capabilities"]["natural_interaction"]["recording_decision_modes"] == [
        "lightweight_trace",
        "guarded_recording",
        "trust_boundary_checkpoint",
    ]
    assert payload["kernel_capabilities"]["natural_interaction"]["next_kernel_entrypoints"] == [
        "aitp_v5_record_sensemaking_report",
        "aitp_v5_request_human_checkpoint",
        "aitp_v5_preflight_trust_update",
    ]
    assert payload["kernel_capabilities"]["natural_interaction"]["can_update_claim_trust"] is False
    assert payload["kernel_capabilities"]["host_integration"]["priority_hosts"] == ["codex", "claude_code", "kimi_code"]
    assert payload["kernel_capabilities"]["host_integration"]["deferred_hosts"] == ["opencode"]
    assert payload["kernel_capabilities"]["host_integration"]["production_loop_surface"] == (
        "runtime_host_readiness_audit"
    )
    assert payload["kernel_capabilities"]["host_integration"]["priority_host_production_loops"] == [
        {
            "runtime": "codex",
            "readiness_cli": "aitp-v5 adapter host-readiness codex",
            "lifecycle_cli": "aitp-v5 adapter host-lifecycle codex",
            "session_start_smoke_supported": False,
            "can_update_claim_trust": False,
        },
        {
            "runtime": "claude_code",
            "readiness_cli": "aitp-v5 adapter host-readiness claude-code --run-session-start-smoke --session <session-id>",
            "lifecycle_cli": "aitp-v5 adapter host-lifecycle claude-code",
            "session_start_smoke_supported": True,
            "can_update_claim_trust": False,
        },
        {
            "runtime": "kimi_code",
            "readiness_cli": "aitp-v5 adapter host-readiness kimi-code --run-session-start-smoke --session <session-id>",
            "lifecycle_cli": "aitp-v5 adapter host-lifecycle kimi-code",
            "session_start_smoke_supported": True,
            "can_update_claim_trust": False,
        },
    ]
    assert payload["content_backlog"]["legacy_semantic_review"]["review_item_count"] == 2
    assert payload["content_backlog"]["legacy_semantic_review"]["worklist_surface"] == (
        "legacy_semantic_review_worklist"
    )
    assert payload["content_backlog"]["legacy_semantic_review"]["work_item_count"] == 2
    assert payload["content_backlog"]["legacy_semantic_review"]["pass_readiness_counts"] == {
        "blocked": 2,
        "candidate": 0,
    }
    assert payload["content_backlog"]["legacy_semantic_review"]["pass_blocker_counts"][
        "initial_semantic_review_not_recorded"
    ] == 2
    assert payload["content_backlog"]["legacy_semantic_review"]["worklist_next_actions"] == [
        "worklist_item:legacy-topic-0",
        "worklist_item:legacy-topic-1",
    ]
    assert payload["content_backlog"]["legacy_semantic_review"]["top_work_items"][0]["topic"] == (
        "legacy-topic-0"
    )
    assert payload["content_backlog"]["legacy_semantic_review"]["top_work_items"][0]["review_status"] == "pending"
    assert payload["content_backlog"]["legacy_semantic_review"]["top_work_items"][0][
        "satisfied_review_actions"
    ] == []
    assert payload["content_backlog"]["legacy_semantic_review"]["top_work_items"][0][
        "followup_review_actions"
    ] == []
    assert payload["content_backlog"]["legacy_semantic_review"]["top_work_items"][0]["can_update_claim_trust"] is False
    assert payload["content_backlog"]["legacy_semantic_review"]["pending_count"] == 2
    assert payload["content_backlog"]["legacy_semantic_review"]["passed_count"] == 0
    assert payload["content_backlog"]["legacy_semantic_review"]["semantic_lossless_proven"] is False
    assert f"source_reconstruction:{claim.claim_id}:complete" in payload["evidence_refs"]
    assert "semantic_review:legacy-v5-lossless-test:pending=2" in payload["backlog_refs"]
    assert require_valid_public_surface("final_engineering_readiness_audit", payload) == payload


def test_final_readiness_audit_reports_missing_legacy_review_without_migration_run(tmp_path):
    from brain.v5.final_readiness import audit_final_engineering_readiness
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    payload = audit_final_engineering_readiness(ws)

    assert payload["completion_status"] == "kernel_ready_content_backlog"
    assert payload["content_backlog"]["legacy_semantic_review"]["status"] == "missing_migration_run"
    assert "legacy_semantic_review_queue_unavailable" in payload["blocking_gaps"]
    assert payload["content_backlog"]["legacy_semantic_review"]["semantic_lossless_proven"] is False


def test_final_readiness_audit_treats_inconclusive_legacy_review_as_blocking_backlog(tmp_path):
    from brain.v5.final_readiness import audit_final_engineering_readiness
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    run = _write_migration_run(ws, topic_count=1)
    record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="legacy-topic-0",
        status="inconclusive",
        summary="Semantic review still needs source reconstruction before passing.",
        reviewed_legacy_refs=["legacy-topic:legacy-topic-0/state.md"],
        remaining_actions=["complete_source_reconstruction_components"],
    )

    payload = audit_final_engineering_readiness(ws, migration_dir=run)

    assert payload["content_backlog_status"] == "legacy_semantic_review_backlog"
    assert payload["content_backlog"]["legacy_semantic_review"]["needs_revision_count"] == 0
    assert payload["content_backlog"]["legacy_semantic_review"]["inconclusive_count"] == 1
    assert "legacy_semantic_review_backlog" in payload["blocking_gaps"]
    assert payload["content_backlog"]["legacy_semantic_review"]["semantic_lossless_proven"] is False


def test_final_readiness_audit_reports_source_reconstruction_content_backlog(tmp_path):
    from brain.v5.final_readiness import audit_final_engineering_readiness
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source reconstruction missing",
    )
    run = _write_migration_run(ws, topic_count=0)

    payload = audit_final_engineering_readiness(ws, migration_dir=run)

    assert payload["completion_status"] == "kernel_ready_content_backlog"
    assert payload["content_backlog_status"] == "source_reconstruction_backlog"
    assert payload["blocking_gaps"] == []
    source_backlog = payload["content_backlog"]["source_reconstruction"]
    assert source_backlog["surface"] == "source_reconstruction_manifest"
    assert source_backlog["status"] == "reconstruction_backlog"
    assert source_backlog["active_claim_count"] == 1
    assert source_backlog["complete_claim_count"] == 0
    assert source_backlog["incomplete_claim_count"] == 1
    assert source_backlog["next_actions"] == [f"source_reconstruction:{claim.claim_id}"]
    assert source_backlog["review_surface"] == "source_reconstruction_review_manifest"
    assert source_backlog["review_progress"] == {
        "passed": 0,
        "needs_revision": 0,
        "inconclusive": 0,
        "pending": 1,
    }
    assert source_backlog["review_next_actions"] == [f"source_reconstruction_review:{claim.claim_id}"]
    assert source_backlog["top_incomplete_claims"] == [
        {
            "topic_id": "fqhe",
            "claim_id": claim.claim_id,
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
                "source_reconstruction_review",
                "complete_source_reconstruction",
            ],
            "review_packet_cli": f"aitp-v5 source reconstruction-review --claim {claim.claim_id}",
            "can_update_claim_trust": False,
        }
    ]
    assert source_backlog["can_update_claim_trust"] is False
    assert f"source_reconstruction:incomplete=1" in payload["backlog_refs"]
    assert f"source_reconstruction_review:pending=1" in payload["backlog_refs"]
    assert require_valid_public_surface("final_engineering_readiness_audit", payload) == payload


def test_final_readiness_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_final_engineering_readiness
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    _write_migration_run(ws, topic_count=1)

    assert main(["--base", str(tmp_path), "adapter", "final-readiness"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_final_engineering_readiness(str(tmp_path))

    assert cli_payload["ok"] is True
    assert cli_payload["kind"] == "final_engineering_readiness_audit"
    assert mcp_payload["kind"] == "final_engineering_readiness_audit"
    assert runtime_entrypoints()["final_engineering_readiness_audit"] == {
        "cli": "aitp-v5 adapter final-readiness",
        "mcp": "aitp_v5_audit_final_engineering_readiness",
        "surface": "final_engineering_readiness_audit",
    }


def test_final_readiness_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    _write_migration_run(ws, topic_count=1)

    assert main(["--base", str(tmp_path), "adapter", "final-readiness", "--compact"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    assert cli_payload["kind"] == "final_engineering_readiness_progress"
    assert cli_payload["source_surface"] == "final_engineering_readiness_audit"
    assert cli_payload["completion_status"] == "kernel_ready_content_backlog"
    assert "legacy_semantic_review_backlog" in cli_payload["blocking_gaps"]
    assert cli_payload["legacy_semantic_review"]["semantic_lossless_proven"] is False
    assert cli_payload["can_update_claim_trust"] is False
    assert "kernel_capabilities" not in cli_payload
