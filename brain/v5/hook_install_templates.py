"""Runtime hook installation templates derived from v5 hook protocols."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


_INSTALLATION_MODES = {
    "codex": "explicit_guard_calls",
    "claude_code": "native_lifecycle_hooks",
    "opencode": "plugin_bridge",
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


def write_codex_hook_bridge(path: str | Path, installation: dict[str, Any]) -> dict[str, Any]:
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
        "path": str(bridge_path),
        "guard_calls": guard_calls,
    }
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(_codex_bridge_markdown(bridge), encoding="utf-8")
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


def _codex_bridge_markdown(bridge: dict[str, Any]) -> str:
    lines = [
        "# AITP v5 Codex Hook Bridge",
        "",
        "Generated from `runtime_hook_installation`.",
        "",
        "- truth_source: false",
        "- summary_inputs_trusted=false",
        "- can_update_kernel_state=false",
        "",
        "## Guard Calls",
        "",
    ]
    for guard_call in bridge["guard_calls"]:
        lines.extend(
            [
                f"### {guard_call['hook_name']}",
                "",
                f"- when: {guard_call['when']}",
                f"- output_kind: `{guard_call['output_kind']}`",
                f"- may_block: `{str(guard_call['may_block']).lower()}`",
                f"- state_mutation: `{guard_call['state_mutation']}`",
                "",
                "```powershell",
                guard_call["command"],
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


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


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value in _INSTALLATION_MODES:
        return value
    return "codex"
