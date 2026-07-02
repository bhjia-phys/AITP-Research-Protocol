"""Contracts for project-scope external domain skill shim manifests."""

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


_STATE_EFFECTS = {"read_only_preview", "project_skill_shim_write"}
_SHIM_STATUSES = {
    "would_create",
    "would_update",
    "created",
    "updated",
    "up_to_date",
    "blocked_existing",
}
_FORBIDDEN_USES = (
    "evidence_support",
    "source_support_result",
    "validation_result",
    "claim_trust_update",
    "trust_apply",
    "external_skill_content_vendoring",
)


def validate_domain_skill_shim_manifest(
    payload: dict[str, Any],
    *,
    path: str = "domain_skill_shim_manifest",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "domain_skill_shim_manifest":
        result.add(f"{path}.kind", "must be 'domain_skill_shim_manifest'")
    if payload.get("truth_source") != "builtin_domain_pack_skill_refs":
        result.add(f"{path}.truth_source", "must be 'builtin_domain_pack_skill_refs'")
    if payload.get("state_effect") not in _STATE_EFFECTS:
        result.add(f"{path}.state_effect", "must be read_only_preview or project_skill_shim_write")
    for key in ("workspace_base", "output_root", "relative_output_root", "state_effect"):
        _require_nonempty_str(payload, key, path, result)
    for key in (
        "requested_pack_ids",
        "selected_pack_ids",
        "shims",
        "required_followup_for_use",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_count(payload, "selected_pack_count", path, result)
    _require_count(payload, "shim_count", path, result)
    _require_count(payload, "write_count", path, result)
    _require_count(payload, "blocked_count", path, result)
    if isinstance(payload.get("selected_pack_ids"), list) and payload.get("selected_pack_count") != len(payload["selected_pack_ids"]):
        result.add(f"{path}.selected_pack_count", "must equal selected_pack_ids length")
    if isinstance(payload.get("shims"), list):
        if payload.get("shim_count") != len(payload["shims"]):
            result.add(f"{path}.shim_count", "must equal shims length")
        for index, shim in enumerate(payload["shims"]):
            _validate_shim(shim, f"{path}.shims[{index}]", result)
    _validate_generation_policy(payload.get("generation_policy"), f"{path}.generation_policy", result)
    for key in ("apply", "overwrite", "writes_project_files"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    for key, expected in (
        ("summary_inputs_trusted", False),
        ("orientation_only", True),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
        ("can_create_evidence", False),
        ("can_materialize_external_skill_content", False),
        ("external_skill_content_copied", False),
    ):
        _require_bool_value(payload.get(key), expected, f"{path}.{key}", result)
    if payload.get("state_effect") == "read_only_preview":
        _require_bool_value(payload.get("writes_project_files"), False, f"{path}.writes_project_files", result)
    if payload.get("state_effect") == "project_skill_shim_write":
        _require_bool_value(payload.get("apply"), True, f"{path}.apply", result)
    return result


def require_valid_domain_skill_shim_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_domain_skill_shim_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_shim(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("kind", "shim_name", "skill_id", "target_path", "content_hash", "status"):
        _require_nonempty_str(value, key, path, result)
    if value.get("kind") != "domain_skill_shim":
        result.add(f"{path}.kind", "must be 'domain_skill_shim'")
    if value.get("status") not in _SHIM_STATUSES:
        result.add(f"{path}.status", f"must be one of {sorted(_SHIM_STATUSES)}")
    for key in ("pack_ids", "domain_ids", "skill_refs"):
        _require_list(value.get(key), f"{path}.{key}", result)
        if isinstance(value.get(key), list) and not value[key]:
            result.add(f"{path}.{key}", "must not be empty")
    for key in (
        "overwrite",
        "exists",
        "content_matches_existing",
        "write_executed",
        "write_blocked",
        "summary_inputs_trusted",
        "orientation_only",
        "can_update_claim_trust",
        "copies_external_skill_content",
    ):
        if not isinstance(value.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(value.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(value.get("copies_external_skill_content"), False, f"{path}.copies_external_skill_content", result)


def _validate_generation_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_nonempty_str(value, "default_output_root", path, result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    for key in (
        "writes_only_project_shims",
        "requires_explicit_apply",
        "overwrite_requires_flag",
    ):
        _require_bool_value(value.get(key), True, f"{path}.{key}", result)
    _require_bool_value(value.get("copies_external_skill_content"), False, f"{path}.copies_external_skill_content", result)
    forbidden = value.get("forbidden_uses") if isinstance(value.get("forbidden_uses"), list) else []
    for item in _FORBIDDEN_USES:
        if item not in forbidden:
            result.add(f"{path}.forbidden_uses", f"must include {item!r}")


def _require_count(payload: dict[str, Any], key: str, path: str, result: ContractResult) -> None:
    if not isinstance(payload.get(key), int) or payload[key] < 0:
        result.add(f"{path}.{key}", "must be a non-negative integer")
