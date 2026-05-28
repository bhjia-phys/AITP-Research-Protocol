"""Contracts for goal continuation audit packets."""

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


def validate_goal_continuation_packet(
    payload: dict[str, Any], *, path: str = "goal_continuation_packet"
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "goal_continuation_packet":
        result.add(f"{path}.kind", "must be 'goal_continuation_packet'")
    _require_nonempty_str(payload, "packet_id", path, result)
    _require_nonempty_str(payload, "timestamp", path, result)
    _require_nonempty_str(payload, "objective", path, result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_list(payload.get("changed_files"), f"{path}.changed_files", result)
    _require_list(payload.get("changed_file_stats"), f"{path}.changed_file_stats", result)
    _require_list(payload.get("commits"), f"{path}.commits", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    _require_list(payload.get("blocking_backlog"), f"{path}.blocking_backlog", result)
    _require_list(payload.get("audit_commands"), f"{path}.audit_commands", result)
    _require_mapping(payload.get("verification"), f"{path}.verification", result)
    _require_mapping(payload.get("readiness_outcome"), f"{path}.readiness_outcome", result)
    _require_mapping(payload.get("files"), f"{path}.files", result)
    for index, commit in enumerate(payload.get("commits") or []):
        _validate_commit(commit, f"{path}.commits[{index}]", result)
    for index, stat in enumerate(payload.get("changed_file_stats") or []):
        _validate_file_stat(stat, f"{path}.changed_file_stats[{index}]", result)
    verification = payload.get("verification")
    if isinstance(verification, dict):
        _require_list(verification.get("tests_run"), f"{path}.verification.tests_run", result)
        _require_list(verification.get("smoke_commands"), f"{path}.verification.smoke_commands", result)
    return result


def require_valid_goal_continuation_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_goal_continuation_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_goal_continuation_list(
    payload: dict[str, Any], *, path: str = "goal_continuation_list"
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "goal_continuation_list":
        result.add(f"{path}.kind", "must be 'goal_continuation_list'")
    if not isinstance(payload.get("count"), int):
        result.add(f"{path}.count", "must be an integer")
    _require_list(payload.get("packet_ids"), f"{path}.packet_ids", result)
    _require_list(payload.get("latest_objectives"), f"{path}.latest_objectives", result)
    return result


def require_valid_goal_continuation_list(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_goal_continuation_list(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_commit(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "hash", path, result)
    _require_nonempty_str(value, "subject", path, result)
    for key in ("files_changed", "insertions", "deletions"):
        if not isinstance(value.get(key), int):
            result.add(f"{path}.{key}", "must be an integer")


def _validate_file_stat(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "path", path, result)
    for key in ("insertions", "deletions"):
        if not isinstance(value.get(key), int):
            result.add(f"{path}.{key}", "must be an integer")
