"""Operation registry and deep result contract for the full M2 execution facade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.v5.contracts import ContractError, ContractResult


import re


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExecutionOperationSpec:
    operation: str
    mcp_name: str
    state_effect: str
    required_result_fields: tuple[str, ...]
    truth_source: str


_READ = {
    "execution_get_record_version": (
        ("pinned_ref", "record", "body", "version_source"),
        "typed_records",
    ),
    "execution_assess_scope": (
        ("decision", "dependency_refs", "reasons"),
        "typed_records",
    ),
    "execution_build_compute_intake": (
        ("status", "coverage", "writes_records", "orientation_only"),
        "detached_collector_manifest",
    ),
    "execution_resolve_effective_attempt": (
        ("requested_run_ref", "topology_status", "attempt_eligible"),
        "typed_records",
    ),
    "execution_assess_baseline_readiness": (
        ("request", "ready", "blocking_reasons"),
        "typed_records",
    ),
    "execution_project_maturity": (
        ("run_ref", "recorded_maturity", "effective_maturity"),
        "typed_records",
    ),
    "execution_build_formula_code_capsule": (
        ("relation_ref", "exact_expansion_refs", "exact_expansion_pins", "ready_for_edit"),
        "typed_records",
    ),
    "execution_project_derivation_status": (
        ("chain_ref", "requested_chain_ref", "structurally_closed", "reviewed", "validated"),
        "typed_records",
    ),
}

_GATED = {
    "execution_request_bound_checkpoint": (
        (
            "status",
            "session_id",
            "claim_id",
            "checkpoint_id",
            "request_ref",
            "binding",
            "pre_tool_decision",
        ),
        "typed_records",
    ),
    "execution_decide_bound_checkpoint": (
        (
            "status",
            "session_id",
            "claim_id",
            "request_ref",
            "decision_ref",
            "binding",
            "pre_tool_decision",
        ),
        "typed_records_and_host_attestation",
    ),
    "execution_apply_bound_action": (
        (
            "status",
            "session_id",
            "claim_id",
            "action",
            "request_ref",
            "decision_ref",
            "result_refs",
            "application_receipt_ref",
            "replayed",
            "pre_tool_decision",
        ),
        "typed_records_and_host_attestation",
    ),
}


def execution_operation_specs() -> dict[str, ExecutionOperationSpec]:
    specs = {
        operation: ExecutionOperationSpec(
            operation=operation,
            mcp_name=f"aitp_v5_{operation}",
            state_effect="read_only",
            required_result_fields=required,
            truth_source=truth_source,
        )
        for operation, (required, truth_source) in _READ.items()
    }
    specs.update({
        operation: ExecutionOperationSpec(
            operation=operation,
            mcp_name=f"aitp_v5_{operation}",
            state_effect="kernel_write",
            required_result_fields=required,
            truth_source=truth_source,
        )
        for operation, (required, truth_source) in _GATED.items()
    })
    return specs


def execution_capability_rows() -> tuple[tuple[str, str, str, str, str, str], ...]:
    return tuple(
        (
            spec.operation,
            spec.mcp_name,
            f"aitp-v5 execution {spec.operation} --payload-file <args>",
            "execution_operation_result",
            spec.state_effect,
            "full",
        )
        for spec in execution_operation_specs().values()
    )


def execution_surface_names() -> tuple[str, ...]:
    return ("execution_operation_result",)


def execution_surface_purposes() -> dict[str, str]:
    return {
        "execution_operation_result": (
            "full-only exact M2 execution or derivation operation result"
        )
    }


def execution_surface_validators():
    return {"execution_operation_result": require_valid_execution_operation_result}


def validate_execution_operation_result(
    payload: dict[str, Any],
    *,
    path: str = "execution_operation_result",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "execution_operation_result":
        result.add(f"{path}.kind", "must be 'execution_operation_result'")
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    operation = payload.get("operation")
    spec = execution_operation_specs().get(operation)
    if spec is None:
        result.add(f"{path}.operation", "must name a registered execution operation")
        return result
    if payload.get("truth_source") != spec.truth_source:
        result.add(f"{path}.truth_source", f"must be {spec.truth_source!r}")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("state_effect") != spec.state_effect:
        result.add(f"{path}.state_effect", f"must be {spec.state_effect!r}")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    kernel_write = spec.state_effect == "kernel_write"
    if payload.get("can_update_kernel_state") is not kernel_write:
        result.add(f"{path}.can_update_kernel_state", f"must be {kernel_write!r}")
    if payload.get("writes_records") is not kernel_write:
        result.add(f"{path}.writes_records", f"must be {kernel_write!r}")
    if payload.get("orientation_only") is not (not kernel_write):
        result.add(f"{path}.orientation_only", f"must be {not kernel_write!r}")
    operation_result = payload.get("result")
    if not isinstance(operation_result, dict):
        result.add(f"{path}.result", "must be a mapping")
        return result
    for field in spec.required_result_fields:
        if field not in operation_result:
            result.add(f"{path}.result.{field}", "is required")
    if kernel_write:
        _validate_gated_result(operation, operation_result, result, f"{path}.result")
    else:
        _validate_read_result(operation, operation_result, result, f"{path}.result")
    return result


def _validate_read_result(
    operation: str,
    value: dict[str, Any],
    result: ContractResult,
    path: str,
) -> None:
    if operation == "execution_get_record_version":
        _validate_pin(value.get("pinned_ref"), result, f"{path}.pinned_ref")
        if not isinstance(value.get("record"), dict):
            result.add(f"{path}.record", "must be a mapping")
        if not isinstance(value.get("body"), str):
            result.add(f"{path}.body", "must be a string")
        if value.get("version_source") not in {"current", "archive"}:
            result.add(f"{path}.version_source", "must be current or archive")
    elif operation == "execution_assess_scope":
        if value.get("decision") not in {"allowed", "denied", "requires_revalidation"}:
            result.add(
                f"{path}.decision",
                "must be allowed, denied, or requires_revalidation",
            )
        _validate_pin_list(value.get("dependency_refs"), result, f"{path}.dependency_refs")
        _validate_string_list(value.get("reasons"), result, f"{path}.reasons")
    elif operation == "execution_build_compute_intake":
        if not isinstance(value.get("status"), str) or not value.get("status"):
            result.add(f"{path}.status", "must be a non-empty string")
        if value.get("writes_records") is not False:
            result.add(f"{path}.writes_records", "must be false")
        if value.get("orientation_only") is not True:
            result.add(f"{path}.orientation_only", "must be true")
    elif operation == "execution_resolve_effective_attempt":
        _validate_pin(value.get("requested_run_ref"), result, f"{path}.requested_run_ref")
        if not isinstance(value.get("topology_status"), str) or not value.get("topology_status"):
            result.add(f"{path}.topology_status", "must be a non-empty string")
        if not isinstance(value.get("attempt_eligible"), bool):
            result.add(f"{path}.attempt_eligible", "must be a boolean")
    elif operation == "execution_assess_baseline_readiness":
        request = value.get("request")
        if not isinstance(request, dict):
            result.add(f"{path}.request", "must be a mapping")
        else:
            _validate_pin(request.get("run_ref"), result, f"{path}.request.run_ref")
            _validate_pin_list(
                request.get("validation_refs"),
                result,
                f"{path}.request.validation_refs",
            )
        if not isinstance(value.get("ready"), bool):
            result.add(f"{path}.ready", "must be a boolean")
    elif operation == "execution_project_maturity":
        _validate_pin(value.get("run_ref"), result, f"{path}.run_ref")
        for field in ("recorded_maturity", "effective_maturity"):
            if not isinstance(value.get(field), str) or not value.get(field):
                result.add(f"{path}.{field}", "must be a non-empty string")
    elif operation == "execution_build_formula_code_capsule":
        _validate_pin(value.get("relation_ref"), result, f"{path}.relation_ref")
        refs = value.get("exact_expansion_refs")
        if not isinstance(refs, list) or not refs or any(not _typed_ref(item) for item in refs):
            result.add(f"{path}.exact_expansion_refs", "must contain typed refs")
        pins = value.get("exact_expansion_pins")
        _validate_pin_list(pins, result, f"{path}.exact_expansion_pins")
        if isinstance(refs, list) and isinstance(pins, list):
            pin_refs = [item.get("record_ref") for item in pins if isinstance(item, dict)]
            if pin_refs != refs:
                result.add(
                    f"{path}.exact_expansion_pins",
                    "must correspond one-to-one with exact_expansion_refs",
                )
            relation_ref = value.get("relation_ref")
            if isinstance(relation_ref, dict) and relation_ref not in pins:
                result.add(
                    f"{path}.relation_ref",
                    "must be present in exact_expansion_pins",
                )
        if not isinstance(value.get("ready_for_edit"), bool):
            result.add(f"{path}.ready_for_edit", "must be a boolean")
    elif operation == "execution_project_derivation_status":
        _validate_pin(value.get("requested_chain_ref"), result, f"{path}.requested_chain_ref")
        requested = value.get("requested_chain_ref")
        if isinstance(requested, dict) and value.get("chain_ref") != requested.get("record_ref"):
            result.add(f"{path}.chain_ref", "must match requested_chain_ref.record_ref")
        for field in ("structurally_closed", "reviewed", "validated"):
            if not isinstance(value.get(field), bool):
                result.add(f"{path}.{field}", "must be a boolean")


def _validate_gated_result(
    operation: str,
    value: dict[str, Any],
    result: ContractResult,
    path: str,
) -> None:
    if not isinstance(value.get("status"), str) or not value.get("status"):
        result.add(f"{path}.status", "must be a non-empty string")
    for field in ("session_id", "claim_id"):
        if not isinstance(value.get(field), str) or not value.get(field):
            result.add(f"{path}.{field}", "must be a non-empty string")
    _validate_pre_tool(value.get("pre_tool_decision"), result, f"{path}.pre_tool_decision")
    if operation == "execution_request_bound_checkpoint":
        _validate_pin(
            value.get("request_ref"),
            result,
            f"{path}.request_ref",
            expected_kind="human_checkpoint",
        )
        request_ref = value.get("request_ref")
        if isinstance(request_ref, dict):
            expected_id = request_ref.get("record_ref", "").partition(":")[2]
            if value.get("checkpoint_id") != expected_id:
                result.add(f"{path}.checkpoint_id", "must match request_ref")
        _validate_binding(value.get("binding"), result, f"{path}.binding")
        _validate_pre_tool_binding(
            value,
            result,
            path,
            expected_action="request_human_checkpoint",
        )
    elif operation == "execution_decide_bound_checkpoint":
        request_ref = value.get("request_ref")
        decision_ref = value.get("decision_ref")
        _validate_pin(request_ref, result, f"{path}.request_ref", expected_kind="human_checkpoint")
        _validate_pin(decision_ref, result, f"{path}.decision_ref", expected_kind="human_checkpoint")
        if isinstance(request_ref, dict) and isinstance(decision_ref, dict):
            if decision_ref.get("record_ref") != request_ref.get("record_ref"):
                result.add(f"{path}.decision_ref.record_ref", "must match request_ref")
            if decision_ref.get("revision") != request_ref.get("revision", 0) + 1:
                result.add(f"{path}.decision_ref.revision", "must supersede request revision")
        _validate_binding(value.get("binding"), result, f"{path}.binding")
        _validate_pre_tool_binding(
            value,
            result,
            path,
            expected_action="decide_human_checkpoint",
        )
    elif operation == "execution_apply_bound_action":
        action = value.get("action")
        allowed = {
            "accept_execution_baseline": {"execution_baseline"},
            "approve_scope_revalidation": {"scope_revalidation_decision"},
            "execute_bound_tool": {"tool_run", "validation_result"},
        }
        if action not in allowed:
            result.add(f"{path}.action", "must be a supported bound action")
        _validate_pin(value.get("request_ref"), result, f"{path}.request_ref", expected_kind="human_checkpoint")
        _validate_pin(value.get("decision_ref"), result, f"{path}.decision_ref", expected_kind="human_checkpoint")
        request_ref = value.get("request_ref")
        decision_ref = value.get("decision_ref")
        if isinstance(request_ref, dict) and isinstance(decision_ref, dict):
            if decision_ref.get("record_ref") != request_ref.get("record_ref"):
                result.add(f"{path}.decision_ref.record_ref", "must match request_ref")
            if decision_ref.get("revision") != request_ref.get("revision", 0) + 1:
                result.add(f"{path}.decision_ref.revision", "must supersede request revision")
        refs = value.get("result_refs")
        _validate_pin_list(refs, result, f"{path}.result_refs")
        if action in allowed and isinstance(refs, list):
            kinds = {
                item.get("record_ref", "").partition(":")[0]
                for item in refs
                if isinstance(item, dict)
            }
            expected_count = len(allowed[action])
            if kinds != allowed[action] or len(refs) != expected_count:
                result.add(f"{path}.result_refs", "must match the bound action result families")
        _validate_pin(
            value.get("application_receipt_ref"),
            result,
            f"{path}.application_receipt_ref",
            expected_kind="checkpoint_application_receipt",
        )
        if not isinstance(value.get("replayed"), bool):
            result.add(f"{path}.replayed", "must be a boolean")
        _validate_pre_tool_binding(value, result, path, expected_action=str(action or ""))


def _validate_binding(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be a checkpoint binding mapping")
        return
    _validate_pin(value.get("intent"), result, f"{path}.intent")
    _validate_pin_list(value.get("subjects"), result, f"{path}.subjects")
    for field in ("action", "effect_policy", "replay_policy"):
        if not isinstance(value.get(field), str) or not value.get(field):
            result.add(f"{path}.{field}", "must be a non-empty string")
    for field in ("action_payload_hash", "request_hash"):
        if not isinstance(value.get(field), str) or not _SHA256.fullmatch(value[field]):
            result.add(f"{path}.{field}", "must be lowercase sha256")
    _validate_string_list(value.get("target_scope_refs"), result, f"{path}.target_scope_refs")


def _validate_pre_tool(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be a pre-tool decision mapping")
        return
    if value.get("block") is not False:
        result.add(f"{path}.block", "must be false")
    if value.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be typed_records")
    if value.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if value.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_pre_tool_binding(
    value: dict[str, Any],
    result: ContractResult,
    path: str,
    *,
    expected_action: str,
) -> None:
    pre_tool = value.get("pre_tool_decision")
    if not isinstance(pre_tool, dict):
        return
    for field in ("session_id", "claim_id"):
        if pre_tool.get(field) != value.get(field):
            result.add(f"{path}.pre_tool_decision.{field}", f"must match {field}")
    if pre_tool.get("action") != expected_action:
        result.add(f"{path}.pre_tool_decision.action", "must match the facade action")
    if expected_action in {
        "accept_execution_baseline",
        "approve_scope_revalidation",
        "execute_bound_tool",
    }:
        decision_ref = value.get("decision_ref")
        expected_checkpoint = (
            decision_ref.get("record_ref", "").partition(":")[2]
            if isinstance(decision_ref, dict)
            else ""
        )
        if pre_tool.get("human_checkpoint_id") != expected_checkpoint:
            result.add(
                f"{path}.pre_tool_decision.human_checkpoint_id",
                "must match decision_ref",
            )


def _validate_pin(
    value: Any,
    result: ContractResult,
    path: str,
    *,
    expected_kind: str = "",
) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be an exact pin mapping")
        return
    if not _typed_ref(value.get("record_ref")):
        result.add(f"{path}.record_ref", "must be a typed record ref")
    elif expected_kind and value["record_ref"].partition(":")[0] != expected_kind:
        result.add(f"{path}.record_ref", f"must use {expected_kind!r} family")
    if not isinstance(value.get("content_hash"), str) or not _SHA256.fullmatch(value["content_hash"]):
        result.add(f"{path}.content_hash", "must be lowercase sha256")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.revision", "must be a positive integer")


def _validate_pin_list(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list of exact pins")
        return
    for index, item in enumerate(value):
        _validate_pin(item, result, f"{path}[{index}]")


def _validate_string_list(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        result.add(path, "must be a list of strings")


def _typed_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    kind, separator, record_id = value.partition(":")
    return bool(separator and kind.strip() and record_id.strip())


def require_valid_execution_operation_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_execution_operation_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
