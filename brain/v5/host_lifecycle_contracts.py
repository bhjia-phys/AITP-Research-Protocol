"""Contracts for host lifecycle probes and bounded real-event dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


HOST_LIFECYCLE_EVENT_SCHEMA_VERSION = "aitp.host_lifecycle_event.v1"
HOST_LIFECYCLE_DISPATCH_SCHEMA_VERSION = "aitp.host_lifecycle_dispatch.v1"


@dataclass(frozen=True)
class HostLifecycleEvent:
    """Allowlisted host event with stable identity and no raw host payload."""

    event_id: str
    logical_event: str
    native_event: str
    occurred_at: str
    host: str
    host_session_id: str
    session_id: str
    topic_id: str
    subject_refs: tuple[str, ...]
    objective_payload: Mapping[str, Any]
    process_payload: Mapping[str, Any]
    automatic: bool
    origin: str
    schema_version: str = HOST_LIFECYCLE_EVENT_SCHEMA_VERSION


@dataclass(frozen=True)
class HostLifecycleDispatch:
    """Trust-neutral result that never carries injected context text."""

    dispatch_id: str
    event_id: str
    logical_event: str
    host: str
    host_session_id: str
    session_id: str
    topic_id: str
    status: str
    operation: str
    reason_codes: tuple[str, ...]
    receipt_id: str = ""
    receipt_status: str = ""
    runtime_write: bool = False
    canonical_write: bool = False
    trust_effect: str = "none"
    schema_version: str = HOST_LIFECYCLE_DISPATCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.canonical_write is not False:
            raise ValueError("host lifecycle dispatch cannot authorize canonical writes")
        if self.trust_effect != "none":
            raise ValueError("host lifecycle dispatch must remain trust-neutral")


def validate_runtime_host_lifecycle_audit(
    payload: dict[str, Any],
    *,
    path: str = "runtime_host_lifecycle_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "runtime_host_lifecycle_audit":
        result.add(f"{path}.kind", "must be 'runtime_host_lifecycle_audit'")
    for key in ("runtime", "status", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "runtime_process_and_hook_trace":
        result.add(
            f"{path}.truth_source", "must be 'runtime_process_and_hook_trace'"
        )
    _require_bool_value(
        payload.get("summary_inputs_trusted"),
        False,
        f"{path}.summary_inputs_trusted",
        result,
    )
    _require_bool_value(
        payload.get("orientation_only"), True, f"{path}.orientation_only", result
    )
    _require_bool_value(
        payload.get("can_update_kernel_state"),
        False,
        f"{path}.can_update_kernel_state",
        result,
    )
    _require_bool_value(
        payload.get("can_update_claim_trust"),
        False,
        f"{path}.can_update_claim_trust",
        result,
    )
    _validate_process(payload.get("process"), f"{path}.process", result)
    _validate_trace(payload.get("trace"), f"{path}.trace", result)
    _validate_hook_output(payload.get("hook_output"), f"{path}.hook_output", result)
    return result


def require_valid_runtime_host_lifecycle_audit(
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = validate_runtime_host_lifecycle_audit(payload)
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
    if payload.get("exit_code") is not None and not isinstance(
        payload.get("exit_code"), int
    ):
        result.add(f"{path}.exit_code", "must be an int or null")
    for key in ("stdout", "stderr"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")


def _validate_trace(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "path", path, result)
    for key in ("before_count", "after_count", "delta_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative int")
    _require_list(payload.get("new_event_ids"), f"{path}.new_event_ids", result)


def _validate_hook_output(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if not isinstance(payload.get("observed"), bool):
        result.add(f"{path}.observed", "must be a bool")
    _require_list(payload.get("observed_kinds"), f"{path}.observed_kinds", result)


__all__ = [
    "HOST_LIFECYCLE_DISPATCH_SCHEMA_VERSION",
    "HOST_LIFECYCLE_EVENT_SCHEMA_VERSION",
    "HostLifecycleDispatch",
    "HostLifecycleEvent",
    "require_valid_runtime_host_lifecycle_audit",
    "validate_runtime_host_lifecycle_audit",
]
