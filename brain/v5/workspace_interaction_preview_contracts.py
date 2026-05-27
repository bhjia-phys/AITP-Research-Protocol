"""Contracts for workspace interaction preview bundles."""

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


_REQUIRED_KEYS = (
    "kind",
    "session_count",
    "decision_mode_counts",
    "items",
    "preview_refs",
    "source_records",
    "derived_from",
    "truth_source",
    "summary_inputs_trusted",
    "orientation_only",
    "adapter_rule",
    "can_update_kernel_state",
    "can_update_claim_trust",
)
_DECISION_MODES = {"lightweight_trace", "guarded_recording", "trust_boundary_checkpoint"}


def validate_workspace_interaction_preview_bundle(
    payload: dict[str, Any],
    *,
    path: str = "workspace_interaction_preview_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    for key in _REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required workspace interaction preview key")
    if payload.get("kind") != "workspace_interaction_preview_bundle":
        result.add(f"{path}.kind", "must be 'workspace_interaction_preview_bundle'")
    if payload.get("derived_from") != "interaction_recording_preview":
        result.add(f"{path}.derived_from", "must be 'interaction_recording_preview'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    if payload.get("adapter_rule") != "read_for_orientation_then_call_kernel_before_trust_updates":
        result.add(f"{path}.adapter_rule", "must be the orientation adapter rule")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_list(payload.get("items"), f"{path}.items", result)
    _require_list(payload.get("preview_refs"), f"{path}.preview_refs", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _validate_counts(payload, path, result)
    for index, item in enumerate(payload.get("items") or []):
        _validate_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_workspace_interaction_preview_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_workspace_interaction_preview_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_counts(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    items = payload.get("items")
    session_count = payload.get("session_count")
    if not isinstance(session_count, int) or session_count < 0:
        result.add(f"{path}.session_count", "must be a non-negative integer")
    if isinstance(items, list) and isinstance(session_count, int) and session_count != len(items):
        result.add(f"{path}.session_count", "must equal the number of preview items")
    counts = payload.get("decision_mode_counts")
    _require_mapping(counts, f"{path}.decision_mode_counts", result)
    if not isinstance(counts, dict):
        return
    for key, value in counts.items():
        if key not in _DECISION_MODES:
            result.add(f"{path}.decision_mode_counts.{key}", "must be a supported recording decision mode")
        if not isinstance(value, int) or value < 0:
            result.add(f"{path}.decision_mode_counts.{key}", "must be a non-negative integer")


def _validate_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "session_id",
        "topic_id",
        "interaction_role",
        "risk_level",
        "flow_profile",
        "recording_mode",
        "source_brief_ref",
        "source_preview_ref",
    ):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("active_claim"), str):
        result.add(f"{path}.active_claim", "must be a string")
    if payload.get("recording_mode") not in _DECISION_MODES:
        result.add(f"{path}.recording_mode", "must be a supported recording decision mode")
    if not isinstance(payload.get("next_kernel_entrypoint"), str):
        result.add(f"{path}.next_kernel_entrypoint", "must be a string")
    if not isinstance(payload.get("can_stay_lightweight"), bool):
        result.add(f"{path}.can_stay_lightweight", "must be a bool")
    for key in ("mandatory_question_count", "max_questions"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_list(payload.get("heavier_triggers"), f"{path}.heavier_triggers", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
