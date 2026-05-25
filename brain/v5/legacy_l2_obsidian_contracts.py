"""Contracts for legacy L2 orientation-only Obsidian view bundles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_l2_obsidian_view_bundle(
    payload: dict[str, Any],
    *,
    path: str = "legacy_l2_obsidian_view_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_l2_obsidian_view_bundle":
        result.add(f"{path}.kind", "must be 'legacy_l2_obsidian_view_bundle'")
    for key in ("view_dir", "legacy_l2_dir", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "legacy_l2_filesystem":
        result.add(f"{path}.derived_from", "must be legacy_l2_filesystem")
    for key in ("legacy_entry_count", "memory_entry_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict):
        for key in ("overview", "entries_index"):
            _require_nonempty_str(payload["files"], key, f"{path}.files", result)
    for key in ("entries_by_role", "entries_by_status", "graph_counts", "source_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("graph_counts"), dict):
        for key in ("graph_nodes", "graph_edges", "graph_steps", "graph_towers"):
            if not isinstance(payload["graph_counts"].get(key), int) or payload["graph_counts"][key] < 0:
                result.add(f"{path}.graph_counts.{key}", "must be a non-negative integer")
    if isinstance(payload.get("source_records"), dict):
        for key in ("legacy_entries", "memory_entries"):
            _require_list(payload["source_records"].get(key), f"{path}.source_records.{key}", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key in ("truth_source", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_legacy_l2_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_l2_obsidian_view_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
