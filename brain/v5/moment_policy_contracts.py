"""Contracts for host-agnostic moment policy payloads."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping


_DECISION_TYPES = {"recording", "brainstorming", "backtrace", "route", "trust_boundary"}
_LIFECYCLE_PHASES = {"pre_turn", "pre_action", "pre_final"}


def validate_host_agnostic_moment_policy(
    payload: dict[str, Any],
    *,
    path: str = "host_agnostic_moment_policy",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "host_agnostic_moment_policy":
        result.add(f"{path}.kind", "must be 'host_agnostic_moment_policy'")
    if payload.get("derived_from") != "process_graph_slice":
        result.add(f"{path}.derived_from", "must be 'process_graph_slice'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("policy_axes", "decisions", "recommended_moments", "trust_boundary_reasons"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("decisions"), list):
        for index, decision in enumerate(payload["decisions"]):
            _validate_decision(decision, f"{path}.decisions[{index}]", result)
    return result


def require_valid_host_agnostic_moment_policy(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_host_agnostic_moment_policy(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_decision(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("moment", "decision_type", "action_kind", "reason", "target_type", "target_id"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("decision_type") not in _DECISION_TYPES:
        result.add(f"{path}.decision_type", f"must be one of {sorted(_DECISION_TYPES)}")
    for key in ("required_now", "trust_boundary", "summary_inputs_trusted", "orientation_only", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key in (
        "missing_components",
        "record_entrypoints",
        "exploration_entrypoints",
        "entrypoints",
        "lifecycle_phases",
        "trigger_conditions",
        "payload_hints",
        "required_before_trust_change",
        "recommended_host_behavior",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _validate_lifecycle_phases(payload.get("lifecycle_phases"), f"{path}.lifecycle_phases", result)
    _validate_string_list(payload.get("trigger_conditions"), f"{path}.trigger_conditions", result)
    _validate_string_list(payload.get("recommended_host_behavior"), f"{path}.recommended_host_behavior", result)
    if not isinstance(payload.get("recording_threshold"), str) or not payload.get("recording_threshold"):
        result.add(f"{path}.recording_threshold", "must be a non-empty string")
    _validate_trust_boundary_inputs(payload.get("trust_boundary_inputs"), payload, f"{path}.trust_boundary_inputs", result)
    if isinstance(payload.get("payload_hints"), list):
        for index, hint in enumerate(payload["payload_hints"]):
            _validate_payload_hint(hint, f"{path}.payload_hints[{index}]", result)
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_lifecycle_phases(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, list):
        return
    if not payload:
        result.add(path, "must not be empty")
        return
    for index, value in enumerate(payload):
        if value not in _LIFECYCLE_PHASES:
            result.add(f"{path}[{index}]", f"must be one of {sorted(_LIFECYCLE_PHASES)}")


def _validate_string_list(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, list):
        return
    if not payload:
        result.add(path, "must not be empty")
        return
    for index, value in enumerate(payload):
        if not isinstance(value, str) or not value:
            result.add(f"{path}[{index}]", "must be a non-empty string")


def _validate_trust_boundary_inputs(
    payload: Any,
    decision: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("target_refs", "entrypoints", "required_before_trust_change"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("requires_preflight", "final_gate_required"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if not isinstance(payload.get("claim_id"), str):
        result.add(f"{path}.claim_id", "must be a string")
    target_ref = f"{decision.get('target_type')}:{decision.get('target_id')}"
    if isinstance(payload.get("target_refs"), list) and target_ref not in payload["target_refs"]:
        result.add(f"{path}.target_refs", f"must include {target_ref!r}")
    if isinstance(payload.get("entrypoints"), list) and isinstance(decision.get("entrypoints"), list):
        if payload["entrypoints"] != decision["entrypoints"]:
            result.add(f"{path}.entrypoints", "must match decision.entrypoints")
    if isinstance(payload.get("required_before_trust_change"), list) and isinstance(
        decision.get("required_before_trust_change"),
        list,
    ):
        if payload["required_before_trust_change"] != decision["required_before_trust_change"]:
            result.add(f"{path}.required_before_trust_change", "must match decision.required_before_trust_change")
    if isinstance(decision.get("entrypoints"), list):
        expected_preflight = "aitp_v5_preflight_trust_update" in decision["entrypoints"]
        if payload.get("requires_preflight") is not expected_preflight:
            result.add(f"{path}.requires_preflight", f"must be {expected_preflight}")
    if isinstance(decision.get("trust_boundary"), bool):
        expected_final_gate = decision["trust_boundary"] or decision.get("decision_type") == "trust_boundary"
        if payload.get("final_gate_required") is not expected_final_gate:
            result.add(f"{path}.final_gate_required", f"must be {expected_final_gate}")


def _validate_payload_hint(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("entrypoint", "record_action", "target_type", "target_id", "action_kind"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    _require_mapping(payload.get("draft"), f"{path}.draft", result)
    _require_list(payload.get("required_fields"), f"{path}.required_fields", result)
    for key in ("orientation_only", "summary_inputs_trusted", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
