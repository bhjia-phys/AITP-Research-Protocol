# Real Topic E2E Runbook

This runbook is the operator-facing playbook for `v1.91`.

## Purpose

Use this when you want to test the current AITP implementation from a real idea
through the actual research flow rather than through a synthetic acceptance
fixture.

## Two Honest Entry Paths

### Path A: idea-first lightweight entry

Use this when the idea is still loose and you want to shape it before opening a
full topic.

1. `aitp explore "<raw idea>"`
2. inspect `runtime/explorations/<exploration_id>/explore_session.md`
3. if the idea becomes specific enough, run:
   `aitp promote-exploration --exploration-id <exploration_id> --current-topic`
   or start a new topic explicitly
4. continue with:
   `aitp loop --topic-slug <topic_slug> --human-request "<next bounded step>"`
5. inspect:
   - `aitp status --topic-slug <topic_slug>`
   - `aitp replay-topic --topic-slug <topic_slug>`
   - `aitp capability-audit --topic-slug <topic_slug>`
   - `aitp paired-backend-audit --topic-slug <topic_slug>`
   - `aitp h-plane-audit --topic-slug <topic_slug>`

### Path B: direct topic bootstrap

Use this when the idea is already concrete enough to name the topic and first
question directly.

1. `aitp bootstrap --topic "<topic>" --statement "<initial idea/question>"`
2. continue with:
   `aitp loop --topic-slug <topic_slug> --human-request "<next bounded step>"`
3. inspect:
   - `aitp status --topic-slug <topic_slug>`
   - `aitp replay-topic --topic-slug <topic_slug>`
   - `aitp capability-audit --topic-slug <topic_slug>`
   - `aitp paired-backend-audit --topic-slug <topic_slug>`
   - `aitp h-plane-audit --topic-slug <topic_slug>`

## Minimum Evidence To Keep

For the chosen topic, record at minimum:

- the initial idea text
- the exact command sequence
- the resolved `topic_slug`
- the final `status --json` snapshot
- the final `replay-topic --json` snapshot
- the final bounded outcome:
  - `promoted`
  - `promotion-ready`
  - blocked
  - deferred
  - still exploratory

Use these companion files during the run:

- `165-ISSUE-CAPTURE-PROTOCOL.md`
- `165-ISSUE-LEDGER.md`
- `evidence/TEMPLATE-POSTMORTEM.md`
- `evidence/TEMPLATE-COMMANDS.md`
- `evidence/TEMPLATE-LIVE-FRONT-DOOR-EVIDENCE.json`

## Live Front-Door Parity Closure

Use this when the real-topic run also needs to close the remaining
Claude Code / OpenCode first-turn bootstrap gap with honest evidence.

1. Pick a shared evidence directory, for example:
   `.planning/phases/165-real-topic-l0-to-l2-e2e-validation/evidence/live-front-door/`
2. Copy `evidence/TEMPLATE-LIVE-FRONT-DOOR-EVIDENCE.json` once per runtime and rename to:
   `claude_code.live-first-turn.json`
   `opencode.live-first-turn.json`
3. Run one real natural-language first turn in the target front door.
4. Fill the JSON with:
   - the exact first user turn
   - a concise summary of the first substantive agent turn
   - transcript / screenshot / artifact refs
   - the concrete `session_start.generated.md`, `runtime_protocol.generated.md`, and `status --json` artifact paths
   - explicit booleans for whether bootstrap consumption and posture visibility were actually observed
5. Re-run the shared parity audit with:
   `python research/knowledge-hub/runtime/scripts/run_runtime_parity_audit.py --live-evidence-root .planning/phases/165-real-topic-l0-to-l2-e2e-validation/evidence/live-front-door --json`

Honesty rule:

- if the first turn is ambiguous, missing artifacts, or does not clearly show the
  human-control/autonomy posture, mark the evidence `partial` or `failed`
  instead of forcing `verified`
- the audit should only close the live gap when the evidence file is explicitly
  `verified`

## Postmortem Questions

Answer these in `evidence/<topic-slug>/POSTMORTEM.md`:

- what was the initial real idea?
- which entry path did you use and why?
- what route did the topic actually take through `L0/L1/L3/L4/L2`?
- which protocol surfaces helped?
- which surfaces created friction or confusion?
- what outcome did the topic honestly reach?
- what follow-up engineering or protocol work is now clearly justified?

## GSD Linkage Rule

GSD does **not** reliably auto-discover arbitrary product/runtime problems just
because they exist in topic artifacts.

Current working rule:

- if you find a problem, write it into `165-ISSUE-LEDGER.md`
- use the fixed fields from `165-ISSUE-CAPTURE-PROTOCOL.md`
- then explicitly route it into GSD as one of:
  - urgent decimal phase in the current milestone
  - next milestone candidate
  - backlog item

Do not leave a discovered issue only in:

- chat memory
- the runtime topic shell
- or the postmortem prose
