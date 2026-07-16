from __future__ import annotations

import pytest


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
        "source_assets",
        SourceAssetRecord(
            asset_id="paper-without-location",
            topic_id="qg",
            asset_type="paper",
            uri="file:///paper-without-location.pdf",
            title="Unanchored paper",
            content_hash="b" * 64,
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
            "source_asset:paper-without-location",
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
    assert len(audit.audit_hash) == 64
    assert [item.role for item in audit.ref_audits] == ["support", "support"]
    assert [item.classification for item in audit.ref_audits] == [
        "source_asset_support",
        "reference_location_support",
    ]
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


def test_every_source_asset_requires_its_own_exact_location(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis

    ws, pins = _setup(tmp_path)
    unanchored = "source_asset:paper-without-location"
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(
            pins["source_asset:paper"],
            pins["reference_location:equation-3"],
            pins[unanchored],
        ),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "Mixed source basis."},
    )

    assert audit.admissible is False
    error = f"exact_source_location_pin_missing:{unanchored}"
    assert error in audit.errors
    unanchored_audit = next(item for item in audit.ref_audits if item.record_ref == unanchored)
    assert error in unanchored_audit.errors


def test_empty_support_basis_is_not_admissible(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis

    ws, _pins = _setup(tmp_path)
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "No exact support."},
    )

    assert audit.admissible is False
    assert "support_basis_refs_required" in audit.errors


def test_claim_scoped_support_cannot_cross_claims_within_one_topic(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim

    ws, _pins = _setup(tmp_path)
    source_claim = create_claim(
        ws,
        topic_id="qg",
        statement="Source claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="scope",
    )
    target_claim = create_claim(
        ws,
        topic_id="qg",
        statement="Target claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="scope",
    )
    run = record_tool_run(
        ws,
        recipe_id="claim-a-check",
        tool_family="formal_theory",
        tool_name="check",
        topic_id="qg",
        claim_id=source_claim.claim_id,
    )
    run_ref = f"tool_run:{run.run_id}"

    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pin_current_record(ws, run_ref),),
        trace_context_refs=(),
        evidence_payload={"claim_id": target_claim.claim_id, "summary": "Wrong claim run."},
    )

    assert audit.admissible is False
    assert f"support_claim_mismatch:{run_ref}" in audit.errors


def test_derived_or_orphan_artifact_cannot_be_support(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.models import ArtifactRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim

    ws, _pins = _setup(tmp_path)
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="Artifact claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="artifact provenance",
    )
    artifact = ArtifactRecord(
        artifact_id="derived-summary",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_type="derived_summary",
        uri="file:///derived-summary.md",
        summary="Orientation-only derived summary.",
        metadata={"source_kind": "summary_orientation"},
    )
    RecordRepository(ws, actor=_actor()).write("artifacts", artifact)
    artifact_ref = f"artifact:{artifact.artifact_id}"

    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(pin_current_record(ws, artifact_ref),),
        trace_context_refs=(),
        evidence_payload={"claim_id": claim.claim_id, "summary": "Wrapped summary."},
    )

    assert audit.admissible is False
    assert f"inadmissible_derived_support:{artifact_ref}" in audit.errors
    assert f"artifact_support_requires_tool_run:{artifact_ref}" in audit.errors


def test_canonical_orientation_only_artifact_role_cannot_be_support(tmp_path):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.models import ArtifactRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim

    ws, _pins = _setup(tmp_path)
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="Role-scoped artifact claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="artifact role",
    )
    artifact = ArtifactRecord(
        artifact_id="orientation-result",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_type="result",
        uri="file:///orientation-result.json",
        summary="Orientation-only result.",
        role="orientation_only",
    )
    RecordRepository(ws, actor=_actor()).write("artifacts", artifact)
    run = record_tool_run(
        ws,
        recipe_id="orientation-run",
        tool_family="diagnostic",
        tool_name="report",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_ids=[artifact.artifact_id],
    )
    artifact_ref = f"artifact:{artifact.artifact_id}"
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(
            pin_current_record(ws, f"tool_run:{run.run_id}"),
            pin_current_record(ws, artifact_ref),
        ),
        trace_context_refs=(),
        evidence_payload={"claim_id": claim.claim_id, "summary": "Unsafe role."},
    )

    assert audit.admissible is False
    assert f"inadmissible_derived_support:{artifact_ref}" in audit.errors


def test_non_ascii_artifact_source_kind_cannot_bypass_derived_support_policy(
    tmp_path,
):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.models import ArtifactRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim

    ws, _pins = _setup(tmp_path)
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="Artifact source-kind boundary claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="artifact source kind",
    )
    artifact = ArtifactRecord(
        artifact_id="unicode-skill-result",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_type="result",
        uri="file:///unicode-skill-result.json",
        summary="Derived workflow output.",
        metadata={"source_kind": "ѕkill"},
    )
    RecordRepository(ws, actor=_actor()).write("artifacts", artifact)
    run = record_tool_run(
        ws,
        recipe_id="unicode-skill-run",
        tool_family="diagnostic",
        tool_name="report",
        topic_id="qg",
        claim_id=claim.claim_id,
        artifact_ids=[artifact.artifact_id],
    )
    artifact_ref = f"artifact:{artifact.artifact_id}"

    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(
            pin_current_record(ws, f"tool_run:{run.run_id}"),
            pin_current_record(ws, artifact_ref),
        ),
        trace_context_refs=(),
        evidence_payload={"claim_id": claim.claim_id, "summary": "Unsafe artifact."},
    )

    assert audit.admissible is False
    assert f"inadmissible_derived_support:{artifact_ref}" in audit.errors


@pytest.mark.parametrize(
    "source_kind",
    [
        "summary",
        "derived summary",
        "summary orientation",
        "derived.summary",
        "rag/chunk",
        "skill.v1",
        "SummaryOrientation",
        "RAGChunk",
        "summаry",
        "ＳｕｍｍａｒｙOrientation",
    ],
)
def test_derived_source_kind_variants_cannot_be_wrapped_as_support(
    tmp_path,
    source_kind,
):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim

    ws, _ = _setup(tmp_path)
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="Summary source claim.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="summary provenance",
    )
    repository = RecordRepository(ws, actor=_actor())
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="summary-source",
            topic_id="qg",
            asset_type="paper",
            uri="file:///summary.md",
            title="Derived summary",
            source_kind=source_kind,
            content_hash="c" * 64,
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id="summary-anchor",
            topic_id="qg",
            claim_id=claim.claim_id,
            connector_id="local-source",
            location_type="section_anchor",
            uri="file:///summary.md#section=1",
            label="Summary section",
            source_ref="source_asset:summary-source",
        ),
    )
    source_ref = "source_asset:summary-source"
    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(
            pin_current_record(ws, source_ref),
            pin_current_record(ws, "reference_location:summary-anchor"),
        ),
        trace_context_refs=(),
        evidence_payload={"claim_id": claim.claim_id, "summary": "Wrapped summary."},
    )

    assert audit.admissible is False
    assert f"inadmissible_derived_support:{source_ref}" in audit.errors


@pytest.mark.parametrize(
    "source_kind",
    ["literature", "local_notes", "local_result", "literature_intake", "manual"],
)
def test_grounded_source_kind_variants_remain_admissible(tmp_path, source_kind):
    from brain.v5.evidence_basis_policy import audit_evidence_basis
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository

    ws, _ = _setup(tmp_path)
    repository = RecordRepository(ws, actor=_actor())
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="grounded-source",
            topic_id="qg",
            asset_type="paper",
            uri="file:///grounded-source.pdf",
            title="Grounded source",
            source_kind=source_kind,
            content_hash="d" * 64,
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id="grounded-anchor",
            topic_id="qg",
            connector_id="local-source",
            location_type="section_anchor",
            uri="file:///grounded-source.pdf#page=1",
            label="Grounded source page 1",
            source_ref="source_asset:grounded-source",
        ),
    )

    audit = audit_evidence_basis(
        ws,
        topic_id="qg",
        support_basis_refs=(
            pin_current_record(ws, "source_asset:grounded-source"),
            pin_current_record(ws, "reference_location:grounded-anchor"),
        ),
        trace_context_refs=(),
        evidence_payload={"claim_id": "claim-qg", "summary": "Grounded support."},
    )

    assert audit.admissible is True
    assert audit.errors == ()
