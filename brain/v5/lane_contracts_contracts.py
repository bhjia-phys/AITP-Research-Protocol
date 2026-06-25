"""Public surface contract for typed lane contracts."""

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


def validate_lane_contract_record(
    payload: dict[str, Any], *, path: str = "lane_contract_record"
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "lane_contract":
        result.add(f"{path}.kind", "must be 'lane_contract'")
    _require_nonempty_str(payload, "contract_id", path, result)
    _require_nonempty_str(payload, "topic_id", path, result)
    _require_list(payload.get("forbidden_roots"), f"{path}.forbidden_roots", result)
    _require_list(payload.get("preferred_clean_roots"), f"{path}.preferred_clean_roots", result)
    _require_list(payload.get("final_allowlist"), f"{path}.final_allowlist", result)
    _require_list(payload.get("final_rules"), f"{path}.final_rules", result)
    _require_list(payload.get("notes"), f"{path}.notes", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    return result


def require_valid_lane_contract_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_lane_contract_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
