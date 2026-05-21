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
