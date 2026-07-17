"""Process execution and fixture preparation for host readiness probes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


def run_host_process(
    command: str,
    args: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    stdin_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = shutil.which(command)
    if not resolved:
        return {
            "command": command,
            "command_path": "",
            "args": args,
            "found": False,
            "ok": False,
            "failure_kind": "command_not_found",
            "stdin_submitted": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "command not found on PATH",
        }
    argv = _argv_for_resolved_command(resolved, args)
    stdin_text = (
        json.dumps(stdin_payload, sort_keys=True, separators=(",", ":"))
        if stdin_payload is not None
        else None
    )
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input=stdin_text,
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
            "failure_kind": "timeout",
            "stdin_submitted": stdin_payload is not None,
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
        "failure_kind": "" if completed.returncode == 0 else "nonzero_exit",
        "stdin_submitted": stdin_payload is not None,
        "exit_code": completed.returncode,
        "stdout": _trim(completed.stdout),
        "stderr": _trim(completed.stderr),
    }


def normalized_lifecycle_fixture(
    runtime: str,
    value: dict[str, Any] | None,
) -> dict[str, Any]:
    source = value if value is not None else {}
    if not isinstance(source, dict):
        raise TypeError("fixture_event must be a mapping")
    defaults = {
        "event_id": f"aitp-readiness-{runtime}-post-tool-v1",
        "event_type": "post_tool",
        "host_session_id": "aitp-readiness-smoke",
        "session_id": "aitp-readiness-smoke",
        "tool_name": "aitp-readiness-smoke",
        "status": "completed",
    }
    fixture: dict[str, Any] = {"runtime": runtime}
    for field in (
        "event_id",
        "event_type",
        "host_session_id",
        "session_id",
        "tool_name",
        "status",
    ):
        raw = source.get(field, defaults[field])
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"fixture_event.{field} must be a non-empty string")
        fixture[field] = raw.strip()
    if "exit_code" in source:
        exit_code = source["exit_code"]
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            raise TypeError("fixture_event.exit_code must be an integer")
        fixture["exit_code"] = exit_code
    return fixture


def fixture_audit(
    fixture: dict[str, Any],
    process: dict[str, Any],
) -> dict[str, Any]:
    encoded = json.dumps(
        fixture,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "requested": True,
        "submitted": bool(process.get("stdin_submitted")),
        "event_id": fixture["event_id"],
        "event_type": fixture["event_type"],
        "payload_sha256": hashlib.sha256(encoded).hexdigest(),
        "raw_payload_persisted": False,
    }


def _argv_for_resolved_command(resolved: str, args: list[str]) -> list[str]:
    if Path(resolved).suffix.lower() == ".ps1":
        return [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            resolved,
            *args,
        ]
    return [resolved, *args]


def _trim(text: str | bytes, limit: int = 2000) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return text[:limit]


__all__ = ["fixture_audit", "normalized_lifecycle_fixture", "run_host_process"]
