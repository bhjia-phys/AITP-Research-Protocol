"""Full-only MCP wrappers for exact M2 execution operations."""

from __future__ import annotations

from typing import Any

from brain.v5.execution_facade_common import decode_payload, execution_result
from brain.v5.execution_facade_reads import dispatch_execution_read
from brain.v5.execution_facade_gated import dispatch_execution_gated
from brain.v5.execution_surface_contracts import execution_operation_specs
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths


def invoke_execution_operation(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    spec = execution_operation_specs().get(operation)
    if spec is None:
        raise ValueError(f"unsupported execution operation: {operation}")
    ws = WorkspacePaths(resolve_workspace_base(base))
    payload = decode_payload(payload_json)
    value = (
        dispatch_execution_read(ws, operation, payload)
        if spec.state_effect == "read_only"
        else dispatch_execution_gated(ws, operation, payload)
    )
    return execution_result(operation, value)


def _invoke(base: str, operation: str, payload_json: str) -> dict[str, Any]:
    return invoke_execution_operation(base, operation, payload_json)


def aitp_v5_execution_get_record_version(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_get_record_version", payload_json)


def aitp_v5_execution_assess_scope(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_assess_scope", payload_json)


def aitp_v5_execution_build_compute_intake(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_build_compute_intake", payload_json)


def aitp_v5_execution_resolve_effective_attempt(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_resolve_effective_attempt", payload_json)


def aitp_v5_execution_assess_baseline_readiness(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_assess_baseline_readiness", payload_json)


def aitp_v5_execution_project_maturity(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_project_maturity", payload_json)


def aitp_v5_execution_build_formula_code_capsule(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_build_formula_code_capsule", payload_json)


def aitp_v5_execution_project_derivation_status(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_project_derivation_status", payload_json)


def aitp_v5_execution_request_bound_checkpoint(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_request_bound_checkpoint", payload_json)


def aitp_v5_execution_decide_bound_checkpoint(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_decide_bound_checkpoint", payload_json)


def aitp_v5_execution_apply_bound_action(base: str, *, payload_json: str) -> dict[str, Any]:
    return _invoke(base, "execution_apply_bound_action", payload_json)
