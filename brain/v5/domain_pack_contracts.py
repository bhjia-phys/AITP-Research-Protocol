"""Contracts for read-only domain-pack catalog surfaces."""

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


def validate_domain_pack_catalog(
    payload: dict[str, Any],
    *,
    path: str = "domain_pack_catalog",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "domain_pack_catalog":
        result.add(f"{path}.kind", "must be 'domain_pack_catalog'")
    if payload.get("truth_source") != "builtin_domain_pack_registry":
        result.add(f"{path}.truth_source", "must be 'builtin_domain_pack_registry'")
    _require_nonempty_str(payload, "selection_scope", path, result)
    _require_mapping(payload.get("claim_context"), f"{path}.claim_context", result)
    _require_list(payload.get("packs"), f"{path}.packs", result)
    _require_list(payload.get("required_followup_for_use"), f"{path}.required_followup_for_use", result)
    _require_count(payload, "known_pack_count", path, result)
    _require_count(payload, "pack_count", path, result)
    if isinstance(payload.get("pack_count"), int) and isinstance(payload.get("packs"), list):
        if payload["pack_count"] != len(payload["packs"]):
            result.add(f"{path}.pack_count", "must match number of packs")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("can_materialize_skills", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    if isinstance(payload.get("packs"), list):
        for index, pack in enumerate(payload["packs"]):
            _validate_pack(pack, f"{path}.packs[{index}]", result)
    return result


def require_valid_domain_pack_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_domain_pack_catalog(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_pack(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("kind", "pack_id", "domain", "description", "integration_boundary", "truth_standard_policy"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("kind") != "domain_pack":
        result.add(f"{path}.kind", "must be 'domain_pack'")
    if payload.get("truth_standard_policy") != "global_only":
        result.add(f"{path}.truth_standard_policy", "must be global_only")
    for key in (
        "suggested_question_intents",
        "risk_signals",
        "failure_taxonomy",
        "context_profile_refs",
        "tool_recipes",
        "skill_refs",
        "manifest_refs",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    for key in ("workflow_graph", "lane_policy", "artifact_schema", "hpc_interpretation"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
        if isinstance(payload.get(key), dict) and "orientation_only" in payload[key]:
            _require_bool_value(payload[key].get("orientation_only"), True, f"{path}.{key}.orientation_only", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    for key in ("skill_refs", "manifest_refs"):
        for index, ref in enumerate(payload.get(key) or []):
            if isinstance(ref, dict) and "orientation_only" in ref:
                _require_bool_value(ref.get("orientation_only"), True, f"{path}.{key}[{index}].orientation_only", result)


def _require_count(payload: dict[str, Any], key: str, path: str, result: ContractResult) -> None:
    if not isinstance(payload.get(key), int) or payload[key] < 0:
        result.add(f"{path}.{key}", "must be a non-negative integer")
