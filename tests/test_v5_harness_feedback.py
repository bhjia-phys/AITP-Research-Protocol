from __future__ import annotations

import inspect
import json

import pytest

from brain.v5.contracts import ContractError
from brain.v5.public_surfaces import require_valid_public_surface


def _valid_monitor_snapshot() -> dict:
    return {
        "ok": True,
        "kind": "monitor_snapshot",
        "snapshot_id": "monitor-snapshot-1",
        "topic_id": "compute-topic",
        "claim_id": "claim-1",
        "tool_run_id": "tool-run-1",
        "run_dir": "/remote/run1",
        "job_id": "12345",
        "scheduler_state": {"squeue": "RUNNING", "sacct": "RUNNING"},
        "elapsed": "00:10:00",
        "output_file_sizes": {"output.log": 2048},
        "latest_log_markers": ["iteration started"],
        "memory_status": {"MaxRSS": "2G"},
        "failure_markers": [],
        "interpretation_boundary": "Live scheduler state only; not physics evidence.",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _valid_skill_patch_proposal() -> dict:
    return {
        "ok": True,
        "kind": "skill_patch_proposal",
        "proposal_id": "skill-patch-1",
        "skill_name": "validated-workflow",
        "current_version": "0.1.0",
        "proposed_version": "0.1.1",
        "patch_summary": "Add one validated failure boundary.",
        "patch_body": "## Failure boundary\n- Stop when the validation fails.\n",
        "supporting_records": ["validation_result:result-1"],
        "trust_level": "validated",
        "review_status": "draft",
        "application_status": "not_applied",
        "requires_human_review": True,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def _case_request() -> dict:
    return {
        "topic_id": "formal-qg",
        "problem_type": "missing_research_provenance",
        "friction": "The resumed derivation does not expose its convention source.",
        "expected_behavior": "Recall should expose the exact convention record.",
        "actual_behavior": "The compact entry reports the result without that source.",
        "impact": "The model may mix incompatible conventions.",
        "reproduction_steps": ["Start a new session.", "Request compact context."],
        "host_id": "codex",
        "runtime_context": {"event": "session_start", "surface": "compact"},
        "source_refs": ["derivation_chain:qg-chain-7"],
        "proposed_direction": "Expose the convention reference in the entry card.",
        "affected_capability": "context_recall",
        "affected_record_family": "derivation_chains",
    }


def test_monitor_snapshot_public_surface_accepts_trust_neutral_payload():
    payload = require_valid_public_surface("monitor_snapshot_record", _valid_monitor_snapshot())
    assert payload["claim_trust_mutation"] == "none"
    assert payload["can_update_claim_trust"] is False


def test_monitor_snapshot_public_surface_rejects_claim_trust_mutation():
    payload = _valid_monitor_snapshot()
    payload["claim_trust_mutation"] = "candidate"
    with pytest.raises(ContractError):
        require_valid_public_surface("monitor_snapshot_record", payload)


def test_skill_patch_surface_remains_owned_by_the_independent_skill_lifecycle():
    payload = require_valid_public_surface(
        "skill_patch_proposal_record", _valid_skill_patch_proposal()
    )
    assert payload["requires_human_review"] is True
    assert payload["application_status"] == "not_applied"


def test_skill_patch_surface_rejects_unapproved_application():
    payload = _valid_skill_patch_proposal()
    payload["application_status"] = "applied"
    with pytest.raises(ContractError):
        require_valid_public_surface("skill_patch_proposal_record", payload)


def test_harness_feedback_runtime_has_no_topic_specific_or_skill_emission_api():
    from brain.v5 import harness_feedback

    for name in (
        "record_skill_patch_proposal",
        "skill_patch_proposal_payload",
        "build_nio_harness_feedback_bundle",
        "build_harness_feedback_problem_dossier",
        "plan_run_dir_provenance_extractor",
    ):
        assert not hasattr(harness_feedback, name)
    source = inspect.getsource(harness_feedback)
    for fixed_content in (
        "g0w0-magnetic-nio",
        "FHI-aims",
        "LibRPA",
        "skill-distillation-candidates",
    ):
        assert fixed_content not in source


def test_legacy_bundle_contract_is_read_only_compatible_without_skill_fields():
    payload = {
        "ok": True,
        "kind": "harness_feedback_bundle",
        "case_id": "legacy-case",
        "meta_topic_path": "legacy/meta-topic",
        "case_report_path": "cases/legacy-case.md",
        "backlog_path": "backlog.md",
        "files": {"cases/legacy-case.md": "# Legacy Case\n"},
        "backlog_items": [],
        "record_schemas": ["monitor_snapshot"],
        "writes_external_topics_root": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
    assert require_valid_public_surface("harness_feedback_bundle", payload) == payload


def test_cli_records_generic_case_from_file_and_reads_review_view(capsys, tmp_path):
    from brain.v5.cli import main

    request_path = tmp_path / "feedback-request.json"
    request_path.write_text(json.dumps(_case_request()), encoding="utf-8")
    record_args = [
        "--base",
        str(tmp_path),
        "harness-feedback",
        "record",
        "--request-json-file",
        str(request_path),
    ]

    assert main(record_args) == 0
    recorded = json.loads(capsys.readouterr().out)
    assert recorded["kind"] == "harness_feedback_case_write"
    assert recorded["status"] == "created"
    assert recorded["requires_human_review"] is True
    assert recorded["produces_harness_optimization_plan"] is False
    assert recorded["produces_skill_implementation_plan"] is False
    assert recorded["can_emit_skill_artifacts"] is False
    assert recorded["can_install_skill"] is False
    assert require_valid_public_surface("harness_feedback_case_write", recorded) == recorded

    assert main(["--base", str(tmp_path), "harness-feedback", "review-view"]) == 0
    view = json.loads(capsys.readouterr().out)
    assert view["kind"] == "harness_feedback_repeated_case_view"
    assert view["groups"] == []
    assert require_valid_public_surface("harness_feedback_repeated_case_view", view) == view


def test_mcp_records_generic_case_and_exposes_review_view(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_build_harness_feedback_review_view,
        aitp_v5_record_harness_feedback_case,
    )

    recorded = aitp_v5_record_harness_feedback_case(
        str(tmp_path), request_json=json.dumps(_case_request())
    )
    view = aitp_v5_build_harness_feedback_review_view(str(tmp_path))

    assert recorded["kind"] == "harness_feedback_case_write"
    assert recorded["status"] == "created"
    assert recorded["can_modify_harness"] is False
    assert recorded["can_install_skill_artifacts"] is False
    assert view["kind"] == "harness_feedback_repeated_case_view"
    assert view["can_update_claim_trust"] is False
