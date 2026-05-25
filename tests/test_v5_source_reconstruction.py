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


def test_source_reconstruction_manifest_prioritizes_incomplete_claims(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.references import record_reference_location
    from brain.v5.source_reconstruction import build_source_reconstruction_manifest
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    incomplete = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source coverage",
    )
    complete = create_claim(
        ws,
        topic_id="fqhe",
        statement="The source stack is reconstructable in the recorded sector.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="sector mismatch",
        scope="Fixed sector only.",
        strongest_failure_mode="wrong sector assignment",
    )
    record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=complete.claim_id,
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
        definition="Candidate chiral edge CFT.",
        source_refs=["paper:fqhe-counting"],
    )
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence matches the edge CFT character.",
        claim_id=complete.claim_id,
        assumptions=["same sector convention"],
        failure_modes=["wrong sector assignment"],
        source_refs=["paper:fqhe-counting"],
    )
    record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=complete.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="The typed source stack reconstructs the claim.",
        supports_outputs=["reconstruction_path"],
        source_refs=["paper:fqhe-counting"],
    )

    manifest = build_source_reconstruction_manifest(ws)

    assert manifest["kind"] == "source_reconstruction_manifest"
    assert manifest["claim_count"] == 2
    assert manifest["complete_claim_count"] == 1
    assert manifest["incomplete_claim_count"] == 1
    assert manifest["can_update_claim_trust"] is False
    assert manifest["can_update_kernel_state"] is False
    assert manifest["truth_source"] == "typed_records"
    assert manifest["next_actions"] == [f"source_reconstruction:{incomplete.claim_id}"]
    by_claim = {item["claim_id"]: item for item in manifest["items"]}
    assert by_claim[incomplete.claim_id]["status"] == "incomplete"
    assert by_claim[incomplete.claim_id]["review_priority"] == "high"
    assert "record_reference_location" in by_claim[incomplete.claim_id]["recommended_actions"]
    assert "aitp-v5 source reconstruction-audit --claim" in by_claim[incomplete.claim_id]["audit_cli"]
    assert by_claim[complete.claim_id]["status"] == "complete"
    assert by_claim[complete.claim_id]["review_priority"] == "low"
    assert require_valid_public_surface("source_reconstruction_manifest", manifest) == manifest


def test_source_reconstruction_manifest_reports_empty_migrated_claim_statements(tmp_path):
    from brain.v5.models import ClaimRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.source_reconstruction import build_source_reconstruction_manifest
    from brain.v5.store import write_record
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "legacy-topic", context_id="legacy-context", title="Legacy Topic")
    write_record(
        ws.registry_dir("claims") / "claim-empty.md",
        ClaimRecord(
            claim_id="claim-empty",
            topic_id="legacy-topic",
            statement="",
            evidence_profile="legacy_import",
            confidence_state="legacy_seed",
            active_uncertainty="semantic review required",
        ),
    )

    manifest = build_source_reconstruction_manifest(ws)

    assert manifest["items"][0]["claim_id"] == "claim-empty"
    assert manifest["items"][0]["claim_statement"] == ""
    assert manifest["items"][0]["status"] == "incomplete"
    assert require_valid_public_surface("source_reconstruction_manifest", manifest) == manifest


def test_source_reconstruction_manifest_counts_missing_components_across_claims(tmp_path):
    from brain.v5.source_reconstruction import build_source_reconstruction_manifest
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "empty-topic", context_id="legacy-context", title="Empty")
    create_topic(ws, "scoped-topic", context_id="legacy-context", title="Scoped")
    create_claim(
        ws,
        topic_id="empty-topic",
        statement="The empty claim has no typed source stack yet.",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="semantic review required",
    )
    create_claim(
        ws,
        topic_id="scoped-topic",
        statement="The scoped claim records only scope so far.",
        evidence_profile="legacy_import",
        confidence_state="legacy_seed",
        active_uncertainty="semantic review required",
        scope="Finite systems only.",
    )

    manifest = build_source_reconstruction_manifest(ws)

    assert manifest["missing_component_counts"] == {
        "definitions": 2,
        "assumptions_or_scope": 1,
        "source_locations": 2,
        "dependency_graph": 2,
        "reconstruction_path": 2,
        "failure_conditions": 2,
    }


def test_source_reconstruction_manifest_cli_mcp_and_runtime(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_source_reconstruction_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence identifies the edge CFT.",
        evidence_profile="literature",
        confidence_state="hypothesis",
        active_uncertainty="source coverage",
    )

    assert main(["--base", str(tmp_path), "source", "reconstruction-manifest"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_source_reconstruction_manifest(str(tmp_path))

    assert cli_payload["kind"] == "source_reconstruction_manifest"
    assert cli_payload["incomplete_claim_count"] == 1
    assert mcp_payload["ok"] is True
    assert mcp_payload["kind"] == "source_reconstruction_manifest"
    assert runtime_entrypoints()["source_reconstruction_manifest"] == {
        "cli": "aitp-v5 source reconstruction-manifest",
        "mcp": "aitp_v5_build_source_reconstruction_manifest",
        "surface": "source_reconstruction_manifest",
    }
