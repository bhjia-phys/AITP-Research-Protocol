"""Contracts for read-only literature source extraction candidate packets."""

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
    "extracted_source_fact",
    "evidence_support",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_source_extraction_candidates(
    payload: dict[str, Any],
    *,
    path: str = "literature_source_extraction_candidates",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_source_extraction_candidates":
        result.add(f"{path}.kind", "must be 'literature_source_extraction_candidates'")
    for key in ("session_id", "topic_id", "read_surface_effect", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "extraction_candidates_only":
        result.add(f"{path}.read_surface_effect", "must be 'extraction_candidates_only'")
    _require_list(payload.get("source_refs"), f"{path}.source_refs", result)
    if isinstance(payload.get("source_refs"), list):
        if not payload["source_refs"]:
            result.add(f"{path}.source_refs", "must not be empty")
        if payload.get("source_ref_count") != len(payload["source_refs"]):
            result.add(f"{path}.source_ref_count", "must equal source_refs length")
    _require_list(payload.get("focus_terms"), f"{path}.focus_terms", result)
    if isinstance(payload.get("focus_terms"), list) and payload.get("focus_term_count") != len(payload["focus_terms"]):
        result.add(f"{path}.focus_term_count", "must equal focus_terms length")
    _require_list(payload.get("extraction_modes"), f"{path}.extraction_modes", result)
    if isinstance(payload.get("extraction_modes"), list):
        if not payload["extraction_modes"]:
            result.add(f"{path}.extraction_modes", "must not be empty")
        if payload.get("extraction_mode_count") != len(payload["extraction_modes"]):
            result.add(f"{path}.extraction_mode_count", "must equal extraction_modes length")
    _require_list(payload.get("candidate_groups"), f"{path}.candidate_groups", result)
    if isinstance(payload.get("candidate_groups"), list):
        if not payload["candidate_groups"]:
            result.add(f"{path}.candidate_groups", "must not be empty")
        if payload.get("candidate_group_count") != len(payload["candidate_groups"]):
            result.add(f"{path}.candidate_group_count", "must equal candidate_groups length")
        for index, item in enumerate(payload["candidate_groups"]):
            _validate_candidate_group(item, f"{path}.candidate_groups[{index}]", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _validate_draft_intent(payload.get("draft_record_intent"), f"{path}.draft_record_intent", result)
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("extraction_policy"), f"{path}.extraction_policy", result)
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


def require_valid_literature_source_extraction_candidates(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_source_extraction_candidates(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_candidate_group(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("mode", "candidate_kind", "target_record", "topic_id", "purpose", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("status") != "candidate_only":
        result.add(f"{path}.status", "must be 'candidate_only'")
    for key in ("source_refs", "focus_terms", "required_fields", "review_questions"):
        _require_list(value.get(key), f"{path}.{key}", result)
    if isinstance(value.get("source_refs"), list) and not value["source_refs"]:
        result.add(f"{path}.source_refs", "must not be empty")
    for key in (
        "requires_source_review",
        "orientation_only",
    ):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    for key in (
        "creates_record_now",
        "records_validation_result",
        "source_support_result",
        "summary_inputs_trusted",
    ):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_draft_intent(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    if value.get("kind") != "literature_source_extraction_candidate_set":
        result.add(f"{path}.kind", "must be 'literature_source_extraction_candidate_set'")
    if value.get("status") != "draft_only":
        result.add(f"{path}.status", "must be 'draft_only'")
    for key in ("requires_explicit_write_surface", "requires_source_review"):
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
    if value.get("action_id") != "source.extract_candidates":
        result.add(f"{path}.action_id", "must be 'source.extract_candidates'")
    _require_bool_value(value.get("requires_explicit_next_action"), True, f"{path}.requires_explicit_next_action", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
