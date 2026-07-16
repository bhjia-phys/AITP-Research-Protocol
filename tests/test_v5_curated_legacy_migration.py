from __future__ import annotations


def _write_qsgw_topic(root):
    from brain.v5.markdown import write_md

    topic = root / "qsgw-headwing-update-librpa"
    for rel in [
        "L0/sources/source-a",
        "L3/candidates",
        "L3/gap-audit",
        "L3/runs/run-001-headwing-trace",
    ]:
        (topic / rel).mkdir(parents=True, exist_ok=True)
    write_md(
        topic / "state.md",
        {
            "title": "QSGW Head-Wing Update Algorithm in LibRPA",
            "question": "How does head-wing update affect QSGW?",
            "stage": "L4",
            "lane": "code_method",
        },
        "# State\n",
    )
    write_md(
        topic / "L0" / "sources" / "source-a" / "source.md",
        {"title": "Source A", "source_url": "https://example.test/source"},
        "# Source A\n",
    )
    write_md(
        topic / "L3" / "candidates" / "cand-headwing-rotation-v1.md",
        {"candidate_id": "cand-headwing-rotation-v1", "claim": "Velocity rotation must be reviewed."},
        "# Candidate A\n",
    )
    write_md(
        topic / "L3" / "candidates" / "headwing-algorithm-trace-v1.md",
        {"candidate_id": "headwing-algorithm-trace-v1", "claim": "Head-wing trace must be reviewed."},
        "# Candidate B\n",
    )
    write_md(topic / "L3" / "gap-audit" / "active_gaps.md", {}, "# Gaps\n")
    write_md(topic / "L3" / "runs" / "run-001-headwing-trace" / "result_summary.md", {}, "# Result\n")
    write_md(topic / "L3" / "runs" / "run-001-headwing-trace" / "derivation_records.md", {}, "# Derivation\n")
    return topic


def test_curated_legacy_migration_creates_active_v5_claim_and_gaps(tmp_path):
    from brain.v5.curated_legacy_migration import migrate_curated_legacy_topic_to_v5
    from brain.v5.models import (
        ClaimStatusRecord,
        EvidenceRecord,
        ProofObligationRecord,
        ValidationContractRecord,
    )
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.store import list_records
    from brain.v5.workspace import get_claim, get_session_binding, init_workspace

    ws = init_workspace(tmp_path / "ws")
    topic = _write_qsgw_topic(tmp_path / "legacy")

    result = migrate_curated_legacy_topic_to_v5(ws, topic)

    assert require_valid_public_surface("legacy_migration_result", result) == result
    assert result["topic_id"] == "qsgw-headwing-update-librpa"
    assert result["session_id"] == "v5-qsgw-headwing-update-librpa"
    assert result["summary_inputs_trusted"] is False
    assert isinstance(result["curation"]["missing_artifacts"], list)
    assert result["curation"]["artifact_ids"]

    session = get_session_binding(ws, result["session_id"])
    assert session.active_claim == result["active_claim_id"]
    claim = get_claim(ws, result["active_claim_id"])
    assert claim.confidence_state == "review_blocked"
    assert "not L2-ready" in claim.statement

    statuses = list_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
    assert any(status.claim_id == claim.claim_id and status.claim_status == "blocked_by_missing_l4_reviews" for status in statuses)

    obligations = [item for item in list_records(ws.registry_dir("proof_obligations"), ProofObligationRecord) if item.claim_id == claim.claim_id]
    assert len(obligations) >= 3
    assert any("cand-headwing-rotation-v1" in item.statement for item in obligations)
    assert any("true-frozen" in item.statement for item in obligations)

    contracts = [item for item in list_records(ws.registry_dir("validation_contracts"), ValidationContractRecord) if item.claim_id == claim.claim_id]
    assert contracts
    assert "missing_l4_review" in contracts[0].failure_modes

    migrated_reports = [
        item
        for item in list_records(ws.registry_dir("evidence"), EvidenceRecord)
        if item.claim_id == claim.claim_id and item.artifact_ids
    ]
    assert migrated_reports
    assert all(item.basis_policy_status == "legacy_unchecked" for item in migrated_reports)
    assert all(item.support_basis_refs == [] for item in migrated_reports)
    assert all(item.can_update_claim_trust is False for item in migrated_reports)
    assert (ws.topic_dir("qsgw-headwing-update-librpa") / "indexes" / "legacy_v5_curated_migration.md").exists()


def test_curated_legacy_topic_catalog_is_stable():
    from brain.v5.curated_legacy_migration import known_curated_legacy_topics

    topics = known_curated_legacy_topics()
    assert "gw-dmft" in topics
    assert "qsgw-headwing-update-librpa" in topics
    assert "quantum-chaos-long-range-spin-chains" in topics
