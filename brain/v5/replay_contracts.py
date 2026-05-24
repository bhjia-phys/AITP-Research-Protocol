"""Contracts for workspace replay packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_workspace_replay_packet(payload: dict[str, Any], *, path: str = "workspace_replay_packet") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "workspace_replay_packet":
        result.add(f"{path}.kind", "must be 'workspace_replay_packet'")
    for key in ("replay_dir", "derived_from", "adapter_rule"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "kernel_state":
        result.add(f"{path}.derived_from", "must be 'kernel_state'")
    for key in ("truth_source", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("entry_count", "attention_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict) and not payload["files"].get("replay_packet"):
        result.add(f"{path}.files.replay_packet", "must be a non-empty string")
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_list(payload.get("entries"), f"{path}.entries", result)
    if isinstance(payload.get("entries"), list):
        for index, entry in enumerate(payload["entries"]):
            _validate_entry(entry, f"{path}.entries[{index}]", result)
    return result


def require_valid_workspace_replay_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_replay_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("session_id", "topic_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("claim_id", "claim_statement", "confidence_state", "risk_level"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in (
        "missing_outputs",
        "satisfied_outputs",
        "next_actions",
        "missing_source_components",
        "memory_entry_ids",
        "validation_result_ids",
        "attention_reasons",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("source_reconstruction_complete"), bool):
        result.add(f"{path}.source_reconstruction_complete", "must be a boolean")
