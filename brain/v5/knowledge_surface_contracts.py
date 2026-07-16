"""Capability registry and deep public contract for M3 knowledge operations."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class KnowledgeOperationSpec:
    operation: str
    mcp_name: str
    state_effect: str
    required_result_fields: tuple[str, ...]
    truth_source: str
    authorization_guard: str


_OPERATIONS = {
    "knowledge_diagnose_candidate": (
        "read_only",
        (
            "candidate_id",
            "candidate_hash",
            "lane",
            "eligible_for_grounded_review",
            "checked_refs",
            "grounding_pins",
        ),
        "typed_records",
        "read_only",
    ),
    "knowledge_record_review": (
        "kernel_write",
        (
            "candidate_id",
            "candidate_hash",
            "candidate_lane",
            "checkpoint_ref",
            "pinned_ref",
            "write_status",
        ),
        "typed_records_and_host_attestation",
        "host_attested_review_checkpoint",
    ),
    "knowledge_promote_candidate": (
        "kernel_write",
        (
            "candidate_id",
            "candidate_hash",
            "candidate_lane",
            "decision_ref",
            "pinned_ref",
            "write_status",
        ),
        "typed_records_and_host_attestation",
        "host_attested_review_checkpoint",
    ),
    "knowledge_build_source_shelf": (
        "runtime_write",
        ("manifest", "checked_count", "indexed_count", "incomplete_coverage", "issues"),
        "typed_records_and_hash_pinned_source_bytes",
        "derived_index_only",
    ),
    "knowledge_get_source_shelf": (
        "read_only",
        ("manifest", "passages", "issues"),
        "derived_source_shelf",
        "read_only",
    ),
    "knowledge_build_discovery_request": (
        "read_only",
        ("request_id", "gap_ref", "prior_audit_ref", "connector_allowlist"),
        "typed_records",
        "read_only",
    ),
    "knowledge_normalize_discovery_result": (
        "read_only",
        ("receipt_id", "request_id", "connector_coverage", "candidates", "errors"),
        "bounded_host_connector_packets",
        "read_only",
    ),
    "knowledge_query": (
        "read_only",
        ("query", "hits", "coverage", "result_hash", "can_claim_no_result"),
        "typed_records_and_derived_indexes",
        "read_only",
    ),
    "knowledge_compile_context": (
        "read_only",
        (
            "mode",
            "topic_id",
            "entries",
            "snapshot_lineage",
            "coverage",
            "context_hash",
        ),
        "typed_records_and_derived_indexes",
        "read_only",
    ),
}


def knowledge_operation_specs() -> dict[str, KnowledgeOperationSpec]:
    return {
        operation: KnowledgeOperationSpec(
            operation=operation,
            mcp_name=f"aitp_v5_{operation}",
            state_effect=state_effect,
            required_result_fields=required,
            truth_source=truth_source,
            authorization_guard=guard,
        )
        for operation, (state_effect, required, truth_source, guard) in _OPERATIONS.items()
    }


def knowledge_capability_rows() -> tuple[tuple[str, str, str, str, str, str], ...]:
    return tuple(
        (
            spec.operation,
            spec.mcp_name,
            f"aitp-v5 knowledge {spec.operation} --payload-file <args>",
            "knowledge_operation_result",
            spec.state_effect,
            "full",
        )
        for spec in knowledge_operation_specs().values()
    )


def knowledge_surface_names() -> tuple[str, ...]:
    return ("knowledge_operation_result",)


def knowledge_surface_purposes() -> dict[str, str]:
    return {
        "knowledge_operation_result": (
            "full-only M3 knowledge, insight, discovery, shelf, retrieval, or context result"
        )
    }


def knowledge_surface_validators():
    return {"knowledge_operation_result": require_valid_knowledge_operation_result}


def validate_knowledge_operation_result(
    payload: dict[str, Any],
    *,
    path: str = "knowledge_operation_result",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "knowledge_operation_result":
        result.add(f"{path}.kind", "must be 'knowledge_operation_result'")
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    operation = payload.get("operation")
    spec = knowledge_operation_specs().get(operation)
    if spec is None:
        result.add(f"{path}.operation", "must name a registered knowledge operation")
        return result
    if payload.get("state_effect") != spec.state_effect:
        result.add(f"{path}.state_effect", f"must be {spec.state_effect!r}")
    if payload.get("truth_source") != spec.truth_source:
        result.add(f"{path}.truth_source", f"must be {spec.truth_source!r}")
    if payload.get("authorization_guard") != spec.authorization_guard:
        result.add(
            f"{path}.authorization_guard",
            f"must be {spec.authorization_guard!r}",
        )
    kernel_write = spec.state_effect == "kernel_write"
    runtime_write = spec.state_effect == "runtime_write"
    expected_flags = {
        "writes_records": kernel_write,
        "writes_derived_state": runtime_write,
        "can_update_kernel_state": kernel_write,
        "orientation_only": not kernel_write,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
    }
    for field, expected in expected_flags.items():
        if payload.get(field) is not expected:
            result.add(f"{path}.{field}", f"must be {expected!r}")
    value = payload.get("result")
    if not isinstance(value, dict):
        result.add(f"{path}.result", "must be a mapping")
        return result
    for field in spec.required_result_fields:
        if field not in value:
            result.add(f"{path}.result.{field}", "is required")
    _reject_nested_trust(value, result, f"{path}.result")
    _validate_operation_result(operation, value, result, f"{path}.result")
    return result


def _validate_operation_result(
    operation: str,
    value: dict[str, Any],
    result: ContractResult,
    path: str,
) -> None:
    if operation.startswith("knowledge_") and "candidate_hash" in value:
        if not _digest(value.get("candidate_hash")):
            result.add(f"{path}.candidate_hash", "must be lowercase sha256")
    if operation == "knowledge_diagnose_candidate":
        _validate_pin_list(value.get("grounding_pins"), result, f"{path}.grounding_pins")
        if not isinstance(value.get("eligible_for_grounded_review"), bool):
            result.add(f"{path}.eligible_for_grounded_review", "must be a boolean")
    elif operation == "knowledge_record_review":
        _validate_pin(value.get("checkpoint_ref"), result, f"{path}.checkpoint_ref")
        _validate_pin(value.get("pinned_ref"), result, f"{path}.pinned_ref")
    elif operation == "knowledge_promote_candidate":
        _validate_pin(value.get("decision_ref"), result, f"{path}.decision_ref")
        _validate_pin(value.get("pinned_ref"), result, f"{path}.pinned_ref")
    elif operation in {"knowledge_build_source_shelf", "knowledge_get_source_shelf"}:
        manifest = value.get("manifest")
        if not isinstance(manifest, dict):
            result.add(f"{path}.manifest", "must be a mapping")
        elif not _digest(manifest.get("generation")):
            result.add(f"{path}.manifest.generation", "must be lowercase sha256")
    elif operation == "knowledge_build_discovery_request":
        _validate_pin(value.get("gap_ref"), result, f"{path}.gap_ref")
        _validate_pin(value.get("prior_audit_ref"), result, f"{path}.prior_audit_ref")
        if value.get("can_create_source_asset") is not False:
            result.add(f"{path}.can_create_source_asset", "must be false")
    elif operation == "knowledge_normalize_discovery_result":
        if value.get("can_create_source_asset") is not False:
            result.add(f"{path}.can_create_source_asset", "must be false")
    elif operation == "knowledge_query":
        if not _digest(value.get("result_hash")):
            result.add(f"{path}.result_hash", "must be lowercase sha256")
        if not isinstance(value.get("coverage"), dict):
            result.add(f"{path}.coverage", "must be a mapping")
        hits = value.get("hits")
        if not isinstance(hits, list):
            result.add(f"{path}.hits", "must be a list")
        else:
            for index, hit in enumerate(hits):
                if not isinstance(hit, dict) or not _typed_ref(hit.get("record_ref")):
                    result.add(f"{path}.hits[{index}].record_ref", "must be a typed ref")
    elif operation == "knowledge_compile_context":
        if not _digest(value.get("context_hash")):
            result.add(f"{path}.context_hash", "must be lowercase sha256")
        if value.get("orientation_only") is not True:
            result.add(f"{path}.orientation_only", "must be true")
        if value.get("can_update_kernel_state") is not False:
            result.add(f"{path}.can_update_kernel_state", "must be false")


def _reject_nested_trust(value: Any, result: ContractResult, path: str) -> None:
    if isinstance(value, dict):
        if value.get("can_update_claim_trust") is True:
            result.add(f"{path}.can_update_claim_trust", "must never be true")
        if value.get("can_write_evidence") is True:
            result.add(f"{path}.can_write_evidence", "must never be true")
        for key, item in value.items():
            _reject_nested_trust(item, result, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_nested_trust(item, result, f"{path}[{index}]")


def _validate_pin(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be an exact pin mapping")
        return
    if not _typed_ref(value.get("record_ref")):
        result.add(f"{path}.record_ref", "must be a typed record ref")
    if not _digest(value.get("content_hash")):
        result.add(f"{path}.content_hash", "must be lowercase sha256")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.revision", "must be a positive integer")


def _validate_pin_list(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list")
        return
    for index, item in enumerate(value):
        _validate_pin(item, result, f"{path}[{index}]")


def _typed_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    kind, separator, record_id = value.partition(":")
    return bool(separator and kind.strip() and record_id.strip())


def _digest(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def require_valid_knowledge_operation_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_knowledge_operation_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


__all__ = [
    "KnowledgeOperationSpec",
    "knowledge_capability_rows",
    "knowledge_operation_specs",
    "knowledge_surface_names",
    "knowledge_surface_purposes",
    "knowledge_surface_validators",
    "require_valid_knowledge_operation_result",
    "validate_knowledge_operation_result",
]
