"""Codex native hooks.json installation helpers for AITP v5."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from brain.v5.hook_install_templates import write_codex_hook_bridge


def install_codex_hooks_json(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    workspace_base: str,
    session_id: str,
    bridge_path: str | Path | None = None,
) -> dict[str, Any]:
    """Merge AITP v5 hook runners into a Codex hooks.json file."""

    hooks_path = Path(path)
    resolved_bridge_path = Path(bridge_path) if bridge_path else hooks_path.parent / "AITP_V5_HOOK_BRIDGE.md"
    bridge = write_codex_hook_bridge(
        resolved_bridge_path,
        installation,
        runtime_gate_protocols,
        session_id=session_id,
    )
    generated = _codex_hooks_payload(
        hooks_path,
        workspace_base=workspace_base,
        session_id=session_id,
        bridge_payload_path=bridge["payload_path"],
    )
    created = not hooks_path.exists()
    merged_hooks = _read_codex_hooks(hooks_path) if not created else {}
    hooks = merged_hooks.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Codex hooks file field 'hooks' must be an object")

    added_hooks = 0
    for event_name, event_hooks in generated["hooks"].items():
        current_hooks = hooks.setdefault(event_name, [])
        if not isinstance(current_hooks, list):
            raise ValueError(f"Codex hooks.{event_name} must be a list")
        for event_hook in event_hooks:
            if event_hook not in current_hooks:
                current_hooks.append(deepcopy(event_hook))
                added_hooks += 1

    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(
        json.dumps(merged_hooks, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "kind": "codex_hook_installation",
        "runtime": "codex",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": True,
        "fixture_installer_available": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "path": str(hooks_path),
        "native_hooks_path": str(hooks_path),
        "bridge_path": bridge["path"],
        "bridge_payload_path": bridge["payload_path"],
        "bridge": bridge,
        "hooks": merged_hooks,
        "created": created,
        "merged": True,
        "added_hooks": added_hooks,
    }


def _codex_event(matcher: str, command: str) -> dict[str, Any]:
    return {
        "matcher": matcher,
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }


def _codex_hooks_payload(
    hooks_path: Path,
    *,
    workspace_base: str,
    session_id: str,
    bridge_payload_path: str,
) -> dict[str, Any]:
    runner = (_repo_root() / "hooks" / "aitp_v5_adapter_event_runner.py").as_posix()
    pre_tool = _shell_command(
        [
            sys.executable,
            runner,
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
    )
    post_tool = _shell_command(
        [
            sys.executable,
            runner,
            "post-tool",
            "--base",
            workspace_base,
            "--runtime",
            "codex",
            "--session-id",
            session_id,
        ]
    )
    return {
        "kind": "codex_hooks_json",
        "runtime": "codex",
        "path": str(hooks_path),
        "hooks": {
            "PreToolUse": [_codex_event("*", pre_tool)],
            "PostToolUse": [_codex_event("*", post_tool)],
        },
    }


def _read_codex_hooks(hooks_path: Path) -> dict[str, Any]:
    text = hooks_path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Codex hooks file must be a JSON object")
    return payload


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _shell_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline([str(item) for item in argv])
    return " ".join(shlex.quote(str(item)) for item in argv)
