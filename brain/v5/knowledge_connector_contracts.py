"""Contracts for knowledge connector catalog surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping


def validate_knowledge_connector_catalog(
    payload: dict[str, Any],
    *,
    path: str = "knowledge_connector_catalog",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "knowledge_connector_catalog":
        result.add(f"{path}.kind", "must be 'knowledge_connector_catalog'")
    if payload.get("truth_source") != "builtin_connector_registry":
        result.add(f"{path}.truth_source", "must be 'builtin_connector_registry'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_list(payload.get("connectors"), f"{path}.connectors", result)
    if isinstance(payload.get("connector_count"), int) and isinstance(payload.get("connectors"), list):
        if payload["connector_count"] != len(payload["connectors"]):
            result.add(f"{path}.connector_count", "must match number of connectors")
    elif "connector_count" in payload:
        result.add(f"{path}.connector_count", "must be an integer")
    if isinstance(payload.get("connectors"), list):
        for index, connector in enumerate(payload["connectors"]):
            _validate_connector(connector, f"{path}.connectors[{index}]", result)
    return result


def require_valid_knowledge_connector_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_knowledge_connector_catalog(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_connector(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "connector_id",
        "connector_kind",
        "display_name",
        "purpose",
        "skill_ref",
        "backend_role",
        "recommended_when",
    ):
        if not isinstance(payload.get(key), str) or not payload[key]:
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(payload.get("is_required"), bool):
        result.add(f"{path}.is_required", "must be a boolean")
    for key in (
        "supported_activities",
        "expected_retrieval_targets",
        "location_ref_targets",
        "protocol_hooks",
        "required_kernel_followup_records",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("truth_policy"), f"{path}.truth_policy", result)
    if isinstance(payload.get("truth_policy"), dict):
        _require_bool_value(
            payload["truth_policy"].get("retrieved_notes_are_truth_source"),
            False,
            f"{path}.truth_policy.retrieved_notes_are_truth_source",
            result,
        )
        _require_bool_value(
            payload["truth_policy"].get("source_backed_evidence_required"),
            True,
            f"{path}.truth_policy.source_backed_evidence_required",
            result,
        )
