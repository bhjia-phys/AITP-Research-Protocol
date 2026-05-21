"""Contracts for adapter record/gate coverage audit payloads."""

from __future__ import annotations

from typing import Any

from brain.v5.adapter_protocols import record_gate_coverage_audit
from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping


def validate_record_gate_coverage_audit(
    payload: dict[str, Any],
    *,
    path: str = "record_gate_coverage_audit",
) -> ContractResult:
    """Validate the public record/gate coverage audit payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    expected = record_gate_coverage_audit()
    for key, expected_value in expected.items():
        if key in {
            "record_protocols",
            "gate_protocols",
            "gated_record_protocols",
            "ungated_record_protocols",
            "extra_gate_protocols",
        }:
            _require_list(payload.get(key), f"{path}.{key}", result)
        if payload.get(key) != expected_value:
            result.add(f"{path}.{key}", f"must be {expected_value!r}")
    return result


def require_valid_record_gate_coverage_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a record/gate coverage audit payload or raise a contract error."""

    result = validate_record_gate_coverage_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
