#!/usr/bin/env python
"""Claude Code SessionStart hook for AITP."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or (script_dir / "..")).resolve()
    skill_path = plugin_root / "skills" / "using-aitp" / "SKILL.md"

    if skill_path.exists():
        using_aitp_content = skill_path.read_text(encoding="utf-8")
    else:
        using_aitp_content = f"Error reading using-aitp skill from {skill_path}"

    session_context = (
        "<EXTREMELY_IMPORTANT>\n"
        "You are in an AITP-enabled Claude Code session.\n\n"
        "**Below is the full content of the using-aitp skill. "
        "It is already loaded. Do not load using-aitp again.**\n\n"
        f"{using_aitp_content}\n"
        "</EXTREMELY_IMPORTANT>"
    )

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
