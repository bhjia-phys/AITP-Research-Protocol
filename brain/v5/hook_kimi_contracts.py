"""Kimi Code hook payload contracts for AITP v5."""

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


def validate_kimi_code_hook_config(
    payload: dict[str, Any],
    *,
    path: str = "kimi_code_hook_config",
) -> ContractResult:
    """Validate generated Kimi Code hook TOML metadata."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "kimi_code_hook_config":
        result.add(f"{path}.kind", "must be 'kimi_code_hook_config'")
    if payload.get("runtime") != "kimi_code":
        result.add(f"{path}.runtime", "must be 'kimi_code'")
    if payload.get("source_protocol_field") != "runtime_hook_installation":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_hook_installation'")
    if payload.get("installation_mode") != "native_lifecycle_hooks":
        result.add(f"{path}.installation_mode", "must be 'native_lifecycle_hooks'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_write_trace_events"), True, f"{path}.can_write_trace_events", result)
    _require_nonempty_str(payload, "path", path, result)
    _require_nonempty_str(payload, "config_text", path, result)
    _validate_kimi_events(payload.get("events"), path, result)
    _validate_config_text(payload.get("config_text"), path, result)
    return result


def require_valid_kimi_code_hook_config(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_kimi_code_hook_config(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_kimi_code_hook_installation(
    payload: dict[str, Any],
    *,
    path: str = "kimi_code_hook_installation",
) -> ContractResult:
    """Validate a safe merge/install result for Kimi Code hook TOML."""

    if not isinstance(payload, dict):
        result = ContractResult()
        _require_mapping(payload, path, result)
        return result
    result = validate_kimi_code_hook_config(
        {**payload, "kind": "kimi_code_hook_config", "ok": payload.get("ok")},
        path=path,
    )
    if payload.get("kind") != "kimi_code_hook_installation":
        result.add(f"{path}.kind", "must be 'kimi_code_hook_installation'")
    if payload.get("config_kind") != "kimi_code_hook_config":
        result.add(f"{path}.config_kind", "must be 'kimi_code_hook_config'")
    for key in ("created", "merged"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if not isinstance(payload.get("added_hooks"), int) or payload.get("added_hooks") < 0:
        result.add(f"{path}.added_hooks", "must be a non-negative integer")
    return result


def require_valid_kimi_code_hook_installation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_kimi_code_hook_installation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_kimi_events(payload: Any, path: str, result: ContractResult) -> None:
    _require_list(payload, f"{path}.events", result)
    if not isinstance(payload, list):
        return
    event_names = [event.get("hook_event_name") for event in payload if isinstance(event, dict)]
    if event_names != ["PreToolUse", "PostToolUse"]:
        result.add(f"{path}.events", "must include PreToolUse and PostToolUse in order")


def _validate_config_text(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, str):
        return
    for token in ("[[hooks]]", "PreToolUse", "PostToolUse", "aitp_v5_kimi_hook.py"):
        if token not in payload:
            result.add(f"{path}.config_text", f"must contain {token!r}")
