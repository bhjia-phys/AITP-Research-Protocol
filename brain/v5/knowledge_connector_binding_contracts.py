"""Contracts for workspace-local knowledge connector binding surfaces."""

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


def validate_knowledge_connector_binding_registry(
    payload: dict[str, Any],
    *,
    path: str = "knowledge_connector_binding_registry",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "knowledge_connector_binding_registry":
        result.add(f"{path}.kind", "must be 'knowledge_connector_binding_registry'")
    if payload.get("truth_source") != "workspace_connector_binding_config":
        result.add(f"{path}.truth_source", "must be 'workspace_connector_binding_config'")
    if payload.get("state_effect") not in {"read_only", "knowledge_connector_binding_config_write"}:
        result.add(f"{path}.state_effect", "must be read_only or knowledge_connector_binding_config_write")
    for key in ("workspace_config_path", "state_effect"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("known_connector_ids", "bindings", "missing_connector_ids", "required_followup_for_use"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("binding_count"), int) or payload["binding_count"] < 0:
        result.add(f"{path}.binding_count", "must be a non-negative integer")
    elif isinstance(payload.get("bindings"), list) and payload["binding_count"] != len(payload["bindings"]):
        result.add(f"{path}.binding_count", "must match number of bindings")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("can_create_evidence", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    for index, binding in enumerate(payload.get("bindings") or []):
        _validate_binding(binding, f"{path}.bindings[{index}]", result)
    if "connectors" in payload:
        _require_list(payload.get("connectors"), f"{path}.connectors", result)
    return result


def require_valid_knowledge_connector_binding_registry(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_knowledge_connector_binding_registry(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_binding(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("binding_id", "connector_id", "label", "root_uri", "priority", "status", "retrieval_boundary"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("file_globs", "domain_hints", "topic_hints"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
