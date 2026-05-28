"""Contracts for vNext readiness manifests."""

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


def validate_vnext_readiness_manifest(
    payload: dict[str, Any], *, path: str = "vnext_readiness_manifest"
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "vnext_readiness_manifest":
        result.add(f"{path}.kind", "must be 'vnext_readiness_manifest'")
    if payload.get("control_plane_status") not in {
        "ready",
        "ready_with_lane_exemplar_backlog",
        "surface_gaps",
    }:
        result.add(f"{path}.control_plane_status", "must be a known vNext readiness status")
    _require_mapping(payload.get("phase_statuses"), f"{path}.phase_statuses", result)
    for key in (
        "workstreams",
        "missing_workstreams",
        "backlog_workstreams",
        "stable_output_spine",
        "priority_hosts",
        "deferred_hosts",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("lane_exemplar_manifest"), f"{path}.lane_exemplar_manifest", result)
    _require_nonempty_str(payload, "stable_output_contract_doc", path, result)
    _require_nonempty_str(payload, "truth_source", path, result)
    for key, expected in (
        ("trust_update_forbidden", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    for index, item in enumerate(payload.get("workstreams") or []):
        _validate_workstream(item, f"{path}.workstreams[{index}]", result)
    return result


def require_valid_vnext_readiness_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_vnext_readiness_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_workstream(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("name", "phase", "status", "acceptance"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("runtime_entrypoints", "surfaces", "missing_entrypoints", "missing_surfaces"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
