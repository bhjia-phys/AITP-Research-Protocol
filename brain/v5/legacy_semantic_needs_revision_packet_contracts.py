"""Contracts for legacy semantic needs-revision basis packets."""

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


def validate_legacy_semantic_needs_revision_basis_packet(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_needs_revision_basis_packet",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_semantic_needs_revision_basis_packet":
        result.add(f"{path}.kind", "must be 'legacy_semantic_needs_revision_basis_packet'")
    for key in (
        "run_id",
        "migration_dir",
        "workspace",
        "topic",
        "active_claim_id",
        "latest_review_id",
        "review_status",
        "needs_revision_result_cli",
        "truth_source",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("review_status") != "inconclusive":
        result.add(f"{path}.review_status", "must be 'inconclusive'")
    if payload.get("truth_source") != "legacy_semantic_needs_revision_basis_queue_and_review_packet":
        result.add(
            f"{path}.truth_source",
            "must be 'legacy_semantic_needs_revision_basis_queue_and_review_packet'",
        )
    for key in (
        "blocking_classes",
        "pass_blockers",
        "remaining_actions",
        "required_actions",
        "legacy_review_refs",
        "review_basis_refs",
        "review_action_commands",
        "likely_repair_basis",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _validate_review_basis(payload.get("review_basis"), f"{path}.review_basis", result)
    _validate_repair_plan(payload.get("repair_plan"), f"{path}.repair_plan", result)
    for index, item in enumerate(payload.get("likely_repair_basis") or []):
        _validate_likely_basis(item, f"{path}.likely_repair_basis[{index}]", result)
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_legacy_semantic_needs_revision_basis_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_needs_revision_basis_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_review_basis(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "reviewed_legacy_refs",
        "reviewed_typed_refs",
        "evidence_refs",
        "validation_result_ids",
        "source_reconstruction_review_refs",
        "open_checkpoint_refs",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)


def _validate_likely_basis(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("action", "basis_kind"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("candidate_command"), f"{path}.candidate_command", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_repair_plan(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("surface", "repair_status", "cli", "mcp"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("surface") != "legacy_semantic_repair_plan":
        result.add(f"{path}.surface", "must be legacy_semantic_repair_plan")
    if not isinstance(payload.get("proposed_repair_count"), int) or payload["proposed_repair_count"] < 0:
        result.add(f"{path}.proposed_repair_count", "must be a non-negative integer")
    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
