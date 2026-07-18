"""Route-aware CLI dispatch for installing AITP v5 host hooks."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

from brain.v5.adapter_protocols import build_adapter_protocols, supported_runtimes
from brain.v5.hook_codex_install import install_codex_hooks_json
from brain.v5.hook_fixture_templates import install_codex_hook_fixture, install_opencode_hook_fixture
from brain.v5.hook_install_templates import build_runtime_hook_installation, install_claude_code_hook_settings
from brain.v5.hook_kimi_install import install_kimi_code_hook_config, write_kimi_code_hook_config
from brain.v5.hook_opencode_install import install_opencode_plugin_file
from brain.v5.hook_routing_mode import HookRoutingMode, normalize_hook_routing_mode
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import get_session_binding


def dispatch_adapter_install_hooks(args: Namespace, ws: Any) -> dict[str, Any]:
    routing = _routing_from_args(args)
    project_root = _project_root_from_args(args, ws, routing)
    _validate_pinned_session(ws, routing)
    runtime = _normalize_runtime(args.runtime)
    protocols = build_adapter_protocols()
    installation = build_runtime_hook_installation(runtime, protocols["runtime_hook_protocols"])
    common = {
        "workspace_base": str(ws.base),
        "routing": routing,
        "project_root": project_root,
    }

    if runtime == "codex":
        if args.settings:
            payload = install_codex_hooks_json(
                args.settings,
                installation,
                protocols["runtime_gate_protocols"],
                bridge_path=args.bridge_output or None,
                **common,
            )
        else:
            if not args.output:
                raise SystemExit("adapter install-hooks codex requires --output or --settings")
            payload = install_codex_hook_fixture(
                args.output,
                installation,
                protocols["runtime_gate_protocols"],
                bridge_path=args.bridge_output or None,
                **common,
            )
        return _validated("codex_hook_installation", payload)

    if runtime == "opencode":
        if args.plugin:
            payload = install_opencode_plugin_file(
                args.plugin,
                installation,
                protocols["runtime_gate_protocols"],
                bridge_path=args.bridge_output or None,
                reviewed_replacement_plan_id=args.reviewed_replacement_plan_id,
                **common,
            )
        else:
            if not args.output:
                raise SystemExit("adapter install-hooks opencode requires --output or --plugin")
            payload = install_opencode_hook_fixture(
                args.output,
                installation,
                protocols["runtime_gate_protocols"],
                bridge_path=args.bridge_output or None,
                **common,
            )
        return _validated("opencode_hook_installation", payload)

    if runtime == "kimi_code":
        if args.settings:
            payload = install_kimi_code_hook_config(args.settings, installation, **common)
            return _validated("kimi_code_hook_installation", payload)
        if not args.output:
            raise SystemExit("adapter install-hooks kimi-code requires --settings or --output")
        payload = write_kimi_code_hook_config(args.output, installation, **common)
        return _validated("kimi_code_hook_config", payload)

    if runtime != "claude_code":
        raise SystemExit("adapter install-hooks supports codex, opencode, claude-code, and kimi-code")
    if not args.settings:
        raise SystemExit("adapter install-hooks claude-code requires --settings")
    payload = install_claude_code_hook_settings(args.settings, installation, **common)
    return _validated("claude_code_hook_installation", payload)


def _routing_from_args(args: Namespace) -> HookRoutingMode:
    legacy_session_id = str(getattr(args, "legacy_session_id", "") or "").strip()
    if legacy_session_id:
        if args.routing_mode or args.pinned_session_id:
            raise SystemExit("legacy positional session cannot be combined with routing flags")
        return normalize_hook_routing_mode("", legacy_session_id, legacy_positional=True)
    try:
        return normalize_hook_routing_mode(args.routing_mode, args.pinned_session_id)
    except (TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


def _project_root_from_args(args: Namespace, ws: Any, routing: HookRoutingMode) -> str:
    project_root = str(args.project_root or "").strip()
    if project_root:
        return project_root
    if routing.legacy_pinned:
        return str(ws.base)
    raise SystemExit("adapter install-hooks requires explicit --project-root")


def _validate_pinned_session(ws: Any, routing: HookRoutingMode) -> None:
    if not routing.pinned_session_id:
        return
    try:
        get_session_binding(ws, routing.pinned_session_id)
    except (FileNotFoundError, ValueError, TypeError) as exc:
        raise SystemExit(f"pinned session is not readable: {routing.pinned_session_id}") from exc


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value not in supported_runtimes():
        raise SystemExit(f"unsupported hook runtime: {runtime}")
    return value


def _validated(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    return require_valid_public_surface(surface, {"ok": True, **payload})


__all__ = ["dispatch_adapter_install_hooks"]
