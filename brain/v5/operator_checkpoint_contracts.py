"""Contracts for topic-local operator checkpoint records."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_nonempty_str,
)

_CHECKPOINT_KINDS = {
    "scope_ambiguity",
    "novelty_direction_choice",
    "benchmark_validation_route_choice",
    "resource_risk_limit_choice",
    "contradiction_adjudication_choice",
    "promotion_approval",
    "stop_continue_branch_redirect_decision",
}
_STATUSES = {"requested", "answered", "superseded", "cancelled"}


def validate_operator_checkpoint_record(payload: dict[str, Any], *, path: str = "operator_checkpoint_record") -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "operator_checkpoint":
        result.add(f"{path}.kind", "must be 'operator_checkpoint'")
    for key in ("checkpoint_id", "topic_id", "checkpoint_kind", "question", "requested_by", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("checkpoint_kind") not in _CHECKPOINT_KINDS:
        result.add(f"{path}.checkpoint_kind", f"must be one of {sorted(_CHECKPOINT_KINDS)}")
    if payload.get("status") not in _STATUSES:
        result.add(f"{path}.status", f"must be one of {sorted(_STATUSES)}")
    _require_list(payload.get("options"), f"{path}.options", result)
    if isinstance(payload.get("options"), list) and not payload["options"]:
        result.add(f"{path}.options", "must not be empty")
    _require_list(payload.get("source_refs"), f"{path}.source_refs", result)
    if payload.get("status") == "answered":
        _require_nonempty_str(payload, "selected_option", path, result)
        _require_nonempty_str(payload, "rationale", path, result)
        _require_nonempty_str(payload, "answered_by", path, result)
        if isinstance(payload.get("options"), list) and payload.get("selected_option") not in payload["options"]:
            result.add(f"{path}.selected_option", "must be one of options")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_operator_checkpoint_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_operator_checkpoint_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
