"""Contracts for Codex-facing AITP context packs."""

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
        "warnings",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_nonempty_str(payload, "relation_map_scope", path, result)
    if payload.get("relation_map_scope") != "active_claim_only":
        result.add(f"{path}.relation_map_scope", "must be active_claim_only")
    if not isinstance(payload.get("not_authoritative_for_current_goal_if_rebind_needed"), bool):
        result.add(f"{path}.not_authoritative_for_current_goal_if_rebind_needed", "must be a boolean")
    _require_mapping(payload.get("active_claim_focus_reconciliation"), f"{path}.active_claim_focus_reconciliation", result)
    if isinstance(payload.get("context_lines"), list) and len(payload["context_lines"]) > 80:
        result.add(f"{path}.context_lines", "must be at most 80 lines")
    _require_mapping(payload.get("distillation_status"), f"{path}.distillation_status", result)
    _require_mapping(payload.get("materialization_boundary"), f"{path}.materialization_boundary", result)
    _require_mapping(payload.get("injection_policy"), f"{path}.injection_policy", result)
    _require_mapping(payload.get("expand"), f"{path}.expand", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _validate_distillation_status(payload.get("distillation_status"), f"{path}.distillation_status", result)
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


def _validate_injection_policy(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        return
    for key in ("host", "recommended_hook", "recommended_authority"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("host") != "codex":
        result.add(f"{path}.host", "must be 'codex'")
    for key in ("inject_when", "avoid_reinjecting_when", "requires_explicit_expand_for"):
        _require_list(payload.get(key), f"{path}.{key}", result)
