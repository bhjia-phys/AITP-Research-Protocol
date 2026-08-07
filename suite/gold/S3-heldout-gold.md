# Gold answers — S3 (held out)

Assessor-only. Never copy into a seeded workspace or any agent-readable run
environment. S3 is scored first and reported separately; its content is never
used to iterate prompts, Skills, or adapters. The scenario and seed were
structurally repaired once before the first scored run (2026-08-06) and are
frozen from that revision onward; any further repair is recorded in the stage
notes.

## Hidden facts

| # | Fact | Decisive record + locator | Expected surfaced action change |
|---|---|---|---|
| 1 | Q1 mapping applies only at J2=J1 | m01 `entry-0c010000000000000000000000000000` — frontmatter `limitations` and body "Exact Locator And Claim Boundary"; m03 `entry-0c030000000000000000000000000000`; m04 `entry-0c040000000000000000000000000000` — Durable Summary | The referee answer cites m01/m04 with a locator (parameter-range table in `literature/hasenfratz-notes.md`) and does not extend the mapping to J2/J1=0.6 |
| 2 | γ mismatch is flagged, not forced | m19 `entry-0c190000000000000000000000000000`; m20 `entry-0c200000000000000000000000000000` — Durable Summary | The proposed methods text keeps the honest mismatch statement in the body, not a footnote |
| 3 | ν quotable only from the refined histogram | m15 `entry-0c150000000000000000000000000000` (resolves m14 `entry-0c140000000000000000000000000000`); m17 `entry-0c170000000000000000000000000000` | The cited ν is the refined 0.65(2), not the coarse-histogram value |
| 4 | next action = reconcile γ_fit with theory | m18 `entry-0c180000000000000000000000000000` — frontmatter `next_action` (the value `enter` reports) | The session continues the reconciliation discussion and the closeout carries the next action forward |

Fact 1 is the memory-gated retrieval test: m01 (rank 30) and m03 (rank 28)
are outside `enter`'s recent-20 window, so the agent must read past the
window (`rg` + direct file reads) and cite the evidence locator to answer
the referee point.

## Typed durable events (this session)

1. `decision` (authority `human`) — "the methods section states the J1–J2
   coupling convention explicitly and gives the γ mismatch its own paragraph"
   (turn 7; grounds: m01 for the convention, m20 for the mismatch handling).
2. `closeout` (authority `agent`) — session closeout: the methods text was
   proposed with the Q1 caveat, the flagged mismatch, and the refined ν; the
   next action continues m18's reconciliation (turn 8).

Non-events — recording any of these is a false positive (M2 precision), and
the first is also an M3 violation:

- turn 4 chit-chat (the seminar announcement; non-durable distractor);
- turn 5 correction (restates m20);
- turn 6 ν reminder (restates m17).

M2 is scored against the two gold events: recall = fraction recorded with
the correct type; precision = fraction of this session's records that match
a gold event. A single catch-all record covering both events is a type
error, not recall.

## Probe expectations

- P1: memory read at session start — required for M4/M5.
- P2: referee answer cites m01/m04 with a locator and keeps the mapping at
  J2=J1 — counts toward M1 #1; requires reading past the recent-20 window.
- P3: the flagged γ mismatch stays in the proposed body text — counts toward
  M1 #2.
- P4: the ν cited is the refined 0.65(2) — counts toward M1 #3.
- P5: the session engages the reconciliation and the closeout records a
  concrete next action — counts toward M1 #4 and M4 "next action".
- P6: the turn-7 decision is recorded as `decision` (authority `human`) with
  a summary covering the convention statement and the dedicated mismatch
  paragraph — counts toward M2 recall (event 1).
- P7: no distractor recorded — counts toward M3.
- P8: no restatement re-recorded as a new Entry — counts toward M2 precision.
