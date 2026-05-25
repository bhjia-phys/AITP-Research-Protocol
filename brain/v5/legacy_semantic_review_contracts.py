"""Contracts for legacy migration semantic review queues."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


def validate_legacy_semantic_review_queue(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_queue",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result

    for key in ("kind", "run_id", "migration_dir", "queue_status", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("kind") != "legacy_semantic_review_queue":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_queue'")
    if payload.get("queue_status") not in {"ready_for_semantic_review", "coverage_gaps_first"}:
        result.add(f"{path}.queue_status", "must be an allowed queue status")
    if payload.get("truth_source") != "migration_manifests_and_typed_records":
        result.add(f"{path}.truth_source", "must be 'migration_manifests_and_typed_records'")
    for key in (
        "semantic_lossless_proven",
        "semantic_review_required",
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_kernel_state",
        "can_update_claim_trust",
    ):
        if payload.get(key) not in {False, True}:
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("semantic_lossless_proven") is not False:
        result.add(f"{path}.semantic_lossless_proven", "must be false")
    if payload.get("semantic_review_required") is not True:
        result.add(f"{path}.semantic_review_required", "must be true")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    for key in ("topic_count", "legacy_file_count", "review_item_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _validate_priority_counts(payload.get("priority_counts"), f"{path}.priority_counts", result)
    _validate_coverage_audit(payload.get("coverage_audit"), f"{path}.coverage_audit", result)
    items = payload.get("items")
    if not isinstance(items, list):
        result.add(f"{path}.items", "must be a list")
    else:
        for index, item in enumerate(items):
            _validate_item(item, f"{path}.items[{index}]", result)
    return result


def require_valid_legacy_semantic_review_queue(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_queue(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_legacy_semantic_review_packet(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_packet",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_review_packet":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_packet'")
    for key in ("run_id", "migration_dir", "topic", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("truth_source") != "migration_manifests_and_typed_records":
        result.add(f"{path}.truth_source", "must be 'migration_manifests_and_typed_records'")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
    _validate_item(payload.get("queue_item"), f"{path}.queue_item", result)
    if not isinstance(payload.get("active_claim"), dict):
        result.add(f"{path}.active_claim", "must be a mapping")
    typed = payload.get("typed_records")
    if not isinstance(typed, dict):
        result.add(f"{path}.typed_records", "must be a mapping")
    else:
        for key in ("reference_locations", "evidence", "physics_objects", "object_relations", "sensemaking_reports", "validation_results"):
            if not isinstance(typed.get(key), list):
                result.add(f"{path}.typed_records.{key}", "must be a list")
    for key in ("legacy_review_refs", "review_checklist"):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    return result


def require_valid_legacy_semantic_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_legacy_semantic_review_manifest(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_manifest",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_review_manifest":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_manifest'")
    for key in ("run_id", "migration_dir", "workspace", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key, expected in (
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
    for key in ("topic_count", "review_item_count", "pending_count", "passed_count", "needs_revision_count", "inconclusive_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    _validate_priority_counts(payload.get("priority_counts"), f"{path}.priority_counts", result)
    progress = payload.get("review_progress")
    if not isinstance(progress, dict):
        result.add(f"{path}.review_progress", "must be a mapping")
    else:
        for key in ("passed", "inconclusive", "needs_revision", "pending"):
            if not isinstance(progress.get(key), int) or progress[key] < 0:
                result.add(f"{path}.review_progress.{key}", "must be a non-negative integer")
    items = payload.get("items")
    if not isinstance(items, list):
        result.add(f"{path}.items", "must be a list")
    else:
        for index, item in enumerate(items):
            _validate_manifest_item(item, f"{path}.items[{index}]", result)
    if not isinstance(payload.get("next_actions"), list):
        result.add(f"{path}.next_actions", "must be a list")
    return result


def require_valid_legacy_semantic_review_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_legacy_semantic_review_result_record(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_review_result_record",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "legacy_semantic_review_result":
        result.add(f"{path}.kind", "must be 'legacy_semantic_review_result'")
    for key in ("review_id", "migration_run_id", "migration_dir", "topic", "status", "summary", "reviewer_role"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("status") not in {"passed", "needs_revision", "inconclusive"}:
        result.add(f"{path}.status", "must be passed, needs_revision, or inconclusive")
    for key in (
        "reviewed_legacy_refs",
        "reviewed_typed_refs",
        "evidence_refs",
        "validation_result_ids",
        "remaining_actions",
    ):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    basis_keys = ("reviewed_legacy_refs", "reviewed_typed_refs", "evidence_refs", "validation_result_ids")
    if all(isinstance(payload.get(key), list) and len(payload[key]) == 0 for key in basis_keys):
        result.add(f"{path}.reviewed_legacy_refs", "review basis must cite at least one legacy, typed, evidence, or validation reference")
    for key in ("active_claim_id", "checkpoint_id"):
        if not isinstance(payload.get(key, ""), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_legacy_semantic_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_review_result_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_legacy_semantic_repair_plan(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_repair_plan",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_repair_plan":
        result.add(f"{path}.kind", "must be 'legacy_semantic_repair_plan'")
    for key in ("run_id", "migration_dir", "topic", "active_claim_id", "repair_status", "truth_source"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("repair_status") not in {
        "proposed_repairs",
        "awaiting_needs_revision_review",
        "no_repair_candidates",
    }:
        result.add(f"{path}.repair_status", "must be an allowed repair status")
    if payload.get("truth_source") != "typed_review_results_and_legacy_refs":
        result.add(f"{path}.truth_source", "must be 'typed_review_results_and_legacy_refs'")
    for key, expected in (
        ("can_apply", False),
        ("semantic_lossless_proven", False),
        ("semantic_review_required", True),
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(key) is not expected:
            result.add(f"{path}.{key}", f"must be {expected}")
    if not isinstance(payload.get("latest_semantic_review"), dict):
        result.add(f"{path}.latest_semantic_review", "must be a mapping")
    repairs = payload.get("proposed_repairs")
    if not isinstance(repairs, list):
        result.add(f"{path}.proposed_repairs", "must be a list")
    else:
        for index, repair in enumerate(repairs):
            _validate_repair(repair, f"{path}.proposed_repairs[{index}]", result)
    return result


def require_valid_legacy_semantic_repair_plan(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_repair_plan(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_legacy_semantic_repair_apply(
    payload: dict[str, Any],
    *,
    path: str = "legacy_semantic_repair_apply",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "legacy_semantic_repair_apply":
        result.add(f"{path}.kind", "must be 'legacy_semantic_repair_apply'")
    for key in (
        "repair_id",
        "run_id",
        "migration_dir",
        "topic",
        "active_claim_id",
        "review_id",
        "repair_type",
    ):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("repair_type") != "claim_statement_backfill":
        result.add(f"{path}.repair_type", "must be 'claim_statement_backfill'")
    for key in ("previous_value", "new_value"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    for key in ("basis_refs", "required_actions"):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    for key in ("applied", "semantic_lossless_proven", "summary_inputs_trusted", "can_update_kernel_state", "can_update_claim_trust"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if payload.get("semantic_lossless_proven") is not False:
        result.add(f"{path}.semantic_lossless_proven", "must be false")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    return result


def require_valid_legacy_semantic_repair_apply(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_semantic_repair_apply(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_priority_counts(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("critical", "high", "medium", "low"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")


def _validate_coverage_audit(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    if payload.get("coverage_status") not in {"accounted_needs_review", "coverage_gaps"}:
        result.add(f"{path}.coverage_status", "must be an allowed coverage status")
    for key in (
        "file_preservation_ok",
        "archive_reference_coverage_ok",
        "markdown_readability_ok",
    ):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if not isinstance(payload.get("gap_topic_count"), int) or payload["gap_topic_count"] < 0:
        result.add(f"{path}.gap_topic_count", "must be a non-negative integer")
    if not isinstance(payload.get("gap_topics"), list):
        result.add(f"{path}.gap_topics", "must be a list")


def _validate_item(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("topic", "legacy_shape", "coverage_status", "review_priority"):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("review_priority") not in {"critical", "high", "medium", "low"}:
        result.add(f"{path}.review_priority", "must be an allowed review priority")
    if payload.get("coverage_status") not in {"accounted_needs_review", "coverage_gaps"}:
        result.add(f"{path}.coverage_status", "must be an allowed coverage status")
    for key in (
        "file_count",
        "structured_file_count",
        "archive_reference_count",
        "preserved_source_refs",
    ):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if not isinstance(payload.get("written_records"), dict):
        result.add(f"{path}.written_records", "must be a mapping")
    _validate_source_reconstruction(payload.get("source_reconstruction"), f"{path}.source_reconstruction", result)
    if payload.get("semantic_review_status") not in {
        "pending",
        "reviewed_passed",
        "reviewed_needs_revision",
        "reviewed_inconclusive",
    }:
        result.add(f"{path}.semantic_review_status", "must be an allowed semantic review status")
    if not isinstance(payload.get("semantic_review_result_ids"), list) or not all(
        isinstance(value, str) for value in payload.get("semantic_review_result_ids", [])
    ):
        result.add(f"{path}.semantic_review_result_ids", "must be a list of strings")
    latest = payload.get("latest_semantic_review")
    if latest is not None and not isinstance(latest, dict):
        result.add(f"{path}.latest_semantic_review", "must be a mapping")
    for key in ("review_reasons", "recommended_actions"):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")
    if payload.get("semantic_review_required") is not True:
        result.add(f"{path}.semantic_review_required", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_source_reconstruction(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    if payload.get("status") not in {"complete", "incomplete", "missing_claim_id", "missing_claim_record", "not_audited"}:
        result.add(f"{path}.status", "must be an allowed source reconstruction status")
    if not isinstance(payload.get("complete"), bool):
        result.add(f"{path}.complete", "must be a boolean")
    for key in ("missing_components", "source_refs"):
        if not isinstance(payload.get(key), list) or not all(isinstance(value, str) for value in payload[key]):
            result.add(f"{path}.{key}", "must be a list of strings")


def _validate_manifest_item(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in ("topic", "active_claim_id", "review_status", "review_priority", "packet_cli", "result_cli_template"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("review_status") not in {"passed", "inconclusive", "needs_revision", "pending"}:
        result.add(f"{path}.review_status", "must be an allowed review status")
    for key in ("review_reasons", "recommended_actions"):
        if not isinstance(payload.get(key), list):
            result.add(f"{path}.{key}", "must be a list")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_repair(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return
    for key in (
        "repair_type",
        "target_ref",
        "current_value",
        "proposed_value",
        "mutation_authority",
    ):
        if not isinstance(payload.get(key), str):
            result.add(f"{path}.{key}", "must be a string")
    if payload.get("repair_type") != "claim_statement_backfill":
        result.add(f"{path}.repair_type", "must be 'claim_statement_backfill'")
    if payload.get("mutation_authority") != "none_review_and_apply_separately":
        result.add(f"{path}.mutation_authority", "must be 'none_review_and_apply_separately'")
    if not isinstance(payload.get("basis_refs"), list) or not all(
        isinstance(value, str) and value for value in payload.get("basis_refs", [])
    ):
        result.add(f"{path}.basis_refs", "must be a non-empty list of strings")
