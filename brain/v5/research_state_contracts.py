"""Contracts for conservative research-state public surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping, _require_nonempty_str
from brain.v5.record_contracts import (
    validate_artifact_record,
    validate_claim_status_record,
    validate_evidence_record,
    validate_tool_run_record,
)


def validate_research_event_classification(
    payload: dict[str, Any],
    *,
    path: str = "research_event_classification",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "research_event_classification":
        result.add(f"{path}.kind", "must be 'research_event_classification'")
    for key in ("topic_id", "event_kind", "event_summary", "recommended_action"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("candidate_record_types", "risk_notes"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("needs_claim_binding", "needs_human_gate", "trust_update_forbidden", "summary_inputs_trusted", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("trust_update_forbidden") is not True:
        result.add(f"{path}.trust_update_forbidden", "must be true")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_research_event_classification(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_research_event_classification(payload), payload)


def validate_bounded_numerical_evidence_bundle(
    payload: dict[str, Any],
    *,
    path: str = "bounded_numerical_evidence_bundle",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "bounded_numerical_evidence_bundle":
        result.add(f"{path}.kind", "must be 'bounded_numerical_evidence_bundle'")
    for key in ("topic_id", "claim_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("artifact", "tool_run", "evidence", "claim_status", "classification", "component_ids"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    _require_list(payload.get("supports_outputs"), f"{path}.supports_outputs", result)
    if isinstance(payload.get("supports_outputs"), list) and not payload["supports_outputs"]:
        result.add(f"{path}.supports_outputs", "must not be empty")
    if isinstance(payload.get("artifact"), dict):
        result.extend(validate_artifact_record({"ok": True, **payload["artifact"]}, path=f"{path}.artifact"))
    if isinstance(payload.get("tool_run"), dict):
        result.extend(validate_tool_run_record({"ok": True, **payload["tool_run"]}, path=f"{path}.tool_run"))
    if isinstance(payload.get("evidence"), dict):
        result.extend(validate_evidence_record({"ok": True, **payload["evidence"]}, path=f"{path}.evidence"))
    if isinstance(payload.get("claim_status"), dict):
        result.extend(validate_claim_status_record({"ok": True, **payload["claim_status"]}, path=f"{path}.claim_status"))
    if isinstance(payload.get("classification"), dict):
        result.extend(validate_research_event_classification(payload["classification"], path=f"{path}.classification"))
    if payload.get("human_gate_required") is not True:
        result.add(f"{path}.human_gate_required", "must be true")
    if payload.get("trust_update_forbidden") is not True:
        result.add(f"{path}.trust_update_forbidden", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    return result


def require_valid_bounded_numerical_evidence_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_bounded_numerical_evidence_bundle(payload), payload)


def _require_valid(result: ContractResult, payload: dict[str, Any]) -> dict[str, Any]:
    if not result.ok:
        raise ContractError(result)
    return payload
