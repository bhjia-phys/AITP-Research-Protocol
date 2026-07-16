"""Contracts for trust-neutral Skill readiness reports."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import re
from typing import Any, Mapping

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OVERLAP_CLASSES = {"new", "extension_candidate", "duplicate", "conflict"}


def validate_skill_readiness_report(
    value: Any,
    *,
    path: str = "skill_readiness_report",
) -> ContractResult:
    payload = asdict(value) if is_dataclass(value) else value
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, Mapping):
        return result
    for key in (
        "report_id",
        "candidate_id",
        "candidate_signature",
        "status",
        "readiness_basis",
        "created_at",
        "kind",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "skill_readiness_report":
        result.add(f"{path}.kind", "must be 'skill_readiness_report'")
    if not _SHA256.fullmatch(str(payload.get("candidate_signature") or "")):
        result.add(f"{path}.candidate_signature", "must be lowercase sha256")
    if payload.get("status") not in {"ready", "blocked"}:
        result.add(f"{path}.status", "must be ready or blocked")
    count = payload.get("independent_use_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        result.add(f"{path}.independent_use_count", "must be a non-negative integer")
    for key in (
        "checked_execution_refs",
        "validation_fixture_refs",
        "blockers",
        "required_actions",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _validate_pin(payload.get("candidate_ref"), f"{path}.candidate_ref", result, required=True)
    _validate_pin(
        payload.get("expert_exception_ref"),
        f"{path}.expert_exception_ref",
        result,
        required=False,
    )
    _require_mapping(payload.get("failure_coverage"), f"{path}.failure_coverage", result)
    _require_mapping(payload.get("overlap"), f"{path}.overlap", result)
    overlap = payload.get("overlap")
    if isinstance(overlap, Mapping):
        if overlap.get("classification") not in _OVERLAP_CLASSES:
            result.add(f"{path}.overlap.classification", "must be a supported overlap class")
        _require_list(overlap.get("matches"), f"{path}.overlap.matches", result)
        _require_list(overlap.get("errors"), f"{path}.overlap.errors", result)
    for field, expected in (
        ("can_install_skill", False),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(field), expected, f"{path}.{field}", result)
    ready = payload.get("ready_for_package_preview")
    if not isinstance(ready, bool):
        result.add(f"{path}.ready_for_package_preview", "must be a boolean")
    if isinstance(ready, bool) and ready != (payload.get("status") == "ready"):
        result.add(f"{path}.ready_for_package_preview", "must match status")
    return result


def require_valid_skill_readiness_report(value: Any):
    result = validate_skill_readiness_report(value)
    if not result.ok:
        raise ContractError(result)
    return value


def _validate_pin(
    value: Any,
    path: str,
    result: ContractResult,
    *,
    required: bool,
) -> None:
    if not value and not required:
        return
    _require_mapping(value, path, result)
    if not isinstance(value, Mapping):
        return
    _require_nonempty_str(value, "record_ref", path, result)
    if not _SHA256.fullmatch(str(value.get("content_hash") or "")):
        result.add(f"{path}.content_hash", "must be lowercase sha256")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.revision", "must be a positive integer")
