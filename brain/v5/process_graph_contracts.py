"""Contracts for read-only process graph slices."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping
from brain.v5.moment_policy_contracts import validate_host_agnostic_moment_policy


def validate_process_graph_slice(payload: dict[str, Any], *, path: str = "process_graph_slice") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "process_graph_slice":
        result.add(f"{path}.kind", "must be 'process_graph_slice'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in (
        "nodes",
        "edges",
        "open_obligations",
        "source_backtrace",
        "relation_neighborhood",
        "exploratory_records",
        "trust_boundary_reasons",
        "recommended_moments",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    moment_policy = payload.get("moment_policy")
    _require_mapping(moment_policy, f"{path}.moment_policy", result)
    if isinstance(moment_policy, dict):
        result.extend(validate_host_agnostic_moment_policy(moment_policy, path=f"{path}.moment_policy"))
    _require_mapping(payload.get("record_counts"), f"{path}.record_counts", result)
    _require_mapping(payload.get("truncation"), f"{path}.truncation", result)
    return result


def require_valid_process_graph_slice(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_process_graph_slice(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
