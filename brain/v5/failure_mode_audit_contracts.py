"""Contracts for read-only failure-mode audit surfaces."""

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


def validate_failure_mode_audit(payload: dict[str, Any], *, path: str = "failure_mode_audit") -> ContractResult:
    """Validate a public, read-only failure-mode coverage audit payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    for key in (
        "ok",
        "kind",
        "claim_id",
        "topic_id",
        "truth_source",
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "active_uncertainty",
        "strongest_failure_mode",
        "coverage_status",
        "failure_mode_review_results",
        "recommended_actions",
    ):
        if key not in payload:
            result.add(f"{path}.{key}", "missing required failure-mode audit key")
    _require_bool_value(payload.get("ok"), True, f"{path}.ok", result)
    if payload.get("kind") != "failure_mode_audit":
        result.add(f"{path}.kind", "must be 'failure_mode_audit'")
    _require_nonempty_str(payload, "claim_id", path, result)
    _require_nonempty_str(payload, "topic_id", path, result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if payload.get("coverage_status") not in {"covered", "gap"}:
        result.add(f"{path}.coverage_status", "must be 'covered' or 'gap'")
    for key in (
        "validation_contract_ids",
        "promotion_packet_ids",
        "failure_mode_review_result_ids",
        "validation_contract_failure_modes",
        "promotion_packet_failure_modes",
        "reviewed_failure_modes",
        "failure_mode_review_results",
        "uncovered_claim_failure_modes",
        "uncovered_validation_failure_modes",
        "recommended_actions",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for index, item in enumerate(payload.get("failure_mode_review_results", [])):
        _validate_review_result_item(item, f"{path}.failure_mode_review_results[{index}]", result)
    return result


def require_valid_failure_mode_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a failure-mode audit payload or raise a contract error."""

    result = validate_failure_mode_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_review_result_item(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("result_id", "checkpoint_id", "status"):
        _require_nonempty_str(item, key, path, result)
    if item.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    for key in (
        "reviewed_failure_modes",
        "basis_refs",
        "evidence_refs",
        "validation_result_ids",
        "tool_run_ids",
        "reference_location_ids",
        "artifact_ids",
    ):
        _require_list(item.get(key), f"{path}.{key}", result)
    _require_bool_value(item.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(item.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
