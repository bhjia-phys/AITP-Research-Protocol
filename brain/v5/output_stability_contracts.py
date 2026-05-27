"""Contracts for stable final-output profile records."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_nonempty_str,
)

_STATUSES = {"active", "superseded", "draft"}


def validate_final_output_profile(payload: dict[str, Any], *, path: str = "final_output_profile") -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "final_output_profile":
        result.add(f"{path}.kind", "must be 'final_output_profile'")
    for key in ("profile_id", "topic_id", "output_version", "audience", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in _STATUSES:
        result.add(f"{path}.status", f"must be one of {sorted(_STATUSES)}")
    for key in ("stable_sections", "flexible_sections"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_final_output_profile(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_final_output_profile(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
