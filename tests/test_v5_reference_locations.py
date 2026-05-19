from __future__ import annotations

import json


def test_record_reference_location_persists_orientation_only_pointer(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Composite-fermion literature conventions must be checked against notes.",
        evidence_profile="literature_synthesis",
        confidence_state="learning",
        active_uncertainty="note location and source convention provenance",
    )

    location = record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="ima",
        location_type="external_note",
        uri="ima://note/fqhe-composite-fermion",
        label="FQHE composite-fermion reading notes",
        source_ref="paper:jain-1989",
        external_id="fqhe-composite-fermion",
        summary="Pointer to prior notes; not evidence by itself.",
        metadata={"backend": "ima", "collection": "fqhe"},
        linked_records={"claim_id": claim.claim_id},
    )

    fm, body = read_md(ws.registry_dir("reference_locations") / f"{location.location_id}.md")
    assert location.kind == "reference_location"
    assert location.orientation_only is True
    assert location.connector_id == "ima"
    assert location.location_type == "external_note"
    assert location.uri == "ima://note/fqhe-composite-fermion"
    assert fm["orientation_only"] is True
    assert fm["source_ref"] == "paper:jain-1989"
    assert fm["metadata"]["backend"] == "ima"
    assert "not evidence by itself" in body


def test_reference_location_record_is_public_surface_valid(tmp_path):
    from dataclasses import asdict

    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")

    location = record_reference_location(
        ws,
        topic_id="qg",
        connector_id="zotero",
        location_type="paper_pdf",
        uri="zotero://select/items/ABC123",
        label="Background-independent observables PDF",
        source_ref="zotero:ABC123",
    )
    payload = {"ok": True, **asdict(location)}

    assert require_valid_public_surface("reference_location_record", payload) == payload


def test_cli_reference_location_record_returns_json(tmp_path, capsys):
    from brain.v5.cli import main

    assert (
        main(
            [
                "--base",
                str(tmp_path),
                "reference",
                "location",
                "record",
                "--topic",
                "fqhe",
                "--claim",
                "claim-fqhe",
                "--connector",
                "local_pdf",
                "--type",
                "paper_pdf",
                "--uri",
                "file:///papers/fqhe/counting.pdf",
                "--label",
                "FQHE counting PDF",
                "--source-ref",
                "paper:fqhe-counting",
                "--metadata-json",
                '{"vault":"local"}',
            ]
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["kind"] == "reference_location"
    assert payload["orientation_only"] is True
    assert payload["connector_id"] == "local_pdf"
    assert payload["metadata"] == {"vault": "local"}


def test_mcp_record_reference_location_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_reference_location
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_record_reference_location(
        str(tmp_path),
        topic_id="fqhe",
        claim_id="claim-fqhe",
        connector_id="obsidian",
        location_type="external_note",
        uri="obsidian://open?vault=Physics&file=FQHE",
        label="FQHE Obsidian note",
        source_ref="note:fqhe",
    )

    assert payload["ok"] is True
    assert payload["kind"] == "reference_location"
    assert require_valid_public_surface("reference_location_record", payload) == payload


def test_adapter_protocol_advertises_reference_location_recording():
    from brain.v5.adapter_protocols import mandatory_record_protocols
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    protocol = mandatory_record_protocols()["record_reference_location"]

    assert protocol["entrypoint"] == "aitp_v5_record_reference_location"
    assert protocol["required_typed_refs"] == ["topic_id", "connector_id", "uri"]
    assert "source_ref" in protocol["accepted_link_fields"]
    assert runtime_entrypoints()["record_reference_location"]["surface"] == "reference_location_record"
