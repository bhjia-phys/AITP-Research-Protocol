from __future__ import annotations


def _write_accounting_legacy_topics(root):
    from brain.v5.markdown import write_md, write_text_atomic

    canonical = root / "canonical-topic"
    (canonical / "L0" / "sources" / "paper-a").mkdir(parents=True)
    (canonical / "L3" / "candidates").mkdir(parents=True)
    write_md(
        canonical / "state.md",
        {
            "title": "Canonical Topic",
            "question": "What is the migrated claim?",
            "stage": "L3",
            "lane": "formal_theory",
        },
        "# Canonical Topic\n",
    )
    write_md(
        canonical / "L0" / "sources" / "paper-a" / "source.md",
        {"title": "Paper A"},
        "# Paper A\n",
    )
    write_md(
        canonical / "L3" / "candidates" / "candidate-a.md",
        {"claim": "The canonical topic has a migrated claim."},
        "# Candidate A\n",
    )

    source_only = root / "source-only-topic"
    write_text_atomic(source_only / "research.md", "# Source-only Topic\n\nPreserved note.\n")
    return canonical, source_only


def test_legacy_migration_accounting_run_unblocks_audit_and_review_queue(tmp_path):
    from brain.v5.legacy_migration_accounting import write_legacy_migration_accounting_run
    from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
    from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_claim, create_context, create_topic, init_workspace

    base = tmp_path / "topics"
    canonical, _source_only = _write_accounting_legacy_topics(base)
    ws = init_workspace(base)
    create_context(ws, "ctx", title="Context")
    create_topic(ws, canonical.name, context_id="ctx", title="Canonical Topic")
    claim = create_claim(
        ws,
        topic_id=canonical.name,
        statement="The canonical topic has a migrated claim.",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="Semantic review is still required.",
    )

    run = write_legacy_migration_accounting_run(ws, legacy_root=base, run_id="legacy-v5-lossless-accounting-test")
    assert (run / "migration_summary.json").exists()
    assert (run / "verification_report.json").exists()
    assert (run / "file_manifest.json").exists()

    audit = audit_legacy_migration_coverage(ws, migration_dir=run)
    assert audit["kind"] == "legacy_migration_coverage_audit"
    assert audit["coverage_status"] == "accounted_needs_review"
    assert audit["topic_count"] == 2
    assert audit["file_preservation"]["ok"] is True
    assert audit["semantic_lossless_proven"] is False
    assert audit["can_update_claim_trust"] is False
    by_topic = {topic["topic"]: topic for topic in audit["topics"]}
    assert by_topic[canonical.name]["active_claim_id"] == claim.claim_id
    assert by_topic["source-only-topic"]["legacy_shape"] == "noncanonical_seed"
    assert require_valid_public_surface("legacy_migration_coverage_audit", audit) == audit

    queue = build_legacy_semantic_review_queue(ws, migration_dir=run)
    assert queue["queue_status"] == "ready_for_semantic_review"
    assert queue["review_item_count"] == 2
    assert queue["semantic_lossless_proven"] is False
    assert require_valid_public_surface("legacy_semantic_review_queue", queue) == queue


def test_legacy_migration_accounting_run_cli_mcp_and_runtime_surface(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_legacy_migration_accounting_run
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import init_workspace

    base = tmp_path / "topics"
    _write_accounting_legacy_topics(base)
    init_workspace(base)

    assert main([
        "--base",
        str(base),
        "legacy",
        "migration-accounting-run",
        "--legacy-root",
        str(base),
        "--run-id",
        "legacy-v5-lossless-accounting-cli",
        "--compact",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["kind"] == "legacy_migration_coverage_audit_progress"
    assert cli_payload["coverage_status"] == "accounted_needs_review"
    assert cli_payload["semantic_lossless_proven"] is False

    mcp_payload = aitp_v5_write_legacy_migration_accounting_run(
        str(base),
        legacy_root=str(base),
        run_id="legacy-v5-lossless-accounting-mcp",
    )
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "legacy_migration_coverage_audit"
    entrypoint = runtime_entrypoints()["write_legacy_migration_accounting_run"]
    assert entrypoint["surface"] == "legacy_migration_coverage_audit"
    assert entrypoint["mcp"] == "aitp_v5_write_legacy_migration_accounting_run"


def test_legacy_migration_accounting_run_keeps_malformed_topic_as_gap(tmp_path):
    from brain.v5.legacy_migration_accounting import write_legacy_migration_accounting_run
    from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
    from brain.v5.markdown import write_text_atomic
    from brain.v5.workspace import init_workspace

    base = tmp_path / "topics"
    broken = base / "broken-topic" / "L0" / "sources" / "bad"
    broken.mkdir(parents=True)
    write_text_atomic(
        broken / "source.md",
        "---\ntitle: bad: yaml\n---\n# Bad Source\n",
    )
    ws = init_workspace(base)

    run = write_legacy_migration_accounting_run(ws, legacy_root=base, run_id="legacy-v5-lossless-broken")
    audit = audit_legacy_migration_coverage(ws, migration_dir=run)

    assert audit["coverage_status"] == "coverage_gaps"
    assert audit["gap_topics"] == ["broken-topic"]
    assert audit["topics"][0]["status"] == "audit_gaps"
    assert audit["topics"][0]["accounted_file_count"] == 1
