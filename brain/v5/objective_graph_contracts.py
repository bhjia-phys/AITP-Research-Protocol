"""Contracts for objective graph and compact brief surfaces."""

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


def validate_objective_graph(payload: dict[str, Any], *, path: str = "objective_graph") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "objective_graph":
        result.add(f"{path}.kind", "must be 'objective_graph'")
    _require_nonempty_str(payload, "topic_id", path, result)
    _require_nonempty_str(payload, "session_id", path, result)
    _require_mapping(payload.get("current_objective"), f"{path}.current_objective", result)
    _require_list(payload.get("active_work_packages"), f"{path}.active_work_packages", result)
    _require_list(payload.get("work_packages"), f"{path}.work_packages", result)
    _require_list(payload.get("claims"), f"{path}.claims", result)
    _require_list(payload.get("artifacts"), f"{path}.artifacts", result)
    _require_list(payload.get("deliverables"), f"{path}.deliverables", result)
    _require_list(payload.get("blockers"), f"{path}.blockers", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_objective_graph(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_objective_graph(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_compact_execution_brief(
    payload: dict[str, Any],
    *,
    path: str = "compact_execution_brief",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "compact_execution_brief":
        result.add(f"{path}.kind", "must be 'compact_execution_brief'")
    _require_nonempty_str(payload, "topic_id", path, result)
    _require_nonempty_str(payload, "session_id", path, result)
    _require_mapping(payload.get("current_objective"), f"{path}.current_objective", result)
    _require_mapping(payload.get("active_work_package"), f"{path}.active_work_package", result)
    _require_list(payload.get("relevant_claims"), f"{path}.relevant_claims", result)
    _require_list(payload.get("can_say"), f"{path}.can_say", result)
    _require_list(payload.get("cannot_say"), f"{path}.cannot_say", result)
    _require_list(payload.get("blockers"), f"{path}.blockers", result)
    _require_list(payload.get("next_valid_actions"), f"{path}.next_valid_actions", result)
    _require_list(payload.get("recent_relevant_artifacts"), f"{path}.recent_relevant_artifacts", result)
    _require_list(payload.get("warnings"), f"{path}.warnings", result)
    _require_nonempty_str(payload, "relation_map_scope", path, result)
    if payload.get("relation_map_scope") != "active_claim_only":
        result.add(f"{path}.relation_map_scope", "must be active_claim_only")
    if not isinstance(payload.get("not_authoritative_for_current_goal_if_rebind_needed"), bool):
        result.add(f"{path}.not_authoritative_for_current_goal_if_rebind_needed", "must be a boolean")
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    _require_mapping(payload.get("expand"), f"{path}.expand", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_list(payload.get("lines"), f"{path}.lines", result)
    if isinstance(payload.get("lines"), list) and len(payload["lines"]) > 40:
        result.add(f"{path}.lines", "must default to at most 40 lines")
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_compact_execution_brief(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_compact_execution_brief(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
