"""Runtime hook installation fixtures derived from v5 bridge metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.hook_install_templates import write_codex_hook_bridge, write_opencode_plugin_bridge


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
    pre_tool_hook = _pre_tool_hook(
        runtime="codex",
        workspace_base=workspace_base,
        session_id=session_id,
        bridge_payload_path=bridge["payload_path"],
    )
    post_tool_hook = _post_tool_hook(
        runtime="codex",
        workspace_base=workspace_base,
        session_id=session_id,
    )
    fixture = {
        "kind": "codex_hook_installation_fixture",
        "runtime": "codex",
        "hooks": {"pre_tool": pre_tool_hook, "post_tool": post_tool_hook},
        "truth_rule": "fixture is runtime metadata only; typed records remain authoritative",
        "summary_inputs_trusted": False,
    }
    payload = _installation_payload(
        kind="codex_hook_installation",
        runtime="codex",
        installation_mode=installation["installation_mode"],
        fixture_path=fixture_path,
        bridge=bridge,
        fixture=fixture,
    )
    _write_fixture(fixture_path, fixture)
    return payload


def install_opencode_hook_fixture(
    path: str | Path,
    installation: dict[str, Any],
    runtime_gate_protocols: dict[str, Any] | None = None,
    *,
    workspace_base: str,
    session_id: str,
    bridge_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write an OpenCode stdin-runner plugin fixture plus its bridge sidecar."""

    fixture_path = Path(path)
    resolved_bridge_path = Path(bridge_path) if bridge_path else fixture_path.parent / "AITP_V5_PLUGIN_BRIDGE.md"
    bridge = write_opencode_plugin_bridge(
        resolved_bridge_path,
        installation,
        runtime_gate_protocols,
        session_id=session_id,
    )
    pre_tool_hook = _pre_tool_hook(
        runtime="opencode",
        workspace_base=workspace_base,
        session_id=session_id,
        bridge_payload_path=bridge["payload_path"],
    )
    post_tool_hook = _post_tool_hook(
        runtime="opencode",
        workspace_base=workspace_base,
        session_id=session_id,
    )
    fixture = {
        "kind": "opencode_hook_installation_fixture",
        "runtime": "opencode",
        "plugin_hooks": {"pre_tool": pre_tool_hook, "post_tool": post_tool_hook},
        "truth_rule": "fixture is runtime metadata only; typed records remain authoritative",
        "summary_inputs_trusted": False,
    }
    payload = _installation_payload(
        kind="opencode_hook_installation",
        runtime="opencode",
        installation_mode=installation["installation_mode"],
        fixture_path=fixture_path,
        bridge=bridge,
        fixture=fixture,
    )
    _write_fixture(fixture_path, fixture)
    return payload


def _installation_payload(
    *,
    kind: str,
    runtime: str,
    installation_mode: str,
    fixture_path: Path,
    bridge: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": kind,
        "runtime": runtime,
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation_mode,
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


def _pre_tool_hook(*, runtime: str, workspace_base: str, session_id: str, bridge_payload_path: str) -> dict[str, Any]:
    return {
        "lifecycle_event": "pre_tool",
        "command_kind": "stdin_json_runner",
        "cwd": str(_repo_root()),
        "argv": _stdin_runner_argv(
            runtime=runtime,
            workspace_base=workspace_base,
            session_id=session_id,
            bridge_payload_path=bridge_payload_path,
        ),
        "stdin": "<platform-event-json>",
        "output_kind": "pre_tool_policy_decision",
        "may_block": True,
        "state_mutation": "none",
    }


def _post_tool_hook(*, runtime: str, workspace_base: str, session_id: str) -> dict[str, Any]:
    return {
        "lifecycle_event": "post_tool",
        "command_kind": "stdin_json_runner",
        "cwd": str(_repo_root()),
        "argv": _post_tool_runner_argv(
            runtime=runtime,
            workspace_base=workspace_base,
            session_id=session_id,
        ),
        "stdin": "<platform-event-json>",
        "output_kind": "hook_trace_event_record",
        "may_block": False,
        "state_mutation": "append_trace_event",
    }


def _stdin_runner_argv(*, runtime: str, workspace_base: str, session_id: str, bridge_payload_path: str) -> list[str]:
    return [
        "python",
        "hooks/aitp_v5_adapter_event_runner.py",
        "pre-tool",
        "--base",
        workspace_base,
        "--runtime",
        runtime,
        "--session-id",
        session_id,
        "--bridge-path",
        bridge_payload_path,
    ]


def _post_tool_runner_argv(*, runtime: str, workspace_base: str, session_id: str) -> list[str]:
    return [
        "python",
        "hooks/aitp_v5_adapter_event_runner.py",
        "post-tool",
        "--base",
        workspace_base,
        "--runtime",
        runtime,
        "--session-id",
        session_id,
    ]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_fixture(fixture_path: Path, fixture: dict[str, Any]) -> None:
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
