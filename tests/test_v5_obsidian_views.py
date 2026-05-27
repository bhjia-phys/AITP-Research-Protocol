from __future__ import annotations

import json


def _seed_memory(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence is reusable only inside the recorded sector.",
        evidence_profile="literature",
        confidence_state="locally_checked",
        active_uncertainty="sector convention",
        scope="Recorded finite-size sector.",
        strongest_failure_mode="wrong sector assignment",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="The sector convention and counting definition are recorded.",
        supports_outputs=["evidence_or_provenance"],
        source_refs=["paper:fqhe-counting"],
    )
    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="counting sequence",
        definition="Degeneracy sequence in the fixed sector.",
        source_refs=["paper:fqhe-counting"],
    )
    sector = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="scope",
        name="recorded sector",
        definition="The finite-size sector covered by the checked source.",
        source_refs=["paper:fqhe-counting"],
    )
    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="scoped_by",
        subject_id=counting.object_id,
        object_id=sector.object_id,
        statement="The counting sequence is reusable only inside the recorded sector.",
        claim_id=claim.claim_id,
        source_refs=["paper:fqhe-counting"],
        evidence_refs=[evidence.evidence_id],
    )
    report = record_sensemaking_report(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        title="Sector-scoped L2 interpretation",
        summary="The reusable unit is the sector-scoped counting relation, not an unrestricted counting claim.",
        object_ids=[counting.object_id, sector.object_id],
        relation_ids=[relation.relation_id],
        evidence_refs=[evidence.evidence_id],
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="Recorded finite-size sector.",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["wrong sector assignment"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Approve reusable L2 memory.",
        requested_by="obsidian_view_test",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Scope and failure mode are explicit.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)
    return ws, claim, evidence, memory, (counting, sector), relation, report


def test_l2_obsidian_view_writes_orientation_only_memory_notes(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.obsidian_views import write_l2_obsidian_view
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, evidence, memory, objects, relation, report = _seed_memory(tmp_path)

    payload = write_l2_obsidian_view(ws)

    assert payload["kind"] == "l2_obsidian_view_bundle"
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert payload["memory_entry_count"] == 1
    assert payload["physics_object_count"] == 2
    assert payload["object_relation_count"] == 1
    assert payload["sensemaking_report_count"] == 1
    assert payload["source_records"]["memory_entries"] == [memory.entry_id]
    assert payload["source_records"]["claims"] == [claim.claim_id]
    assert payload["source_records"]["evidence"] == [evidence.evidence_id]
    assert payload["source_records"]["physics_objects"] == [obj.object_id for obj in objects]
    assert payload["source_records"]["object_relations"] == [relation.relation_id]
    assert payload["source_records"]["sensemaking_reports"] == [report.report_id]
    assert require_valid_public_surface("l2_obsidian_view_bundle", payload) == payload

    overview_fm, overview = read_md(payload["files"]["overview"])
    entry_fm, entry = read_md(payload["files"]["entries"][0])
    graph_fm, graph = read_md(payload["files"]["graph"])
    assert overview_fm["truth_source"] is False
    assert entry_fm["orientation_only"] is True
    assert graph_fm["view_role"] == "l2_graph_overview"
    assert memory.entry_id in overview
    assert relation.relation_id in overview
    assert "Typed Graph" in overview
    assert claim.statement in entry
    assert evidence.evidence_id in entry
    assert "Linked Physics Objects" in entry
    assert objects[0].object_id in entry
    assert relation.relation_id in entry
    assert report.report_id in entry
    assert objects[0].name in graph
    assert relation.statement in graph
    assert report.title in graph
    assert "Use typed AITP records for trust updates" in entry


def test_l2_obsidian_view_cli_mcp_and_runtime(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_write_l2_obsidian_view
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    _seed_memory(tmp_path)

    assert main(["--base", str(tmp_path), "memory", "obsidian-view"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_write_l2_obsidian_view(str(tmp_path))

    assert cli_payload["kind"] == "l2_obsidian_view_bundle"
    assert cli_payload["truth_source"] is False
    assert mcp_payload["kind"] == "l2_obsidian_view_bundle"
    assert runtime_entrypoints()["l2_obsidian_view"]["mcp"] == "aitp_v5_write_l2_obsidian_view"
