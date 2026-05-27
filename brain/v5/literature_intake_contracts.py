"""Contracts for literature intake assistant surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str

_ACTIONS = {
    "record_reference_only",
    "record_reference_plus_sensemaking",
    "record_reference_plus_evidence_candidate",
    "needs_human_review",
}
_EVIDENCE_STATUSES = {"supports", "contradicts", "mixed", "inconclusive"}


def validate_literature_intake_suggestion(
    payload: dict[str, Any], *, path: str = "literature_intake_suggestion"
) -> ContractResult:
    result = ContractResult()
    _require_common(payload, path, result, kind="literature_intake_suggestion")
    if not isinstance(payload, dict):
        return result
    _require_nonempty_str(payload, "recommended_action", path, result)
    if payload.get("recommended_action") not in _ACTIONS:
        result.add(f"{path}.recommended_action", f"must be one of {sorted(_ACTIONS)}")
    _validate_reference_candidate(payload.get("reference_candidate"), f"{path}.reference_candidate", result)
    _require_mapping(payload.get("mcp_templates"), f"{path}.mcp_templates", result)
    _require_list(payload.get("cli_templates"), f"{path}.cli_templates", result)
    _require_list(payload.get("risk_notes"), f"{path}.risk_notes", result)
    _require_list(payload.get("guarded_next_steps"), f"{path}.guarded_next_steps", result)
    _require_list(payload.get("forbidden_without_preflight"), f"{path}.forbidden_without_preflight", result)
    _validate_optional_evidence_candidate(payload.get("evidence_candidate"), f"{path}.evidence_candidate", result)
    _validate_optional_sensemaking_candidate(payload.get("sensemaking_candidate"), f"{path}.sensemaking_candidate", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    return result


def require_valid_literature_intake_suggestion(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_intake_suggestion(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_literature_intake_record_result(
    payload: dict[str, Any], *, path: str = "literature_intake_record_result"
) -> ContractResult:
    result = ContractResult()
    _require_common(payload, path, result, kind="literature_intake_record_result")
    if not isinstance(payload, dict):
        return result
    _require_nonempty_str(payload, "recommended_action", path, result)
    _require_mapping(payload.get("recorded_reference_location"), f"{path}.recorded_reference_location", result)
    _require_list(payload.get("guarded_next_steps"), f"{path}.guarded_next_steps", result)
    _require_bool_value(payload.get("evidence_written"), False, f"{path}.evidence_written", result)
    _require_bool_value(payload.get("sensemaking_written"), False, f"{path}.sensemaking_written", result)
    _require_bool_value(payload.get("can_update_kernel_state"), True, f"{path}.can_update_kernel_state", result)
    if payload.get("kernel_state_change") != "reference_location_record_only":
        result.add(f"{path}.kernel_state_change", "must be reference_location_record_only")
    ref = payload.get("recorded_reference_location")
    if isinstance(ref, dict) and ref.get("orientation_only") is not True:
        result.add(f"{path}.recorded_reference_location.orientation_only", "must be true")
    return result


def require_valid_literature_intake_record_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_intake_record_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _require_common(payload: Any, path: str, result: ContractResult, *, kind: str) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    for key in ("session_id", "topic_id", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    _require_bool_value(payload.get("trust_update_forbidden"), True, f"{path}.trust_update_forbidden", result)
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_reference_candidate(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("topic_id", "connector_id", "location_type", "uri", "label", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if value.get("status") != "candidate":
        result.add(f"{path}.status", "must be candidate")
    for key in ("metadata", "linked_records"):
        _require_mapping(value.get(key), f"{path}.{key}", result)


def _validate_optional_sensemaking_candidate(value: Any, path: str, result: ContractResult) -> None:
    if value == {}:
        return
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("topic_id", "claim_id", "title", "summary", "validation_status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("validation_status") != "not_validation":
        result.add(f"{path}.validation_status", "must be not_validation")
    for key in ("open_questions", "next_actions"):
        _require_list(value.get(key), f"{path}.{key}", result)


def _validate_optional_evidence_candidate(value: Any, path: str, result: ContractResult) -> None:
    if value == {}:
        return
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("topic_id", "claim_id", "evidence_type", "status", "summary", "reference_location_id", "scope_note"):
        _require_nonempty_str(value, key, path, result)
    if value.get("status") not in _EVIDENCE_STATUSES:
        result.add(f"{path}.status", f"must be one of {sorted(_EVIDENCE_STATUSES)}")
    for key in ("supports_outputs", "source_refs"):
        _require_list(value.get(key), f"{path}.{key}", result)
    if not value.get("supports_outputs"):
        result.add(f"{path}.supports_outputs", "must name the scoped output before evidence is recorded")
