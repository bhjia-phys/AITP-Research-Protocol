from __future__ import annotations

import json


def test_source_reconstruction_audit_reports_missing_components(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.source_reconstruction import audit_source_reconstruction
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source coverage",
    )

    payload = audit_source_reconstruction(ws, claim_id=claim.claim_id)

    assert payload["kind"] == "source_reconstruction_audit"
    assert payload["complete"] is False
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert set(payload["missing_components"]) == {
        "definitions",
        "assumptions_or_scope",
        "source_locations",
        "dependency_graph",
        "reconstruction_path",
        "failure_conditions",
    }
    assert require_valid_public_surface("source_reconstruction_audit", payload) == payload


def test_source_reconstruction_audit_accepts_typed_source_stack(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.source_reconstruction import audit_source_reconstruction
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT in the recorded sector.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
        scope="Fixed sector, finite-size counting table.",
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
        assumptions=["fixed particle number"],
        source_refs=["paper:fqhe-counting"],
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate chiral edge conformal field theory.",
        source_refs=["paper:fqhe-counting"],
    )
    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence matches the edge CFT character.",
        claim_id=claim.claim_id,
        assumptions=["same sector convention"],
        failure_modes=["wrong sector assignment"],
        source_refs=["paper:fqhe-counting"],
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="Definition, sector convention, and counting comparison are reconstructable from the cited source.",
        supports_outputs=["reconstruction_path"],
        source_refs=["paper:fqhe-counting"],
    )

    payload = audit_source_reconstruction(ws, claim_id=claim.claim_id)

    assert payload["complete"] is True
    assert payload["missing_components"] == []
    assert payload["source_refs"] == ["paper:fqhe-counting"]
    assert payload["components"]["definitions"]["record_ids"] == [counting.object_id, cft.object_id]
    assert payload["components"]["dependency_graph"]["record_ids"] == [relation.relation_id]
    assert payload["components"]["reconstruction_path"]["record_ids"] == [evidence.evidence_id]


def test_source_reconstruction_audit_cli_mcp_and_runtime(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_source_reconstruction
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source coverage",
    )

    assert main(["--base", str(tmp_path), "source", "reconstruction-audit", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_source_reconstruction(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["kind"] == "source_reconstruction_audit"
    assert mcp_payload["kind"] == "source_reconstruction_audit"
    assert runtime_entrypoints()["source_reconstruction_audit"]["mcp"] == "aitp_v5_audit_source_reconstruction"
