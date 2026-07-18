"""Runtime hook installation templates derived from v5 hook protocols."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from brain.v5.hook_bridge_markdown import codex_bridge_markdown, opencode_bridge_markdown
from brain.v5.hook_claude_install import install_claude_code_hook_settings, write_claude_code_hook_settings
from brain.v5.hook_entrypoint_schemas import pre_tool_event_platform_schema, pre_tool_policy_input_schema
from brain.v5.hook_routing_mode import (
    HookRoutingMode,
    hook_routing_metadata,
    resolve_installer_hook_routing,
)
from brain.v5.hook_runner_payloads import build_pre_tool_event_runner


_INSTALLATION_MODES = {
    "codex": "explicit_guard_calls",
    "claude_code": "native_lifecycle_hooks",
    "kimi_code": "native_lifecycle_hooks",
    "opencode": "plugin_bridge",
}
_PRE_TOOL_POLICY_ENTRYPOINT = {
    "cli": "aitp-v5 policy pre-tool <args>",
    "mcp": "aitp_v5_evaluate_pre_tool_policy",
    "surface": "pre_tool_policy_decision",
    "truth_source": "typed_records",
    "summary_inputs_trusted": False,
    "can_update_kernel_state": False,
    "can_update_claim_trust": False,
    "input_schema": pre_tool_policy_input_schema(),
}
_PRE_TOOL_EVENT_ENTRYPOINT = {
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


def build_runtime_hook_installation(runtime: str, runtime_hook_protocols: dict[str, Any]) -> dict[str, Any]:
    """Build runtime-facing hook installation metadata from hook protocols."""

    normalized_runtime = _normalize_runtime(runtime)
    from brain.v5.adapter_protocols import mandatory_recording_trigger_protocol

    return {
        "kind": "runtime_hook_installation_template",
        "runtime": normalized_runtime,
        "source_protocol_field": "runtime_hook_protocols",
        "installation_mode": _INSTALLATION_MODES[normalized_runtime],
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "recording_trigger_protocol": mandatory_recording_trigger_protocol(),
        "hooks": [
            _hook_template(hook_name, runtime_hook_protocols[hook_name])
            for hook_name in ("pre_commit", "pre_tool", "post_tool")
        ],
        "adapter_rule": "derive_commands_from_runtime_hook_protocols_and_use_recording_trigger_protocol_for_read_only_navigation",
    }


def write_codex_hook_bridge(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    session_id: str = "",
    routing: HookRoutingMode | None = None,
    project_root: str = "",
    topics_root: str = "",
) -> dict[str, Any]:
    """Write Codex guard-call instructions derived from hook installation metadata."""

    bridge_path = Path(path)
    resolved_routing, routing_metadata = _resolve_hook_routing_context(
        bridge_path,
        routing=routing,
        session_id=session_id,
        project_root=project_root,
        topics_root=topics_root,
    )
    guard_calls = [
        {
            "hook_name": hook["hook_name"],
            "when": _codex_when(hook["hook_name"]),
            "command": _command_string(hook["command"]),
            "required_inputs": deepcopy(hook["required_inputs"]),
            "output_kind": hook["output_kind"],
            "may_block": hook["may_block"],
            "state_mutation": hook["state_mutation"],
        }
        for hook in installation["hooks"]
    ]
    bridge = {
        "kind": "codex_hook_bridge",
        "runtime": "codex",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": installation["native_installer_available"],
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "pre_tool_policy_entrypoint": deepcopy(_PRE_TOOL_POLICY_ENTRYPOINT),
        "pre_tool_event_entrypoint": deepcopy(_PRE_TOOL_EVENT_ENTRYPOINT),
        "recording_trigger_protocol": deepcopy(installation.get("recording_trigger_protocol", {})),
        "gate_protocols": _gate_protocol_payload(runtime_gate_protocols),
        "path": str(bridge_path),
        "payload_path": str(_payload_sidecar_path(bridge_path)),
        **routing_metadata,
        "pre_tool_event_runner": build_pre_tool_event_runner(
            "codex",
            _payload_sidecar_path(bridge_path),
            routing=resolved_routing,
            topics_root=str(routing_metadata["topics_root"]),
            project_root=str(routing_metadata["project_root"]),
        ),
        "guard_calls": guard_calls,
    }
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(codex_bridge_markdown(bridge), encoding="utf-8")
    _write_payload_sidecar(bridge)
    return bridge


def write_opencode_plugin_bridge(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    session_id: str = "",
    routing: HookRoutingMode | None = None,
    project_root: str = "",
    topics_root: str = "",
) -> dict[str, Any]:
    """Write OpenCode plugin bridge instructions derived from hook installation metadata."""

    bridge_path = Path(path)
    resolved_routing, routing_metadata = _resolve_hook_routing_context(
        bridge_path,
        routing=routing,
        session_id=session_id,
        project_root=project_root,
        topics_root=topics_root,
    )
    lifecycle_calls = [
        {
            "hook_name": hook["hook_name"],
            "lifecycle_event": hook["lifecycle_event"],
            "command": _command_string(hook["command"]),
            "required_inputs": deepcopy(hook["required_inputs"]),
            "output_kind": hook["output_kind"],
            "may_block": hook["may_block"],
            "state_mutation": hook["state_mutation"],
        }
        for hook in installation["hooks"]
    ]
    bridge = {
        "kind": "opencode_plugin_bridge",
        "runtime": "opencode",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": installation["native_installer_available"],
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "path": str(bridge_path),
        "payload_path": str(_payload_sidecar_path(bridge_path)),
        **routing_metadata,
        "plugin_bridge": {
            "setup": ["load AITP skills", "connect AITP MCP server", "read v5 adapter packet"],
            "lifecycle_calls": lifecycle_calls,
            "pre_tool_policy_entrypoint": deepcopy(_PRE_TOOL_POLICY_ENTRYPOINT),
            "pre_tool_event_entrypoint": deepcopy(_PRE_TOOL_EVENT_ENTRYPOINT),
            "pre_tool_event_runner": build_pre_tool_event_runner(
                "opencode",
                _payload_sidecar_path(bridge_path),
                routing=resolved_routing,
                topics_root=str(routing_metadata["topics_root"]),
                project_root=str(routing_metadata["project_root"]),
            ),
            **routing_metadata,
            "recording_trigger_protocol": deepcopy(installation.get("recording_trigger_protocol", {})),
            "gate_protocols": _gate_protocol_payload(runtime_gate_protocols),
            "persistence_entrypoint": "aitp_v5_persist_hook_trace_event",
            "truth_rule": "generated bridge is orientation-only; typed records remain authoritative",
        },
    }
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(opencode_bridge_markdown(bridge), encoding="utf-8")
    _write_payload_sidecar(bridge)
    return bridge


def _hook_template(hook_name: str, protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "hook_name": hook_name,
        "lifecycle_event": protocol["lifecycle_event"],
        "command": deepcopy(protocol["command"]),
        "required_inputs": deepcopy(protocol["required_inputs"]),
        "output_kind": protocol["output_kind"],
        "may_block": protocol["may_block"],
        "state_mutation": protocol["state_mutation"],
    }


def _gate_protocol_payload(runtime_gate_protocols: dict[str, Any] | None) -> dict[str, Any]:
    if runtime_gate_protocols is None:
        from brain.v5.adapter_protocols import mandatory_gate_protocols

        runtime_gate_protocols = mandatory_gate_protocols()
    payload = {"source_protocol_field": "runtime_gate_protocols"}
    for action in runtime_gate_protocols:
        payload[action] = deepcopy(runtime_gate_protocols[action])
    return payload


def _codex_when(hook_name: str) -> str:
    if hook_name == "pre_commit":
        return "before committing v5 harness, migration, policy, adapter, or public-surface changes"
    if hook_name == "pre_tool":
        return "before trust-changing, promotion, remote, destructive, or expensive tool actions"
    if hook_name == "post_tool":
        return "after meaningful physics, numerical, code, or literature tool runs with active v5 ids"
    return "when the matching v5 lifecycle event occurs"


def _command_string(command: list[str]) -> str:
    return " ".join(command)


def _payload_sidecar_path(bridge_path: Path) -> Path:
    return bridge_path.with_suffix(".json")


def _write_payload_sidecar(bridge: dict[str, Any]) -> None:
    sidecar_path = Path(str(bridge["payload_path"]))
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(
        json.dumps(bridge, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_hook_routing_context(
    bridge_path: Path,
    *,
    routing: HookRoutingMode | None,
    session_id: str,
    project_root: str,
    topics_root: str,
) -> tuple[HookRoutingMode, dict[str, object]]:
    resolved_routing = resolve_installer_hook_routing(routing, session_id=session_id)
    fallback_root = bridge_path.parent.resolve(strict=False)
    metadata = hook_routing_metadata(
        resolved_routing,
        project_root=project_root or fallback_root,
        topics_root=topics_root or fallback_root,
    )
    return resolved_routing, metadata


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value in _INSTALLATION_MODES:
        return value
    return "codex"
