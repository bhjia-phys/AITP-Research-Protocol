#!/usr/bin/env python3
"""PreToolUse guard for AITP v5 routing discipline.

Scope: only blocks Write/Edit to files inside the configured AITP topics
directory unless routing has been confirmed via a short-lived marker.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

AITP_TOPICS_DIR = "aitp-topics"
AITP_TOPICS_FULL = Path(
    os.environ.get("AITP_TOPICS_ROOT", "{{TOPICS_ROOT}}")
)

WRITE_TOOLS = {"Write", "Edit"}
ROUTING_MARKER_DIR = Path(os.environ.get("TEMP", "/tmp"))


def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', raw)
            fixed = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            return None


def get_cwd_hash() -> str:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def get_marker_path() -> Path:
    return ROUTING_MARKER_DIR / f"aitp_routed_{get_cwd_hash()}"


def has_routed_this_session() -> bool:
    marker = get_marker_path()
    if not marker.exists():
        return False
    try:
        import time
        mtime = marker.stat().st_mtime
        if time.time() - mtime > 4 * 3600:
            return False
    except OSError:
        return False
    return True


def main() -> int:
    raw = sys.stdin.read()
    tool_input = safe_json_loads(raw) if raw.strip() else {}
    if not tool_input:
        return 0

    tool_name = tool_input.get("tool_name", "")
    tool_input_data = tool_input.get("tool_input", {})

    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = tool_input_data.get("file_path", "")
    if not file_path:
        return 0

    normalized = file_path.replace("\\", "/")
    if AITP_TOPICS_DIR not in normalized and AITP_TOPICS_FULL.as_posix() not in normalized:
        return 0

    if has_routed_this_session():
        return 0

    marker = get_marker_path()
    message = (
        "AITP V5 WRITE GUARD: You are about to write to an AITP topic file:\n"
        f"  {file_path}\n\n"
        "Before modifying AITP topic files, you MUST:\n"
        "1. Get a v5 execution brief if a v5 session id is known.\n"
        "2. Otherwise migrate or bind the legacy topic into v5 first.\n"
        "3. Use typed v5 records for state changes, not legacy stage files.\n"
        f"4. Create routing marker after routing is confirmed: echo routed > {marker}\n\n"
        "This guard protects protocol consistency. Non-AITP files are not restricted."
    )

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": message,
            "decision": "block",
            "reason": message,
        }
    }

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
