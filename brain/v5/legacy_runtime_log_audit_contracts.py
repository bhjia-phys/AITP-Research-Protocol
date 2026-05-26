"""Contracts for legacy runtime-log marker audit packets."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_legacy_runtime_log_marker_audit(
    payload: dict[str, Any],
    *,
    path: str = "legacy_runtime_log_marker_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "legacy_runtime_log_marker_audit":
        result.add(f"{path}.kind", "must be 'legacy_runtime_log_marker_audit'")
    for key in ("workspace", "topic", "truth_source", "marker_match_mode", "status"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("migration_dir"), str):
        result.add(f"{path}.migration_dir", "must be a string")
    if payload.get("truth_source") != "raw_runtime_logs":
        result.add(f"{path}.truth_source", "must be 'raw_runtime_logs'")
    if payload.get("marker_match_mode") != "literal_substring_case_sensitive":
        result.add(f"{path}.marker_match_mode", "must be literal_substring_case_sensitive")
    if payload.get("status") not in {"satisfied", "incomplete", "missing_raw_logs"}:
        result.add(f"{path}.status", "must be an allowed audit status")
    _validate_marker_specs(payload.get("marker_specs"), f"{path}.marker_specs", result)
    for key in ("raw_log_files", "orientation_log_files", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("total_raw_matches_by_marker", "total_orientation_matches_by_marker"):
        _validate_marker_counts(payload.get(key), f"{path}.{key}", result)
    for index, audit in enumerate(payload.get("raw_log_files") or []):
        _validate_log_file_audit(audit, f"{path}.raw_log_files[{index}]", result, role="raw")
    for index, audit in enumerate(payload.get("orientation_log_files") or []):
        _validate_log_file_audit(audit, f"{path}.orientation_log_files[{index}]", result, role="orientation")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_legacy_runtime_log_marker_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_runtime_log_marker_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_marker_specs(payload: Any, path: str, result: ContractResult) -> None:
    _require_list(payload, path, result)
    if not isinstance(payload, list):
        return
    if not payload:
        result.add(path, "must include at least one marker spec")
    for index, spec in enumerate(payload):
        spec_path = f"{path}[{index}]"
        _require_mapping(spec, spec_path, result)
        if not isinstance(spec, dict):
            continue
        _require_nonempty_str(spec, "marker", spec_path, result)
        if not isinstance(spec.get("expected_min_count"), int) or spec["expected_min_count"] < 1:
            result.add(f"{spec_path}.expected_min_count", "must be a positive integer")


def _validate_marker_counts(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            result.add(path, "keys must be non-empty strings")
        if not isinstance(value, int) or value < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_log_file_audit(payload: Any, path: str, result: ContractResult, *, role: str) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("path", "provided_path", "log_role"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("log_role") != role:
        result.add(f"{path}.log_role", f"must be {role!r}")
    if not isinstance(payload.get("exists"), bool):
        result.add(f"{path}.exists", "must be a boolean")
    if not isinstance(payload.get("line_count"), int) or payload["line_count"] < 0:
        result.add(f"{path}.line_count", "must be a non-negative integer")
    _validate_marker_counts(payload.get("match_counts_by_marker"), f"{path}.match_counts_by_marker", result)
    _require_list(payload.get("matched_lines"), f"{path}.matched_lines", result)
    for index, line in enumerate(payload.get("matched_lines") or []):
        _validate_matched_line(line, f"{path}.matched_lines[{index}]", result)
    if not isinstance(payload.get("truncated_matches"), bool):
        result.add(f"{path}.truncated_matches", "must be a boolean")
    if not isinstance(payload.get("read_error"), str):
        result.add(f"{path}.read_error", "must be a string")


def _validate_matched_line(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("marker", "text"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("line_number"), int) or payload["line_number"] < 1:
        result.add(f"{path}.line_number", "must be a positive integer")
