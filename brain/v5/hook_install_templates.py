"""Runtime hook installation templates derived from v5 hook protocols."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from brain.v5.hook_bridge_markdown import codex_bridge_markdown, opencode_bridge_markdown
from brain.v5.hook_runner_payloads import build_pre_tool_event_runner


_INSTALLATION_MODES = {
    "codex": "explicit_guard_calls",
    "claude_code": "native_lifecycle_hooks",
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
}


def build_runtime_hook_installation(runtime: str, runtime_hook_protocols: dict[str, Any]) -> dict[str, Any]:
    """Build runtime-facing hook installation metadata from hook protocols."""

    normalized_runtime = _normalize_runtime(runtime)
    return {
        "kind": "runtime_hook_installation_template",
        "runtime": normalized_runtime,
        "source_protocol_field": "runtime_hook_protocols",
        "installation_mode": _INSTALLATION_MODES[normalized_runtime],
        "native_installer_available": False,
        "summary_inputs_trusted": False,
        "hooks": [
            _hook_template(hook_name, runtime_hook_protocols[hook_name])
            for hook_name in ("pre_commit", "pre_tool", "post_tool")
        ],
        "adapter_rule": "derive_commands_from_runtime_hook_protocols",
    }


def write_codex_hook_bridge(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    session_id: str = "<session-id>",
) -> dict[str, Any]:
    """Write Codex guard-call instructions derived from hook installation metadata."""

    bridge_path = Path(path)
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
        "gate_protocols": _gate_protocol_payload(runtime_gate_protocols),
        "path": str(bridge_path),
        "payload_path": str(_payload_sidecar_path(bridge_path)),
        "pre_tool_event_runner": build_pre_tool_event_runner("codex", session_id, _payload_sidecar_path(bridge_path)),
        "guard_calls": guard_calls,
    }
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(codex_bridge_markdown(bridge), encoding="utf-8")
    _write_payload_sidecar(bridge)
    return bridge


def install_codex_hook_fixture(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    workspace_base: str,
    session_id: str,
    bridge_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write a Codex stdin-runner hook fixture plus its bridge sidecar."""

    fixture_path = Path(path)
    resolved_bridge_path = Path(bridge_path) if bridge_path else fixture_path.parent / "AITP_V5_HOOK_BRIDGE.md"
    bridge = write_codex_hook_bridge(
        resolved_bridge_path,
        installation,
        runtime_gate_protocols,
        session_id=session_id,
    )
    pre_tool_hook = {
        "lifecycle_event": "pre_tool",
        "command_kind": "stdin_json_runner",
        "argv": _codex_stdin_runner_argv(
            workspace_base=workspace_base,
            session_id=session_id,
            bridge_payload_path=bridge["payload_path"],
        ),
        "stdin": "<platform-event-json>",
        "output_kind": "pre_tool_policy_decision",
        "may_block": True,
        "state_mutation": "none",
    }
    fixture = {
        "kind": "codex_hook_installation_fixture",
        "runtime": "codex",
        "hooks": {"pre_tool": pre_tool_hook},
        "truth_rule": "fixture is runtime metadata only; typed records remain authoritative",
        "summary_inputs_trusted": False,
    }
    payload = {
        "kind": "codex_hook_installation",
        "runtime": "codex",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": False,
        "fixture_installer_available": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "path": str(fixture_path),
        "bridge_path": bridge["path"],
        "bridge_payload_path": bridge["payload_path"],
        "bridge": bridge,
        "fixture": fixture,
    }
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def write_opencode_plugin_bridge(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    session_id: str = "<session-id>",
) -> dict[str, Any]:
    """Write OpenCode plugin bridge instructions derived from hook installation metadata."""

    bridge_path = Path(path)
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
        "plugin_bridge": {
            "setup": ["load AITP skills", "connect AITP MCP server", "read v5 adapter packet"],
            "lifecycle_calls": lifecycle_calls,
            "pre_tool_policy_entrypoint": deepcopy(_PRE_TOOL_POLICY_ENTRYPOINT),
            "pre_tool_event_entrypoint": deepcopy(_PRE_TOOL_EVENT_ENTRYPOINT),
            "pre_tool_event_runner": build_pre_tool_event_runner(
                "opencode",
                session_id,
                _payload_sidecar_path(bridge_path),
            ),
            "gate_protocols": _gate_protocol_payload(runtime_gate_protocols),
            "persistence_entrypoint": "aitp_v5_persist_hook_trace_event",
            "truth_rule": "generated bridge is orientation-only; typed records remain authoritative",
        },
    }
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(opencode_bridge_markdown(bridge), encoding="utf-8")
    _write_payload_sidecar(bridge)
    return bridge


def write_claude_code_hook_settings(
    path: str | Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    """Write Claude Code hook settings derived from hook installation metadata."""

    settings_path = Path(path)
    payload = _claude_settings_payload(settings_path, installation, workspace_base=workspace_base, session_id=session_id)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(payload["settings"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def install_claude_code_hook_settings(
    path: str | Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    """Merge AITP v5 Claude hooks into an existing settings file without clobbering it."""

    settings_path = Path(path)
    generated = _claude_settings_payload(
        settings_path,
        installation,
        workspace_base=workspace_base,
        session_id=session_id,
    )
    created = not settings_path.exists()
    merged_settings = _read_claude_settings(settings_path) if not created else {}
    hooks = merged_settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Claude Code settings field 'hooks' must be an object")

    added_hooks = 0
    for event_name, event_hooks in generated["settings"]["hooks"].items():
        current_hooks = hooks.setdefault(event_name, [])
        if not isinstance(current_hooks, list):
            raise ValueError(f"Claude Code settings hooks.{event_name} must be a list")
        for event_hook in event_hooks:
            if event_hook not in current_hooks:
                current_hooks.append(deepcopy(event_hook))
                added_hooks += 1

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(merged_settings, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        **generated,
        "kind": "claude_code_hook_installation",
        "settings_kind": generated["kind"],
        "created": created,
        "merged": True,
        "added_hooks": added_hooks,
        "settings": merged_settings,
    }


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


def _claude_event(matcher: str, command: str) -> dict[str, Any]:
    return {
        "matcher": matcher,
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }


def _claude_settings_payload(
    settings_path: Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    command_base = f'python hooks/aitp_v5_claude_hook.py {{command}} --base "{workspace_base}" --session-id {session_id}'
    settings = {
        "hooks": {
            "PreToolUse": [_claude_event("*", command_base.format(command="pre-tool"))],
            "PostToolUse": [_claude_event("*", command_base.format(command="post-tool"))],
        }
    }
    return {
        "kind": "claude_code_hook_settings",
        "runtime": "claude_code",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": installation["native_installer_available"],
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "path": str(settings_path),
        "events": [
            {"hook_event_name": "PreToolUse", "matcher": "*", "protocol_hook": "pre_tool"},
            {"hook_event_name": "PostToolUse", "matcher": "*", "protocol_hook": "post_tool"},
        ],
        "settings": settings,
    }


def _read_claude_settings(settings_path: Path) -> dict[str, Any]:
    text = settings_path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Claude Code settings must be a JSON object")
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


def _codex_stdin_runner_argv(*, workspace_base: str, session_id: str, bridge_payload_path: str) -> list[str]:
    return [
        "python",
        "hooks/aitp_v5_adapter_event_runner.py",
        "pre-tool",
        "--base",
        workspace_base,
        "--runtime",
        "codex",
        "--session-id",
        session_id,
        "--bridge-path",
        bridge_payload_path,
    ]


def _payload_sidecar_path(bridge_path: Path) -> Path:
    return bridge_path.with_suffix(".json")


def _write_payload_sidecar(bridge: dict[str, Any]) -> None:
    sidecar_path = Path(str(bridge["payload_path"]))
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(
        json.dumps(bridge, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value in _INSTALLATION_MODES:
        return value
    return "codex"
