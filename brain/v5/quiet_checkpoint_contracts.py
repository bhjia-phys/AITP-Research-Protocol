"""Contracts for quiet research checkpoint preview/apply surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


def validate_quiet_checkpoint_preview(
    payload: dict[str, Any],
    *,
    path: str = "quiet_checkpoint_preview",
) -> ContractResult:
    result = _validate_common(payload, path=path, kind="quiet_checkpoint_preview")
    if not isinstance(payload, dict):
        return result
    if payload.get("status") != "preview_only":
        result.add(f"{path}.status", "must be 'preview_only'")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_quiet_checkpoint_preview(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_quiet_checkpoint_preview(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_quiet_checkpoint_batch(
    payload: dict[str, Any],
    *,
    path: str = "quiet_checkpoint_batch",
) -> ContractResult:
    result = _validate_common(payload, path=path, kind="quiet_checkpoint_batch")
    if not isinstance(payload, dict):
        return result
    if payload.get("status") != "recorded_without_trust_promotion":
        result.add(f"{path}.status", "must be 'recorded_without_trust_promotion'")
    _require_list(payload.get("written_refs"), f"{path}.written_refs", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_quiet_checkpoint_batch(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_quiet_checkpoint_batch(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_common(payload: Any, *, path: str, kind: str) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    for key in ("checkpoint_id", "topic_id", "session_id", "claim_id", "run_id", "summary"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "inputs",
        "outputs",
        "changed_files",
        "generated_artifacts",
        "validation_commands",
        "durable_observations",
        "next_blockers",
        "planned_typed_writes",
        "source_refs",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("claim_boundary"), f"{path}.claim_boundary", result)
    _validate_record_completeness_audit(payload.get("record_completeness_audit"), f"{path}.record_completeness_audit", result)
    return result


def _validate_record_completeness_audit(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "record_completeness_audit":
        result.add(f"{path}.kind", "must be 'record_completeness_audit'")
    for key in (
        "recorded_slots",
        "planned_slots",
        "missing_recommended_slots",
        "recommended_next_records",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("trust_boundary"), f"{path}.trust_boundary", result)
    for key in (
        "recording_complete",
        "requires_user_confirmation",
        "orientation_only",
        "summary_inputs_trusted",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be boolean")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
