"""Contracts for workspace recovery binding repair surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_STATUSES = {
    "already_bound",
    "bound_existing_session",
    "created_session",
    "planned_bind_existing_session",
    "planned_create_session",
    "review_required_multiple_claims",
    "review_required_no_claim",
}


def validate_workspace_recovery_binding_repair(
    payload: dict[str, Any],
    *,
    path: str = "workspace_recovery_binding_repair",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_recovery_binding_repair":
        result.add(f"{path}.kind", "must be 'aitp_workspace_recovery_binding_repair'")
    if payload.get("mode") not in {"plan", "apply"}:
        result.add(f"{path}.mode", "must be plan or apply")
    for key in ("canonical_topics_root", "canonical_store"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        result.add(f"{path}.summary", "must be a mapping")
        summary = {}
    for key in ("action_count", "applyable_count", "review_required_count"):
        if not isinstance(summary.get(key), int) or summary.get(key) < 0:
            result.add(f"{path}.summary.{key}", "must be a non-negative integer")
    if not isinstance(summary.get("status_counts"), dict):
        result.add(f"{path}.summary.status_counts", "must be a mapping")
    actions = payload.get("actions")
    if not isinstance(actions, list):
        result.add(f"{path}.actions", "must be a list")
        actions = []
    if isinstance(summary.get("action_count"), int) and len(actions) != summary.get("action_count"):
        result.add(f"{path}.summary.action_count", "must equal len(actions)")
    for index, action in enumerate(actions[:50]):
        _validate_action(action, result, path=f"{path}.actions[{index}]")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if payload.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    return result


def require_valid_workspace_recovery_binding_repair(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_recovery_binding_repair(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_action(item: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(item, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("topic_id", "claim_id", "session_id", "context_id", "status", "reason"):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if item.get("status") not in _STATUSES:
        result.add(f"{path}.status", "must be an allowed recovery binding status")
    for key in ("claim_count", "session_count"):
        if not isinstance(item.get(key), int) or item.get(key) < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if not isinstance(item.get("applyable"), bool):
        result.add(f"{path}.applyable", "must be a boolean")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if item.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
