"""Contracts for canonical legacy L2 seed audits."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


_QUARANTINE_STATUSES = {
    "active_seed_leak_detected",
    "canonical_legacy_l2_seeds_require_review",
    "no_canonical_legacy_l2_seeds",
}


def validate_canonical_legacy_l2_seed_audit(
    payload: dict[str, Any],
    *,
    path: str = "canonical_legacy_l2_seed_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "canonical_legacy_l2_seed_audit":
        result.add(f"{path}.kind", "must be 'canonical_legacy_l2_seed_audit'")
    for key in ("canonical_store", "memory_entries_dir", "truth_source", "quarantine_status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "canonical_memory_l2_seed_scan":
        result.add(f"{path}.truth_source", "must be 'canonical_memory_l2_seed_scan'")
    if payload.get("quarantine_status") not in _QUARANTINE_STATUSES:
        result.add(f"{path}.quarantine_status", "must be an allowed quarantine status")
    for key in (
        "total_memory_file_count",
        "legacy_seed_count",
        "active_legacy_seed_count",
        "legacy_seed_topic_count",
    ):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("status_counts", "topic_counts", "memory_kind_counts"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    _require_list(payload.get("sample_entries"), f"{path}.sample_entries", result)
    if isinstance(payload.get("sample_entries"), list):
        for index, item in enumerate(payload["sample_entries"][:50]):
            _validate_seed_entry(item, result, path=f"{path}.sample_entries[{index}]")
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_canonical_legacy_l2_seed_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_canonical_legacy_l2_seed_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_seed_entry(item: Any, result: ContractResult, *, path: str) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("entry_id", "canonical_rel_path"):
        _require_nonempty_str(item, key, path, result)
    if not isinstance(item.get("status"), str):
        result.add(f"{path}.status", "must be a string")
    if item.get("requires_semantic_l2_reassignment") is not True:
        result.add(f"{path}.requires_semantic_l2_reassignment", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
