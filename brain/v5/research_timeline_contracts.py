"""Contracts for read-only research timeline surfaces."""

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


def validate_research_timeline(payload: dict[str, Any], *, path: str = "research_timeline") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "research_timeline":
        result.add(f"{path}.kind", "must be 'research_timeline'")
    for key in ("session_id", "topic_id", "claim_id", "scope", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("events", "previous_failed_attempts", "wrong_or_superseded_routes"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("latest_results", "continuation_state", "timeline_policy", "source_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("event_count"), int):
        result.add(f"{path}.event_count", "must be an integer")
    for index, event in enumerate(payload.get("events") or []):
        _validate_event(event, f"{path}.events[{index}]", result)
    for index, attempt in enumerate(payload.get("previous_failed_attempts") or []):
        _validate_attempt(attempt, f"{path}.previous_failed_attempts[{index}]", result)
    policy = payload.get("timeline_policy")
    if isinstance(policy, dict):
        for key, expected in (
            ("summary_inputs_trusted", False),
            ("orientation_only", True),
            ("can_update_kernel_state", False),
            ("can_update_claim_trust", False),
            ("can_rebind_without_confirmation", False),
            ("validation_result_is_not_claim_support_by_itself", True),
        ):
            _require_bool_value(policy.get(key), expected, f"{path}.timeline_policy.{key}", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_research_timeline(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_research_timeline(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_event(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("record_ref", "record_kind", "record_id", "event_time", "time_source", "classification", "summary"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("refs"), f"{path}.refs", result)
    if not isinstance(payload.get("orientation_only"), bool):
        result.add(f"{path}.orientation_only", "must be a boolean")
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_attempt(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("record_ref", "record_kind", "classification", "summary", "continuation_boundary"):
        _require_nonempty_str(payload, key, path, result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
