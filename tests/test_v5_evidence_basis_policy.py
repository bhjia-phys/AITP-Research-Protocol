from __future__ import annotations


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="evidence-basis-test", host="pytest")


def _setup(tmp_path):
    from brain.v5.models import InsightRecord, ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    repository = RecordRepository(ws, actor=_actor())
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
    repository.write(
        "insights",
        InsightRecord(
            insight_id="analogy",
            insight_kind="analogy",
            statement="A speculative analogy.",
            topic_id="qg",
            review_status="reviewed",
        ),
    )
    return ws, {
        ref: pin_current_record(ws, ref)
        for ref in (
            "source_asset:paper",
            "reference_location:equation-3",
            "insight:analogy",
        )
    }


def test_exact_source_asset_and_location_are_admissible_support(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis

    ws, pins = _setup(tmp_path)
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pins["source_asset:paper"], pins["reference_location:equation-3"]),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "Equation 3 supports the scoped statement."},
    )

    assert audit.admissible is True
    assert audit.errors == ()
    assert len(audit.payload_hash) == 64
    assert audit.can_update_claim_trust is False


def test_insight_is_allowed_as_trace_but_forbidden_as_support(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis

    ws, pins = _setup(tmp_path)
    trace = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pins["source_asset:paper"], pins["reference_location:equation-3"]),
        trace_context_refs=(pins["insight:analogy"],),
        evidence_payload={"claim_id": "claim-qg", "summary": "Source-grounded support."},
    )
    support = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pins["insight:analogy"],),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "Unsafe wrapped insight."},
    )

    assert trace.admissible is True
    assert support.admissible is False
    assert "inadmissible_support_kind:insight" in support.errors


def test_location_without_its_exact_asset_is_not_admissible(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis

    ws, pins = _setup(tmp_path)
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pins["reference_location:equation-3"],),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "Incomplete source basis."},
    )

    assert audit.admissible is False
    assert "source_location_asset_pin_missing:source_asset:paper" in audit.errors
