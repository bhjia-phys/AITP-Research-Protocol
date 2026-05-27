"""Contracts for workspace replay packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_workspace_replay_packet(payload: dict[str, Any], *, path: str = "workspace_replay_packet") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "workspace_replay_packet":
        result.add(f"{path}.kind", "must be 'workspace_replay_packet'")
    for key in ("replay_dir", "derived_from", "adapter_rule"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("derived_from") != "kernel_state":
        result.add(f"{path}.derived_from", "must be 'kernel_state'")
    for key in ("truth_source", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("entry_count", "attention_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("files"), f"{path}.files", result)
    if isinstance(payload.get("files"), dict) and not payload["files"].get("replay_packet"):
        result.add(f"{path}.files.replay_packet", "must be a non-empty string")
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_mapping(payload.get("workspace_backlog_summary"), f"{path}.workspace_backlog_summary", result)
    if isinstance(payload.get("workspace_backlog_summary"), dict):
        _validate_workspace_backlog_summary(
            payload["workspace_backlog_summary"],
            f"{path}.workspace_backlog_summary",
            result,
        )
    _require_list(payload.get("entries"), f"{path}.entries", result)
    if isinstance(payload.get("entries"), list):
        for index, entry in enumerate(payload["entries"]):
            _validate_entry(entry, f"{path}.entries[{index}]", result)
    return result


def require_valid_workspace_replay_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_replay_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("session_id", "topic_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("claim_id", "claim_statement", "confidence_state", "risk_level"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if not isinstance(payload.get("source_reconstruction_review_status"), str):
        result.add(f"{path}.source_reconstruction_review_status", "must be a string")
    for key in (
        "missing_outputs",
        "satisfied_outputs",
        "next_actions",
        "missing_source_components",
        "source_reconstruction_review_result_ids",
        "memory_entry_ids",
        "validation_result_ids",
        "attention_reasons",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("source_reconstruction_complete"), bool):
        result.add(f"{path}.source_reconstruction_complete", "must be a boolean")


def _validate_workspace_backlog_summary(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    for key in ("active_session_count", "active_topic_count", "active_claim_count", "attention_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("source_reconstruction"), f"{path}.source_reconstruction", result)
    if isinstance(payload.get("source_reconstruction"), dict):
        source = payload["source_reconstruction"]
        if source.get("surface") != "source_reconstruction_manifest":
            result.add(f"{path}.source_reconstruction.surface", "must be source_reconstruction_manifest")
        for key in ("complete_claim_count", "incomplete_claim_count"):
            if not isinstance(source.get(key), int) or source[key] < 0:
                result.add(f"{path}.source_reconstruction.{key}", "must be a non-negative integer")
        _require_mapping(source.get("review_status_counts"), f"{path}.source_reconstruction.review_status_counts", result)
        _require_mapping(source.get("missing_component_counts"), f"{path}.source_reconstruction.missing_component_counts", result)
        _require_list(source.get("top_incomplete_claims"), f"{path}.source_reconstruction.top_incomplete_claims", result)
        if isinstance(source.get("top_incomplete_claims"), list):
            for index, item in enumerate(source["top_incomplete_claims"]):
                _validate_source_backlog_item(item, f"{path}.source_reconstruction.top_incomplete_claims[{index}]", result)
    _require_mapping(payload.get("resume_attention"), f"{path}.resume_attention", result)
    if isinstance(payload.get("resume_attention"), dict):
        attention = payload["resume_attention"]
        if not isinstance(attention.get("attention_count"), int) or attention["attention_count"] < 0:
            result.add(f"{path}.resume_attention.attention_count", "must be a non-negative integer")
        _require_list(attention.get("top_items"), f"{path}.resume_attention.top_items", result)
    if payload.get("truth_source") != "kernel_state":
        result.add(f"{path}.truth_source", "must be kernel_state")
    if "legacy_semantic_review" in payload:
        _validate_legacy_semantic_review_backlog(
            payload.get("legacy_semantic_review"),
            f"{path}.legacy_semantic_review",
            result,
        )
    if "legacy_source_reconstruction" in payload:
        _validate_legacy_source_reconstruction_backlog(
            payload.get("legacy_source_reconstruction"),
            f"{path}.legacy_source_reconstruction",
            result,
        )
    if "legacy_semantic_repair" in payload:
        _validate_legacy_semantic_repair_backlog(
            payload.get("legacy_semantic_repair"),
            f"{path}.legacy_semantic_repair",
            result,
        )
    if "legacy_human_checkpoints" in payload:
        _validate_legacy_human_checkpoint_backlog(
            payload.get("legacy_human_checkpoints"),
            f"{path}.legacy_human_checkpoints",
            result,
        )
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_source_backlog_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("session_id", "topic_id", "claim_id", "review_status", "review_packet_cli"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("missing_components", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_semantic_review_backlog(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("surface") != "legacy_semantic_review_manifest":
        result.add(f"{path}.surface", "must be legacy_semantic_review_manifest")
    _require_nonempty_str(payload, "migration_dir", path, result)
    if not isinstance(payload.get("review_item_count"), int) or payload["review_item_count"] < 0:
        result.add(f"{path}.review_item_count", "must be a non-negative integer")
    _require_mapping(payload.get("review_progress"), f"{path}.review_progress", result)
    if not isinstance(payload.get("semantic_lossless_proven"), bool):
        result.add(f"{path}.semantic_lossless_proven", "must be a boolean")
    if not isinstance(payload.get("open_human_checkpoint_count"), int) or payload["open_human_checkpoint_count"] < 0:
        result.add(f"{path}.open_human_checkpoint_count", "must be a non-negative integer")
    _require_list(payload.get("open_human_checkpoints"), f"{path}.open_human_checkpoints", result)
    if isinstance(payload.get("open_human_checkpoints"), list):
        for index, item in enumerate(payload["open_human_checkpoints"]):
            _validate_open_checkpoint(item, f"{path}.open_human_checkpoints[{index}]", result)
    _require_list(payload.get("top_backlog_items"), f"{path}.top_backlog_items", result)
    if isinstance(payload.get("top_backlog_items"), list):
        for index, item in enumerate(payload["top_backlog_items"]):
            _validate_legacy_backlog_item(item, f"{path}.top_backlog_items[{index}]", result)
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_source_reconstruction_backlog(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("surface") != "legacy_source_reconstruction_manifest":
        result.add(f"{path}.surface", "must be legacy_source_reconstruction_manifest")
    _require_nonempty_str(payload, "migration_dir", path, result)
    for key in ("work_item_count", "proposed_repair_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("repair_status_counts"), f"{path}.repair_status_counts", result)
    _require_list(payload.get("top_backlog_items"), f"{path}.top_backlog_items", result)
    if isinstance(payload.get("top_backlog_items"), list):
        for index, item in enumerate(payload["top_backlog_items"]):
            _validate_legacy_source_backlog_item(item, f"{path}.top_backlog_items[{index}]", result)
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_source_backlog_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "repair_status", "review_packet_cli"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("latest_review_id"), str):
        result.add(f"{path}.latest_review_id", "must be a string")
    for key in ("missing_components", "required_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_semantic_repair_backlog(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("surface") != "legacy_semantic_repair_manifest":
        result.add(f"{path}.surface", "must be legacy_semantic_repair_manifest")
    _require_nonempty_str(payload, "migration_dir", path, result)
    for key in ("work_item_count", "proposed_repair_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("repair_status_counts"), f"{path}.repair_status_counts", result)
    _require_mapping(payload.get("required_action_counts"), f"{path}.required_action_counts", result)
    _require_list(payload.get("top_repair_items"), f"{path}.top_repair_items", result)
    if isinstance(payload.get("top_repair_items"), list):
        for index, item in enumerate(payload["top_repair_items"]):
            _validate_legacy_semantic_repair_item(item, f"{path}.top_repair_items[{index}]", result)
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_semantic_repair_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "review_status", "repair_status", "repair_plan_cli"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("latest_review_id"), str):
        result.add(f"{path}.latest_review_id", "must be a string")
    if not isinstance(payload.get("proposed_repair_count"), int) or payload["proposed_repair_count"] < 0:
        result.add(f"{path}.proposed_repair_count", "must be a non-negative integer")
    for key in ("proposed_repair_types", "required_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_human_checkpoint_backlog(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("surface") != "legacy_human_checkpoint_packet":
        result.add(f"{path}.surface", "must be legacy_human_checkpoint_packet")
    _require_nonempty_str(payload, "migration_dir", path, result)
    for key in ("checkpoint_item_count", "open_decision_count", "pending_request_count", "next_action_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_list(payload.get("top_checkpoint_items"), f"{path}.top_checkpoint_items", result)
    if isinstance(payload.get("top_checkpoint_items"), list):
        for index, item in enumerate(payload["top_checkpoint_items"]):
            _validate_legacy_human_checkpoint_item(item, f"{path}.top_checkpoint_items[{index}]", result)
    for key in ("summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_human_checkpoint_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topic",
        "active_claim_id",
        "latest_review_id",
        "review_status",
        "action",
        "mode",
        "reason",
        "cli",
        "mcp",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("mode") == "decide_open_checkpoint":
        _require_nonempty_str(payload, "checkpoint_id", path, result)
    elif not isinstance(payload.get("checkpoint_id"), str):
        result.add(f"{path}.checkpoint_id", "must be a string")
    _require_list(payload.get("options"), f"{path}.options", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_open_checkpoint(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topic",
        "active_claim_id",
        "checkpoint_id",
        "checkpoint_ref",
        "action",
        "decision_cli",
        "decision_mcp",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_legacy_backlog_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topic", "active_claim_id", "review_status", "review_priority", "packet_cli"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("latest_review_id"), str):
        result.add(f"{path}.latest_review_id", "must be a string")
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
