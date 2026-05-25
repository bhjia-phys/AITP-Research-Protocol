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
    assert payload["kernel_capabilities"]["host_integration"]["priority_hosts"] == ["codex", "claude_code", "kimi_code"]
    assert payload["kernel_capabilities"]["host_integration"]["deferred_hosts"] == ["opencode"]
    assert payload["content_backlog"]["legacy_semantic_review"]["review_item_count"] == 2
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
