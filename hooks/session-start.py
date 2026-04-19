#!/usr/bin/env python3
"""Claude Code SessionStart hook for AITP.

On startup/clear: injects the using-aitp skill.
On compact: also scans active AITP topics, injects their runtime state,
and writes a session-active marker so the PreToolUse guard can enforce routing.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path


AITP_TOPICS_ROOT = Path(
    os.environ.get("AITP_TOPICS_ROOT",
        "D:/BaiduSyncdisk/repos/AITP-Research-Protocol"
        "/research/knowledge-hub/runtime/topics"
    )
)
MARKER_DIR = Path(os.environ.get("TEMP", "/tmp"))


def get_cwd_hash() -> str:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def write_session_active_marker(topics: list[dict]) -> Path:
    """Write a marker file indicating AITP session is active (compact recovery)."""
    marker = MARKER_DIR / f"aitp_session_active_{get_cwd_hash()}"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({
        "topics": [t["slug"] for t in topics],
        "created_at": time.time(),
    }), encoding="utf-8")
    return marker


def safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def scan_active_topics() -> list[dict]:
    """Scan AITP topics directory for active (non-completed) topics."""
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
        if stage in ("missing",):
            continue

        active.append({
            "slug": state.get("topic_slug", topic_dir.name),
            "stage": stage,
            "resume_stage": state.get("resume_stage", "?"),
            "resume_reason": state.get("resume_reason", ""),
            "research_mode": state.get("research_mode", "?"),
            "load_profile": state.get("load_profile", "?"),
            "updated_at": state.get("updated_at", ""),
            "executor": state.get("active_executor_kind", ""),
        })

    return active


def build_skill_injection() -> str:
    script_dir = Path(__file__).resolve().parent
    plugin_root = Path(
        os.environ.get("CLAUDE_PLUGIN_ROOT") or (script_dir / "..")
    ).resolve()
    skill_path = plugin_root / "skills" / "using-aitp" / "SKILL.md"

    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return f"Error reading using-aitp skill from {skill_path}"


def build_aitp_state_injection(active_topics: list[dict]) -> str:
    if not active_topics:
        return ""

    lines = [
        "<AITP_RUNTIME_STATE_INJECTION>",
        "## AITP Protocol State Recovery (post-compaction)",
        "",
        "Context was compacted. The following AITP topics are active:",
        "You MUST restore your AITP execution posture before doing any work.",
        "",
        "### Active Topics",
        "",
    ]

    for t in active_topics:
        lines.append(f"**{t['slug']}**:")
        lines.append(f"  - Stage: {t['stage']}, Resume at: {t['resume_stage']}")
        lines.append(f"  - Mode: {t['research_mode']}, Load: {t['load_profile']}")
        lines.append(f"  - Reason: {t['resume_reason']}")
        lines.append(f"  - Updated: {t['updated_at']}")
        lines.append("")

    lines.extend([
        "### Required Recovery Steps",
        "",
        "1. Call `mcp__aitp__aitp_get_popup` for the relevant topic",
        "2. Call `mcp__aitp__aitp_get_runtime_state` to read full state",
        "3. Follow the `resume_stage` and `next_bounded_action` guidance",
        "4. Use `mcp__aitp__aitp_run_topic_loop` to continue the protocol",
        "5. After routing, create the routing marker with Bash:",
        f"   `echo routed > {MARKER_DIR / f'aitp_routed_{get_cwd_hash()}'}`",
        "",
        "Do NOT skip these steps and start coding directly.",
        "The PreToolUse guard will block work tools until you route.",
        "",
        "</AITP_RUNTIME_STATE_INJECTION>",
    ])

    return "\n".join(lines)


def main() -> int:
    trigger = ""
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ("startup", "clear", "compact"):
            trigger = arg
            break

    if not trigger:
        try:
            raw = sys.stdin.read()
            if raw.strip():
                hook_input = safe_json_loads(raw)
                if hook_input and "trigger" in hook_input:
                    trigger = hook_input["trigger"]
        except Exception:
            pass

    skill_content = build_skill_injection()
    session_context = (
        "<EXTREMELY_IMPORTANT>\n"
        "You are in an AITP-enabled Claude Code session.\n\n"
        "**Below is the full content of the using-aitp skill. "
        "It is already loaded. Do not load using-aitp again.**\n\n"
        f"{skill_content}\n"
    )

    # On compact: inject AITP state + write session-active marker
    if trigger == "compact":
        active_topics = scan_active_topics()
        if active_topics:
            state_injection = build_aitp_state_injection(active_topics)
            session_context += f"\n{state_injection}\n"
            # Write marker so the PreToolUse guard knows to enforce routing
            marker_path = write_session_active_marker(active_topics)
            session_context += (
                f"\nSession-active marker written to: {marker_path}\n"
                f"The PreToolUse guard will enforce AITP routing for this session.\n"
            )

    session_context += "</EXTREMELY_IMPORTANT>"

    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": session_context,
            }
        }
    else:
        payload = {"additional_context": session_context}

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
