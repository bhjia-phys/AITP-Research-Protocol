from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="test-source-acquisition", host="pytest")


def _setup_workspace(tmp_path):
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    create_topic(ws, "other", context_id="theory", title="Other topic")
    return ws


def _allow_decision(ws, **overrides):
    from brain.v5.source_acquisition import record_source_acquisition_decision

    values = {
        "topic_id": "qg",
        "claim_id": "claim-1",
        "canonical_uri": "https://example.org/paper.pdf",
        "dedup_key": "doi:10.1000/example",
        "action": "allow",
        "policy_basis": "institutional-access",
        "access_disposition": "licensed",
        "storage_permission": "local-research-copy",
        "connector_id": "crossref",
        "collector_id": "pdf-collector",
        "decided_at": "2026-01-01T00:00:00+00:00",
        "expires_at": "2030-01-01T00:00:00+00:00",
        "actor": _actor(),
    }
    values.update(overrides)
    return record_source_acquisition_decision(ws, **values)


def _successful_receipt(ws, decision, **overrides):
    from brain.v5.source_acquisition import record_source_acquisition_receipt

    values = {
        "topic_id": "qg",
        "claim_id": "claim-1",
        "decision_ref": decision.pinned_ref,
        "canonical_uri": "https://example.org/paper.pdf",
        "dedup_key": "doi:10.1000/example",
        "status": "succeeded",
        "byte_sha256": "a" * 64,
        "hash_algorithm": "sha256",
        "byte_length": 123,
        "stored_uri": "file:///canonical/source-blobs/example.pdf",
        "connector_id": "crossref",
        "collector_id": "pdf-collector",
        "acquired_at": "2026-01-02T00:00:00+00:00",
        "errors": [],
        "actor": _actor(),
    }
    values.update(overrides)
    return record_source_acquisition_receipt(ws, **values)


def test_allow_decision_and_successful_receipt_resolve_by_exact_pins(tmp_path):
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest
    from brain.v5.record_family_registry import record_family_specs
    from brain.v5.source_acquisition import resolve_source_acquisition_for_source_asset

    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws)
    receipt = _successful_receipt(ws, decision)

    resolved = resolve_source_acquisition_for_source_asset(ws, receipt.pinned_ref)
    closure = build_frozen_dependency_manifest(ws, [receipt.pinned_ref])

    assert resolved.decision == decision.record
    assert resolved.receipt == receipt.record
    assert resolved.decision_ref == decision.pinned_ref
    assert resolved.receipt_ref == receipt.pinned_ref
    assert {node.record_ref for node in closure.nodes} == {
        decision.pinned_ref.record_ref,
        receipt.pinned_ref.record_ref,
    }
    assert [(edge.field_name, edge.target_ref) for edge in closure.edges] == [
        ("decision_ref", decision.pinned_ref.record_ref)
    ]
    assert receipt.record.decision_ref == {
        "record_ref": decision.pinned_ref.record_ref,
        "content_hash": decision.pinned_ref.content_hash,
        "revision": decision.pinned_ref.revision,
    }
    for family in ("source_acquisition_decisions", "source_acquisition_receipts"):
        spec = record_family_specs()[family]
        assert spec.schema_version == "v2"
        assert spec.lifecycle_policy == "append_only"
        assert spec.trust_effect == "none"
        assert spec.record_role == "process_record"
        assert spec.participates_in >= {"exact_ref", "inventory"}
    assert "decision_ref" in record_family_specs()["source_acquisition_receipts"].dependency_fields


@pytest.mark.parametrize("action", ["deny", "review"])
def test_deny_or_review_decision_cannot_create_successful_receipt(tmp_path, action):
    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws, action=action)

    with pytest.raises(ValueError, match="allow"):
        _successful_receipt(ws, decision)


@pytest.mark.parametrize(
    ("name", "decision_overrides", "receipt_overrides", "match"),
    [
        ("stale decision pin", {}, {"decision_ref": {"record_ref": "source_acquisition_decision:missing", "content_hash": "0" * 64, "revision": 1}}, "decision"),
        ("uri mismatch", {}, {"canonical_uri": "https://example.org/other.pdf"}, "canonical_uri"),
        ("dedup mismatch", {}, {"dedup_key": "doi:10.1000/other"}, "dedup_key"),
        ("topic mismatch", {}, {"topic_id": "other"}, "topic_id"),
        ("connector mismatch", {}, {"connector_id": "other-connector"}, "connector_id"),
        ("collector mismatch", {}, {"collector_id": "other-collector"}, "collector_id"),
        ("expired decision", {"expires_at": "2026-01-01T12:00:00+00:00"}, {}, "expired"),
        ("missing hash", {}, {"byte_sha256": ""}, "byte_sha256"),
        ("non sha256", {}, {"hash_algorithm": "sha1"}, "hash_algorithm"),
        ("zero bytes", {}, {"byte_length": 0}, "byte_length"),
        ("stored uri missing", {}, {"stored_uri": ""}, "stored_uri"),
        ("success with errors", {}, {"errors": ["download warning"]}, "errors"),
    ],
)
def test_receipt_creation_rejects_invalid_authority_or_success_binding(
    tmp_path,
    name,
    decision_overrides,
    receipt_overrides,
    match,
):
    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws, **decision_overrides)

    with pytest.raises(ValueError, match=match):
        _successful_receipt(ws, decision, **receipt_overrides)


def test_receipt_creation_rejects_a_pin_to_the_wrong_record_type(tmp_path):
    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws)
    receipt = _successful_receipt(ws, decision)

    with pytest.raises(ValueError, match="wrong record type"):
        _successful_receipt(ws, decision, decision_ref=receipt.pinned_ref)


def test_receipt_cannot_precede_its_decision(tmp_path):
    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws, decided_at="2026-01-02T00:00:00+00:00")

    with pytest.raises(ValueError, match="precede"):
        _successful_receipt(
            ws,
            decision,
            acquired_at="2026-01-01T12:00:00+00:00",
        )


def test_receipt_writer_rejects_authority_expired_at_actual_write_time(tmp_path):
    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(
        ws,
        decided_at="2026-01-01T00:00:00+00:00",
        expires_at="2026-01-02T00:00:00+00:00",
    )

    with pytest.raises(ValueError, match="expired"):
        _successful_receipt(
            ws,
            decision,
            acquired_at="2026-01-01T12:00:00+00:00",
        )


def test_writers_reject_future_decision_and_receipt_times(tmp_path):
    ws = _setup_workspace(tmp_path)
    with pytest.raises(ValueError, match="future"):
        _allow_decision(
            ws,
            decided_at="2035-01-01T00:00:00+00:00",
            expires_at="2040-01-01T00:00:00+00:00",
        )
    decision = _allow_decision(ws, expires_at="2040-01-01T00:00:00+00:00")
    with pytest.raises(ValueError, match="future"):
        _successful_receipt(
            ws,
            decision,
            acquired_at="2035-01-01T00:00:00+00:00",
        )


def test_immutable_ids_make_decision_and_receipt_retries_idempotent(tmp_path):
    ws = _setup_workspace(tmp_path)

    decision = _allow_decision(ws)
    decision_retry = _allow_decision(ws)
    receipt = _successful_receipt(ws, decision)
    receipt_retry = _successful_receipt(ws, decision_retry)

    assert decision_retry.record == decision.record
    assert decision_retry.pinned_ref == decision.pinned_ref
    assert decision_retry.write_status == "unchanged"
    assert receipt_retry.record == receipt.record
    assert receipt_retry.pinned_ref == receipt.pinned_ref
    assert receipt_retry.write_status == "unchanged"


def test_failed_receipt_keeps_explicit_errors_without_acquired_bytes(tmp_path):
    from brain.v5.source_acquisition import (
        SourceAcquisitionResolutionError,
        resolve_source_acquisition_for_source_asset,
    )

    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws)
    receipt = _successful_receipt(
        ws,
        decision,
        status="failed",
        byte_sha256="",
        hash_algorithm="",
        byte_length=0,
        stored_uri="",
        errors=["network timeout"],
    )

    assert receipt.record.status == "failed"
    assert receipt.record.errors == ["network timeout"]
    assert receipt.record.byte_sha256 == ""
    assert receipt.record.byte_length == 0
    with pytest.raises(SourceAcquisitionResolutionError, match="succeeded"):
        resolve_source_acquisition_for_source_asset(ws, receipt.pinned_ref)


def test_contracts_reject_trust_mutation_and_bad_success_records(tmp_path):
    from brain.v5.source_acquisition_contracts import (
        validate_source_acquisition_decision_record,
        validate_source_acquisition_receipt_record,
    )

    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws).record
    receipt = _successful_receipt(ws, _allow_decision(ws)).record

    assert validate_source_acquisition_decision_record(decision) == ()
    assert validate_source_acquisition_receipt_record(receipt) == ()
    assert "can_update_claim_trust" in " ".join(
        validate_source_acquisition_decision_record(
            replace(decision, can_update_claim_trust=True)
        )
    )
    assert "stored_uri" in " ".join(
        validate_source_acquisition_receipt_record(replace(receipt, stored_uri=""))
    )
    for malformed in ([], 0, False):
        assert "expires_at" in " ".join(
            validate_source_acquisition_decision_record(
                replace(decision, expires_at=malformed)
            )
        )
    assert "action" in " ".join(
        validate_source_acquisition_decision_record(replace(decision, action=[]))
    )
    assert "status" in " ".join(
        validate_source_acquisition_receipt_record(replace(receipt, status=[]))
    )


@pytest.mark.parametrize(
    ("family", "capture_name", "match"),
    [
        ("source_acquisition_receipts", "receipt", "receipt"),
        ("source_acquisition_decisions", "decision", "decision"),
    ],
)
def test_tampered_canonical_records_fail_closed_during_resolution(
    tmp_path,
    family,
    capture_name,
    match,
):
    from brain.v5.source_acquisition import (
        SourceAcquisitionResolutionError,
        resolve_source_acquisition_for_source_asset,
    )

    ws = _setup_workspace(tmp_path)
    decision = _allow_decision(ws)
    receipt = _successful_receipt(ws, decision)
    capture = {"decision": decision, "receipt": receipt}[capture_name]
    record_id = capture.record.decision_id if capture_name == "decision" else capture.record.receipt_id
    record_path = ws.registry_dir(family) / f"{record_id}.md"
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "https://example.org/paper.pdf", "https://example.org/tampered.pdf", 1
        ),
        encoding="utf-8",
    )

    with pytest.raises(SourceAcquisitionResolutionError, match=match):
        resolve_source_acquisition_for_source_asset(ws, receipt.pinned_ref)
