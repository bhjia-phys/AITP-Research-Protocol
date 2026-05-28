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
from brain.v5.topic_status_contracts import validate_topic_status_bundle


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
    refresh_mode = str(payload.get("refresh_mode") or "full")
    if isinstance(payload.get("refreshed_surfaces"), list):
        base_expected = [
            "workspace_summary_bundle",
            "workspace_replay_packet",
            "source_stack_coverage_manifest",
            "l2_obsidian_view_bundle",
            "source_reconstruction_obsidian_view_bundle",
            "workspace_interaction_preview_bundle",
            "interaction_recording_worklist",
        ]
        topic_status_expected = [
            *base_expected,
            "topic_status_bundle",
        ]
        legacy_expected = [
            *base_expected,
            "legacy_source_reconstruction_obsidian_view_bundle",
            "legacy_semantic_review_obsidian_view_bundle",
            "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
            "legacy_human_checkpoint_obsidian_view_bundle",
        ]
        legacy_with_topic_status_expected = [
            *topic_status_expected,
            "legacy_source_reconstruction_obsidian_view_bundle",
            "legacy_semantic_review_obsidian_view_bundle",
            "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
            "legacy_human_checkpoint_obsidian_view_bundle",
        ]
        startup_expected = [
            "workspace_summary_bundle",
            "workspace_interaction_preview_bundle",
            "interaction_recording_worklist",
            "topic_status_bundle",
        ]
        surfaces = tuple(payload["refreshed_surfaces"])
        valid_surface_orders = {
            tuple(base_expected),
            tuple(topic_status_expected),
            tuple(legacy_expected),
            tuple(legacy_with_topic_status_expected),
        }
        if refresh_mode == "startup_lightweight":
            valid_surface_orders.add(tuple(startup_expected))
        if surfaces not in valid_surface_orders:
            result.add(f"{path}.refreshed_surfaces", "must list the refreshed workspace surfaces in order")
    _require_mapping(payload.get("workspace_summary"), f"{path}.workspace_summary", result)
    if refresh_mode != "startup_lightweight":
        _require_mapping(payload.get("workspace_replay"), f"{path}.workspace_replay", result)
        _require_mapping(payload.get("source_stack_coverage"), f"{path}.source_stack_coverage", result)
        _require_mapping(payload.get("l2_obsidian_view"), f"{path}.l2_obsidian_view", result)
        _require_mapping(payload.get("source_reconstruction_obsidian_view"), f"{path}.source_reconstruction_obsidian_view", result)
    else:
        _require_list(payload.get("deferred_surfaces"), f"{path}.deferred_surfaces", result)
    _require_mapping(payload.get("workspace_interaction_preview"), f"{path}.workspace_interaction_preview", result)
    _require_mapping(payload.get("interaction_recording_worklist"), f"{path}.interaction_recording_worklist", result)
    _require_list(payload.get("topic_status_bundles"), f"{path}.topic_status_bundles", result)
    if isinstance(payload.get("topic_status_bundles"), list):
        for index, item in enumerate(payload["topic_status_bundles"]):
            result.extend(validate_topic_status_bundle(item, path=f"{path}.topic_status_bundles[{index}]"))
    _require_mapping(payload.get("topic_status_refresh_policy"), f"{path}.topic_status_refresh_policy", result)
    if "legacy_source_reconstruction_obsidian_view" in payload:
        _require_mapping(
            payload.get("legacy_source_reconstruction_obsidian_view"),
            f"{path}.legacy_source_reconstruction_obsidian_view",
            result,
        )
    if "legacy_semantic_review_obsidian_view" in payload:
        _require_mapping(
            payload.get("legacy_semantic_review_obsidian_view"),
            f"{path}.legacy_semantic_review_obsidian_view",
            result,
        )
    if "legacy_semantic_needs_revision_basis_obsidian_view" in payload:
        _require_mapping(
            payload.get("legacy_semantic_needs_revision_basis_obsidian_view"),
            f"{path}.legacy_semantic_needs_revision_basis_obsidian_view",
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
