from dataclasses import replace
from datetime import date

import pytest

from brain.v5.models import ClaimRecord
from brain.v5.record_envelope import (
    EnvelopeValidationError,
    RecordActor,
    canonical_record_hash,
    envelope_for_record,
    read_envelope_compat,
    validate_record_envelope,
)
from brain.v5.record_family_registry import record_family_specs


def test_envelope_hash_is_stable_for_key_order():
    left = canonical_record_hash({"kind": "claim", "claim_id": "c1"}, "# Claim\n")
    right = canonical_record_hash({"claim_id": "c1", "kind": "claim"}, "# Claim\n")

    assert left == right


def test_envelope_hash_covers_scientific_content_but_not_its_own_digest():
    baseline = canonical_record_hash(
        {"claim_id": "c1", "statement": "A", "record_content_hash": "old"},
        "# Claim\r\n",
    )
    same_payload = canonical_record_hash(
        {"statement": "A", "claim_id": "c1", "record_content_hash": "new"},
        "# Claim\n",
    )
    changed_statement = canonical_record_hash(
        {"claim_id": "c1", "statement": "B"},
        "# Claim\n",
    )

    assert baseline == same_payload
    assert baseline != changed_statement


def test_source_asset_content_hash_remains_scientific_payload():
    left = canonical_record_hash(
        {"asset_id": "a1", "content_hash": "source-bytes-a"},
        "# Source\n",
    )
    right = canonical_record_hash(
        {"asset_id": "a1", "content_hash": "source-bytes-b"},
        "# Source\n",
    )

    assert left != right


def test_envelope_hash_ignores_only_control_metadata_needed_for_revisions():
    scientific = {"claim_id": "c1", "topic_id": "t1", "statement": "A"}
    envelope_aware = {
        **scientific,
        "record_id": "c1",
        "record_family": "claims",
        "schema_version": "v1",
        "created_at": "2026-07-10T00:00:00+00:00",
        "created_by": {"actor_type": "model", "actor_id": "a1", "host": "codex"},
        "revision": 2,
        "lifecycle_status": "active",
        "supersedes": ["claim:c1@sha256:old"],
        "trust_effect": "trust_path_input",
    }

    assert canonical_record_hash(scientific, "# Claim\n") == canonical_record_hash(
        envelope_aware, "# Claim\n"
    )


def test_envelope_hash_normalizes_yaml_date_values():
    digest = canonical_record_hash(
        {"claim_id": "c1", "observed_on": date(2026, 6, 1)},
        "# Claim\n",
    )

    assert len(digest) == 64


def test_schema_v1_record_gets_compatibility_envelope(tmp_path):
    envelope = read_envelope_compat(
        {"claim_id": "c1", "topic_id": "t1", "kind": "claim"},
        record_family_specs()["claims"],
        tmp_path / "c1.md",
    )

    assert envelope.record_id == "c1"
    assert envelope.schema_version == "v1-compat"
    assert envelope.trust_effect == "trust_path_input"
    assert envelope.record_id_source == "canonical_field:claim_id"


@pytest.mark.parametrize(
    ("family", "legacy_field", "record_id"),
    [
        ("reference_locations", "reference_location_id", "reference-location-1"),
        ("validation_results", "validation_result_id", "validation-result-1"),
    ],
)
def test_compatibility_envelope_labels_registered_legacy_id_fields(
    tmp_path, family, legacy_field, record_id
):
    envelope = read_envelope_compat(
        {legacy_field: record_id, "topic_id": "t1", "kind": record_family_specs()[family].record_kind},
        record_family_specs()[family],
        tmp_path / f"{record_id}.md",
    )

    assert envelope.record_id == record_id
    assert envelope.record_id_source == f"legacy_field:{legacy_field}"


def test_compatibility_envelope_labels_generic_v1_id_and_topic_fields(tmp_path):
    envelope = read_envelope_compat(
        {"id": "evidence-1", "topic": "qsgw", "kind": "evidence"},
        record_family_specs()["evidence"],
        tmp_path / "evidence-1.md",
    )

    assert envelope.record_id == "evidence-1"
    assert envelope.record_id_source == "legacy_field:id"
    assert envelope.topic_id == "qsgw"
    assert "topic_id:legacy_field:topic" in envelope.compatibility_sources


def test_compatibility_envelope_accepts_generic_v1_id_and_topic_fields(tmp_path):
    envelope = read_envelope_compat(
        {"id": "evidence-legacy", "topic": "topic-legacy", "kind": "evidence"},
        record_family_specs()["evidence"],
        tmp_path / "evidence-legacy.md",
    )

    assert envelope.record_id == "evidence-legacy"
    assert envelope.record_id_source == "legacy_field:id"
    assert envelope.topic_id == "topic-legacy"
    assert envelope.scope_refs == ("topic:topic-legacy",)


def test_envelope_for_record_captures_actor_revision_and_scope():
    claim = ClaimRecord(
        claim_id="c1",
        topic_id="t1",
        statement="The scoped statement.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="The all-order closure remains open.",
    )
    actor = RecordActor(actor_type="model", actor_id="codex-local", host="codex")

    envelope = envelope_for_record(
        claim,
        family="claims",
        actor=actor,
        timestamp="2026-07-10T12:00:00+00:00",
        body="# Claim\n",
        source_record_refs=["source_asset:paper-1"],
    )

    assert envelope.record_id == "c1"
    assert envelope.record_family == "claims"
    assert envelope.schema_version == "v1"
    assert envelope.created_by == actor
    assert envelope.revision == 1
    assert envelope.scope_refs == ("topic:t1",)
    assert envelope.source_record_refs == ("source_asset:paper-1",)
    assert validate_record_envelope(envelope) == ()


def test_envelope_validation_rejects_invalid_actor_revision_family_hash_and_trust_effect():
    claim = ClaimRecord(
        claim_id="c1",
        topic_id="t1",
        statement="The scoped statement.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Open.",
    )
    valid = envelope_for_record(
        claim,
        family="claims",
        actor=RecordActor(actor_type="human", actor_id="researcher", host="cli"),
        timestamp="2026-07-10T12:00:00+00:00",
    )
    invalid = replace(
        valid,
        record_family="missing",
        created_by=RecordActor(actor_type="agent", actor_id="", host=""),
        content_hash="",
        revision=0,
        trust_effect="promotes_claim",
    )

    errors = validate_record_envelope(invalid)

    assert any("record_family" in error for error in errors)
    assert any("actor_type" in error for error in errors)
    assert any("actor_id" in error for error in errors)
    assert any("content_hash" in error for error in errors)
    assert any("revision" in error for error in errors)
    assert any("trust_effect" in error for error in errors)


def test_envelope_validation_rejects_untyped_scope_and_source_refs():
    claim = ClaimRecord(
        claim_id="c1",
        topic_id="t1",
        statement="The scoped statement.",
        evidence_profile="formal_derivation",
        confidence_state="hypothesis",
        active_uncertainty="Open.",
    )
    valid = envelope_for_record(
        claim,
        family="claims",
        actor=RecordActor(actor_type="human", actor_id="researcher", host="cli"),
        timestamp="2026-07-10T12:00:00+00:00",
    )
    invalid = replace(
        valid,
        scope_refs=("missing-colon",),
        source_record_refs=("also-missing-colon",),
    )

    errors = validate_record_envelope(invalid)

    assert any("scope_refs" in error and "typed refs" in error for error in errors)
    assert any("source_record_refs" in error and "typed refs" in error for error in errors)


@pytest.mark.parametrize("revision", [0, -1, "not-an-integer", True])
def test_compatibility_envelope_rejects_explicit_invalid_revision(tmp_path, revision):
    with pytest.raises(EnvelopeValidationError, match="revision"):
        read_envelope_compat(
            {
                "claim_id": "c1",
                "topic_id": "t1",
                "kind": "claim",
                "revision": revision,
            },
            record_family_specs()["claims"],
            tmp_path / "c1.md",
        )


def test_compatibility_envelope_rejects_missing_id_and_invalid_actor(tmp_path):
    with pytest.raises(EnvelopeValidationError, match="record_id"):
        read_envelope_compat(
            {"topic_id": "t1", "kind": "claim"},
            record_family_specs()["claims"],
            tmp_path / "missing-id.md",
        )

    with pytest.raises(EnvelopeValidationError, match="actor_type"):
        read_envelope_compat(
            {
                "claim_id": "c1",
                "topic_id": "t1",
                "kind": "claim",
                "created_by": {"actor_type": "agent", "actor_id": "a1", "host": "codex"},
            },
            record_family_specs()["claims"],
            tmp_path / "c1.md",
        )

    with pytest.raises(EnvelopeValidationError, match="actor_id"):
        read_envelope_compat(
            {
                "claim_id": "c1",
                "topic_id": "t1",
                "kind": "claim",
                "created_by": {"actor_type": "human", "host": "cli"},
            },
            record_family_specs()["claims"],
            tmp_path / "c1.md",
        )


def test_compatibility_envelope_uses_mtime_without_mutating_legacy_file(tmp_path):
    from brain.v5.markdown import write_md

    path = tmp_path / "c1.md"
    write_md(path, {"claim_id": "c1", "topic_id": "t1", "kind": "claim"}, "# Claim\n")
    before = path.read_bytes()

    envelope = read_envelope_compat(
        {"claim_id": "c1", "topic_id": "t1", "kind": "claim"},
        record_family_specs()["claims"],
        path,
    )

    assert envelope.creation_time_source == "file_mtime_fallback"
    assert envelope.created_at != "unknown"
    assert path.read_bytes() == before
