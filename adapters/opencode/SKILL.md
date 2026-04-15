---
name: aitp-runtime
description: Reference note for the OpenCode adapter surface; the active OpenCode bootstrap now lives in `/.opencode/plugins/aitp.js` plus the repository `skills/` directory.
---

# OpenCode Adapter Reference

The public OpenCode path is now plugin-first:

1. install the plugin from `/.opencode/plugins/aitp.js` or follow `docs/INSTALL_OPENCODE.md`;
2. let the plugin inject `using-aitp` and register the repository `skills/` directory;
3. use `aitp session-start "<task>"` only as the manual fallback when plugin bootstrap is unavailable.

## Phase 6 behavior

During OpenCode topic work:

1. vague ideas trigger the clarification sub-protocol before ordinary `L0-L4` execution;
2. clarification should ask only the smallest useful question set and should tighten `research_question.contract.json`;
3. route choices, benchmark disagreements, promotion gates, and other high-impact checkpoints should be emitted as decision points;
4. resolved checkpoints should produce decision traces, and the session should leave behind a chronicle;
5. the adapter should treat these as normal file-backed runtime surfaces, not as a separate controller process.
6. inspect active human-choice surfaces with `aitp interaction --topic-slug <topic_slug> --json`;
7. use the plugin tool surface to render `primary_interaction.options` as UI choices when possible, send formal decision-point answers back through `aitp resolve-decision ...`, and send operator-checkpoint answers back through `aitp resolve-checkpoint ...`.
