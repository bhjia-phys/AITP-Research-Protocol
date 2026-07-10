"""Contracts for the cross-surface AITP capability registry audit."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_COUNT_FIELDS = (
    "capability_count",
    "catalog_count",
    "mcp_wrapper_count",
    "public_surface_count",
    "compact_count",
    "bridge_target_count",
)


def validate_capability_registry_audit(
    payload: dict[str, Any],
    *,
    path: str = "capability_registry_audit",
) -> ContractResult:
    result = ContractResult()
    if payload.get("kind") != "capability_registry_audit":
        result.add(f"{path}.kind", "must be 'capability_registry_audit'")
    if payload.get("schema_version") != "aitp.capability_registry_audit.v1":
        result.add(f"{path}.schema_version", "must be the v1 audit schema")
    for field in _COUNT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, int) or value < 0:
            result.add(f"{path}.{field}", "must be a non-negative integer")
    issues = payload.get("issues")
    if not isinstance(issues, list) or any(not isinstance(item, str) for item in issues):
        result.add(f"{path}.issues", "must be a list of strings")
    ok = payload.get("ok")
    if not isinstance(ok, bool):
        result.add(f"{path}.ok", "must be boolean")
    elif isinstance(issues, list) and ok != (not issues):
        result.add(f"{path}.ok", "must equal whether the issue list is empty")
    for field in ("state_effect_counts", "visibility_counts"):
        value = payload.get(field)
        if not isinstance(value, dict) or any(
            not isinstance(key, str) or not isinstance(count, int) or count < 0
            for key, count in value.items()
        ):
            result.add(f"{path}.{field}", "must be string-to-count mapping")
    operations = payload.get("mcp_only_operations")
    if not isinstance(operations, list) or any(
        not isinstance(operation, str) or not operation for operation in operations
    ):
        result.add(f"{path}.mcp_only_operations", "must be non-empty string list")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    if ok is False:
        result.add(f"{path}.ok", "registry parity must be clean")
    return result


def require_valid_capability_registry_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_capability_registry_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
