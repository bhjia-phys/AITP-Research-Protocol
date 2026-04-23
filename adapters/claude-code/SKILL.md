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

1. if the idea is vague, run the clarification sub-protocol before normal `L0→L1→L3→L4→L2→L5` execution;
2. clarification rounds target `scope`, `assumptions`, and `target_claims`, with at most 3 rounds and 1-3 questions per round;
3. non-trivial checkpoints should become decision points and later decision traces, not only chat prose;
4. session summaries should be written back as chronicles so operator questions can be answered from runtime state;
5. "AITP pause" means Claude asks the human in chat and records the checkpoint, not that a background controller exists.
6. inspect active human-choice surfaces with `aitp interaction --topic-slug <topic_slug> --json` or the native AITP MCP tool surface;
7. when the active surface is a formal decision point, answer it with `aitp resolve-decision ...`; when it is an operator checkpoint, answer it with `aitp resolve-checkpoint ...` and add a comment when the choice needs extra steering detail.
8. use `aitp_get_popup` (MCP tool) before continuing work; if a popup is active, present it using the pre-built `ask_user_question` field (pass `ask_user_question.questions` directly to `AskUserQuestion`), then resolve with `aitp_resolve_popup` before any deeper execution.
