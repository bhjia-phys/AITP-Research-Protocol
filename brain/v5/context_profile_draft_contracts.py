"""Contracts for read-only context profile report and closeout drafts."""

from __future__ import annotations

from typing import Any

from brain.v5.context_profile_drafts import SUPPORTED_DRAFT_PROFILES
from brain.v5.context_profile_templates import FORBIDDEN_USES
from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


def validate_context_profile_draft(
    payload: dict[str, Any],
    *,
    path: str = "context_profile_draft",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "context_profile_draft":
        result.add(f"{path}.kind", "must be 'context_profile_draft'")
    for key in (
        "draft_version",
        "requested_profile_id",
        "profile_id",
        "draft_kind",
        "session_id",
        "topic_id",
        "context_pack_id",
        "context_pack_fingerprint",
        "markdown",
        "read_surface_effect",
        "truth_source",
    ):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("profile_id") not in SUPPORTED_DRAFT_PROFILES:
        result.add(f"{path}.profile_id", "must be a supported draft profile")
    if payload.get("draft_kind") not in {"group_meeting_report_draft", "closeout_draft"}:
        result.add(f"{path}.draft_kind", "must be a known draft kind")
    if payload.get("read_surface_effect") != "context_profile_draft_only":
        result.add(f"{path}.read_surface_effect", "must be 'context_profile_draft_only'")
    if not isinstance(payload.get("context_pack_line_count"), int) or payload["context_pack_line_count"] < 0:
        result.add(f"{path}.context_pack_line_count", "must be a non-negative integer")
    _require_mapping(payload.get("profile_template_hint"), f"{path}.profile_template_hint", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_mapping(payload.get("draft_policy"), f"{path}.draft_policy", result)
    _require_list(payload.get("sections"), f"{path}.sections", result)
    _require_list(payload.get("missing_section_ids"), f"{path}.missing_section_ids", result)
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    if isinstance(payload.get("sections"), list):
        if payload.get("section_count") != len(payload["sections"]):
            result.add(f"{path}.section_count", "must equal sections length")
        if not payload["sections"]:
            result.add(f"{path}.sections", "must not be empty")
        for index, section in enumerate(payload["sections"]):
            _validate_section(section, f"{path}.sections[{index}]", result)
    _validate_policy(payload.get("draft_policy"), f"{path}.draft_policy", result)
    _require_top_level_flags(payload, path, result)
    return result


def require_valid_context_profile_draft(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_context_profile_draft(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_section(section: Any, path: str, result: ContractResult) -> None:
    _require_mapping(section, path, result)
    if not isinstance(section, dict):
        return
    for key in ("section_id", "heading", "coverage_status"):
        _require_nonempty_str(section, key, path, result)
    if section.get("coverage_status") not in {"filled_from_context_pack", "missing_context"}:
        result.add(f"{path}.coverage_status", "must be filled_from_context_pack or missing_context")
    for key in ("draft_items", "source_fields", "missing_inputs"):
        _require_list(section.get(key), f"{path}.{key}", result)
    if isinstance(section.get("draft_items"), list) and section.get("item_count") != len(section["draft_items"]):
        result.add(f"{path}.item_count", "must equal draft_items length")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("source_support_result", False),
        ("records_validation_result", False),
    ):
        _require_bool_value(section.get(key), expected, f"{path}.{key}", result)
    if section.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_policy(policy: Any, path: str, result: ContractResult) -> None:
    if not isinstance(policy, dict):
        return
    _require_list(policy.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(policy.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_bool_value(
        policy.get("requires_runtime_context_pack_before_final_answer"),
        True,
        f"{path}.requires_runtime_context_pack_before_final_answer",
        result,
    )
    _require_bool_value(policy.get("requires_explicit_next_entrypoint"), True, f"{path}.requires_explicit_next_entrypoint", result)
    for key in ("records_validation_result", "source_support_result", "summary_inputs_trusted", "can_update_claim_trust"):
        _require_bool_value(policy.get(key), False, f"{path}.{key}", result)
    if policy.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    forbidden_uses = policy.get("forbidden_uses") if isinstance(policy.get("forbidden_uses"), list) else []
    for forbidden in FORBIDDEN_USES:
        if forbidden not in forbidden_uses:
            result.add(f"{path}.forbidden_uses", f"must include {forbidden!r}")


def _require_top_level_flags(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    for key in (
        "draft_creates_records",
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "write_executed",
    ):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)
    for key in ("read_only", "requires_explicit_next_action", "orientation_only", "trust_update_forbidden"):
        _require_bool_value(payload.get(key), True, f"{path}.{key}", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
