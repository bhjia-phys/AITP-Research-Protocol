---
name: aitp-runtime
description: Reference note for the Codex adapter surface; Codex should enter `using-aitp` at session start and keep Phase 6 decision records current during topic work.
---

# Codex Adapter Reference

The public Codex path is skill-discovery-first:

1. let Codex load repository `skills/` and enter `using-aitp` before any substantive theory response;
2. if the user starts from a vague idea, run the clarification sub-protocol before normal `L0-L4` execution;
3. use `aitp session-start "<task>"` only as the manual fallback when native bootstrap is unavailable.

## Phase 6 behavior

During Codex-driven topic work:

1. keep `research_question.contract.json` and `control_note.md` current before deep execution;
2. if ambiguity remains, ask up to 3 clarification rounds with 1-3 questions per round;
3. materialize non-trivial checkpoints with `aitp emit-decision ...` and resolve them durably rather than leaving them only in chat memory;
4. materialize paired decision traces and maintain a session chronicle so later status or "why?" questions can be answered from runtime records;
5. treat "AITP pause" as a question to the human in chat, not as a background process or hidden controller.
6. inspect active human-choice surfaces with `aitp interaction --topic-slug <topic_slug> --json`;
7. when the active surface is a formal decision point, answer it with `aitp resolve-decision ...`; when it is an operator checkpoint, answer it with `aitp resolve-checkpoint ...` and add a comment when the choice needs extra steering detail.
