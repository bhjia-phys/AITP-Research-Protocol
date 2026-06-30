"""Contracts for active-claim focus reconciliation surfaces."""

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


def validate_active_claim_focus_reconciliation(
    payload: dict[str, Any],
    *,
    path: str = "active_claim_focus_reconciliation",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "active_claim_focus_reconciliation":
        result.add(f"{path}.kind", "must be 'active_claim_focus_reconciliation'")
    for key in ("status", "session_id", "requested_session_id", "relation_map_scope", "recommended_next_action"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("relation_map_scope") != "active_claim_only":
        result.add(f"{path}.relation_map_scope", "must be active_claim_only")
    for key in ("warnings", "candidate_sibling_claims", "available_options"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("active_claim"), f"{path}.active_claim", result)
    _require_mapping(payload.get("record_distribution"), f"{path}.record_distribution", result)
    for key, expected in (
        ("truth_source", False),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("trust_update_allowed", False),
        ("can_rebind_without_confirmation", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    if not isinstance(payload.get("not_authoritative_for_current_goal_if_rebind_needed"), bool):
        result.add(f"{path}.not_authoritative_for_current_goal_if_rebind_needed", "must be a boolean")
    for index, candidate in enumerate(payload.get("candidate_sibling_claims") or []):
        _validate_candidate(candidate, f"{path}.candidate_sibling_claims[{index}]", result)
    return result


def require_valid_active_claim_focus_reconciliation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_active_claim_focus_reconciliation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_active_claim_rebind_proposal(
    payload: dict[str, Any],
    *,
    path: str = "active_claim_rebind_proposal",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "active_claim_rebind_proposal":
        result.add(f"{path}.kind", "must be 'active_claim_rebind_proposal'")
    for key in ("status", "session_id", "requested_session_id", "topic_id", "old_claim_id", "reason"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("candidate_claim"), f"{path}.candidate_claim", result)
    _require_mapping(payload.get("proposed_operation"), f"{path}.proposed_operation", result)
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("trust_update_allowed", False),
        ("can_apply_without_confirmation", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_active_claim_rebind_proposal(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_active_claim_rebind_proposal(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_active_claim_rebind_confirmation(
    payload: dict[str, Any],
    *,
    path: str = "active_claim_rebind_confirmation",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "active_claim_rebind_confirmation":
        result.add(f"{path}.kind", "must be 'active_claim_rebind_confirmation'")
    for key in ("status", "session_id", "requested_session_id", "topic_id", "old_claim_id", "new_claim_id", "audit_id"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("audit_record"), f"{path}.audit_record", result)
    _require_mapping(payload.get("session_binding"), f"{path}.session_binding", result)
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    for key, expected in (
        ("orientation_only", False),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
        ("trust_update_allowed", False),
        ("evidence_trust_update_allowed", False),
        ("l2_memory_update_allowed", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_active_claim_rebind_confirmation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_active_claim_rebind_confirmation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_candidate(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("claim_id", "statement_excerpt", "latest_update"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("matching_reasons", "sample_record_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("recent_record_count", "total_record_count", "orientation_only_record_count"):
        if not isinstance(payload.get(key), int) or payload.get(key) < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_bool_value(payload.get("trust_promotion_allowed"), False, f"{path}.trust_promotion_allowed", result)
