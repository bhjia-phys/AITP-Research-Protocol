"""Public surface contract for the HPC cockpit."""

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


def validate_hpc_cockpit(payload: dict[str, Any], *, path: str = "hpc_cockpit") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "hpc_cockpit":
        result.add(f"{path}.kind", "must be 'hpc_cockpit'")
    _require_nonempty_str(payload, "topic_id", path, result)
    _require_list(payload.get("effective_attempts"), f"{path}.effective_attempts", result)
    _require_list(payload.get("active_jobs"), f"{path}.active_jobs", result)
    _require_list(payload.get("failure_history"), f"{path}.failure_history", result)
    _require_list(payload.get("next_valid_actions"), f"{path}.next_valid_actions", result)
    _require_list(payload.get("conclusions_allowed"), f"{path}.conclusions_allowed", result)
    _require_list(payload.get("conclusions_not_allowed"), f"{path}.conclusions_not_allowed", result)
    _require_mapping(payload.get("lane_counts"), f"{path}.lane_counts", result)
    _require_mapping(payload.get("provenance_gaps"), f"{path}.provenance_gaps", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    return result


def require_valid_hpc_cockpit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_hpc_cockpit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
