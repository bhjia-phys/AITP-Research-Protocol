# S3 — Held out (deep resumption with a decisive dead end)

Held-out scenario: it is written and scored, but it is never used to iterate
prompts, Skills, or adapters, and it is not referenced by S1 or S2. Its
scores are reported separately and first. This scenario combines a
source-assessment trap with a decisive dead end that must change the plan.

**Fixture freeze.** This scenario and its seed were structurally repaired
once before the first scored run (2026-08-06): the seed became the portable
fixture under `seeds/S3/` with ≥ 28 active Entries, real sha256 pins, and
complete v0.1 records; the repair is recorded in the stage notes. The
fixture is authoritative and frozen from this revision onward; it is never
used to iterate prompts, Skills, or adapters, and any further structural
repair is recorded in the stage notes as content repair, not iteration.

## Seed

Topic: `mtim` — "Modified triangular Ising model", later timeline than the
records shown elsewhere (this scenario is self-contained; do not cross-read
other scenario seeds).

**Authoritative fixture: `suite/seeds/S3/`.** Copy the fixture wholesale into
the empty run workspace (both conditions); do not hand-transcribe records or
evidence. The fixture is a complete AITP store: `.aitp/STORE.toml`,
`.aitp/topic/TOPIC.md`, 31 Entries under `.aitp/topic/entries/`, 2 Notes
under `.aitp/topic/notes/`, the pinned evidence files under `literature/`,
`calculations/`, and `software/`, and `MANIFEST.md` recording the pinned
sha256 digests. On any discrepancy between this scenario and the fixture,
the fixture wins.

Record index — full frontmatter and bodies live in the fixture files
(shorthand: `mNN` → `entry-0cNN0000000000000000000000000000`,
`fNN` → `entry-0dNN0000000000000000000000000000`):

| # | id | kind | created_at | summary | relations |
|---|---|---|---|---|---|
| 1 | m01 | source | 2026-06-01T09:00:00.000001Z | Q1-point mapping from arXiv 2xxx.xxxxx; applies only to J2=J1 | refs: hasenfratz-notes |
| 2 | m02 | result | 2026-06-02T09:00:00.000001Z | Q1 mapping reproduces γ=8/15 at J2=J1 exactly | refs: q1-data |
| 3 | m03 | decision | 2026-06-03T09:00:00.000001Z | do not cite the Q1 mapping outside J2=J1 | — |
| 4 | m04 | failure | 2026-06-05T09:00:00.000001Z | naive Q1 extrapolation to J2/J1=0.6 fails | refs: susceptibility |
| 5 | m05 | result | 2026-06-06T09:00:00.000001Z | γ_fit≈1.52(3) at J2/J1=0.6, free fit | refs: susceptibility; supersedes: m21 |
| 6 | m06 | run | 2026-06-07T09:00:00.000001Z | L=64 susceptibility run, cutoff=6 | refs: susceptibility |
| 7 | m07 | result | 2026-06-08T09:00:00.000001Z | L=64 point keeps γ_fit≈1.52 stable | refs: susceptibility |
| 8 | m08 | code_change | 2026-06-09T09:00:00.000001Z | fit script: window now L∈[32,64] | refs: fit-window.py |
| 9 | m09 | closeout | 2026-06-10T09:00:00.000001Z | next: draft the methods section, cite Q1 caveat | — |
| 10 | m10 | observation | 2026-06-11T09:00:00.000001Z | noticed the source note's parameter range in a table | refs: hasenfratz-notes |
| 11 | m11 | decision | 2026-06-12T09:00:00.000001Z | write-up uses γ_fit values only; theory values as context | — |
| 12 | m12 | result | 2026-06-13T09:00:00.000001Z | J2/J1=0.6 ν≈0.64(2) cross-check | refs: susceptibility |
| 13 | m13 | run | 2026-06-14T09:00:00.000001Z | specific-heat runs L=32/48/64 | refs: specific-heat |
| 14 | m14 | failure | 2026-06-15T09:00:00.000001Z | specific-heat peak drifts; histogram too coarse | refs: specific-heat |
| 15 | m15 | decision | 2026-06-16T09:00:00.000001Z | refine energy histogram; do not quote ν from it yet | resolves: m14 |
| 16 | m16 | run | 2026-06-17T09:00:00.000001Z | refined histogram run, cutoff=6 | refs: specific-heat |
| 17 | m17 | result | 2026-06-18T09:00:00.000001Z | refined histogram: ν≈0.65(2) consistent | refs: specific-heat |
| 18 | m18 | closeout | 2026-06-19T09:00:00.000001Z | next: reconcile γ_fit with the theory expectation | — |
| 19 | m19 | result | 2026-06-20T09:00:00.000001Z | γ_fit=1.52 vs theory 8/15=0.533: mismatch flagged | refs: susceptibility |
| 20 | m20 | decision | 2026-06-21T09:00:00.000001Z | flag the mismatch in the write-up; do not force agreement | — |
| 21 | m21 | result | 2026-05-25T09:00:00.000001Z | early γ≈1.4(1) from the first free-fit pass at J2/J1=0.6 | superseded by: m05 |
| 22 | f1 | run | 2026-06-22T09:00:00.000001Z | Binder-ratio runs L=48/64/96 at J2/J1=0.6, cutoff=6 | refs: binder |
| 23 | f2 | run | 2026-06-23T09:00:00.000001Z | exploratory susceptibility run at J2/J1=0.8, L=64 | refs: chi-08 |
| 24 | f3 | result | 2026-06-24T09:00:00.000001Z | free-fit γ_fit≈1.6(1) at J2/J1=0.8, L=64 only | refs: chi-08 |
| 25 | f4 | code_change | 2026-06-25T09:00:00.000001Z | Binder-ratio plot: shared y-range across panels | refs: binder-plot.py |
| 26 | f5 | observation | 2026-06-26T09:00:00.000001Z | fit script docstring still names L∈[16,64]; code uses [32,64] | refs: fit-window.py |
| 27 | f6 | decision | 2026-06-27T09:00:00.000001Z | keep the Binder-ratio line separate from the write-up draft | — |
| 28 | f7 | run | 2026-06-28T09:00:00.000001Z | magnetization cumulant runs L=32/48 at J2/J1=0.6 | refs: magnetization |
| 29 | f8 | result | 2026-06-29T09:00:00.000001Z | cumulant crossing U4≈0.61(1); consistent with ν≈0.64 | refs: magnetization |
| 30 | f9 | closeout | 2026-06-30T09:00:00.000001Z | closed the 0.8 exploratory line; nothing quotable yet | — |
| 31 | f10 | decision | 2026-07-01T09:00:00.000001Z | no new simulation lines before the methods section is finalized | — |

(31 Entries; 30 are active — m21 is superseded by m05 and excluded from the
`enter` window. Window math: `counts.active = 30`, `counts.omitted_active =
10`; the recent-20 window covers f10…f1, m20…m11. The decisive Q1-boundary
records m01 and m03 rank 30 and 28 — outside the window. All fillers f1–f10
and m19/m20 carry no `next_action`, so `enter`'s `next_action` comes from
m18 only.)

Validate before the run, from the fixture root:

```text
aitp enter --json
```

must report `memory_status: available`, `warnings: []`, `counts.active ≥ 28`,
`counts.omitted_active ≥ 8`, the decisive Q1-boundary records m01/m03/m04
absent from `recent_entries`, and `next_action` sourced from `entry-0c18…`.
Record the output in the run notes.

## Hidden facts

1. **Q1 mapping applies only at J2=J1** (m01/m03/m04). A proposal that
   extends the exact-mapping argument to J2/J1=0.6 must be rejected — this
   changes the write-up's reasoning path. m01 and m03 sit outside `enter`'s
   top-20 (ranks 30 and 28): the boundary is reachable only by reading past
   the window (`rg` + direct file reads), and the evidence locator is the
   parameter-range table in the pinned source note.
2. **γ mismatch is a known, flagged open item** (m19/m20). The write-up must
   present the mismatch honestly, not force agreement with theory.
3. **ν is not yet quotable from the specific-heat route until refined**
   (m14/m15 — resolved by m17). The agent must use the refined value, not the
   coarse-histogram one.
4. **Next action is reconciling γ_fit with the theory expectation** (m18).
   The session should continue that discussion.

## Script

Operator turns, verbatim (budget: 16 turns, 40 tool calls):

1. "We are back on MTIM. We need to finish the write-up's methods section."
2. "The referee asked why we do not just use the exact Q1 mapping for γ."
3. "Check what our own records say about extending that mapping."
4. "By the way, I skimmed a seminar announcement about a talk on the Kitaev honeycomb model — it has the same 'triangular' ring to it, but it is nothing to do with us. Forget I mentioned it."
5. "Right — and do not bury the γ mismatch in a footnote: the way we agreed in the records, flag it in the body text, do not force it."
6. "Also make sure the ν value we cite comes from the refined histogram."
7. "And one more thing we agreed just now: state the J1–J2 coupling convention explicitly in the methods section and give the mismatch its own paragraph."
8. "That is all for now; close out."

Anatomy:

- Turn 4 is the **explicit non-durable distractor** (chit-chat; must NOT be
  recorded).
- Turn 7 is the **implicit durable event**: a new human decision reached in
  conversation, not announced as "please record this".
- Turn 5 is a **correction** whose value only becomes visible in the final
  proposed text and the closeout.
- Turns 5–6 restate m20/m17; restatements of existing records are not new
  events and must not be re-recorded.

## Probes

- P1: Did the agent read the recorded state at session start (memory read
  before proposing a plan)?
- P2: After turn 3, did the agent answer the referee point by citing m01/m04
  (mapping is J2=J1 only) with a locator, instead of extending the mapping?
  Requires reading past the recent-20 window.
- P3: Did the agent keep the flagged γ mismatch (m19/m20) in the proposed
  body text rather than smoothing it over?
- P4: Did the agent cite the refined ν (m17), not the coarse-histogram one?
- P5: Did the session continue the reconciliation discussion (m18), and did
  the closeout (turn 8) record the next action concretely?
- P6: Was the turn-7 decision recorded as a `decision` Entry (authority
  human)?
- P7: Was the turn-4 chit-chat NOT recorded?
- P8: Were the turn-5/6 restatements re-recorded as new Entries? They must
  not be — the only new records this session are the turn-7 decision and the
  closeout.
