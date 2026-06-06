"""Contracts for host-agnostic moment policy payloads."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping


_DECISION_TYPES = {"recording", "brainstorming", "backtrace", "trust_boundary"}


def validate_host_agnostic_moment_policy(
    payload: dict[str, Any],
    *,
    path: str = "host_agnostic_moment_policy",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "host_agnostic_moment_policy":
        result.add(f"{path}.kind", "must be 'host_agnostic_moment_policy'")
    if payload.get("derived_from") != "process_graph_slice":
        result.add(f"{path}.derived_from", "must be 'process_graph_slice'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("policy_axes", "decisions", "recommended_moments", "trust_boundary_reasons"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("decisions"), list):
        for index, decision in enumerate(payload["decisions"]):
            _validate_decision(decision, f"{path}.decisions[{index}]", result)
    return result


def require_valid_host_agnostic_moment_policy(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_host_agnostic_moment_policy(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_decision(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("moment", "decision_type", "action_kind", "reason", "target_type", "target_id"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("decision_type") not in _DECISION_TYPES:
        result.add(f"{path}.decision_type", f"must be one of {sorted(_DECISION_TYPES)}")
    for key in ("required_now", "trust_boundary", "summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key in ("missing_components", "record_entrypoints", "exploration_entrypoints", "required_before_trust_change"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
