"""Read-only acceptance checks for live host MCP bridge exposure."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest


_MANIFEST_TOOL = "aitp_v5_get_runtime_bridge_target_manifest"
_RECORDING_NAVIGATOR_TOOLS = (
    "aitp_v5_build_workspace_recording_audit",
    "aitp_v5_classify_recording_candidate",
    "aitp_v5_get_recording_navigation_state",
    "aitp_v5_expand_recording_slot",
    "aitp_v5_verify_recording_effect",
)


def audit_runtime_mcp_bridge_acceptance(
    *,
    live_manifest: dict[str, Any] | None = None,
    live_tool_names: Any | None = None,
) -> dict[str, Any]:
    """Compare live host MCP exposure with the canonical bridge target manifest."""

    expected_manifest = runtime_bridge_target_manifest()
    expected_operations = [target["operation"] for target in expected_manifest["targets"]]
    expected_mcp_tools = sorted({target["mcp_tool"] for target in expected_manifest["targets"]})
    required_mcp_tools = sorted({*expected_mcp_tools, _MANIFEST_TOOL})
    live_manifest_payload = _normalize_manifest(live_manifest)
    live_tools = _normalize_tool_names(live_tool_names)
    manifest_comparison = _compare_manifest(expected_manifest, live_manifest_payload)
    tool_comparison = _compare_tools(required_mcp_tools, live_tools)
    comparison = {
        "manifest_checked": live_manifest_payload is not None,
        "tools_checked": live_tools is not None,
        "target_count_matches": manifest_comparison["target_count_matches"],
        "missing_operations": manifest_comparison["missing_operations"],
        "extra_operations": manifest_comparison["extra_operations"],
        "missing_mcp_tools": tool_comparison["missing_mcp_tools"],
        "extra_mcp_tools": tool_comparison["extra_mcp_tools"],
        "recording_navigator_tools_missing": [
            tool for tool in _RECORDING_NAVIGATOR_TOOLS if tool in tool_comparison["missing_mcp_tools"]
        ],
    }
    status = _status(comparison)
    return {
        "kind": "runtime_mcp_bridge_acceptance",
        "status": status,
        "expected": {
            "target_count": expected_manifest["target_count"],
            "operation_count": len(expected_operations),
            "operations": expected_operations,
            "mcp_tool_count": len(expected_mcp_tools),
            "mcp_tools": expected_mcp_tools,
            "required_mcp_tools": required_mcp_tools,
            "recording_navigator_tools": list(_RECORDING_NAVIGATOR_TOOLS),
            "manifest_tool": _MANIFEST_TOOL,
            "canonical_manifest": deepcopy(expected_manifest),
        },
        "live": {
            "manifest_provided": live_manifest_payload is not None,
            "target_count": _live_target_count(live_manifest_payload),
            "operations": _live_operations(live_manifest_payload),
            "tools_provided": live_tools is not None,
            "mcp_tools": live_tools or [],
        },
        "comparison": comparison,
        "acceptance_criteria": [
            "live manifest target_count equals canonical target_count",
            "live manifest operations include every canonical bridge target operation",
            "live MCP tools include every canonical bridge target mcp_tool plus the manifest tool",
            "recording navigator MCP tools are present before hosts rely on progressive recording",
        ],
        "next_actions": _next_actions(status, comparison),
        "truth_source": "runtime_bridge_target_manifest_and_live_host_inputs",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _normalize_manifest(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    manifest = payload.get("runtime_bridge_target_manifest", payload)
    if isinstance(manifest, dict):
        return manifest
    return None


def _normalize_tool_names(payload: Any | None) -> list[str] | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        if isinstance(payload.get("tool_names"), list):
            return _normalize_tool_names(payload["tool_names"])
        if isinstance(payload.get("tools"), list):
            return _normalize_tool_names(payload["tools"])
        result = payload.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            return _normalize_tool_names(result["tools"])
        return []
    if not isinstance(payload, list):
        return []
    names: list[str] = []
    for item in payload:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return sorted({name for name in names if name})


def _compare_manifest(
    expected: dict[str, Any],
    live: dict[str, Any] | None,
) -> dict[str, Any]:
    expected_operations = set(_live_operations(expected))
    if live is None:
        return {
            "target_count_matches": False,
            "missing_operations": [],
            "extra_operations": [],
        }
    live_operations = set(_live_operations(live))
    target_count_matches = _live_target_count(live) == expected.get("target_count")
    return {
        "target_count_matches": target_count_matches,
        "missing_operations": sorted(expected_operations - live_operations),
        "extra_operations": sorted(live_operations - expected_operations),
    }


def _compare_tools(required: list[str], live: list[str] | None) -> dict[str, list[str]]:
    if live is None:
        return {
            "missing_mcp_tools": [],
            "extra_mcp_tools": [],
        }
    live_set = set(live or [])
    required_set = set(required)
    return {
        "missing_mcp_tools": sorted(required_set - live_set),
        "extra_mcp_tools": sorted(live_set - required_set),
    }


def _status(comparison: dict[str, Any]) -> str:
    if not comparison["manifest_checked"] and not comparison["tools_checked"]:
        return "expected_contract_only"
    if comparison["manifest_checked"] and not comparison["target_count_matches"]:
        return "stale_or_incomplete"
    if comparison["missing_operations"] or comparison["missing_mcp_tools"]:
        return "stale_or_incomplete"
    return "accepted"


def _next_actions(status: str, comparison: dict[str, Any]) -> list[str]:
    if status == "accepted":
        return ["host_mcp_bridge_exposure_accepted"]
    if status == "expected_contract_only":
        return ["call_live_mcp_manifest_and_tools_list_then_rerun_acceptance"]
    actions: list[str] = []
    if not comparison["target_count_matches"] or comparison["missing_operations"]:
        actions.append("restart_or_refresh_host_mcp_session")
    if comparison["recording_navigator_tools_missing"]:
        actions.append("verify_host_reimported_latest_native_mcp_server")
    if _MANIFEST_TOOL in comparison["missing_mcp_tools"]:
        actions.append("repair_mcp_config_to_expose_v5_manifest_tool")
    if comparison["missing_mcp_tools"]:
        actions.append("rerun_tools_list_after_refresh")
    return actions or ["inspect_live_host_mcp_exposure"]


def _live_target_count(payload: dict[str, Any] | None) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get("target_count")
    return value if isinstance(value, int) else None


def _live_operations(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    targets = payload.get("targets")
    if not isinstance(targets, list):
        return []
    return [
        target["operation"]
        for target in targets
        if isinstance(target, dict) and isinstance(target.get("operation"), str)
    ]
