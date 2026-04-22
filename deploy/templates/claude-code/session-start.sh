#!/usr/bin/env bash
# SessionStart hook for AITP

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="{{CLAUDE_USER_DIR}}"
SKILL_PATH="${PLUGIN_ROOT}/skills/using-aitp/SKILL.md"

if [ -f "$SKILL_PATH" ]; then
    using_aitp_content=$(cat "$SKILL_PATH")
else
    using_aitp_content="Error reading using-aitp skill from ${SKILL_PATH}"
fi

escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

using_aitp_escaped=$(escape_for_json "$using_aitp_content")
session_context="<EXTREMELY_IMPORTANT>\nYou are in an AITP-enabled Claude Code session.\n\n**Below is the full content of the using-aitp skill. It is already loaded. Do not load using-aitp again.**\n\n${using_aitp_escaped}\n</EXTREMELY_IMPORTANT>"

if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$session_context"
else
  printf '{\n  "additional_context": "%s"\n}\n' "$session_context"
fi

exit 0
