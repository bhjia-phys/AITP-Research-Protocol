"""Contracts for typed write-record public surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping, _require_nonempty_str


def validate_artifact_record(payload: dict[str, Any], *, path: str = "artifact_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="artifact")
    if result.issues:
        return result
    for key in ("artifact_id", "topic_id", "claim_id", "artifact_type", "uri", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("size_bytes"), int):
        result.add(f"{path}.size_bytes", "must be an integer")
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    return result


def require_valid_artifact_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_artifact_record(payload), payload)


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


def validate_claim_status_record(payload: dict[str, Any], *, path: str = "claim_status_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="claim_status")
    if result.issues:
        return result
    for key in ("status_id", "topic_id", "claim_id", "maturity_level", "claim_status", "scope", "risk", "next_action"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("assumptions", "open_gaps", "source_refs", "evidence_refs", "artifact_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("human_gate_required") is not True:
        result.add(f"{path}.human_gate_required", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_claim_status_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_claim_status_record(payload), payload)


def validate_proof_obligation_record(payload: dict[str, Any], *, path: str = "proof_obligation_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="proof_obligation")
    if result.issues:
        return result
    for key in (
        "obligation_id",
        "topic_id",
        "claim_id",
        "statement",
        "obligation_type",
        "status",
        "maturity_level",
        "next_action",
    ):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "required_evidence",
        "proof_strategy",
        "failure_modes",
        "source_refs",
        "evidence_refs",
        "artifact_ids",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("human_gate_required") is not True:
        result.add(f"{path}.human_gate_required", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_proof_obligation_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_proof_obligation_record(payload), payload)


def validate_authority_record(payload: dict[str, Any], *, path: str = "authority_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="authority")
    if result.issues:
        return result
    for key in ("authority_id", "topic_id", "authority_type", "authority_statement", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("authority_type") not in {
        "sector_authority",
        "statistics_convention",
        "formula_convention",
        "dataset_authority",
        "code_path_authority",
    }:
        result.add(f"{path}.authority_type", "must be a supported authority type")
    if payload.get("status") not in {
        "research_authority_not_trust_promotion",
        "candidate",
        "active",
        "superseded",
        "rejected",
    }:
        result.add(f"{path}.status", "must be a supported authority status")
    for key in ("scope", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("evidence_refs", "source_refs", "artifact_ids", "limitations"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_authority_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_authority_record(payload), payload)


def validate_authority_registry(payload: dict[str, Any], *, path: str = "authority_registry") -> ContractResult:
    result = _validate_base_record(payload, path, kind="authority_registry")
    if result.issues:
        return result
    _require_nonempty_str(payload, "topic_id", path, result)
    if not isinstance(payload.get("authority_count"), int):
        result.add(f"{path}.authority_count", "must be an integer")
    if not isinstance(payload.get("include_inactive"), bool):
        result.add(f"{path}.include_inactive", "must be a boolean")
    _require_list(payload.get("authorities"), f"{path}.authorities", result)
    for index, authority in enumerate(payload.get("authorities") or []):
        if isinstance(authority, dict):
            result.extend(validate_authority_record({"ok": True, **authority}, path=f"{path}.authorities[{index}]"))
        else:
            result.add(f"{path}.authorities[{index}]", "must be a mapping")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_authority_registry(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_authority_registry(payload), payload)


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


def validate_source_asset_record(payload: dict[str, Any], *, path: str = "source_asset_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="source_asset")
    if result.issues:
        return result
    for key in ("asset_id", "topic_id", "asset_type", "uri", "title", "source_kind"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("asset_type") not in {
        "paper",
        "lecture",
        "note",
        "book",
        "code_repo",
        "code_snapshot",
        "dataset",
        "generated_artifact",
        "web_page",
        "correspondence",
        "other",
    }:
        result.add(
            f"{path}.asset_type",
            "must be a supported source asset type",
        )
    for key in ("version_anchor", "metadata", "linked_records"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in (
        "source_refs",
        "artifact_ids",
        "code_state_ids",
        "reference_location_ids",
        "derived_from",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_source_asset_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_source_asset_record(payload), payload)


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


def validate_exploratory_record(payload: dict[str, Any], *, path: str = "exploratory_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="exploratory_record")
    if result.issues:
        return result
    for key in ("record_id", "topic_id", "exploration_type", "title", "focal_question", "summary", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("exploration_type") not in {
        "source_asset",
        "question_decomposition",
        "relation_path_brainstorm",
        "backtrace_step",
        "steering_checkpoint",
    }:
        result.add(
            f"{path}.exploration_type",
            "must be source_asset, question_decomposition, relation_path_brainstorm, backtrace_step, or steering_checkpoint",
        )
    if payload.get("status") not in {"open", "active", "resolved", "deferred", "superseded"}:
        result.add(f"{path}.status", "must be open, active, resolved, deferred, or superseded")
    for key in (
        "object_ids",
        "relation_ids",
        "source_refs",
        "artifact_ids",
        "parent_record_ids",
        "derived_record_ids",
        "reasoning_moves",
        "backtrace_targets",
        "candidate_paths",
        "relation_path_questions",
        "definition_boundary_questions",
        "derivation_backtrace_questions",
        "source_dependency_questions",
        "original_question_guard",
        "unresolved_points",
        "next_actions",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_exploratory_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_exploratory_record(payload), payload)


def validate_research_route_record(payload: dict[str, Any], *, path: str = "research_route_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="research_route")
    if result.issues:
        return result
    for key in ("route_id", "topic_id", "title", "route_type", "status", "rationale"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("route_type") not in {
        "derivation",
        "source_backtrace",
        "relation_path",
        "code_validation",
        "benchmark_validation",
        "literature_route",
        "steering_route",
        "other",
    }:
        result.add(f"{path}.route_type", "must be a known route type")
    if payload.get("status") not in {"live", "blocked", "abandoned", "superseded", "selected"}:
        result.add(f"{path}.status", "must be live, blocked, abandoned, superseded, or selected")
    for key in (
        "failure_modes",
        "source_refs",
        "evidence_refs",
        "artifact_ids",
        "parent_route_ids",
        "checkpoint_ids",
        "exploratory_record_ids",
        "object_ids",
        "relation_ids",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_research_route_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_research_route_record(payload), payload)


def validate_research_run_record(payload: dict[str, Any], *, path: str = "research_run_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="research_run")
    if result.issues:
        return result
    for key in ("run_id", "topic_id", "objective", "research_question", "operator", "status", "phase"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"active", "paused", "stopped", "complete", "blocked"}:
        result.add(f"{path}.status", "must be active, paused, stopped, complete, or blocked")
    if payload.get("phase") not in {
        "planning",
        "context_refresh",
        "action_selection",
        "source_review",
        "validation",
        "answer_drafting",
        "awaiting_approval",
        "blocked",
        "complete",
    }:
        result.add(f"{path}.phase", "must be a known research-run phase")
    if payload.get("terminal_answer_state") not in {
        "",
        "answered_with_validated_support",
        "answered_with_conditional_support",
        "blocked_needs_human",
        "negative_or_inconclusive",
        "draft_only",
    }:
        result.add(f"{path}.terminal_answer_state", "must be a known terminal answer state")
    for key in (
        "aitp_slice_refs",
        "action_refs",
        "evidence_refs",
        "validation_refs",
        "source_refs",
        "event_ids",
        "operator_trail",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("metadata"), f"{path}.metadata", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_research_run_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_research_run_record(payload), payload)


def validate_research_run_event_record(
    payload: dict[str, Any],
    *,
    path: str = "research_run_event_record",
) -> ContractResult:
    result = _validate_base_record(payload, path, kind="research_run_event")
    if result.issues:
        return result
    for key in ("event_id", "run_id", "topic_id", "operator", "event_type", "summary", "status"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("event_type") not in {
        "run_started",
        "context_refreshed",
        "action_selected",
        "action_started",
        "action_completed",
        "operator_checkpoint",
        "status_changed",
        "answer_drafted",
        "answer_finalized",
        "blocked",
        "run_stopped",
    }:
        result.add(f"{path}.event_type", "must be a known research-run event type")
    if payload.get("status") not in {"recorded", "blocked", "failed", "superseded"}:
        result.add(f"{path}.status", "must be recorded, blocked, failed, or superseded")
    phase = payload.get("phase")
    if phase and phase not in {
        "planning",
        "context_refresh",
        "action_selection",
        "source_review",
        "validation",
        "answer_drafting",
        "awaiting_approval",
        "blocked",
        "complete",
    }:
        result.add(f"{path}.phase", "must be empty or a known research-run phase")
    for key in ("source_refs", "evidence_refs", "validation_refs", "artifact_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("payload"), f"{path}.payload", result)
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", True),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {str(expected).lower()}")
    return result


def require_valid_research_run_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_research_run_event_record(payload), payload)


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


def validate_lifecycle_event_record(payload: dict[str, Any], *, path: str = "lifecycle_event_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="lifecycle_event")
    if result.issues:
        return result
    for key in ("event_id", "event_type", "subject_record_id", "subject_kind", "lifecycle_status", "reason", "operator", "timestamp"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("event_type") not in {"rehome", "supersede"}:
        result.add(f"{path}.event_type", "must be rehome or supersede")
    if payload.get("subject_kind") not in {"claim", "evidence", "tool_run", "session"}:
        result.add(f"{path}.subject_kind", "must be claim, evidence, tool_run, or session")
    if payload.get("event_type") == "rehome" and not payload.get("to_topic"):
        result.add(f"{path}.to_topic", "must be non-empty for rehome events")
    valid_status = {"active", "misrouted", "voided", "superseded", "duplicate", "rehomed"}
    if payload.get("lifecycle_status") not in valid_status:
        result.add(f"{path}.lifecycle_status", "must be a known lifecycle status")
    return result


def require_valid_lifecycle_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_lifecycle_event_record(payload), payload)


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
