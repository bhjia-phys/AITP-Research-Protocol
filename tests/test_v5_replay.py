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
    assert f"`{gw_claim.claim_id}`" in body
    assert "Source review: `pending`" in body
    assert "orientation only" in body


def test_workspace_replay_packet_can_include_legacy_semantic_review_backlog(tmp_path):
    from dataclasses import asdict

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
        remaining_actions=["review_legacy_l2_memory_entry_candidates"],
    )

    packet = write_workspace_replay_packet(ws, migration_dir=migration)
    payload = asdict(packet)

    assert require_valid_public_surface("workspace_replay_packet", {"ok": True, **payload})["ok"] is True
    legacy = packet.workspace_backlog_summary["legacy_semantic_review"]
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
    _, body = read_md(packet.files["replay_packet"])
    assert "Legacy Semantic Review Backlog" in body
    assert "semantic lossless proven: False" in body
    assert "legacy-l2" in body


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
    assert mcp_payload["workspace_backlog_summary"]["legacy_semantic_review"]["migration_dir"] == str(migration)
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["can_update_kernel_state"] is False
