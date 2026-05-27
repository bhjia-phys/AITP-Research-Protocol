"""Contracts for legacy executable evidence packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_executable_evidence_packet(
    payload: dict[str, Any],
    *,
    path: str = "legacy_executable_evidence_packet",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_executable_evidence_packet":
        result.add(f"{path}.kind", "must be 'legacy_executable_evidence_packet'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("topic_filter"), str):
        result.add(f"{path}.topic_filter", "must be a string")
    if payload.get("truth_source") != "legacy_semantic_review_worklist_validation_and_tool_run_commands":
        result.add(f"{path}.truth_source", "must be 'legacy_semantic_review_worklist_validation_and_tool_run_commands'")
    for key in ("evidence_item_count", "executable_action_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_list(payload.get("evidence_items"), f"{path}.evidence_items", result)
    if isinstance(payload.get("evidence_items"), list):
        if payload.get("evidence_item_count") != len(payload["evidence_items"]):
            result.add(f"{path}.evidence_item_count", "must match evidence_items length")
        action_count = 0
        for index, item in enumerate(payload["evidence_items"]):
            _validate_evidence_item(item, f"{path}.evidence_items[{index}]", result)
            if isinstance(item, dict) and isinstance(item.get("executable_actions"), list):
                action_count += len(item["executable_actions"])
        if payload.get("executable_action_count") != action_count:
            result.add(f"{path}.executable_action_count", "must match executable_actions length")
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


def require_valid_legacy_executable_evidence_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_executable_evidence_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_evidence_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "latest_review_id", "review_status", "followup_result_cli"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("review_status") not in {"needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be a backlog review status")
    for key in (
        "executable_actions",
        "validation_commands",
        "tool_run_commands",
        "reviewed_legacy_refs",
        "reviewed_typed_refs",
        "evidence_refs",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("executable_actions"), list) and not payload["executable_actions"]:
        result.add(f"{path}.executable_actions", "must not be empty")
    if not (payload.get("validation_commands") or payload.get("tool_run_commands")):
        result.add(path, "must include at least one validation or tool-run command")
    for key in ("validation_commands", "tool_run_commands"):
        for index, command in enumerate(payload.get(key) or []):
            _validate_executable_command(command, f"{path}.{key}[{index}]", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_executable_command(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("action", "latest_review_id", "cli", "mcp", "surface", "effect"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("surface") not in {"validation_result_record", "tool_run_record"}:
        result.add(f"{path}.surface", "must be validation_result_record or tool_run_record")
    if payload.get("surface") == "validation_result_record" and payload.get("mcp") != "aitp_v5_record_validation_result":
        result.add(f"{path}.mcp", "must be aitp_v5_record_validation_result")
    if payload.get("surface") == "tool_run_record" and payload.get("mcp") != "aitp_v5_record_tool_run":
        result.add(f"{path}.mcp", "must be aitp_v5_record_tool_run")
    if payload.get("effect") != "typed_record_write":
        result.add(f"{path}.effect", "must be typed_record_write")
    _require_bool_value(payload.get("can_update_kernel_state"), True, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
