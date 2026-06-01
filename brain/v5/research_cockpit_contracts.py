"""Contracts for workspace-level research cockpit surfaces."""

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


def validate_research_cockpit_bundle(
    payload: dict[str, Any],
    *,
    path: str = "research_cockpit_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "research_cockpit_bundle":
        result.add(f"{path}.kind", "must be 'research_cockpit_bundle'")
    for key in ("manifest_version", "derived_from"):
        _require_nonempty_str(payload, key, path, result)
    for key, expected in (
        ("truth_source", False),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    _validate_files(payload.get("files"), f"{path}.files", result)
    _validate_manifest(payload.get("manifest"), f"{path}.manifest", result)
    _validate_source_records(payload.get("source_records"), f"{path}.source_records", result)
    return result


def require_valid_research_cockpit_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_research_cockpit_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_files(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("manifest", "dashboard", "queue"):
        _require_nonempty_str(payload, key, path, result)


def _validate_manifest(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "research_cockpit_manifest":
        result.add(f"{path}.kind", "must be 'research_cockpit_manifest'")
    _require_nonempty_str(payload, "manifest_version", path, result)
    if not isinstance(payload.get("degraded_mode"), bool):
        result.add(f"{path}.degraded_mode", "must be a boolean")
    _require_list(payload.get("read_errors"), f"{path}.read_errors", result)
    for key in (
        "workspace_summary",
        "source_stack_coverage",
        "interaction_worklist",
        "refresh_policy",
        "source_surface_refs",
    ):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("today_queue", "operator_queue", "learning_gaps", "reading_queue", "topic_overview"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key, expected in (
        ("trust_update_forbidden", True),
        ("truth_source", False),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    _validate_queue_items(payload.get("today_queue"), f"{path}.today_queue", result)


def _validate_queue_items(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, list):
        return
    for index, item in enumerate(payload):
        item_path = f"{path}[{index}]"
        _require_mapping(item, item_path, result)
        if not isinstance(item, dict):
            continue
        for key in ("topic_id", "recommended_action"):
            _require_nonempty_str(item, key, item_path, result)
        _require_bool_value(item.get("orientation_only"), True, f"{item_path}.orientation_only", result)
        _require_bool_value(item.get("can_update_claim_trust"), False, f"{item_path}.can_update_claim_trust", result)


def _validate_source_records(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("topics", "sessions", "claims", "reference_locations"):
        _require_list(payload.get(key), f"{path}.{key}", result)
