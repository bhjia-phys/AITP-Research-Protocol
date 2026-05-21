"""Runtime hook protocol contracts for AITP v5 adapter packets."""

from __future__ import annotations

from typing import Any

from brain.v5.adapter_protocols import mandatory_gate_protocols, mandatory_hook_protocols
from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_level,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)
from brain.v5.hook_entrypoint_schemas import pre_tool_event_platform_schema, pre_tool_policy_input_schema


def validate_runtime_hook_protocols(payload: Any, path: str, result: ContractResult) -> None:
    """Validate lifecycle hook metadata advertised to runtime adapters."""

    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    for hook_name, expected_protocol in mandatory_hook_protocols().items():
        protocol = payload.get(hook_name)
        _require_mapping(protocol, f"{path}.{hook_name}", result)
        if not isinstance(protocol, dict):
            continue

        for key in ("lifecycle_event", "output_kind", "state_mutation"):
            if protocol.get(key) != expected_protocol[key]:
                result.add(f"{path}.{hook_name}.{key}", f"must be {expected_protocol[key]!r}")

        for key in ("command", "required_inputs"):
            _require_list(protocol.get(key), f"{path}.{hook_name}.{key}", result)
            if isinstance(protocol.get(key), list) and protocol[key] != expected_protocol[key]:
                result.add(f"{path}.{hook_name}.{key}", f"must be {expected_protocol[key]!r}")

        _require_bool_value(
            protocol.get("may_block"),
            expected_protocol["may_block"],
            f"{path}.{hook_name}.may_block",
            result,
        )
        if protocol.get("block_exit_code") != expected_protocol["block_exit_code"]:
            result.add(
                f"{path}.{hook_name}.block_exit_code",
                f"must be {expected_protocol['block_exit_code']!r}",
            )
        _require_bool_value(
            protocol.get("summary_inputs_trusted"),
            expected_protocol["summary_inputs_trusted"],
            f"{path}.{hook_name}.summary_inputs_trusted",
            result,
        )


def validate_runtime_hook_installation(
    payload: Any,
    path: str,
    runtime: Any,
    runtime_hook_protocols: Any,
    result: ContractResult,
) -> None:
    """Validate runtime hook installation metadata against hook protocols."""

    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if not isinstance(runtime, str) or not isinstance(runtime_hook_protocols, dict):
        return

    from brain.v5.hook_install_templates import build_runtime_hook_installation

    expected = build_runtime_hook_installation(runtime, runtime_hook_protocols)
    if payload != expected:
        result.add(path, "must match build_runtime_hook_installation(runtime, runtime_hook_protocols)")


def validate_codex_hook_bridge(
    payload: dict[str, Any],
    *,
    path: str = "codex_hook_bridge",
) -> ContractResult:
    """Validate the public Codex hook bridge write payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "codex_hook_bridge":
        result.add(f"{path}.kind", "must be 'codex_hook_bridge'")
    if payload.get("runtime") != "codex":
        result.add(f"{path}.runtime", "must be 'codex'")
    if payload.get("source_protocol_field") != "runtime_hook_installation":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_hook_installation'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_kernel_state") is not False:
        result.add(f"{path}.can_update_kernel_state", "must be false")
    _validate_pre_tool_policy_entrypoint(
        payload.get("pre_tool_policy_entrypoint"),
        f"{path}.pre_tool_policy_entrypoint",
        result,
    )
    _validate_pre_tool_event_entrypoint(
        payload.get("pre_tool_event_entrypoint"),
        f"{path}.pre_tool_event_entrypoint",
        result,
    )
    _validate_gate_protocols(payload.get("gate_protocols"), f"{path}.gate_protocols", result)

    for key in ("installation_mode", "path"):
        _require_nonempty_str(payload, key, path, result)
    if not isinstance(payload.get("native_installer_available"), bool):
        result.add(f"{path}.native_installer_available", "must be a boolean")

    _require_list(payload.get("guard_calls"), f"{path}.guard_calls", result)
    if isinstance(payload.get("guard_calls"), list):
        for index, guard_call in enumerate(payload["guard_calls"]):
            _validate_codex_guard_call(guard_call, f"{path}.guard_calls[{index}]", result)

    return result


def require_valid_codex_hook_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a Codex hook bridge payload or raise a contract error."""

    result = validate_codex_hook_bridge(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_opencode_plugin_bridge(
    payload: dict[str, Any],
    *,
    path: str = "opencode_plugin_bridge",
) -> ContractResult:
    """Validate the public OpenCode plugin bridge write payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "opencode_plugin_bridge":
        result.add(f"{path}.kind", "must be 'opencode_plugin_bridge'")
    if payload.get("runtime") != "opencode":
        result.add(f"{path}.runtime", "must be 'opencode'")
    if payload.get("source_protocol_field") != "runtime_hook_installation":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_hook_installation'")
    if payload.get("installation_mode") != "plugin_bridge":
        result.add(f"{path}.installation_mode", "must be 'plugin_bridge'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    if not isinstance(payload.get("native_installer_available"), bool):
        result.add(f"{path}.native_installer_available", "must be a boolean")
    _require_nonempty_str(payload, "path", path, result)
    _require_mapping(payload.get("plugin_bridge"), f"{path}.plugin_bridge", result)
    bridge = payload.get("plugin_bridge")
    if isinstance(bridge, dict):
        if bridge.get("persistence_entrypoint") != "aitp_v5_persist_hook_trace_event":
            result.add(f"{path}.plugin_bridge.persistence_entrypoint", "must be 'aitp_v5_persist_hook_trace_event'")
        _validate_pre_tool_policy_entrypoint(
            bridge.get("pre_tool_policy_entrypoint"),
            f"{path}.plugin_bridge.pre_tool_policy_entrypoint",
            result,
        )
        _validate_pre_tool_event_entrypoint(
            bridge.get("pre_tool_event_entrypoint"),
            f"{path}.plugin_bridge.pre_tool_event_entrypoint",
            result,
        )
        _validate_gate_protocols(bridge.get("gate_protocols"), f"{path}.plugin_bridge.gate_protocols", result)
        _require_list(bridge.get("lifecycle_calls"), f"{path}.plugin_bridge.lifecycle_calls", result)
        if isinstance(bridge.get("lifecycle_calls"), list):
            for index, call in enumerate(bridge["lifecycle_calls"]):
                _validate_opencode_lifecycle_call(call, f"{path}.plugin_bridge.lifecycle_calls[{index}]", result)
    return result


def require_valid_opencode_plugin_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_opencode_plugin_bridge(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_claude_code_hook_settings(
    payload: dict[str, Any],
    *,
    path: str = "claude_code_hook_settings",
) -> ContractResult:
    """Validate generated Claude Code hook settings metadata."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "claude_code_hook_settings":
        result.add(f"{path}.kind", "must be 'claude_code_hook_settings'")
    if payload.get("runtime") != "claude_code":
        result.add(f"{path}.runtime", "must be 'claude_code'")
    if payload.get("source_protocol_field") != "runtime_hook_installation":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_hook_installation'")
    if payload.get("installation_mode") != "native_lifecycle_hooks":
        result.add(f"{path}.installation_mode", "must be 'native_lifecycle_hooks'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_write_trace_events"), True, f"{path}.can_write_trace_events", result)
    for key in ("path",):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("events"), f"{path}.events", result)
    _require_mapping(payload.get("settings"), f"{path}.settings", result)
    return result


def require_valid_claude_code_hook_settings(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_claude_code_hook_settings(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_claude_code_hook_installation(
    payload: dict[str, Any],
    *,
    path: str = "claude_code_hook_installation",
) -> ContractResult:
    """Validate a safe merge/install result for Claude Code hook settings."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "claude_code_hook_installation":
        result.add(f"{path}.kind", "must be 'claude_code_hook_installation'")
    if payload.get("settings_kind") != "claude_code_hook_settings":
        result.add(f"{path}.settings_kind", "must be 'claude_code_hook_settings'")
    if payload.get("runtime") != "claude_code":
        result.add(f"{path}.runtime", "must be 'claude_code'")
    if payload.get("source_protocol_field") != "runtime_hook_installation":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_hook_installation'")
    if payload.get("installation_mode") != "native_lifecycle_hooks":
        result.add(f"{path}.installation_mode", "must be 'native_lifecycle_hooks'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("can_write_trace_events"), True, f"{path}.can_write_trace_events", result)
    for key in ("created", "merged"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if not isinstance(payload.get("added_hooks"), int) or payload.get("added_hooks") < 0:
        result.add(f"{path}.added_hooks", "must be a non-negative integer")
    _require_nonempty_str(payload, "path", path, result)
    _require_list(payload.get("events"), f"{path}.events", result)
    _require_mapping(payload.get("settings"), f"{path}.settings", result)
    return result


def require_valid_claude_code_hook_installation(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_claude_code_hook_installation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_hook_trace_event_payload(payload: Any, *, path: str = "hook_trace_event") -> ContractResult:
    """Validate stdout emitted by the post-tool shell hook before persistence."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("kind") != "hook_trace_event":
        result.add(f"{path}.kind", "must be 'hook_trace_event'")
    if payload.get("hook_name") != "post_tool":
        result.add(f"{path}.hook_name", "must be 'post_tool'")
    if payload.get("exit_code") != 0:
        result.add(f"{path}.exit_code", "must be 0")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _validate_trace_event_payload(payload.get("event"), f"{path}.event", result)
    return result


def require_valid_hook_trace_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_hook_trace_event_payload(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_hook_trace_event_record(
    payload: dict[str, Any],
    *,
    path: str = "hook_trace_event_record",
) -> ContractResult:
    """Validate a persisted hook trace-event write result."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "hook_trace_event_record":
        result.add(f"{path}.kind", "must be 'hook_trace_event_record'")
    if payload.get("source_kind") != "hook_trace_event":
        result.add(f"{path}.source_kind", "must be 'hook_trace_event'")
    if payload.get("source_hook") != "post_tool":
        result.add(f"{path}.source_hook", "must be 'post_tool'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_bool_value(payload.get("writes_trace_event"), True, f"{path}.writes_trace_event", result)
    for key in ("event_id", "session_id", "topic_id", "event_type", "risk_level", "trace_path"):
        _require_nonempty_str(payload, key, path, result)
    return result


def require_valid_hook_trace_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_hook_trace_event_record(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_pre_tool_policy_decision(
    payload: dict[str, Any],
    *,
    path: str = "pre_tool_policy_decision",
) -> ContractResult:
    """Validate a public pre-tool decision without granting state mutation authority."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "hook_decision":
        result.add(f"{path}.kind", "must be 'hook_decision'")
    if payload.get("hook_name") != "pre_tool":
        result.add(f"{path}.hook_name", "must be 'pre_tool'")
    for key in ("action", "session_id", "claim_id", "message"):
        _require_nonempty_str(payload, key, path, result)
    _require_level(payload.get("risk_level"), f"{path}.risk_level", result)
    mode = payload.get("mode")
    if mode not in {"log", "warn", "block"}:
        result.add(f"{path}.mode", "must be one of log, warn, block")
    if not isinstance(payload.get("block"), bool):
        result.add(f"{path}.block", "must be a boolean")
    elif mode == "block" and payload.get("block") is not True:
        result.add(f"{path}.block", "must be true when mode is block")
    elif mode in {"log", "warn"} and payload.get("block") is not False:
        result.add(f"{path}.block", "must be false when mode is log or warn")
    expected_exit = 2 if payload.get("block") is True else 0
    if payload.get("exit_code") != expected_exit:
        result.add(f"{path}.exit_code", f"must be {expected_exit}")
    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_list(payload.get("validation_contract_ids"), f"{path}.validation_contract_ids", result)
    if isinstance(payload.get("validation_contract_ids"), list):
        for index, contract_id in enumerate(payload["validation_contract_ids"]):
            if not isinstance(contract_id, str) or not contract_id.strip():
                result.add(f"{path}.validation_contract_ids[{index}]", "must be a non-empty string")
    _require_list(payload.get("policy_reasons"), f"{path}.policy_reasons", result)
    if isinstance(payload.get("policy_reasons"), list):
        for index, reason in enumerate(payload["policy_reasons"]):
            _validate_policy_reason(reason, f"{path}.policy_reasons[{index}]", result)
    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    if isinstance(payload.get("required_actions"), list):
        for index, action in enumerate(payload["required_actions"]):
            if not isinstance(action, str) or not action.strip():
                result.add(f"{path}.required_actions[{index}]", "must be a non-empty string")
    return result


def require_valid_pre_tool_policy_decision(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_pre_tool_policy_decision(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_codex_guard_call(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    for key in ("hook_name", "when", "command", "output_kind", "state_mutation"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("required_inputs"), f"{path}.required_inputs", result)
    if not isinstance(payload.get("may_block"), bool):
        result.add(f"{path}.may_block", "must be a boolean")


def _validate_opencode_lifecycle_call(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("hook_name", "lifecycle_event", "command", "output_kind", "state_mutation"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("required_inputs"), f"{path}.required_inputs", result)
    if not isinstance(payload.get("may_block"), bool):
        result.add(f"{path}.may_block", "must be a boolean")


def _validate_pre_tool_policy_entrypoint(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    expected = {
        "cli": "aitp-v5 policy pre-tool <args>",
        "mcp": "aitp_v5_evaluate_pre_tool_policy",
        "surface": "pre_tool_policy_decision",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "input_schema": pre_tool_policy_input_schema(),
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            result.add(f"{path}.{key}", f"must be {value!r}")


def _validate_pre_tool_event_entrypoint(payload: Any, path: str, result: ContractResult) -> None:
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


def _validate_gate_protocols(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("source_protocol_field") != "runtime_gate_protocols":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_gate_protocols'")
    for action, expected in mandatory_gate_protocols().items():
        protocol = payload.get(action)
        _require_mapping(protocol, f"{path}.{action}", result)
        if isinstance(protocol, dict) and protocol != expected:
            result.add(f"{path}.{action}", "must match mandatory runtime gate protocol")


def _validate_policy_reason(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("policy_id", "severity", "message"):
        _require_nonempty_str(payload, key, path, result)


def _validate_trace_event_payload(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "trace_event":
        result.add(f"{path}.kind", "must be 'trace_event'")
    for key in ("event_id", "session_id", "topic_id", "event_type", "risk_level"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("payload"), f"{path}.payload", result)
