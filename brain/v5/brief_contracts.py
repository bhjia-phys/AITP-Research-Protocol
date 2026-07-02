"""Execution-brief contract validation."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
    _validate_flow_profile,
    validate_action_budget,
    validate_risk_assessment,
)


_BRIEF_REQUIRED_KEYS = (
    "session",
    "current_focus",
    "flow_profile",
    "risk_assessment",
    "action_budget",
    "known_context",
    "claim_relation_map",
    "mandatory_reflection",
    "next_action_candidates",
    "forbidden_now",
    "human_checkpoint",
)


def validate_execution_brief(payload: dict[str, Any], *, path: str = "brief") -> ContractResult:
    """Validate the public execution-brief payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _BRIEF_REQUIRED_KEYS:
        if key not in payload:
            result.add(key, "missing required execution brief key")

    if "session" in payload:
        _validate_session(payload["session"], f"{path}.session", result)

    if "flow_profile" in payload:
        _validate_flow_profile(payload["flow_profile"], f"{path}.flow_profile", result)

    if "risk_assessment" in payload:
        result.extend(validate_risk_assessment(payload["risk_assessment"], path=f"{path}.risk_assessment"))

    if "action_budget" in payload:
        result.extend(validate_action_budget(payload["action_budget"], path=f"{path}.action_budget"))

    _validate_risk_budget_match(payload, path, result)

    if "known_context" in payload:
        _validate_known_context(payload["known_context"], f"{path}.known_context", result)

    if "mandatory_reflection" in payload:
        _validate_mandatory_reflection(payload, path, result)

    if "human_checkpoint" in payload:
        _validate_human_checkpoint(payload["human_checkpoint"], f"{path}.human_checkpoint", result)

    if "claim_relation_map" in payload:
        from brain.v5.claim_relation_map_contracts import validate_claim_relation_map

        result.extend(validate_claim_relation_map(payload["claim_relation_map"], path=f"{path}.claim_relation_map"))

    for key in ("next_action_candidates", "forbidden_now"):
        if key in payload:
            _require_list(payload[key], f"{path}.{key}", result)

    return result


def _validate_session(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if isinstance(payload, dict):
        _require_nonempty_str(payload, "session_id", path, result)
        _require_nonempty_str(payload, "topic_id", path, result)
        _require_nonempty_str(payload, "context_id", path, result)


def _validate_risk_budget_match(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if not isinstance(payload.get("risk_assessment"), dict) or not isinstance(payload.get("action_budget"), dict):
        return
    risk_level = payload["risk_assessment"].get("level")
    budget_level = payload["action_budget"].get("level")
    if risk_level != budget_level:
        result.add(
            f"{path}.action_budget.level",
            f"must match risk_assessment.level ({risk_level!r}), got {budget_level!r}",
        )


def _validate_known_context(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if "memory_entries" in payload:
        _require_list(payload["memory_entries"], f"{path}.memory_entries", result)
        if isinstance(payload["memory_entries"], list):
            for index, entry in enumerate(payload["memory_entries"]):
                _validate_memory_entry(entry, f"{path}.memory_entries[{index}]", result)
    if "domain_packs" in payload:
        _require_list(payload["domain_packs"], f"{path}.domain_packs", result)
        if isinstance(payload["domain_packs"], list):
            for index, pack in enumerate(payload["domain_packs"]):
                _validate_domain_pack(pack, f"{path}.domain_packs[{index}]", result)
    if "operating_notes" in payload:
        _require_list(payload["operating_notes"], f"{path}.operating_notes", result)
        if isinstance(payload["operating_notes"], list):
            for index, note in enumerate(payload["operating_notes"]):
                _validate_operating_note(note, f"{path}.operating_notes[{index}]", result)


def _validate_memory_entry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("entry_id", "memory_kind", "scope", "source_packet_id", "human_checkpoint_id"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("evidence_refs"), f"{path}.evidence_refs", result)
    if "validation_result_ids" in payload:
        _require_list(payload.get("validation_result_ids"), f"{path}.validation_result_ids", result)
    if "code_state_ids" in payload:
        _require_list(payload.get("code_state_ids"), f"{path}.code_state_ids", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)


def _validate_domain_pack(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("pack_id", "domain", "description", "integration_boundary", "truth_standard_policy"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "suggested_question_intents",
        "risk_signals",
        "tool_recipes",
        "skill_refs",
        "manifest_refs",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)


def _validate_operating_note(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("location_id", "label", "uri", "summary", "status", "location_type"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("diagnostic_lane_labels",):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)


def _validate_mandatory_reflection(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    _require_list(payload["mandatory_reflection"], f"{path}.mandatory_reflection", result)
    budget = payload.get("action_budget")
    if not isinstance(budget, dict) or not isinstance(payload["mandatory_reflection"], list):
        return
    max_questions = budget.get("max_questions")
    if isinstance(max_questions, int) and len(payload["mandatory_reflection"]) > max_questions:
        result.add(f"{path}.mandatory_reflection", "contains more questions than action_budget.max_questions")


def _validate_human_checkpoint(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if isinstance(payload, dict) and not isinstance(payload.get("needed"), bool):
        result.add(f"{path}.needed", "must be a boolean")
