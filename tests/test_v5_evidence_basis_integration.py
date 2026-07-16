from __future__ import annotations

import json
from dataclasses import asdict, replace

import pytest


def _setup(tmp_path):
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="A source-grounded scoped claim.",
        evidence_profile="literature_derivation",
        confidence_state="hypothesis",
        active_uncertainty="The exact source interpretation needs review.",
    )
    actor = RecordActor(actor_type="tool", actor_id="evidence-basis-integration", host="pytest")
    repository = RecordRepository(ws, actor=actor)
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="paper",
            topic_id="qg",
            asset_type="paper",
            uri="file:///paper.pdf",
            title="Paper",
            content_hash="a" * 64,
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id="equation-3",
            topic_id="qg",
            connector_id="local-source",
            location_type="equation_anchor",
            uri="file:///paper.pdf#eq=3",
            label="Equation 3",
            source_ref="source_asset:paper",
        ),
    )
    pins = [
        pin_current_record(ws, "source_asset:paper"),
        pin_current_record(ws, "reference_location:equation-3"),
    ]
    return ws, claim, pins


def test_evidence_writer_persists_payload_bound_basis_audit(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws, claim, pins = _setup(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="Equation 3 supports the statement within the declared regime.",
        support_basis_refs=pins,
        trace_context_refs=[],
    )
    loaded = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="reader", host="pytest"),
    ).read(f"evidence:{evidence.evidence_id}").record

    assert loaded.basis_policy_status == "admissible"
    assert loaded.basis_audit["admissible"] is True
    assert loaded.basis_payload_hash == loaded.basis_audit["payload_hash"]
    assert len(loaded.basis_audit["audit_hash"]) == 64
    assert loaded.basis_audit["ref_audits"][0]["role"] == "support"
    assert loaded.support_basis_refs[0]["record_ref"] == "source_asset:paper"
    assert loaded.can_update_claim_trust is False

    from brain.v5.evidence_basis_policy import persisted_evidence_basis_is_admissible

    tampered = replace(
        loaded,
        basis_audit={**loaded.basis_audit, "checked_refs": []},
    )
    assert persisted_evidence_basis_is_admissible(ws, tampered) is False


def test_trust_audit_excludes_legacy_unchecked_support(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.trust_audit import audit_claim_trust

    ws, claim, pins = _setup(tmp_path)
    legacy = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="legacy_note",
        status="supports_scoped_claim",
        summary="A pre-policy support record.",
    )
    admissible = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="Exact source support.",
        support_basis_refs=pins,
        trace_context_refs=[],
    )

    audit = audit_claim_trust(ws, claim_id=claim.claim_id)

    assert legacy.basis_policy_status == "legacy_unchecked"
    assert audit["supporting_evidence_refs"] == [admissible.evidence_id]
    assert audit["inadmissible_supporting_evidence_refs"] == [legacy.evidence_id]


def test_pretool_and_memory_promotion_reject_legacy_unchecked_evidence(tmp_path):
    import pytest

    from brain.v5.evidence import record_evidence
    from brain.v5.memory import create_promotion_packet
    from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
    from brain.v5.workspace import bind_session

    ws, claim, _pins = _setup(tmp_path)
    bind_session(ws, "s1", topic_id="qg", context_id="formal-theory", active_claim=claim.claim_id)
    legacy = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="legacy_note",
        status="supports_scoped_claim",
        summary="Unchecked support must not authorize promotion.",
    )

    decision = evaluate_context_pre_tool_policy(
        ws,
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=[legacy.evidence_id],
        risk_level="rigorous",
    )

    assert decision["mode"] == "block"
    assert decision["block"] is True
    assert any(
        reason["policy_id"] == "inadmissible_evidence_basis"
        for reason in decision["policy_reasons"]
    )
    with pytest.raises(ValueError, match="admissible evidence basis"):
        create_promotion_packet(
            ws,
            topic_id="qg",
            claim_id=claim.claim_id,
            scope="A scope that cannot inherit unchecked evidence.",
            evidence_refs=[legacy.evidence_id],
            known_failure_modes=["source interpretation mismatch"],
        )


def test_full_mcp_accepts_structured_exact_basis_refs(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_evidence
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws, claim, pins = _setup(tmp_path)
    payload = aitp_v5_record_evidence(
        str(tmp_path),
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="MCP exact source support.",
        support_basis_refs=[asdict(pin) for pin in pins],
        trace_context_refs=[],
        body="Exact quoted derivation context.",
    )

    assert payload["basis_policy_status"] == "admissible"
    assert payload["support_basis_refs"] == [asdict(pin) for pin in pins]
    loaded = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="mcp-body-reader", host="pytest"),
    ).read(f"evidence:{payload['evidence_id']}")
    assert loaded.body == "Exact quoted derivation context."


@pytest.mark.parametrize("revision", [True, 1.5, "1"])
def test_exact_basis_input_rejects_non_integer_revisions(revision):
    from brain.v5.evidence_basis_inputs import coerce_pinned_record_refs

    with pytest.raises(ValueError, match="revision must be an integer"):
        coerce_pinned_record_refs(
            [
                {
                    "record_ref": "source_asset:paper",
                    "content_hash": "a" * 64,
                    "revision": revision,
                }
            ],
            field_name="support_basis_refs",
        )


@pytest.mark.parametrize("revision", [True, 1.5])
def test_persisted_basis_rejects_non_integer_revisions(tmp_path, revision):
    from brain.v5.evidence import record_evidence
    from brain.v5.evidence_basis_policy import persisted_evidence_basis_is_admissible

    ws, claim, pins = _setup(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="Pinned support before tampering.",
        support_basis_refs=pins,
        trace_context_refs=[],
    )
    tampered_pin = {**evidence.support_basis_refs[0], "revision": revision}
    tampered = replace(
        evidence,
        support_basis_refs=[tampered_pin, *evidence.support_basis_refs[1:]],
    )

    assert persisted_evidence_basis_is_admissible(ws, tampered) is False
def test_cli_accepts_file_backed_exact_basis_refs(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws, claim, pins = _setup(tmp_path)
    basis_file = tmp_path / "support-basis.json"
    basis_file.write_text(json.dumps([asdict(pin) for pin in pins]), encoding="utf-8")
    body_file = tmp_path / "evidence-body.md"
    body_file.write_text("CLI derivation context.\n", encoding="utf-8")

    result = main(
        [
            "--base",
            str(tmp_path),
            "evidence",
            "record",
            "--topic",
            "qg",
            "--claim",
            claim.claim_id,
            "--type",
            "literature_equation",
            "--status",
            "supports_scoped_claim",
            "--summary",
            "CLI exact source support.",
            "--support-basis-json-file",
            str(basis_file),
            "--body-file",
            str(body_file),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["basis_policy_status"] == "admissible"
    assert payload["support_basis_refs"] == [asdict(pin) for pin in pins]
    loaded = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="cli-body-reader", host="pytest"),
    ).read(f"evidence:{payload['evidence_id']}")
    assert loaded.body == "CLI derivation context.\n"


def test_runtime_bridge_declares_evidence_basis_arguments():
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest

    manifest = runtime_bridge_target_manifest()
    target = next(
        item
        for item in manifest["targets"]
        if item["operation"] == "recordEvidence"
    )

    assert require_valid_public_surface("runtime_bridge_target_manifest", manifest) == manifest
    assert target["mcp_arguments"]["required"] == [
        "base",
        "topic_id",
        "claim_id",
        "evidence_type",
        "status",
        "summary",
    ]
    assert "support_basis_refs" in target["mcp_arguments"]["optional"]
    assert "trace_context_refs" in target["mcp_arguments"]["optional"]
    assert "body" in target["mcp_arguments"]["optional"]


def test_evidence_family_declares_v2_exact_basis_dependencies():
    from brain.v5.record_family_registry import spec_for_family

    spec = spec_for_family("evidence")

    assert spec.schema_version == "v2"
    assert spec.dependency_fields == (
        "support_basis_refs",
        "trace_context_refs",
    )


def test_evidence_dependency_manifest_preserves_exact_basis_hash_and_revision(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.models import SourceAssetRecord
    from brain.v5.pinned_record_refs import (
        build_frozen_dependency_manifest,
        pin_current_record,
    )
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy
    from brain.v5.evidence_basis_policy import persisted_evidence_basis_is_admissible

    ws, claim, pins = _setup(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="Dependency closure exact source support.",
        support_basis_refs=pins,
        trace_context_refs=[],
    )
    RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="source-reviser", host="pytest"),
    ).write(
        "source_assets",
        SourceAssetRecord(
            asset_id="paper",
            topic_id="qg",
            asset_type="paper",
            uri="file:///paper.pdf",
            title="Paper revised after evidence capture",
            content_hash="c" * 64,
            hash_algorithm="sha256",
        ),
        policy=WritePolicy(mode="revision", expected_hash=pins[0].content_hash),
    )
    manifest = build_frozen_dependency_manifest(
        ws, [pin_current_record(ws, f"evidence:{evidence.evidence_id}")]
    )

    edges = {edge.target_ref: edge for edge in manifest.edges}
    for pin in pins:
        assert edges[pin.record_ref].target_hash == pin.content_hash
        assert edges[pin.record_ref].target_revision == pin.revision
    assert persisted_evidence_basis_is_admissible(ws, evidence) is True
    with pytest.raises(ValueError, match="inadmissible evidence basis"):
        record_evidence(
            ws,
            topic_id="qg",
            claim_id=claim.claim_id,
            evidence_type="stale_explicit_pin",
            status="supports_scoped_claim",
            summary="A new write cannot submit a stale source pin.",
            support_basis_refs=pins,
            trace_context_refs=[],
        )


def test_evidence_public_surface_rejects_trust_inflation_and_tampered_basis_hash(tmp_path):
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.evidence import record_evidence
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, pins = _setup(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports_scoped_claim",
        summary="Contracted exact source support.",
        support_basis_refs=pins,
        trace_context_refs=[],
    )
    payload = {"ok": True, **asdict(evidence)}

    with pytest.raises(ContractError, match="can_update_claim_trust"):
        require_valid_public_surface(
            "evidence_record", {**payload, "can_update_claim_trust": True}
        )
    with pytest.raises(ContractError, match="basis_payload_hash"):
        require_valid_public_surface(
            "evidence_record", {**payload, "basis_payload_hash": "0" * 64}
        )
    tampered_audit = {**payload["basis_audit"], "checked_refs": []}
    with pytest.raises(ContractError, match="audit_hash"):
        require_valid_public_surface(
            "evidence_record", {**payload, "basis_audit": tampered_audit}
        )


def test_exact_tool_run_basis_is_recordable_but_not_trust_admissible_without_validation(
    tmp_path,
):
    from brain.v5.evidence import record_evidence
    from brain.v5.evidence_basis_policy import (
        persisted_evidence_basis_is_admissible,
        persisted_evidence_basis_is_trust_admissible,
    )
    from brain.v5.tools import record_tool_run

    ws, claim, _pins = _setup(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="qg-checklist",
        tool_family="formal_theory",
        tool_name="checklist",
        topic_id="qg",
        claim_id=claim.claim_id,
        outputs={"all_checked": True},
    )
    evidence = record_evidence(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        evidence_type="formal_theory_check",
        status="supports_scoped_claim",
        summary="The checklist ran, but no validation result exists yet.",
        tool_run_ids=[run.run_id],
    )

    assert persisted_evidence_basis_is_admissible(ws, evidence) is True
    assert persisted_evidence_basis_is_trust_admissible(ws, evidence) is False
