"""Contracts for legacy semantic review worklists."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


def validate_legacy_semantic_review_worklist(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_worklist",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_review_worklist":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_worklist'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
    if not isinstance(payload.get("work_item_count"), int) or payload["work_item_count"] < 0:
        result.add(f"{path}.work_item_count", "must be a non-negative integer")
    _validate_status_counts(payload.get("status_counts"), f"{path}.status_counts", result)
    if not isinstance(payload.get("next_actions"), list):
        result.add(f"{path}.next_actions", "must be a list")
    items = payload.get("items")
    if not isinstance(items, list):
        result.add(f"{path}.items", "must be a list")
    else:
        for index, item in enumerate(items):
            _validate_worklist_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_legacy_semantic_review_worklist(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_worklist(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_status_counts(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("needs_revision", "inconclusive", "pending"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_worklist_item(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in (
        "topic",
        "active_claim_id",
        "review_status",
        "review_priority",
        "latest_review_id",
        "packet_cli",
        "result_cli_template",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("review_status") not in {"needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be a backlog review status")
    if payload.get("review_priority") not in {"critical", "high", "medium", "low"}:
        result.add(f"{path}.review_priority", "must be an allowed review priority")
    for key in ("priority_reasons", "review_focus", "missing_source_components", "repair_candidates"):
        if not isinstance(payload.get(key), list):
            result.add(f"{path}.{key}", "must be a list")
    for key in ("priority_score", "repair_candidate_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
