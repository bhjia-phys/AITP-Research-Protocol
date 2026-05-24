from __future__ import annotations

import json


def _seed_memory(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
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
    return ws, claim, evidence, memory


def test_l2_obsidian_view_writes_orientation_only_memory_notes(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.obsidian_views import write_l2_obsidian_view
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, evidence, memory = _seed_memory(tmp_path)

    payload = write_l2_obsidian_view(ws)

    assert payload["kind"] == "l2_obsidian_view_bundle"
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert payload["memory_entry_count"] == 1
    assert payload["source_records"]["memory_entries"] == [memory.entry_id]
    assert payload["source_records"]["claims"] == [claim.claim_id]
    assert payload["source_records"]["evidence"] == [evidence.evidence_id]
    assert require_valid_public_surface("l2_obsidian_view_bundle", payload) == payload

    overview_fm, overview = read_md(payload["files"]["overview"])
    entry_fm, entry = read_md(payload["files"]["entries"][0])
    assert overview_fm["truth_source"] is False
    assert entry_fm["orientation_only"] is True
    assert memory.entry_id in overview
    assert claim.statement in entry
    assert evidence.evidence_id in entry
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
