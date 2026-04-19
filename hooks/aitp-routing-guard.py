#!/usr/bin/env python3
"""PreToolUse guard for AITP routing enforcement.

Only activates when a session-active marker exists (written by session-start.py
on compact). This ensures the guard is opt-in: normal coding sessions are never
affected. Only after a compact during AITP research does enforcement kick in.

When active, blocks Write/Edit/Bash until routing is confirmed via marker:
  {TEMP}/aitp_routed_{cwd_hash}

MCP tools (mcp__aitp__*) are always allowed regardless of guard state.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


AITP_TOPICS_ROOT = Path(
    os.environ.get("AITP_TOPICS_ROOT",
        "D:/BaiduSyncdisk/repos/AITP-Research-Protocol"
        "/research/knowledge-hub/runtime/topics"
    )
)

WORK_TOOLS = {"Write", "Edit", "Bash"}
MCP_AITP_TOOLS_PREFIX = "mcp__aitp__"
ROUTING_MARKER_DIR = Path(os.environ.get("TEMP", "/tmp"))


def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def get_cwd_hash() -> str:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def get_marker_path() -> Path:
    """Get the session-specific routing marker path."""
    return ROUTING_MARKER_DIR / f"aitp_routed_{get_cwd_hash()}"


def get_session_active_marker_path() -> Path:
    """Path to the session-active marker written by session-start.py on compact."""
    return ROUTING_MARKER_DIR / f"aitp_session_active_{get_cwd_hash()}"


def has_routed_this_session() -> bool:
    """Check if AITP routing has been done for this project session."""
    marker = get_marker_path()
    if not marker.exists():
        return False
    # Check marker is recent (within 4 hours)
    try:
        import time
        mtime = marker.stat().st_mtime
        if time.time() - mtime > 4 * 3600:
            return False
    except OSError:
        return False
    return True


def mark_routed() -> None:
    """Create the routing marker file."""
    marker = get_marker_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("routed", encoding="utf-8")


def scan_active_topics() -> list[str]:
    """Return slugs of active (non-completed, non-missing) AITP topics."""
    if not AITP_TOPICS_ROOT.exists():
        return []

    active = []
    for topic_dir in sorted(AITP_TOPICS_ROOT.iterdir()):
        if not topic_dir.is_dir():
            continue
        state_file = topic_dir / "topic_state.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        stage = state.get("last_materialized_stage", "missing")
        if stage == "missing":
            continue
        active.append(state.get("topic_slug", topic_dir.name))

    return active


def main() -> int:
    # Read tool input from stdin
    raw = sys.stdin.read()
    tool_input = safe_json_loads(raw) if raw.strip() else {}
    if not tool_input:
        return 0  # Can't determine tool, allow

    tool_name = tool_input.get("tool_name", "")
    tool_input_data = tool_input.get("tool_input", {})

    # Always allow non-work tools
    if tool_name not in WORK_TOOLS:
        return 0

    # Always allow MCP AITP tools
    if tool_name.startswith(MCP_AITP_TOOLS_PREFIX):
        return 0

    # Only activate guard when session-active marker exists (set by compact trigger)
    session_active = get_session_active_marker_path()
    if not session_active.exists():
        return 0  # No AITP session active in this project, allow all

    # Check for AITP active topics
    active_topics = scan_active_topics()
    if not active_topics:
        return 0  # No AITP topics, allow

    # Check routing marker
    if has_routed_this_session():
        return 0  # Already routed, allow

    # Build warning message
    topics_str = ", ".join(active_topics[:5])
    if len(active_topics) > 5:
        topics_str += f", ... ({len(active_topics)} total)"

    # For Bash: allow if it's creating the routing marker itself
    if tool_name == "Bash":
        command = tool_input_data.get("command", "")
        if "aitp_routed" in command:
            # This is the agent creating the marker, allow it
            mark_routed()
            return 0

    # Block with guidance
    message = (
        f"AITP ROUTING REQUIRED: {len(active_topics)} active topic(s) found "
        f"({topics_str}), but no AITP routing has been done this session.\n\n"
        f"Before using {tool_name}, you MUST:\n"
        f"1. Call mcp__aitp__aitp_get_popup for the active topic\n"
        f"2. Call mcp__aitp__aitp_get_runtime_state to read current state\n"
        f"3. Follow the resume_stage guidance from the runtime state\n"
        f"4. Create routing marker: Bash with 'echo routed > marker_path'\n"
        f"   (marker path: {get_marker_path()})\n\n"
        f"This guard ensures AITP protocol continuity after context compaction."
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
