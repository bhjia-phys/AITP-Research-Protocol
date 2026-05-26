from __future__ import annotations


def _write_legacy_topic(root):
    from brain.v5.markdown import write_md

    topic = root / "legacy-fqhe"
    (topic / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (topic / "L3" / "candidates").mkdir(parents=True)
    write_md(
        topic / "state.md",
        {
            "title": "Legacy FQHE",
            "question": "How does finite-size counting identify the edge sector?",
            "stage": "L3",
            "lane": "toy_numeric",
        },
        "# Legacy FQHE\n",
    )
    write_md(
        topic / "L0" / "sources" / "paper-a" / "source.md",
        {"title": "Counting paper", "source_url": "https://example.test/paper"},
        "# Counting paper\n",
    )
    write_md(
        topic / "L3" / "candidates" / "candidate-counting.md",
        {
            "candidate_id": "candidate-counting",
            "claim": "Finite-size counting identifies the FQHE edge sector.",
            "evidence": "Reproduces a small-system counting table.",
        },
        "# Candidate\n",
    )
    return topic


def _write_migration_run(ws):
    import json

    run = ws.root / "migrations" / "legacy-v5-lossless-test"
    run.mkdir(parents=True)
    summary = {
        "kind": "legacy_v5_lossless_migration_report",
        "run_id": "legacy-v5-lossless-test",
        "workspace": str(ws.base),
        "legacy_root": str(ws.base / "research" / "aitp-topics"),
        "v5_root": str(ws.root),
        "output_dir": str(run),
        "totals": {
            "topic_count": 2,
            "legacy_file_count": 4,
            "post_legacy_file_count": 4,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "structured_file_count": 3,
            "archive_reference_count": 1,
            "accounted_file_count": 4,
            "topics_with_errors": 0,
            "missing_archive_record_files": 0,
            "summary_inputs_trusted": False,
        },
        "topics": [
            {
                "topic": "canonical-topic",
                "status": "ok",
                "file_count": 3,
                "audit_mapped_file_count": 2,
                "structured_file_count": 2,
                "archive_reference_count": 1,
                "accounted_file_count": 3,
                "missing_expected_paths": [],
                "can_write_v5_records": True,
                "active_claim_id": "claim-canonical",
                "written_records": {
                    "topics": 1,
                    "claims": 1,
                    "evidence": 2,
                    "reference_locations": 1,
                    "sensemaking_reports": 1,
                    "trace_events": 0,
                    "memory_entries": 0,
                },
                "preserved_source_refs": 1,
                "summary_inputs_trusted": False,
            },
            {
                "topic": "legacy-l2",
                "status": "ok",
                "file_count": 1,
                "audit_mapped_file_count": 1,
                "structured_file_count": 1,
                "archive_reference_count": 0,
                "accounted_file_count": 1,
                "missing_expected_paths": ["state.md"],
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
            },
        ],
    }
    verification = {
        "kind": "legacy_v5_lossless_migration_verification",
        "run_id": "legacy-v5-lossless-test",
        "file_accounting_ok": True,
        "manifest_check": {"pre_count": 4, "post_count": 4, "missing": 0, "extra": 0, "changed": 0},
        "archive_reference_check": {
            "archive_records_checked": 1,
            "archive_records_expected": 1,
            "registry_archive_reference_count": 1,
            "problem_count": 0,
            "problems": [],
        },
        "markdown_readability_check": {
            "markdown_files_checked": 4,
            "problem_count": 0,
            "problems": [],
        },
        "brief_check": [],
        "all_checks_ok": True,
    }
    (run / "migration_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run / "verification_report.json").write_text(json.dumps(verification), encoding="utf-8")
    return run


def test_legacy_bridge_reads_legacy_artifacts_without_rewriting(tmp_path):
    from brain.v5.legacy_bridge import scan_legacy_topic

    legacy_topic = _write_legacy_topic(tmp_path)
    before = (legacy_topic / "state.md").read_text(encoding="utf-8")

    summary = scan_legacy_topic(legacy_topic)

    after = (legacy_topic / "state.md").read_text(encoding="utf-8")
    assert before == after
    assert summary.topic_slug == "legacy-fqhe"
    assert summary.title == "Legacy FQHE"
    assert summary.candidate_claims == ["Finite-size counting identifies the FQHE edge sector."]
    assert summary.source_paths == [str(legacy_topic / "L0" / "sources" / "paper-a" / "source.md")]


def test_legacy_topic_can_produce_v5_execution_brief(tmp_path):
    from brain.v5.contracts import validate_execution_brief
    from brain.v5.legacy_bridge import build_v5_brief_from_legacy

    legacy_topic = _write_legacy_topic(tmp_path / "legacy")

    brief = build_v5_brief_from_legacy(
        tmp_path / "v5",
        legacy_topic,
        context_id="legacy-context",
        session_id="s1",
    )

    assert validate_execution_brief(brief).ok is True
    assert brief["session"]["topic_id"] == "legacy-fqhe"
    assert brief["current_focus"]["claim_statement"] == "Finite-size counting identifies the FQHE edge sector."


def test_legacy_bridge_preserves_source_paths_as_evidence_refs(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import seed_v5_from_legacy
    from brain.v5.workspace import init_workspace

    legacy_topic = _write_legacy_topic(tmp_path / "legacy")
    ws = init_workspace(tmp_path / "v5")

    seed = seed_v5_from_legacy(ws, legacy_topic, context_id="legacy-context", session_id="s1")
    evidence = list_evidence_for_claim(ws, seed.active_claim_id)

    assert evidence
    assert evidence[0].source_refs == [f"legacy_source:{legacy_topic / 'L0' / 'sources' / 'paper-a' / 'source.md'}"]


def test_legacy_candidates_map_to_v5_claim_records(tmp_path):
    from brain.v5.legacy_bridge import seed_v5_from_legacy
    from brain.v5.workspace import get_claim, init_workspace

    legacy_topic = _write_legacy_topic(tmp_path / "legacy")
    ws = init_workspace(tmp_path / "v5")

    seed = seed_v5_from_legacy(ws, legacy_topic, context_id="legacy-context", session_id="s1")
    claim = get_claim(ws, seed.active_claim_id)

    assert claim.topic_id == "legacy-fqhe"
    assert claim.statement == "Finite-size counting identifies the FQHE edge sector."
    assert claim.evidence_profile == "toy_numeric"


def test_legacy_migration_extracts_research_question_from_state_body(tmp_path):
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.models import ClaimRecord, SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    topic = tmp_path / "legacy" / "body-question-topic"
    topic.mkdir(parents=True)
    question = (
        "What are the known solutions to Einstein's equations in asymptotically "
        "AdS spacetime?"
    )
    (topic / "state.md").write_text(
        "---\n"
        "title: Body Question Topic\n"
        "lane: formal_theory\n"
        "---\n"
        "# Body Question Topic\n\n"
        "## Research Question\n"
        f"{question}\n\n"
        "## Notes\n"
        "This state file stores the question in the body, as older topics did.\n",
        encoding="utf-8",
    )
    ws = init_workspace(tmp_path / "v5")

    migrate_legacy_topic_to_v5(ws, topic, context_id="legacy-context", session_id="s1")

    claims = list_records(ws.registry_dir("claims"), ClaimRecord)
    assert [claim.statement for claim in claims] == [question]
    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert any(question in report.summary for report in reports)


def test_legacy_topic_dry_run_reports_missing_and_mapped_sections(tmp_path):
    from pathlib import Path

    from brain.v5.legacy_bridge import audit_legacy_topic_migration

    topic = tmp_path / "old-topic"
    (topic / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (topic / "L1").mkdir()
    (topic / "state.md").write_text("---\ntitle: Old Topic\n---\n# State\n", encoding="utf-8")
    (topic / "L0" / "sources" / "paper-a" / "source.md").write_text("# Paper A\n", encoding="utf-8")
    (topic / "L1" / "question_contract.md").write_text("# Question\n", encoding="utf-8")

    audit = audit_legacy_topic_migration(topic)

    assert audit["kind"] == "legacy_topic_migration_audit"
    assert audit["can_write_v5_records"] is False
    assert "L1/source_basis.md" in audit["missing_expected_paths"]
    assert audit["mapped_paths"]["state.md"] == "topic/runtime metadata"
    assert audit["mapped_paths"]["L0/sources/paper-a/source.md"] == "reference_location/source evidence candidate"


def test_legacy_topic_dry_run_maps_candidates_and_reviews(tmp_path):
    from brain.v5.legacy_bridge import audit_legacy_topic_migration

    topic = tmp_path / "old-topic"
    (topic / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (topic / "L1").mkdir()
    (topic / "L3" / "candidates").mkdir(parents=True)
    (topic / "L4" / "reviews").mkdir(parents=True)
    (topic / "state.md").write_text("---\ntitle: Old Topic\n---\n# State\n", encoding="utf-8")
    (topic / "L0" / "sources" / "paper-a" / "source.md").write_text("# Paper A\n", encoding="utf-8")
    (topic / "L1" / "question_contract.md").write_text("# Question\n", encoding="utf-8")
    (topic / "L1" / "source_basis.md").write_text("# Sources\n", encoding="utf-8")
    (topic / "L1" / "convention_snapshot.md").write_text("# Conventions\n", encoding="utf-8")
    (topic / "L1" / "derivation_anchor_map.md").write_text("# Anchors\n", encoding="utf-8")
    (topic / "L1" / "contradiction_register.md").write_text("# Contradictions\n", encoding="utf-8")
    (topic / "L3" / "candidates" / "candidate-a.md").write_text("# Candidate A\n", encoding="utf-8")
    (topic / "L4" / "reviews" / "review-a.md").write_text("# Review A\n", encoding="utf-8")

    audit = audit_legacy_topic_migration(topic)

    assert audit["can_write_v5_records"] is True
    assert audit["mapped_paths"]["L3/candidates/candidate-a.md"] == "claim/candidate seed"
    assert audit["mapped_paths"]["L4/reviews/review-a.md"] == "validation evidence candidate"
    assert audit["mapped_paths"]["L1/convention_snapshot.md"] == "understanding/conventions candidate"
    assert audit["mapped_paths"]["L1/derivation_anchor_map.md"] == "understanding/derivation anchor candidate"
    assert audit["mapped_paths"]["L1/contradiction_register.md"] == "understanding/contradiction candidate"
    assert audit["summary_inputs_trusted"] is False


def test_explicit_legacy_migration_writes_v5_records_without_rewriting_legacy(tmp_path):
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.references import list_reference_locations_for_claim
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    before = (legacy / "state.md").read_text(encoding="utf-8")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    assert (legacy / "state.md").read_text(encoding="utf-8") == before
    assert result["kind"] == "legacy_topic_migration_result"
    assert result["summary_inputs_trusted"] is False
    assert result["written_records"]["claims"] == [result["active_claim_id"]]
    assert result["written_records"]["evidence"]
    assert result["written_records"]["reference_locations"]
    locations = list_reference_locations_for_claim(ws, result["active_claim_id"])
    assert [location.location_id for location in locations] == result["written_records"]["reference_locations"]


def test_legacy_migration_preserves_source_metadata_as_reference_locations(tmp_path):
    from brain.v5.legacy_bridge import audit_legacy_topic_migration, migrate_legacy_topic_to_v5
    from brain.v5.references import list_reference_locations_for_claim
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    source = legacy / "L0" / "sources" / "paper-a" / "source.md"
    source.write_text(
        "---\n"
        "title: Counting paper\n"
        "source_url: https://example.test/paper\n"
        "pdf_path: file:///papers/fqhe/counting.pdf\n"
        "doi: 10.1234/fqhe.counting\n"
        "arxiv_id: 2201.12345\n"
        "note_path: notes/FQHE Counting.md\n"
        "---\n"
        "# Counting paper\n",
        encoding="utf-8",
    )
    ws = init_workspace(tmp_path / "v5")

    audit = audit_legacy_topic_migration(legacy)
    assert audit["mapped_paths"]["L0/sources/paper-a/source.md#source_url"] == (
        "reference_location/source_url metadata anchor"
    )
    assert audit["mapped_paths"]["L0/sources/paper-a/source.md#doi"] == (
        "reference_location/doi metadata anchor"
    )

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    locations = list_reference_locations_for_claim(ws, result["active_claim_id"])
    by_type = {location.location_type: location for location in locations}
    assert {
        "legacy_source_file",
        "source_url",
        "paper_pdf",
        "doi",
        "arxiv",
        "note_path",
    } <= set(by_type)
    assert by_type["source_url"].uri == "https://example.test/paper"
    assert by_type["paper_pdf"].uri == "file:///papers/fqhe/counting.pdf"
    assert by_type["doi"].uri == "doi:10.1234/fqhe.counting"
    assert by_type["arxiv"].uri == "https://arxiv.org/abs/2201.12345"
    assert by_type["note_path"].uri == "legacy-note:notes/FQHE%20Counting.md"
    assert all(location.orientation_only is True for location in locations)
    assert all(location.source_ref == f"legacy_source:{source}" for location in locations)
    assert set(result["written_records"]["reference_locations"]) == {
        location.location_id for location in locations
    }


def test_legacy_migration_result_is_public_surface_valid(tmp_path):
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    assert require_valid_public_surface("legacy_migration_result", result) == result


def test_legacy_migration_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_migrate_legacy_topic_to_v5
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    legacy = _write_legacy_topic(tmp_path / "legacy")
    cli_base = tmp_path / "v5-cli"

    assert main([
        "--base", str(cli_base), "legacy", "migrate", str(legacy),
        "--context", "legacy-context", "--session", "s1",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["ok"] is True
    assert cli_payload["kind"] == "legacy_topic_migration_result"
    assert cli_payload["written_records"]["reference_locations"]

    mcp_payload = aitp_v5_migrate_legacy_topic_to_v5(
        str(tmp_path / "v5-mcp"),
        topic_dir=str(legacy),
        context_id="legacy-context",
        session_id="s1",
    )
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_topic_migration_result"
    assert runtime_entrypoints()["migrate_legacy_topic"]["surface"] == "legacy_migration_result"


def test_legacy_migration_coverage_audit_reports_accounting_without_semantic_overclaim(tmp_path):
    from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)

    audit = audit_legacy_migration_coverage(ws, migration_dir=run)

    assert audit["kind"] == "legacy_migration_coverage_audit"
    assert audit["coverage_status"] == "accounted_needs_review"
    assert audit["file_preservation"]["ok"] is True
    assert audit["archive_reference_coverage"]["ok"] is True
    assert audit["markdown_readability"]["ok"] is True
    assert audit["gap_topic_count"] == 0
    assert audit["semantic_lossless_proven"] is False
    assert audit["semantic_review_required"] is True
    assert audit["can_update_claim_trust"] is False
    by_topic = {topic["topic"]: topic for topic in audit["topics"]}
    assert by_topic["canonical-topic"]["legacy_shape"] == "canonical_topic"
    assert by_topic["legacy-l2"]["legacy_shape"] == "noncanonical_seed"
    assert by_topic["legacy-l2"]["missing_expected_paths"] == ["state.md"]
    assert by_topic["legacy-l2"]["coverage_status"] == "accounted_needs_review"
    assert require_valid_public_surface("legacy_migration_coverage_audit", audit) == audit


def test_legacy_migration_coverage_audit_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_legacy_migration_coverage
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "migration-audit", "--migration-dir", str(run),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["ok"] is True
    assert cli_payload["kind"] == "legacy_migration_coverage_audit"
    assert cli_payload["coverage_status"] == "accounted_needs_review"

    mcp_payload = aitp_v5_audit_legacy_migration_coverage(str(base), migration_dir=str(run))
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_migration_coverage_audit"
    assert runtime_entrypoints()["legacy_migration_coverage_audit"]["surface"] == (
        "legacy_migration_coverage_audit"
    )


def test_legacy_semantic_review_queue_operationalizes_per_topic_review(tmp_path):
    from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    create_topic(ws, "canonical-topic", context_id="legacy-context", title="Canonical Topic")
    claim = ClaimRecord(
        claim_id="claim-canonical",
        topic_id="canonical-topic",
        statement="Migrated canonical claim.",
        evidence_profile="legacy_import",
        confidence_state="hypothesis",
        active_uncertainty="Semantic review required.",
    )
    write_record(ws.registry_dir("claims") / "claim-canonical.md", claim)

    queue = build_legacy_semantic_review_queue(ws, migration_dir=run)

    assert queue["kind"] == "legacy_semantic_review_queue"
    assert queue["queue_status"] == "ready_for_semantic_review"
    assert queue["semantic_lossless_proven"] is False
    assert queue["semantic_review_required"] is True
    assert queue["can_update_claim_trust"] is False
    assert queue["review_item_count"] == 2
    by_topic = {item["topic"]: item for item in queue["items"]}
    canonical = by_topic["canonical-topic"]
    assert canonical["semantic_review_required"] is True
    assert canonical["source_reconstruction"]["status"] == "incomplete"
    assert "complete_source_reconstruction" in canonical["recommended_actions"]
    assert "archive_only_records_require_sampling" in canonical["review_reasons"]
    assert by_topic["legacy-l2"]["review_priority"] == "critical"
    assert "source_reconstruction_missing_claim_record" in by_topic["legacy-l2"]["review_reasons"]
    assert "classify_noncanonical_seed_before_promotion" in by_topic["legacy-l2"]["recommended_actions"]
    assert require_valid_public_surface("legacy_semantic_review_queue", queue) == queue


def test_legacy_semantic_review_queue_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_semantic_review_queue
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "semantic-review-queue", "--migration-dir", str(run),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["ok"] is True
    assert cli_payload["kind"] == "legacy_semantic_review_queue"
    assert cli_payload["semantic_lossless_proven"] is False
    assert cli_payload["items"]

    mcp_payload = aitp_v5_build_legacy_semantic_review_queue(str(base), migration_dir=str(run))
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_semantic_review_queue"
    assert runtime_entrypoints()["legacy_semantic_review_queue"]["surface"] == (
        "legacy_semantic_review_queue"
    )


def test_legacy_semantic_review_packet_collects_review_basis_without_writing(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.legacy_semantic_review import build_legacy_semantic_review_packet
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    create_topic(ws, "canonical-topic", context_id="legacy-context", title="Canonical Topic")
    claim = ClaimRecord(
        claim_id="claim-canonical",
        topic_id="canonical-topic",
        statement="Migrated canonical claim.",
        evidence_profile="legacy_import",
        confidence_state="hypothesis",
        active_uncertainty="Semantic review required.",
    )
    write_record(ws.registry_dir("claims") / "claim-canonical.md", claim)
    evidence = record_evidence(
        ws,
        topic_id="canonical-topic",
        claim_id="claim-canonical",
        evidence_type="legacy_candidate",
        status="needs_review",
        summary="Migrated candidate evidence.",
        supports_outputs=["legacy_migration"],
        source_refs=["legacy_source:canonical-topic/state.md"],
    )
    before = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}

    packet = build_legacy_semantic_review_packet(ws, migration_dir=run, topic="canonical-topic")

    after = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}
    assert before == after
    assert packet["kind"] == "legacy_semantic_review_packet"
    assert packet["topic"] == "canonical-topic"
    assert packet["active_claim"]["claim_id"] == "claim-canonical"
    assert packet["active_claim"]["statement"] == "Migrated canonical claim."
    assert packet["queue_item"]["semantic_review_status"] == "pending"
    assert packet["typed_records"]["evidence"][0]["evidence_id"] == evidence.evidence_id
    assert "legacy_source:canonical-topic/state.md" in packet["legacy_review_refs"]
    assert packet["review_checklist"]
    assert packet["semantic_lossless_proven"] is False
    assert packet["orientation_only"] is True
    assert packet["can_update_kernel_state"] is False
    assert packet["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_review_packet", packet) == packet


def test_legacy_semantic_review_packet_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_semantic_review_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "semantic-review-packet",
        "--migration-dir", str(run), "--topic", "legacy-l2",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_semantic_review_packet(
        str(base),
        migration_dir=str(run),
        topic="legacy-l2",
    )

    assert cli_payload["kind"] == "legacy_semantic_review_packet"
    assert cli_payload["topic"] == "legacy-l2"
    assert mcp_payload["kind"] == "legacy_semantic_review_packet"
    assert runtime_entrypoints()["legacy_semantic_review_packet"] == {
        "cli": "aitp-v5 legacy semantic-review-packet <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_packet",
        "surface": "legacy_semantic_review_packet",
    }


def test_legacy_semantic_review_manifest_batches_packets_without_writing(tmp_path):
    from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    before = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=run)

    after = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}
    assert before == after
    assert manifest["kind"] == "legacy_semantic_review_manifest"
    assert manifest["run_id"] == "legacy-v5-lossless-test"
    assert manifest["topic_count"] == 2
    assert manifest["pending_count"] == 2
    assert manifest["passed_count"] == 0
    assert manifest["review_progress"] == {"passed": 0, "inconclusive": 0, "needs_revision": 0, "pending": 2}
    assert "legacy semantic-review-packet" in manifest["items"][0]["packet_cli"]
    assert "legacy semantic-review-result" in manifest["items"][0]["result_cli_template"]
    assert manifest["items"][0]["can_update_claim_trust"] is False
    assert manifest["next_actions"][0] == "review_packet:canonical-topic"
    assert manifest["semantic_lossless_proven"] is False
    assert manifest["orientation_only"] is True
    assert manifest["can_update_kernel_state"] is False
    assert require_valid_public_surface("legacy_semantic_review_manifest", manifest) == manifest


def test_legacy_semantic_review_manifest_summarizes_repair_candidates(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    candidate = legacy_topic / "L3" / "candidates" / "candidate.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("# Candidate\n\nA reconstruction sketch.\n", encoding="utf-8")
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Claim statement and reconstruction path need typed backfill.",
        reviewed_legacy_refs=[f"legacy_candidate:{candidate}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "Backfill the active claim statement from the legacy Research Question.",
            "Complete definitions, assumptions_or_scope, dependency_graph, reconstruction_path, and failure_conditions before promotion.",
        ],
    )
    before = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=run)

    after = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}
    canonical = next(item for item in manifest["items"] if item["topic"] == "canonical-topic")
    assert before == after
    assert canonical["repair_candidate_count"] == 1
    assert canonical["repair_candidates"] == [
        {
            "repair_surface": "legacy_source_reconstruction_apply",
            "repair_type": "reconstruction_path_evidence_backfill",
            "review_id": review.review_id,
            "apply_cli": (
                f"aitp-v5 --base {ws.base} legacy source-reconstruction-apply "
                f"--migration-dir {run} --topic canonical-topic "
                "--repair-type reconstruction_path_evidence_backfill"
                f" --review-id {review.review_id}"
            ),
            "can_update_claim_trust": False,
        }
    ]
    assert "repair_candidate:canonical-topic:reconstruction_path_evidence_backfill" in manifest["next_actions"]
    assert require_valid_public_surface("legacy_semantic_review_manifest", manifest) == manifest


def test_legacy_semantic_review_manifest_summarizes_failed_validation_repair_candidate(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
    from brain.v5.models import ClaimRecord, ValidationResultRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A validation-backed legacy claim.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    failed_result = ValidationResultRecord(
        result_id="validation-result-failed-toy",
        topic_id="canonical-topic",
        claim_id="claim-canonical",
        contract_id="validation-contract-canonical",
        tool_run_id="tool-run-failed-toy",
        status="failed",
        checked_outputs=["toy script reported 0/3 checks passed"],
        failure_modes_observed=["target projector weights zeroed the checked transition"],
        summary="The legacy toy validation failed and must be repaired before semantic pass.",
    )
    write_record(ws.registry_dir("validation_results") / f"{failed_result.result_id}.md", failed_result)
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The legacy validation surface failed and needs revision.",
        reviewed_typed_refs=["claim-canonical"],
        validation_result_ids=[failed_result.result_id],
        remaining_actions=["repair_or_replace_validate_wcrpa_toy_model_to_exercise_target_screening"],
    )

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=run)

    canonical = next(item for item in manifest["items"] if item["topic"] == "canonical-topic")
    assert canonical["repair_candidate_count"] == 1
    assert canonical["repair_candidates"] == [
        {
            "repair_surface": "legacy_semantic_repair_apply",
            "repair_type": "validation_result_revision",
            "review_id": review.review_id,
            "apply_cli": (
                f"aitp-v5 --base {ws.base} legacy semantic-repair-apply "
                f"--migration-dir {run} --topic canonical-topic "
                "--repair-type validation_result_revision"
                f" --review-id {review.review_id}"
            ),
            "can_update_claim_trust": False,
        }
    ]
    assert "repair_candidate:canonical-topic:validation_result_revision" in manifest["next_actions"]
    assert require_valid_public_surface("legacy_semantic_review_manifest", manifest) == manifest


def test_legacy_semantic_review_manifest_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_semantic_review_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "semantic-review-manifest",
        "--migration-dir", str(run),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_semantic_review_manifest(str(base), migration_dir=str(run))

    assert cli_payload["kind"] == "legacy_semantic_review_manifest"
    assert mcp_payload["kind"] == "legacy_semantic_review_manifest"
    assert runtime_entrypoints()["legacy_semantic_review_manifest"] == {
        "cli": "aitp-v5 legacy semantic-review-manifest <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_manifest",
        "surface": "legacy_semantic_review_manifest",
    }


def test_legacy_semantic_review_manifest_cli_compact_progress(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "semantic-review-manifest",
        "--migration-dir", str(run),
        "--compact",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    assert cli_payload["kind"] == "legacy_semantic_review_manifest_progress"
    assert cli_payload["source_surface"] == "legacy_semantic_review_manifest"
    assert cli_payload["review_item_count"] == 2
    assert cli_payload["review_progress"]["pending"] == 2
    assert cli_payload["semantic_lossless_proven"] is False
    assert cli_payload["can_update_claim_trust"] is False
    assert "items" not in cli_payload


def test_legacy_semantic_review_worklist_prioritizes_backlog_without_writing(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    state = legacy_topic / "state.md"
    state.parent.mkdir(parents=True)
    state.write_text("# Canonical\n\n## Research Question\nWhich claim needs restoration?\n", encoding="utf-8")
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Claim statement needs backfill and source reconstruction needs review.",
        reviewed_legacy_refs=[f"legacy_candidate:{state}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "Backfill the active claim statement from the legacy Research Question.",
            "Complete definitions, assumptions_or_scope, dependency_graph, reconstruction_path, and failure_conditions before promotion.",
        ],
    )
    before = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    after = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}
    assert before == after
    assert worklist["kind"] == "legacy_semantic_review_worklist"
    assert worklist["work_item_count"] == 2
    assert worklist["status_counts"] == {"needs_revision": 1, "inconclusive": 0, "pending": 1}
    assert worklist["pass_readiness_counts"] == {"blocked": 2, "candidate": 0}
    assert worklist["pass_blocker_counts"]["source_reconstruction_incomplete"] == 2
    assert worklist["pass_blocker_counts"]["latest_review_needs_revision"] == 1
    assert worklist["items"][0]["topic"] == "canonical-topic"
    assert worklist["items"][0]["review_status"] == "needs_revision"
    assert worklist["items"][0]["latest_review_id"] == review.review_id
    assert worklist["items"][0]["repair_candidate_count"] == 2
    assert worklist["items"][0]["review_focus"][:2] == [
        "apply_or_review_typed_repair_candidates",
        "complete_source_reconstruction_components",
    ]
    assert worklist["items"][0]["missing_source_components"] == [
        "definitions",
        "assumptions_or_scope",
        "source_locations",
        "dependency_graph",
        "reconstruction_path",
        "failure_conditions",
    ]
    assert worklist["items"][0]["can_update_claim_trust"] is False
    assert worklist["items"][1]["topic"] == "legacy-l2"
    assert worklist["next_actions"][0] == "worklist_item:canonical-topic"
    assert worklist["semantic_lossless_proven"] is False
    assert worklist["orientation_only"] is True
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_flags_satisfied_backfill_actions_for_followup(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    state = legacy_topic / "state.md"
    state.parent.mkdir(parents=True)
    question = "Which claim has already been restored from the legacy question?"
    state.write_text("# Canonical\n\n## Research Question\n" f"{question}\n", encoding="utf-8")
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement=question,
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The active claim statement was missing and needed the legacy research question.",
        reviewed_legacy_refs=[f"legacy_candidate:{state}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["Backfill the active claim statement from the legacy Research Question."],
    )

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=run)
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    manifest_item = next(item for item in manifest["items"] if item["topic"] == "canonical-topic")
    work_item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    assert manifest_item["latest_semantic_review"]["review_id"] == review.review_id
    assert manifest_item["repair_candidate_count"] == 0
    assert manifest_item["satisfied_review_actions"] == [
        "backfill_active_claim_statement_from_legacy_state_question"
    ]
    assert manifest_item["followup_review_actions"] == [
        "record_followup_semantic_review_result_for_satisfied_actions"
    ]
    assert work_item["satisfied_review_actions"] == manifest_item["satisfied_review_actions"]
    assert work_item["followup_review_actions"] == manifest_item["followup_review_actions"]
    assert work_item["followup_review_commands"] == [
        {
            "action": "record_followup_semantic_review_result_for_satisfied_actions",
            "latest_review_id": review.review_id,
            "satisfied_review_actions": [
                "backfill_active_claim_statement_from_legacy_state_question"
            ],
            "result_cli": (
                f"aitp-v5 --base {ws.base} legacy semantic-review-result "
                f"--migration-dir {run} --topic canonical-topic "
                "--status <passed|inconclusive> "
                f"--typed-ref claim-canonical --legacy-ref legacy_candidate:{state} "
                "--summary <reviewed satisfied actions; explain any remaining semantic gaps>"
            ),
            "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
            "can_update_claim_trust": False,
        }
    ]
    assert "record_followup_semantic_review_result_for_satisfied_actions" in work_item["review_focus"]
    assert work_item["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_review_manifest", manifest) == manifest
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_validation_remaining_actions(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord, ValidationContractRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A code-validation-backed claim.",
            evidence_profile="code_method",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    write_record(
        ws.registry_dir("validation_contracts") / "validation-contract-canonical.md",
        ValidationContractRecord(
            contract_id="validation-contract-canonical",
            topic_id="canonical-topic",
            claim_id="claim-canonical",
            required_checks=[
                "trace_compute_Wc_freq_q_accepts_chi_r_substitution",
                "validate_static_U_and_J_against_SrVO3_reference",
            ],
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="Remaining validation actions need typed tool runs and validation results.",
        reviewed_typed_refs=["claim-canonical", "validation-contract-canonical"],
        remaining_actions=[
            "trace_compute_Wc_freq_q_accepts_chi_r_substitution_on_actual_LibRPA_code",
            "validate_static_U_and_J_against_SrVO3_reference",
            "implement_or_import_executable_SrVO3_t2g_crpa_benchmark_with_Wannier_U_J_outputs",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    commands = {command["action"]: command for command in item["review_action_commands"]}
    trace_action = "trace_compute_Wc_freq_q_accepts_chi_r_substitution_on_actual_LibRPA_code"
    assert commands[trace_action] == {
        "action": trace_action,
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} tool run record "
            "--recipe <code-trace-recipe-id> --family code_trace --name trace_compute_Wc_freq_q "
            "--topic canonical-topic --claim claim-canonical "
            "--outputs-json <trace-result-json> --source-ref <LibRPA-code-ref>"
        ),
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    srvo3 = commands["validate_static_U_and_J_against_SrVO3_reference"]
    assert srvo3["cli"] == (
        f"aitp-v5 --base {ws.base} validation result record "
        "--topic canonical-topic --claim claim-canonical --contract validation-contract-canonical "
        "--tool-run <srvo3-validation-tool-run-id> --status <partial|passed|failed> "
        "--checked-output validation_result --summary <SrVO3 U/J benchmark result>"
    )
    assert srvo3["surface"] == "validation_result_record"
    assert srvo3["can_update_claim_trust"] is False
    executable_srvo3 = commands[
        "implement_or_import_executable_SrVO3_t2g_crpa_benchmark_with_Wannier_U_J_outputs"
    ]
    assert executable_srvo3["cli"] == (
        f"aitp-v5 --base {ws.base} validation result record "
        "--topic canonical-topic --claim claim-canonical --contract validation-contract-canonical "
        "--tool-run <srvo3-crpa-benchmark-tool-run-id> --status <partial|passed|failed|inconclusive> "
        "--checked-output validation_result "
        "--summary <executable SrVO3 t2g cRPA benchmark with Wannier U/J outputs>"
    )
    assert executable_srvo3["surface"] == "validation_result_record"
    assert executable_srvo3["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_qsgw_ac_remaining_actions(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord, ValidationContractRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Padé analytic continuation can amplify QSGW molecule errors.",
            evidence_profile="code_method",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review requires code readback and molecular regression evidence.",
        ),
    )
    write_record(
        ws.registry_dir("validation_contracts") / "validation-contract-qsgw-ac.md",
        ValidationContractRecord(
            contract_id="validation-contract-qsgw-ac",
            topic_id="canonical-topic",
            claim_id="claim-canonical",
            required_checks=[
                "readback_librpa_task_qsgw_ac_call_site_and_truncation_fallback_logic_from_actual_code",
                "readback_librpa_analycont_thiele_pade_division_or_pole_instability_points_from_actual_code",
                "compare_nfreq_and_n_params_anacon_sensitivity_on_molecular_regression_cases",
                "compare_pade_mitigation_against_full_frequency_or_contour_deformation_reference",
            ],
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="QSGW AC review needs code readback and molecule regression validation.",
        reviewed_typed_refs=["claim-canonical", "validation-contract-qsgw-ac"],
        remaining_actions=[
            "readback_librpa_task_qsgw_ac_call_site_and_truncation_fallback_logic_from_actual_code_or_preserved_originals",
            "readback_librpa_analycont_thiele_pade_division_or_pole_instability_points_from_actual_code_or_preserved_originals",
            "resolve_n_params_anacon_input_parsing_before_molecular_sensitivity_sweep",
            "provide_or_patch_n_params_anacon_parameter_injection_before_n_params_sensitivity_sweep",
            "compare_nfreq_and_n_params_anacon_sensitivity_on_molecular_regression_cases",
            "compare_pade_mitigation_against_full_frequency_or_contour_deformation_reference",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    commands = {command["action"]: command for command in item["review_action_commands"]}
    callsite = "readback_librpa_task_qsgw_ac_call_site_and_truncation_fallback_logic_from_actual_code_or_preserved_originals"
    assert commands[callsite] == {
        "action": callsite,
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} tool run record "
            "--recipe <code-trace-recipe-id> --family code_trace --name qsgw_ac_callsite_readback "
            "--topic canonical-topic --claim claim-canonical "
            "--outputs-json <code-readback-json> --source-ref <LibRPA-code-ref>"
        ),
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    pade = "readback_librpa_analycont_thiele_pade_division_or_pole_instability_points_from_actual_code_or_preserved_originals"
    assert commands[pade]["surface"] == "tool_run_record"
    assert "--name qsgw_ac_pade_readback " in commands[pade]["cli"]
    parse = "resolve_n_params_anacon_input_parsing_before_molecular_sensitivity_sweep"
    assert commands[parse]["surface"] == "tool_run_record"
    assert "--name qsgw_ac_parameter_parse_readback " in commands[parse]["cli"]
    injection = "provide_or_patch_n_params_anacon_parameter_injection_before_n_params_sensitivity_sweep"
    assert commands[injection] == {
        "action": injection,
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} code state record "
            "--repo-id <LibRPA-repo-id> --upstream-remote <remote> --upstream-branch <branch> "
            "--upstream-commit <commit> --local-branch <branch> --worktree-path <LibRPA-worktree-path> "
            "--linked-records-json <parameter-injection-validation-links> "
            "--known-divergence <n_params_anacon parameter injection path or nfreq-only sweep decision>"
        ),
        "mcp": "aitp_v5_record_code_state",
        "surface": "code_state_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    sensitivity = commands["compare_nfreq_and_n_params_anacon_sensitivity_on_molecular_regression_cases"]
    assert sensitivity["cli"] == (
        f"aitp-v5 --base {ws.base} validation result record "
        "--topic canonical-topic --claim claim-canonical --contract validation-contract-qsgw-ac "
        "--tool-run <molecular-sensitivity-tool-run-id> --status <partial|passed|failed|inconclusive> "
        "--checked-output validation_result --summary <nfreq/n_params_anacon molecular regression comparison>"
    )
    mitigation = commands["compare_pade_mitigation_against_full_frequency_or_contour_deformation_reference"]
    assert mitigation["surface"] == "validation_result_record"
    assert "--tool-run <pade-mitigation-comparison-tool-run-id>" in mitigation["cli"]
    assert all(command["can_update_claim_trust"] is False for command in item["review_action_commands"])
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_generic_readback_and_validation_actions(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord, ValidationContractRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Contour-deformation source readback can bound Padé residue risks.",
            evidence_profile="code_method",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review requires source readback and regression comparison.",
        ),
    )
    write_record(
        ws.registry_dir("validation_contracts") / "validation-contract-gw-residue.md",
        ValidationContractRecord(
            contract_id="validation-contract-gw-residue",
            topic_id="canonical-topic",
            claim_id="claim-canonical",
            required_checks=[
                "verify_g_pole_residue_windows_sign_and_chemical_potential_conventions",
                "compare_cd_or_ac_of_w_against_pade_sigma_on_molecular_or_qsgw_reference_set_before_promotion",
            ],
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="GW residue review needs paper/code readback and validation comparison.",
        reviewed_typed_refs=["claim-canonical", "validation-contract-gw-residue"],
        remaining_actions=[
            "readback_cd_formula_from_godby_golze_sources",
            "extract_formula_level_cd_equations_from_godby_1988_1989_and_golze_2018_sections",
            "map_wc_real_or_complex_frequency_requirement_to_librpa_ac_boundary",
            "design_or_import_real_axis_cd_or_residue_sum_Wc_sigma_path_for_LibRPA",
            "verify_g_pole_residue_windows_sign_and_chemical_potential_conventions",
            "compare_cd_or_ac_of_w_against_pade_sigma_on_molecular_or_qsgw_reference_set_before_promotion",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    commands = {command["action"]: command for command in item["review_action_commands"]}
    readback = commands["readback_cd_formula_from_godby_golze_sources"]
    assert readback["latest_review_id"] == review.review_id
    assert readback["cli"] == (
        f"aitp-v5 --base {ws.base} tool run record "
        "--recipe <source-readback-recipe-id> --family source_readback "
        "--name readback_cd_formula_from_godby_golze_sources "
        "--topic canonical-topic --claim claim-canonical "
        "--outputs-json <source-readback-json> --source-ref <source-or-code-ref>"
    )
    assert readback["surface"] == "tool_run_record"
    mapped = commands["map_wc_real_or_complex_frequency_requirement_to_librpa_ac_boundary"]
    assert mapped["surface"] == "tool_run_record"
    assert "--name map_wc_real_or_complex_frequency_requirement_to_librpa_ac_boundary " in mapped["cli"]
    extract = commands["extract_formula_level_cd_equations_from_godby_1988_1989_and_golze_2018_sections"]
    assert extract["surface"] == "tool_run_record"
    assert (
        "--name extract_formula_level_cd_equations_from_godby_1988_1989_and_golze_2018_sections "
        in extract["cli"]
    )
    assert "--family source_readback " in extract["cli"]
    design = commands["design_or_import_real_axis_cd_or_residue_sum_Wc_sigma_path_for_LibRPA"]
    assert design["surface"] == "tool_run_record"
    assert "--recipe <implementation-boundary-recipe-id> --family implementation_boundary " in design["cli"]
    assert "--outputs-json <implementation-boundary-json>" in design["cli"]
    verify = commands["verify_g_pole_residue_windows_sign_and_chemical_potential_conventions"]
    assert verify["cli"] == (
        f"aitp-v5 --base {ws.base} validation result record "
        "--topic canonical-topic --claim claim-canonical --contract validation-contract-gw-residue "
        "--tool-run <validation-tool-run-id> --status <partial|passed|failed|inconclusive> "
        "--checked-output validation_result "
        "--summary <verify g pole residue windows sign and chemical potential conventions>"
    )
    compare = commands[
        "compare_cd_or_ac_of_w_against_pade_sigma_on_molecular_or_qsgw_reference_set_before_promotion"
    ]
    assert compare["surface"] == "validation_result_record"
    assert "--summary <compare cd or ac of w against pade sigma on molecular or qsgw reference set before promotion>" in compare["cli"]
    assert all(command["can_update_claim_trust"] is False for command in item["review_action_commands"])
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_exposes_inconclusive_followup_commands(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-l2.md",
        ClaimRecord(
            claim_id="claim-l2",
            topic_id="legacy-l2",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy L2 graph needs typed migration before promotion.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="legacy-l2",
        status="inconclusive",
        summary="Legacy L2 is a global graph/index seed, not a claim; route it through typed L2 migration and source review.",
        active_claim_id="claim-l2",
        reviewed_legacy_refs=[
            "legacy_archive:L2/index.md",
            "legacy_archive:L2/entries/INDEX.md",
        ],
        reviewed_typed_refs=["claim-l2"],
        remaining_actions=[
            "classify_noncanonical_seed_before_promotion",
            "require_human_topic_question_before_claim_backfill",
            "decide_archive_or_delete_noncanonical_seed",
            "keep_semantic_review_blocking_until_legacy_basis_exists",
            "migrate_legacy_l2_graph_entries_into_typed_l2_records",
            "rebuild_l2_obsidian_view_from_typed_graph",
            "complete_source_reconstruction",
            "decide_human_checkpoint_before_promotion",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "legacy-l2")
    assert item["review_status"] == "inconclusive"
    assert item["latest_review_id"] == review.review_id
    assert [command["action"] for command in item["review_action_commands"]] == [
        "classify_noncanonical_seed_before_promotion",
        "require_human_topic_question_before_claim_backfill",
        "decide_archive_or_delete_noncanonical_seed",
        "keep_semantic_review_blocking_until_legacy_basis_exists",
        "migrate_legacy_l2_graph_entries_into_typed_l2_records",
        "rebuild_l2_obsidian_view_from_typed_graph",
        "complete_source_reconstruction",
        "decide_human_checkpoint_before_promotion",
    ]
    commands_by_action = {
        command["action"]: command for command in item["review_action_commands"]
    }
    assert commands_by_action["migrate_legacy_l2_graph_entries_into_typed_l2_records"] == {
        "action": "migrate_legacy_l2_graph_entries_into_typed_l2_records",
        "latest_review_id": review.review_id,
        "cli": f"aitp-v5 --base {ws.base} legacy l2-graph-manifest",
        "mcp": "aitp_v5_build_legacy_l2_graph_manifest",
        "surface": "legacy_l2_graph_manifest",
        "effect": "orientation_only",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["classify_noncanonical_seed_before_promotion"]["surface"] == (
        "legacy_semantic_review_result_record"
    )
    assert commands_by_action["classify_noncanonical_seed_before_promotion"]["effect"] == (
        "typed_review_record_write"
    )
    assert commands_by_action["classify_noncanonical_seed_before_promotion"]["can_update_kernel_state"] is True
    assert commands_by_action["classify_noncanonical_seed_before_promotion"]["can_update_claim_trust"] is False
    assert commands_by_action["require_human_topic_question_before_claim_backfill"]["surface"] == (
        "human_checkpoint_record"
    )
    assert "--option provide_topic_question" in commands_by_action[
        "require_human_topic_question_before_claim_backfill"
    ]["cli"]
    assert commands_by_action["decide_archive_or_delete_noncanonical_seed"]["surface"] == (
        "human_checkpoint_record"
    )
    assert "--option archive_seed" in commands_by_action["decide_archive_or_delete_noncanonical_seed"]["cli"]
    assert commands_by_action["keep_semantic_review_blocking_until_legacy_basis_exists"]["surface"] == (
        "legacy_semantic_review_result_record"
    )
    assert (
        "--status inconclusive"
        in commands_by_action["keep_semantic_review_blocking_until_legacy_basis_exists"]["cli"]
    )
    assert commands_by_action["rebuild_l2_obsidian_view_from_typed_graph"]["surface"] == (
        "legacy_l2_obsidian_view_bundle"
    )
    assert commands_by_action["complete_source_reconstruction"] == {
        "action": "complete_source_reconstruction",
        "latest_review_id": review.review_id,
        "cli": f"aitp-v5 --base {ws.base} source reconstruction-review --claim claim-l2",
        "mcp": "aitp_v5_build_source_reconstruction_review_packet",
        "surface": "source_reconstruction_review_packet",
        "effect": "orientation_only",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["decide_human_checkpoint_before_promotion"]["surface"] == "human_checkpoint_record"
    assert all(command["can_update_claim_trust"] is False for command in item["review_action_commands"])
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_exposes_pass_readiness_blockers(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Migrated canonical claim.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review still requires a human checkpoint.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="The source stack is reviewed, but a human checkpoint remains before semantic pass.",
        active_claim_id="claim-canonical",
        reviewed_legacy_refs=["legacy_archive:canonical-topic/state.md"],
        reviewed_typed_refs=["claim:claim-canonical"],
        remaining_actions=["decide_human_checkpoint_before_promotion"],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    readiness = item["pass_readiness"]
    assert readiness["status"] == "blocked"
    assert readiness["pass_candidate"] is False
    assert readiness["latest_review_id"] == review.review_id
    assert readiness["requirements"]["active_claim_statement_present"] is True
    assert "source_reconstruction_incomplete" in readiness["blockers"]
    assert "latest_review_remaining_actions" in readiness["blockers"]
    assert "archive_reference_sampling_required" not in readiness["blockers"]
    assert readiness["remaining_actions"] == ["decide_human_checkpoint_before_promotion"]
    assert readiness["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_l2_typed_review_actions(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-l2.md",
        ClaimRecord(
            claim_id="claim-l2",
            topic_id="legacy-l2",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Legacy L2 graph needs typed review before promotion.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="legacy-l2",
        status="inconclusive",
        summary="The L2 typed migration packet groups legacy graph work items but remains review-only.",
        active_claim_id="claim-l2",
        reviewed_legacy_refs=["legacy_archive:L2/index.md"],
        reviewed_typed_refs=["claim-l2", "legacy_l2_typed_migration_packet:work_items=153"],
        remaining_actions=[
            "review_legacy_l2_memory_entry_candidates",
            "review_legacy_l2_graph_nodes_for_physics_objects",
            "review_legacy_l2_graph_edges_for_object_relations",
            "review_legacy_l2_steps_for_sensemaking_reports",
            "review_legacy_l2_towers_for_memory_entries",
            "record_reviewed_typed_l2_records_or_keep_orientation_only",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "legacy-l2")
    commands_by_action = {
        command["action"]: command for command in item["review_action_commands"]
    }
    for action in [
        "review_legacy_l2_memory_entry_candidates",
        "review_legacy_l2_graph_nodes_for_physics_objects",
        "review_legacy_l2_graph_edges_for_object_relations",
        "review_legacy_l2_steps_for_sensemaking_reports",
        "review_legacy_l2_towers_for_memory_entries",
    ]:
        assert commands_by_action[action] == {
            "action": action,
            "latest_review_id": review.review_id,
            "cli": f"aitp-v5 --base {ws.base} legacy l2-typed-migration-packet",
            "mcp": "aitp_v5_build_legacy_l2_typed_migration_packet",
            "surface": "legacy_l2_typed_migration_packet",
            "effect": "orientation_only",
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }
    assert commands_by_action["record_reviewed_typed_l2_records_or_keep_orientation_only"] == {
        "action": "record_reviewed_typed_l2_records_or_keep_orientation_only",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {run} --topic legacy-l2 "
            "--status <inconclusive|passed> --legacy-ref <reviewed-l2-ref> "
            "--typed-ref <reviewed-typed-l2-record-or-packet-ref> "
            "--summary <reviewed typed L2 migration basis and remaining gaps>"
        ),
        "mcp": "aitp_v5_record_legacy_semantic_review_result",
        "surface": "legacy_semantic_review_result_record",
        "effect": "typed_review_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_source_review_result_action_to_result_record(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A canonical legacy claim needs source reconstruction review.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    source_ref = "legacy-topic:canonical-topic/state.md"
    record_evidence(
        ws,
        topic_id="canonical-topic",
        claim_id="claim-canonical",
        evidence_type="legacy_source",
        status="legacy_seed",
        summary="Legacy source basis preserved for review.",
        source_refs=[source_ref],
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="The legacy claim needs a typed source reconstruction review result before semantic pass.",
        active_claim_id="claim-canonical",
        reviewed_legacy_refs=[source_ref],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "complete_source_reconstruction_components",
            "record_source_reconstruction_review_result",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    commands_by_action = {
        command["action"]: command for command in item["review_action_commands"]
    }
    assert commands_by_action["complete_source_reconstruction_components"] == {
        "action": "complete_source_reconstruction_components",
        "latest_review_id": review.review_id,
        "cli": f"aitp-v5 --base {ws.base} source reconstruction-review --claim claim-canonical",
        "mcp": "aitp_v5_build_source_reconstruction_review_packet",
        "surface": "source_reconstruction_review_packet",
        "effect": "orientation_only",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["record_source_reconstruction_review_result"] == {
        "action": "record_source_reconstruction_review_result",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} source reconstruction-review-result "
            "--claim claim-canonical --status <passed|needs_revision|inconclusive> "
            "--reviewed-component definitions --reviewed-component assumptions_or_scope "
            "--reviewed-component dependency_graph --reviewed-component reconstruction_path "
            "--reviewed-component failure_conditions "
            f"--basis-ref {source_ref} "
            "--summary <source reconstruction review basis>"
        ),
        "mcp": "aitp_v5_record_source_reconstruction_review_result",
        "surface": "source_reconstruction_review_result_record",
        "effect": "typed_review_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_manifest_flags_completed_source_review_result_for_followup(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.source_reconstruction_review import record_source_reconstruction_review_result
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A canonical legacy claim needs source reconstruction review.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    source_ref = "legacy-topic:canonical-topic/state.md"
    record_evidence(
        ws,
        topic_id="canonical-topic",
        claim_id="claim-canonical",
        evidence_type="legacy_source",
        status="legacy_seed",
        summary="Legacy source basis preserved for review.",
        source_refs=[source_ref],
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="The legacy claim needs a typed source reconstruction review result before semantic pass.",
        active_claim_id="claim-canonical",
        reviewed_legacy_refs=[source_ref],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "record_source_reconstruction_review_result",
        ],
    )
    source_review = record_source_reconstruction_review_result(
        ws,
        claim_id="claim-canonical",
        status="inconclusive",
        reviewed_components=["definitions", "assumptions_or_scope"],
        basis_refs=[source_ref],
        remaining_actions=["record_missing_physics_objects"],
        summary="Definitions and scope were reviewed but still require typed object records.",
    )

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=run)
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    manifest_item = next(item for item in manifest["items"] if item["topic"] == "canonical-topic")
    work_item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    assert manifest_item["satisfied_review_actions"] == [
        "record_source_reconstruction_review_result"
    ]
    assert manifest_item["followup_review_actions"] == [
        "record_followup_semantic_review_result_for_satisfied_actions"
    ]
    assert work_item["followup_review_commands"] == [
        {
            "action": "record_followup_semantic_review_result_for_satisfied_actions",
            "latest_review_id": review.review_id,
            "satisfied_review_actions": [
                "record_source_reconstruction_review_result"
            ],
            "result_cli": (
                f"aitp-v5 --base {ws.base} legacy semantic-review-result "
                f"--migration-dir {run} --topic canonical-topic "
                "--status <passed|inconclusive> "
                f"--typed-ref claim-canonical --typed-ref source-reconstruction-review:{source_review.result_id} "
                f"--legacy-ref {source_ref} "
                f"--summary <reviewed satisfied actions; explain any remaining semantic gaps>"
            ),
            "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
            "can_update_claim_trust": False,
        }
    ]
    assert source_review.result_id
    assert require_valid_public_surface("legacy_semantic_review_manifest", manifest) == manifest
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_worklist_maps_typed_source_stack_backfill_actions(tmp_path):
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A canonical legacy claim needs typed source-stack backfill.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="The source reconstruction review identified concrete typed source-stack backfill actions.",
        active_claim_id="claim-canonical",
        reviewed_legacy_refs=["legacy_l1:canonical-topic/L1/question_contract.md"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "record_physics_object_definitions_for_crpa_core_quantities",
            "record_claim_scope_or_object_assumptions_for_selected_crpa_variant",
            "record_object_relations_for_chi0_chitilde_wr_u_workflow",
            "record_failure_conditions_or_validation_contract_for_projection_and_wannier_transform",
        ],
    )

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=run)

    item = next(item for item in worklist["items"] if item["topic"] == "canonical-topic")
    commands_by_action = {
        command["action"]: command for command in item["review_action_commands"]
    }
    assert commands_by_action["record_physics_object_definitions_for_crpa_core_quantities"] == {
        "action": "record_physics_object_definitions_for_crpa_core_quantities",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} object record --topic canonical-topic "
            "--type <object_type> --name <name> --definition <source-grounded-definition> "
            "--source-ref <legacy-or-typed-source-ref>"
        ),
        "mcp": "aitp_v5_record_physics_object",
        "surface": "physics_object_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["record_claim_scope_or_object_assumptions_for_selected_crpa_variant"] == {
        "action": "record_claim_scope_or_object_assumptions_for_selected_crpa_variant",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} object record --topic canonical-topic "
            "--type <object_type> --name <scoped-object-or-regime> "
            "--definition <source-grounded-definition> --assumption <assumption-or-scope-limit> "
            "--source-ref <legacy-or-typed-source-ref>"
        ),
        "mcp": "aitp_v5_record_physics_object",
        "surface": "physics_object_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["record_object_relations_for_chi0_chitilde_wr_u_workflow"] == {
        "action": "record_object_relations_for_chi0_chitilde_wr_u_workflow",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} relation record --topic canonical-topic "
            "--type <relation_type> --subject <object-id> --object <object-id> "
            "--statement <source-grounded-relation> --claim claim-canonical "
            "--source-ref <legacy-or-typed-source-ref>"
        ),
        "mcp": "aitp_v5_record_object_relation",
        "surface": "object_relation_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert commands_by_action["record_failure_conditions_or_validation_contract_for_projection_and_wannier_transform"] == {
        "action": "record_failure_conditions_or_validation_contract_for_projection_and_wannier_transform",
        "latest_review_id": review.review_id,
        "cli": (
            f"aitp-v5 --base {ws.base} validation contract create --topic canonical-topic "
            "--claim claim-canonical --required-check <check> --failure-mode <failure-mode> "
            "--required-output source_reconstruction"
        ),
        "mcp": "aitp_v5_create_validation_contract",
        "surface": "validation_contract_record",
        "effect": "typed_record_write",
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }
    assert require_valid_public_surface("legacy_semantic_review_worklist", worklist) == worklist


def test_legacy_semantic_review_queue_uses_latest_written_review_not_lexicographic_id(tmp_path):
    from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
    from brain.v5.models import ClaimRecord, LegacySemanticReviewResultRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Migrated canonical claim.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review_dir = ws.registry_dir("legacy_semantic_reviews")
    old = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-z-old",
        migration_run_id="legacy-v5-lossless-test",
        migration_dir=str(run),
        topic="canonical-topic",
        active_claim_id="claim-canonical",
        status="needs_revision",
        summary="Older review sorted later by id.",
        reviewed_typed_refs=["claim-canonical"],
        created_at="2026-05-24T00:00:00Z",
    )
    new = LegacySemanticReviewResultRecord(
        review_id="legacy-semantic-review-a-new",
        migration_run_id="legacy-v5-lossless-test",
        migration_dir=str(run),
        topic="canonical-topic",
        active_claim_id="claim-canonical",
        status="inconclusive",
        summary="Newer follow-up review sorted earlier by id.",
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["complete_source_reconstruction_components"],
        created_at="2026-05-25T00:00:00Z",
    )
    write_record(review_dir / f"{old.review_id}.md", old)
    write_record(review_dir / f"{new.review_id}.md", new)

    queue = build_legacy_semantic_review_queue(ws, migration_dir=run)

    canonical = next(item for item in queue["items"] if item["topic"] == "canonical-topic")
    assert canonical["semantic_review_status"] == "reviewed_inconclusive"
    assert canonical["latest_semantic_review"]["review_id"] == new.review_id


def test_legacy_semantic_review_worklist_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_semantic_review_worklist
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base", str(base), "legacy", "semantic-review-worklist",
        "--migration-dir", str(run),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_semantic_review_worklist(str(base), migration_dir=str(run))

    assert cli_payload["kind"] == "legacy_semantic_review_worklist"
    assert mcp_payload["kind"] == "legacy_semantic_review_worklist"
    assert runtime_entrypoints()["legacy_semantic_review_worklist"] == {
        "cli": "aitp-v5 legacy semantic-review-worklist <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_worklist",
        "surface": "legacy_semantic_review_worklist",
    }


def test_legacy_semantic_review_result_records_basis_and_updates_queue(tmp_path):
    from brain.v5.legacy_semantic_review import (
        build_legacy_semantic_review_queue,
        record_legacy_semantic_review_result,
    )
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Migrated canonical claim.",
            evidence_profile="legacy_import",
            confidence_state="hypothesis",
            active_uncertainty="Semantic review required.",
        ),
    )

    result = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="inconclusive",
        summary="Reviewed the migrated claim against state.md; source reconstruction is still missing.",
        reviewed_legacy_refs=["legacy-topic:canonical-topic/state.md"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["complete_source_reconstruction"],
    )
    payload = {"ok": True, **result.__dict__}

    assert require_valid_public_surface("legacy_semantic_review_result_record", payload) == payload
    assert result.kind == "legacy_semantic_review_result"
    assert result.topic == "canonical-topic"
    assert result.status == "inconclusive"
    assert result.reviewed_legacy_refs == ["legacy-topic:canonical-topic/state.md"]
    assert result.created_at
    assert result.summary_inputs_trusted is False
    assert result.can_update_claim_trust is False

    queue = build_legacy_semantic_review_queue(ws, migration_dir=run)
    by_topic = {item["topic"]: item for item in queue["items"]}
    canonical = by_topic["canonical-topic"]
    assert canonical["semantic_review_status"] == "reviewed_inconclusive"
    assert canonical["semantic_review_result_ids"] == [result.review_id]
    assert canonical["latest_semantic_review"]["review_id"] == result.review_id
    assert canonical["latest_semantic_review"]["orientation_only"] is True


def test_legacy_semantic_review_result_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_record_legacy_semantic_review_result
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)

    assert main([
        "--base",
        str(base),
        "legacy",
        "semantic-review-result",
        "--migration-dir",
        str(run),
        "--topic",
        "legacy-l2",
        "--status",
        "needs_revision",
        "--legacy-ref",
        "legacy-topic:legacy-l2/state.md",
        "--summary",
        "Claim statement still needs source reconstruction before trust.",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_record_legacy_semantic_review_result(
        str(base),
        migration_dir=str(run),
        topic="legacy-l2",
        status="inconclusive",
        summary="Noncanonical seed needs classification before promotion.",
        reviewed_legacy_refs=["legacy-topic:L2/state.md"],
        remaining_actions=["classify_noncanonical_seed_before_promotion"],
    )

    assert cli_payload["kind"] == "legacy_semantic_review_result"
    assert cli_payload["status"] == "needs_revision"
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["kind"] == "legacy_semantic_review_result"
    assert mcp_payload["topic"] == "legacy-l2"
    assert runtime_entrypoints()["record_legacy_semantic_review_result"] == {
        "cli": "aitp-v5 legacy semantic-review-result <args>",
        "mcp": "aitp_v5_record_legacy_semantic_review_result",
        "surface": "legacy_semantic_review_result_record",
    }


def test_legacy_semantic_repair_plan_proposes_question_backfill_from_reviewed_revision(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    question = "Which AdS Einstein-equation solutions did the legacy topic ask us to classify?"
    (legacy_topic / "state.md").write_text(
        "---\n"
        "title: Canonical Topic\n"
        "---\n"
        "# Canonical Topic\n\n"
        "## Research Question\n"
        f"{question}\n\n"
        "## Notes\n"
        "The migrated claim statement was empty before repair planning.\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Active claim statement is empty while legacy state.md has a research question.",
        reviewed_legacy_refs=["legacy-topic:canonical-topic/state.md"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_statement_from_legacy_state_question"],
    )
    before = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    after = {path.as_posix() for path in ws.root.rglob("*") if path.is_file()}
    assert before == after
    assert plan["kind"] == "legacy_semantic_repair_plan"
    assert plan["repair_status"] == "proposed_repairs"
    assert plan["active_claim_id"] == "claim-canonical"
    assert plan["latest_semantic_review"]["review_id"] == review.review_id
    assert plan["proposed_repairs"] == [
        {
            "repair_type": "claim_statement_backfill",
            "target_ref": "claim-canonical",
            "current_value": "",
            "proposed_value": question,
            "basis_refs": [
                "legacy-topic:canonical-topic/state.md",
                review.review_id,
            ],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]
    assert plan["can_apply"] is False
    assert plan["semantic_lossless_proven"] is False
    assert plan["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_repair_plan", plan) == plan


def test_legacy_semantic_repair_plan_accepts_review_action_phrase_for_question_backfill(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    question = "Which AdS Einstein-equation boundary conditions should be classified?"
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n"
        "## Research Question\n"
        f"{question}\n\n"
        "## Notes\n"
        "The typed migration kept this topic but the claim statement was empty.\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Active claim statement is empty while legacy state.md preserves the research question.",
        reviewed_legacy_refs=[f"legacy_candidate:{legacy_topic / 'state.md'}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["Backfill the active claim statement from the legacy Research Question."],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["repair_status"] == "proposed_repairs"
    assert plan["latest_semantic_review"]["review_id"] == review.review_id
    assert plan["proposed_repairs"][0]["repair_type"] == "claim_statement_backfill"
    assert plan["proposed_repairs"][0]["proposed_value"] == question


def test_legacy_semantic_repair_plan_proposes_validation_revision_from_failed_result(tmp_path):
    from brain.v5.legacy_semantic_repair import (
        apply_legacy_semantic_repair,
        build_legacy_semantic_repair_plan,
    )
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord, ValidationResultRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="A validation-backed legacy claim.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    failed_result = ValidationResultRecord(
        result_id="validation-result-failed-toy",
        topic_id="canonical-topic",
        claim_id="claim-canonical",
        contract_id="validation-contract-canonical",
        tool_run_id="tool-run-failed-toy",
        status="failed",
        checked_outputs=["toy script reported 0/3 checks passed"],
        failure_modes_observed=["target projector weights zeroed the checked transition"],
        summary="The legacy toy validation failed and must be repaired before semantic pass.",
    )
    write_record(ws.registry_dir("validation_results") / f"{failed_result.result_id}.md", failed_result)
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The legacy validation surface failed and needs revision.",
        reviewed_typed_refs=["claim-canonical"],
        validation_result_ids=[failed_result.result_id],
        remaining_actions=["repair_or_replace_validate_wcrpa_toy_model_to_exercise_target_screening"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["repair_status"] == "proposed_repairs"
    assert plan["proposed_repairs"] == [
        {
            "repair_type": "validation_result_revision",
            "target_ref": failed_result.result_id,
            "current_value": "failed",
            "proposed_value": "Record a revised validation result after repairing or replacing the failed validation surface.",
            "basis_refs": [
                failed_result.result_id,
                review.review_id,
            ],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]
    assert require_valid_public_surface("legacy_semantic_repair_plan", plan) == plan

    result = apply_legacy_semantic_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="validation_result_revision",
        review_id=review.review_id,
    )

    assert result["applied"] is False
    assert result["required_actions"] == ["record_revised_validation_result_before_semantic_pass"]
    assert result["can_update_kernel_state"] is False
    assert result["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_repair_apply", result) == result


def test_legacy_semantic_repair_plan_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_legacy_semantic_repair_plan
    from brain.v5.models import ClaimRecord
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n## Research Question\nWhich question should be restored?\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    assert main([
        "--base",
        str(base),
        "legacy",
        "semantic-review-result",
        "--migration-dir",
        str(run),
        "--topic",
        "canonical-topic",
        "--status",
        "needs_revision",
        "--legacy-ref",
        "legacy-topic:canonical-topic/state.md",
        "--typed-ref",
        "claim-canonical",
        "--summary",
        "Claim statement needs body-question backfill.",
    ]) == 0
    capsys.readouterr()

    assert main([
        "--base", str(base), "legacy", "semantic-repair-plan",
        "--migration-dir", str(run), "--topic", "canonical-topic",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_legacy_semantic_repair_plan(
        str(base),
        migration_dir=str(run),
        topic="canonical-topic",
    )

    assert cli_payload["kind"] == "legacy_semantic_repair_plan"
    assert cli_payload["repair_status"] == "proposed_repairs"
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_semantic_repair_plan"
    assert runtime_entrypoints()["legacy_semantic_repair_plan"] == {
        "cli": "aitp-v5 legacy semantic-repair-plan <args>",
        "mcp": "aitp_v5_build_legacy_semantic_repair_plan",
        "surface": "legacy_semantic_repair_plan",
    }


def test_legacy_semantic_repair_apply_backfills_claim_statement_and_records_provenance(tmp_path):
    from brain.v5.legacy_semantic_repair import apply_legacy_semantic_repair
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord, LegacySemanticRepairRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records, write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    question = "Which AdS solutions should be restored into the migrated claim?"
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n## Research Question\n"
        f"{question}\n\n"
        "## Notes\nLegacy review found the migrated claim was empty.\n",
        encoding="utf-8",
    )
    claim = ClaimRecord(
        claim_id="claim-canonical",
        topic_id="canonical-topic",
        statement="",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="Semantic review required.",
    )
    write_record(ws.registry_dir("claims") / "claim-canonical.md", claim)
    write_record(ws.topic_dir("canonical-topic") / "claims" / "ledger" / "claim-canonical.md", claim)
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Active claim statement is empty while legacy state.md preserves the research question.",
        reviewed_legacy_refs=["legacy-topic:canonical-topic/state.md"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_statement_from_legacy_state_question"],
    )

    result = apply_legacy_semantic_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="claim_statement_backfill",
        review_id=review.review_id,
    )

    assert result["kind"] == "legacy_semantic_repair_apply"
    assert result["applied"] is True
    assert result["repair_type"] == "claim_statement_backfill"
    assert result["active_claim_id"] == "claim-canonical"
    assert result["previous_value"] == ""
    assert result["new_value"] == question
    assert result["review_id"] == review.review_id
    assert result["can_update_claim_trust"] is False
    assert result["can_update_kernel_state"] is True
    assert result["semantic_lossless_proven"] is False
    assert require_valid_public_surface("legacy_semantic_repair_apply", result) == result

    claims = {record.claim_id: record for record in list_records(ws.registry_dir("claims"), ClaimRecord)}
    ledger_claims = {
        record.claim_id: record
        for record in list_records(ws.topic_dir("canonical-topic") / "claims" / "ledger", ClaimRecord)
    }
    assert claims["claim-canonical"].statement == question
    assert ledger_claims["claim-canonical"].statement == question
    assert claims["claim-canonical"].confidence_state == "legacy_seed"

    repairs = list_records(ws.registry_dir("legacy_semantic_repairs"), LegacySemanticRepairRecord)
    assert [repair.repair_id for repair in repairs] == [result["repair_id"]]
    assert repairs[0].review_id == review.review_id
    assert repairs[0].applied is True
    assert repairs[0].can_update_claim_trust is False


def test_legacy_semantic_repair_applies_scope_and_failure_mode_from_reviewed_legacy_refs(tmp_path):
    from brain.v5.legacy_semantic_repair import (
        apply_legacy_semantic_repair,
        build_legacy_semantic_repair_plan,
    )
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records, write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    candidate = legacy_topic / "L3" / "candidates" / "candidate-counting.md"
    review_file = legacy_topic / "L4" / "reviews" / "candidate-counting.md"
    candidate.parent.mkdir(parents=True)
    review_file.parent.mkdir(parents=True)
    candidate.write_text(
        "---\n"
        "candidate_id: candidate-counting\n"
        "claim: Finite-size counting identifies the FQHE edge sector.\n"
        "regime_of_validity: N<=10 fixed sector only.\n"
        "---\n"
        "# Candidate\n\n"
        "## Assumptions\n"
        "Same sector convention.\n",
        encoding="utf-8",
    )
    review_file.write_text(
        "---\n"
        "artifact_kind: l4_review\n"
        "candidate_id: candidate-counting\n"
        "outcome: pass\n"
        "devils_advocate: Wrong sector assignment breaks the counting match.\n"
        "---\n"
        "# Review\n\n"
        "## Devil's Advocate\n"
        "Wrong sector assignment breaks the counting match.\n",
        encoding="utf-8",
    )
    claim = ClaimRecord(
        claim_id="claim-canonical",
        topic_id="canonical-topic",
        statement="Finite-size counting identifies the FQHE edge sector.",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="Semantic review required.",
    )
    write_record(ws.registry_dir("claims") / "claim-canonical.md", claim)
    write_record(ws.topic_dir("canonical-topic") / "claims" / "ledger" / "claim-canonical.md", claim)
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="Claim statement is preserved, but candidate scope and failure mode were not backfilled.",
        reviewed_legacy_refs=[f"legacy_candidate:{candidate}", f"legacy_l4_review:{review_file}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=[
            "backfill_active_claim_scope_from_legacy_candidate_regime",
            "backfill_active_claim_failure_mode_from_legacy_review",
        ],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert {
        (repair["repair_type"], repair["proposed_value"])
        for repair in plan["proposed_repairs"]
    } == {
        ("claim_scope_backfill", "N<=10 fixed sector only."),
        ("claim_failure_mode_backfill", "Wrong sector assignment breaks the counting match."),
    }
    assert require_valid_public_surface("legacy_semantic_repair_plan", plan) == plan

    scope_result = apply_legacy_semantic_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="claim_scope_backfill",
        review_id=review.review_id,
    )
    failure_result = apply_legacy_semantic_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="claim_failure_mode_backfill",
        review_id=review.review_id,
    )

    assert scope_result["applied"] is True
    assert scope_result["repair_type"] == "claim_scope_backfill"
    assert scope_result["can_update_claim_trust"] is False
    assert require_valid_public_surface("legacy_semantic_repair_apply", scope_result) == scope_result
    assert failure_result["applied"] is True
    assert failure_result["repair_type"] == "claim_failure_mode_backfill"
    assert require_valid_public_surface("legacy_semantic_repair_apply", failure_result) == failure_result
    claims = {record.claim_id: record for record in list_records(ws.registry_dir("claims"), ClaimRecord)}
    assert claims["claim-canonical"].statement == "Finite-size counting identifies the FQHE edge sector."
    assert claims["claim-canonical"].scope == "N<=10 fixed sector only."
    assert claims["claim-canonical"].strongest_failure_mode == "Wrong sector assignment breaks the counting match."
    assert claims["claim-canonical"].confidence_state == "legacy_seed"


def test_legacy_semantic_repair_backfills_failure_mode_from_l1_non_success_conditions(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    l1_contract = legacy_topic / "L1" / "question_contract.md"
    l1_contract.parent.mkdir(parents=True)
    l1_contract.write_text(
        "---\n"
        "artifact_kind: l1_question_contract\n"
        "bounded_question: Which runtime failure modes should remain visible?\n"
        "---\n"
        "# Question Contract\n\n"
        "## Non-Success Conditions\n\n"
        "- Code compiles but produces NaN gaps.\n"
        "- Iteration diverges or exceeds memory limits.\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Head-wing recomputation should be checked.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The reviewed L1 contract names failure conditions missing from the claim.",
        reviewed_legacy_refs=[f"legacy_l1:{l1_contract}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_failure_mode_from_legacy_l1_non_success_conditions"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"] == [
        {
            "repair_type": "claim_failure_mode_backfill",
            "target_ref": "claim-canonical",
            "current_value": "",
            "proposed_value": "- Code compiles but produces NaN gaps. - Iteration diverges or exceeds memory limits.",
            "basis_refs": [f"legacy_l1:{l1_contract}", review.review_id],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]


def test_legacy_semantic_repair_backfills_scope_from_reviewed_l1_question_contract(tmp_path):
    from brain.v5.legacy_semantic_repair import (
        apply_legacy_semantic_repair,
        build_legacy_semantic_repair_plan,
    )
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records, write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    l1_contract = legacy_topic / "L1" / "question_contract.md"
    l1_contract.parent.mkdir(parents=True)
    l1_contract.write_text(
        "---\n"
        "artifact_kind: l1_question_contract\n"
        "bounded_question: Which contour-deformation question should be preserved?\n"
        "scope_boundaries: Single-shot QSGW cycle only; no vertex corrections.\n"
        "---\n"
        "# Question Contract\n",
        encoding="utf-8",
    )
    claim = ClaimRecord(
        claim_id="claim-canonical",
        topic_id="canonical-topic",
        statement="Which contour-deformation question should be preserved?",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="Semantic review required.",
    )
    write_record(ws.registry_dir("claims") / "claim-canonical.md", claim)
    write_record(ws.topic_dir("canonical-topic") / "claims" / "ledger" / "claim-canonical.md", claim)
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="L1 scope boundaries were reviewed but are missing from the migrated claim scope.",
        reviewed_legacy_refs=[f"legacy_l1:{l1_contract}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_scope_from_legacy_l1_question_contract"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"] == [
        {
            "repair_type": "claim_scope_backfill",
            "target_ref": "claim-canonical",
            "current_value": "",
            "proposed_value": "Single-shot QSGW cycle only; no vertex corrections.",
            "basis_refs": [f"legacy_l1:{l1_contract}", review.review_id],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]
    assert require_valid_public_surface("legacy_semantic_repair_plan", plan) == plan

    result = apply_legacy_semantic_repair(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        repair_type="claim_scope_backfill",
        review_id=review.review_id,
    )

    assert result["applied"] is True
    assert result["repair_type"] == "claim_scope_backfill"
    assert require_valid_public_surface("legacy_semantic_repair_apply", result) == result
    claims = {record.claim_id: record for record in list_records(ws.registry_dir("claims"), ClaimRecord)}
    assert claims["claim-canonical"].scope == "Single-shot QSGW cycle only; no vertex corrections."
    assert claims["claim-canonical"].confidence_state == "legacy_seed"


def test_legacy_semantic_repair_l1_scope_action_ignores_candidate_assumptions(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    candidate = legacy_topic / "L3" / "candidates" / "candidate.md"
    l1_contract = legacy_topic / "L1" / "question_contract.md"
    candidate.parent.mkdir(parents=True)
    l1_contract.parent.mkdir(parents=True)
    candidate.write_text(
        "---\n"
        "candidate_id: candidate\n"
        "claim: Candidate claim.\n"
        "---\n"
        "# Candidate\n\n"
        "## Assumptions\n"
        "Candidate assumptions are not the L1 scope.\n",
        encoding="utf-8",
    )
    l1_contract.write_text(
        "---\n"
        "artifact_kind: l1_question_contract\n"
        "scope_boundaries: L1 scope is the requested repair source.\n"
        "---\n"
        "# Question Contract\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Candidate claim.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The reviewed action asks for L1 scope, not candidate assumptions.",
        reviewed_legacy_refs=[f"legacy_candidate:{candidate}", f"legacy_l1:{l1_contract}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_scope_from_legacy_l1_question_contract"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"] == [
        {
            "repair_type": "claim_scope_backfill",
            "target_ref": "claim-canonical",
            "current_value": "",
            "proposed_value": "L1 scope is the requested repair source.",
            "basis_refs": [f"legacy_candidate:{candidate}", f"legacy_l1:{l1_contract}", review.review_id],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]


def test_legacy_semantic_repair_joins_l1_scope_frontmatter_list(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    l1_contract = legacy_topic / "L1" / "question_contract.md"
    l1_contract.parent.mkdir(parents=True)
    l1_contract.write_text(
        "---\n"
        "artifact_kind: l1_question_contract\n"
        "scope_boundaries:\n"
        "  - Standard RPA correlation energy from ACFD theorem\n"
        "  - EXCLUDED: vertex corrections and SOC\n"
        "---\n"
        "# Question Contract\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="Claim already present.",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The reviewed L1 scope is stored as a YAML list.",
        reviewed_legacy_refs=[f"legacy_l1:{l1_contract}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_scope_from_legacy_l1_question_contract"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"] == [
        {
            "repair_type": "claim_scope_backfill",
            "target_ref": "claim-canonical",
            "current_value": "",
            "proposed_value": "Standard RPA correlation energy from ACFD theorem; EXCLUDED: vertex corrections and SOC",
            "basis_refs": [f"legacy_l1:{l1_contract}", review.review_id],
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]


def test_legacy_semantic_repair_prefers_reviewed_l1_bounded_question_for_statement(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n## Research Question\nWhat was the broad topic question?\n",
        encoding="utf-8",
    )
    l1_contract = legacy_topic / "L1" / "question_contract.md"
    l1_contract.parent.mkdir(parents=True)
    l1_contract.write_text(
        "---\n"
        "artifact_kind: l1_question_contract\n"
        "bounded_question: How does the reviewed L1 contract sharpen the imported claim?\n"
        "scope_boundaries: L1-only scope.\n"
        "---\n"
        "# Question Contract\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The reviewed L1 bounded question is sharper than the broad legacy state question.",
        reviewed_legacy_refs=[f"legacy_candidate:{legacy_topic / 'state.md'}", f"legacy_l1:{l1_contract}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_statement_from_legacy_l1_bounded_question"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"][0] == {
        "repair_type": "claim_statement_backfill",
        "target_ref": "claim-canonical",
        "current_value": "",
        "proposed_value": "How does the reviewed L1 contract sharpen the imported claim?",
        "basis_refs": [
            f"legacy_candidate:{legacy_topic / 'state.md'}",
            f"legacy_l1:{l1_contract}",
            review.review_id,
        ],
        "mutation_authority": "none_review_and_apply_separately",
    }


def test_legacy_semantic_repair_prefers_reviewed_l3_distilled_claim_for_statement(tmp_path):
    from brain.v5.legacy_semantic_repair import build_legacy_semantic_repair_plan
    from brain.v5.legacy_semantic_review import record_legacy_semantic_review_result
    from brain.v5.models import ClaimRecord
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "v5")
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n## Research Question\nWhich research question was asked?\n",
        encoding="utf-8",
    )
    distillation = legacy_topic / "L3" / "distill" / "active_distillation.md"
    distillation.parent.mkdir(parents=True)
    distillation.write_text(
        "---\n"
        "artifact_kind: l3_active_distillation\n"
        "distilled_claim: The reviewed derivation establishes a reusable topological Hamiltonian pipeline.\n"
        "---\n"
        "# Active Distillation\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    review = record_legacy_semantic_review_result(
        ws,
        migration_dir=run,
        topic="canonical-topic",
        status="needs_revision",
        summary="The legacy L3 distillation has a claim but the migrated claim statement is empty.",
        reviewed_legacy_refs=[f"legacy_candidate:{legacy_topic / 'state.md'}", f"legacy_l3_process:{distillation}"],
        reviewed_typed_refs=["claim-canonical"],
        remaining_actions=["backfill_active_claim_statement_from_legacy_l3_distilled_claim"],
    )

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=run, topic="canonical-topic")

    assert plan["proposed_repairs"][0]["repair_type"] == "claim_statement_backfill"
    assert plan["proposed_repairs"][0]["proposed_value"] == (
        "The reviewed derivation establishes a reusable topological Hamiltonian pipeline."
    )
    assert plan["proposed_repairs"][0]["basis_refs"] == [
        f"legacy_candidate:{legacy_topic / 'state.md'}",
        f"legacy_l3_process:{distillation}",
        review.review_id,
    ]


def test_legacy_semantic_repair_apply_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_apply_legacy_semantic_repair
    from brain.v5.models import ClaimRecord
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.store import write_record
    from brain.v5.workspace import init_workspace

    base = tmp_path / "v5"
    ws = init_workspace(base)
    run = _write_migration_run(ws)
    legacy_topic = ws.base / "research" / "aitp-topics" / "canonical-topic"
    legacy_topic.mkdir(parents=True)
    (legacy_topic / "state.md").write_text(
        "# Canonical Topic\n\n## Research Question\nWhich question should be applied?\n",
        encoding="utf-8",
    )
    write_record(
        ws.registry_dir("claims") / "claim-canonical.md",
        ClaimRecord(
            claim_id="claim-canonical",
            topic_id="canonical-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="Semantic review required.",
        ),
    )
    assert main([
        "--base",
        str(base),
        "legacy",
        "semantic-review-result",
        "--migration-dir",
        str(run),
        "--topic",
        "canonical-topic",
        "--status",
        "needs_revision",
        "--legacy-ref",
        "legacy-topic:canonical-topic/state.md",
        "--typed-ref",
        "claim-canonical",
        "--summary",
        "Claim statement needs apply-surface backfill.",
    ]) == 0
    review_payload = json.loads(capsys.readouterr().out)

    assert main([
        "--base", str(base), "legacy", "semantic-repair-apply",
        "--migration-dir", str(run),
        "--topic", "canonical-topic",
        "--repair-type", "claim_statement_backfill",
        "--review-id", review_payload["review_id"],
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_apply_legacy_semantic_repair(
        str(base),
        migration_dir=str(run),
        topic="canonical-topic",
        repair_type="claim_statement_backfill",
        review_id=review_payload["review_id"],
    )

    assert cli_payload["kind"] == "legacy_semantic_repair_apply"
    assert cli_payload["applied"] is True
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_semantic_repair_apply"
    assert mcp_payload["applied"] is False
    assert mcp_payload["required_actions"] == ["select_available_repair"]
    assert runtime_entrypoints()["legacy_semantic_repair_apply"] == {
        "cli": "aitp-v5 legacy semantic-repair-apply <args>",
        "mcp": "aitp_v5_apply_legacy_semantic_repair",
        "surface": "legacy_semantic_repair_apply",
    }


def test_legacy_migration_converts_all_candidates_and_reviews_to_typed_records(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.markdown import read_md
    from brain.v5.models import ClaimRecord, SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    candidate_dir = legacy / "L3" / "candidates"
    review_dir = legacy / "L4" / "reviews"
    review_dir.mkdir(parents=True)
    second = candidate_dir / "candidate-negative-control.md"
    review = review_dir / "review-counting.md"
    second.write_text(
        "---\n"
        "candidate_id: candidate-negative-control\n"
        "claim: A negative-control sector breaks the same counting sequence.\n"
        "evidence: The mismatch appears in the control sector.\n"
        "---\n"
        "# Candidate Negative Control\n\nThe control sector should not match the edge CFT.\n",
        encoding="utf-8",
    )
    review.write_text(
        "---\n"
        "review_id: review-counting\n"
        "status: supports\n"
        "summary: L4 review accepts the scoped counting claim.\n"
        "---\n"
        "# Review\n\nThe review accepts the claim only within the recorded finite-size scope.\n",
        encoding="utf-8",
    )
    before = second.read_text(encoding="utf-8")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    assert second.read_text(encoding="utf-8") == before
    claims = list_records(ws.registry_dir("claims"), ClaimRecord)
    statements = {claim.statement for claim in claims}
    assert statements == {
        "Finite-size counting identifies the FQHE edge sector.",
        "A negative-control sector breaks the same counting sequence.",
    }
    assert set(result["written_records"]["claims"]) == {claim.claim_id for claim in claims}
    assert result["written_records"]["sensemaking_reports"]

    all_evidence = []
    for claim in claims:
        all_evidence.extend(list_evidence_for_claim(ws, claim.claim_id))
    evidence_types = {evidence.evidence_type for evidence in all_evidence}
    assert "legacy_candidate" in evidence_types
    assert "legacy_l4_review" in evidence_types
    assert any(review.as_posix() in ref for evidence in all_evidence for ref in evidence.source_refs)
    review_evidence = next(evidence for evidence in all_evidence if evidence.evidence_type == "legacy_l4_review")
    _fm, review_body = read_md(ws.registry_dir("evidence") / f"{review_evidence.evidence_id}.md")
    assert "The review accepts the claim only within the recorded finite-size scope." in review_body

    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert {report.report_id for report in reports} == set(result["written_records"]["sensemaking_reports"])
    assert any("control sector" in report.summary for report in reports)


def test_legacy_migration_preserves_runtime_log_as_trace_events(tmp_path):
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.trace import read_trace_events
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    runtime_dir = legacy / "runtime"
    runtime_dir.mkdir()
    log = runtime_dir / "log.md"
    log.write_text(
        "# Topic Log\n\n"
        "## Events\n"
        "- 2026-05-17 L4_test_fail: negative control failed\n"
        "- 2026-05-18 session ended\n",
        encoding="utf-8",
    )
    before = log.read_text(encoding="utf-8")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    assert log.read_text(encoding="utf-8") == before
    assert result["written_records"]["trace_events"]
    events = read_trace_events(ws.root / "runtime" / "legacy_migration_trace.jsonl")
    assert [event.event_id for event in events] == result["written_records"]["trace_events"]
    assert [event.event_type for event in events] == ["legacy_runtime_log", "legacy_runtime_log"]
    assert events[0].topic_id == "legacy-fqhe"
    assert events[0].claim_id == result["active_claim_id"]
    assert events[0].payload["summary"] == "2026-05-17 L4_test_fail: negative control failed"
    assert log.as_posix() in events[0].payload["source_ref"]


def test_legacy_migration_preserves_l1_source_basis_and_conventions(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.markdown import read_md
    from brain.v5.models import SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    l1 = legacy / "L1"
    l1.mkdir()
    source_basis = l1 / "source_basis.md"
    conventions = l1 / "convention_snapshot.md"
    source_basis.write_text(
        "---\n"
        "summary: Counting paper is the primary source; lecture notes are background.\n"
        "---\n"
        "# Source Basis\n\nThe source roles separate benchmark data from pedagogical context.\n",
        encoding="utf-8",
    )
    conventions.write_text(
        "---\n"
        "summary: Magnetic length is set to one and edge momentum is counted relative to the ground sector.\n"
        "---\n"
        "# Convention Snapshot\n\nMagnetic length set to one; finite-size sectors use the same orbital cutoff.\n",
        encoding="utf-8",
    )
    before = conventions.read_text(encoding="utf-8")
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    assert conventions.read_text(encoding="utf-8") == before
    evidence = list_evidence_for_claim(ws, result["active_claim_id"])
    evidence_types = {item.evidence_type for item in evidence}
    assert {"legacy_l1_source_basis", "legacy_l1_convention_snapshot"} <= evidence_types
    assert any(source_basis.as_posix() in ref for item in evidence for ref in item.source_refs)
    assert any(conventions.as_posix() in ref for item in evidence for ref in item.source_refs)
    evidence_by_type = {item.evidence_type: item for item in evidence}
    _fm, source_basis_body = read_md(
        ws.registry_dir("evidence") / f"{evidence_by_type['legacy_l1_source_basis'].evidence_id}.md"
    )
    _fm, conventions_body = read_md(
        ws.registry_dir("evidence") / f"{evidence_by_type['legacy_l1_convention_snapshot'].evidence_id}.md"
    )
    assert "The source roles separate benchmark data from pedagogical context." in source_basis_body
    assert "finite-size sectors use the same orbital cutoff." in conventions_body

    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert {report.report_id for report in reports} >= set(result["written_records"]["sensemaking_reports"])
    assert any("Magnetic length is set to one" in report.summary for report in reports)


def test_legacy_migration_preserves_l1_derivation_anchors_and_contradictions(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
    from brain.v5.models import SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    l1 = legacy / "L1"
    l1.mkdir()
    anchors = l1 / "derivation_anchor_map.md"
    contradictions = l1 / "contradiction_register.md"
    anchors.write_text(
        "---\n"
        "summary: Eq. 3 anchors the edge-counting generating function to the finite-size table.\n"
        "---\n"
        "# Derivation Anchors\n\nEq. 3 is the source anchor for the generating function.\n",
        encoding="utf-8",
    )
    contradictions.write_text(
        "---\n"
        "summary: Paper B uses a shifted momentum convention that can mimic a mismatch.\n"
        "---\n"
        "# Contradiction Register\n\nThe shifted convention remains unresolved.\n",
        encoding="utf-8",
    )
    ws = init_workspace(tmp_path / "v5")

    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    evidence = list_evidence_for_claim(ws, result["active_claim_id"])
    evidence_types = {item.evidence_type for item in evidence}
    assert {"legacy_l1_derivation_anchor_map", "legacy_l1_contradiction_register"} <= evidence_types
    assert any(anchors.as_posix() in ref for item in evidence for ref in item.source_refs)
    assert any(contradictions.as_posix() in ref for item in evidence for ref in item.source_refs)

    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert any("edge-counting generating function" in report.summary for report in reports)
    assert any("shifted momentum convention" in report.summary for report in reports)


def test_legacy_migration_preserves_l1_question_contract_and_intake_notes(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import audit_legacy_topic_migration, migrate_legacy_topic_to_v5
    from brain.v5.models import SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    l1 = legacy / "L1"
    intake = l1 / "intake"
    intake.mkdir(parents=True)
    question = l1 / "question_contract.md"
    note = intake / "edge-paper.md"
    question.write_text(
        "---\n"
        "summary: Determine whether finite-size edge counting distinguishes the CFT sector.\n"
        "---\n"
        "# Question Contract\n\nBounded question: compare counting with CFT characters.\n",
        encoding="utf-8",
    )
    note.write_text(
        "---\n"
        "summary: The paper's counting table is useful, but its momentum convention is shifted.\n"
        "---\n"
        "# Intake Note\n\nRecord the convention shift before using the table.\n",
        encoding="utf-8",
    )

    audit = audit_legacy_topic_migration(legacy)
    assert audit["mapped_paths"]["L1/question_contract.md"] == "l1/question contract candidate"
    assert audit["mapped_paths"]["L1/intake/edge-paper.md"] == "l1/intake note candidate"

    ws = init_workspace(tmp_path / "v5")
    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    evidence = list_evidence_for_claim(ws, result["active_claim_id"])
    evidence_types = {item.evidence_type for item in evidence}
    assert {"legacy_l1_question_contract", "legacy_l1_intake_note"} <= evidence_types
    assert any(question.as_posix() in ref for item in evidence for ref in item.source_refs)
    assert any(note.as_posix() in ref for item in evidence for ref in item.source_refs)

    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert any("distinguishes the CFT sector" in report.summary for report in reports)
    assert any("momentum convention is shifted" in report.summary for report in reports)


def test_legacy_migration_preserves_l2_entries_as_legacy_seed_memory(tmp_path):
    from brain.v5.legacy_bridge import audit_legacy_topic_migration, migrate_legacy_topic_to_v5
    from brain.v5.models import MemoryEntryRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    l2 = legacy.parent / "L2"
    entries = l2 / "entries"
    nodes = l2 / "graph" / "nodes"
    edges = l2 / "graph" / "edges"
    entries.mkdir(parents=True)
    nodes.mkdir(parents=True)
    edges.mkdir(parents=True)
    entry = entries / "edge-counting-rule.md"
    node = nodes / "edge-cft.md"
    edge = edges / "counting-to-cft.md"
    entry.write_text(
        "---\n"
        "entry_id: edge-counting-rule\n"
        "role: claim\n"
        "title: Edge counting rule\n"
        "statement: Edge counting identifies the chiral CFT sector after convention alignment.\n"
        "status: verified\n"
        "regime: disk geometry\n"
        "source_ref: paper:counting\n"
        "---\n"
        "# Edge counting rule\n",
        encoding="utf-8",
    )
    node.write_text(
        "---\n"
        "node_id: edge-cft\n"
        "type: concept\n"
        "title: Chiral edge CFT\n"
        "physical_meaning: The low-energy edge sector is organized by chiral CFT characters.\n"
        "regime_of_validity: finite disk spectra\n"
        "source_ref: paper:cft\n"
        "---\n"
        "# Chiral edge CFT\n",
        encoding="utf-8",
    )
    edge.write_text(
        "---\n"
        "edge_id: counting-to-cft\n"
        "from_node: edge-counting-rule\n"
        "to_node: edge-cft\n"
        "type: uses\n"
        "source_ref: paper:bridge\n"
        "---\n"
        "# counting-to-cft\n",
        encoding="utf-8",
    )

    audit = audit_legacy_topic_migration(legacy)
    assert audit["mapped_paths"]["L2/entries/edge-counting-rule.md"] == "l2/memory entry candidate"
    assert audit["mapped_paths"]["L2/graph/nodes/edge-cft.md"] == "l2/graph node memory candidate"
    assert audit["mapped_paths"]["L2/graph/edges/counting-to-cft.md"] == "l2/graph edge memory candidate"

    ws = init_workspace(tmp_path / "v5")
    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    memories = list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
    assert {memory.entry_id for memory in memories} == set(result["written_records"]["memory_entries"])
    assert {memory.memory_kind for memory in memories} == {
        "legacy_l2_entry:claim",
        "legacy_l2_graph_node:concept",
        "legacy_l2_graph_edge:uses",
    }
    assert all(memory.status == "legacy_seed" for memory in memories)
    assert all(memory.source_claim_id == result["active_claim_id"] for memory in memories)
    assert all(memory.human_checkpoint_id == "legacy_migration_review_required" for memory in memories)
    assert all(memory.evidence_refs for memory in memories)
    assert any("chiral CFT sector" in memory.statement for memory in memories)
    assert any("edge-counting-rule --[uses]--> edge-cft" in memory.statement for memory in memories)


def test_legacy_migration_preserves_l3_process_notes_as_typed_records(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim
    from brain.v5.legacy_bridge import audit_legacy_topic_migration, migrate_legacy_topic_to_v5
    from brain.v5.markdown import read_md
    from brain.v5.models import SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.workspace import init_workspace

    legacy = _write_legacy_topic(tmp_path / "legacy")
    derive_dir = legacy / "L3" / "derive"
    gap_dir = legacy / "L3" / "gap-audit"
    diagnose_dir = legacy / "L3" / "diagnose"
    derive_dir.mkdir(parents=True)
    gap_dir.mkdir(parents=True)
    diagnose_dir.mkdir(parents=True)
    derivation = derive_dir / "active_derivation.md"
    gap_audit = gap_dir / "active_gaps.md"
    failed_route = diagnose_dir / "failed-route.md"
    derivation.write_text(
        "---\n"
        "summary: Kac-Moody edge counting was traced through the finite-size table.\n"
        "---\n"
        "# Active Derivation\n\nThe main route reconstructs the counting character step by step.\n",
        encoding="utf-8",
    )
    gap_audit.write_text(
        "---\n"
        "summary: The neutral-sector assumption is still missing from the source trace.\n"
        "---\n"
        "# Active Gaps\n\nMissing neutral-sector assumption before promoting the claim.\n",
        encoding="utf-8",
    )
    failed_route.write_text(
        "---\n"
        "summary: A wrong angular momentum shift explains the failed comparison route.\n"
        "---\n"
        "# Failed Route\n\nThis failed attempt should remain visible after migration.\n",
        encoding="utf-8",
    )

    audit = audit_legacy_topic_migration(legacy)
    assert audit["mapped_paths"]["L3/derive/active_derivation.md"] == "l3/derive process note candidate"
    assert audit["mapped_paths"]["L3/gap-audit/active_gaps.md"] == "l3/gap-audit process note candidate"
    assert audit["mapped_paths"]["L3/diagnose/failed-route.md"] == "l3/diagnose process note candidate"

    ws = init_workspace(tmp_path / "v5")
    result = migrate_legacy_topic_to_v5(
        ws,
        legacy,
        context_id="legacy-context",
        session_id="s1",
    )

    evidence = list_evidence_for_claim(ws, result["active_claim_id"])
    evidence_types = {item.evidence_type for item in evidence}
    assert {
        "legacy_l3_derive_process_note",
        "legacy_l3_gap_audit_process_note",
        "legacy_l3_diagnose_process_note",
    } <= evidence_types
    assert any(derivation.as_posix() in ref for item in evidence for ref in item.source_refs)
    assert any(gap_audit.as_posix() in ref for item in evidence for ref in item.source_refs)
    assert any(failed_route.as_posix() in ref for item in evidence for ref in item.source_refs)
    evidence_by_type = {item.evidence_type: item for item in evidence}
    _fm, derivation_body = read_md(
        ws.registry_dir("evidence")
        / f"{evidence_by_type['legacy_l3_derive_process_note'].evidence_id}.md"
    )
    _fm, gap_body = read_md(
        ws.registry_dir("evidence")
        / f"{evidence_by_type['legacy_l3_gap_audit_process_note'].evidence_id}.md"
    )
    _fm, failed_body = read_md(
        ws.registry_dir("evidence")
        / f"{evidence_by_type['legacy_l3_diagnose_process_note'].evidence_id}.md"
    )
    assert "The main route reconstructs the counting character step by step." in derivation_body
    assert "Missing neutral-sector assumption before promoting the claim." in gap_body
    assert "This failed attempt should remain visible after migration." in failed_body

    reports = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert {report.report_id for report in reports} >= set(result["written_records"]["sensemaking_reports"])
    assert any("Kac-Moody edge counting" in report.summary for report in reports)
    assert any("neutral-sector assumption" in report.summary for report in reports)
    assert any("wrong angular momentum shift" in report.summary for report in reports)
    assert any("review_legacy_l3_process_note" in report.next_actions for report in reports)
