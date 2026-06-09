"""Contracts for literature/source review handoff packets."""

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
from brain.v5.literature_intake_contracts import validate_literature_intake_suggestion
from brain.v5.record_ref_contracts import validate_record_ref_lookup
from brain.v5.source_reconstruction_contracts import validate_source_reconstruction_review_packet


def validate_literature_source_review_handoff(
    payload: dict[str, Any],
    *,
    path: str = "literature_source_review_handoff",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_source_review_handoff":
        result.add(f"{path}.kind", "must be 'literature_source_review_handoff'")
    for key in ("session_id", "topic_id", "truth_source", "read_surface_effect"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "handoff_context_only":
        result.add(f"{path}.read_surface_effect", "must be 'handoff_context_only'")

    result.extend(
        validate_literature_intake_suggestion(
            payload.get("literature_intake_suggestion"),
            path=f"{path}.literature_intake_suggestion",
        )
    )
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _validate_optional_mapping(payload.get("source_stack_coverage_item"), f"{path}.source_stack_coverage_item", result)
    _validate_optional_review_packet(payload.get("source_reconstruction_review_packet"), f"{path}.source_reconstruction_review_packet", result)
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _require_mapping(payload.get("handoff_policy"), f"{path}.handoff_policy", result)
    if isinstance(payload.get("handoff_policy"), dict):
        policy = payload["handoff_policy"]
        _require_bool_value(
            policy.get("requires_explicit_next_entrypoint"),
            True,
            f"{path}.handoff_policy.requires_explicit_next_entrypoint",
            result,
        )
        _require_list(policy.get("allowed_next_entrypoints"), f"{path}.handoff_policy.allowed_next_entrypoints", result)
        _require_list(policy.get("forbidden_uses"), f"{path}.handoff_policy.forbidden_uses", result)
        for forbidden in (
            "evidence_support",
            "source_support_result",
            "validation_result",
            "write_execution",
            "final_gate_satisfaction",
            "claim_trust_update",
            "trust_apply",
        ):
            if forbidden not in (policy.get("forbidden_uses") or []):
                result.add(f"{path}.handoff_policy.forbidden_uses", f"must include {forbidden!r}")
    _require_mapping(payload.get("allowed_next_tool_call"), f"{path}.allowed_next_tool_call", result)
    if isinstance(payload.get("allowed_next_tool_call"), dict):
        call = payload["allowed_next_tool_call"]
        if call.get("action") != "plan_primitive_tools":
            result.add(f"{path}.allowed_next_tool_call.action", "must be 'plan_primitive_tools'")
        if call.get("action_id") != "source.review_context":
            result.add(f"{path}.allowed_next_tool_call.action_id", "must be 'source.review_context'")
        _require_bool_value(
            call.get("requires_explicit_next_action"),
            True,
            f"{path}.allowed_next_tool_call.requires_explicit_next_action",
            result,
        )
        _require_bool_value(
            call.get("records_validation_result"),
            False,
            f"{path}.allowed_next_tool_call.records_validation_result",
            result,
        )
        _require_bool_value(
            call.get("source_support_result"),
            False,
            f"{path}.allowed_next_tool_call.source_support_result",
            result,
        )
        if call.get("claim_trust_mutation") != "none":
            result.add(f"{path}.allowed_next_tool_call.claim_trust_mutation", "must be 'none'")

    for key in (
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "write_executed",
        "bridge_called",
        "executes_write_now",
        "mutates_next_payload_now",
        "infers_payload_values",
        "trust_update_forbidden",
    ):
        if key == "trust_update_forbidden":
            _require_bool_value(payload.get(key), True, f"{path}.{key}", result)
        else:
            _require_bool_value(payload.get(key), False, f"{path}.{key}", result)
    _require_bool_value(payload.get("read_only"), True, f"{path}.read_only", result)
    _require_bool_value(
        payload.get("requires_explicit_next_action"),
        True,
        f"{path}.requires_explicit_next_action",
        result,
    )
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    return result


def require_valid_literature_source_review_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_source_review_handoff(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_optional_mapping(value: Any, path: str, result: ContractResult) -> None:
    if value == {}:
        return
    _require_mapping(value, path, result)


def _validate_optional_review_packet(value: Any, path: str, result: ContractResult) -> None:
    if value == {}:
        return
    result.extend(validate_source_reconstruction_review_packet(value, path=path))
