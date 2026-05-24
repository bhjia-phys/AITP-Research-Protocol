"""CLI dispatch helpers for AITP v5 runtime adapter commands."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

from brain.v5.adapter_protocols import adapter_protocol_registry, record_gate_coverage_audit
from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.adapters import build_adapter_packet
from brain.v5.hook_codex_install import install_codex_hooks_json
from brain.v5.hook_fixture_templates import install_codex_hook_fixture, install_opencode_hook_fixture
from brain.v5.hook_install_templates import (
    install_claude_code_hook_settings,
    write_claude_code_hook_settings,
    write_codex_hook_bridge,
    write_opencode_plugin_bridge,
)
from brain.v5.hook_kimi_install import install_kimi_code_hook_config, write_kimi_code_hook_config
from brain.v5.hook_install_audit import audit_hook_installation
from brain.v5.hook_install_paths import discover_hook_install_paths
from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report
from brain.v5.hook_opencode_install import install_opencode_plugin_file
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface


def dispatch_adapter_command(args: Namespace, ws: Any | None) -> dict[str, Any]:
    """Dispatch adapter CLI subcommands without growing the main CLI module."""

    if args.adapter_command == "registry":
        return {
            "ok": True,
            "adapter_protocol_registry": require_valid_public_surface(
                "adapter_protocol_registry",
                adapter_protocol_registry(),
            ),
        }
    if args.adapter_command == "public-surfaces":
        return {"ok": True, "public_surfaces": describe_public_surfaces()}
    if args.adapter_command == "record-gate-audit":
        return {
            "ok": True,
            "record_gate_coverage_audit": require_valid_public_surface(
                "record_gate_coverage_audit",
                record_gate_coverage_audit(),
            ),
        }
    if args.adapter_command == "smoke-coverage":
        return {
            "ok": True,
            **require_valid_public_surface(
                "runtime_hook_smoke_coverage",
                runtime_hook_smoke_coverage_report(),
            ),
        }
    if ws is None:
        raise SystemExit("adapter command requires an initialized v5 workspace")

    if args.adapter_command == "install-paths":
        return {
            "ok": True,
            **require_valid_public_surface("runtime_hook_installation_paths", discover_hook_install_paths(ws)),
        }

    if args.adapter_command == "install-audit":
        return {
            "ok": True,
            **require_valid_public_surface(
                "runtime_hook_installation_audit",
                audit_hook_installation(
                    ws,
                    runtime=args.runtime,
                    settings_path=args.settings,
                    plugin_path=args.plugin,
                    output_path=args.output,
                ),
            ),
        }

    packet = require_valid_public_surface(
        "adapter_packet",
        build_adapter_packet(ws, args.session_id, runtime=args.runtime),
    )
    if args.adapter_command == "packet":
        return {"ok": True, **packet}
    if args.adapter_command == "hook-bridge":
        return _dispatch_hook_bridge(args, packet)
    if args.adapter_command == "pre-tool-event":
        return require_valid_public_surface(
            "pre_tool_policy_decision",
            evaluate_platform_pre_tool_event(ws, _bridge_payload(args), _json_object(args.event_json)),
        )
    if args.adapter_command == "hook-settings":
        if packet["runtime"] == "kimi_code":
            config = {
                "ok": True,
                **write_kimi_code_hook_config(
                    args.output,
                    packet["runtime_hook_installation"],
                    workspace_base=str(ws.base),
                    session_id=args.session_id,
                ),
            }
            return require_valid_public_surface("kimi_code_hook_config", config)
        if packet["runtime"] != "claude_code":
            raise SystemExit("adapter hook-settings currently supports claude-code and kimi-code runtimes only")
        settings = {
            "ok": True,
            **write_claude_code_hook_settings(
                args.output,
                packet["runtime_hook_installation"],
                workspace_base=str(ws.base),
                session_id=args.session_id,
            ),
        }
        return require_valid_public_surface("claude_code_hook_settings", settings)
    if args.adapter_command == "install-hooks":
        if packet["runtime"] == "codex":
            if args.settings:
                installed = {
                    "ok": True,
                    **install_codex_hooks_json(
                        args.settings,
                        packet["runtime_hook_installation"],
                        packet["runtime_gate_protocols"],
                        workspace_base=str(ws.base),
                        session_id=args.session_id,
                        bridge_path=args.bridge_output or None,
                    ),
                }
                return require_valid_public_surface("codex_hook_installation", installed)
            if not args.output:
                raise SystemExit("adapter install-hooks codex requires --output or --settings")
            installed = {
                "ok": True,
                **install_codex_hook_fixture(
                    args.output,
                    packet["runtime_hook_installation"],
                    packet["runtime_gate_protocols"],
                    workspace_base=str(ws.base),
                    session_id=args.session_id,
                    bridge_path=args.bridge_output or None,
                ),
            }
            return require_valid_public_surface("codex_hook_installation", installed)
        if packet["runtime"] == "opencode":
            if args.plugin:
                installed = {
                    "ok": True,
                    **install_opencode_plugin_file(
                        args.plugin,
                        packet["runtime_hook_installation"],
                        packet["runtime_gate_protocols"],
                        workspace_base=str(ws.base),
                        session_id=args.session_id,
                        bridge_path=args.bridge_output or None,
                    ),
                }
                return require_valid_public_surface("opencode_hook_installation", installed)
            if not args.output:
                raise SystemExit("adapter install-hooks opencode requires --output or --plugin")
            installed = {
                "ok": True,
                **install_opencode_hook_fixture(
                    args.output,
                    packet["runtime_hook_installation"],
                    packet["runtime_gate_protocols"],
                    workspace_base=str(ws.base),
                    session_id=args.session_id,
                    bridge_path=args.bridge_output or None,
                ),
            }
            return require_valid_public_surface("opencode_hook_installation", installed)
        if packet["runtime"] == "kimi_code":
            if args.settings:
                installed = {
                    "ok": True,
                    **install_kimi_code_hook_config(
                        args.settings,
                        packet["runtime_hook_installation"],
                        workspace_base=str(ws.base),
                        session_id=args.session_id,
                    ),
                }
                return require_valid_public_surface("kimi_code_hook_installation", installed)
            if not args.output:
                raise SystemExit("adapter install-hooks kimi-code requires --settings or --output")
            config = {
                "ok": True,
                **write_kimi_code_hook_config(
                    args.output,
                    packet["runtime_hook_installation"],
                    workspace_base=str(ws.base),
                    session_id=args.session_id,
                ),
            }
            return require_valid_public_surface("kimi_code_hook_config", config)
        if packet["runtime"] != "claude_code":
            raise SystemExit("adapter install-hooks currently supports codex, opencode, claude-code, and kimi-code runtimes")
        if not args.settings:
            raise SystemExit("adapter install-hooks claude-code requires --settings")
        installed = {
            "ok": True,
            **install_claude_code_hook_settings(
                args.settings,
                packet["runtime_hook_installation"],
                workspace_base=str(ws.base),
                session_id=args.session_id,
            ),
        }
        return require_valid_public_surface("claude_code_hook_installation", installed)
    raise SystemExit(f"unknown adapter command: {args.adapter_command}")


def _dispatch_hook_bridge(args: Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    if packet["runtime"] == "opencode":
        bridge = {
            "ok": True,
            **write_opencode_plugin_bridge(
                args.output,
                packet["runtime_hook_installation"],
                packet["runtime_gate_protocols"],
                session_id=args.session_id,
            ),
        }
        return require_valid_public_surface("opencode_plugin_bridge", bridge)
    if packet["runtime"] != "codex":
        raise SystemExit("adapter hook-bridge currently supports codex and opencode runtimes only")
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            args.output,
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
            session_id=args.session_id,
        ),
    }
    return require_valid_public_surface("codex_hook_bridge", bridge)


def _json_object(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("expected a JSON object")
    return payload


def _bridge_payload(args: Namespace) -> dict[str, Any]:
    if args.bridge_json:
        return _json_object(args.bridge_json)
    if args.bridge_path:
        return _json_object(Path(args.bridge_path).read_text(encoding="utf-8"))
    raise SystemExit("adapter pre-tool-event requires --bridge-json or --bridge-path")
