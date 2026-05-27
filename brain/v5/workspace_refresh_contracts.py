"""Contracts for workspace refresh bundles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
)


def validate_workspace_refresh_bundle(payload: dict[str, Any], *, path: str = "workspace_refresh_bundle") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "workspace_refresh_bundle":
        result.add(f"{path}.kind", "must be 'workspace_refresh_bundle'")
    if payload.get("derived_from") != "kernel_state":
        result.add(f"{path}.derived_from", "must be 'kernel_state'")
    if payload.get("adapter_rule") != "read_for_orientation_then_call_kernel_before_trust_updates":
        result.add(f"{path}.adapter_rule", "must be the orientation adapter rule")
    for key in ("truth_source", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_list(payload.get("refreshed_surfaces"), f"{path}.refreshed_surfaces", result)
    if isinstance(payload.get("refreshed_surfaces"), list):
        base_expected = [
            "workspace_summary_bundle",
            "workspace_replay_packet",
            "l2_obsidian_view_bundle",
            "source_reconstruction_obsidian_view_bundle",
        ]
        legacy_expected = [
            *base_expected,
            "legacy_semantic_review_obsidian_view_bundle",
            "legacy_human_checkpoint_obsidian_view_bundle",
        ]
        surfaces = tuple(payload["refreshed_surfaces"])
        if surfaces not in {tuple(base_expected), tuple(legacy_expected)}:
            result.add(f"{path}.refreshed_surfaces", "must list the refreshed workspace surfaces in order")
    _require_mapping(payload.get("workspace_summary"), f"{path}.workspace_summary", result)
    _require_mapping(payload.get("workspace_replay"), f"{path}.workspace_replay", result)
    _require_mapping(payload.get("l2_obsidian_view"), f"{path}.l2_obsidian_view", result)
    _require_mapping(payload.get("source_reconstruction_obsidian_view"), f"{path}.source_reconstruction_obsidian_view", result)
    if "legacy_semantic_review_obsidian_view" in payload:
        _require_mapping(
            payload.get("legacy_semantic_review_obsidian_view"),
            f"{path}.legacy_semantic_review_obsidian_view",
            result,
        )
    if "legacy_human_checkpoint_obsidian_view" in payload:
        _require_mapping(
            payload.get("legacy_human_checkpoint_obsidian_view"),
            f"{path}.legacy_human_checkpoint_obsidian_view",
            result,
        )
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    return result


def require_valid_workspace_refresh_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_refresh_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
