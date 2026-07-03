"""Contracts for read-only literature extraction reports."""

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
    "paper_summary_as_evidence",
    "extraction_report_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_extraction_report(
    payload: dict[str, Any],
    *,
    path: str = "literature_extraction_report",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_extraction_report":
        result.add(f"{path}.kind", "must be 'literature_extraction_report'")
    for key in (
        "session_id",
        "topic_id",
        "requested_report_profile",
        "report_profile",
        "report_profile_label",
        "read_surface_effect",
        "truth_source",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "literature_extraction_report_only":
        result.add(f"{path}.read_surface_effect", "must be 'literature_extraction_report_only'")
    _require_counted_list(payload, "source_refs", "source_ref_count", path, result, nonempty=True)
    _require_counted_list(payload, "focus_terms", "focus_term_count", path, result)
    _require_counted_list(payload, "profile_sections", "profile_section_count", path, result, nonempty=True)
    _require_counted_list(payload, "source_reports", "source_report_count", path, result, nonempty=True)
    if isinstance(payload.get("profile_sections"), list):
        for index, item in enumerate(payload["profile_sections"]):
            _validate_profile_section(item, f"{path}.profile_sections[{index}]", result)
    if isinstance(payload.get("source_reports"), list):
        for index, item in enumerate(payload["source_reports"]):
            _validate_source_report(item, f"{path}.source_reports[{index}]", result)
    for key in ("covered_source_count", "blocked_source_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if isinstance(payload.get("source_reports"), list):
        if payload.get("covered_source_count", 0) + payload.get("blocked_source_count", 0) != len(payload["source_reports"]):
            result.add(f"{path}.covered_source_count", "covered plus blocked counts must equal source report count")
    _require_list(payload.get("missing_section_ids"), f"{path}.missing_section_ids", result)
    _validate_aggregate_counts(payload.get("aggregate_counts"), f"{path}.aggregate_counts", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("report_policy"), f"{path}.report_policy", result)
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


def require_valid_literature_extraction_report(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_extraction_report(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_profile_section(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("section_id", "purpose"):
        _require_nonempty_str(value, key, path, result)
    _require_list(value.get("target_records"), f"{path}.target_records", result)
    if isinstance(value.get("target_records"), list) and not value["target_records"]:
        result.add(f"{path}.target_records", "must not be empty")
    _require_bool_value(value.get("requires_existing_typed_records"), True, f"{path}.requires_existing_typed_records", result)
    _require_orientation_flags(value, path, result)


def _validate_source_report(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("source_ref", "topic_id", "report_profile", "coverage_status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("coverage_status") not in {"profile_ready", "missing_typed_records"}:
        result.add(f"{path}.coverage_status", "must be profile_ready or missing_typed_records")
    for key in (
        "source_identity_refs",
        "reference_location_refs",
        "extracted_object_refs",
        "extracted_relation_refs",
        "proof_obligation_refs",
        "sensemaking_report_refs",
        "extracted_objects",
        "extracted_relations",
        "proof_obligations",
        "sensemaking_reports",
        "sections",
        "missing_section_ids",
        "recommended_next_entrypoints",
    ):
        _require_list(value.get(key), f"{path}.{key}", result)
    if isinstance(value.get("sections"), list):
        if value.get("section_count") != len(value["sections"]):
            result.add(f"{path}.section_count", "must equal sections length")
        for index, section in enumerate(value["sections"]):
            _validate_source_section(section, f"{path}.sections[{index}]", result)
    _require_orientation_flags(value, path, result)


def _validate_source_section(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("section_id", "purpose", "coverage_status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("coverage_status") not in {"covered", "missing_typed_records"}:
        result.add(f"{path}.coverage_status", "must be covered or missing_typed_records")
    for key in ("target_records", "item_refs", "missing_record_kinds"):
        _require_list(value.get(key), f"{path}.{key}", result)
    if isinstance(value.get("item_refs"), list) and value.get("item_count") != len(value["item_refs"]):
        result.add(f"{path}.item_count", "must equal item_refs length")
    if not isinstance(value.get("recommended_next_entrypoint"), str):
        result.add(f"{path}.recommended_next_entrypoint", "must be a string")
    _require_orientation_flags(value, path, result)


def _validate_aggregate_counts(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in (
        "source_asset_count",
        "reference_location_count",
        "physics_object_count",
        "object_relation_count",
        "proof_obligation_count",
        "sensemaking_report_count",
    ):
        if not isinstance(value.get(key), int) or value[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_list(value.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(value.get("allowed_next_entrypoints"), f"{path}.allowed_next_entrypoints", result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_bool_value(value.get("requires_existing_typed_records"), True, f"{path}.requires_existing_typed_records", result)
    _require_bool_value(value.get("requires_explicit_next_entrypoint"), True, f"{path}.requires_explicit_next_entrypoint", result)
    forbidden_uses = value.get("forbidden_uses") if isinstance(value.get("forbidden_uses"), list) else []
    for forbidden in _FORBIDDEN_USES:
        if forbidden not in forbidden_uses:
            result.add(f"{path}.forbidden_uses", f"must include {forbidden!r}")


def _require_orientation_flags(value: dict[str, Any], path: str, result: ContractResult) -> None:
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _require_counted_list(
    payload: dict[str, Any],
    key: str,
    count_key: str,
    path: str,
    result: ContractResult,
    *,
    nonempty: bool = False,
) -> None:
    _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get(key), list):
        if nonempty and not payload[key]:
            result.add(f"{path}.{key}", "must not be empty")
        if payload.get(count_key) != len(payload[key]):
            result.add(f"{path}.{count_key}", f"must equal {key} length")
