from __future__ import annotations

import json

import pytest

from brain.v5.contracts import ContractError
from brain.v5.public_surfaces import require_valid_public_surface


def _valid_monitor_snapshot() -> dict:
    return {
        "ok": True,
        "kind": "monitor_snapshot",
        "snapshot_id": "monitor-snapshot-nio-1",
        "topic_id": "g0w0-magnetic-nio",
        "claim_id": "claim-nio",
        "tool_run_id": "tool-run-nio",
        "run_dir": "/remote/nio/run1",
        "job_id": "12345",
        "scheduler_state": {"squeue": "RUNNING", "sacct": "RUNNING"},
        "elapsed": "00:10:00",
        "output_file_sizes": {"librpa.out": 2048},
        "latest_log_markers": ["Reading librpa.in", "Self-energy"],
        "memory_status": {"MaxRSS": "2G"},
        "failure_markers": [],
        "interpretation_boundary": "Live scheduler state only; not physics evidence.",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def test_monitor_snapshot_public_surface_accepts_trust_neutral_payload():
    payload = require_valid_public_surface("monitor_snapshot_record", _valid_monitor_snapshot())

    assert payload["kind"] == "monitor_snapshot"
    assert payload["claim_trust_mutation"] == "none"
    assert payload["can_update_claim_trust"] is False


def test_monitor_snapshot_public_surface_rejects_claim_trust_mutation():
    payload = _valid_monitor_snapshot()
    payload["claim_trust_mutation"] = "candidate"

    with pytest.raises(ContractError):
        require_valid_public_surface("monitor_snapshot_record", payload)


def test_monitor_snapshot_public_surface_rejects_claim_trust_authority():
    payload = _valid_monitor_snapshot()
    payload["can_update_claim_trust"] = True

    with pytest.raises(ContractError):
        require_valid_public_surface("monitor_snapshot_record", payload)


def _valid_skill_patch_proposal() -> dict:
    return {
        "ok": True,
        "kind": "skill_patch_proposal",
        "proposal_id": "skill-patch-nio-1",
        "skill_name": "fhi-aims-librpa-magnetic-gw-workflow",
        "current_version": "draft-0",
        "proposed_version": "draft-1",
        "patch_summary": "Add NiO magnetic G0W0/QSGW workflow checks.",
        "patch_body": "## Monitoring checklist\n- Record monitor snapshots.\n",
        "supporting_records": ["case:g0w0-magnetic-nio"],
        "trust_level": "diagnostic",
        "review_status": "draft",
        "application_status": "not_applied",
        "requires_human_review": True,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def test_skill_patch_proposal_public_surface_accepts_review_gated_payload():
    payload = require_valid_public_surface("skill_patch_proposal_record", _valid_skill_patch_proposal())

    assert payload["requires_human_review"] is True
    assert payload["application_status"] == "not_applied"


def test_skill_patch_proposal_public_surface_requires_human_review():
    payload = _valid_skill_patch_proposal()
    payload["requires_human_review"] = False

    with pytest.raises(ContractError):
        require_valid_public_surface("skill_patch_proposal_record", payload)


def test_skill_patch_proposal_public_surface_rejects_unapproved_application():
    payload = _valid_skill_patch_proposal()
    payload["review_status"] = "draft"
    payload["application_status"] = "applied"

    with pytest.raises(ContractError):
        require_valid_public_surface("skill_patch_proposal_record", payload)


def test_kernel_records_monitor_snapshot_without_trust_mutation(tmp_path):
    from brain.v5.harness_feedback import monitor_snapshot_payload, record_monitor_snapshot
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record = record_monitor_snapshot(
        ws,
        snapshot_id="monitor-snapshot-nio-1",
        topic_id="g0w0-magnetic-nio",
        claim_id="claim-nio",
        tool_run_id="tool-run-nio",
        run_dir="/remote/nio/run1",
        job_id="12345",
        scheduler_state={"squeue": "RUNNING"},
        elapsed="00:10:00",
        output_file_sizes={"librpa.out": 2048},
        latest_log_markers=["Self-energy"],
        memory_status={"MaxRSS": "2G"},
        failure_markers=[],
        interpretation_boundary="Live scheduler state only.",
    )

    payload = monitor_snapshot_payload(record)
    assert payload["claim_trust_mutation"] == "none"
    assert payload["can_update_claim_trust"] is False
    assert (ws.registry_dir("monitor_snapshots") / f"{record.snapshot_id}.md").exists()


def test_kernel_records_review_gated_skill_patch_proposal(tmp_path):
    from brain.v5.harness_feedback import record_skill_patch_proposal, skill_patch_proposal_payload
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record = record_skill_patch_proposal(
        ws,
        proposal_id="skill-patch-nio-1",
        skill_name="fhi-aims-librpa-magnetic-gw-workflow",
        current_version="draft-0",
        proposed_version="draft-1",
        patch_summary="Add NiO checks.",
        patch_body="## Trust-update gate\nDiagnostic runs do not update trust.\n",
        supporting_records=["case:g0w0-magnetic-nio"],
        trust_level="diagnostic",
    )

    payload = skill_patch_proposal_payload(record)
    assert payload["requires_human_review"] is True
    assert payload["application_status"] == "not_applied"
    assert (ws.registry_dir("skill_patch_proposals") / f"{record.proposal_id}.md").exists()


def test_nio_harness_feedback_bundle_contains_required_sections():
    from brain.v5.harness_feedback import build_nio_harness_feedback_bundle

    payload = require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())
    case_markdown = payload["files"]["cases/g0w0-magnetic-nio.md"]
    for heading in (
        "## Timeline",
        "## Major Run Directory Classes",
        "## AIMS Input-Contract Lessons",
        "## LibRPA Input-Contract Lessons",
        "## G0W0 Diagnostic/Results Boundary",
        "## QSGW Smoke Workflow",
        "## Proposed Skill Outline",
    ):
        assert heading in case_markdown
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False


def test_nio_backlog_items_have_required_fields():
    from brain.v5.harness_feedback import build_nio_harness_feedback_bundle

    payload = build_nio_harness_feedback_bundle()
    required = {
        "title",
        "source_case",
        "real_topic_evidence",
        "pain_point",
        "proposed_change",
        "minimal_implementation_slice",
        "acceptance_test",
        "risk",
        "linked_topic_records_artifacts",
        "status",
    }
    assert len(payload["backlog_items"]) >= 10
    for item in payload["backlog_items"]:
        assert required <= set(item)


def test_run_dir_provenance_extractor_plan_is_non_writing():
    from brain.v5.harness_feedback import plan_run_dir_provenance_extractor

    payload = require_valid_public_surface("run_dir_provenance_extractor_plan", plan_run_dir_provenance_extractor())
    assert payload["writes_records"] is False
    assert payload["can_update_claim_trust"] is False
    assert "monitor_snapshot_candidate" in payload["outputs"]


def test_cli_harness_feedback_nio_seed_returns_bundle(capsys, tmp_path):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "harness-feedback", "nio-seed"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "harness_feedback_bundle"
    assert payload["case_id"] == "g0w0-magnetic-nio"
    assert payload["writes_external_topics_root"] is False


def test_cli_harness_feedback_extractor_plan_returns_non_writing_plan(capsys, tmp_path):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "harness-feedback", "extractor-plan"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "run_dir_provenance_extractor_plan"
    assert payload["case_id"] == "g0w0-magnetic-nio"
    assert payload["writes_records"] is False


def test_mcp_harness_feedback_wrappers(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_build_harness_feedback_seed_bundle,
        aitp_v5_plan_run_dir_provenance_extractor,
    )

    bundle = aitp_v5_build_harness_feedback_seed_bundle(str(tmp_path))
    plan = aitp_v5_plan_run_dir_provenance_extractor(str(tmp_path))

    assert bundle["kind"] == "harness_feedback_bundle"
    assert bundle["can_update_claim_trust"] is False
    assert plan["kind"] == "run_dir_provenance_extractor_plan"
    assert plan["writes_records"] is False
