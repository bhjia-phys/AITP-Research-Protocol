"""Contracts for file-level workspace migration ledgers."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_DECISIONS = {
    "archive_reference",
    "semantic_review_basis",
    "typed_import_candidate",
}
_REVIEW_STATUSES = {
    "archive_accounted",
    "archive_decision_required",
    "duplicate_review_required",
    "import_review_required",
    "semantic_review_required",
}


def validate_workspace_file_migration_ledger(
    payload: dict[str, Any],
    *,
    path: str = "workspace_file_migration_ledger",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_file_migration_ledger":
        result.add(f"{path}.kind", "must be 'aitp_workspace_file_migration_ledger'")
    for key in ("workspace_root", "canonical_topics_root", "canonical_store"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        result.add(f"{path}.summary", "must be a mapping")
        summary = {}
    for key in (
        "file_decision_count",
        "expected_total_file_count",
        "blocking_file_count",
        "root_l2_global_memory_decision_count",
        "root_l2_global_memory_topic_count",
        "root_l2_global_memory_entries_per_topic",
        "root_l2_global_memory_replay_key_count",
        "root_l2_global_memory_max_topic_repetition",
    ):
        if key not in summary:
            continue
        if not isinstance(summary.get(key), int) or summary.get(key) < 0:
            result.add(f"{path}.summary.{key}", "must be a non-negative integer")
    if not isinstance(summary.get("no_omission_check"), bool):
        result.add(f"{path}.summary.no_omission_check", "must be a boolean")
    for key in ("root_l2_global_memory_risk", "root_l2_global_memory_uniform_topic_copy_pattern"):
        if key in summary and not isinstance(summary.get(key), bool):
            result.add(f"{path}.summary.{key}", "must be a boolean")
    if "root_l2_global_memory_risk_reason" in summary and not isinstance(summary.get("root_l2_global_memory_risk_reason"), str):
        result.add(f"{path}.summary.root_l2_global_memory_risk_reason", "must be a string")
    if "root_l2_global_memory_risk_triggers" in summary:
        _validate_string_list(
            summary.get("root_l2_global_memory_risk_triggers"),
            result,
            path=f"{path}.summary.root_l2_global_memory_risk_triggers",
        )
    decisions = payload.get("file_decisions")
    if not isinstance(decisions, list):
        result.add(f"{path}.file_decisions", "must be a list")
        decisions = []
    if isinstance(summary.get("file_decision_count"), int) and len(decisions) != summary.get("file_decision_count"):
        result.add(f"{path}.summary.file_decision_count", "must equal len(file_decisions)")
    for index, item in enumerate(decisions[:50]):
        _validate_decision(item, result, path=f"{path}.file_decisions[{index}]")
    for key in ("orientation_only", "summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if payload.get(key) is not False and key != "orientation_only":
            result.add(f"{path}.{key}", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    return result


def require_valid_workspace_file_migration_ledger(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_file_migration_ledger(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_workspace_file_migration_ledger_progress(
    payload: dict[str, Any],
    *,
    path: str = "workspace_file_migration_ledger_progress",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "aitp_workspace_file_migration_ledger_progress":
        result.add(f"{path}.kind", "must be 'aitp_workspace_file_migration_ledger_progress'")
    for key in (
        "file_decision_count",
        "expected_total_file_count",
        "blocking_file_count",
        "root_l2_global_memory_decision_count",
        "root_l2_global_memory_topic_count",
        "root_l2_global_memory_entries_per_topic",
        "root_l2_global_memory_replay_key_count",
        "root_l2_global_memory_max_topic_repetition",
    ):
        if key not in payload:
            continue
        if not isinstance(payload.get(key), int) or payload.get(key) < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in (
        "no_omission_check",
        "old_store_retirement_safe",
        "semantic_review_required",
        "root_l2_global_memory_risk",
        "root_l2_global_memory_uniform_topic_copy_pattern",
    ):
        if key not in payload:
            continue
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if "root_l2_global_memory_risk_reason" in payload and not isinstance(payload.get("root_l2_global_memory_risk_reason"), str):
        result.add(f"{path}.root_l2_global_memory_risk_reason", "must be a string")
    if "root_l2_global_memory_risk_triggers" in payload:
        _validate_string_list(
            payload.get("root_l2_global_memory_risk_triggers"),
            result,
            path=f"{path}.root_l2_global_memory_risk_triggers",
        )
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_workspace_file_migration_ledger_progress(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_file_migration_ledger_progress(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_decision(item: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(item, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("decision_ref", "source_family", "source_path", "recommended_decision", "review_status"):
        if not isinstance(item.get(key), str) or not item.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if item.get("recommended_decision") not in _DECISIONS:
        result.add(f"{path}.recommended_decision", "must be an allowed migration decision")
    if item.get("review_status") not in _REVIEW_STATUSES:
        result.add(f"{path}.review_status", "must be an allowed review status")
    if not isinstance(item.get("blocks_old_store_retirement"), bool):
        result.add(f"{path}.blocks_old_store_retirement", "must be a boolean")
    if item.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_string_list(value: Any, result: ContractResult, *, path: str) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            result.add(f"{path}[{index}]", "must be a string")
