"""Contracts for QSGW/LibRPA cockpit surfaces."""

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


def validate_qsgw_cockpit_bundle(payload: dict[str, Any], *, path: str = "qsgw_cockpit_bundle") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "qsgw_cockpit_bundle":
        result.add(f"{path}.kind", "must be 'qsgw_cockpit_bundle'")
    for key in ("topic_id", "derived_from"):
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


def require_valid_qsgw_cockpit_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_qsgw_cockpit_bundle(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_files(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("manifest", "dashboard_dry_run", "plot_guard"):
        _require_nonempty_str(payload, key, path, result)


def _validate_manifest(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "qsgw_cockpit_manifest":
        result.add(f"{path}.kind", "must be 'qsgw_cockpit_manifest'")
    for key in ("manifest_version", "topic_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "lane_manifest",
        "current_records",
        "report_artifacts",
        "script_artifacts",
        "plot_guard",
        "refresh_intake",
        "typed_record_templates",
        "dashboard",
    ):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key, expected in (
        ("trust_update_forbidden", True),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    _validate_lane_manifest(payload.get("lane_manifest"), f"{path}.lane_manifest", result)


def _validate_lane_manifest(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("status",):
        _require_nonempty_str(payload, key, path, result)
    for key in ("final_lane", "diagnostic_lane"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("forbidden_roots", "preferred_roots", "observed_remote_roots"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_source_records(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topics",
        "evidence",
        "tool_runs",
        "reference_locations",
        "validation_contracts",
        "sensemaking_reports",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
