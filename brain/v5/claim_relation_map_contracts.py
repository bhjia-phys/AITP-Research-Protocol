"""Contracts for derived claim relation maps."""

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


def validate_claim_relation_map(payload: dict[str, Any], *, path: str = "claim_relation_map") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "claim_relation_map":
        result.add(f"{path}.kind", "must be 'claim_relation_map'")
    for key in ("topic_id", "session_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "supported_by",
        "limited_by",
        "contradicted_by",
        "not_tested_by",
        "object_relations",
        "key_object_relations",
        "current_blockers",
        "next_valid_actions",
        "derived_from",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _validate_conclusion(payload.get("current_conclusion"), f"{path}.current_conclusion", result)
    _validate_source_records(payload.get("source_records"), f"{path}.source_records", result)
    for key, expected in (
        ("truth_source", False),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("trust_update_allowed", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    for bucket in ("supported_by", "limited_by", "contradicted_by", "not_tested_by"):
        if isinstance(payload.get(bucket), list):
            for index, entry in enumerate(payload[bucket]):
                _validate_relation_entry(entry, f"{path}.{bucket}[{index}]", result)
    return result


def require_valid_claim_relation_map(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_claim_relation_map(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_conclusion(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_list(payload.get("can_say"), f"{path}.can_say", result)
    _require_list(payload.get("cannot_say"), f"{path}.cannot_say", result)


def _validate_source_records(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("claims", "evidence", "tool_runs", "claim_statuses", "proof_obligations", "object_relations"):
        _require_list(payload.get(key), f"{path}.{key}", result)


def _validate_relation_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("record_kind", "record_id", "relation_to_claim", "status", "summary", "reason"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("source_refs", "evidence_refs", "tool_run_ids", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
