"""Contracts for legacy source reconstruction orientation-only Obsidian views."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_source_reconstruction_obsidian_view_bundle(
    payload: dict[str, Any],
    *,
    path: str = "legacy_source_reconstruction_obsidian_view_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_source_reconstruction_obsidian_view_bundle":
        result.add(f"{path}.kind", "must be 'legacy_source_reconstruction_obsidian_view_bundle'")
    for key in ("view_dir", "migration_dir", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "legacy_source_reconstruction_manifest":
        result.add(f"{path}.derived_from", "must be legacy_source_reconstruction_manifest")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict):
        _require_nonempty_str(payload["files"], "review_worklist", f"{path}.files", result)
    for key in ("work_item_count", "proposed_repair_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("repair_status_counts", "missing_component_counts", "required_action_counts", "source_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("source_records"), dict):
        for key in ("topics", "active_claim_ids", "latest_review_ids"):
            _require_list(payload["source_records"].get(key), f"{path}.source_records.{key}", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key in ("semantic_lossless_proven", "semantic_review_required"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("semantic_lossless_proven"), False, f"{path}.semantic_lossless_proven", result)
    _require_bool_value(payload.get("semantic_review_required"), True, f"{path}.semantic_review_required", result)
    for key in ("truth_source", "summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_legacy_source_reconstruction_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_source_reconstruction_obsidian_view_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
