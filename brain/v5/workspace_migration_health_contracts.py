"""Contracts for workspace migration health surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


_STATUSES = {"unknown", "blocked", "review_required", "clear"}
_QUARANTINE_STATUSES = {
    "active_seed_leak_detected",
    "canonical_legacy_l2_seeds_require_review",
    "no_canonical_legacy_l2_seeds",
}


def validate_workspace_migration_health(
    payload: dict[str, Any],
    *,
    path: str = "workspace_migration_health",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "aitp_workspace_migration_health":
        result.add(f"{path}.kind", "must be 'aitp_workspace_migration_health'")
    if payload.get("status") not in _STATUSES:
        result.add(f"{path}.status", "must be an allowed migration health status")
    for key in ("canonical_store", "ledger_status", "truth_source", "legacy_seed_quarantine_status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("legacy_seed_quarantine_status") not in _QUARANTINE_STATUSES:
        result.add(f"{path}.legacy_seed_quarantine_status", "must be an allowed quarantine status")
    if payload.get("truth_source") != "workspace_migration_ledgers_and_canonical_l2_seed_scan":
        result.add(f"{path}.truth_source", "must be 'workspace_migration_ledgers_and_canonical_l2_seed_scan'")
    for key in (
        "file_decision_count",
        "expected_total_file_count",
        "blocking_file_count",
        "root_l2_global_memory_decision_count",
        "root_l2_global_memory_topic_count",
        "canonical_legacy_seed_count",
        "active_legacy_seed_count",
        "legacy_seed_topic_count",
    ):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in (
        "no_omission_check",
        "old_store_retirement_safe",
        "semantic_review_required",
        "root_l2_global_memory_risk",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key in ("legacy_seed_next_actions", "legacy_seed_samples", "next_actions", "summary_lines"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_workspace_migration_health(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_migration_health(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
