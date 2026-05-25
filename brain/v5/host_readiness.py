"""Dynamic host-process readiness checks for AITP v5 runtime adapters."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from brain.v5.hook_install_audit import audit_hook_installation
from brain.v5.trace import hook_trace_event_path, read_trace_events


_DEFAULT_COMMANDS = {
    "codex": "codex",
    "claude_code": "claude",
    "kimi_code": "kimi",
    "opencode": "opencode",
}
_PRIORITY_HOSTS = {"codex", "claude_code", "kimi_code"}
_DEFERRED_HOSTS = {"opencode"}


def audit_runtime_host_readiness(
    ws,
    *,
    runtime: str,
    command: str = "",
    version_args: list[str] | None = None,
    timeout_seconds: int = 20,
    settings_path: str = "",
    plugin_path: str = "",
    output_path: str = "",
    check_installation: bool = True,
    session_id: str = "",
    run_session_start_smoke: bool = False,
) -> dict[str, Any]:
    """Run local process and optional hook checks without changing claim trust."""

    runtime = _normalize_runtime(runtime)
    command = command or _DEFAULT_COMMANDS.get(runtime, runtime)
    args = version_args if version_args is not None else ["--version"]
    process = _run_process(command, args, cwd=ws.base, timeout_seconds=timeout_seconds)
    install = _installation_payload(
        ws,
        runtime=runtime,
        settings_path=settings_path,
        plugin_path=plugin_path,
        output_path=output_path,
        check_installation=check_installation,
    )
    session_start = _session_start_payload(
        ws,
        runtime=runtime,
        session_id=session_id,
        run=run_session_start_smoke,
        timeout_seconds=timeout_seconds,
    )
    status = _status(process, install, session_start)
    return {
        "kind": "runtime_host_readiness_audit",
        "runtime": runtime,
        "status": status,
        "process": process,
        "installation_audit": install,
        "session_start_smoke": session_start,
        "production_loop": _production_loop(runtime, status, process, install, session_start),
        "truth_source": "runtime_process_and_files",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def audit_runtime_host_lifecycle(
    ws,
    *,
    runtime: str,
    command: str = "",
    args: list[str] | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Run a host command and audit whether lifecycle hook signals appeared."""

    runtime = _normalize_runtime(runtime)
    command = command or _DEFAULT_COMMANDS.get(runtime, runtime)
    run_args = args if args is not None else ["--version"]
    trace_path = hook_trace_event_path(ws)
    before = read_trace_events(trace_path)
    process = _run_process(command, run_args, cwd=ws.base, timeout_seconds=timeout_seconds)
    after = read_trace_events(trace_path)
    new_events = after[len(before):] if len(after) >= len(before) else []
    hook_output = _hook_output_payload(process)
    trace_delta = len(new_events)
    status = _lifecycle_status(process, trace_delta=trace_delta, hook_observed=hook_output["observed"])
    return {
        "kind": "runtime_host_lifecycle_audit",
        "runtime": runtime,
        "status": status,
        "process": process,
        "trace": {
            "path": str(trace_path),
            "before_count": len(before),
            "after_count": len(after),
            "delta_count": trace_delta,
            "new_event_ids": [event.event_id for event in new_events],
        },
        "hook_output": hook_output,
        "truth_source": "runtime_process_and_hook_trace",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _normalize_runtime(runtime: str) -> str:
    aliases = {"claude-code": "claude_code", "kimi-code": "kimi_code"}
    return aliases.get(runtime, runtime)


def _run_process(command: str, args: list[str], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    resolved = shutil.which(command)
    if not resolved:
        return {
            "command": command,
            "args": args,
            "found": False,
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "command not found on PATH",
        }
    argv = _argv_for_resolved_command(resolved, args)
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "command_path": resolved,
            "args": args,
            "found": True,
            "ok": False,
            "exit_code": None,
            "stdout": _trim(exc.stdout or ""),
            "stderr": f"timed out after {timeout_seconds}s",
        }
    return {
        "command": command,
        "command_path": resolved,
        "args": args,
        "found": True,
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": _trim(completed.stdout),
        "stderr": _trim(completed.stderr),
    }


def _argv_for_resolved_command(resolved: str, args: list[str]) -> list[str]:
    if Path(resolved).suffix.lower() == ".ps1":
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", resolved, *args]
    return [resolved, *args]


def _installation_payload(
    ws,
    *,
    runtime: str,
    settings_path: str,
    plugin_path: str,
    output_path: str,
    check_installation: bool,
) -> dict[str, Any]:
    if not check_installation:
        return {"checked": False, "status": "skipped", "required_actions": []}
    paths = _default_install_paths(ws.base, runtime, settings_path, plugin_path, output_path)
    audit = audit_hook_installation(ws, runtime=runtime, **paths)
    return {
        "checked": True,
        "status": audit["status"],
        "required_actions": audit["required_actions"],
        "checked_paths": audit["checked_paths"],
    }


def _default_install_paths(base: Path, runtime: str, settings: str, plugin: str, output: str) -> dict[str, str]:
    if runtime == "codex":
        return {"settings_path": settings or str(base / ".codex" / "hooks.json"), "plugin_path": plugin, "output_path": output}
    if runtime == "claude_code":
        return {"settings_path": settings or str(base / ".claude" / "settings.local.json"), "plugin_path": plugin, "output_path": output}
    if runtime == "kimi_code":
        return {"settings_path": settings or str(base / ".kimi" / "config.toml"), "plugin_path": plugin, "output_path": output}
    if runtime == "opencode":
        return {"settings_path": settings, "plugin_path": plugin or str(base / ".opencode" / "plugins" / "aitp-v5.js"), "output_path": output}
    return {"settings_path": settings, "plugin_path": plugin, "output_path": output}


def _session_start_payload(ws, *, runtime: str, session_id: str, run: bool, timeout_seconds: int) -> dict[str, Any]:
    if not run:
        return {"ran": False, "ok": False, "reason": "not requested"}
    if runtime not in {"claude_code", "kimi_code"}:
        return {"ran": False, "ok": False, "reason": "session-start smoke is implemented for Claude Code and Kimi Code"}
    if not session_id:
        return {"ran": False, "ok": False, "reason": "session_id is required"}
    script = Path(__file__).resolve().parents[2] / "hooks" / f"aitp_v5_{'claude' if runtime == 'claude_code' else 'kimi'}_hook.py"
    completed = subprocess.run(
        [sys.executable, str(script), "session-start", "--base", str(ws.base), "--session-id", session_id],
        cwd=str(ws.base),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    output = _parse_json_object(completed.stdout)
    return {
        "ran": True,
        "ok": completed.returncode == 0 and output.get("aitp", {}).get("kind") == "workspace_refresh_bundle",
        "exit_code": completed.returncode,
        "output_kind": output.get("aitp", {}).get("kind", ""),
        "stdout": _trim(completed.stdout),
        "stderr": _trim(completed.stderr),
    }


def _status(process: dict[str, Any], install: dict[str, Any], session_start: dict[str, Any]) -> str:
    if not process.get("ok"):
        return "process_unavailable"
    if install.get("checked") and install.get("status") != "installed":
        return "process_ready_installation_incomplete"
    if session_start.get("ran") and not session_start.get("ok"):
        return "process_ready_session_start_failed"
    if session_start.get("ran"):
        return "ready_with_session_start_smoke"
    return "process_ready"


def _production_loop(
    runtime: str,
    status: str,
    process: dict[str, Any],
    install: dict[str, Any],
    session_start: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "runtime": runtime,
        "priority_host": runtime in _PRIORITY_HOSTS,
        "deferred_host": runtime in _DEFERRED_HOSTS,
        "next_actions": _production_next_actions(runtime, process, install, session_start),
        "install_audit_required": not install.get("checked") or install.get("status") != "installed",
        "session_start_smoke_available": runtime in {"claude_code", "kimi_code"},
        "lifecycle_probe_command": f"aitp-v5 adapter host-lifecycle {_cli_runtime(runtime)}",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _production_next_actions(
    runtime: str,
    process: dict[str, Any],
    install: dict[str, Any],
    session_start: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if not process.get("ok"):
        actions.append("install_or_fix_host_command")
        return actions
    if not install.get("checked"):
        actions.append("install_or_audit_runtime_hooks")
    elif install.get("status") != "installed":
        actions.append("install_or_repair_runtime_hooks")
    if runtime in {"claude_code", "kimi_code"} and not session_start.get("ran"):
        actions.append("run_session_start_smoke")
    elif session_start.get("ran") and not session_start.get("ok"):
        actions.append("repair_session_start_refresh")
    actions.append("run_runtime_host_lifecycle_probe")
    return _unique(actions)


def _cli_runtime(runtime: str) -> str:
    return {"claude_code": "claude-code", "kimi_code": "kimi-code"}.get(runtime, runtime)


def _lifecycle_status(process: dict[str, Any], *, trace_delta: int, hook_observed: bool) -> str:
    if not process.get("ok"):
        return "process_unavailable"
    if trace_delta > 0 and hook_observed:
        return "lifecycle_observed"
    if trace_delta > 0:
        return "trace_delta_observed"
    if hook_observed:
        return "hook_output_observed"
    return "process_ready_no_lifecycle_event_observed"


def _hook_output_payload(process: dict[str, Any]) -> dict[str, Any]:
    text = "\n".join([str(process.get("stdout") or ""), str(process.get("stderr") or "")])
    kinds = [
        kind
        for kind in [
            "workspace_refresh_bundle",
            "hook_trace_event_record",
            "hook_decision",
            "PreToolUse",
            "PostToolUse",
            "SessionStart",
        ]
        if kind in text
    ]
    return {"observed": bool(kinds), "observed_kinds": kinds}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _parse_json_object(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _trim(text: str, limit: int = 2000) -> str:
    return text[:limit]
