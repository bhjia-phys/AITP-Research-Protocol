"""Contracts for source reconstruction coverage audits."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping, _require_nonempty_str


def validate_source_reconstruction_audit(payload: dict[str, Any], *, path: str = "source_reconstruction_audit") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_audit":
        result.add(f"{path}.kind", "must be 'source_reconstruction_audit'")
    for key in ("topic_id", "claim_id", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    for key in ("complete", "summary_inputs_trusted", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in ("required_components", "missing_components", "source_refs"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_mapping(payload.get("components"), f"{path}.components", result)
    if isinstance(payload.get("components"), dict):
        for name, component in payload["components"].items():
            _validate_component(component, f"{path}.components.{name}", result)
    return result


def require_valid_source_reconstruction_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_source_reconstruction_manifest(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_manifest":
        result.add(f"{path}.kind", "must be 'source_reconstruction_manifest'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    for key in ("claim_count", "complete_claim_count", "incomplete_claim_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _require_mapping(payload.get("missing_component_counts"), f"{path}.missing_component_counts", result)
    if isinstance(payload.get("missing_component_counts"), dict):
        for key in (
            "definitions",
            "assumptions_or_scope",
            "source_locations",
            "dependency_graph",
            "reconstruction_path",
            "failure_conditions",
        ):
            if not isinstance(payload["missing_component_counts"].get(key), int) or payload["missing_component_counts"][key] < 0:
                result.add(f"{path}.missing_component_counts.{key}", "must be a non-negative integer")
    for key in ("items", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in (
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if isinstance(payload.get("items"), list):
        for index, item in enumerate(payload["items"]):
            _validate_manifest_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_source_reconstruction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_source_reconstruction_review_manifest(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_review_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("kind") != "source_reconstruction_review_manifest":
        result.add(f"{path}.kind", "must be 'source_reconstruction_review_manifest'")
    if not isinstance(payload.get("claim_count"), int) or payload["claim_count"] < 0:
        result.add(f"{path}.claim_count", "must be a non-negative integer")
    _require_mapping(payload.get("review_progress"), f"{path}.review_progress", result)
    if isinstance(payload.get("review_progress"), dict):
        for key in ("passed", "needs_revision", "inconclusive", "pending"):
            if not isinstance(payload["review_progress"].get(key), int) or payload["review_progress"][key] < 0:
                result.add(f"{path}.review_progress.{key}", "must be a non-negative integer")
    for key in ("items", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if isinstance(payload.get("items"), list):
        for index, item in enumerate(payload["items"]):
            _validate_review_manifest_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_source_reconstruction_review_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_review_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_source_reconstruction_review_packet(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_review_packet",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    for key in (
        "ok",
        "kind",
        "topic_id",
        "claim_id",
        "claim",
        "reconstruction_audit",
        "missing_components",
        "satisfied_components",
        "typed_records",
        "component_reviews",
        "review_scope",
        "requires_human_or_adversarial_review",
        "recommended_actions",
        "truth_source",
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if key not in payload:
            result.add(f"{path}.{key}", "missing required source reconstruction review key")
    _require_bool_value(payload.get("ok"), True, f"{path}.ok", result)
    if payload.get("kind") != "source_reconstruction_review_packet":
        result.add(f"{path}.kind", "must be 'source_reconstruction_review_packet'")
    for key in ("topic_id", "claim_id", "truth_source", "review_scope"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    if payload.get("review_scope") != "source_stack_reconstruction_before_trust_promotion":
        result.add(f"{path}.review_scope", "must be 'source_stack_reconstruction_before_trust_promotion'")
    for key in (
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if not isinstance(payload.get("requires_human_or_adversarial_review"), bool):
        result.add(f"{path}.requires_human_or_adversarial_review", "must be a boolean")
    _require_mapping(payload.get("claim"), f"{path}.claim", result)
    _require_mapping(payload.get("reconstruction_audit"), f"{path}.reconstruction_audit", result)
    _require_mapping(payload.get("typed_records"), f"{path}.typed_records", result)
    for key in ("missing_components", "satisfied_components", "component_reviews", "recommended_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("component_reviews"), list):
        for index, item in enumerate(payload["component_reviews"]):
            _validate_review_component(item, f"{path}.component_reviews[{index}]", result)
    if isinstance(payload.get("typed_records"), dict):
        for key in ("reference_locations", "evidence", "physics_objects", "object_relations", "validation_contracts"):
            _require_list(payload["typed_records"].get(key), f"{path}.typed_records.{key}", result)
    return result


def require_valid_source_reconstruction_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_review_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_source_reconstruction_review_result_record(
    payload: dict[str, Any],
    *,
    path: str = "source_reconstruction_review_result_record",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "source_reconstruction_review_result":
        result.add(f"{path}.kind", "must be 'source_reconstruction_review_result'")
    for key in ("result_id", "topic_id", "claim_id", "status", "reviewer_role", "summary"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    for key in (
        "reviewed_components",
        "basis_refs",
        "evidence_refs",
        "validation_result_ids",
        "reference_location_ids",
        "object_ids",
        "relation_ids",
        "remaining_actions",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("reviewed_components"), list) and len(payload["reviewed_components"]) == 0:
        result.add(f"{path}.reviewed_components", "must not be empty")
    basis_keys = (
        "basis_refs",
        "evidence_refs",
        "validation_result_ids",
        "reference_location_ids",
        "object_ids",
        "relation_ids",
    )
    if all(isinstance(payload.get(key), list) and len(payload[key]) == 0 for key in basis_keys):
        result.add(f"{path}.basis_refs", "review basis must cite at least one source or typed record")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    return result


def require_valid_source_reconstruction_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_source_reconstruction_review_result_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_component(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("status") not in {"satisfied", "missing"}:
        result.add(f"{path}.status", "must be satisfied or missing")
    _require_list(payload.get("record_ids"), f"{path}.record_ids", result)


def _validate_manifest_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topic_id",
        "claim_id",
        "status",
        "review_priority",
        "audit_cli",
        "audit_mcp",
        "review_packet_cli",
        "review_packet_mcp",
        "review_packet_surface",
    ):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(payload.get("claim_statement"), str):
        result.add(f"{path}.claim_statement", "must be a string")
    if payload.get("status") not in {"complete", "incomplete"}:
        result.add(f"{path}.status", "must be complete or incomplete")
    if payload.get("review_priority") not in {"high", "low"}:
        result.add(f"{path}.review_priority", "must be high or low")
    for key in ("missing_components", "satisfied_components", "source_refs", "recommended_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_review_component(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "component", path, result)
    if payload.get("status") not in {"satisfied", "missing"}:
        result.add(f"{path}.status", "must be satisfied or missing")
    for key in ("record_ids", "review_questions", "recommended_actions", "recommended_record_commands"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)


def _validate_review_manifest_item(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in (
        "topic_id",
        "claim_id",
        "source_reconstruction_status",
        "review_status",
        "review_packet_cli",
        "result_cli",
    ):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("claim_statement"), str):
        result.add(f"{path}.claim_statement", "must be a string")
    if payload.get("source_reconstruction_status") not in {"complete", "incomplete"}:
        result.add(f"{path}.source_reconstruction_status", "must be complete or incomplete")
    if payload.get("review_status") not in {"passed", "needs_revision", "inconclusive", "pending"}:
        result.add(f"{path}.review_status", "must be an allowed review status")
    _require_mapping(payload.get("latest_review_result"), f"{path}.latest_review_result", result)
    for key in ("missing_components", "review_result_ids", "reviewed_components", "remaining_actions", "next_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
