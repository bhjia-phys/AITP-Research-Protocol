---
name: aitp-runtime
description: Reference note for the Claude Code adapter surface; the active Claude bootstrap now lives in `/.claude-plugin`, `/hooks`, and the repository `skills/` directory.
---

# Claude Code Adapter Reference

The public Claude Code path is now SessionStart-first:

1. install the plugin or compatibility hook bundle described in `docs/INSTALL_CLAUDE_CODE.md`;
2. let SessionStart inject `using-aitp` before substantive theory work;
3. use `aitp session-start "<task>"` only as the manual fallback when bootstrap is unavailable.
