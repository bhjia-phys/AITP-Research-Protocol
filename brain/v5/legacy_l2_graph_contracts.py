"""Contracts for legacy L2 graph migration planning manifests."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_l2_graph_manifest(
    payload: dict[str, Any],
    *,
    path: str = "legacy_l2_graph_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_l2_graph_manifest":
        result.add(f"{path}.kind", "must be 'legacy_l2_graph_manifest'")
    for key in ("legacy_l2_dir", "legacy_shape", "typed_migration_status", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "legacy_l2_filesystem":
        result.add(f"{path}.truth_source", "must be 'legacy_l2_filesystem'")
    if payload.get("legacy_shape") not in {"global_l2_graph", "missing"}:
        result.add(f"{path}.legacy_shape", "must be global_l2_graph or missing")
    if payload.get("typed_migration_status") not in {
        "needs_typed_l2_migration",
        "no_legacy_l2_records_found",
        "missing_legacy_l2_dir",
    }:
        result.add(f"{path}.typed_migration_status", "must be an allowed migration status")
    _require_mapping(payload.get("counts"), f"{path}.counts", result)
    if isinstance(payload.get("counts"), dict):
        for key in ("entries", "graph_nodes", "graph_edges", "graph_steps", "graph_towers", "index_files"):
            if not isinstance(payload["counts"].get(key), int) or payload["counts"][key] < 0:
                result.add(f"{path}.counts.{key}", "must be a non-negative integer")
    for key in ("entries_by_role", "entries_by_status"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("entry_samples", "obsidian_view_targets", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_legacy_l2_graph_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_l2_graph_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
