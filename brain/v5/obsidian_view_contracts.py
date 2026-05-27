"""Contracts for orientation-only Obsidian view bundles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_l2_obsidian_view_bundle(payload: dict[str, Any], *, path: str = "l2_obsidian_view_bundle") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "l2_obsidian_view_bundle":
        result.add(f"{path}.kind", "must be 'l2_obsidian_view_bundle'")
    for key in ("view_dir", "derived_from"):
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
    if not isinstance(payload.get("memory_entry_count"), int) or payload["memory_entry_count"] < 0:
        result.add(f"{path}.memory_entry_count", "must be a non-negative integer")
    for key in ("physics_object_count", "object_relation_count", "sensemaking_report_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict):
        _require_nonempty_str(payload["files"], "overview", f"{path}.files", result)
        _require_nonempty_str(payload["files"], "graph", f"{path}.files", result)
        _require_list(payload["files"].get("entries"), f"{path}.files.entries", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    if isinstance(payload.get("source_records"), dict):
        for key in (
            "memory_entries",
            "claims",
            "evidence",
            "validation_results",
            "physics_objects",
            "object_relations",
            "sensemaking_reports",
        ):
            _require_list(payload["source_records"].get(key), f"{path}.source_records.{key}", result)
    return result


def require_valid_l2_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_l2_obsidian_view_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
