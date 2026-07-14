"""Public payload contracts for the v5 research-session lifecycle."""

from __future__ import annotations

from functools import partial
from typing import Any, Callable

from brain.v5.contracts import ContractError, ContractResult


_RULES = {
    "session_start_boundary": (
        "read-only startup orientation compiled from indexed typed records",
        "session_start_boundary",
        ("session_id", "resume_card", "context_receipt", "write_executed"),
        "read_only",
    ),
    "recall_audit_result": (
        "canonical trust-neutral coverage audit for explicit deep recall",
        "recall_audit_result",
        ("audit_ref", "session_id", "checked_families", "write_executed"),
        "kernel_write",
    ),
    "recording_candidate_staging": (
        "runtime-only durable-moment candidate awaiting canonical review batching",
        "recording_candidate_staging",
        ("status", "state_effect", "write_executed"),
        "runtime_write",
    ),
    "recording_batch_handoff": (
        "canonical coalesced candidate batch requiring human review",
        "recording_batch_handoff",
        ("batch_ref", "review_status", "human_review_required"),
        "kernel_write",
    ),
    "session_closeout_plan": (
        "read-only hash-bound closeout plan requiring an explicit reviewed plan id",
        "session_closeout_plan",
        ("plan_id", "plan_fingerprint", "request", "record", "allowed"),
        "read_only",
    ),
    "session_closeout_apply": (
        "explicit canonical closeout result bound to a current reviewed plan",
        "session_closeout_apply",
        ("plan_id", "plan_fingerprint", "closeout_ref", "write_status"),
        "kernel_write",
    ),
}


def lifecycle_surface_names() -> tuple[str, ...]:
    return tuple(_RULES)


def lifecycle_surface_purposes() -> dict[str, str]:
    return {name: values[0] for name, values in _RULES.items()}


def lifecycle_surface_validators() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    return {
        name: partial(require_valid_lifecycle_surface, name)
        for name in lifecycle_surface_names()
    }


def require_valid_lifecycle_surface(
    surface_name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    result = ContractResult()
    rule = _RULES.get(surface_name)
    if rule is None:
        result.add(surface_name, "unknown lifecycle surface")
    elif not isinstance(payload, dict):
        result.add(surface_name, "must be a mapping")
    else:
        _purpose, kind, required, state_effect = rule
        if payload.get("kind") != kind:
            result.add(f"{surface_name}.kind", f"must be {kind!r}")
        for field in required:
            if field not in payload:
                result.add(f"{surface_name}.{field}", "is required")
        if payload.get("state_effect") != state_effect:
            result.add(
                f"{surface_name}.state_effect",
                f"must be {state_effect!r}",
            )
        if payload.get("can_update_claim_trust") is not False:
            result.add(f"{surface_name}.can_update_claim_trust", "must be false")
        if payload.get("summary_inputs_trusted") is not False:
            result.add(f"{surface_name}.summary_inputs_trusted", "must be false")
    if not result.ok:
        raise ContractError(result)
    return payload
