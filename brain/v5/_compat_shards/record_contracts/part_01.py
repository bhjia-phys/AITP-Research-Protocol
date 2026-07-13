# Compatibility shard 1 for record_contracts.
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
    for key in ("scientific_run_id", "supersedes_run_id", "supersedes", "lane"):
        if key not in payload or not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be present and must be a string")
    if payload.get("lane") not in {"final", "diagnostic", "exploratory"}:
        result.add(f"{path}.lane", "must be final, diagnostic, or exploratory")
    if (
        isinstance(payload.get("supersedes"), str)
        and isinstance(payload.get("supersedes_run_id"), str)
        and payload.get("supersedes") != payload.get("supersedes_run_id")
    ):
        result.add(f"{path}.supersedes", "must equal supersedes_run_id")
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
