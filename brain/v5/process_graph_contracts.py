"""Contracts for read-only process graph slices."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_bool_value, _require_list, _require_mapping
from brain.v5.moment_policy_contracts import validate_host_agnostic_moment_policy, validate_payload_hint
from brain.v5.source_reconstruction_contracts import (
    validate_source_reconstruction_review_manifest,
    validate_source_stack_coverage_manifest,
)


def validate_process_graph_slice(payload: dict[str, Any], *, path: str = "process_graph_slice") -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "process_graph_slice":
        result.add(f"{path}.kind", "must be 'process_graph_slice'")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    for key in (
        "nodes",
        "edges",
        "open_obligations",
        "source_backtrace",
        "source_asset_index",
        "relation_neighborhood",
        "exploratory_records",
        "provenance_gaps",
        "trust_boundary_reasons",
        "recommended_moments",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("provenance_gaps"), list):
        for index, gap in enumerate(payload["provenance_gaps"]):
            _validate_provenance_gap(gap, f"{path}.provenance_gaps[{index}]", result)
    _require_mapping(payload.get("route_state"), f"{path}.route_state", result)
    _require_mapping(payload.get("source_stack_coverage"), f"{path}.source_stack_coverage", result)
    if isinstance(payload.get("source_stack_coverage"), dict):
        result.extend(
            validate_source_stack_coverage_manifest(
                payload["source_stack_coverage"],
                path=f"{path}.source_stack_coverage",
            )
        )
    _require_mapping(payload.get("source_reconstruction_review"), f"{path}.source_reconstruction_review", result)
    if isinstance(payload.get("source_reconstruction_review"), dict):
        result.extend(
            validate_source_reconstruction_review_manifest(
                payload["source_reconstruction_review"],
                path=f"{path}.source_reconstruction_review",
            )
        )
    moment_policy = payload.get("moment_policy")
    _require_mapping(moment_policy, f"{path}.moment_policy", result)
    if isinstance(moment_policy, dict):
        result.extend(validate_host_agnostic_moment_policy(moment_policy, path=f"{path}.moment_policy"))
    _require_mapping(payload.get("record_counts"), f"{path}.record_counts", result)
    _require_mapping(payload.get("truncation"), f"{path}.truncation", result)
    return result


def require_valid_process_graph_slice(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_process_graph_slice(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_provenance_gap(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("gap_id", "gap_type", "target_type", "target_id", "provenance_kind"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key in ("target_refs", "recommended_actions", "recommended_entrypoints", "payload_hints"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("required_now", "required_before_trust_change"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if isinstance(payload.get("payload_hints"), list):
        for index, hint in enumerate(payload["payload_hints"]):
            validate_payload_hint(hint, f"{path}.payload_hints[{index}]", result)
