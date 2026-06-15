"""Contracts for canonical legacy L2 seed review worklists."""

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


def validate_canonical_legacy_l2_seed_review_worklist(
    payload: dict[str, Any],
    *,
    path: str = "canonical_legacy_l2_seed_review_worklist",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "canonical_legacy_l2_seed_review_worklist":
        result.add(f"{path}.kind", "must be 'canonical_legacy_l2_seed_review_worklist'")
    for key in ("canonical_store", "memory_entries_dir", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "canonical_memory_l2_seed_scan_grouped_for_review":
        result.add(f"{path}.truth_source", "must be 'canonical_memory_l2_seed_scan_grouped_for_review'")
    for key in (
        "legacy_seed_count",
        "active_legacy_seed_count",
        "legacy_seed_topic_count",
        "review_group_count",
        "open_review_group_count",
        "reviewed_group_count",
        "terminal_review_group_count",
        "visible_review_group_count",
        "topic_scope_mismatch_count",
        "global_l2_seed_count",
    ):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in (
        "status_counts",
        "memory_kind_counts",
        "review_status_counts",
        "review_decision_counts",
        "review_group_blocking_class_counts",
        "promotion_policy",
    ):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    _validate_promotion_policy(payload.get("promotion_policy"), f"{path}.promotion_policy", result)
    _require_list(payload.get("review_groups"), f"{path}.review_groups", result)
    if isinstance(payload.get("review_groups"), list):
        for index, item in enumerate(payload["review_groups"]):
            _validate_review_group(item, f"{path}.review_groups[{index}]", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_canonical_legacy_l2_seed_review_worklist(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_canonical_legacy_l2_seed_review_worklist(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_promotion_policy(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        return
    if payload.get("legacy_seed_status") != "orientation_only":
        result.add(f"{path}.legacy_seed_status", "must be 'orientation_only'")
    for key in ("promotion_requires", "forbidden_shortcuts"):
        if not isinstance(payload.get(key), list) or not all(isinstance(item, str) for item in payload.get(key, [])):
            result.add(f"{path}.{key}", "must be a list of strings")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_review_group(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "group_id",
        "topic_id",
        "target_topic_id",
        "source_claim_id",
        "memory_role",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in ("seed_count", "priority_score", "topic_scope_mismatch_count", "semantic_subgroup_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("blocking_classes", "review_focus", "sample_entries", "review_actions", "semantic_subgroups"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("memory_kind_counts", "source_topic_counts", "scoped_topic_counts", "source_family_counts"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("semantic_mix_detected"), bool):
        result.add(f"{path}.semantic_mix_detected", "must be a boolean")
    if payload.get("review_status") not in {"pending", "passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.review_status", "must be an allowed review status")
    if payload.get("review_decision") not in {
        "pending",
        "archive",
        "reassign",
        "promote_candidate",
        "already_represented",
        "irrelevant",
        "needs_source_reconstruction",
        "needs_topic_alignment",
    }:
        result.add(f"{path}.review_decision", "must be an allowed review decision")
    _require_mapping(payload.get("latest_review_result"), f"{path}.latest_review_result", result)
    if not isinstance(payload.get("terminal_review_recorded"), bool):
        result.add(f"{path}.terminal_review_recorded", "must be a boolean")
    if isinstance(payload.get("sample_entries"), list):
        for index, entry in enumerate(payload["sample_entries"]):
            _validate_seed_entry(entry, f"{path}.sample_entries[{index}]", result)
    if isinstance(payload.get("semantic_subgroups"), list):
        for index, subgroup in enumerate(payload["semantic_subgroups"]):
            _validate_semantic_subgroup(subgroup, f"{path}.semantic_subgroups[{index}]", result)
    if isinstance(payload.get("review_actions"), list):
        for index, action in enumerate(payload["review_actions"]):
            _validate_review_action(action, f"{path}.review_actions[{index}]", result)
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_seed_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "entry_id",
        "topic_id",
        "source_topic_id",
        "scoped_topic_id",
        "source_claim_id",
        "source_object_id",
        "source_family",
        "status",
        "memory_kind",
        "scope",
        "source_packet_id",
        "source_path",
        "canonical_rel_path",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("requires_semantic_l2_reassignment") is not True:
        result.add(f"{path}.requires_semantic_l2_reassignment", "must be true")
    if not isinstance(payload.get("topic_scope_mismatch"), bool):
        result.add(f"{path}.topic_scope_mismatch", "must be a boolean")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_semantic_subgroup(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("source_family", "source_object_id", "review_hint"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if not isinstance(payload.get("seed_count"), int) or payload["seed_count"] < 0:
        result.add(f"{path}.seed_count", "must be a non-negative integer")
    _require_mapping(payload.get("memory_kind_counts"), f"{path}.memory_kind_counts", result)
    for key in ("source_paths", "sample_entry_ids"):
        if not isinstance(payload.get(key), list) or not all(isinstance(item, str) for item in payload.get(key, [])):
            result.add(f"{path}.{key}", "must be a list of strings")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_review_action(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("action", "cli", "mcp", "surface", "effect"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("effect") not in {
        "orientation_only",
        "typed_record_write_without_claim_trust",
        "typed_record_write_requires_evidence_and_human_gate",
    }:
        result.add(f"{path}.effect", "must be an allowed effect")
    if payload.get("effect") == "orientation_only" and payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false for orientation-only actions")
    if (
        payload.get("effect") == "typed_record_write_requires_evidence_and_human_gate"
        and payload.get("can_update_kernel_state") is not True
    ):
        result.add(f"{path}.can_update_kernel_state", "must be true for typed writes")
    if payload.get("effect") == "typed_record_write_without_claim_trust" and payload.get("can_update_kernel_state") is not True:
        result.add(f"{path}.can_update_kernel_state", "must be true for typed writes")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def validate_legacy_l2_seed_group_review_result_record(
    payload: dict[str, Any],
    *,
    path: str = "legacy_l2_seed_group_review_result_record",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "legacy_l2_seed_group_review_result":
        result.add(f"{path}.kind", "must be 'legacy_l2_seed_group_review_result'")
    for key in ("review_id", "group_id", "status", "decision", "summary", "reviewer_role"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    if payload.get("decision") not in {
        "archive",
        "reassign",
        "promote_candidate",
        "already_represented",
        "irrelevant",
        "needs_source_reconstruction",
        "needs_topic_alignment",
    }:
        result.add(f"{path}.decision", "must be an allowed review decision")
    for key in (
        "topic_id",
        "target_topic_id",
        "source_claim_id",
        "memory_role",
        "checkpoint_id",
        "created_at",
    ):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in (
        "reviewed_seed_entry_ids",
        "reviewed_seed_refs",
        "reviewed_typed_refs",
        "evidence_refs",
        "validation_result_ids",
        "remaining_actions",
    ):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    basis_keys = (
        "reviewed_seed_entry_ids",
        "reviewed_seed_refs",
        "reviewed_typed_refs",
        "evidence_refs",
        "validation_result_ids",
    )
    if all(isinstance(payload.get(key), list) and len(payload[key]) == 0 for key in basis_keys):
        result.add(f"{path}.reviewed_seed_entry_ids", "review basis must cite at least one seed, typed, evidence, or validation reference")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_legacy_l2_seed_group_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_l2_seed_group_review_result_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
