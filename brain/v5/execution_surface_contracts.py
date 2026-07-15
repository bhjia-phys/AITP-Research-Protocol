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
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("writes_records") is not False:
        result.add(f"{path}.writes_records", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    operation_result = payload.get("result")
    if not isinstance(operation_result, dict):
        result.add(f"{path}.result", "must be a mapping")
        return result
    for field in spec.required_result_fields:
        if field not in operation_result:
            result.add(f"{path}.result.{field}", "is required")
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


def _validate_pin(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be an exact pin mapping")
        return
    if not _typed_ref(value.get("record_ref")):
        result.add(f"{path}.record_ref", "must be a typed record ref")
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
