"""Contracts for progressive recording navigator surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping
from brain.v5.record_ref_contracts import validate_record_ref_lookup

_DECISIONS = {"ignore", "defer", "navigate", "checkpoint"}


def validate_recording_candidate_classification(
    payload: dict[str, Any],
    *,
    path: str = "recording_candidate_classification",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    _require_kind(payload, path, result, "recording_candidate_classification")
    if payload.get("decision") not in _DECISIONS:
        result.add(f"{path}.decision", "must be a supported decision")
    for key in ("trigger_reasons", "suggested_slots", "candidate_refs", "produced_artifacts", "allowed_decisions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    policy = payload.get("navigation_policy")
    _require_mapping(policy, f"{path}.navigation_policy", result)
    if isinstance(policy, dict):
        for key in ("write_at_classification", "write_at_navigation"):
            if policy.get(key) is not False:
                result.add(f"{path}.navigation_policy.{key}", "must be false")
        for key in ("write_only_after_slot_expansion", "trust_change_requires_preflight", "agent_should_not_record_every_step"):
            if policy.get(key) is not True:
                result.add(f"{path}.navigation_policy.{key}", "must be true")
    _require_read_only(payload, path, result)
    return result


def require_valid_recording_candidate_classification(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_recording_candidate_classification(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_recording_navigation_state(
    payload: dict[str, Any],
    *,
    path: str = "recording_navigation_state",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    _require_kind(payload, path, result, "recording_navigation_state")
    for key in ("first_level_slots", "recommended_slots", "trust_boundary_reasons", "warnings"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    current = payload.get("current_position")
    _require_mapping(current, f"{path}.current_position", result)
    graph = payload.get("graph_context")
    _require_mapping(graph, f"{path}.graph_context", result)
    if isinstance(graph, dict):
        for key in ("recommended_moments", "provenance_gaps", "open_obligations"):
            _require_list(graph.get(key), f"{path}.graph_context.{key}", result)
    next_step = payload.get("next_step")
    _require_mapping(next_step, f"{path}.next_step", result)
    if isinstance(next_step, dict):
        if next_step.get("read_tool") != "aitp_v5_expand_recording_slot":
            result.add(f"{path}.next_step.read_tool", "must point to slot expansion")
        if next_step.get("verify_tool") != "aitp_v5_verify_recording_effect":
            result.add(f"{path}.next_step.verify_tool", "must point to effect verification")
    slots = payload.get("first_level_slots")
    if isinstance(slots, list):
        for index, item in enumerate(slots):
            _validate_slot_summary(item, f"{path}.first_level_slots[{index}]", result)
    _require_read_only(payload, path, result)
    return result


def require_valid_recording_navigation_state(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_recording_navigation_state(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_recording_slot_expansion(
    payload: dict[str, Any],
    *,
    path: str = "recording_slot_expansion",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    _require_kind(payload, path, result, "recording_slot_expansion")
    for key in (
        "required_fields",
        "optional_fields",
        "recommended_links",
        "graph_edges_created",
        "warnings",
        "recording_sequence",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("recommended_write_tool"), str):
        result.add(f"{path}.recommended_write_tool", "must be a string")
    if payload.get("verify_with") != "aitp_v5_verify_recording_effect":
        result.add(f"{path}.verify_with", "must be aitp_v5_verify_recording_effect")
    trust = payload.get("trust_effect")
    _require_mapping(trust, f"{path}.trust_effect", result)
    if isinstance(trust, dict):
        if trust.get("can_update_claim_trust") is not False:
            result.add(f"{path}.trust_effect.can_update_claim_trust", "must be false")
        if trust.get("claim_trust_mutation") != "none":
            result.add(f"{path}.trust_effect.claim_trust_mutation", "must be none")
    for field_key in ("required_fields", "optional_fields"):
        fields = payload.get(field_key)
        if isinstance(fields, list):
            for index, item in enumerate(fields):
                _validate_field_hint(item, f"{path}.{field_key}[{index}]", result)
    _require_read_only(payload, path, result)
    return result


def require_valid_recording_slot_expansion(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_recording_slot_expansion(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_recording_effect_verification(
    payload: dict[str, Any],
    *,
    path: str = "recording_effect_verification",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    _require_kind(payload, path, result, "recording_effect_verification")
    for key in ("expected_refs", "found_refs", "missing_refs", "current_recommended_slots", "failure_reasons"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if not isinstance(payload.get("verified"), bool):
        result.add(f"{path}.verified", "must be a boolean")
    graph_delta = payload.get("graph_delta")
    _require_mapping(graph_delta, f"{path}.graph_delta", result)
    if isinstance(graph_delta, dict):
        for key in ("new_node_ids", "new_edge_ids"):
            _require_list(graph_delta.get(key), f"{path}.graph_delta.{key}", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _require_read_only(payload, path, result)
    return result


def require_valid_recording_effect_verification(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_recording_effect_verification(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _require_kind(payload: dict[str, Any], path: str, result: ContractResult, expected: str) -> None:
    if payload.get("kind") != expected:
        result.add(f"{path}.kind", f"must be {expected!r}")


def _require_read_only(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if payload.get("truth_source") != "typed_records" and payload.get("truth_source") != "event_metadata_and_typed_records":
        result.add(f"{path}.truth_source", "must be typed_records or event_metadata_and_typed_records")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_slot_summary(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("slot", "record_kind", "recommended_write_tool", "expand_with", "when_to_use"):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if item.get("read_only_at_this_layer") is not True:
        result.add(f"{path}.read_only_at_this_layer", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_field_hint(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("name", "known_value", "source"):
        if not isinstance(item.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
