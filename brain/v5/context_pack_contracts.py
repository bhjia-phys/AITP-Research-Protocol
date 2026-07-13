"""Contracts for Codex-facing AITP context packs."""

from __future__ import annotations

from typing import Any

from brain.v5.context_compiler import estimate_context_tokens
from brain.v5.context_selection import NOT_SHOWN_REASON_CODES
from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


def validate_aitp_context_pack(payload: dict[str, Any], *, path: str = "aitp_context_pack") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "aitp_context_pack":
        result.add(f"{path}.kind", "must be 'aitp_context_pack'")
    for key in ("context_pack_version", "designed_for_host", "session_id", "topic_id", "fingerprint", "pack_id", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("designed_for_host") != "codex":
        result.add(f"{path}.designed_for_host", "must be 'codex'")
    _require_mapping(payload.get("current_objective"), f"{path}.current_objective", result)
    _require_mapping(payload.get("active_work_package"), f"{path}.active_work_package", result)
    for key in (
        "relevant_claims",
        "can_say",
        "cannot_say",
        "blockers",
        "next_valid_actions",
        "recent_relevant_artifacts",
        "context_lines",
        "read_errors",
        "not_found_refs",
        "not_checked_families",
        "not_shown_reason",
        "warnings",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_nonempty_str(payload, "relation_map_scope", path, result)
    if payload.get("relation_map_scope") != "active_claim_only":
        result.add(f"{path}.relation_map_scope", "must be active_claim_only")
    if not isinstance(payload.get("not_authoritative_for_current_goal_if_rebind_needed"), bool):
        result.add(f"{path}.not_authoritative_for_current_goal_if_rebind_needed", "must be a boolean")
    if not isinstance(payload.get("requested_task_profile"), str):
        result.add(f"{path}.requested_task_profile", "must be a string")
    _require_mapping(payload.get("task_profile"), f"{path}.task_profile", result)
    _require_mapping(payload.get("profile_template_hint"), f"{path}.profile_template_hint", result)
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    if isinstance(payload.get("context_lines"), list) and len(payload["context_lines"]) > 80:
        result.add(f"{path}.context_lines", "must be at most 80 lines")
    _require_mapping(payload.get("distillation_status"), f"{path}.distillation_status", result)
    _require_mapping(payload.get("materialization_boundary"), f"{path}.materialization_boundary", result)
    _require_mapping(payload.get("injection_policy"), f"{path}.injection_policy", result)
    _require_mapping(payload.get("expand"), f"{path}.expand", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_mapping(payload.get("retrieval_coverage"), f"{path}.retrieval_coverage", result)
    _require_mapping(payload.get("context_budget"), f"{path}.context_budget", result)
    _require_list(payload.get("record_refs"), f"{path}.record_refs", result)
    _validate_compiled_budget(payload, path, result)
    _validate_retrieval_coverage(payload, path, result)
    _validate_recall_selection(payload, path, result)
    _validate_distillation_status(payload.get("distillation_status"), f"{path}.distillation_status", result)
    _validate_task_profile(payload.get("task_profile"), f"{path}.task_profile", result)
    _validate_profile_template_hint(payload.get("profile_template_hint"), f"{path}.profile_template_hint", result)
    _validate_injection_policy(payload.get("injection_policy"), f"{path}.injection_policy", result)
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("can_materialize_without_human_review", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    boundary = payload.get("materialization_boundary")
    if isinstance(boundary, dict):
        for key in ("can_create_skill", "can_create_l2_memory", "can_update_claim_trust"):
            _require_bool_value(boundary.get(key), False, f"{path}.materialization_boundary.{key}", result)
        _require_bool_value(
            boundary.get("requires_human_review_before_materialization"),
            True,
            f"{path}.materialization_boundary.requires_human_review_before_materialization",
            result,
        )
    return result


def _validate_compiled_budget(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    markdown = payload.get("markdown")
    byte_count = payload.get("byte_count")
    token_count = payload.get("estimated_tokens")
    budget = payload.get("context_budget")
    if not isinstance(markdown, str):
        result.add(f"{path}.markdown", "must be a string")
        return
    actual_bytes = len(markdown.encode("utf-8"))
    actual_tokens = estimate_context_tokens(markdown)
    if byte_count != actual_bytes:
        result.add(f"{path}.byte_count", "must match markdown UTF-8 bytes")
    if token_count != actual_tokens:
        result.add(f"{path}.estimated_tokens", "must match deterministic token estimate")
    if not isinstance(budget, dict):
        return
    max_bytes = budget.get("max_bytes")
    max_tokens = budget.get("max_tokens")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        result.add(f"{path}.context_budget.max_bytes", "must be a positive integer")
    elif actual_bytes > max_bytes:
        result.add(f"{path}.byte_count", "must not exceed context_budget.max_bytes")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 1:
        result.add(f"{path}.context_budget.max_tokens", "must be a positive integer")
    elif actual_tokens > max_tokens:
        result.add(f"{path}.estimated_tokens", "must not exceed context_budget.max_tokens")


def _validate_retrieval_coverage(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    coverage = payload.get("retrieval_coverage")
    if not isinstance(coverage, dict):
        return
    for key in (
        "exhaustive",
        "can_claim_no_result",
        "checked_families",
        "unchecked_families",
        "malformed_count",
        "reason",
    ):
        if key not in coverage:
            result.add(f"{path}.retrieval_coverage.{key}", "is required")
    index_status = payload.get("index_status")
    if index_status not in {"fresh", "stale"}:
        result.add(f"{path}.index_status", "must be fresh or stale")
    generation = payload.get("source_index_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        result.add(f"{path}.source_index_generation", "must be a positive integer")
    if index_status == "stale" and coverage.get("exhaustive"):
        result.add(f"{path}.retrieval_coverage.exhaustive", "must be false for a stale index")
    if (coverage.get("malformed_count") or payload.get("read_errors")) and coverage.get("can_claim_no_result"):
        result.add(
            f"{path}.retrieval_coverage.can_claim_no_result",
            "must be false when reads are partial",
        )


def _validate_recall_selection(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    count = payload.get("not_shown_count")
    reasons = payload.get("not_shown_reason")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        result.add(f"{path}.not_shown_count", "must be a non-negative integer")
    if isinstance(reasons, list):
        unknown = set(reasons) - set(NOT_SHOWN_REASON_CODES)
        if unknown:
            result.add(f"{path}.not_shown_reason", f"contains unknown codes: {sorted(unknown)}")
        if count == 0 and reasons:
            result.add(f"{path}.not_shown_reason", "must be empty when count is zero")
        if isinstance(count, int) and count > 0 and not reasons:
            result.add(f"{path}.not_shown_reason", "is required when candidates are omitted")
    for key in ("partial", "retrieval_truncated", "render_truncated", "truncated"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if isinstance(payload.get("truncated"), bool) and payload.get("truncated") != bool(
        payload.get("retrieval_truncated") or payload.get("render_truncated")
    ):
        result.add(
            f"{path}.truncated",
            "must combine retrieval_truncated and render_truncated",
        )
    partial_signal = bool(
        payload.get("index_status") != "fresh"
        or payload.get("not_found_refs")
        or payload.get("not_checked_families")
        or payload.get("read_errors")
        or payload.get("truncated")
        or (isinstance(count, int) and count > 0)
    )
    if partial_signal and payload.get("partial") is not True:
        result.add(f"{path}.partial", "must be true when recall or selection is partial")


def require_valid_aitp_context_pack(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_aitp_context_pack(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_distillation_status(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        return
    _require_mapping(payload.get("summary"), f"{path}.summary", result)
    for key in ("top_candidates", "gate_policy", "next_valid_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for index, candidate in enumerate(payload.get("top_candidates") or []):
        _require_mapping(candidate, f"{path}.top_candidates[{index}]", result)
        if not isinstance(candidate, dict):
            continue
        for key in ("candidate_id", "candidate_kind", "distillation_state", "trust_boundary"):
            _require_nonempty_str(candidate, key, f"{path}.top_candidates[{index}]", result)
        for key in ("family", "status"):
            _require_nonempty_str(candidate, key, f"{path}.top_candidates[{index}]", result)
        for key in ("retrieval_rank", "retrieval_score", "exact_score", "lexical_score"):
            value = candidate.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                result.add(
                    f"{path}.top_candidates[{index}].{key}",
                    "must be a non-negative integer",
                )
        for key, expected in (
            ("can_materialize_without_human_review", False),
            ("can_promote_claim_trust", False),
            ("orientation_only", True),
        ):
            _require_bool_value(candidate.get(key), expected, f"{path}.top_candidates[{index}].{key}", result)
        if not isinstance(candidate.get("can_draft_reusable_block"), bool):
            result.add(f"{path}.top_candidates[{index}].can_draft_reusable_block", "must be a boolean")
        _require_list(candidate.get("missing_requirements"), f"{path}.top_candidates[{index}].missing_requirements", result)
        _require_mapping(candidate.get("source_records"), f"{path}.top_candidates[{index}].source_records", result)


def _validate_task_profile(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict) or not payload:
        return
    for key in ("kind", "profile_id", "task_type", "purpose"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "context_compilation_profile":
        result.add(f"{path}.kind", "must be 'context_compilation_profile'")
    for key in (
        "include_sections",
        "can_say",
        "cannot_say",
        "must_verify",
        "reusable_experience",
        "recommended_surfaces",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("truth_policy"), f"{path}.truth_policy", result)
    if isinstance(payload.get("truth_policy"), dict):
        for key, expected in (
            ("orientation_only", True),
            ("summary_inputs_trusted", False),
            ("can_update_kernel_state", False),
            ("can_update_claim_trust", False),
            ("requires_typed_followup_for_claim_support", True),
        ):
            _require_bool_value(payload["truth_policy"].get(key), expected, f"{path}.truth_policy.{key}", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)


def _validate_profile_template_hint(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict) or not payload:
        return
    if payload.get("kind") != "context_profile_template_hint":
        result.add(f"{path}.kind", "must be 'context_profile_template_hint'")
    for key in ("profile_id", "template_id", "template_family", "output_shape", "template_catalog_entrypoint"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "required_section_ids",
        "report_section_order",
        "closeout_section_order",
        "must_verify_before_trust_or_promotion",
        "read_only_surfaces_to_expand",
        "recommended_next_entrypoints",
        "forbidden_uses",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in (
        "required_section_ids",
        "must_verify_before_trust_or_promotion",
        "read_only_surfaces_to_expand",
        "recommended_next_entrypoints",
        "forbidden_uses",
    ):
        if isinstance(payload.get(key), list) and not payload[key]:
            result.add(f"{path}.{key}", "must not be empty")
    _require_mapping(payload.get("trust_boundary"), f"{path}.trust_boundary", result)
    if isinstance(payload.get("trust_boundary"), dict):
        boundary = payload["trust_boundary"]
        for key, expected in (
            ("summary_inputs_trusted", False),
            ("requires_typed_followup_for_claim_support", True),
            ("requires_passed_validation_for_tool_derived_support", True),
        ):
            _require_bool_value(boundary.get(key), expected, f"{path}.trust_boundary.{key}", result)
        if not isinstance(boundary.get("requires_exact_source_anchors_for_literature_support"), bool):
            result.add(
                f"{path}.trust_boundary.requires_exact_source_anchors_for_literature_support",
                "must be a boolean",
            )
        if boundary.get("claim_trust_mutation") != "none":
            result.add(f"{path}.trust_boundary.claim_trust_mutation", "must be 'none'")
    for key, expected in (
        ("read_only", True),
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("records_validation_result", False),
        ("source_support_result", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    forbidden_uses = payload.get("forbidden_uses") if isinstance(payload.get("forbidden_uses"), list) else []
    for forbidden in (
        "profile_report_as_evidence",
        "profile_closeout_as_evidence",
        "validation_result",
        "final_gate_satisfaction",
        "claim_trust_update",
        "trust_apply",
    ):
        if forbidden not in forbidden_uses:
            result.add(f"{path}.forbidden_uses", f"must include {forbidden!r}")


def _validate_injection_policy(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        return
    for key in ("host", "recommended_hook", "recommended_authority"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("host") != "codex":
        result.add(f"{path}.host", "must be 'codex'")
    for key in ("inject_when", "avoid_reinjecting_when", "requires_explicit_expand_for"):
        _require_list(payload.get(key), f"{path}.{key}", result)
