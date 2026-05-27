"""Contracts for vNext topic status bundles."""

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


def validate_topic_status_bundle(payload: dict[str, Any], *, path: str = "topic_status_bundle") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "topic_status_bundle":
        result.add(f"{path}.kind", "must be 'topic_status_bundle'")
    for key in ("topic_id", "session_id", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    for key, expected in (
        ("truth_source", False),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    _validate_files(payload.get("files"), f"{path}.files", result)
    _validate_topic_state(payload.get("topic_state"), f"{path}.topic_state", result)
    _validate_source_records(payload.get("source_records"), f"{path}.source_records", result)
    return result


def require_valid_topic_status_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_topic_status_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_files(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic_state", "topic_dashboard", "operator_console", "runtime_protocol", "session_start"):
        _require_nonempty_str(payload, key, path, result)


def _validate_topic_state(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "topic_state":
        result.add(f"{path}.kind", "must be 'topic_state'")
    for key in ("topic_id", "session_id", "context_id", "current_route_choice"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("last_evidence_return", "next_bounded_action", "blocker_summary"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("summary_inputs_trusted", "can_update_claim_trust"):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)


def _validate_source_records(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topics", "sessions", "claims", "evidence"):
        _require_list(payload.get(key), f"{path}.{key}", result)
