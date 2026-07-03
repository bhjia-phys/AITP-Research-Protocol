"""Contracts for read-only literature reading route packets."""

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


_ROUTE_TYPES = {"single_paper", "paired_paper", "multi_paper"}
_FORBIDDEN_USES = (
    "paper_summary_as_evidence",
    "literature_synthesis_record",
    "evidence_support",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_reading_route(
    payload: dict[str, Any],
    *,
    path: str = "literature_reading_route",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_reading_route":
        result.add(f"{path}.kind", "must be 'literature_reading_route'")
    for key in ("session_id", "topic_id", "reading_question", "context_profile_id", "read_surface_effect", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("route_type") not in _ROUTE_TYPES:
        result.add(f"{path}.route_type", f"must be one of {sorted(_ROUTE_TYPES)}")
    if payload.get("read_surface_effect") != "literature_reading_route_only":
        result.add(f"{path}.read_surface_effect", "must be 'literature_reading_route_only'")
    for key, count_key in (
        ("source_refs", "source_ref_count"),
        ("focus_terms", "focus_term_count"),
        ("source_requirements", "source_requirement_count"),
        ("route_steps", "route_step_count"),
        ("extraction_report_templates", "extraction_report_template_count"),
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
        if isinstance(payload.get(key), list) and payload.get(count_key) != len(payload[key]):
            result.add(f"{path}.{count_key}", f"must equal {key} length")
    if isinstance(payload.get("source_refs"), list) and not payload["source_refs"]:
        result.add(f"{path}.source_refs", "must not be empty")
    for index, item in enumerate(payload.get("source_requirements") or []):
        _validate_source_requirement(item, f"{path}.source_requirements[{index}]", result)
    for index, item in enumerate(payload.get("route_steps") or []):
        _validate_route_step(item, f"{path}.route_steps[{index}]", result)
    _require_list(payload.get("comparison_dimensions"), f"{path}.comparison_dimensions", result)
    for index, item in enumerate(payload.get("comparison_dimensions") or []):
        _validate_comparison_dimension(item, f"{path}.comparison_dimensions[{index}]", result)
    for index, item in enumerate(payload.get("extraction_report_templates") or []):
        _validate_extraction_template(item, f"{path}.extraction_report_templates[{index}]", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("route_policy"), f"{path}.route_policy", result)
    _require_list(payload.get("allowed_next_tool_calls"), f"{path}.allowed_next_tool_calls", result)
    for index, item in enumerate(payload.get("allowed_next_tool_calls") or []):
        _validate_allowed_next_tool_call(item, f"{path}.allowed_next_tool_calls[{index}]", result)
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


def require_valid_literature_reading_route(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_reading_route(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_source_requirement(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "source_ref", path, result)
    _require_list(value.get("required_before_synthesis"), f"{path}.required_before_synthesis", result)
    _require_list(value.get("acceptable_anchor_types"), f"{path}.acceptable_anchor_types", result)
    for key in ("exact_anchor_required", "orientation_only"):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    for key in ("summary_inputs_trusted", "creates_record_now", "source_support_result"):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_route_step(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("step_id", "purpose", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("status") != "planned":
        result.add(f"{path}.status", "must be 'planned'")
    _require_list(value.get("source_refs"), f"{path}.source_refs", result)
    _require_bool_value(value.get("requires_exact_reference_locations"), True, f"{path}.requires_exact_reference_locations", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    for key in ("creates_record_now", "records_validation_result", "source_support_result", "summary_inputs_trusted"):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_comparison_dimension(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "dimension", path, result)
    if value.get("status") != "draft_placeholder":
        result.add(f"{path}.status", "must be 'draft_placeholder'")
    _require_bool_value(value.get("requires_source_review"), True, f"{path}.requires_source_review", result)
    for key in ("creates_record_now", "source_support_result", "summary_inputs_trusted"):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_extraction_template(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("template_id", "template_type", "source_ref"):
        _require_nonempty_str(value, key, path, result)
    _require_list(value.get("required_sections"), f"{path}.required_sections", result)
    for key in ("requires_exact_reference_locations", "orientation_only"):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    for key in ("records_created_by_template", "summary_inputs_trusted"):
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
        value.get("requires_exact_reference_locations_before_synthesis"),
        True,
        f"{path}.requires_exact_reference_locations_before_synthesis",
        result,
    )
    _require_bool_value(value.get("requires_explicit_next_entrypoint"), True, f"{path}.requires_explicit_next_entrypoint", result)
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
    _require_nonempty_str(value, "action_id", path, result)
    _require_bool_value(value.get("requires_explicit_next_action"), True, f"{path}.requires_explicit_next_action", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
