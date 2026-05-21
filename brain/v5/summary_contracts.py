"""Summary-surface contracts for AITP v5 orientation files."""

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


_SUMMARY_ORIENTATION_REQUIRED_KEYS = (
    "kind",
    "session_id",
    "summary_dir",
    "files",
    "truth_source",
    "orientation_only",
    "can_update_kernel_state",
)
_SESSION_SUMMARY_BUNDLE_REQUIRED_KEYS = (
    "kind",
    "session_id",
    "topic_id",
    "active_claim",
    "summary_dir",
    "files",
    "derived_from",
    "truth_source",
    "orientation_only",
    "adapter_rule",
    "source_records",
)
_WORKSPACE_SUMMARY_BUNDLE_REQUIRED_KEYS = (
    "kind",
    "summary_dir",
    "files",
    "session_count",
    "active_claim_count",
    "memory_entry_count",
    "derived_from",
    "truth_source",
    "orientation_only",
    "adapter_rule",
    "source_records",
)


def validate_summary_orientation(payload: dict[str, Any], *, path: str = "summary_orientation") -> ContractResult:
    """Validate a public orientation-only summary view."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _SUMMARY_ORIENTATION_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required summary orientation key")

    if payload.get("kind") != "summary_orientation":
        result.add(f"{path}.kind", "must be 'summary_orientation'")
    _require_nonempty_str(payload, "session_id", path, result)
    _require_nonempty_str(payload, "summary_dir", path, result)
    validate_summary_orientation_flags(payload, path, result)

    files = payload.get("files")
    if isinstance(files, dict):
        for role, file_payload in files.items():
            _validate_summary_orientation_file(file_payload, f"{path}.files.{role}", result)

    return result


def require_valid_summary_orientation(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a summary orientation payload or raise a contract error."""

    result = validate_summary_orientation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_session_summary_bundle(payload: dict[str, Any], *, path: str = "session_summary_bundle") -> ContractResult:
    """Validate a public session-summary write result."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _SESSION_SUMMARY_BUNDLE_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required session summary bundle key")

    if payload.get("kind") != "session_summary_bundle":
        result.add(f"{path}.kind", "must be 'session_summary_bundle'")
    for key in ("session_id", "topic_id", "summary_dir"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("active_claim"), str):
        result.add(f"{path}.active_claim", "must be a string")
    if payload.get("derived_from") != "kernel_state":
        result.add(f"{path}.derived_from", "must be 'kernel_state'")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    if payload.get("adapter_rule") != "read_for_orientation_then_call_kernel_before_trust_updates":
        result.add(
            f"{path}.adapter_rule",
            "must be 'read_for_orientation_then_call_kernel_before_trust_updates'",
        )

    files = payload.get("files")
    _require_mapping(files, f"{path}.files", result)
    if isinstance(files, dict):
        for role in ("task_plan", "findings", "progress"):
            if role not in files:
                result.add(f"{path}.files.{role}", "missing required summary file path")
            elif not isinstance(files[role], str) or not files[role]:
                result.add(f"{path}.files.{role}", "must be a non-empty string")

    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    return result


def require_valid_session_summary_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a session-summary bundle payload or raise a contract error."""

    result = validate_session_summary_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_workspace_summary_bundle(payload: dict[str, Any], *, path: str = "workspace_summary_bundle") -> ContractResult:
    """Validate a public workspace-summary write result."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _WORKSPACE_SUMMARY_BUNDLE_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required workspace summary bundle key")

    if payload.get("kind") != "workspace_summary_bundle":
        result.add(f"{path}.kind", "must be 'workspace_summary_bundle'")
    _require_nonempty_str(payload, "summary_dir", path, result)
    if payload.get("derived_from") != "kernel_state":
        result.add(f"{path}.derived_from", "must be 'kernel_state'")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    if payload.get("adapter_rule") != "read_for_orientation_then_call_kernel_before_trust_updates":
        result.add(
            f"{path}.adapter_rule",
            "must be 'read_for_orientation_then_call_kernel_before_trust_updates'",
        )
    for key in ("session_count", "active_claim_count", "memory_entry_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")

    files = payload.get("files")
    _require_mapping(files, f"{path}.files", result)
    if isinstance(files, dict):
        if not isinstance(files.get("overview"), str) or not files.get("overview"):
            result.add(f"{path}.files.overview", "must be a non-empty string")
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    if isinstance(payload.get("source_records"), dict):
        for key in ("sessions", "topics", "claims", "memory_entries", "validation_results"):
            _require_list(payload["source_records"].get(key), f"{path}.source_records.{key}", result)
    return result


def require_valid_workspace_summary_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a workspace-summary bundle payload or raise a contract error."""

    result = validate_workspace_summary_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_summary_orientation_flags(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    if "files" in payload:
        _require_mapping(payload["files"], f"{path}.files", result)


def _validate_summary_orientation_file(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "path", path, result)
    if "frontmatter" in payload:
        _require_mapping(payload["frontmatter"], f"{path}.frontmatter", result)
    if "body" in payload and not isinstance(payload["body"], str):
        result.add(f"{path}.body", "must be a string")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
