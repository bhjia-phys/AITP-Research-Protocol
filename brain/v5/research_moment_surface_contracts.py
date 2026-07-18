"""Public contract for the explicit Research Moment process surface."""

from __future__ import annotations

from typing import Any, Callable

from brain.v5.contracts import ContractError, ContractResult
from brain.v5.research_moment_contracts import RESEARCH_MOMENT_OUTCOMES, STATE_EFFECTS


_SURFACE = "research_moment_process_result"


def research_moment_surface_names() -> tuple[str, ...]:
    return (_SURFACE,)


def research_moment_surface_purposes() -> dict[str, str]:
    return {
        _SURFACE: (
            "bounded decision and optional application receipt for one explicit "
            "host-neutral research event"
        )
    }


def research_moment_surface_validators() -> dict[
    str, Callable[[dict[str, Any]], dict[str, Any]]
]:
    return {_SURFACE: require_valid_research_moment_process_result}


def validate_research_moment_process_result(
    payload: dict[str, Any],
    *,
    path: str = _SURFACE,
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != _SURFACE:
        result.add(f"{path}.kind", f"must be {_SURFACE!r}")
    applied = payload.get("applied")
    if not isinstance(applied, bool):
        result.add(f"{path}.applied", "must be a boolean")
    if payload.get("state_effect") not in STATE_EFFECTS:
        result.add(f"{path}.state_effect", "must be a supported state effect")
    if payload.get("trust_effect") != "none":
        result.add(f"{path}.trust_effect", "must be none")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _validate_decision(payload.get("decision"), f"{path}.decision", result)
    receipt = payload.get("receipt")
    if applied is True:
        _validate_receipt(receipt, f"{path}.receipt", result)
        _validate_applied_effects(payload, path, result)
    elif receipt is not None:
        result.add(f"{path}.receipt", "must be null when applied is false")
    if applied is False and payload.get("state_effect") != "read_only":
        result.add(f"{path}.state_effect", "must be read_only when applied is false")
    return result


def require_valid_research_moment_process_result(
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = validate_research_moment_process_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_decision(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for field in (
        "decision_id",
        "event",
        "outcome",
        "reason_codes",
        "dedup_key",
        "expires_at",
        "declared_effect",
        "trust_effect",
        "can_update_claim_trust",
    ):
        if field not in payload:
            result.add(f"{path}.{field}", "is required")
    if payload.get("outcome") not in RESEARCH_MOMENT_OUTCOMES:
        result.add(f"{path}.outcome", "must be a bounded research moment outcome")
    if payload.get("declared_effect") not in STATE_EFFECTS:
        result.add(f"{path}.declared_effect", "must be a supported state effect")
    if payload.get("trust_effect") != "none":
        result.add(f"{path}.trust_effect", "must be none")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    event = payload.get("event")
    if not isinstance(event, dict):
        result.add(f"{path}.event", "must be a mapping")
    else:
        for field in ("event_id", "event_type", "session_id", "topic_id"):
            if not isinstance(event.get(field), str) or not event[field]:
                result.add(f"{path}.event.{field}", "must be a non-empty string")


def _validate_receipt(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping when applied is true")
        return
    for field in (
        "receipt_id",
        "decision_id",
        "event_id",
        "outcome",
        "status",
        "application_effect",
        "trust_effect",
        "can_update_claim_trust",
    ):
        if field not in payload:
            result.add(f"{path}.{field}", "is required")
    if payload.get("outcome") not in RESEARCH_MOMENT_OUTCOMES:
        result.add(f"{path}.outcome", "must be a bounded research moment outcome")
    if payload.get("application_effect") not in STATE_EFFECTS:
        result.add(f"{path}.application_effect", "must be a supported state effect")
    if payload.get("trust_effect") != "none":
        result.add(f"{path}.trust_effect", "must be none")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_applied_effects(
    payload: dict[str, Any], path: str, result: ContractResult
) -> None:
    decision = payload.get("decision")
    receipt = payload.get("receipt")
    if not isinstance(decision, dict) or not isinstance(receipt, dict):
        return
    expected_effect = decision.get("declared_effect")
    if payload.get("state_effect") != expected_effect:
        result.add(
            f"{path}.state_effect",
            "must equal the applied decision declared_effect",
        )
    if receipt.get("application_effect") != expected_effect:
        result.add(
            f"{path}.receipt.application_effect",
            "must equal the applied decision declared_effect",
        )
    for field in ("decision_id", "outcome"):
        if receipt.get(field) != decision.get(field):
            result.add(
                f"{path}.receipt.{field}",
                f"must equal decision.{field}",
            )
    event = decision.get("event")
    if isinstance(event, dict) and receipt.get("event_id") != event.get("event_id"):
        result.add(
            f"{path}.receipt.event_id",
            "must equal decision.event.event_id",
        )


__all__ = [
    "require_valid_research_moment_process_result",
    "research_moment_surface_names",
    "research_moment_surface_purposes",
    "research_moment_surface_validators",
    "validate_research_moment_process_result",
]
