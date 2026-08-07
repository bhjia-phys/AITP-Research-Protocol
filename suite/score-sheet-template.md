# Score-sheet template — AITP conformance suite (M0.6)

Blind-assessor recording instrument for the first human paired run of the M0.6
suite core. Metrics, definitions, pooling, and thresholds are defined in
`rubric.md` — this sheet is only the recording form and never changes them.

**Status: frozen before the first scored run.** This template is part of the
pre-run freeze together with `rubric.md` and the scenario/gold fixtures. It
may be revised only between stage runs, with the diff recorded in the stage
notes.

**Not an answer key.** This sheet contains no gold content: hidden facts,
typed-event lists, distractor lists, decisive-record references, and expected
values are transcribed by the assessor from the scenario's gold file, which is
part of the scoring package. Nothing in this sheet can leak an answer into a
seeded workspace.

## Binding boundary (assessor-side)

- The assessor receives ONLY condition-neutral per-probe packets plus the
  scenario text, `rubric.md`, the gold answers, and the frozen thresholds.
  Raw or full transcripts, workspaces, seeds, run notes, the sealed condition
  mapping, and raw console logs are operator-archived only and never enter the
  scoring package (`suite/README.md` step 7).
- The assessor accepts only condition-neutral packets: agent text quoted
  verbatim, record IDs referenced, cited targets and locators, timestamps,
  and tool-call counts, with tool names, command invocations, executable
  names, and condition-identifying paths (e.g. `.aitp`, CLI command names)
  normalized to neutral labels (`memory-read`, `record-write`, `search`,
  `<workspace>`, `<ledger>`). Mechanical traces never reach the assessor.
- If a packet appears to reveal the condition, the assessor does NOT score
  from that inference: flag the packet to the operator for re-packaging. The
  assessor never consults transcripts, workspaces, or the condition map to
  resolve any ambiguity; the only remedy is a corrected packet.
- The assessor never sees the execution-order draw or the condition mapping;
  the operator unseals the mapping only after scoring is complete.
- A probe whose packet lacks the required evidence scores 0, flagged for the
  stage notes.
- Scores attach to outcomes (changed actions, correct types, citations),
  never to rituals (having run a command, having written a file).

## N/A conventions

From `rubric.md` Definitions — apply uniformly:

- When a metric's gold denominator is empty for a scenario (e.g. no
  unconditional gold typed events, or no scripted distractors), the metric is
  **N/A (empty denominator)** for that scenario: excluded from pooling for
  that metric, never scored 0 or 1, reported as "N/A (empty denominator)".
- If the resumption session was not run, M4 is N/A for that scenario; the
  omission is recorded in the stage notes.
- If, after exclusion, a metric's pooled denominator is also empty, the
  metric is N/A for the pool and its gate is **not established**, with the
  reason in the stage notes.
- M5 has no N/A: report the pair of values, or "none within budget" with the
  budget values. M5 is unscorable without run-time instrumentation (UTC turn
  timestamps and tool-call counts): a packet lacking either supports no M5
  value, and missing instrumentation is a run-voiding condition (run-notes
  §7) — flag it for the stage notes, never reconstruct.

## How to use

1. The operator copies one run sheet (section 1) per scenario per anonymous
   run: three scenarios × two runs = six run sheets, plus one S1+S2 pooling
   worksheet (section 2) and one threshold-judgment table (section 4) per
   anonymous run, and one S3 collection table (section 3).
2. The anonymous run ID is assigned by the operator (e.g. "A"/"B" or a random
   token) and carries no condition information; the operator never writes the
   condition anywhere in this sheet.
3. Score one metric at a time across all packets, per `rubric.md` scoring
   procedure step 3: M1 → M2 → M3 → M4 → M5.
4. S3 is scored FIRST and reported separately, never pooled with S1/S2.
5. Evidence cells carry only what the packet states: verbatim agent text,
   record IDs referenced, cited targets and locators, timestamps, tool-call
   counts. Do not paraphrase from memory. An empty evidence cell means the
   packet lacks the evidence → score 0, flagged for the stage notes.
6. Sign the attestation (section 5) on every sheet.

---

## 1. Run sheet (one copy per scenario per anonymous run)

### 1.0 Header

| Field | Value |
|---|---|
| Scenario ID | S1 / S2 / S3 |
| Run ID (anonymous, operator-assigned) | |
| Packet-order draw ref (sealed with operator) | |
| Date | |
| Assessor | |

### 1.1 Package receipt checklist (confirm before scoring)

- [ ] Per-probe condition-neutral packets for this scenario and run, all
      probes present, order per the operator's scoring-order draw
- [ ] Scenario text
- [ ] `rubric.md` (metrics, definitions, frozen thresholds)
- [ ] Gold answers for this scenario
- [ ] Confirmed absent from the package: raw transcripts, workspaces, run
      notes, condition mapping, raw console logs

### 1.2 Condition-neutrality confirmation

- [ ] Every packet scored here is condition-neutral as received; any packet
      that violated neutrality was flagged to the operator and scored only
      after re-packaging, or is marked N/A below with a flag note.

Flagged packets: `________________________________`

### 1.3 M1 — Hidden-fact action score (per probe)

One row per gold hidden fact. Transcribe the fact label and the decisive
record + locator expectation from the gold file; the score is 1 only if the
packet shows all three: surfaced, action changed, and cited with an evidence
locator.

| Fact ID | Gold fact (transcribed from gold file) | Probe ref | Packet ID | Evidence (verbatim quotes; record IDs referenced; cited targets + locators) | Surfaced? Y/N | Action changed? Y/N | Cited decisive record + locator? Y/N | Score 1/0 |
|---|---|---|---|---|---|---|---|---|
| H1 | | | | | | | | |
| H2 | | | | | | | | |
| H3 | | | | | | | | |
| H4 | | | | | | | | |
| H5 | | | | | | | | |

Scoring reminders (`rubric.md` M1):

- Running a memory read and ignoring what it returned scores 0 for that fact.
- A correct action for an incidental reason (no citation) does not count.
- Surfacing must come from the records; an operator-disclosed correction of
  the same content does not by itself earn credit. If the agent first acted on
  the wrong value and corrected after the disclosure, the item can still
  score 1, but only if the correction cites the decisive record with an
  evidence locator.
- Rows beyond the gold list: leave blank, score nothing, contribute no
  denominator.

M1 (this scenario): `____ / ____` (scored / gold |H|) — or **N/A (empty
denominator)** if the gold hidden-fact set is empty.

### 1.4 M2 — Typed durable-event recall / precision

**1.4.1 Gold typed events (fixed denominator).** One row per UNCONDITIONAL
gold typed event, transcribed from the gold file. The gold files state the M2
scope; by default "records(this session)" counts Entry records saved during
the session — Notes written during the session are assessed under M1/M4 and
never enter the M2 numerator or denominator.

| Event ID | Gold event (transcribed from gold file) | Gold type | Recorded? (record ID from packet) | Record type as written | Type matches gold? Y/N | TP / FN | Evidence (verbatim quotes; record IDs referenced; cited targets + locators; pinned turn-time artifact target/hash verified) |
|---|---|---|---|---|---|---|---|
| E1 | | | | | | | |
| E2 | | | | | | | |
| E3 | | | | | | | |

**Turn-time artifact pins (per-event evidence).** Where a gold entry requires
a pinned ref to an evidence artifact created during the session, the
`pinned turn-time artifact target/hash verified` part of the Evidence cell
records the packet-stated: (a) pinned target (neutral locator); (b) the
`sha256:` digest written in the record and the packet-stated digest of the
artifact itself; (c) the packet's attestation that the artifact was dropped
into the workspace at the event's turn — absent from the canonical seed
manifest and not among the scenario text's pre-seeded pinned evidence files.
A turn-time artifact must never be pre-seeded: pre-seeding leaks the event
into the seeded state, where it could be read before its turn. The assessor
verifies from the packet alone: (1) the digest written in the record equals
the packet-stated artifact digest — the record's `sha256:` pin is
runtime-validated against the artifact bytes, so equality confirms the
artifact existed with those exact bytes when the record was written; (2) the
target is not pre-seeded; (3) the attestation places the artifact's first
appearance at the event's turn, so the event could not have been read from
the seeded state before its turn. A packet lacking any of (a)–(c) leaves the
event's evidence unverifiable → score 0 (FN), flagged for the stage notes.
The packet-stated digest also anchors the paired-run byte-identity check:
the same gold event must show the same digest in both anonymous run sheets;
a mismatch is flagged for the stage notes.

**1.4.2 Conditional corrections (outside the fixed denominator).** One row
per gold conditional correction. They never enter the M2 denominator; a
triggered-and-missed replacement is scored under the affected M1 fact and,
if left open at closeout, under M4 item 4.

| Correction | Trigger fired? Y/N | Replacing record produced (right type, cites superseded record)? Y/N | Cross-effect on M1 fact / M4 item 4 | Evidence |
|---|---|---|---|---|
| | | | | |
| | | | | |

**1.4.3 Session records → TP/FP.** One row per Entry record the packet shows
written this session. A true positive matches an unconditional gold typed
event, or is a properly recorded triggered conditional correction (right
type, cites the superseded record, not a duplicate). All other records are
false positives. A record matched to a gold event whose entry requires a
pinned turn-time artifact must carry the same field in its Evidence cell
(per the 1.4.1 note).

| Record ID | Matches gold event? (which) | TP / FP | If FP: class (duplicate of recorded convention / un-triggered correction record / catch-all / wrong type / recorded distractor / other) | Evidence |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
(add rows as needed)

**1.4.4 Computation.**

| Quantity | Value |
|---|---|
| Gold unconditional typed events (denominator) | |
| True positives | |
| **Recall = TP / denominator** | |
| Records written this session (precision denominator) | |
| False positives | |
| **Precision = TP / (TP + FP)** | |

Scoring reminders (`rubric.md` M2):

- A single catch-all closeout covering several heterogeneous gold events is a
  type error for each covered event (each covered event → FN; the catch-all →
  FP), not recall.
- A record of the right event with the wrong type counts against recall AND
  precision.
- Duplicate records of already-recorded conventions, un-triggered correction
  records, catch-alls, wrong-type records, and recorded distractors are
  false positives.
- A scenario with no unconditional gold typed events reports M2 as
  **N/A (empty denominator)**.

### 1.5 M3 — Non-durable rejection (per distractor)

One row per gold scripted distractor, transcribed from the gold file. A
distractor recorded directly, or folded into a catch-all closeout, is a
failure for that distractor (the closeout itself remains scored under M2).

| Distractor ID | Distractor (transcribed from gold file) | Probe ref | Packet ID | Evidence (recorded? how? unrecorded?) | Pass (not recorded) / Fail | Score 1/0 |
|---|---|---|---|---|---|---|
| D1 | | | | | | |
| D2 | | | | | | |

M3 (this scenario): `____ / ____` (passed / gold distractors) — or
**N/A (empty denominator)** if the gold distractor list is empty.

### 1.6 M4 — Resumption checklist (four items)

Scored from the fresh resumption session's packets (session 2), seeded from
the scenario's end state. Each item is 1 if the resumption packet shows the
session demonstrably used the record (named or cited the record the item
lives in), else 0. If the resumption session was not run, M4 is
**N/A (empty denominator)** for this scenario.

| Item | Record the item lives in (transcribed from gold file) | Packet ID | Evidence (record named or cited in the resumption session) | Score 1/0 |
|---|---|---|---|---|
| 1. Current goal | | | | |
| 2. Active route | | | | |
| 3. Next action | | | | |
| 4. Open corrections | | | | |

Scoring reminders (`rubric.md` M4):

- "Open corrections" means records still in force that supersede or revise an
  earlier statement, plus unresolved failures the records flag. Where the end
  state has no open corrections, item 4 is satisfied if the agent verifies
  from the records that none are open; an invented open correction, or an
  ignored real one, scores 0.
- The resumption session's time and tool calls are recorded descriptively,
  never scored.

M4 (this scenario): `____ / 4`

### 1.7 M5 — Cold-start metrics (read-only transcription)

Transcribe exactly what the packet reports from the operator's session-1
instrumentation (`TURN_START(turn 1)`, `FIRST_GROUNDED_PROPOSAL`, `TOOL_CALL`
counter). Read-only: no judgment, no editing, never self-reported by the
agent. M5 is unscorable without instrumentation: if the packet does not carry
run-time timestamps and tool-call counts, mark M5 "unscorable (missing
instrumentation — run-voiding per run-notes §7)" and flag it for the stage
notes; do not reconstruct a value.

| Field | Value |
|---|---|
| Seconds from session start to first grounded proposal | |
| Tool calls from session start to first grounded proposal | |
| Declared budget (turns, tool calls) | |
| Outcome | value pair / **none within budget** (report the budget values) |

### 1.8 Per-run metric summary (this scenario)

| Metric | Value | Denominator | N/A? (state reason) | Flagged probes (stage-notes refs) |
|---|---|---|---|---|
| M1 | | | | |
| M2 recall | | | | |
| M2 precision | | | | |
| M3 | | | | |
| M4 | | | | |
| M5 | (seconds, tool calls) | — | — | |

---

## 2. Pooling worksheet — S1 + S2 (one per anonymous run)

Item-level pooling over the two scenarios of the same anonymous run: sum the
numerators, sum the denominators, then divide. This is NOT an average of
per-scenario scores. M4 pools as 4 items per scenario (8 items over S1+S2).
A metric N/A for a scenario is excluded from pooling for that metric; if the
pooled denominator is then empty, the metric is N/A for the pool and its gate
is not established (reason in the stage notes).

Run ID (anonymous): `__________`

| Metric | S1 numerator | S1 denominator | S2 numerator | S2 denominator | **Pooled value** | N/A? |
|---|---|---|---|---|---|---|
| M1 | | | | | | |
| M2 recall | | | | | | |
| M2 precision | | | | | | |
| M3 | | | | | | |
| M4 | | (4) | | (4) | | |
| M5 | — | — | — | — | reported per scenario; not pooled | — |

---

## 3. S3 — separate sheet, scored first, reported separately

S3 uses the same run sheet (section 1). Its scores are reported SEPARATELY
and FIRST, and never enter the S1 + S2 pooling worksheet or gate totals.
S3's M5 is reported together with S3. S3 is held out: its content is never
used to iterate prompts, Skills, or adapters.

Run ID (anonymous): `__________` — Scenario: S3

| Metric | S3 value | Denominator | N/A? (state reason) |
|---|---|---|---|
| M1 | | | |
| M2 recall | | | |
| M2 precision | | | |
| M3 | | | |
| M4 | | | |
| M5 | (seconds, tool calls) | — | — |

Report order in the stage notes: **S3 first and separately; S1/S2 pooled
values follow.**

---

## 4. Threshold judgment (one table per anonymous run)

Frozen thresholds — mirror of `rubric.md` §Pre-registered thresholds; the
rubric remains the authority. This sheet never revises a threshold; any
revision happens only between stage runs, recorded as a diff in the stage
notes.

| Metric | Frozen threshold (rubric.md) |
|---|---|
| M1 hidden-fact action score | ≥ 0.6 treatment AND > control |
| M2 typed recall | ≥ 0.7 |
| M2 typed precision | ≥ 0.7 |
| M3 non-durable rejection | 1.0 |
| M4 resumption checklist | 1.0 (4/4) |
| M5 cold-start | reported only |

Gate scope: thresholds are evaluated on pooled S1 + S2 treatment metrics; S3
is reported separately and first; a metric with an empty pooled denominator
is N/A and its gate is not established (see `rubric.md` Definitions).

Run ID (anonymous): `__________`

| Metric | Pooled value (S1+S2, this run) | Frozen threshold | N/A? | Judgment (pass / not established / N/A) | Notes |
|---|---|---|---|---|---|
| M1 (absolute part) | | ≥ 0.6 | | | |
| M1 (strict inequality) | | > control | | deferred — resolved at Report time | |
| M2 recall | | ≥ 0.7 | | | |
| M2 precision | | ≥ 0.7 | | | |
| M3 | | 1.0 | | | |
| M4 | | 1.0 | | | |
| M5 | | reported only | — | reported only | |

Judgment notes:

- The M1 absolute part (≥ 0.6) can be judged blind on this run's pooled
  value. The strict-inequality part (> control) requires the sealed condition
  mapping: it is resolved at Report time after the operator unseals the
  mapping, and the verdict is recorded in the stage notes — never guessed
  here.
- Gate scope ("treatment condition") is likewise resolved at Report time.
  Pooled S1+S2 values and the per-scenario sheets above are the assessor's
  complete deliverable for that step.

---

## 5. Assessor attestation (sign on every sheet)

I scored the packets recorded in this sheet from the scoring package only —
per-probe condition-neutral packets, the scenario text, `rubric.md`, the gold
answers, and the frozen thresholds. I did not read raw transcripts,
workspaces, seeds, run notes, or the condition mapping, and I did not attempt
to infer the condition from packet content. I recorded per-probe evidence
verbatim from the packets, and any probe whose packet lacked the required
evidence was scored 0 and flagged for the stage notes.

Assessor: `________________`   Date: `________________`

Scenario: `______`   Run ID (anonymous): `______`
