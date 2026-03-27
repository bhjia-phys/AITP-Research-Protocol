---
name: aitp-runtime
description: Reference note for the Claude Code adapter surface; the active Claude bootstrap now lives in `/.claude-plugin`, `/hooks`, and the repository `skills/` directory.
---

# Claude Code Adapter Reference

The public Claude Code path is now SessionStart-first:

1. install the plugin or compatibility hook bundle described in `docs/INSTALL_CLAUDE_CODE.md`;
2. let SessionStart inject `using-aitp` before substantive theory work;
3. use `aitp session-start "<task>"` only as the manual fallback when bootstrap is unavailable.

## Phase 6 behavior

During Claude Code topic work:

1. if the idea is vague, run the clarification sub-protocol before normal `L0-L4` execution;
2. clarification rounds target `scope`, `assumptions`, and `target_claims`, with at most 3 rounds and 1-3 questions per round;
3. non-trivial checkpoints should become decision points and later decision traces, not only chat prose;
4. session summaries should be written back as chronicles so operator questions can be answered from runtime state;
5. "AITP pause" means Claude asks the human in chat and records the checkpoint, not that a background controller exists.
