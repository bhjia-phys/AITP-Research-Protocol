"""Contracts for read-only L2 memory audit surfaces."""

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


def validate_l2_memory_audit(payload: dict[str, Any], *, path: str = "l2_memory_audit") -> ContractResult:
    """Validate a public, read-only L2 memory audit payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    for key in (
        "ok",
        "kind",
        "claim_id",
        "topic_id",
        "truth_source",
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "entry_count",
        "memory_entries",
    ):
        if key not in payload:
            result.add(f"{path}.{key}", "missing required L2 memory audit key")
    _require_bool_value(payload.get("ok"), True, f"{path}.ok", result)
    if payload.get("kind") != "l2_memory_audit":
        result.add(f"{path}.kind", "must be 'l2_memory_audit'")
    _require_nonempty_str(payload, "claim_id", path, result)
    _require_nonempty_str(payload, "topic_id", path, result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    entries = payload.get("memory_entries")
    _require_list(entries, f"{path}.memory_entries", result)
    if isinstance(entries, list):
        if payload.get("entry_count") != len(entries):
            result.add(f"{path}.entry_count", "must equal len(memory_entries)")
        for index, entry in enumerate(entries):
            _validate_l2_memory_audit_entry(entry, f"{path}.memory_entries[{index}]", result)
    elif not isinstance(payload.get("entry_count"), int):
        result.add(f"{path}.entry_count", "must be an integer")
    return result


def require_valid_l2_memory_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an L2 memory audit payload or raise a contract error."""

    result = validate_l2_memory_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_l2_memory_audit_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "entry_id",
        "topic_id",
        "source_claim_id",
        "source_topic_id",
        "statement",
        "memory_kind",
        "scope",
        "source_packet_id",
        "promotion_packet_status",
        "human_checkpoint_id",
        "human_checkpoint_decision",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in (
        "evidence_refs",
        "validation_result_ids",
        "code_state_ids",
        "non_claims",
        "known_failure_modes",
        "missing_links",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
