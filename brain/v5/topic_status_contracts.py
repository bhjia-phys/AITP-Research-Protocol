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
    _validate_compact_context(payload.get("compact_context"), f"{path}.compact_context", result)
    if isinstance(payload.get("topic_state"), dict) and (
        payload["topic_state"].get("compact_context") != payload.get("compact_context")
    ):
        result.add(f"{path}.topic_state.compact_context", "must match bundle compact_context")
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
    for key in ("topic_state", "topic_dashboard", "operator_console", "claim_relation_map", "runtime_protocol", "session_start"):
        _require_nonempty_str(payload, key, path, result)


def _validate_topic_state(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "topic_state":
        result.add(f"{path}.kind", "must be 'topic_state'")
    for key in ("topic_id", "session_id", "context_id", "current_route_choice"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "last_evidence_return",
        "next_bounded_action",
        "blocker_summary",
        "claim_relation_map",
        "compact_context",
    ):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("claim_relation_map"), dict):
        from brain.v5.claim_relation_map_contracts import validate_claim_relation_map

        result.extend(validate_claim_relation_map(payload["claim_relation_map"], path=f"{path}.claim_relation_map"))
    for key in ("summary_inputs_trusted", "can_update_claim_trust"):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)


def _validate_compact_context(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "compact_context_boundary":
        result.add(f"{path}.kind", "must be 'compact_context_boundary'")
    for key in ("fingerprint", "pack_id", "index_status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("index_status") not in {"fresh", "stale"}:
        result.add(f"{path}.index_status", "must be fresh or stale")
    generation = payload.get("source_index_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        result.add(f"{path}.source_index_generation", "must be a positive integer")
    _require_mapping(payload.get("retrieval_coverage"), f"{path}.retrieval_coverage", result)
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)


def _validate_source_records(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topics", "sessions", "claims", "evidence"):
        _require_list(payload.get(key), f"{path}.{key}", result)
