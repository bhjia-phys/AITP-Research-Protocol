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
    for key in ("supports_outputs", "source_refs", "tool_run_ids", "artifact_ids"):
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
