# M1b adjudication — reviewed freeze revision (2026-08-12)

Status: **adjudication complete; reviewed freeze revision recorded**. The
post-M1a natural-use pause is complete with two ordinary, unscripted
real-Topic sessions. The 2026-08-12 reviewed freeze revision selects the
read-side slice **M1b-R1**; its implementation-level spec is
[`docs/m1b-r1-spec.md`](m1b-r1-spec.md), the implementation is complete,
and its deterministic gate **passed** (evidence recorded in
`docs/m1b-r1-stage-notes.md`). `check` is a shipped, gated contract;
`lineage` is a deferred candidate.

This document is the §0.1 review record required by
[`docs/m1b-spec.md`](m1b-spec.md) §0.1 and `docs/roadmap.md` §Simplicity.
It records actual use, headroom, every A–H disposition with dependencies,
the six followup suggestions, the selected slice, untested claims, and the
attributable approval. It does not authorize M2/M3.

## 1. Evidence

| Evidence | Date | Role |
|---|---|---|
| [`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`](../feedback/2026-08-11-gw-librpa-natural-use-feedback.md) | 2026-08-11 | First ordinary session: one long, unscripted GW/LibRPA session chain (ABACUS/LibRPA SOC development and numerics), with interruption/resume, many entries, remote Slurm evidence |
| [`feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md`](../feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md) | 2026-08-12 | Second ordinary session: an independent real Topic (SU(2) × D_L spectral-spacing) with a genuine correction workflow (challenge → failure Entry → repair → resolve → new closeout) |
| [`feedback/2026-08-12-gw-librpa-followup-feedback.md`](../feedback/2026-08-12-gw-librpa-followup-feedback.md) | 2026-08-12 | Researcher's six followup suggestions (short `enter`, lineage/relations, stale-handoff hint, malformed diagnostics + suppression, empty TOPIC goal hint, structured prepare input) |
| Runtime actual | 2026-08-12 | Canonical runtime = **1,256 nonblank lines** (per `docs/m1a-stage-notes.md`), every module < 400; M1b cap 1,450 → **headroom 194** |

Neither session is a controlled experiment, and neither session alone
authorizes any runtime. The two sessions together satisfy the two-session
ordinary natural-use pause: both are ordinary, unscripted, real-Topic
sessions; the first is a single long session chain and the second is an
independent Topic's independent correction session.

## 2. Pause completed

The post-M1a natural-use pause requirement (at least two ordinary,
unscripted real-Topic sessions plus this short review of actual use, unmet
pain, workarounds, and maintenance cost) is **complete** as of 2026-08-12.
No new gold set or synthetic suite was required for the pause and none was
run.

## 3. Budget reconciliation

Fixed caps are never adjusted: M1a ≤ 1,300 (actual 1,256); M1b ≤ 1,450.
M1b headroom = 1,450 − 1,256 = **194 nonblank lines**, and every module
must stay below 400 nonblank lines. The selected slice's implementation
spec targets ≤ 1,425 cumulative (≤ 169 net lines) and is hard-capped at
1,450; its estimate and cut order are in `docs/m1b-r1-spec.md` §Budget.

**Budget reconciliation addendum (2026-08-12, same day):** an
author-reported prototype of the revised R1 contracts measured **1,413
nonblank lines total (net +157)** — within the 1,425 target with a
37-line margin to the hard cap. The same prototype **with `aitp lineage`
included measured 1,445** (5 lines of cap margin, above the target), so
per the budget rule the slice **re-deferred Followup-2 (`lineage`)**: the
disposition in §4 below and in `docs/m1b-spec.md` §0.1 is recorded as
deferred at this reconciliation, and `lineage` may return only through a
new reviewed freeze revision. Nothing was cut from `check` semantics or
the M1a safety signals to fit the budget. The prototype measurement is
author-reported development evidence (diff hash, module counts, and the
56-test transcript are recorded in `docs/m1b-r1-spec.md` §Implementation
map), **not** gate evidence; the implementation session must reproduce it
independently.

## 4. Reviewed freeze revision — full roster

Every A–H row has exactly one disposition, recorded here and mirrored in
`docs/m1b-spec.md` §0.1. The revision is deliberately conservative: one
read-side slice named **M1b-R1** is selected; nothing else produces an
implementation spec.

| ID | Candidate unit | 2026-08-12 disposition | Boundary and reason |
|---|---|---|---|
| A | Store health: read-only `check` report | **selected in M1b-R1** | Selected only as the **v0.1-only** read-only `check` over current shipped Entry/Note contracts (`docs/m1b-r1-spec.md`); implemented and gated (evidence: `docs/m1b-r1-stage-notes.md`). No `--fix`, no write, no migration, no diagnostics for unselected M1b schemas |
| B | Dependency links: `based_on`, derived `used_by` | **deferred** | Persisted `based_on`, derived `used_by`, and their envelope/schema versioning are all deferred: both natural sessions show narrow, real need, but the write-side schema and the unversioned-envelope rule make them a larger slice. The narrow read-side lineage view is tracked separately as Followup 2 below — it is not a B split |
| C | Open-item schema: `prediction`/`question`/typed closures | **deferred** | Both sessions were served by v0.1 kinds; no session produced a typed open item the current kinds cannot express |
| D | Remote-run pointer bundle + templates | **deferred** | Strong need in the GW session only (remote Slurm evidence); the second session is fully local. Single-session evidence is not enough; templates/Skill conventions already exist non-normatively |
| E | Conditional quick-run experiment | **deferred** | Write friction is real (GW §4.2) but the local-report + one-Entry workaround is workable; the sessions do not show durable events are missed primarily because of write friction. Not selected; remains the first feature cut |
| F | `aitp-collaborator` Skill behavior pilot | **moved to M4** | Unchanged; Skill-only, +0 runtime lines |
| G | Methodology Skills | **independent use-driven Skill track** | Unchanged; outside M1b runtime/schema/gate |
| H | Next-action closure relation | **dropped from M1b** | Unchanged; closeout-first remains the selected solution. The stale-handoff hint below is a structural text signal, not a restored H runtime |
| Followup 1 | Compact `enter` text renderer only (JSON `enter-0.2` unchanged), restoring the two M1a safety lines (`recent_entries: <shown> of <active> active (<omitted> omitted)`; `recent_notes: <shown>; latest_working_note: …; active_newer: <n|unknown>`) | **selected in M1b-R1** |
| Followup 2 | Current-v0.1 lineage projection (`aitp lineage`, schema `aitp/lineage-0.1`: outgoing `resolves`/`supersedes`, incoming `resolved_by`/`superseded_by`; no recursion/graph/index) | **deferred** — selected in R1 at the freeze revision, **re-deferred at the 2026-08-12 budget reconciliation** (measured prototype with lineage: 1,445 — above the 1,425 target with ~5 lines of cap margin). May return only through a new reviewed freeze revision |
| Followup 3 | Stale-handoff text hint (`handoff_status: review`, structural timestamp condition) | **selected in M1b-R1** |
| Followup 4 | Malformed diagnostics + suppression: read-only `check` plus a warning-count summary in `enter` text pointing at it; no persistent suppression | **selected in M1b-R1** |
| Followup 5 | Empty TOPIC goal hint (`goal_status: not_established` in text; `empty_topic_goal` warning in `check`) | **selected in M1b-R1** |
| Followup 6 | Structured JSON/YAML prepare input preserving draft | **deferred (explicit)** — a separate candidate, not a variant of E: it would preserve the draft path but still needs a new input contract, template interplay, and validation order — and its natural evidence is mixed (one session chain). Budget is prioritized for the read-side slice. The draft-preserving property is kept as a design constraint if it is ever re-proposed |

### Text-only hints (not H; not semantic)

The two hints selected for `enter` text are factual structural prompts, both
computed only in the text renderer from existing `enter-0.2` payload fields:

- `goal_status: not_established` — shown when the normalized Topic goal text
  equals the placeholder (`Not established yet`); empty, missing, and
  literal-placeholder sections all normalize to that single value, so one
  exact match covers all three. `check` reads the source with the same rule
  and reports the `empty_topic_goal` warning.
- `handoff_status: review` — shown only when the selected handoff source's
  `created_at` is older than a newer unresolved active failure's
  `created_at`. It never changes `next_action`, never claims semantic
  staleness, and does not restore roster H.

## 5. Selected slice M1b-R1 (frozen scope)

1. **Compact `enter` text renderer only** — `enter-0.2` JSON unchanged,
   byte-for-byte; the text rendering becomes compact and restores the two
   frozen M1a safety lines (`recent_entries: <shown> of <active> active
   (<omitted> omitted)`; `recent_notes: <shown>; latest_working_note:
   <id @ time|(none)>; active_newer: <n|unknown>`), with the warning
   summary and the two text-only hints above. `refs`/`limitations` blobs
   and per-failure details stay out of text.
2. **`aitp check`** — read-only whole-store validation over the current
   shipped v0.1 Entry/Note contracts only, schema `aitp/check-report-0.1`,
   exit 0 clean / 1 findings / 2 unable or misuse; zero-write, no fix, no
   migration; reuses the existing structural validators and evidence
   validation (one code path); frozen no-crash mappings
   (`unreadable_record`, `unreadable_ref`, `malformed_store`,
   `invalid_git_ref` warning/error split; no path raises a traceback);
   invalid timestamps and empty TOPIC goal are warnings; malformed/
   duplicate/pin failures are errors; findings are deterministic by
   `(path, code, message)`.
3. Text-only `goal_status: not_established` on the normalized placeholder.
4. Text-only `handoff_status: review` under the timestamp condition above.
5. `enter` text shows only a warning-count summary with a pointer to
   `aitp check`; JSON keeps the full warnings list. No persistent
   suppression (no config, no state).

`aitp lineage` is **not** in the final slice (Followup 2 re-deferred at the
budget reconciliation — see §3). Implementation-level details, grammar,
help text, exact text/JSON shapes, errors, exit codes, line budget, file
map, tests, goldens, real-store acceptance, version/docs sync, and cut
order are frozen in `docs/m1b-r1-spec.md`.

## 6. Untested claims

The following remain **not measured; deferred; not counted** and are not
claimed by this adjudication or by R1:

- treatment/control, causal, or superiority evidence of AITP over plain
  files (both sessions are uncontrolled natural use);
- bootstrap validation, recall/false-import/human-time, held-out S3,
  paired S1/S2 scores, conformance-suite scores, or treatment advantage
  (unchanged from the M0.6/M1a closures; FROZEN v6 remains an anchored,
  unexecuted preregistration);
- any claim that R1's read-side features improve research outcomes — R1 is
  an implementation-stage decision justified by observed pain points, not a
  scored experiment;
- any claim that the GW or Power-law stores are "health-checked" in a
  research-quality sense: the R1 gate records **observed dynamic snapshots**
  (counts, finding codes, exit codes consistent with the reports, and
  byte-identical `.aitp` trees before/after) as read-only compatibility
  evidence — not a health certificate, not fixed values, and not a claim
  that the recorded findings are anything other than record-state
  diagnostics;

## 7. Approval record

- The researcher directed continuation of development on 2026-08-12
  (conversation instruction, Chinese: 继续做下一步开发), with the six
  followup suggestions listed in `feedback/2026-08-12-gw-librpa-followup-feedback.md`
  given in the same chain.
- Together these are the **attributable approval** for this freeze
  revision and for drafting the M1b-R1 implementation spec and its
  planning-state synchronization. The approval is recorded from the
  conversation instruction and the suggestions; no signature is fabricated
  and no named individual is quoted beyond the instruction's own wording.
- This approval **selects** R1 and authorizes drafting the spec; it does
  **not** green-light implementation. R1 implementation requires the
  separately reviewed implementation spec (`docs/m1b-r1-spec.md`) per the
  roadmap's stage-authorization rule — the spec is **pending green-light**,
  not yet green-lit — and then its own deterministic gate evidence recorded
  in `docs/m1b-r1-stage-notes.md`.
- Status note (implementation session, 2026-08-12): the spec's separate
  review/green-light was subsequently granted and the R1 implementation
  landed in the working tree (see the status header above); the
  deterministic gate **passed** on 2026-08-12 with its evidence recorded in
  `docs/m1b-r1-stage-notes.md`. The "pending green-light" wording above
  records the state at approval time only; it is superseded by this status
  note for the current boundary. This approval record itself
  stands as written.

## 8. Consequences for other documents

The 2026-08-12 freeze revision is mirrored in `docs/m1b-spec.md` §0.1
(status: reviewed freeze revision; R1 selected — `check` + compact `enter`
text — implemented per `docs/m1b-r1-spec.md`, deterministic gate passed
with evidence in `docs/m1b-r1-stage-notes.md`,
with the Followup roster and the Followup-2
budget-reconciliation re-deferral recorded). `docs/roadmap.md` (v3.10),
`README.md`, `AGENTS.md`,
`docs/m1-read-write-balance.md`, `docs/design.md`, `docs/m1a-stage-notes.md`,
the `docs/hakimi/` handoff, and the `using-aitp` Skill
are synchronized in the same change. The current CLI is
`init`, `enter`, `inventory`, `record`, `note`, `list`,
`show`, and `check` (`check` shipped and gated); `lineage` is a
deferred candidate and must not be invoked or described as shipped.
