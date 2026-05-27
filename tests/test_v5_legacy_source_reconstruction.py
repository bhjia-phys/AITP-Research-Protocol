from __future__ import annotations

import json


def _write_migration_run(ws, *, topic="canonical-topic", claim_id="claim-canonical"):
    run = ws.root / "migrations" / "legacy-v5-lossless-source-test"
    run.mkdir(parents=True)
    summary = {
        "kind": "legacy_v5_lossless_migration_report",
        "run_id": "legacy-v5-lossless-source-test",
        "workspace": str(ws.base),
        "legacy_root": str(ws.base / "research" / "aitp-topics"),
        "v5_root": str(ws.root),
        "output_dir": str(run),
        "totals": {
            "topic_count": 1,
            "legacy_file_count": 2,
            "post_legacy_file_count": 2,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "structured_file_count": 2,
            "archive_reference_count": 0,
            "accounted_file_count": 2,
            "topics_with_errors": 0,
            "missing_archive_record_files": 0,
            "summary_inputs_trusted": False,
        },
        "topics": [
            {
                "topic": topic,
                "status": "ok",
                "file_count": 2,
                "audit_mapped_file_count": 2,
                "structured_file_count": 2,
                "archive_reference_count": 0,
                "accounted_file_count": 2,
                "missing_expected_paths": [],
                "can_write_v5_records": True,
                "active_claim_id": claim_id,
                "written_records": {
                    "topics": 1,
                    "claims": 1,
                    "evidence": 0,
                    "reference_locations": 0,
                    "sensemaking_reports": 0,
                    "trace_events": 0,
                    "memory_entries": 0,
                },
                "preserved_source_refs": 0,
                "summary_inputs_trusted": False,
            }
        ],
    }
    verification = {
        "kind": "legacy_v5_lossless_migration_verification",
        "run_id": "legacy-v5-lossless-source-test",
        "file_accounting_ok": True,
        "manifest_check": {"pre_count": 2, "post_count": 2, "missing": 0, "extra": 0, "changed": 0},
        "archive_reference_check": {
            "archive_records_checked": 0,
            "archive_records_expected": 0,
            "registry_archive_reference_count": 0,
            "problem_count": 0,
            "problems": [],
        },
        "markdown_readability_check": {
            "markdown_files_checked": 2,
            "problem_count": 0,
            "problems": [],
        },
        "brief_check": [],
        "all_checks_ok": True,
    }
    (run / "migration_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run / "verification_report.json").write_text(json.dumps(verification), encoding="utf-8")
    return run


def _seed_reviewed_legacy_topic(
    tmp_path,
    *,
    summary="Claim statement was reviewed; source reconstruction still needs a typed reconstruction path.",
    remaining_actions=None,
):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path / "v5")
    create_topic(ws, "canonical-topic", context_id="legacy-context", title="Canonical")
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Finite-size counting identifies the edge sector.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy semantic review required.",
        ),
    )
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    candidate = legacy_topic / "L3" / "candidates" / "candidate-counting.md"
    derivation = legacy_topic / "L3" / "derive" / "active_derivation.md"
    candidate.parent.mkdir(parents=True)
    derivation.parent.mkdir(parents=True)
    candidate.write_text("# Candidate\n\nFinite-size counting identifies the edge sector.\n", encoding="utf-8")
    derivation.write_text("# Derivation\n\n1. Define the sector. 2. Compare counting.\n", encoding="utf-8")
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary=summary,
        active_claim_id="claim-canonical",
        reviewed_legacy_refs=[f"legacy_candidate:{candidate}", f"legacy_l3_process:{derivation}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=remaining_actions or ["complete_source_reconstruction"],
    )
    return ws, run, review, candidate, derivation


def test_legacy_source_reconstruction_plan_uses_reviewed_l3_refs(tmp_path):
    from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_plan
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, run, review, candidate, derivation = _seed_reviewed_legacy_topic(tmp_path)

    plan = build_legacy_source_reconstruction_plan(ws, migration_dir=run, topic="canonical-topic")

    assert require_valid_public_surface("legacy_source_reconstruction_plan", plan) == plan
    assert plan["repair_status"] == "proposed_repairs"
    assert plan["can_update_kernel_state"] is False
    assert plan["can_update_claim_trust"] is False
    assert plan["latest_semantic_review"]["review_id"] == review.review_id
    assert plan["proposed_repairs"] == [
        {
            "repair_type": "reconstruction_path_evidence_backfill",
            "target_ref": "claim-canonical",
            "current_missing_component": "reconstruction_path",
            "proposed_evidence_type": "source_reconstruction",
            "proposed_status": "supports",
            "proposed_supports_outputs": ["reconstruction_path"],
            "source_refs": [f"legacy_candidate:{candidate}", f"legacy_l3_process:{derivation}"],
            "basis_refs": [f"legacy_candidate:{candidate}", f"legacy_l3_process:{derivation}", review.review_id],
            "mutation_authority": "typed_review_and_apply_separately",
        }
    ]


def test_legacy_source_reconstruction_plan_accepts_review_action_phrase(tmp_path):
    from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_plan

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(
        tmp_path,
        summary="Natural-language review action asks for reconstruction-path completion.",
        remaining_actions=[
            "Complete definitions, assumptions_or_scope, dependency_graph, reconstruction_path, and failure_conditions before promotion."
        ],
    )

    plan = build_legacy_source_reconstruction_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["repair_status"] == "proposed_repairs"
    assert plan["latest_semantic_review"]["review_id"] == review.review_id
    assert plan["proposed_repairs"][0]["repair_type"] == "reconstruction_path_evidence_backfill"


def test_legacy_source_reconstruction_manifest_batches_backlog(tmp_path):
    from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_manifest
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=run)

    assert require_valid_public_surface("legacy_source_reconstruction_manifest", manifest) == manifest
    assert manifest["kind"] == "legacy_source_reconstruction_manifest"
    assert manifest["work_item_count"] == 1
    assert manifest["repair_status_counts"] == {
        "awaiting_needs_revision_review": 0,
        "no_repair_candidates": 0,
        "proposed_repairs": 1,
    }
    assert manifest["proposed_repair_count"] == 1
    assert manifest["missing_component_counts"]["reconstruction_path"] == 1
    assert manifest["required_action_counts"] == {
        "apply_selected_source_reconstruction_repair_with_latest_review_id": 1,
        "inspect_legacy_refs_for_source_reconstruction_components": 1,
        "record_source_reconstruction_review_result": 1,
        "review_proposed_source_reconstruction_repair_before_apply": 1,
    }
    assert manifest["semantic_lossless_proven"] is False
    assert manifest["orientation_only"] is True
    assert manifest["can_update_kernel_state"] is False
    assert manifest["can_update_claim_trust"] is False
    item = manifest["items"][0]
    assert item["topic"] == "canonical-topic"
    assert item["active_claim_id"] == "claim-canonical"
    assert item["latest_review_id"] == review.review_id
    assert item["source_reconstruction_status"] == "incomplete"
    assert "reconstruction_path" in item["missing_components"]
    assert item["repair_status"] == "proposed_repairs"
    assert item["proposed_repair_count"] == 1
    assert item["proposed_repair_types"] == ["reconstruction_path_evidence_backfill"]
    assert item["review_packet_cli"] == (
        f"aitp-v5 --base {ws.base} legacy source-reconstruction-review "
        f"--migration-dir {run} --topic canonical-topic"
    )
    assert item["apply_cli"] == (
        f"aitp-v5 --base {ws.base} legacy source-reconstruction-apply "
        f"--migration-dir {run} --topic canonical-topic "
        "--repair-type reconstruction_path_evidence_backfill "
        f"--review-id {review.review_id}"
    )
    assert item["can_update_claim_trust"] is False


def test_legacy_source_reconstruction_manifest_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-manifest",
        "--migration-dir",
        str(run),
        "--compact",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "legacy_source_reconstruction_manifest_progress"
    assert payload["source_surface"] == "legacy_source_reconstruction_manifest"
    assert payload["migration_dir"] == str(run)
    assert payload["run_id"] == "legacy-v5-lossless-source-test"
    assert payload["work_item_count"] == 1
    assert payload["proposed_repair_count"] == 1
    assert payload["repair_status_counts"]["proposed_repairs"] == 1
    assert payload["missing_component_counts"]["reconstruction_path"] == 1
    assert payload["required_action_counts"]["apply_selected_source_reconstruction_repair_with_latest_review_id"] == 1
    assert payload["next_action_count"] == 1
    assert payload["next_action_refs"] == ["legacy_source_reconstruction:canonical-topic"]
    assert payload["top_work_item_refs"] == ["legacy_source_reconstruction:canonical-topic"]
    assert payload["top_work_item_topics"] == ["canonical-topic"]
    assert payload["top_work_item_active_claim_ids"] == ["claim-canonical"]
    assert payload["top_work_item_latest_review_ids"] == [review.review_id]
    assert payload["top_work_item_repair_statuses"] == ["proposed_repairs"]
    assert payload["top_work_item_missing_components"] == [
        [
            "definitions",
            "assumptions_or_scope",
            "source_locations",
            "dependency_graph",
            "reconstruction_path",
            "failure_conditions",
        ]
    ]
    assert payload["top_work_item_required_actions"] == [
        [
            "inspect_legacy_refs_for_source_reconstruction_components",
            "record_source_reconstruction_review_result",
            "review_proposed_source_reconstruction_repair_before_apply",
            "apply_selected_source_reconstruction_repair_with_latest_review_id",
        ]
    ]
    assert payload["semantic_lossless_proven"] is False
    assert payload["semantic_review_required"] is True
    assert payload["truth_source"] == "typed_review_results_legacy_refs_and_source_reconstruction_audit"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False


def test_legacy_source_reconstruction_obsidian_view_writes_worklist(tmp_path):
    from brain.v5.legacy_source_reconstruction_obsidian import write_legacy_source_reconstruction_obsidian_view
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    bundle = write_legacy_source_reconstruction_obsidian_view(ws, migration_dir=run)

    assert require_valid_public_surface("legacy_source_reconstruction_obsidian_view_bundle", bundle) == bundle
    assert bundle["kind"] == "legacy_source_reconstruction_obsidian_view_bundle"
    assert bundle["migration_dir"] == str(run)
    assert bundle["work_item_count"] == 1
    assert bundle["proposed_repair_count"] == 1
    assert bundle["repair_status_counts"]["proposed_repairs"] == 1
    assert bundle["source_records"] == {
        "topics": ["canonical-topic"],
        "active_claim_ids": ["claim-canonical"],
        "latest_review_ids": [review.review_id],
    }
    assert bundle["semantic_lossless_proven"] is False
    assert bundle["orientation_only"] is True
    assert bundle["can_update_kernel_state"] is False
    assert bundle["can_update_claim_trust"] is False
    worklist = (tmp_path / "v5" / ".aitp" / "surfaces" / "legacy_source_reconstruction" / "Legacy Source Reconstruction Worklist.md").read_text(
        encoding="utf-8"
    )
    assert "# Legacy Source Reconstruction Worklist" in worklist
    assert "`canonical-topic`" in worklist
    assert "`proposed_repairs`" in worklist
    assert "reconstruction_path_evidence_backfill" in worklist
    assert "Use typed source reconstruction review records" in worklist
    assert "cannot update claim trust" in worklist


def test_legacy_source_reconstruction_obsidian_view_cli_compact_progress(tmp_path, capsys):
    from brain.v5.cli import main

    ws, run, _review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-obsidian-view",
        "--migration-dir",
        str(run),
        "--compact",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "legacy_source_reconstruction_obsidian_view_bundle_progress"
    assert payload["source_surface"] == "legacy_source_reconstruction_obsidian_view_bundle"
    assert payload["migration_dir"] == str(run)
    assert payload["work_item_count"] == 1
    assert payload["proposed_repair_count"] == 1
    assert payload["repair_status_counts"]["proposed_repairs"] == 1
    assert payload["missing_component_counts"]["reconstruction_path"] == 1
    assert payload["required_action_counts"]["apply_selected_source_reconstruction_repair_with_latest_review_id"] == 1
    assert payload["next_action_count"] == 1
    assert payload["view_file_count"] == 1
    assert payload["view_files"] == [
        str(ws.root / "surfaces" / "legacy_source_reconstruction" / "Legacy Source Reconstruction Worklist.md")
    ]
    assert payload["semantic_lossless_proven"] is False
    assert payload["semantic_review_required"] is True
    assert payload["truth_source"] is False
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False


def test_legacy_source_reconstruction_review_packet_carries_legacy_refs(tmp_path):
    from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_review_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, run, review, candidate, derivation = _seed_reviewed_legacy_topic(tmp_path)

    packet = build_legacy_source_reconstruction_review_packet(
        ws,
        migration_dir=run,
        topic="canonical-topic",
    )

    assert require_valid_public_surface("legacy_source_reconstruction_review_packet", packet) == packet
    assert packet["kind"] == "legacy_source_reconstruction_review_packet"
    assert packet["run_id"] == "legacy-v5-lossless-source-test"
    assert packet["topic"] == "canonical-topic"
    assert packet["active_claim_id"] == "claim-canonical"
    assert packet["can_update_kernel_state"] is False
    assert packet["can_update_claim_trust"] is False
    assert packet["semantic_lossless_proven"] is False
    assert packet["latest_semantic_review"]["review_id"] == review.review_id
    assert packet["source_reconstruction_review_packet"]["kind"] == "source_reconstruction_review_packet"
    assert packet["source_reconstruction_review_packet"]["claim_id"] == "claim-canonical"
    assert packet["legacy_refs"]["reviewed_legacy_refs"] == [
        f"legacy_candidate:{candidate}",
        f"legacy_l3_process:{derivation}",
    ]
    assert packet["legacy_refs"]["refs_by_prefix"]["legacy_candidate"] == [f"legacy_candidate:{candidate}"]
    assert packet["legacy_refs"]["refs_by_prefix"]["legacy_l3_process"] == [f"legacy_l3_process:{derivation}"]
    by_component = {
        item["component"]: item
        for item in packet["legacy_component_review_guidance"]
    }
    assert by_component["reconstruction_path"]["legacy_refs_to_inspect"] == [
        f"legacy_candidate:{candidate}",
        f"legacy_l3_process:{derivation}",
    ]
    assert by_component["reconstruction_path"]["record_result_cli"] == (
        "aitp-v5 source reconstruction-review-result --claim claim-canonical "
        "--status <passed|needs_revision|inconclusive> --reviewed-component reconstruction_path "
        "--basis-ref <legacy-ref-or-typed-record> --summary <source reconstruction review basis>"
    )


def test_legacy_source_reconstruction_apply_writes_reconstruction_path_evidence(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_source_reconstruction import apply_legacy_source_reconstruction_repair
    from brain.v5.legacy_source_reconstruction_models import LegacySourceReconstructionRepairRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.source_reconstruction import audit_source_reconstruction
    from brain.v5.store import list_records

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    payload = apply_legacy_source_reconstruction_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="reconstruction_path_evidence_backfill",
        review_id=review.review_id,
    )

    assert require_valid_public_surface("legacy_source_reconstruction_apply", payload) == payload
    assert payload["applied"] is True
    assert payload["evidence_id"]
    assert payload["can_update_kernel_state"] is True
    assert payload["can_update_claim_trust"] is False
    evidence = list_evidence_for_claim(ws, "claim-canonical")
    assert [record.evidence_id for record in evidence] == [payload["evidence_id"]]
    assert evidence[0].evidence_type == "source_reconstruction"
    assert evidence[0].supports_outputs == ["reconstruction_path"]
    repairs = list_records(
        ws.registry_dir("legacy_source_reconstruction_repairs"),
        LegacySourceReconstructionRepairRecord,
    )
    assert [repair.repair_id for repair in repairs] == [payload["repair_id"]]
    assert repairs[0].evidence_id == payload["evidence_id"]
    assert repairs[0].review_id == review.review_id
    assert repairs[0].applied is True
    assert repairs[0].can_update_claim_trust is False
    audit = audit_source_reconstruction(ws, claim_id="claim-canonical")
    assert "reconstruction_path" not in audit["missing_components"]


def test_legacy_source_reconstruction_apply_is_idempotent_after_existing_evidence(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_source_reconstruction import apply_legacy_source_reconstruction_repair
    from brain.v5.legacy_source_reconstruction_models import LegacySourceReconstructionRepairRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records

    ws, run, review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)
    first = apply_legacy_source_reconstruction_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="reconstruction_path_evidence_backfill",
        review_id=review.review_id,
    )

    second = apply_legacy_source_reconstruction_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="reconstruction_path_evidence_backfill",
        review_id=review.review_id,
    )

    assert require_valid_public_surface("legacy_source_reconstruction_apply", second) == second
    assert second["applied"] is True
    assert second["required_actions"] == []
    assert second["evidence_id"] == first["evidence_id"]
    assert second["repair_id"] == first["repair_id"]
    assert second["can_update_claim_trust"] is False
    evidence = [record for record in list_evidence_for_claim(ws, "claim-canonical") if record.evidence_type == "source_reconstruction"]
    assert [record.evidence_id for record in evidence] == [first["evidence_id"]]
    repairs = list_records(
        ws.registry_dir("legacy_source_reconstruction_repairs"),
        LegacySourceReconstructionRepairRecord,
    )
    assert [repair.repair_id for repair in repairs] == [first["repair_id"]]
    assert repairs[0].applied is True
    assert repairs[0].evidence_id == first["evidence_id"]


def test_legacy_source_reconstruction_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_build_legacy_source_reconstruction_manifest,
        aitp_v5_build_legacy_source_reconstruction_plan,
        aitp_v5_build_legacy_source_reconstruction_review_packet,
        aitp_v5_write_legacy_source_reconstruction_obsidian_view,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, run, _review, _candidate, _derivation = _seed_reviewed_legacy_topic(tmp_path)

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-plan",
        "--migration-dir",
        str(run),
        "--topic",
        "canonical-topic",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_source_reconstruction_plan(
        str(ws.base),
        migration_dir=str(run),
        topic="canonical-topic",
    )

    assert cli_payload["kind"] == "legacy_source_reconstruction_plan"
    assert mcp_payload["kind"] == "legacy_source_reconstruction_plan"
    assert runtime_entrypoints()["legacy_source_reconstruction_plan"] == {
        "cli": "aitp-v5 legacy source-reconstruction-plan <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_plan",
        "surface": "legacy_source_reconstruction_plan",
    }

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-manifest",
        "--migration-dir",
        str(run),
    ]) == 0
    cli_manifest_payload = json.loads(capsys.readouterr().out)
    mcp_manifest_payload = aitp_v5_build_legacy_source_reconstruction_manifest(
        str(ws.base),
        migration_dir=str(run),
    )

    assert cli_manifest_payload["kind"] == "legacy_source_reconstruction_manifest"
    assert mcp_manifest_payload["kind"] == "legacy_source_reconstruction_manifest"
    assert runtime_entrypoints()["legacy_source_reconstruction_manifest"] == {
        "cli": "aitp-v5 legacy source-reconstruction-manifest <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_manifest",
        "surface": "legacy_source_reconstruction_manifest",
    }

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-obsidian-view",
        "--migration-dir",
        str(run),
    ]) == 0
    cli_obsidian_payload = json.loads(capsys.readouterr().out)
    mcp_obsidian_payload = aitp_v5_write_legacy_source_reconstruction_obsidian_view(
        str(ws.base),
        migration_dir=str(run),
    )

    assert cli_obsidian_payload["kind"] == "legacy_source_reconstruction_obsidian_view_bundle"
    assert mcp_obsidian_payload["kind"] == "legacy_source_reconstruction_obsidian_view_bundle"
    assert runtime_entrypoints()["legacy_source_reconstruction_obsidian_view"] == {
        "cli": "aitp-v5 legacy source-reconstruction-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_source_reconstruction_obsidian_view",
        "surface": "legacy_source_reconstruction_obsidian_view_bundle",
    }

    assert main([
        "--base",
        str(ws.base),
        "legacy",
        "source-reconstruction-review",
        "--migration-dir",
        str(run),
        "--topic",
        "canonical-topic",
    ]) == 0
    cli_review_payload = json.loads(capsys.readouterr().out)
    mcp_review_payload = aitp_v5_build_legacy_source_reconstruction_review_packet(
        str(ws.base),
        migration_dir=str(run),
        topic="canonical-topic",
    )

    assert cli_review_payload["kind"] == "legacy_source_reconstruction_review_packet"
    assert mcp_review_payload["kind"] == "legacy_source_reconstruction_review_packet"
    assert runtime_entrypoints()["legacy_source_reconstruction_review_packet"] == {
        "cli": "aitp-v5 legacy source-reconstruction-review <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_review_packet",
        "surface": "legacy_source_reconstruction_review_packet",
    }
