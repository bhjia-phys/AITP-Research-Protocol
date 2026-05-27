"""CLI dispatch helpers for AITP v5 runtime adapter commands."""

from __future__ import annotations

import json
import argparse
from argparse import Namespace
from pathlib import Path
from typing import Any

from brain.v5.adapter_protocols import adapter_protocol_registry, record_gate_coverage_audit
from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.adapters import build_adapter_packet
from brain.v5.cli_progress import compact_final_readiness
from brain.v5.final_readiness import audit_final_engineering_readiness
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
from brain.v5.host_readiness import audit_priority_host_production_loops, audit_runtime_host_lifecycle, audit_runtime_host_readiness
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface


def add_adapter_parser(sp) -> None:
    ap = sp.add_parser("adapter")
    aps = ap.add_subparsers(dest="adapter_command", required=True)
    aps.add_parser("record-gate-audit")
    apt = aps.add_parser("packet"); apt.add_argument("runtime"); apt.add_argument("session_id")
    ahb = aps.add_parser("hook-bridge"); ahb.add_argument("runtime"); ahb.add_argument("session_id")
    ahb.add_argument("--output", required=True)
    ahs = aps.add_parser("hook-settings"); ahs.add_argument("runtime"); ahs.add_argument("session_id")
    ahs.add_argument("--output", required=True)
    aih = aps.add_parser("install-hooks"); aih.add_argument("runtime"); aih.add_argument("session_id")
    aih.add_argument("--settings", default=""); aih.add_argument("--output", default="")
    aih.add_argument("--plugin", default=""); aih.add_argument("--bridge-output", default="")
    aia = aps.add_parser("install-audit"); aia.add_argument("runtime")
    aia.add_argument("--settings", default=""); aia.add_argument("--output", default=""); aia.add_argument("--plugin", default="")
    ahr = aps.add_parser("host-readiness"); ahr.add_argument("runtime"); ahr.add_argument("--session", default="", dest="session_id")
    ahr.add_argument("--command", default="", dest="host_command"); ahr.add_argument("--arg", action="append", default=[], dest="version_args"); ahr.add_argument("--timeout", type=int, default=20)
    ahr.add_argument("--settings", default=""); ahr.add_argument("--output", default=""); ahr.add_argument("--plugin", default="")
    ahr.add_argument("--skip-install-audit", action="store_true"); ahr.add_argument("--run-session-start-smoke", action="store_true")
    ahp = aps.add_parser("host-production-loop"); ahp.add_argument("--session", default="", dest="session_id")
    ahp.add_argument("--command", default="", dest="host_command"); ahp.add_argument("--arg", action="append", default=[], dest="version_args"); ahp.add_argument("--timeout", type=int, default=20)
    ahp.add_argument("--skip-install-audit", action="store_true"); ahp.add_argument("--run-session-start-smoke", action="store_true")
    ahp.add_argument("--run-lifecycle-smoke", action="store_true")
    ahl = aps.add_parser("host-lifecycle"); ahl.add_argument("runtime")
    ahl.add_argument("--command", default="", dest="host_command"); ahl.add_argument("--arg", action="append", default=[], dest="host_args"); ahl.add_argument("--timeout", type=int, default=60)
    afr = aps.add_parser("final-readiness"); afr.add_argument("--migration-dir", default="")
    afr.add_argument("--compact", "--progress", action="store_true", dest="compact")
    aps.add_parser("install-paths"); aps.add_parser("smoke-coverage")
    ape = aps.add_parser("pre-tool-event"); ape.add_argument("runtime"); ape.add_argument("session_id")
    ape.add_argument("--bridge-json", default=""); ape.add_argument("--bridge-path", default="")
    ape.add_argument("--event-json", required=True)
    aps.add_parser("registry"); aps.add_parser("public-surfaces")


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

    if args.adapter_command == "final-readiness":
        payload = {
            "ok": True,
            **require_valid_public_surface(
                "final_engineering_readiness_audit",
                audit_final_engineering_readiness(ws, migration_dir=args.migration_dir or None),
            ),
        }
        if getattr(args, "compact", False):
            return compact_final_readiness(payload)
        return payload

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
    if args.adapter_command == "host-readiness":
        return {
            "ok": True,
            **require_valid_public_surface(
                "runtime_host_readiness_audit",
                audit_runtime_host_readiness(
                    ws,
                    runtime=args.runtime,
                    command=args.host_command,
                    version_args=args.version_args or None,
                    timeout_seconds=args.timeout,
                    settings_path=args.settings,
                    plugin_path=args.plugin,
                    output_path=args.output,
                    check_installation=not args.skip_install_audit,
                    session_id=args.session_id,
                    run_session_start_smoke=args.run_session_start_smoke,
                ),
            ),
        }
    if args.adapter_command == "host-production-loop":
        return {
            "ok": True,
            **require_valid_public_surface(
                "runtime_host_production_loop_audit",
                audit_priority_host_production_loops(
                    ws,
                    command=args.host_command,
                    version_args=args.version_args or None,
                    timeout_seconds=args.timeout,
                    check_installation=not args.skip_install_audit,
                    session_id=args.session_id,
                    run_session_start_smoke=args.run_session_start_smoke,
                    run_lifecycle_smoke=args.run_lifecycle_smoke,
                ),
            ),
        }
    if args.adapter_command == "host-lifecycle":
        return {
            "ok": True,
            **require_valid_public_surface(
                "runtime_host_lifecycle_audit",
                audit_runtime_host_lifecycle(
                    ws,
                    runtime=args.runtime,
                    command=args.host_command,
                    args=args.host_args or None,
                    timeout_seconds=args.timeout,
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
