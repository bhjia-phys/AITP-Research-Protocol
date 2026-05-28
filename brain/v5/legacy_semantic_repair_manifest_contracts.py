"""Contracts for legacy semantic repair batch manifests."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


_REPAIR_STATUSES = {
    "proposed_repairs",
    "external_evidence_required",
    "awaiting_needs_revision_review",
    "no_repair_candidates",
}


def validate_legacy_semantic_repair_manifest(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_repair_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_semantic_repair_manifest":
        result.add(f"{path}.kind", "must be 'legacy_semantic_repair_manifest'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "legacy_semantic_review_manifest":
        result.add(f"{path}.truth_source", "must be 'legacy_semantic_review_manifest'")
    for key in ("work_item_count", "proposed_repair_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("repair_status_counts"), f"{path}.repair_status_counts", result)
    _require_mapping(payload.get("required_action_counts"), f"{path}.required_action_counts", result)
    _require_list(payload.get("items"), f"{path}.items", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    if isinstance(payload.get("items"), list):
        for index, item in enumerate(payload["items"]):
            _validate_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_legacy_semantic_repair_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_repair_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topic",
        "active_claim_id",
        "review_status",
        "repair_status",
        "repair_plan_cli",
        "repair_plan_mcp",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("repair_status") not in _REPAIR_STATUSES:
        result.add(f"{path}.repair_status", "must be an allowed repair status")
    if not isinstance(payload.get("latest_review_id"), str):
        result.add(f"{path}.latest_review_id", "must be a string")
    if not isinstance(payload.get("proposed_repair_count"), int) or payload["proposed_repair_count"] < 0:
        result.add(f"{path}.proposed_repair_count", "must be a non-negative integer")
    _require_list(payload.get("proposed_repair_types"), f"{path}.proposed_repair_types", result)
    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
