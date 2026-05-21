"""Contracts for host hook installation fixture payloads."""

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
from brain.v5.hook_protocol_contracts import validate_codex_hook_bridge, validate_opencode_plugin_bridge


def validate_codex_hook_installation(
    payload: dict[str, Any],
    *,
    path: str = "codex_hook_installation",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    expected_values = {
        "kind": "codex_hook_installation",
        "runtime": "codex",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "explicit_guard_calls",
    }
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    for key, value in expected_values.items():
        if payload.get(key) != value:
            result.add(f"{path}.{key}", f"must be {value!r}")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("fixture_installer_available"), True, f"{path}.fixture_installer_available", result)
    if not isinstance(payload.get("native_installer_available"), bool):
        result.add(f"{path}.native_installer_available", "must be a boolean")
    for key in ("path", "bridge_path", "bridge_payload_path"):
        _require_nonempty_str(payload, key, path, result)

    bridge = payload.get("bridge")
    if isinstance(bridge, dict):
        bridge_result = validate_codex_hook_bridge({**bridge, "ok": True}, path=f"{path}.bridge")
        result.issues.extend(bridge_result.issues)
    else:
        _require_mapping(bridge, f"{path}.bridge", result)

    fixture = payload.get("fixture")
    hooks_file = payload.get("hooks")
    if fixture is None and hooks_file is None:
        result.add(path, "must include either fixture or native hooks payload")
    if isinstance(fixture, dict):
        if fixture.get("kind") != "codex_hook_installation_fixture":
            result.add(f"{path}.fixture.kind", "must be 'codex_hook_installation_fixture'")
        _require_bool_value(
            fixture.get("summary_inputs_trusted"),
            False,
            f"{path}.fixture.summary_inputs_trusted",
            result,
        )
        hooks = fixture.get("hooks")
        _require_mapping(hooks, f"{path}.fixture.hooks", result)
        if isinstance(hooks, dict):
            _validate_pre_tool_hook(hooks.get("pre_tool"), f"{path}.fixture.hooks.pre_tool", result)
            _validate_post_tool_hook(hooks.get("post_tool"), f"{path}.fixture.hooks.post_tool", result)
    elif fixture is not None:
        _require_mapping(fixture, f"{path}.fixture", result)
    if isinstance(hooks_file, dict):
        _validate_codex_hooks_file(hooks_file, f"{path}.hooks", result)
        for key in ("created", "merged"):
            if not isinstance(payload.get(key), bool):
                result.add(f"{path}.{key}", "must be a boolean")
        if not isinstance(payload.get("added_hooks"), int) or payload.get("added_hooks") < 0:
            result.add(f"{path}.added_hooks", "must be a non-negative integer")
        _require_nonempty_str(payload, "native_hooks_path", path, result)
    elif hooks_file is not None:
        _require_mapping(hooks_file, f"{path}.hooks", result)
    return result


def require_valid_codex_hook_installation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_codex_hook_installation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_opencode_hook_installation(
    payload: dict[str, Any],
    *,
    path: str = "opencode_hook_installation",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    expected_values = {
        "kind": "opencode_hook_installation",
        "runtime": "opencode",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": "plugin_bridge",
    }
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    for key, value in expected_values.items():
        if payload.get(key) != value:
            result.add(f"{path}.{key}", f"must be {value!r}")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("fixture_installer_available"), True, f"{path}.fixture_installer_available", result)
    if not isinstance(payload.get("native_installer_available"), bool):
        result.add(f"{path}.native_installer_available", "must be a boolean")
    for key in ("path", "bridge_path", "bridge_payload_path"):
        _require_nonempty_str(payload, key, path, result)

    bridge = payload.get("bridge")
    if isinstance(bridge, dict):
        bridge_result = validate_opencode_plugin_bridge({**bridge, "ok": True}, path=f"{path}.bridge")
        result.issues.extend(bridge_result.issues)
    else:
        _require_mapping(bridge, f"{path}.bridge", result)

    fixture = payload.get("fixture")
    plugin = payload.get("plugin")
    if fixture is None and plugin is None:
        result.add(path, "must include either fixture or native plugin payload")
    if isinstance(fixture, dict):
        if fixture.get("kind") != "opencode_hook_installation_fixture":
            result.add(f"{path}.fixture.kind", "must be 'opencode_hook_installation_fixture'")
        _require_bool_value(
            fixture.get("summary_inputs_trusted"),
            False,
            f"{path}.fixture.summary_inputs_trusted",
            result,
        )
        hooks = fixture.get("plugin_hooks")
        _require_mapping(hooks, f"{path}.fixture.plugin_hooks", result)
        if isinstance(hooks, dict):
            _validate_pre_tool_hook(hooks.get("pre_tool"), f"{path}.fixture.plugin_hooks.pre_tool", result)
            _validate_post_tool_hook(hooks.get("post_tool"), f"{path}.fixture.plugin_hooks.post_tool", result)
    elif fixture is not None:
        _require_mapping(fixture, f"{path}.fixture", result)
    if isinstance(plugin, dict):
        if plugin.get("kind") != "opencode_local_plugin":
            result.add(f"{path}.plugin.kind", "must be 'opencode_local_plugin'")
        _require_bool_value(
            plugin.get("summary_inputs_trusted"),
            False,
            f"{path}.plugin.summary_inputs_trusted",
            result,
        )
        lifecycle_events = plugin.get("lifecycle_events")
        _require_list(lifecycle_events, f"{path}.plugin.lifecycle_events", result)
        if isinstance(lifecycle_events, list) and lifecycle_events != ["tool.execute.before", "tool.execute.after"]:
            result.add(f"{path}.plugin.lifecycle_events", "must be ['tool.execute.before', 'tool.execute.after']")
        _validate_pre_tool_hook(plugin.get("pre_tool"), f"{path}.plugin.pre_tool", result)
        _validate_post_tool_hook(plugin.get("post_tool"), f"{path}.plugin.post_tool", result)
        for key in ("created", "changed"):
            if not isinstance(payload.get(key), bool):
                result.add(f"{path}.{key}", "must be a boolean")
        _require_nonempty_str(payload, "plugin_path", path, result)
    elif plugin is not None:
        _require_mapping(plugin, f"{path}.plugin", result)
    return result


def require_valid_opencode_hook_installation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_opencode_hook_installation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_runtime_hook_installation_audit(
    payload: dict[str, Any],
    *,
    path: str = "runtime_hook_installation_audit",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result
    expected_values = {
        "kind": "runtime_hook_installation_audit",
        "truth_source": "runtime_files",
    }
    for key, value in expected_values.items():
        if payload.get(key) != value:
            result.add(f"{path}.{key}", f"must be {value!r}")
    if payload.get("runtime") not in {"codex", "claude_code", "opencode"}:
        result.add(f"{path}.runtime", "must be a supported runtime")
    if payload.get("status") not in {"installed", "partial", "missing", "conflict"}:
        result.add(f"{path}.status", "must be installed, partial, missing, or conflict")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_list(payload.get("checked_paths"), f"{path}.checked_paths", result)
    _require_list(payload.get("findings"), f"{path}.findings", result)
    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    findings = payload.get("findings")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            _validate_install_audit_finding(finding, f"{path}.findings[{index}]", result)
    return result


def require_valid_runtime_hook_installation_audit(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_runtime_hook_installation_audit(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_pre_tool_hook(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("lifecycle_event") != "pre_tool":
        result.add(f"{path}.lifecycle_event", "must be 'pre_tool'")
    if payload.get("stdin") != "<platform-event-json>":
        result.add(f"{path}.stdin", "must be '<platform-event-json>'")
    if payload.get("output_kind") != "pre_tool_policy_decision":
        result.add(f"{path}.output_kind", "must be 'pre_tool_policy_decision'")
    _require_bool_value(payload.get("may_block"), True, f"{path}.may_block", result)
    _require_nonempty_str(payload, "cwd", path, result)
    _require_list(payload.get("argv"), f"{path}.argv", result)
    argv = payload.get("argv")
    if isinstance(argv, list):
        for token in ("hooks/aitp_v5_adapter_event_runner.py", "--bridge-path"):
            if token not in argv:
                result.add(f"{path}.argv", f"must include {token!r}")


def _validate_post_tool_hook(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("lifecycle_event") != "post_tool":
        result.add(f"{path}.lifecycle_event", "must be 'post_tool'")
    if payload.get("stdin") != "<platform-event-json>":
        result.add(f"{path}.stdin", "must be '<platform-event-json>'")
    if payload.get("output_kind") != "hook_trace_event_record":
        result.add(f"{path}.output_kind", "must be 'hook_trace_event_record'")
    if payload.get("state_mutation") != "append_trace_event":
        result.add(f"{path}.state_mutation", "must be 'append_trace_event'")
    _require_bool_value(payload.get("may_block"), False, f"{path}.may_block", result)
    _require_nonempty_str(payload, "cwd", path, result)
    _require_list(payload.get("argv"), f"{path}.argv", result)
    argv = payload.get("argv")
    if isinstance(argv, list):
        for token in ("hooks/aitp_v5_adapter_event_runner.py", "post-tool"):
            if token not in argv:
                result.add(f"{path}.argv", f"must include {token!r}")


def _validate_codex_hooks_file(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    hooks = payload.get("hooks")
    _require_mapping(hooks, f"{path}.hooks", result)
    if not isinstance(hooks, dict):
        return
    _validate_codex_native_event_list(hooks.get("PreToolUse"), f"{path}.hooks.PreToolUse", "pre-tool", result)
    _validate_codex_native_event_list(hooks.get("PostToolUse"), f"{path}.hooks.PostToolUse", "post-tool", result)


def _validate_codex_native_event_list(payload: Any, path: str, command_token: str, result: ContractResult) -> None:
    _require_list(payload, path, result)
    if not isinstance(payload, list) or not payload:
        return
    for index, event in enumerate(payload):
        _require_mapping(event, f"{path}[{index}]", result)
        if not isinstance(event, dict):
            continue
        event_hooks = event.get("hooks")
        _require_list(event_hooks, f"{path}[{index}].hooks", result)
        if not isinstance(event_hooks, list):
            continue
        if any(
            isinstance(hook, dict)
            and hook.get("type") == "command"
            and "hooks/aitp_v5_adapter_event_runner.py" in str(hook.get("command", ""))
            and command_token in str(hook.get("command", ""))
            for hook in event_hooks
        ):
            return
    result.add(path, f"must include AITP {command_token!r} command hook")


def _validate_install_audit_finding(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "path", path, result)
    if not isinstance(payload.get("exists"), bool):
        result.add(f"{path}.exists", "must be a boolean")
    if payload.get("status") not in {"installed", "partial", "missing", "conflict"}:
        result.add(f"{path}.status", "must be installed, partial, missing, or conflict")
    _require_list(payload.get("expected"), f"{path}.expected", result)
    _require_list(payload.get("observed"), f"{path}.observed", result)
    _require_list(payload.get("messages"), f"{path}.messages", result)
    _require_bool_value(payload.get("runtime_metadata_only"), True, f"{path}.runtime_metadata_only", result)
