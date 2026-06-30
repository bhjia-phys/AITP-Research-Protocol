"""Contracts for read-only note-outline compiler surfaces."""

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


def validate_note_outline(
    payload: dict[str, Any],
    *,
    path: str = "note_outline",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "note_outline":
        result.add(f"{path}.kind", "must be 'note_outline'")
    for key in ("outline_id", "topic_id", "session_id", "style"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("active_claim_id", ""), str):
        result.add(f"{path}.active_claim_id", "must be a string")
    for key in ("sections", "next_valid_actions", "required_record_policy"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("compile_summary"), f"{path}.compile_summary", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_mapping(payload.get("note_boundary"), f"{path}.note_boundary", result)
    for index, section in enumerate(payload.get("sections") or []):
        _validate_section(section, f"{path}.sections[{index}]", result)
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_note_outline(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_note_outline(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_section(section: Any, path: str, result: ContractResult) -> None:
    _require_mapping(section, path, result)
    if not isinstance(section, dict):
        return
    for key in ("section_id", "title", "purpose", "readiness_state", "trust_boundary"):
        _require_nonempty_str(section, key, path, result)
    if section.get("readiness_state") not in {"draftable", "needs_records"}:
        result.add(f"{path}.readiness_state", "must be 'draftable' or 'needs_records'")
    _require_mapping(section.get("record_refs"), f"{path}.record_refs", result)
    for key in (
        "source_refs",
        "evidence_refs",
        "claim_ids",
        "missing_requirements",
        "recommended_record_actions",
    ):
        _require_list(section.get(key), f"{path}.{key}", result)
    _require_bool_value(section.get("orientation_only"), True, f"{path}.orientation_only", result)
