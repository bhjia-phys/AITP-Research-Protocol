"""Fail-closed contracts for generated hook routing metadata and argv."""

from __future__ import annotations

from pathlib import Path
import os
import shlex
from typing import Any

from brain.v5.contracts import (
    ContractResult,
    _require_bool_value,
    _require_mapping,
    _require_nonempty_str,
)
from brain.v5.hook_entrypoint_schemas import pre_tool_event_platform_schema
from brain.v5.hook_routing_mode import HOOK_ROUTING_MODES


def validate_hook_routing_metadata(payload: Any, path: str, result: ContractResult) -> None:
    if not isinstance(payload, dict):
        result.add(path, "must be an object")
        return
    mode = payload.get("routing_mode")
    pinned_session_id = payload.get("pinned_session_id")
    if mode not in HOOK_ROUTING_MODES:
        result.add(f"{path}.routing_mode", "must be dynamic, pinned, or pinned_compat")
    if not isinstance(pinned_session_id, str):
        result.add(f"{path}.pinned_session_id", "must be a string")
    elif mode == "dynamic" and pinned_session_id:
        result.add(f"{path}.pinned_session_id", "dynamic routing cannot carry a session pin")
    elif mode in {"pinned", "pinned_compat"} and not pinned_session_id:
        result.add(f"{path}.pinned_session_id", "pinned routing requires a session pin")

    expected_legacy = mode == "pinned_compat"
    _require_bool_value(payload.get("legacy_pinned"), expected_legacy, f"{path}.legacy_pinned", result)
    _require_bool_value(
        payload.get("migration_required"),
        expected_legacy,
        f"{path}.migration_required",
        result,
    )
    _require_bool_value(payload.get("runtime_metadata_only"), True, f"{path}.runtime_metadata_only", result)
    for key in ("project_root", "topics_root"):
        _require_nonempty_str(payload, key, path, result)
        value = payload.get(key)
        if isinstance(value, str) and value and not Path(value).is_absolute():
            result.add(f"{path}.{key}", "must be an absolute path")


def validate_hook_routing_argv(
    argv: Any,
    metadata: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    if not isinstance(argv, list):
        result.add(path, "must be a list")
        return
    expected = {
        "--base": metadata.get("topics_root"),
        "--project-root": metadata.get("project_root"),
        "--routing-mode": metadata.get("routing_mode"),
    }
    for option, value in expected.items():
        if _option_value(argv, option) != value:
            result.add(path, f"{option} must match routing metadata")
    session_value = _option_value(argv, "--session-id")
    expected_session = metadata.get("pinned_session_id") or None
    if session_value != expected_session:
        result.add(path, "--session-id must match routing metadata")


def validate_native_hook_commands(
    events: Any,
    metadata: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    if not isinstance(events, list):
        return
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            result.add(f"{path}[{index}]", "must be an object")
            continue
        command = event.get("command")
        if not isinstance(command, str) or not command:
            result.add(f"{path}[{index}].command", "must be a non-empty string")
            continue
        try:
            argv = [item.strip('"') for item in shlex.split(command, posix=os.name != "nt")]
        except ValueError:
            result.add(f"{path}[{index}].command", "must be a parseable command")
            continue
        validate_hook_routing_argv(argv, metadata, f"{path}[{index}].command", result)


def validate_fixture_hook_routing(
    hooks: dict[str, Any],
    metadata: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    for hook_name in ("pre_tool", "post_tool"):
        hook = hooks.get(hook_name)
        if isinstance(hook, dict):
            validate_hook_routing_argv(
                hook.get("argv"), metadata, f"{path}.{hook_name}.argv", result
            )


def validate_pre_tool_event_entrypoint(
    payload: Any,
    path: str,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    expected = {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "requires_bridge_payload": True,
        "requires_platform_event": True,
        "platform_event_schema": pre_tool_event_platform_schema(),
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            result.add(f"{path}.{key}", f"must be {value!r}")


def validate_pre_tool_event_runner_payload(
    payload: Any,
    metadata: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "pre_tool_event_runner":
        result.add(f"{path}.kind", "must be 'pre_tool_event_runner'")
    validate_hook_routing_metadata(payload, path, result)
    validate_hook_routing_argv(payload.get("argv"), metadata, f"{path}.argv", result)
    nested = payload.get("stdin_runner")
    _require_mapping(nested, f"{path}.stdin_runner", result)
    if isinstance(nested, dict):
        validate_hook_routing_argv(
            nested.get("argv"), metadata, f"{path}.stdin_runner.argv", result
        )


def _option_value(argv: list[Any], option: str) -> Any | None:
    positions = [index for index, value in enumerate(argv) if value == option]
    if len(positions) != 1:
        return None
    index = positions[0]
    if index + 1 >= len(argv):
        return None
    return argv[index + 1]


__all__ = [
    "validate_hook_routing_argv",
    "validate_hook_routing_metadata",
    "validate_fixture_hook_routing",
    "validate_native_hook_commands",
    "validate_pre_tool_event_entrypoint",
    "validate_pre_tool_event_runner_payload",
]
