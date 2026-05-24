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

    ws, claim, gw_claim, _ = _seed_replay_workspace(tmp_path)

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

    complete = next(entry for entry in packet.entries if entry["claim_id"] == claim.claim_id)
    incomplete = next(entry for entry in packet.entries if entry["claim_id"] == gw_claim.claim_id)
    assert complete["source_reconstruction_complete"] is True
    assert complete["missing_source_components"] == []
    assert incomplete["source_reconstruction_complete"] is False
    assert "definitions" in incomplete["missing_source_components"]
    assert incomplete["attention_reasons"]

    _, body = read_md(packet.files["replay_packet"])
    assert "Workspace Replay Packet" in body
    assert claim.claim_id in body
    assert gw_claim.claim_id in body
    assert "orientation only" in body


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
