"""Contracts for legacy human-checkpoint orientation-only Obsidian view bundles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_human_checkpoint_obsidian_view_bundle(
    payload: dict[str, Any],
    *,
    path: str = "legacy_human_checkpoint_obsidian_view_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_human_checkpoint_obsidian_view_bundle":
        result.add(f"{path}.kind", "must be 'legacy_human_checkpoint_obsidian_view_bundle'")
    for key in ("view_dir", "migration_dir", "workspace", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "legacy_human_checkpoint_packet":
        result.add(f"{path}.derived_from", "must be legacy_human_checkpoint_packet")
    if not isinstance(payload.get("topic_filter"), str):
        result.add(f"{path}.topic_filter", "must be a string")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict):
        _require_nonempty_str(payload["files"], "checkpoint_worklist", f"{path}.files", result)
    for key in ("checkpoint_item_count", "open_decision_count", "pending_request_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    if isinstance(payload.get("source_records"), dict):
        _require_list(payload["source_records"].get("checkpoint_ids"), f"{path}.source_records.checkpoint_ids", result)
        _require_list(payload["source_records"].get("latest_review_ids"), f"{path}.source_records.latest_review_ids", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    if not isinstance(payload.get("semantic_lossless_proven"), bool):
        result.add(f"{path}.semantic_lossless_proven", "must be a boolean")
    _require_bool_value(payload.get("semantic_lossless_proven"), False, f"{path}.semantic_lossless_proven", result)
    for key in ("truth_source", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_legacy_human_checkpoint_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_human_checkpoint_obsidian_view_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
