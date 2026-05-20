"""CLI dispatch helpers for AITP v5 runtime adapter commands."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

from brain.v5.adapter_protocols import adapter_protocol_registry
from brain.v5.adapters import build_adapter_packet
from brain.v5.hook_install_templates import (
    install_claude_code_hook_settings,
    write_claude_code_hook_settings,
    write_codex_hook_bridge,
    write_opencode_plugin_bridge,
)
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
    if ws is None:
        raise SystemExit("adapter command requires an initialized v5 workspace")

    packet = require_valid_public_surface(
        "adapter_packet",
        build_adapter_packet(ws, args.session_id, runtime=args.runtime),
    )
    if args.adapter_command == "packet":
        return {"ok": True, **packet}
    if args.adapter_command == "hook-bridge":
        return _dispatch_hook_bridge(args, packet)
    if args.adapter_command == "hook-settings":
        if packet["runtime"] != "claude_code":
            raise SystemExit("adapter hook-settings currently supports claude-code runtime only")
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
        if packet["runtime"] != "claude_code":
            raise SystemExit("adapter install-hooks currently supports claude-code runtime only")
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
        ),
    }
    return require_valid_public_surface("codex_hook_bridge", bridge)
