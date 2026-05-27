"""Contracts for vNext lane exemplar surfaces."""

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


def validate_lane_exemplar_record(payload: dict[str, Any], *, path: str = "lane_exemplar_record") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "lane_exemplar":
        result.add(f"{path}.kind", "must be 'lane_exemplar'")
    for key in ("exemplar_id", "topic_id", "lane", "title", "summary", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("gates_demonstrated", "artifact_refs", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def validate_lane_exemplar_manifest(payload: dict[str, Any], *, path: str = "lane_exemplar_manifest") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "lane_exemplar_manifest":
        result.add(f"{path}.kind", "must be 'lane_exemplar_manifest'")
    for key in ("required_lanes", "covered_lanes", "missing_lanes", "items"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("lane_status_counts"), f"{path}.lane_status_counts", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_lane_exemplar_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_lane_exemplar_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def require_valid_lane_exemplar_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_lane_exemplar_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
