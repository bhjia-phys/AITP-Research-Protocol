"""Dynamic host-process readiness checks for AITP v5 runtime adapters."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from brain.v5.hook_install_audit import audit_hook_installation


_DEFAULT_COMMANDS = {
    "codex": "codex",
    "claude_code": "claude",
    "kimi_code": "kimi",
    "opencode": "opencode",
}


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
        "truth_source": "runtime_process_and_files",
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


def _parse_json_object(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _trim(text: str, limit: int = 2000) -> str:
    return text[:limit]
