# Compatibility shard 2 for legacy_semantic_review_contracts.
from __future__ import annotations

def _validate_file_review_scope(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    if payload.get("kind") != "legacy_file_review_scope":
        result.add(f"{path}.kind", "must be 'legacy_file_review_scope'")
    if payload.get("scope_status") not in {"ready", "empty", "ledger_unavailable", "invalid_ledger"}:
        result.add(f"{path}.scope_status", "must be an allowed scope status")
    for key in ("topic", "ledger_path", "ledger_status", "truth_source"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in ("file_decision_count", "blocking_file_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("review_status_counts", "decision_counts", "source_family_counts"):
        if not isinstance(payload.get(key), dict):
            result.add(f"{path}.{key}", "must be a mapping")
    for key in ("all_file_decision_refs", "required_review_refs"):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    if not isinstance(payload.get("file_decisions"), list):
        result.add(f"{path}.file_decisions", "must be a list")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")

def _validate_current_recovery_focus(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    if payload.get("kind") != "legacy_current_recovery_focus":
        result.add(f"{path}.kind", "must be 'legacy_current_recovery_focus'")
    for key in (
        "topic",
        "recovery_status",
        "session_id",
        "active_claim_id",
        "migration_active_claim_id",
        "recovery_selection_source",
        "next_valid_action",
        "recovery_gap",
        "truth_source",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in ("active_claim_divergence", "has_relation_map"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
