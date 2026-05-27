"""Contracts for legacy human checkpoint packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_human_checkpoint_packet(
    payload: dict[str, Any],
    *,
    path: str = "legacy_human_checkpoint_packet",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_human_checkpoint_packet":
        result.add(f"{path}.kind", "must be 'legacy_human_checkpoint_packet'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("topic_filter"), str):
        result.add(f"{path}.topic_filter", "must be a string")
    if payload.get("truth_source") != "legacy_semantic_review_worklist_human_checkpoint_commands":
        result.add(f"{path}.truth_source", "must be 'legacy_semantic_review_worklist_human_checkpoint_commands'")
    for key in ("checkpoint_item_count", "open_decision_count", "pending_request_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_list(payload.get("checkpoint_items"), f"{path}.checkpoint_items", result)
    if isinstance(payload.get("checkpoint_items"), list):
        if payload.get("checkpoint_item_count") != len(payload["checkpoint_items"]):
            result.add(f"{path}.checkpoint_item_count", "must match checkpoint_items length")
        open_count = 0
        request_count = 0
        for index, item in enumerate(payload["checkpoint_items"]):
            _validate_checkpoint_item(item, f"{path}.checkpoint_items[{index}]", result)
            if isinstance(item, dict) and item.get("mode") == "decide_open_checkpoint":
                open_count += 1
            if isinstance(item, dict) and item.get("mode") == "request_checkpoint":
                request_count += 1
        if payload.get("open_decision_count") != open_count:
            result.add(f"{path}.open_decision_count", "must match decide_open_checkpoint items")
        if payload.get("pending_request_count") != request_count:
            result.add(f"{path}.pending_request_count", "must match request_checkpoint items")
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    if isinstance(payload.get("next_actions"), list) and not all(
        isinstance(value, str) and value for value in payload["next_actions"]
    ):
        result.add(f"{path}.next_actions", "must contain non-empty strings")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_legacy_human_checkpoint_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_human_checkpoint_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_checkpoint_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "latest_review_id", "review_status", "action", "mode", "reason"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("review_status") not in {"needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be a backlog review status")
    if payload.get("mode") not in {"decide_open_checkpoint", "request_checkpoint"}:
        result.add(f"{path}.mode", "must be decide_open_checkpoint or request_checkpoint")
    if payload.get("mode") == "decide_open_checkpoint":
        _require_nonempty_str(payload, "checkpoint_id", path, result)
    if payload.get("mode") == "request_checkpoint" and not isinstance(payload.get("checkpoint_id"), str):
        result.add(f"{path}.checkpoint_id", "must be a string")
    _require_list(payload.get("options"), f"{path}.options", result)
    if isinstance(payload.get("options"), list) and not payload["options"]:
        result.add(f"{path}.options", "must not be empty")
    _validate_command(payload.get("command"), f"{path}.command", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_command(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("action", "latest_review_id", "cli", "mcp", "surface", "effect"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("mcp") not in {"aitp_v5_request_human_checkpoint", "aitp_v5_decide_human_checkpoint"}:
        result.add(f"{path}.mcp", "must be a human checkpoint MCP")
    if payload.get("surface") != "human_checkpoint_record":
        result.add(f"{path}.surface", "must be human_checkpoint_record")
    if payload.get("effect") != "typed_record_write":
        result.add(f"{path}.effect", "must be typed_record_write")
    _require_bool_value(payload.get("can_update_kernel_state"), True, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
