"""Contracts for source reconstruction coverage audits."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_source_reconstruction_audit(payload: dict[str, Any], *, path: str = "source_reconstruction_audit") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_audit":
        result.add(f"{path}.kind", "must be 'source_reconstruction_audit'")
    for key in ("topic_id", "claim_id", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    for key in ("complete", "summary_inputs_trusted", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("required_components", "missing_components", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("components"), f"{path}.components", result)
    if isinstance(payload.get("components"), dict):
        for name, component in payload["components"].items():
            _validate_component(component, f"{path}.components.{name}", result)
    return result


def require_valid_source_reconstruction_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_component(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("status") not in {"satisfied", "missing"}:
        result.add(f"{path}.status", "must be satisfied or missing")
    _require_list(payload.get("record_ids"), f"{path}.record_ids", result)
