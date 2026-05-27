"""Contracts for legacy semantic needs-revision basis queues."""

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


def validate_legacy_semantic_needs_revision_basis_queue(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_needs_revision_basis_queue",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_semantic_needs_revision_basis_queue":
        result.add(f"{path}.kind", "must be 'legacy_semantic_needs_revision_basis_queue'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "legacy_semantic_review_worklist":
        result.add(f"{path}.truth_source", "must be 'legacy_semantic_review_worklist'")
    if not isinstance(payload.get("basis_item_count"), int) or payload["basis_item_count"] < 0:
        result.add(f"{path}.basis_item_count", "must be a non-negative integer")
    _require_mapping(payload.get("status_counts"), f"{path}.status_counts", result)
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


def require_valid_legacy_semantic_needs_revision_basis_queue(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_needs_revision_basis_queue(payload)
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
        "latest_review_id",
        "review_status",
        "basis_packet_cli",
        "needs_revision_result_cli",
        "repair_plan_cli",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("review_status") != "inconclusive":
        result.add(f"{path}.review_status", "must be 'inconclusive'")
    for key in ("blocking_classes", "pass_blockers", "remaining_actions", "required_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
