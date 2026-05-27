"""Contracts for source reconstruction orientation-only Obsidian view bundles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_source_reconstruction_obsidian_view_bundle(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_obsidian_view_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_obsidian_view_bundle":
        result.add(f"{path}.kind", "must be 'source_reconstruction_obsidian_view_bundle'")
    for key in ("view_dir", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "source_reconstruction_review_manifest":
        result.add(f"{path}.derived_from", "must be source_reconstruction_review_manifest")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict):
        _require_nonempty_str(payload["files"], "review_worklist", f"{path}.files", result)
    for key in ("claim_count", "incomplete_claim_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("review_progress"), f"{path}.review_progress", result)
    if isinstance(payload.get("review_progress"), dict):
        for key in ("passed", "needs_revision", "inconclusive", "pending"):
            if not isinstance(payload["review_progress"].get(key), int) or payload["review_progress"][key] < 0:
                result.add(f"{path}.review_progress.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    if isinstance(payload.get("source_records"), dict):
        _require_list(payload["source_records"].get("claim_ids"), f"{path}.source_records.claim_ids", result)
        _require_list(payload["source_records"].get("review_result_ids"), f"{path}.source_records.review_result_ids", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key in ("truth_source", "summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_source_reconstruction_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_obsidian_view_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
