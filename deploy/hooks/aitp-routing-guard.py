#!/usr/bin/env python3
"""PreToolUse guard for AITP v5 routing discipline.

Blocks Write/Edit/MultiEdit to canonical AITP topic state and workspace-root runtime
state until routing has been confirmed via a short-lived marker. The hook is a
guard only; it does not update AITP state.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

AITP_TOPICS_DIR = "aitp-topics"
AITP_TOPICS_FULL = Path(os.environ.get("AITP_TOPICS_ROOT", "{{TOPICS_ROOT}}"))
PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "{{TARGET_ROOT}}"))
ROOT_AITP_FULL = Path(os.environ.get("AITP_WORKSPACE_ROOT", str(PROJECT_ROOT / ".aitp")))

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}
ROUTING_MARKER_DIR = Path(os.environ.get("TEMP", "/tmp"))


def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r"\\\\\1", raw)
            fixed = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", fixed)
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

        if time.time() - marker.stat().st_mtime > 4 * 3600:
            return False
    except OSError:
        return False
    return True


def normalize_candidate_path(file_path: str) -> Path:
    candidate = Path(file_path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def classify_aitp_target(file_path: str) -> str:
    candidate = normalize_candidate_path(file_path)
    normalized = file_path.replace("\\", "/")
    if is_under(candidate, AITP_TOPICS_FULL) or AITP_TOPICS_DIR in normalized:
        return "canonical topics store"
    if is_under(candidate, ROOT_AITP_FULL):
        return "workspace-root runtime store"
    return ""


def extract_file_path(tool_input_data: dict) -> str:
    for key in ("file_path", "path", "target_path", "filename", "file"):
        value = tool_input_data.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def main() -> int:
    raw = sys.stdin.read()
    tool_input = safe_json_loads(raw) if raw.strip() else {}
    if not tool_input:
        return 0

    tool_name = tool_input.get("tool_name", "")
    tool_input_data = tool_input.get("tool_input", {})
    if tool_name not in WRITE_TOOLS:
        return 0

    file_path = extract_file_path(tool_input_data)
    if not file_path:
        return 0

    target_kind = classify_aitp_target(file_path)
    if not target_kind:
        return 0

    if has_routed_this_session():
        return 0

    marker = get_marker_path()
    message = (
        "AITP V5 WRITE GUARD: You are about to write inside an AITP state store "
        f"({target_kind}):\n"
        f"  {file_path}\n\n"
        "Before modifying AITP topic state, you MUST:\n"
        "1. Get a v5 execution brief if a v5 session id is known.\n"
        "2. Otherwise migrate or bind the legacy topic into v5 first.\n"
        "3. Use typed v5 records or aitp-v5 CLI operations for state changes.\n"
        "4. Do not hand-edit research/aitp-topics/.aitp records, workspace-root .aitp runtime records, "
        "legacy stage files, trust state, or topic memory as a shortcut.\n"
        f"5. Create routing marker only after typed routing is confirmed: echo routed > {marker}\n\n"
        "Docs/config/hook maintenance is allowed when it is clearly not editing topic state. "
        "Non-AITP files are not restricted."
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
