"""Contracts for corpus-backed literature extraction artifact drafts."""

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
    "curated_rag_chunk_as_evidence",
    "corpus_backed_artifact_as_evidence",
    "paper_summary_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_corpus_extraction_artifact(
    payload: dict[str, Any],
    *,
    path: str = "literature_corpus_extraction_artifact",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_corpus_extraction_artifact":
        result.add(f"{path}.kind", "must be 'literature_corpus_extraction_artifact'")
    for key in (
        "session_id",
        "topic_id",
        "artifact_intent",
        "report_profile",
        "read_surface_effect",
        "truth_source",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "literature_corpus_extraction_artifact_only":
        result.add(f"{path}.read_surface_effect", "must be 'literature_corpus_extraction_artifact_only'")
    _require_counted_list(payload, "chunk_ids", "chunk_count", path, result, nonempty=True)
    _require_counted_list(payload, "reference_location_ids", "reference_location_count", path, result, nonempty=True)
    _require_counted_list(payload, "focus_terms", "focus_term_count", path, result)
    _require_counted_list(payload, "chunk_items", "chunk_item_count", path, result, nonempty=True)
    _require_counted_list(payload, "reference_location_items", "reference_location_item_count", path, result, nonempty=True)
    _require_counted_list(payload, "alignment_items", "alignment_item_count", path, result, nonempty=True)
    for key in ("found_reference_location_count", "missing_reference_location_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if isinstance(payload.get("reference_location_items"), list):
        if payload.get("found_reference_location_count", 0) + payload.get("missing_reference_location_count", 0) != len(payload["reference_location_items"]):
            result.add(f"{path}.found_reference_location_count", "found plus missing counts must equal reference item count")
        for index, item in enumerate(payload["reference_location_items"]):
            _validate_reference_location_item(item, f"{path}.reference_location_items[{index}]", result)
    if isinstance(payload.get("chunk_items"), list):
        for index, item in enumerate(payload["chunk_items"]):
            _validate_chunk_item(item, f"{path}.chunk_items[{index}]", result)
    if isinstance(payload.get("alignment_items"), list):
        for index, item in enumerate(payload["alignment_items"]):
            _validate_alignment_item(item, f"{path}.alignment_items[{index}]", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _validate_artifact_draft(payload.get("artifact_draft"), f"{path}.artifact_draft", result)
    _validate_downstream_call(payload.get("downstream_extraction_report_call"), f"{path}.downstream_extraction_report_call", result)
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("artifact_policy"), f"{path}.artifact_policy", result)
    for key in (
        "draft_creates_records",
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "artifact_record_created",
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


def require_valid_literature_corpus_extraction_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_corpus_extraction_artifact(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_chunk_item(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in (
        "chunk_id",
        "document_id",
        "corpus_id",
        "index_mode",
        "index_status",
        "retrieval_role",
        "document_title",
        "document_source_uri",
        "document_content_hash",
        "chunk_summary",
        "chunk_content_hash",
    ):
        _require_nonempty_str(value, key, path, result)
    if value.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    _require_mapping(value.get("chunk_anchor"), f"{path}.chunk_anchor", result)
    _require_list(value.get("chunk_tags"), f"{path}.chunk_tags", result)
    _require_bool_value(
        value.get("promotion_required_before_claim_support"),
        True,
        f"{path}.promotion_required_before_claim_support",
        result,
    )
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_orientation_flags(value, path, result)


def _validate_reference_location_item(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("input_ref", "record_ref", "location_id", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("status") not in {"found", "missing"}:
        result.add(f"{path}.status", "must be found or missing")
    if not isinstance(value.get("exact_anchor_available"), bool):
        result.add(f"{path}.exact_anchor_available", "must be a boolean")
    if value.get("status") == "found":
        for key in ("topic_id", "connector_id", "location_type", "uri", "label"):
            _require_nonempty_str(value, key, path, result)
        _require_mapping(value.get("metadata"), f"{path}.metadata", result)
    if not isinstance(value.get("recommended_next_entrypoint"), str):
        result.add(f"{path}.recommended_next_entrypoint", "must be a string")
    _require_orientation_flags(value, path, result)


def _validate_alignment_item(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("chunk_id", "document_id", "alignment_status", "retrieval_role"):
        _require_nonempty_str(value, key, path, result)
    if value.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    if value.get("alignment_status") not in {"has_typed_anchor_candidate", "missing_reference_location"}:
        result.add(f"{path}.alignment_status", "must be a known alignment status")
    _require_counted_list(value, "candidate_reference_locations", "candidate_reference_location_count", path, result)
    if not isinstance(value.get("direct_alignment_count"), int) or value["direct_alignment_count"] < 0:
        result.add(f"{path}.direct_alignment_count", "must be a non-negative integer")
    if isinstance(value.get("candidate_reference_locations"), list):
        for index, candidate in enumerate(value["candidate_reference_locations"]):
            _validate_alignment_candidate(candidate, f"{path}.candidate_reference_locations[{index}]", result)
    _require_bool_value(value.get("requires_human_or_agent_review"), True, f"{path}.requires_human_or_agent_review", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_orientation_flags(value, path, result)


def _validate_alignment_candidate(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in (
        "reference_location_ref",
        "reference_location_status",
        "alignment_basis",
        "alignment_status",
        "chunk_id",
        "document_id",
    ):
        _require_nonempty_str(value, key, path, result)
    if value.get("alignment_status") != "candidate_alignment_requires_review":
        result.add(f"{path}.alignment_status", "must require review")
    _require_bool_value(value.get("exact_anchor_available"), True if value.get("reference_location_status") == "found" else False, f"{path}.exact_anchor_available", result)
    _require_bool_value(value.get("retrieval_is_claim_support"), False, f"{path}.retrieval_is_claim_support", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_orientation_flags(value, path, result)


def _validate_artifact_draft(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    if value.get("kind") != "corpus_backed_extraction_report_artifact":
        result.add(f"{path}.kind", "must be 'corpus_backed_extraction_report_artifact'")
    if value.get("status") != "draft_only":
        result.add(f"{path}.status", "must be 'draft_only'")
    if value.get("artifact_role") != "literature_extraction_orientation":
        result.add(f"{path}.artifact_role", "must be 'literature_extraction_orientation'")
    for key in (
        "artifact_record_created_now",
        "creates_record_now",
        "records_validation_result",
        "source_support_result",
        "summary_inputs_trusted",
    ):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    _require_list(value.get("required_inputs"), f"{path}.required_inputs", result)
    _require_list(value.get("sections"), f"{path}.sections", result)
    if isinstance(value.get("sections"), list):
        for index, section in enumerate(value["sections"]):
            _validate_artifact_section(section, f"{path}.sections[{index}]", result)


def _validate_artifact_section(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("section_id", "purpose"):
        _require_nonempty_str(value, key, path, result)
    for key in ("creates_record_now", "records_validation_result", "source_support_result", "summary_inputs_trusted"):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_downstream_call(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    expected = {
        "entrypoint": "build_literature_extraction_report",
        "mcp": "aitp_v5_build_literature_extraction_report",
        "cli": "aitp-v5 literature extraction-report <args>",
        "surface": "literature_extraction_report",
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            result.add(f"{path}.{key}", f"must be {expected_value!r}")
    for key in ("session_id", "report_profile"):
        _require_nonempty_str(value, key, path, result)
    _require_list(value.get("source_refs"), f"{path}.source_refs", result)
    _require_list(value.get("focus_terms"), f"{path}.focus_terms", result)
    _require_bool_value(value.get("requires_explicit_next_action"), True, f"{path}.requires_explicit_next_action", result)
    _require_bool_value(value.get("records_validation_result"), False, f"{path}.records_validation_result", result)
    _require_orientation_flags(value, path, result)


def _validate_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_list(value.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(value.get("allowed_next_entrypoints"), f"{path}.allowed_next_entrypoints", result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    for key in (
        "requires_curated_rag_chunks",
        "requires_exact_reference_locations",
        "requires_explicit_next_entrypoint",
        "retrieval_requires_promotion_for_claim_support",
    ):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    if value.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
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
