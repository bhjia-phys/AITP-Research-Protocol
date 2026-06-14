"""Contracts for workspace-level recovery audits."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_RECOVERY_STATUSES = {
    "brief_or_relation_error",
    "no_active_claim",
    "no_session",
    "recovery_ready",
    "recovery_source_divergence",
    "relation_boundary_gap",
}


def validate_workspace_recovery_audit(
    payload: dict[str, Any],
    *,
    path: str = "workspace_recovery_audit",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_recovery_audit":
        result.add(f"{path}.kind", "must be 'aitp_workspace_recovery_audit'")
    for key in ("canonical_topics_root", "canonical_store", "migration_plan_source"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        result.add(f"{path}.summary", "must be a mapping")
        summary = {}
    for key in (
        "topic_count",
        "recovery_ready_count",
        "recovery_gap_count",
        "topics_with_active_claim",
        "topics_with_relation_map",
        "topics_blocked_by_migration_review",
    ):
        if not isinstance(summary.get(key), int) or summary.get(key) < 0:
            result.add(f"{path}.summary.{key}", "must be a non-negative integer")
    rows = payload.get("topic_rows")
    if not isinstance(rows, list):
        result.add(f"{path}.topic_rows", "must be a list")
        rows = []
    if isinstance(summary.get("topic_count"), int) and len(rows) != summary.get("topic_count"):
        result.add(f"{path}.summary.topic_count", "must equal len(topic_rows)")
    if (
        isinstance(summary.get("recovery_ready_count"), int)
        and isinstance(summary.get("recovery_gap_count"), int)
        and isinstance(summary.get("topic_count"), int)
        and summary.get("recovery_ready_count") + summary.get("recovery_gap_count") != summary.get("topic_count")
    ):
        result.add(f"{path}.summary.recovery_gap_count", "must complement recovery_ready_count")
    for index, row in enumerate(rows[:50]):
        _validate_recovery_row(row, result, path=f"{path}.topic_rows[{index}]")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if payload.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    return result


def require_valid_workspace_recovery_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_recovery_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_workspace_recovery_audit_progress(
    payload: dict[str, Any],
    *,
    path: str = "workspace_recovery_audit_progress",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_recovery_audit_progress":
        result.add(f"{path}.kind", "must be 'aitp_workspace_recovery_audit_progress'")
    for key in (
        "topic_count",
        "recovery_ready_count",
        "recovery_gap_count",
        "topics_with_active_claim",
        "topics_with_relation_map",
        "topics_blocked_by_migration_review",
    ):
        if not isinstance(payload.get(key), int) or payload.get(key) < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("status_counts",):
        if not isinstance(payload.get(key), dict):
            result.add(f"{path}.{key}", "must be a mapping")
    if not isinstance(payload.get("top_gap_topics"), list):
        result.add(f"{path}.top_gap_topics", "must be a list")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if payload.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    return result


def require_valid_workspace_recovery_audit_progress(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_recovery_audit_progress(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_recovery_row(item: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(item, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("topic_id", "recovery_status", "recovery_gap"):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if item.get("recovery_status") not in _RECOVERY_STATUSES:
        result.add(f"{path}.recovery_status", "must be an allowed recovery status")
    for key in (
        "migration_review_required",
        "has_execution_brief",
        "has_relation_map",
        "has_current_conclusion",
        "has_next_valid_action",
    ):
        if not isinstance(item.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if not isinstance(item.get("session_count"), int) or item.get("session_count") < 0:
        result.add(f"{path}.session_count", "must be a non-negative integer")
