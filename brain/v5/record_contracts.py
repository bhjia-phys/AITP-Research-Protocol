"""Contracts for typed write-record public surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping, _require_nonempty_str


def validate_evidence_record(payload: dict[str, Any], *, path: str = "evidence_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="evidence")
    if result.issues:
        return result
    for key in ("evidence_id", "topic_id", "claim_id", "evidence_type", "status", "summary"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("supports_outputs", "source_refs", "tool_run_ids", "validation_result_ids", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_evidence_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_evidence_record(payload), payload)


def validate_tool_run_record(payload: dict[str, Any], *, path: str = "tool_run_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="tool_run")
    if result.issues:
        return result
    for key in ("run_id", "recipe_id", "tool_family", "tool_name", "topic_id", "claim_id", "evidence_status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("inputs", "outputs", "environment"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("code_state_ids", "artifact_ids", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_tool_run_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_tool_run_record(payload), payload)


def validate_code_state_record(payload: dict[str, Any], *, path: str = "code_state_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="code_state")
    if result.issues:
        return result
    for key in (
        "code_state_id",
        "repo_id",
        "upstream_remote",
        "upstream_branch",
        "upstream_commit",
        "local_branch",
        "worktree_path",
    ):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("dirty"), bool):
        result.add(f"{path}.dirty", "must be a boolean")
    for key in ("build_config", "runtime_environment", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_code_state_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_code_state_record(payload), payload)


def validate_tool_recipe_record(payload: dict[str, Any], *, path: str = "tool_recipe_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="tool_recipe")
    if result.issues:
        return result
    for key in ("recipe_id", "tool_family", "tool_name", "purpose"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("required_inputs", "expected_outputs", "invariants"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_tool_recipe_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_tool_recipe_record(payload), payload)


def validate_reference_location_record(payload: dict[str, Any], *, path: str = "reference_location_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="reference_location")
    if result.issues:
        return result
    for key in ("location_id", "topic_id", "connector_id", "location_type", "uri", "label", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("metadata", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    return result


def require_valid_reference_location_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_reference_location_record(payload), payload)


def validate_physics_object_record(payload: dict[str, Any], *, path: str = "physics_object_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="physics_object")
    if result.issues:
        return result
    for key in ("object_id", "topic_id", "object_type", "name", "definition", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("assumptions", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("metadata", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_physics_object_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_physics_object_record(payload), payload)


def validate_object_relation_record(payload: dict[str, Any], *, path: str = "object_relation_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="object_relation")
    if result.issues:
        return result
    for key in ("relation_id", "topic_id", "relation_type", "subject_id", "object_id", "statement", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("assumptions", "failure_modes", "source_refs", "evidence_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    return result


def require_valid_object_relation_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_object_relation_record(payload), payload)


def validate_sensemaking_report_record(payload: dict[str, Any], *, path: str = "sensemaking_report_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="sensemaking_report")
    if result.issues:
        return result
    for key in ("report_id", "topic_id", "claim_id", "title", "summary"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("object_ids", "relation_ids", "evidence_refs", "open_questions", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("validation_status") != "not_validation":
        result.add(f"{path}.validation_status", "must be 'not_validation' — sensemaking reports are orientation-only")
    return result


def require_valid_sensemaking_report_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_sensemaking_report_record(payload), payload)


def validate_validation_contract_record(payload: dict[str, Any], *, path: str = "validation_contract_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="validation_contract")
    if result.issues:
        return result
    for key in ("contract_id", "topic_id", "claim_id", "validator_role", "status"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("required_checks", "failure_modes", "required_evidence_outputs"):
        lst = payload.get(key)
        _require_list(lst, f"{path}.{key}", result)
        if isinstance(lst, list) and len(lst) == 0:
            result.add(f"{path}.{key}", "must not be empty — validation requires explicit failure hypotheses")
    for key in ("tool_recipe_ids", "executor_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_validation_contract_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_validation_contract_record(payload), payload)


def validate_validation_result_record(payload: dict[str, Any], *, path: str = "validation_result_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="validation_result")
    if result.issues:
        return result
    for key in ("result_id", "topic_id", "claim_id", "contract_id", "tool_run_id", "status", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"passed", "failed", "inconclusive", "partial"}:
        result.add(f"{path}.status", "must be passed, failed, inconclusive, or partial")
    for key in ("checked_outputs", "missing_outputs", "covered_failure_modes", "failure_modes_observed", "evidence_refs", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("status") == "passed" and payload.get("missing_outputs"):
        result.add(f"{path}.missing_outputs", "must be empty when status is passed")
    if payload.get("status") == "passed" and payload.get("failure_modes_observed"):
        result.add(f"{path}.failure_modes_observed", "must be empty when status is passed")
    return result


def require_valid_validation_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_validation_result_record(payload), payload)


def validate_human_checkpoint_record(payload: dict[str, Any], *, path: str = "human_checkpoint_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="human_checkpoint")
    if result.issues:
        return result
    for key in ("checkpoint_id", "topic_id", "claim_id", "reason", "requested_by"):
        _require_nonempty_str(payload, key, path, result)
    options = payload.get("options")
    _require_list(options, f"{path}.options", result)
    if isinstance(options, list) and len(options) == 0:
        result.add(f"{path}.options", "must not be empty — checkpoint requires at least one option")
    status = payload.get("status")
    if status not in ("open", "decided"):
        result.add(f"{path}.status", "must be 'open' or 'decided'")
    if status == "decided":
        for key in ("decision", "rationale", "decided_by"):
            _require_nonempty_str(payload, key, path, result)
        if isinstance(options, list) and isinstance(payload.get("decision"), str) and payload["decision"] not in options:
            result.add(f"{path}.decision", f"must be one of options {options}")
    return result


def require_valid_human_checkpoint_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_human_checkpoint_record(payload), payload)


def validate_failure_mode_review_result_record(
    payload: dict[str, Any], *, path: str = "failure_mode_review_result_record"
) -> ContractResult:
    result = _validate_base_record(payload, path, kind="failure_mode_review_result")
    if result.issues:
        return result
    for key in ("result_id", "topic_id", "claim_id", "checkpoint_id", "status", "reviewer_role", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    for key in (
        "reviewed_failure_modes",
        "basis_refs",
        "evidence_refs",
        "validation_result_ids",
        "tool_run_ids",
        "reference_location_ids",
        "artifact_ids",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("reviewed_failure_modes"), list) and len(payload["reviewed_failure_modes"]) == 0:
        result.add(f"{path}.reviewed_failure_modes", "must not be empty")
    basis_keys = ("basis_refs", "evidence_refs", "validation_result_ids", "tool_run_ids", "reference_location_ids", "artifact_ids")
    if all(isinstance(payload.get(key), list) and len(payload[key]) == 0 for key in basis_keys):
        result.add(f"{path}.basis_refs", "review basis must cite at least one typed/literature/tool reference")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_failure_mode_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_failure_mode_review_result_record(payload), payload)


def validate_promotion_packet_record(payload: dict[str, Any], *, path: str = "promotion_packet_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="promotion_packet")
    if result.issues:
        return result
    for key in ("packet_id", "topic_id", "claim_id", "proposed_memory_kind", "scope"):
        _require_nonempty_str(payload, key, path, result)
    evidence = payload.get("evidence_refs")
    _require_list(evidence, f"{path}.evidence_refs", result)
    if isinstance(evidence, list) and len(evidence) == 0:
        result.add(f"{path}.evidence_refs", "must not be empty — promotion requires evidence")
    _require_list(payload.get("validation_result_ids"), f"{path}.validation_result_ids", result)
    failure_modes = payload.get("known_failure_modes")
    _require_list(failure_modes, f"{path}.known_failure_modes", result)
    if isinstance(failure_modes, list) and len(failure_modes) == 0:
        result.add(f"{path}.known_failure_modes", "must not be empty — promotion requires known failure modes")
    for key in ("failure_mode_review_checkpoint_id", "failure_mode_review_result_id"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    return result


def require_valid_promotion_packet_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_promotion_packet_record(payload), payload)


def validate_memory_entry_record(payload: dict[str, Any], *, path: str = "memory_entry_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="memory_entry")
    if result.issues:
        return result
    for key in (
        "entry_id",
        "topic_id",
        "source_claim_id",
        "source_topic_id",
        "statement",
        "memory_kind",
        "scope",
        "source_packet_id",
        "human_checkpoint_id",
        "status",
    ):
        _require_nonempty_str(payload, key, path, result)
    evidence = payload.get("evidence_refs")
    _require_list(evidence, f"{path}.evidence_refs", result)
    if isinstance(evidence, list) and len(evidence) == 0:
        result.add(f"{path}.evidence_refs", "must not be empty — memory entries require evidence")
    _require_list(payload.get("validation_result_ids"), f"{path}.validation_result_ids", result)
    for key in ("non_claims", "known_failure_modes"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("failure_mode_review_checkpoint_id", "failure_mode_review_result_id"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    return result


def require_valid_memory_entry_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_memory_entry_record(payload), payload)


def validate_trust_update_record(payload: dict[str, Any], *, path: str = "trust_update_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="trust_update")
    if result.issues:
        return result
    for key in ("update_id", "request_id", "action", "session_id", "topic_id", "claim_id", "previous_state", "new_state", "status", "preflight_token"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"applied", "blocked"}:
        result.add(f"{path}.status", "must be 'applied' or 'blocked'")
    for key in ("applied", "preflight_allowed"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("applied") is True and payload.get("status") != "applied":
        result.add(f"{path}.status", "must be 'applied' when applied is true")
    if payload.get("applied") is False and payload.get("status") != "blocked":
        result.add(f"{path}.status", "must be 'blocked' when applied is false")
    for key in ("evidence_refs", "code_state_ids", "required_actions", "policy_reason_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    return result


def require_valid_trust_update_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_trust_update_record(payload), payload)


def _validate_base_record(payload: Any, path: str, *, kind: str) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    return result


def _require_valid(result: ContractResult, payload: dict[str, Any]) -> dict[str, Any]:
    if not result.ok:
        raise ContractError(result)
    return payload
