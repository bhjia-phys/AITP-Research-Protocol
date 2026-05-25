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


def validate_source_reconstruction_manifest(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_manifest":
        result.add(f"{path}.kind", "must be 'source_reconstruction_manifest'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    for key in ("claim_count", "complete_claim_count", "incomplete_claim_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("missing_component_counts"), f"{path}.missing_component_counts", result)
    if isinstance(payload.get("missing_component_counts"), dict):
        for key in (
            "definitions",
            "assumptions_or_scope",
            "source_locations",
            "dependency_graph",
            "reconstruction_path",
            "failure_conditions",
        ):
            if not isinstance(payload["missing_component_counts"].get(key), int) or payload["missing_component_counts"][key] < 0:
                result.add(f"{path}.missing_component_counts.{key}", "must be a non-negative integer")
    for key in ("items", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in (
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if isinstance(payload.get("items"), list):
        for index, item in enumerate(payload["items"]):
            _validate_manifest_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_source_reconstruction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_manifest(payload)
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


def _validate_manifest_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic_id", "claim_id", "status", "review_priority", "audit_cli", "audit_mcp"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(payload.get("claim_statement"), str):
        result.add(f"{path}.claim_statement", "must be a string")
    if payload.get("status") not in {"complete", "incomplete"}:
        result.add(f"{path}.status", "must be complete or incomplete")
    if payload.get("review_priority") not in {"high", "low"}:
        result.add(f"{path}.review_priority", "must be high or low")
    for key in ("missing_components", "satisfied_components", "source_refs", "recommended_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
