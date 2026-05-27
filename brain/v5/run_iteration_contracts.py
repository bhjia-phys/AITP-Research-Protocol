"""Contracts for run-local iteration continuity records."""

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


def validate_run_iteration_record(payload: dict[str, Any], *, path: str = "run_iteration_record") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "run_iteration":
        result.add(f"{path}.kind", "must be 'run_iteration'")
    for key in ("topic_id", "run_id", "iteration_id", "plan_summary", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("deliverables", "checks", "stop_rules", "l4_artifact_refs", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("files"), f"{path}.files", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_run_iteration_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_run_iteration_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
