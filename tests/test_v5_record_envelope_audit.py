from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope_audit import audit_record_envelope_compatibility


def test_envelope_audit_separates_loaded_and_malformed_records(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_md(
        ws.registry_dir("claims") / "claim-valid.md",
        {"claim_id": "c1", "topic_id": "t1", "kind": "claim"},
        "# Claim\n",
    )
    write_md(
        ws.registry_dir("claims") / "claim-missing-id.md",
        {"topic_id": "t1", "kind": "claim"},
        "# Malformed claim\n",
    )

    report = audit_record_envelope_compatibility(
        tmp_path,
        families=["claims"],
        issue_limit=10,
    )

    assert report.checked_count == 2
    assert report.loaded_count == 1
    assert report.malformed_count == 1
    assert report.family_counts["claims"].checked_count == 2
    assert report.family_counts["claims"].loaded_count == 1
    assert report.family_counts["claims"].malformed_count == 1
    assert len(report.issues) == 1
    assert "record_id" in report.issues[0].error
    assert report.orientation_only is True
    assert report.can_update_claim_trust is False


def test_envelope_audit_bounds_issue_samples_without_hiding_counts(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    for index in range(3):
        write_md(
            ws.registry_dir("claims") / f"bad-{index}.md",
            {"topic_id": "t1", "kind": "claim"},
            "# Malformed claim\n",
        )

    report = audit_record_envelope_compatibility(
        tmp_path,
        families=["claims"],
        issue_limit=1,
    )

    assert report.checked_count == 3
    assert report.malformed_count == 3
    assert len(report.issues) == 1
    assert report.issue_count == 3
