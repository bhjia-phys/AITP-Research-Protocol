"""Contracts for read-only literature comparison draft packets."""

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
from brain.v5.record_ref_contracts import validate_record_ref_lookup


_FORBIDDEN_USES = (
    "literature_comparison_record",
    "evidence_support",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_comparison_draft(
    payload: dict[str, Any],
    *,
    path: str = "literature_comparison_draft",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_comparison_draft":
        result.add(f"{path}.kind", "must be 'literature_comparison_draft'")
    for key in (
        "session_id",
        "topic_id",
        "comparison_question",
        "read_surface_effect",
        "truth_source",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "comparison_draft_only":
        result.add(f"{path}.read_surface_effect", "must be 'comparison_draft_only'")
    _require_list(payload.get("source_refs"), f"{path}.source_refs", result)
    if isinstance(payload.get("source_refs"), list):
        if not payload["source_refs"]:
            result.add(f"{path}.source_refs", "must not be empty")
        if payload.get("source_ref_count") != len(payload["source_refs"]):
            result.add(f"{path}.source_ref_count", "must equal source_refs length")
    _require_list(payload.get("comparison_dimensions"), f"{path}.comparison_dimensions", result)
    if isinstance(payload.get("comparison_dimensions"), list):
        if not payload["comparison_dimensions"]:
            result.add(f"{path}.comparison_dimensions", "must not be empty")
        if payload.get("comparison_dimension_count") != len(payload["comparison_dimensions"]):
            result.add(
                f"{path}.comparison_dimension_count",
                "must equal comparison_dimensions length",
            )
        for index, item in enumerate(payload["comparison_dimensions"]):
            _validate_dimension(item, f"{path}.comparison_dimensions[{index}]", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _validate_draft_intent(payload.get("draft_record_intent"), f"{path}.draft_record_intent", result)
    _require_list(payload.get("suggested_sections"), f"{path}.suggested_sections", result)
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("draft_policy"), f"{path}.draft_policy", result)
    _validate_allowed_next_tool_call(
        payload.get("allowed_next_tool_call"),
        f"{path}.allowed_next_tool_call",
        result,
    )
    for key in (
        "draft_creates_records",
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
    ):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)
    for key in ("read_only", "requires_explicit_next_action", "orientation_only", "trust_update_forbidden"):
        _require_bool_value(payload.get(key), True, f"{path}.{key}", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    return result


def require_valid_literature_comparison_draft(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_comparison_draft(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_dimension(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "dimension", path, result)
    if value.get("status") != "draft_placeholder":
        result.add(f"{path}.status", "must be 'draft_placeholder'")
    _require_bool_value(value.get("requires_source_review"), True, f"{path}.requires_source_review", result)
    for key in (
        "summary_inputs_trusted",
        "creates_record_now",
        "records_validation_result",
        "source_support_result",
    ):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_draft_intent(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    if value.get("kind") != "literature_comparison_record_candidate":
        result.add(f"{path}.kind", "must be 'literature_comparison_record_candidate'")
    if value.get("status") != "draft_only":
        result.add(f"{path}.status", "must be 'draft_only'")
    for key in (
        "requires_explicit_write_surface",
        "requires_source_review",
        "requires_evidence_or_reference_records",
        "requires_trust_preflight_before_claim_trust",
    ):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    for key in (
        "creates_record_now",
        "records_validation_result",
        "source_support_result",
        "can_update_claim_trust",
    ):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_list(value.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(value.get("allowed_next_entrypoints"), f"{path}.allowed_next_entrypoints", result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_bool_value(
        value.get("requires_explicit_next_entrypoint"),
        True,
        f"{path}.requires_explicit_next_entrypoint",
        result,
    )
    forbidden_uses = value.get("forbidden_uses") if isinstance(value.get("forbidden_uses"), list) else []
    for forbidden in _FORBIDDEN_USES:
        if forbidden not in forbidden_uses:
            result.add(f"{path}.forbidden_uses", f"must include {forbidden!r}")


def _validate_allowed_next_tool_call(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    if value.get("action") != "plan_primitive_tools":
        result.add(f"{path}.action", "must be 'plan_primitive_tools'")
    if value.get("action_id") != "source.compare_literature":
        result.add(f"{path}.action_id", "must be 'source.compare_literature'")
    _require_bool_value(value.get("requires_explicit_next_action"), True, f"{path}.requires_explicit_next_action", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
