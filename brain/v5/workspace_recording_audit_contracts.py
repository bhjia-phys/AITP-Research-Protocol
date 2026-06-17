"""Contracts for workspace-level recording navigation audits."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_RECORDING_STATUSES = {
    "blocked_by_recovery_gap",
    "navigation_error",
    "navigation_ready",
    "navigation_ready_with_blockers",
}


def validate_workspace_recording_audit(
    payload: dict[str, Any],
    *,
    path: str = "workspace_recording_audit",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_recording_audit":
        result.add(f"{path}.kind", "must be 'aitp_workspace_recording_audit'")
    for key in ("canonical_topics_root", "canonical_store", "migration_plan_source", "recovery_audit_source"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        result.add(f"{path}.summary", "must be a mapping")
        summary = {}
    for key in ("topic_count", "navigable_topic_count", "blocked_topic_count", "human_review_topic_count"):
        if not isinstance(summary.get(key), int) or summary.get(key) < 0:
            result.add(f"{path}.summary.{key}", "must be a non-negative integer")
    for key in ("status_counts", "recommended_slot_counts", "zero_slot_counts"):
        if not isinstance(summary.get(key), dict):
            result.add(f"{path}.summary.{key}", "must be a mapping")
    rows = payload.get("topic_rows")
    if not isinstance(rows, list):
        result.add(f"{path}.topic_rows", "must be a list")
        rows = []
    if isinstance(summary.get("topic_count"), int) and summary.get("topic_count") != len(rows):
        result.add(f"{path}.summary.topic_count", "must equal len(topic_rows)")
    for index, row in enumerate(rows[:50]):
        _validate_row(row, result, path=f"{path}.topic_rows[{index}]")
    sequence = payload.get("navigation_sequence")
    if not isinstance(sequence, list) or not sequence:
        result.add(f"{path}.navigation_sequence", "must be a non-empty list")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if payload.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    return result


def require_valid_workspace_recording_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_recording_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_row(item: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(item, dict):
        result.add(path, "must be a mapping")
        return
    for key in (
        "topic_id",
        "session_id",
        "active_claim_id",
        "recovery_status",
        "recovery_gap",
        "recording_status",
        "next_slot",
        "next_read_tool",
        "next_verify_tool",
        "next_valid_action",
        "truth_source",
    ):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if item.get("recording_status") not in _RECORDING_STATUSES:
        result.add(f"{path}.recording_status", "must be an allowed recording status")
    for key in (
        "migration_review_required",
        "human_review_required",
        "orientation_only",
    ):
        if not isinstance(item.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key in ("can_update_kernel_state", "can_update_claim_trust"):
        if item.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    if not isinstance(item.get("first_level_slot_counts"), dict):
        result.add(f"{path}.first_level_slot_counts", "must be a mapping")
    for key in ("first_level_slots", "recommended_slots", "zero_count_slots", "relation_blockers", "human_review_reasons"):
        if not isinstance(item.get(key), list):
            result.add(f"{path}.{key}", "must be a list")
