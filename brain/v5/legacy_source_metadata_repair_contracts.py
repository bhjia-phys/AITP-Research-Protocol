"""Contracts for legacy source metadata repair packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_source_metadata_repair_packet(
    payload: dict[str, Any],
    *,
    path: str = "legacy_source_metadata_repair_packet",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_source_metadata_repair_packet":
        result.add(f"{path}.kind", "must be 'legacy_source_metadata_repair_packet'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("topic_filter"), str):
        result.add(f"{path}.topic_filter", "must be a string")
    if payload.get("truth_source") != "legacy_semantic_review_worklist_remaining_actions":
        result.add(f"{path}.truth_source", "must be 'legacy_semantic_review_worklist_remaining_actions'")
    if not isinstance(payload.get("repair_item_count"), int) or payload["repair_item_count"] < 0:
        result.add(f"{path}.repair_item_count", "must be a non-negative integer")
    _require_list(payload.get("repair_items"), f"{path}.repair_items", result)
    if isinstance(payload.get("repair_items"), list):
        if payload.get("repair_item_count") != len(payload["repair_items"]):
            result.add(f"{path}.repair_item_count", "must match repair_items length")
        for index, item in enumerate(payload["repair_items"]):
            _validate_repair_item(item, f"{path}.repair_items[{index}]", result)
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


def require_valid_legacy_source_metadata_repair_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_source_metadata_repair_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_repair_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "latest_review_id", "review_status", "followup_result_cli"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("review_status") not in {"needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be a backlog review status")
    for key in (
        "source_metadata_actions",
        "reviewed_legacy_refs",
        "reviewed_typed_refs",
        "reference_location_commands",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("source_metadata_actions"), list) and not payload["source_metadata_actions"]:
        result.add(f"{path}.source_metadata_actions", "must not be empty")
    if isinstance(payload.get("reference_location_commands"), list) and not payload["reference_location_commands"]:
        result.add(f"{path}.reference_location_commands", "must not be empty")
    for index, command in enumerate(payload.get("reference_location_commands") or []):
        _validate_reference_location_command(command, f"{path}.reference_location_commands[{index}]", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_reference_location_command(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("action", "latest_review_id", "cli", "mcp", "surface", "effect"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("mcp") != "aitp_v5_record_reference_location":
        result.add(f"{path}.mcp", "must be aitp_v5_record_reference_location")
    if payload.get("surface") != "reference_location_record":
        result.add(f"{path}.surface", "must be reference_location_record")
    if payload.get("effect") != "typed_record_write":
        result.add(f"{path}.effect", "must be typed_record_write")
    _require_bool_value(payload.get("can_update_kernel_state"), True, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
