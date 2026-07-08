"""Contracts for trust-neutral real-topic harness feedback surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


def validate_monitor_snapshot_record(
    payload: dict[str, Any],
    *,
    path: str = "monitor_snapshot_record",
) -> ContractResult:
    result = _validate_base(payload, path, kind="monitor_snapshot")
    if result.issues:
        return result
    for key in (
        "snapshot_id",
        "topic_id",
        "claim_id",
        "tool_run_id",
        "run_dir",
        "job_id",
        "elapsed",
        "interpretation_boundary",
    ):
        _require_nonempty_str(payload, key, path, result)
    for key in ("scheduler_state", "output_file_sizes", "memory_status"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("latest_log_markers", "failure_markers"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    return result


def require_valid_monitor_snapshot_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_monitor_snapshot_record(payload), payload)


def validate_skill_patch_proposal_record(
    payload: dict[str, Any],
    *,
    path: str = "skill_patch_proposal_record",
) -> ContractResult:
    result = _validate_base(payload, path, kind="skill_patch_proposal")
    if result.issues:
        return result
    for key in (
        "proposal_id",
        "skill_name",
        "current_version",
        "proposed_version",
        "patch_summary",
        "patch_body",
        "trust_level",
        "review_status",
        "application_status",
    ):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("supporting_records"), f"{path}.supporting_records", result)
    if payload.get("trust_level") not in {"diagnostic", "validated", "deprecated", "open"}:
        result.add(f"{path}.trust_level", "must be diagnostic, validated, deprecated, or open")
    if payload.get("review_status") not in {
        "draft",
        "ready_for_review",
        "approved",
        "rejected",
        "applied",
    }:
        result.add(f"{path}.review_status", "must be draft, ready_for_review, approved, rejected, or applied")
    if payload.get("application_status") not in {"not_applied", "applied", "superseded"}:
        result.add(f"{path}.application_status", "must be not_applied, applied, or superseded")
    if payload.get("application_status") == "applied" and payload.get("review_status") != "approved":
        result.add(f"{path}.application_status", "cannot be applied unless review_status is approved")
    if payload.get("requires_human_review") is not True:
        result.add(f"{path}.requires_human_review", "must be true")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    _require_false_flags(payload, path, result)
    return result


def require_valid_skill_patch_proposal_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_skill_patch_proposal_record(payload), payload)


def validate_harness_feedback_bundle(
    payload: dict[str, Any],
    *,
    path: str = "harness_feedback_bundle",
) -> ContractResult:
    result = _validate_base(payload, path, kind="harness_feedback_bundle")
    if result.issues:
        return result
    for key in (
        "case_id",
        "meta_topic_path",
        "case_report_path",
        "backlog_path",
        "skill_draft_path",
    ):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("files"), f"{path}.files", result)
    _require_list(payload.get("backlog_items"), f"{path}.backlog_items", result)
    for index, item in enumerate(payload.get("backlog_items") or []):
        if not isinstance(item, dict):
            result.add(f"{path}.backlog_items[{index}]", "must be a mapping")
            continue
        for key in (
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
        ):
            _require_nonempty_str(item, key, f"{path}.backlog_items[{index}]", result)
    _require_list(payload.get("record_schemas"), f"{path}.record_schemas", result)
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("writes_external_topics_root") is not False:
        result.add(f"{path}.writes_external_topics_root", "must be false")
    return result


def require_valid_harness_feedback_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_harness_feedback_bundle(payload), payload)


def validate_run_dir_provenance_extractor_plan(
    payload: dict[str, Any],
    *,
    path: str = "run_dir_provenance_extractor_plan",
) -> ContractResult:
    result = _validate_base(payload, path, kind="run_dir_provenance_extractor_plan")
    if result.issues:
        return result
    for key in ("case_id", "purpose", "acceptance_test"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("inputs", "outputs", "extractors", "review_gates"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("writes_records") is not False:
        result.add(f"{path}.writes_records", "must be false")
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    return result


def require_valid_run_dir_provenance_extractor_plan(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_run_dir_provenance_extractor_plan(payload), payload)


def _validate_base(payload: Any, path: str, *, kind: str) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    return result


def _require_false_flags(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _require_valid(result: ContractResult, payload: dict[str, Any]) -> dict[str, Any]:
    if not result.ok:
        raise ContractError(result)
    return payload
