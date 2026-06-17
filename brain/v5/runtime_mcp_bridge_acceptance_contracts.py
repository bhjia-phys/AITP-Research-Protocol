"""Contracts for live host MCP bridge acceptance checks."""

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


def validate_runtime_mcp_bridge_acceptance(
    payload: dict[str, Any],
    *,
    path: str = "runtime_mcp_bridge_acceptance",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "runtime_mcp_bridge_acceptance":
        result.add(f"{path}.kind", "must be 'runtime_mcp_bridge_acceptance'")
    if payload.get("status") not in {
        "accepted",
        "expected_contract_only",
        "stale_or_incomplete",
    }:
        result.add(f"{path}.status", "must be an accepted bridge exposure status")
    if payload.get("truth_source") != "runtime_bridge_target_manifest_and_live_host_inputs":
        result.add(
            f"{path}.truth_source",
            "must be 'runtime_bridge_target_manifest_and_live_host_inputs'",
        )
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _validate_expected(payload.get("expected"), f"{path}.expected", result)
    _validate_live(payload.get("live"), f"{path}.live", result)
    _validate_comparison(payload.get("comparison"), f"{path}.comparison", result)
    _require_list(payload.get("acceptance_criteria"), f"{path}.acceptance_criteria", result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    return result


def require_valid_runtime_mcp_bridge_acceptance(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_runtime_mcp_bridge_acceptance(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_expected(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("target_count", "operation_count", "mcp_tool_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("operations", "mcp_tools", "required_mcp_tools", "recording_navigator_tools"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_nonempty_str(payload, "manifest_tool", path, result)
    _require_mapping(payload.get("canonical_manifest"), f"{path}.canonical_manifest", result)


def _validate_live(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("manifest_provided", "tools_provided"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a bool")
    if payload.get("target_count") is not None and not isinstance(payload.get("target_count"), int):
        result.add(f"{path}.target_count", "must be an int or null")
    _require_list(payload.get("operations"), f"{path}.operations", result)
    _require_list(payload.get("mcp_tools"), f"{path}.mcp_tools", result)


def _validate_comparison(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("manifest_checked", "tools_checked", "target_count_matches"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a bool")
    for key in (
        "missing_operations",
        "extra_operations",
        "missing_mcp_tools",
        "extra_mcp_tools",
        "recording_navigator_tools_missing",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
