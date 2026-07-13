from __future__ import annotations

import pytest

from brain.v5.legacy_record_materialization import materialize_record_class
from brain.v5.models import (
    CodeStateRecord,
    EvidenceRecord,
    ReferenceLocationRecord,
    SensemakingReportRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.query_index import _typed_materialization_status
from brain.v5.record_family_registry import spec_for_family
from brain.v5.record_repository import _materialize_record, _validate_payload_schema


@pytest.mark.parametrize(
    ("record_class", "frontmatter", "checks"),
    (
        (
            CodeStateRecord,
            {"id": "code-old", "topic": "qg", "kind": "code_state"},
            {"code_state_id": "code-old", "dirty": True, "repo_id": ""},
        ),
        (
            EvidenceRecord,
            {"id": "evidence-old", "topic": "qg", "kind": "evidence"},
            {
                "evidence_id": "evidence-old",
                "claim_id": "",
                "status": "unreviewed",
            },
        ),
        (
            ReferenceLocationRecord,
            {
                "reference_location_id": "location-old",
                "topic_id": "qg",
                "title": "Legacy source bundle",
                "paths": ["notes/source.md"],
                "kind": "reference_location",
            },
            {
                "location_id": "location-old",
                "uri": "notes/source.md",
                "orientation_only": True,
            },
        ),
        (
            SensemakingReportRecord,
            {
                "report_id": "report-old",
                "topic_id": "qg",
                "summary": "legacy interpretation",
                "kind": "sensemaking_report",
            },
            {"report_id": "report-old", "claim_id": "", "title": "report-old"},
        ),
        (
            ToolRunRecord,
            {
                "run_id": "run-old",
                "topic_id": "qg",
                "inputs": {"mesh": "4x4x4"},
                "kind": "tool_run",
            },
            {
                "run_id": "run-old",
                "recipe_id": "legacy-unresolved",
                "claim_id": "",
                "lane": "diagnostic",
            },
        ),
        (
            ValidationResultRecord,
            {
                "validation_result_id": "validation-old",
                "topic_id": "qg",
                "claim_id": "claim-1",
                "contract_id": "contract-1",
                "status": "passed_for_inputs",
                "checks": ["input hash checked"],
                "kind": "validation_result",
            },
            {
                "result_id": "validation-old",
                "tool_run_id": "",
                "checked_outputs": ["input hash checked"],
            },
        ),
    ),
)
def test_schema_v1_records_materialize_with_conservative_explicit_defaults(
    record_class,
    frontmatter,
    checks,
):
    record = materialize_record_class(frontmatter, record_class)

    for field, expected in checks.items():
        assert getattr(record, field) == expected


def test_new_enveloped_payload_cannot_use_legacy_defaults():
    frontmatter = {
        "record_family": "evidence",
        "record_content_hash": "a" * 64,
        "evidence_id": "evidence-new",
        "topic_id": "qg",
        "kind": "evidence",
    }

    with pytest.raises(TypeError, match="claim_id"):
        materialize_record_class(frontmatter, EvidenceRecord)


def test_write_validation_can_disable_legacy_materialization():
    with pytest.raises(TypeError, match="claim_id"):
        materialize_record_class(
            {"evidence_id": "candidate", "topic_id": "qg", "kind": "evidence"},
            EvidenceRecord,
            allow_legacy=False,
        )


def test_repository_and_index_share_the_same_schema_v1_materialization():
    spec = spec_for_family("reference_locations")
    frontmatter = {
        "reference_location_id": "legacy-location",
        "topic_id": "qg",
        "title": "Legacy source bundle",
        "paths": ["notes/source.md"],
        "kind": "reference_location",
    }

    record = _materialize_record(frontmatter, spec)

    assert record.location_id == "legacy-location"
    assert record.uri == "notes/source.md"
    assert _typed_materialization_status(frontmatter, spec) == "ready"


def test_repository_write_schema_does_not_accept_legacy_defaults():
    spec = spec_for_family("evidence")

    with pytest.raises(TypeError, match="claim_id"):
        _validate_payload_schema(
            {"evidence_id": "new", "topic_id": "qg", "kind": "evidence"},
            spec,
        )
