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
        "historical",
        "misrouted",
        "cross_topic_references",
        "warnings",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_nonempty_str(payload, "relation_map_scope", path, result)
    if payload.get("relation_map_scope") != "active_claim_only":
        result.add(f"{path}.relation_map_scope", "must be active_claim_only")
    if not isinstance(payload.get("not_authoritative_for_current_goal_if_rebind_needed"), bool):
        result.add(f"{path}.not_authoritative_for_current_goal_if_rebind_needed", "must be a boolean")
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    _validate_conclusion(payload.get("current_conclusion"), f"{path}.current_conclusion", result)
    _validate_source_records(payload.get("source_records"), f"{path}.source_records", result)
    _validate_topic_claim_boundaries(payload.get("topic_claim_boundaries"), f"{path}.topic_claim_boundaries", result)
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
    for key in (
        "claims",
        "evidence",
        "tool_runs",
        "claim_statuses",
        "proof_obligations",
        "object_relations",
        "sibling_claims",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)


def _validate_topic_claim_boundaries(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "topic_claim_boundaries":
        result.add(f"{path}.kind", "must be 'topic_claim_boundaries'")
    _require_nonempty_str(payload, "boundary_rule", path, result)
    _require_list(payload.get("sibling_claims"), f"{path}.sibling_claims", result)
    _validate_conclusion(payload.get("current_conclusion"), f"{path}.current_conclusion", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for index, item in enumerate(payload.get("sibling_claims") or []):
        _require_mapping(item, f"{path}.sibling_claims[{index}]", result)
        if isinstance(item, dict):
            _require_nonempty_str(item, "claim_id", f"{path}.sibling_claims[{index}]", result)
            _require_nonempty_str(item, "statement_excerpt", f"{path}.sibling_claims[{index}]", result)


def _validate_relation_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("record_kind", "record_id", "relation_to_claim", "status", "summary", "reason"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("source_refs", "evidence_refs", "tool_run_ids", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
