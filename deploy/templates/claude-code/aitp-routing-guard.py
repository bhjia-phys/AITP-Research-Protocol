#!/usr/bin/env python3
"""PreToolUse guard for AITP routing enforcement.

Narrow scope: only blocks Write/Edit to files inside the AITP topics directory
unless routing has been confirmed via marker.

Always allows: MCP tools, Read, Grep, Glob, Bash, and writes outside aitp-topics/.
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
            import re as _re
            fixed = _re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', raw)
            fixed = _re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', fixed)
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
    if AITP_TOPICS_DIR not in normalized:
        return 0

    if has_routed_this_session():
        return 0

    message = (
        f"AITP WRITE GUARD: You are about to write to an AITP topic file:\n"
        f"  {file_path}\n\n"
        f"Before modifying AITP topic files, you MUST:\n"
        f"1. Call mcp__aitp__aitp_get_execution_brief to check current state\n"
        f"2. Follow the protocol workflow — use MCP tools for state changes\n"
        f"3. Create routing marker: Bash 'echo routed > {get_marker_path()}'\n\n"
        f"This ensures AITP protocol consistency. For non-AITP files, no restriction applies."
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
