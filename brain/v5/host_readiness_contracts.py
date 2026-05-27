"""Contracts for dynamic runtime host-readiness audits."""

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


def validate_runtime_host_readiness_audit(
    payload: dict[str, Any],
    *,
    path: str = "runtime_host_readiness_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "runtime_host_readiness_audit":
        result.add(f"{path}.kind", "must be 'runtime_host_readiness_audit'")
    for key in ("runtime", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "runtime_process_and_files":
        result.add(f"{path}.truth_source", "must be 'runtime_process_and_files'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _validate_process(payload.get("process"), f"{path}.process", result)
    _validate_install(payload.get("installation_audit"), f"{path}.installation_audit", result)
    _validate_session_start(payload.get("session_start_smoke"), f"{path}.session_start_smoke", result)
    _validate_production_loop(payload.get("production_loop"), f"{path}.production_loop", result)
    return result


def require_valid_runtime_host_readiness_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_runtime_host_readiness_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_runtime_host_production_loop_audit(
    payload: dict[str, Any],
    *,
    path: str = "runtime_host_production_loop_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "runtime_host_production_loop_audit":
        result.add(f"{path}.kind", "must be 'runtime_host_production_loop_audit'")
    if payload.get("truth_source") != "runtime_process_and_files":
        result.add(f"{path}.truth_source", "must be 'runtime_process_and_files'")
    for key in ("runtimes", "priority_hosts", "deferred_hosts", "items"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("runtime_count", "ready_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("status_counts", "next_action_counts", "lifecycle_status_counts"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("lifecycle_smoke_ran"), bool):
        result.add(f"{path}.lifecycle_smoke_ran", "must be a bool")
    if isinstance(payload.get("items"), list):
        for index, item in enumerate(payload["items"]):
            _validate_production_item(item, f"{path}.items[{index}]", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_runtime_host_production_loop_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_runtime_host_production_loop_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_process(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "command", path, result)
    _require_list(payload.get("args"), f"{path}.args", result)
    for key in ("found", "ok"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a bool")
    if payload.get("exit_code") is not None and not isinstance(payload.get("exit_code"), int):
        result.add(f"{path}.exit_code", "must be an int or null")
    for key in ("stdout", "stderr"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")


def _validate_install(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if not isinstance(payload.get("checked"), bool):
        result.add(f"{path}.checked", "must be a bool")
    _require_nonempty_str(payload, "status", path, result)
    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    if payload.get("checked"):
        _require_list(payload.get("checked_paths"), f"{path}.checked_paths", result)


def _validate_session_start(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if not isinstance(payload.get("ran"), bool):
        result.add(f"{path}.ran", "must be a bool")
    if not isinstance(payload.get("ok"), bool):
        result.add(f"{path}.ok", "must be a bool")


def _validate_production_loop(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("status", "runtime", "lifecycle_probe_command"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    for key in (
        "priority_host",
        "deferred_host",
        "install_audit_required",
        "session_start_smoke_available",
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a bool")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_production_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("runtime", "status", "command", "install_status", "lifecycle_probe_command"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "process_ok",
        "process_found",
        "install_audit_required",
        "session_start_smoke_available",
        "session_start_smoke_ran",
        "session_start_smoke_ok",
        "lifecycle_smoke_ran",
        "lifecycle_process_ok",
        "lifecycle_hook_output_observed",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a bool")
    if not isinstance(payload.get("lifecycle_smoke_status"), str):
        result.add(f"{path}.lifecycle_smoke_status", "must be a string")
    if not isinstance(payload.get("lifecycle_trace_delta_count"), int) or payload["lifecycle_trace_delta_count"] < 0:
        result.add(f"{path}.lifecycle_trace_delta_count", "must be a non-negative integer")
    if not isinstance(payload.get("command_path"), str):
        result.add(f"{path}.command_path", "must be a string")
    _require_list(payload.get("next_actions"), f"{path}.next_actions", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
