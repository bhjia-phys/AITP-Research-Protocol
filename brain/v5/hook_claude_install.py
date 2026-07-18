"""Claude Code JSON hook settings generation and safe merge."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from brain.v5.hook_command_line import render_hook_command
from brain.v5.hook_python import stable_python_executable
from brain.v5.hook_routing_mode import (
    HookRoutingMode,
    hook_routing_metadata,
    resolve_installer_hook_routing,
)
from brain.v5.hook_runner_payloads import build_native_lifecycle_hook_argv


def write_claude_code_hook_settings(
    path: str | Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str = "",
    routing: HookRoutingMode | None = None,
    project_root: str = "",
) -> dict[str, Any]:
    settings_path = Path(path)
    resolved_routing, metadata = _routing_context(
        routing,
        session_id=session_id,
        workspace_base=workspace_base,
        project_root=project_root,
    )
    payload = _settings_payload(
        settings_path,
        installation,
        routing=resolved_routing,
        routing_metadata=metadata,
    )
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
    session_id: str = "",
    routing: HookRoutingMode | None = None,
    project_root: str = "",
) -> dict[str, Any]:
    settings_path = Path(path)
    resolved_routing, metadata = _routing_context(
        routing,
        session_id=session_id,
        workspace_base=workspace_base,
        project_root=project_root,
    )
    generated = _settings_payload(
        settings_path,
        installation,
        routing=resolved_routing,
        routing_metadata=metadata,
    )
    created = not settings_path.exists()
    merged_settings = _read_settings(settings_path) if not created else {}
    hooks = merged_settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Claude Code settings field 'hooks' must be an object")

    added_hooks = 0
    for event_name, event_hooks in generated["settings"]["hooks"].items():
        current_hooks = hooks.setdefault(event_name, [])
        if not isinstance(current_hooks, list):
            raise ValueError(f"Claude Code settings hooks.{event_name} must be a list")
        current_hooks[:] = [
            hook
            for hook in current_hooks
            if not _is_stale_v5_hook(hook, expected_hooks=event_hooks)
        ]
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


def _routing_context(routing, *, session_id, workspace_base, project_root):
    resolved = resolve_installer_hook_routing(routing, session_id=session_id)
    return resolved, hook_routing_metadata(
        resolved,
        project_root=project_root or workspace_base,
        topics_root=workspace_base,
    )


def _settings_payload(settings_path, installation, *, routing, routing_metadata):
    hook_script = (Path(__file__).resolve().parents[2] / "hooks" / "aitp_v5_claude_hook.py").as_posix()
    python_exe = stable_python_executable()

    def command(name: str) -> str:
        return render_hook_command(
            build_native_lifecycle_hook_argv(
                executable=python_exe,
                hook_path=hook_script,
                command=name,
                topics_root=str(routing_metadata["topics_root"]),
                project_root=str(routing_metadata["project_root"]),
                routing=routing,
            )
        )

    commands = {name: command(name) for name in ("session-start", "pre-tool", "post-tool")}
    events = [
        _event("SessionStart", "startup|resume", "session_start", commands["session-start"]),
        _event("PreToolUse", "*", "pre_tool", commands["pre-tool"]),
        _event("PostToolUse", "*", "post_tool", commands["post-tool"]),
    ]
    settings = {
        "hooks": {
            event["hook_event_name"]: [_claude_event(event["matcher"], event["command"])]
            for event in events
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
        **routing_metadata,
        "events": events,
        "settings": settings,
    }


def _event(hook_event_name, matcher, protocol_hook, command):
    return {
        "hook_event_name": hook_event_name,
        "matcher": matcher,
        "protocol_hook": protocol_hook,
        "command": command,
    }


def _claude_event(matcher: str, command: str) -> dict[str, Any]:
    return {"matcher": matcher, "hooks": [{"type": "command", "command": command}]}


def _is_stale_v5_hook(event_hook: Any, *, expected_hooks: list[dict[str, Any]]) -> bool:
    if event_hook in expected_hooks or not isinstance(event_hook, dict):
        return False
    command_hooks = event_hook.get("hooks")
    return isinstance(command_hooks, list) and any(
        isinstance(command_hook, dict)
        and "aitp_v5_claude_hook.py" in str(command_hook.get("command", ""))
        for command_hook in command_hooks
    )


def _read_settings(settings_path: Path) -> dict[str, Any]:
    text = settings_path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Claude Code settings must be a JSON object")
    return payload


__all__ = ["install_claude_code_hook_settings", "write_claude_code_hook_settings"]
