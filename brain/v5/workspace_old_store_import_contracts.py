"""Contracts for controlled old-store import results."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_MODES = {"apply", "plan"}
_STATUSES = {
    "already_present_same_hash",
    "archive_only",
    "conflict_existing_different_hash",
    "imported",
    "requires_semantic_l2_reassignment",
    "would_import",
}


def validate_workspace_old_store_import_result(
    payload: dict[str, Any],
    *,
    path: str = "workspace_old_store_import_result",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_old_store_import_result":
        result.add(f"{path}.kind", "must be 'aitp_workspace_old_store_import_result'")
    if payload.get("mode") not in _MODES:
        result.add(f"{path}.mode", "must be plan or apply")
    for key in ("workspace_root", "canonical_topics_root", "canonical_store", "old_store_manifest_source"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        result.add(f"{path}.summary", "must be a mapping")
        summary = {}
    for key in (
        "action_count",
        "importable_count",
        "would_import_count",
        "imported_count",
        "already_present_count",
        "conflict_count",
        "archive_only_count",
        "requires_semantic_l2_reassignment_count",
        "selected_topic_count",
    ):
        if not isinstance(summary.get(key), int) or summary.get(key) < 0:
            result.add(f"{path}.summary.{key}", "must be a non-negative integer")
    if not isinstance(summary.get("safe_to_apply"), bool):
        result.add(f"{path}.summary.safe_to_apply", "must be a boolean")
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


def require_valid_workspace_old_store_import_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_old_store_import_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_action(item: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(item, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("source_store_label", "source_path", "source_category", "status"):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if item.get("status") not in _STATUSES:
        result.add(f"{path}.status", "must be an allowed import status")
    if not isinstance(item.get("importable"), bool):
        result.add(f"{path}.importable", "must be a boolean")
    if not isinstance(item.get("size_bytes"), int) or item.get("size_bytes") < 0:
        result.add(f"{path}.size_bytes", "must be a non-negative integer")
    for key in ("summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if item.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
