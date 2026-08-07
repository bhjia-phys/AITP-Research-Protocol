# Conformance suite rubric

Metrics and pre-registered thresholds. The thresholds below are FROZEN before
the first scored run; they are not negotiated per run. They may be revised
only between stage runs, with the diff recorded in the stage notes.

This file is the scoring contract. It operationalizes how each metric is
scored, pooled, and gated without changing any frozen threshold. The scenario
files carry the concrete seeds, scripts, and probes; the gold files carry the
assessor-only answers.

## Run contract

The suite is an evaluation protocol executed by a human operator with an agent
under test. It has zero runtime: no automated harness, no LLM judge, and no CI
integration participates in scoring. Preconditions for a valid run:

- **Isolation.** The agent under test operates only inside the isolated
  seeded workspace. The only suite artifacts it may see are the byte-identical
  `policy.md` copy and its condition's adapter, both placed inside that
  workspace. It must not be given the repository, `scenarios/`, `gold/`, this
  rubric, or any other suite file. Evidence that an agent response drew on
  those files voids the run.
- **Condition symmetry.** Treatment and control differ ONLY in the I/O
  adapter. Both conditions use the same model, the same fixed system prompt
  (as declared in the run notes), the same `policy.md` bytes (sha256 recorded
  in the run notes), the same seed copies (verified byte-identical), the same
  script, and the same declared budgets (turns, tool calls, wall clock). Any
  other difference voids the run.
- **Seed window.** The seed's window is measured on active Entries: valid
  seeded Entries minus those superseded by another seeded Entry, as projected
  by the `enter` active-state semantics. A valid seed has at least 28 active
  Entries, and at least one decisive memory-gated fact whose decisive record
  is outside the recent-20 window (not among the 20 most recent active
  Entries), so passive top-of-window reading cannot surface it.
- **Fixture validity.** Every seeded Entry and Note must be valid v0.1
  Markdown as the runtime validator enforces: parseable frontmatter with the
  correct schema, all required fields, kind-appropriate non-empty sections,
  and no unfilled template markers; fixed IDs and `created_at` timestamps;
  complete refs, limitations, and body; and sha256 pins that match the actual
  bytes of the pinned evidence files. Filler records leave `next_action` empty
  so the window projection surfaces the scenario's designated next action.
- **Gold is never seeded.** No content from `gold/` enters a seeded workspace;
  a violation voids the run.

## Definitions

- **Memory-gated fact** — an item of the scenario's gold hidden-fact set `H`.
  Its decisive evidence exists only in the seeded records, and no script turn
  states it before the agent's first opportunity to act on it. Memory-gated
  facts are scored by M1, which requires the fact to be surfaced from the
  records.
- **Operator-disclosed correction** — a script turn in which the operator
  states a correction, decision, or convention in the conversation. It is not
  a memory-gated fact. It is scored as a typed durable event when it is a
  durable event, and it may trigger a conditional correction.
- **Conditional correction** — a gold typed event whose expectation is
  conditional: a replacing record is required only if the agent first acts on
  the superseded value (a misquote or wrong-value use). Conditional
  corrections are excluded from the M2 typed-event denominator. When the
  trigger fires and the agent does not produce the replacing record, the
  underlying memory-gated fact scores 0 for M1, and if the correction is left
  open at closeout, M4 item 4 scores 0; the failure is recorded in the
  per-probe evidence.
- **Unconditional gold typed event** — a gold typed event the script requires
  to be recorded regardless of agent behavior. These alone form the M2
  denominator.
- **Duplicate rule** — restating an already-recorded convention produces no
  new record; a duplicate record of an existing convention is a false positive
  for M2 precision.
- **Empty denominator (N/A)** — when a metric's gold denominator is empty for
  a scenario (for example, a scenario with no unconditional gold typed events
  or no scripted distractors), the metric is N/A for that scenario: it is
  excluded from pooling for that metric, never scored as 0 or 1, and reported
  as "N/A (empty denominator)". If, after exclusion, a metric's pooled
  denominator is also empty, the metric is N/A for the pool and its gate is
  reported as not established, with the reason in the stage notes.
- **Pooling** — M1–M4 are pooled at the item level over S1 + S2: numerators
  are summed and denominators are summed, then divided. This is not an average
  of per-scenario scores. S3 is scored with the same rubric but is reported
  separately and first, and is never pooled with S1/S2.

## Metrics

### M1 — Hidden-fact action score

Definition: among the scenario's hidden facts (`H`, the memory-gated facts),
the fraction that (a) surfaced in the session, (b) changed the corresponding
concrete action, and (c) did so with a citation to the decisive record and an
evidence locator.

Formula:

```text
M1 = |{h in H : surfaced(h) AND action-changed(h) AND cited(h)}| / |H|
```

- Running a memory read and ignoring what it returned scores zero for that
  fact.
- A correct action for an incidental reason (no citation) does not count.
- `H` is the hidden-fact set defined in the scenario's gold answers; every
  item in `H` is a memory-gated fact.
- Surfacing must come from the records. An operator-disclosed correction of
  the same content does not by itself earn credit: an agent that merely echoes
  the operator's words without reading the decisive record has not surfaced
  the fact. If the agent first acts on the wrong value and corrects after the
  disclosure, the item can still score 1, but only if the correction cites the
  decisive record with an evidence locator.
- The citation must name the decisive seeded record fixed in the gold
  answers, with an evidence locator in that record. A record the agent writes
  this session that duplicates or restates the historical decision is not the
  decisive record and cannot substitute for it — the fact is memory-gated and
  must be surfaced from the seeded records, not re-created in a new entry.

Pre-registered thresholds: **M1 ≥ 0.6 in the treatment condition AND
strictly above the control condition on the same scenarios.**

### M2 — Typed durable-event recall / precision

Definition: against the scenario's gold typed-event list, the fraction of
events recorded with the correct type (recall) and the fraction of records
written this session that match a gold typed event (precision).

Formula:

```text
recall    = |records(this session) ∩ gold typed events| / |gold typed events|
precision = |records(this session) ∩ gold typed events| / |records(this session)|
```

- A single catch-all closeout covering several heterogeneous gold events is
  scored as a type error for each covered event, not as recall.
- A record of the right event with the wrong type counts against recall and
  precision.
- The recall denominator is the unconditional gold typed events only;
  conditional corrections never enter the denominator.
- Precision is scored over the records written this session. A record is a
  true positive if it matches an unconditional gold typed event, or is a
  triggered conditional correction properly recorded (right type, cites the
  superseded record, not a duplicate). Duplicate records of already-recorded
  conventions, un-triggered correction records, catch-alls, wrong-type
  records, and recorded distractors are false positives.
- Gold files mark each typed event as unconditional or conditional, and state
  the trigger for each conditional correction.
- A typed event matches on substance: a record that captures the gold event's
  content scores recall even when worded differently; phrasing alone never
  costs recall. A closeout's next action must be concrete and
  evidence-grounded: it may be the projected next action, or — if the
  session's new results supersede it — the new action with the basis stated
  (which result or record takes the action over).

Pre-registered thresholds: **typed recall ≥ 0.7 AND precision ≥ 0.7.**

### M3 — Non-durable rejection

Definition: the fraction of scripted distractors (chit-chat, undeveloped
ideas, discarded proposals) that were NOT recorded.

Formula:

```text
M3 = |distractors not recorded| / |distractors in script|
```

- A distractor recorded directly is a failure for that distractor.
- A distractor folded into a catch-all closeout is a failure for that
  distractor (the closeout itself remains scored under M2).
- A scenario whose gold distractor list is empty reports M3 as N/A (empty
  denominator), per the Definitions.

Pre-registered threshold: **M3 = 1.0 (100% rejection).**

### M4 — Resumption checklist

Definition: M4 is scored on a separate fresh session run AFTER the main
session, seeded from the scenario's end state — the workspace as the agent
left it after the main session, in a new conversation under the same
condition, model, prompt, and policy. The main session's transcript does not
score M4. Four items must each be checkable against the records:

1. current goal;
2. active route;
3. next action;
4. open corrections.

The assessor reads only the resumption session's condition-neutral evidence
packet — the mechanically extracted verbatim agent evidence from that
session, per the scoring procedure — never the raw resumption transcript or
the live end state. Each item is 1 if the packet's verbatim evidence
demonstrably used the end-state record or file the gold answers name for
that item (named or cited that record or file), else 0. Each of the four
items must reference an end-state record or file; restating the content
without naming its record or file scores 0.

Formula:

```text
M4 = (goal + route + next + corrections) / 4
```

- "Open corrections" means records still in force that supersede or revise an
  earlier statement, plus unresolved failures the records flag. Where the end
  state has no open corrections, item 4 is satisfied if the agent verifies
  from the records that none are open; an invented open correction, or an
  ignored real one, scores 0.
- Item 4 requires the agent to honestly enumerate the unresolved failures and
  open corrections that the ledger projection and the records mark as open
  (the unresolved-failure projection and the failure or superseding records
  that carry them). Renaming them into generic or unrelated "open questions"
  does not satisfy the item; the session must name them as what the records
  flag them to be.
- The resumption session has its own declared budget (small; declared in
  the README/run notes before the first paired run). If the resumption
  session was not run, M4 is N/A for that scenario (see Definitions) and the
  omission is recorded in the stage notes.

Pre-registered threshold: **M4 = 1.0 (4/4).**

### M5 — Cold-start metrics

Definition: per condition and per scenario, the wall-clock time and the number
of tool calls from session start to the first grounded proposal — the first
agent turn containing a proposal (plan, answer, or written text) that cites
recorded evidence with a locator. Determined post hoc: the operator records,
for every script turn, the wall-clock time and the agent's cumulative
tool-call count; M5 is read off these artifacts after the run, never
self-reported by the agent. If no grounded proposal occurs within the budget,
report "none within budget" with the budget values and both components.

Formula:

```text
M5 = (seconds_to_first_grounded_proposal, tool_calls_to_first_grounded_proposal)
```

No pre-registered threshold; reported as descriptive evidence, per run, per
condition, per scenario (S3's M5 reported together with S3).

## Scoring procedure

1. **Archive.** The operator archives the transcript and final workspace
   state per condition per scenario under `suite/runs/<date>/`, with per-turn
   wall-clock timestamps and cumulative tool-call counts, and — for every
   conditional script turn — the verbatim trigger evidence from the preceding
   agent output, or a record that the trigger did not fire and the turn was
   not sent.
2. **Condition-neutral evidence packets.** The operator extracts per-probe
   evidence into packets that cannot reveal the condition: agent text quoted
   verbatim, record IDs referenced, cited targets and locators, timestamps,
   and tool-call counts, with tool names, command invocations, executable
   names, and condition-identifying paths (e.g. `.aitp`, CLI command names)
   normalized to neutral labels (`memory-read`, `record-write`, `search`,
   `<workspace>`, `<ledger>`). Mechanical traces must not reach the assessor.
   Packet order is randomized across conditions before scoring.
3. **Per-probe scoring.** Each probe in the gold file states the evidence
   required, the decision rule (1/0 or a count), and when it is N/A. M1 and M4
   items come from the gold hidden-fact answers; M2 uses the gold typed-event
   list; M3 uses the gold distractor list. The assessor scores one metric at a
   time across all packets, recording per-probe evidence in the score sheet. A
   probe whose packet lacks the required evidence scores 0, flagged in the
   stage notes. The assessor reads only the packets, the gold answers, and
   this rubric — never the live workspace, the raw transcripts, or the seeds.
4. **Gate scope.** M1–M4 thresholds are gates on the treatment condition,
   computed on pooled S1 + S2 items. M1 additionally requires treatment pooled
   M1 strictly above control pooled M1 on the same item set; equality, or an
   empty control denominator, means the strict-inequality gate is not
   established. The control condition is scored with the identical rubric, and
   all five of its metrics are reported completely (per scenario and pooled)
   as descriptive comparisons; only M1 participates in a gate.
5. **M4 resumption.** M4 is scored from the resumption session per the M4
   definition; if the resumption session was not run, M4 is N/A for that
   scenario.
6. **S3.** S3 is scored first and reported separately, never pooled; its
   numbers do not enter the S1 + S2 gate totals.
7. **Budget.** A run exceeding its declared budget ends and scores what
   exists.
8. **Single paired run.** One paired run (one treatment and one control per
   scenario) yields point comparisons only. No statistical significance — no
   p-values, confidence intervals, or significance claims — is computed or
   claimed from a single run; the M1 strict inequality is a deterministic
   point comparison, not a statistical test.

## Pre-registered thresholds (frozen)

| Metric | Threshold |
|---|---|
| M1 hidden-fact action score | ≥ 0.6 treatment AND > control |
| M2 typed recall | ≥ 0.7 |
| M2 typed precision | ≥ 0.7 |
| M3 non-durable rejection | 1.0 |
| M4 resumption checklist | 1.0 (4/4) |
| M5 cold-start | reported only |

Gate scope: thresholds are evaluated on pooled S1 + S2 treatment metrics (M4
pooled as 4 items per scenario). S3 is reported separately and first; a metric
with an empty pooled denominator is N/A and its gate is not established (see
Definitions).

## Revision rule

Thresholds are revised only between stage runs; any revision is recorded as a
diff in the stage notes, never silently.
