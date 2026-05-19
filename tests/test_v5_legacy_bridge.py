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
