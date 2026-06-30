"""Contracts for research distillation candidate surfaces."""

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

_CANDIDATE_KINDS = {
    "workflow_recipe_candidate",
    "physics_semantic_fragment_candidate",
    "method_capsule_candidate",
    "failure_playbook_candidate",
    "handoff_profile_candidate",
}


def validate_research_distillation_candidates(
    payload: dict[str, Any],
    *,
    path: str = "research_distillation_candidates",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "research_distillation_candidates":
        result.add(f"{path}.kind", "must be 'research_distillation_candidates'")
    for key in ("topic_id", "session_id"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("candidates", "gate_policy", "next_valid_actions", "read_errors"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("summary"), f"{path}.summary", result)
    _require_mapping(payload.get("source_records"), f"{path}.source_records", result)
    _require_mapping(payload.get("distillation_boundary"), f"{path}.distillation_boundary", result)
    for index, candidate in enumerate(payload.get("candidates") or []):
        _validate_candidate(candidate, f"{path}.candidates[{index}]", result)
    for key, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    return result


def require_valid_research_distillation_candidates(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_research_distillation_candidates(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_candidate(candidate: Any, path: str, result: ContractResult) -> None:
    _require_mapping(candidate, path, result)
    if not isinstance(candidate, dict):
        return
    for key in ("candidate_id", "candidate_kind", "title", "distillation_state", "trust_boundary"):
        _require_nonempty_str(candidate, key, path, result)
    if candidate.get("candidate_kind") not in _CANDIDATE_KINDS:
        result.add(f"{path}.candidate_kind", f"must be one of {sorted(_CANDIDATE_KINDS)}")
    for key in ("target_surfaces", "quality_gates", "missing_requirements", "recommended_record_actions"):
        _require_list(candidate.get(key), f"{path}.{key}", result)
    _require_mapping(candidate.get("reuse_boundary"), f"{path}.reuse_boundary", result)
    _require_mapping(candidate.get("source_records"), f"{path}.source_records", result)
    for index, gate in enumerate(candidate.get("quality_gates") or []):
        _validate_gate(gate, f"{path}.quality_gates[{index}]", result)
    for key, expected in (
        ("can_materialize_without_human_review", False),
        ("can_promote_claim_trust", False),
        ("orientation_only", True),
    ):
        _require_bool_value(candidate.get(key), expected, f"{path}.{key}", result)
    if not isinstance(candidate.get("can_draft_reusable_block"), bool):
        result.add(f"{path}.can_draft_reusable_block", "must be a boolean")


def _validate_gate(gate: Any, path: str, result: ContractResult) -> None:
    _require_mapping(gate, path, result)
    if not isinstance(gate, dict):
        return
    _require_nonempty_str(gate, "gate", path, result)
    if gate.get("status") not in {"passed", "missing"}:
        result.add(f"{path}.status", "must be 'passed' or 'missing'")
    _require_list(gate.get("evidence"), f"{path}.evidence", result)
    _require_list(gate.get("missing"), f"{path}.missing", result)
