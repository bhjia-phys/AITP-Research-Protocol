"""Contracts for the final engineering readiness audit surface."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


def validate_final_engineering_readiness_audit(
    payload: dict[str, Any],
    *,
    path: str = "final_engineering_readiness_audit",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "final_engineering_readiness_audit":
        result.add(f"{path}.kind", "must be 'final_engineering_readiness_audit'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _require_nonempty_str(payload, "completion_status", path, result)
    _require_nonempty_str(payload, "kernel_capability_status", path, result)
    _require_nonempty_str(payload, "content_backlog_status", path, result)
    _require_mapping(payload.get("kernel_capabilities"), f"{path}.kernel_capabilities", result)
    natural = _mapping(payload.get("kernel_capabilities")).get("natural_interaction")
    _require_mapping(natural, f"{path}.kernel_capabilities.natural_interaction", result)
    if isinstance(natural, dict):
        if natural.get("surface") != "interaction_recording_preview":
            result.add(
                f"{path}.kernel_capabilities.natural_interaction.surface",
                "must be interaction_recording_preview",
            )
        if natural.get("workspace_preview_surface") != "workspace_interaction_preview_bundle":
            result.add(
                f"{path}.kernel_capabilities.natural_interaction.workspace_preview_surface",
                "must be workspace_interaction_preview_bundle",
            )
        if natural.get("host_refresh_preview_supported") is not True:
            result.add(
                f"{path}.kernel_capabilities.natural_interaction.host_refresh_preview_supported",
                "must be true",
            )
        _require_list(
            natural.get("recording_decision_modes"),
            f"{path}.kernel_capabilities.natural_interaction.recording_decision_modes",
            result,
        )
        _require_list(
            natural.get("next_kernel_entrypoints"),
            f"{path}.kernel_capabilities.natural_interaction.next_kernel_entrypoints",
            result,
        )
        for key in ("summary_can_drive_trust", "can_update_kernel_state", "can_update_claim_trust"):
            if natural.get(key) is not False:
                result.add(f"{path}.kernel_capabilities.natural_interaction.{key}", "must be false")
    host = _mapping(payload.get("kernel_capabilities")).get("host_integration")
    _require_mapping(host, f"{path}.kernel_capabilities.host_integration", result)
    if isinstance(host, dict):
        if host.get("production_loop_surface") != "runtime_host_readiness_audit":
            result.add(
                f"{path}.kernel_capabilities.host_integration.production_loop_surface",
                "must be runtime_host_readiness_audit",
            )
        _require_list(
            host.get("priority_host_production_loops"),
            f"{path}.kernel_capabilities.host_integration.priority_host_production_loops",
            result,
        )
        for index, item in enumerate(host.get("priority_host_production_loops") or []):
            _validate_host_production_loop(
                item,
                f"{path}.kernel_capabilities.host_integration.priority_host_production_loops[{index}]",
                result,
            )
    _require_mapping(payload.get("content_backlog"), f"{path}.content_backlog", result)
    _require_list(payload.get("blocking_gaps"), f"{path}.blocking_gaps", result)
    _require_list(payload.get("residual_risks"), f"{path}.residual_risks", result)
    _require_list(payload.get("evidence_refs"), f"{path}.evidence_refs", result)
    _require_list(payload.get("backlog_refs"), f"{path}.backlog_refs", result)
    legacy = _mapping(payload.get("content_backlog")).get("legacy_semantic_review")
    _require_mapping(legacy, f"{path}.content_backlog.legacy_semantic_review", result)
    if isinstance(legacy, dict):
        if legacy.get("semantic_lossless_proven") is not False:
            result.add(
                f"{path}.content_backlog.legacy_semantic_review.semantic_lossless_proven",
                "must be false",
            )
        if legacy.get("worklist_surface") != "legacy_semantic_review_worklist":
            result.add(
                f"{path}.content_backlog.legacy_semantic_review.worklist_surface",
                "must be legacy_semantic_review_worklist",
            )
        for key in [
            "review_item_count",
            "work_item_count",
            "open_human_checkpoint_count",
            "pending_count",
            "passed_count",
            "needs_revision_count",
            "inconclusive_count",
        ]:
            if not isinstance(legacy.get(key), int):
                result.add(f"{path}.content_backlog.legacy_semantic_review.{key}", "must be an integer")
        _require_mapping(
            legacy.get("pass_readiness_counts"),
            f"{path}.content_backlog.legacy_semantic_review.pass_readiness_counts",
            result,
        )
        _require_list(
            legacy.get("open_human_checkpoints"),
            f"{path}.content_backlog.legacy_semantic_review.open_human_checkpoints",
            result,
        )
        if isinstance(legacy.get("pass_readiness_counts"), dict):
            for key in ("blocked", "candidate"):
                if not isinstance(legacy["pass_readiness_counts"].get(key), int):
                    result.add(
                        f"{path}.content_backlog.legacy_semantic_review.pass_readiness_counts.{key}",
                        "must be an integer",
                    )
        _require_mapping(
            legacy.get("pass_blocker_counts"),
            f"{path}.content_backlog.legacy_semantic_review.pass_blocker_counts",
            result,
        )
        if isinstance(legacy.get("pass_blocker_counts"), dict):
            for key, value in legacy["pass_blocker_counts"].items():
                if not isinstance(key, str) or not isinstance(value, int):
                    result.add(
                        f"{path}.content_backlog.legacy_semantic_review.pass_blocker_counts",
                        "must map strings to integers",
                    )
        _require_mapping(
            legacy.get("blocking_class_counts"),
            f"{path}.content_backlog.legacy_semantic_review.blocking_class_counts",
            result,
        )
        if isinstance(legacy.get("blocking_class_counts"), dict):
            for key, value in legacy["blocking_class_counts"].items():
                if not isinstance(key, str) or not isinstance(value, int):
                    result.add(
                        f"{path}.content_backlog.legacy_semantic_review.blocking_class_counts",
                        "must map strings to integers",
                    )
        _require_list(
            legacy.get("worklist_next_actions"),
            f"{path}.content_backlog.legacy_semantic_review.worklist_next_actions",
            result,
        )
        _require_list(
            legacy.get("top_work_items"),
            f"{path}.content_backlog.legacy_semantic_review.top_work_items",
            result,
        )
        for index, item in enumerate(legacy.get("top_work_items") or []):
            if isinstance(item, dict):
                _require_list(
                    item.get("open_human_checkpoint_refs"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].open_human_checkpoint_refs",
                    result,
                )
                _require_list(
                    item.get("source_reconstruction_review_refs"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].source_reconstruction_review_refs",
                    result,
                )
                _require_list(
                    item.get("satisfied_review_actions"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].satisfied_review_actions",
                    result,
                )
                _require_list(
                    item.get("followup_review_actions"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].followup_review_actions",
                    result,
                )
                _require_list(
                    item.get("blocking_classes"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].blocking_classes",
                    result,
                )
                _require_mapping(
                    item.get("pass_readiness"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].pass_readiness",
                    result,
                )
                _require_list(
                    item.get("review_action_commands"),
                    f"{path}.content_backlog.legacy_semantic_review.top_work_items[{index}].review_action_commands",
                    result,
                )
    source = _mapping(payload.get("content_backlog")).get("source_reconstruction")
    _require_mapping(source, f"{path}.content_backlog.source_reconstruction", result)
    if isinstance(source, dict):
        if source.get("surface") != "source_reconstruction_manifest":
            result.add(f"{path}.content_backlog.source_reconstruction.surface", "must be source_reconstruction_manifest")
        if source.get("review_surface") != "source_reconstruction_review_manifest":
            result.add(
                f"{path}.content_backlog.source_reconstruction.review_surface",
                "must be source_reconstruction_review_manifest",
            )
        if source.get("status") not in {"complete", "reconstruction_backlog"}:
            result.add(f"{path}.content_backlog.source_reconstruction.status", "must be complete or reconstruction_backlog")
        for key in ["active_claim_count", "complete_claim_count", "incomplete_claim_count"]:
            if not isinstance(source.get(key), int):
                result.add(f"{path}.content_backlog.source_reconstruction.{key}", "must be an integer")
        _require_list(source.get("next_actions"), f"{path}.content_backlog.source_reconstruction.next_actions", result)
        _require_list(
            source.get("review_next_actions"),
            f"{path}.content_backlog.source_reconstruction.review_next_actions",
            result,
        )
        _require_mapping(
            source.get("review_progress"),
            f"{path}.content_backlog.source_reconstruction.review_progress",
            result,
        )
        if isinstance(source.get("review_progress"), dict):
            for key in ("passed", "needs_revision", "inconclusive", "pending"):
                if not isinstance(source["review_progress"].get(key), int):
                    result.add(
                        f"{path}.content_backlog.source_reconstruction.review_progress.{key}",
                        "must be an integer",
                    )
        _require_mapping(
            source.get("missing_components_by_claim"),
            f"{path}.content_backlog.source_reconstruction.missing_components_by_claim",
            result,
        )
        _require_list(
            source.get("top_incomplete_claims"),
            f"{path}.content_backlog.source_reconstruction.top_incomplete_claims",
            result,
        )
        for index, item in enumerate(source.get("top_incomplete_claims") or []):
            if isinstance(item, dict):
                _require_nonempty_str(
                    item,
                    "claim_id",
                    f"{path}.content_backlog.source_reconstruction.top_incomplete_claims[{index}]",
                    result,
                )
                _require_list(
                    item.get("missing_components"),
                    f"{path}.content_backlog.source_reconstruction.top_incomplete_claims[{index}].missing_components",
                    result,
                )
                _require_list(
                    item.get("next_actions"),
                    f"{path}.content_backlog.source_reconstruction.top_incomplete_claims[{index}].next_actions",
                    result,
                )
                if item.get("can_update_claim_trust") is not False:
                    result.add(
                        f"{path}.content_backlog.source_reconstruction.top_incomplete_claims[{index}].can_update_claim_trust",
                        "must be false",
                    )
        if source.get("can_update_kernel_state") is not False:
            result.add(f"{path}.content_backlog.source_reconstruction.can_update_kernel_state", "must be false")
        if source.get("can_update_claim_trust") is not False:
            result.add(f"{path}.content_backlog.source_reconstruction.can_update_claim_trust", "must be false")
    return result


def require_valid_final_engineering_readiness_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_final_engineering_readiness_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _require_mapping(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be a mapping")


def _require_list(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list")


def _require_nonempty_str(payload: dict[str, Any], key: str, path: str, result: ContractResult) -> None:
    if not isinstance(payload.get(key), str) or not payload.get(key):
        result.add(f"{path}.{key}", "must be a non-empty string")


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _validate_host_production_loop(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("runtime", "readiness_cli", "lifecycle_cli"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("session_start_smoke_supported"), bool):
        result.add(f"{path}.session_start_smoke_supported", "must be a bool")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
