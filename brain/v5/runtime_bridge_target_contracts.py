"""Contracts for host-facing runtime bridge target manifests."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping
from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
from brain.v5.runtime_entrypoints import runtime_entrypoints


def validate_runtime_bridge_target_manifest(
    payload: dict[str, Any],
    *,
    path: str = "runtime_bridge_target_manifest",
) -> ContractResult:
    """Validate that bridge targets match canonical runtime entrypoints."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("kind") != "runtime_bridge_target_manifest":
        result.add(f"{path}.kind", "must be 'runtime_bridge_target_manifest'")
    if payload.get("preferred_transport") != "mcp":
        result.add(f"{path}.preferred_transport", "must be 'mcp'")
    if payload.get("fallback_transport") != "cli":
        result.add(f"{path}.fallback_transport", "must be 'cli'")
    if payload.get("truth_source") != "runtime_entrypoint_catalog":
        result.add(f"{path}.truth_source", "must be 'runtime_entrypoint_catalog'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")

    targets = payload.get("targets")
    _require_list(targets, f"{path}.targets", result)
    if isinstance(targets, list):
        if payload.get("target_count") != len(targets):
            result.add(f"{path}.target_count", "must match targets length")
        _validate_targets(targets, f"{path}.targets", result)

    expected = runtime_bridge_target_manifest()
    if payload != expected:
        result.add(path, "must match runtime_bridge_target_manifest()")
    return result


def require_valid_runtime_bridge_target_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a runtime bridge target manifest or raise a contract error."""

    result = validate_runtime_bridge_target_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_targets(targets: list[Any], path: str, result: ContractResult) -> None:
    entrypoints = runtime_entrypoints()
    seen_operations: set[str] = set()
    for index, target in enumerate(targets):
        item_path = f"{path}.{index}"
        _require_mapping(target, item_path, result)
        if not isinstance(target, dict):
            continue

        operation = target.get("operation")
        if not isinstance(operation, str) or not operation:
            result.add(f"{item_path}.operation", "must be a non-empty string")
        elif operation in seen_operations:
            result.add(f"{item_path}.operation", "must be unique")
        else:
            seen_operations.add(operation)

        entrypoint_key = target.get("entrypoint_key")
        if not isinstance(entrypoint_key, str) or entrypoint_key not in entrypoints:
            result.add(f"{item_path}.entrypoint_key", "must name a runtime entrypoint")
            continue
        entrypoint = entrypoints[entrypoint_key]
        if target.get("mcp_tool") != entrypoint["mcp"]:
            result.add(f"{item_path}.mcp_tool", "must match runtime entrypoint MCP tool")
        if target.get("cli_fallback") != entrypoint["cli"]:
            result.add(f"{item_path}.cli_fallback", "must match runtime entrypoint CLI template")
        if target.get("surface") != entrypoint["surface"]:
            result.add(f"{item_path}.surface", "must match runtime entrypoint surface")
        if target.get("preferred_transport") != "mcp":
            result.add(f"{item_path}.preferred_transport", "must be 'mcp'")
        if target.get("fallback_transport") != "cli":
            result.add(f"{item_path}.fallback_transport", "must be 'cli'")
        if target.get("claim_trust_mutation") != "none":
            result.add(f"{item_path}.claim_trust_mutation", "must be 'none'")
        if target.get("can_update_claim_trust") is not False:
            result.add(f"{item_path}.can_update_claim_trust", "must be false")
