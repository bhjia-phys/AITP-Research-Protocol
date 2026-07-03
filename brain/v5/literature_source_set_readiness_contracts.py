"""Contracts for read-only literature source-set readiness audits."""

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
from brain.v5.record_ref_contracts import validate_record_ref_lookup


_REQUIRED_COMPONENTS = (
    "source_asset",
    "reference_location",
    "extraction_trace",
    "source_reconstruction_review",
)
_FORBIDDEN_USES = (
    "paper_summary_as_evidence",
    "source_set_synthesis_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
)


def validate_literature_source_set_readiness(
    payload: dict[str, Any],
    *,
    path: str = "literature_source_set_readiness",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "literature_source_set_readiness":
        result.add(f"{path}.kind", "must be 'literature_source_set_readiness'")
    for key in ("session_id", "topic_id", "readiness_scope", "read_surface_effect", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "literature_source_set_readiness_only":
        result.add(f"{path}.read_surface_effect", "must be 'literature_source_set_readiness_only'")
    _require_counted_list(payload, "source_refs", "source_ref_count", path, result, nonempty=True)
    _require_counted_list(payload, "source_items", "source_item_count", path, result, nonempty=True)
    if isinstance(payload.get("source_items"), list):
        for index, item in enumerate(payload["source_items"]):
            _validate_source_item(item, f"{path}.source_items[{index}]", result)
    for key in ("ready_source_count", "blocked_source_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if isinstance(payload.get("source_items"), list):
        if payload.get("ready_source_count", 0) + payload.get("blocked_source_count", 0) != len(payload["source_items"]):
            result.add(f"{path}.ready_source_count", "ready plus blocked counts must equal source item count")
    _validate_component_counts(payload.get("component_counts"), f"{path}.component_counts", result)
    _require_list(payload.get("missing_components"), f"{path}.missing_components", result)
    result.extend(validate_record_ref_lookup(payload.get("record_ref_lookup"), path=f"{path}.record_ref_lookup"))
    _require_list(payload.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _validate_policy(payload.get("readiness_policy"), f"{path}.readiness_policy", result)
    for key in (
        "draft_creates_records",
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "write_executed",
        "bridge_called",
        "executes_write_now",
        "mutates_next_payload_now",
        "infers_payload_values",
    ):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)
    for key in ("read_only", "requires_explicit_next_action", "orientation_only", "trust_update_forbidden"):
        _require_bool_value(payload.get(key), True, f"{path}.{key}", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    return result


def require_valid_literature_source_set_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_literature_source_set_readiness(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_source_item(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("source_ref", "topic_id", "readiness_status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("readiness_status") not in {"ready_for_synthesis_review", "blocked_missing_components"}:
        result.add(f"{path}.readiness_status", "must be ready_for_synthesis_review or blocked_missing_components")
    _require_mapping(value.get("components"), f"{path}.components", result)
    components = value.get("components") if isinstance(value.get("components"), dict) else {}
    for component in _REQUIRED_COMPONENTS:
        if component not in components:
            result.add(f"{path}.components", f"must include {component!r}")
        else:
            _validate_component(components[component], f"{path}.components.{component}", result)
    _require_list(value.get("missing_components"), f"{path}.missing_components", result)
    _require_list(value.get("recommended_next_entrypoints"), f"{path}.recommended_next_entrypoints", result)
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_component(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("component", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("component") not in _REQUIRED_COMPONENTS:
        result.add(f"{path}.component", "must be a required readiness component")
    if value.get("status") not in {"present", "missing", "ready_review_present", "review_present_but_not_ready"}:
        result.add(f"{path}.status", "must be a known readiness status")
    if not isinstance(value.get("present"), bool):
        result.add(f"{path}.present", "must be a boolean")
    _require_list(value.get("refs"), f"{path}.refs", result)
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(value.get("source_support_result"), False, f"{path}.source_support_result", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_component_counts(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for component in _REQUIRED_COMPONENTS:
        _require_mapping(value.get(component), f"{path}.{component}", result)
        counts = value.get(component) if isinstance(value.get(component), dict) else {}
        for key in ("present_count", "missing_count"):
            if not isinstance(counts.get(key), int) or counts[key] < 0:
                result.add(f"{path}.{component}.{key}", "must be a non-negative integer")


def _validate_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_list(value.get("required_components"), f"{path}.required_components", result)
    for component in _REQUIRED_COMPONENTS:
        if component not in (value.get("required_components") or []):
            result.add(f"{path}.required_components", f"must include {component!r}")
    _require_list(value.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(value.get("allowed_next_entrypoints"), f"{path}.allowed_next_entrypoints", result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_bool_value(
        value.get("requires_all_sources_ready_before_synthesis"),
        True,
        f"{path}.requires_all_sources_ready_before_synthesis",
        result,
    )
    _require_bool_value(value.get("requires_explicit_next_entrypoint"), True, f"{path}.requires_explicit_next_entrypoint", result)
    forbidden_uses = value.get("forbidden_uses") if isinstance(value.get("forbidden_uses"), list) else []
    for forbidden in _FORBIDDEN_USES:
        if forbidden not in forbidden_uses:
            result.add(f"{path}.forbidden_uses", f"must include {forbidden!r}")


def _require_counted_list(
    payload: dict[str, Any],
    key: str,
    count_key: str,
    path: str,
    result: ContractResult,
    *,
    nonempty: bool = False,
) -> None:
    _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get(key), list):
        if nonempty and not payload[key]:
            result.add(f"{path}.{key}", "must not be empty")
        if payload.get(count_key) != len(payload[key]):
            result.add(f"{path}.{count_key}", f"must equal {key} length")
