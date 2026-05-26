"""Contracts for legacy semantic review worklists."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


def validate_legacy_semantic_review_worklist(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_worklist",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_review_worklist":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_worklist'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
    if not isinstance(payload.get("work_item_count"), int) or payload["work_item_count"] < 0:
        result.add(f"{path}.work_item_count", "must be a non-negative integer")
    _validate_status_counts(payload.get("status_counts"), f"{path}.status_counts", result)
    _validate_pass_readiness_counts(payload.get("pass_readiness_counts"), f"{path}.pass_readiness_counts", result)
    _validate_pass_blocker_counts(payload.get("pass_blocker_counts"), f"{path}.pass_blocker_counts", result)
    if not isinstance(payload.get("next_actions"), list):
        result.add(f"{path}.next_actions", "must be a list")
    items = payload.get("items")
    if not isinstance(items, list):
        result.add(f"{path}.items", "must be a list")
    else:
        for index, item in enumerate(items):
            _validate_worklist_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_legacy_semantic_review_worklist(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_worklist(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_status_counts(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("needs_revision", "inconclusive", "pending"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_pass_readiness_counts(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("blocked", "candidate"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_pass_blocker_counts(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            result.add(path, "keys must be non-empty strings")
        if not isinstance(value, int) or value < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_worklist_item(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in (
        "topic",
        "active_claim_id",
        "review_status",
        "review_priority",
        "latest_review_id",
        "packet_cli",
        "result_cli_template",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("review_status") not in {"needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be a backlog review status")
    if payload.get("review_priority") not in {"critical", "high", "medium", "low"}:
        result.add(f"{path}.review_priority", "must be an allowed review priority")
    for key in (
        "priority_reasons",
        "review_focus",
        "missing_source_components",
        "source_reconstruction_review_refs",
        "satisfied_review_actions",
        "followup_review_actions",
        "review_action_commands",
        "followup_review_commands",
        "repair_candidates",
    ):
        if not isinstance(payload.get(key), list):
            result.add(f"{path}.{key}", "must be a list")
    for index, command in enumerate(payload.get("review_action_commands") or []):
        _validate_review_action_command(command, f"{path}.review_action_commands[{index}]", result)
    for index, command in enumerate(payload.get("followup_review_commands") or []):
        _validate_followup_command(command, f"{path}.followup_review_commands[{index}]", result)
    _validate_pass_readiness(payload.get("pass_readiness"), f"{path}.pass_readiness", result)
    for key in ("priority_score", "repair_candidate_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_pass_readiness(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    if payload.get("status") not in {"blocked", "candidate"}:
        result.add(f"{path}.status", "must be blocked or candidate")
    if not isinstance(payload.get("pass_candidate"), bool):
        result.add(f"{path}.pass_candidate", "must be a boolean")
    if payload.get("status") == "candidate" and payload.get("pass_candidate") is not True:
        result.add(f"{path}.pass_candidate", "must be true when status is candidate")
    if payload.get("status") == "blocked" and payload.get("pass_candidate") is not False:
        result.add(f"{path}.pass_candidate", "must be false when status is blocked")
    if not isinstance(payload.get("latest_review_id"), str):
        result.add(f"{path}.latest_review_id", "must be a string")
    requirements = payload.get("requirements")
    if not isinstance(requirements, dict):
        result.add(f"{path}.requirements", "must be a mapping")
    else:
        for key in (
            "active_claim_present",
            "active_claim_statement_present",
            "source_reconstruction_complete",
            "latest_review_recorded",
            "latest_review_not_needs_revision",
            "no_remaining_review_actions",
            "no_followup_review_actions",
            "archive_sampled_when_needed",
        ):
            if not isinstance(requirements.get(key), bool):
                result.add(f"{path}.requirements.{key}", "must be a boolean")
    for key in ("blockers", "remaining_actions", "followup_review_actions"):
        if not isinstance(payload.get(key), list) or not all(
            isinstance(value, str) for value in payload.get(key, [])
        ):
            result.add(f"{path}.{key}", "must be a list of strings")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_review_action_command(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("action", "latest_review_id", "cli", "mcp", "surface", "effect"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("effect") not in {"orientation_only", "typed_review_record_write", "typed_record_write"}:
        result.add(f"{path}.effect", "must be an allowed effect")
    if payload.get("effect") == "orientation_only" and payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false for orientation-only commands")
    if payload.get("effect") == "typed_review_record_write" and payload.get("can_update_kernel_state") is not True:
        result.add(f"{path}.can_update_kernel_state", "must be true for typed review record writes")
    if payload.get("effect") == "typed_record_write" and payload.get("can_update_kernel_state") is not True:
        result.add(f"{path}.can_update_kernel_state", "must be true for typed record writes")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_followup_command(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("action", "latest_review_id", "result_cli", "result_mcp"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(payload.get("satisfied_review_actions"), list):
        result.add(f"{path}.satisfied_review_actions", "must be a list")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
