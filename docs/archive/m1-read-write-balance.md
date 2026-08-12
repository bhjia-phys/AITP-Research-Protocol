# M1 Read/Write Balance

Status: M1 specification index; M1a **done; deterministic gate passed**; M1b
natural-use pause **complete** — the 2026-08-12 reviewed freeze revision
(`docs/m1b-adjudication.md`) selected the read-side slice **M1b-R1**,
implemented per `docs/m1b-r1-spec.md` with its deterministic gate **passed**
(evidence recorded in `docs/m1b-r1-stage-notes.md`);
M2/M3 remain design options.
The M1a implementation and gate evidence are recorded in
[`docs/m1a-stage-notes.md`](m1a-stage-notes.md). This document
keeps the M1 problem, dogfood evidence, request crosswalk, implementation order,
and sync discipline. `docs/m1a-spec.md` remains the implementation-level spec;
`docs/m1b-spec.md` is the candidate-inventory pre-spec under its recorded
2026-08-12 reviewed freeze revision. Its authoritative
A–H roster is §0.1, and the selected-slice implementation spec
`docs/m1b-r1-spec.md` follows the completed natural-use pause, adjudication,
and fixed-cap reconciliation (headroom 194). This index does not itself
authorize additional runtime scope.

## Problem

The M0 ledger is deliberately strong at writing: templates, limitations,
idempotency keys, append-only supersession, and evidence pins make durable
records disciplined. Dense-ledger dogfooding exposed the complementary
problem: a store can be correctly written yet difficult to navigate, connect,
and resume.

The goal is a read/write-balanced protocol without turning AITP into a search
engine, task manager, remote filesystem, or weak-evidence capture tool.

## Dogfood evidence

A read-only audit of `/home/bhjia/physics/GW_librpa` on 2026-08-06 found:

- 60 `aitp/lite-entry-0.1` Entries: 41 active, 19 superseded, 26 results,
  eight kinds represented, and no migration requirement;
- only three closeouts and no Notes, so a long result chain had little
  synthesis or handoff structure;
- `enter` could parse all 60 records but could only orient the session; it
  could not directly answer "show all results" or open one exact Entry;
- the selected next action came from the newest active timestamp, including
  backfilled timestamps, rather than from an explicit current handoff;
- 201 local sha256 pins, of which the dated snapshot had 37 missing targets
  and 78 mismatches; `enter` correctly remained readable, but no whole-store
  diagnostic summarized the drift;
- 22 external `retrieved` pins were valid HTTP source observations; they did
  not solve remote-run evidence, whose important paths lived on another host;
- the store is not a test namespace. Writing synthetic acceptance Entries
  would permanently alter real research memory.

These are product findings, not permission to weaken validation. In
particular, a changed local document is evidence drift, not a reason to treat
a retrieval timestamp as an integrity pin.

The first natural-use feedback is
[`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`](../feedback/2026-08-11-gw-librpa-natural-use-feedback.md)
(2026-08-11): one long session chain in `/home/bhjia/physics/GW_librpa`; the
second ordinary session is
[`feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md`](../feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md)
(2026-08-12, an independent real-Topic correction session). Together they
complete the two-session ordinary natural-use pause. The researcher's six
followup suggestions are archived in
[`feedback/2026-08-12-gw-librpa-followup-feedback.md`](../feedback/2026-08-12-gw-librpa-followup-feedback.md).
The 2026-08-12 reviewed freeze revision in
[`docs/m1b-adjudication.md`](../docs/m1b-adjudication.md) revises the A–H
dispositions (A selected in M1b-R1 v0.1-only; B deferred; C–E deferred;
F → M4; G independent; H dropped) and adjudicates the six followup
suggestions (Followups 1/3/4/5 selected in M1b-R1; Followup 2 `lineage`
re-deferred at the budget reconciliation; Followup 6 structured prepare
deferred). Neither session is a controlled experiment.

## Governing constraints

- Existing v0.1 Entries and Notes are never migrated or rewritten.
- New frontmatter fields are optional and land only in a versioned schema.
- `refs` remain evidence pins; relation fields never replace evidence.
- `enter`, `list`, and `show` are projections; a selected and shipped `check`
  would be a read-only diagnostic. None is a semantic ranking engine.
- No persistent search index is introduced; Markdown remains canonical.
- Remote paths are metadata unless a locally pinned manifest makes their
  contents auditable.
- Quick capture, if justified, reuses the same validator, lock, idempotency,
  and save path as ordinary records.
- The canonical runtime is only
  `plugins/aitp-research-protocol/scripts/vendor/aitp/`; installed managed or
  cached plugin copies are never hand-maintained.
- The binding evidence-before-complexity ratchet, stage authorization, fixed
  caps, and post-M1a pause are in [`docs/roadmap.md`](roadmap.md#simplicity-and-stage-authorization).
- The exhaustive A–H roster, dispositions, and no-runtime rule are in
  [`docs/m1b-spec.md` §0.1](m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions).

## Disposition of the ten requests

| Request | Decision | Stage |
|---|---|---|
| `aitp list` | Primary dense-store retrieval view | M1a |
| optional `based_on` and reverse links | Roster B: narrow dependency only; never replaces `refs`; disposition follows natural-use review | M1b inventory |
| next-action closure relation | Roster H: dropped; closeout-first is sufficient absent new evidence; no silent scope growth | M1a discipline |
| `record quick` | Roster E: deferred, conditional run-only experiment; only if measured | M1b roster |
| run/source execution fields | Roster D: deferred templates/Skill conventions, not a broad schema | M1b roster |
| raw `host:path` refs | Roster D boundary: not evidence pins; use local pointer manifests | M1b roster |
| automatic pin grading | Reject; retain explicit schemes and improve diagnostics | M1a/M1b |
| implicit last-enter increment | Reject; use explicit deterministic `--since` | M1a |
| Note trigger and coverage hint | Skill trigger plus structural age count | M1a |
| methodology Skills `surveying-literature` / `analyzing-a-source` | Roster G: independent use-driven Skill track, outside M1b runtime/schema/gate | independent track |
| Skill synchronization | Required whenever behavior changes | every stage |

## Implementation order

M1 work follows the roadmap and frozen specs. M1a is complete; this index does
not authorize additional runtime scope:

1. **M0.6 gate review** — the 2026-08-10 decision closed M0.6 under the
   narrowed reviewed claim and accepted the original bootstrap Notes/decisions,
   recall/false-import/human-time, held-out S3, paired S1/S2, cold-start,
   conformance, causal, and treatment-advantage evidence as **not measured;
   deferred; not counted**. FROZEN v6 remains an anchored, unexecuted
   preregistration and does not retroactively satisfy those gaps.
2. **M1a** — the frozen `docs/m1a-spec.md` implementation is complete. Its
   deterministic S1/S2 regression, generated goldens, all tests, read-only
   byte-identical GW_librpa acceptance, performance, and 1,300-line gates passed;
   evidence is in `docs/m1a-stage-notes.md`. Treatment-control paired evidence
   is optional future evidence, not a required M1a gate.
3. **Natural-use pause** — **complete**: the two ordinary, unscripted
   real-Topic sessions (GW 2026-08-11; Power-law Heisenberg 2026-08-12) plus
   this review of use, unmet pain, workarounds, and maintenance cost. No new
   gold set or synthetic suite was required.
4. **M1b adjudication** — **recorded 2026-08-12** in
   `docs/m1b-adjudication.md`: actual fixed-cap headroom is 194 (1,450 −
   1,256); every A–H row and every followup suggestion got exactly one
   disposition with the full roster and dependencies; deferred, moved,
   dropped, and no-runtime outcomes produce no implementation spec; the
   selected slice's spec is separately reviewed and green-lit afterward.
   The revision selects **M1b-R1** (read-side): v0.1-only `check` plus the
   compact `enter` text; Followup 2 (`lineage`) was re-deferred at the
   budget reconciliation (measured prototype with lineage leaves
   insufficient cap margin — see §Scope and cut order and
   `docs/m1b-r1-spec.md` §Budget).
5. **Selected slice** — **M1b-R1** is selected, implemented per
   `docs/m1b-r1-spec.md`, and its deterministic gate **passed** (evidence in
   `docs/m1b-r1-stage-notes.md`: independent review with no S0/S1/S2
   blockers, 78 tests, benchmark final PASS, 1,423-line runtime within the
   1,425 target and 1,450 cap, goldens, S1/S2 regression, read-only
   byte-identical GW/PH acceptance). Only that spec was implemented and
   gated, preserving
   required validation, v0.1 compatibility, and no-index boundaries. F is moved
   to M4 and does not force any A–E selection now; M4 adjudication must resolve
   dependencies. If the selected collaborator protocol requires typed
   `prediction`/`question` records, C or an explicitly reviewed equivalent
   contract must first be selected and shipped. G and H remain outside M1b
   runtime/schema/gate scope. Leave v0.1 records and GW_librpa untouched.
6. A no-runtime M1b result closes only that decision point and does not authorize
   M2; M2/M3 require their own natural-demand adjudication.

## Sync discipline: the seven-piece set

A stage that changes command behavior updates all seven artifacts in the same
change (see the "Skill synchronization" row above; runtime, golden fixtures,
and the conformance suite change under the stage spec's own rules — budget
caps, fixture regeneration — and the seven pieces must not drift from them):

| # | Artifact | Role |
|---|---|---|
| 1 | `docs/roadmap.md` | stage status, scope, gates |
| 2 | `docs/design.md` | canonical command contracts |
| 3 | `docs/m1-read-write-balance.md` | this index: product rationale, rejections, order |
| 4 | `docs/m1a-spec.md` | M1a implementation-level spec (frozen before M1a work) |
| 5 | `docs/m1b-spec.md` | M1b candidate-inventory pre-spec, design freeze; 2026-08-12 reviewed freeze revision recorded (§0.1); selected-slice implementation-level spec is `docs/m1b-r1-spec.md` (M1b-R1, implemented; deterministic gate passed) |
| 6 | `plugins/aitp-research-protocol/skills/using-aitp/SKILL.md` | agent-facing command map; future-command sync checklist |
| 7 | `README.md` | user-facing "Current state" command overview |

The `using-aitp` Skill keeps a future-command checklist naming the surfaces
to verify when M1a/M1b land.

## M1a: retrieval-first memory

### `aitp list`

Proposed interface:

```text
aitp list [--kind KIND] [--since DATE] [--json] [--cwd PATH]
```

Semantics:

- default scope is every structurally valid canonical Entry, including
  superseded Entries;
- text rows contain date, Entry ID, kind, active/superseded status, and a
  summary truncated to approximately 110 Unicode characters;
- JSON carries the complete summary and an explicit versioned payload schema;
- `--kind` accepts the known kinds and fails with the allowed values;
- `--since` accepts an ISO date or timestamp and is inclusive;
- valid timestamps sort newest first with Entry ID as the tie-breaker;
- a legacy invalid timestamp does not crash an unfiltered list: the raw value
  is shown after valid timestamps and a warning identifies the path;
- when `--since` is present, an invalid timestamp cannot be compared and is
  omitted with a warning rather than guessed.

`list` is a projection over files. It writes no cursor or cache.

### `aitp show`

Proposed interface:

```text
aitp show <entry-id> [--json] [--cwd PATH]
```

It returns the complete frontmatter and body, canonical source path, and
active/superseded status. M1b may add derived `used_by`; M1a does not invent
relations that are absent from v0.1.

### `enter` v2 and handoff selection

`enter` remains a compact orientation view. It does not become a result
search command.

- The current next action retains its exact source Entry ID, `created_at`,
  authority, and file path; current M0 already exposes these fields.
- The latest active closeout with a non-empty next action is the authoritative
  handoff. Only when no active closeout establishes one does `enter` fall back
  to another active Entry.
- The Skill writes one closeout per unfinished session and supersedes the
  previous closeout when replacing its handoff. This is append-only and keeps
  the old state visible.
- No `record complete` command is added in M1a. A separate completion marker
  would turn the handoff field into a task lifecycle before evidence shows
  that closeout discipline is insufficient.
- Notes sort by their recorded `created_at` and ID, not UUID filename.
- `enter` reports the count of active Entries newer than the latest working
  Note. This is a structural age signal, not a claim that those Entries are
  semantically uncovered.

### Incremental reads

AITP does not maintain an implicit `.aitp/local/last-enter` cursor:

- `using-aitp` calls `enter` both at session start and before ending;
- multiple agents or terminals would overwrite one shared cursor;
- the same store on another machine would produce a different projection;
- an orientation command should not silently mutate local state.

Incremental inspection is explicit and reproducible through `list --since`.
The frozen M1a spec rejects an incremental option on `enter`; `list --since` is
the only planned explicit incremental read.

### Note trigger

The Skill trigger is:

> When four or more related durable Entries form a conclusion chain that a
> returning session would otherwise have to reconstruct, consider a working
> Note.

"Related" remains semantic Skill judgment. The runtime only exposes the
record-age count. It never writes a Note or warns merely because four unrelated
records exist.

### Diagnostics and performance

- A local `hash_mismatch` reports target, expected digest, actual digest, and
  the choices: pin an immutable revision/snapshot or correct the draft.
- A missing target reports the exact target and does not suggest weakening the
  pin.
- `--help` remains below 250 ms.
- 1,000-Entry `enter` remains below 1 s with a wider margin than the M0.5
  baseline; a 1,000-Entry `list` baseline is reported.
- No persistent index or derived canonical file is allowed to meet the gate.

Likely implementation surfaces for the authorized M1a work are `state.py` (or
one small query module), `cli.py`, `core.py`, the generated golden fixtures,
and `skills/using-aitp/SKILL.md`. The implementation specification must keep
every module below 400 nonblank lines and the stage total at or below 1,300.

## M1b candidate inventory: structured dependency and remote-run evidence

The authoritative A–H roster, dependencies, and current dispositions are in
`docs/m1b-spec.md` §0.1 (2026-08-12 reviewed freeze revision recorded).
The sections below are candidate designs only; the 2026-08-12 adjudication
(`docs/m1b-adjudication.md`) selected **M1b-R1** — the read-side slice fully
specified in `docs/m1b-r1-spec.md` (v0.1-only `check` plus the compact
`enter` text; implemented, deterministic gate passed) — and the
candidate designs below that
are not in R1 remain deferred/moved/dropped with no implementation spec.
The researcher's Followup 2 (`aitp lineage`) is a deferred candidate after
the budget reconciliation (§Scope and cut order below); it is not part of
R1.
G is independent use-driven Skill-track work and H is dropped from M1b;
neither is runtime candidate scope. Selected capabilities follow the versioned
success-envelope or same-change adapter-revision rule in
`docs/hakimi/compatibility-matrix.md` §3.

### `based_on`

`aitp/lite-entry-0.2` may contain:

```yaml
based_on:
  - entry-<32hex>
```

Definition:

> The durable claim in this Entry materially depends on the recorded content
> of the target Entry.

Rules:

- optional; v0.1 records remain valid without it;
- a list of Entry IDs, with no self-target;
- every target must already exist at save time;
- it expresses a claim dependency, not chronology, topical similarity, or
  replacement;
- it does not satisfy a kind's evidence-ref requirement;
- dependence on a superseded Entry is allowed for history; whenever a newly
  saved Entry's `based_on` targets one, the save-time warning applies;
- `show` and `enter` derive `used_by` by scanning canonical Markdown; no
  reverse index is stored if the B capability is selected and shipped;
- a selected and shipped A store-health capability may use `check` to validate
  targets and report `based_on_superseded`.

The save-time warning is candidate behavior, not permission to add `warnings` to
the current unversioned exact-key envelope. A selected B capability must first
freeze a versioned envelope (preferred) or same-change adapter revision; the
optional `check` report exists only if selected A ships, and B is deferred or
moved in the reviewed freeze revision if required A is omitted unless semantics
are revised and re-reviewed.

The save-time target-existence rule provides protocol order. `created_at`
remains an editable record time and is not treated as causal proof.

### Run and source context

The M1b run template carries, where applicable:

- host and remote path;
- scheduler and job ID;
- question and exact command/config;
- binary sha256 or stable version;
- consequential build flags such as `ENABLE_*` choices;
- input directory or input-manifest identity;
- seed;
- exit status and partial/cancelled state;
- estimated and actual wall/memory cost;
- local pointer manifest and output digest locations.

The source template carries stable identity, version/retrieval context, claim
boundary, and binary/build context when the source is an executable artifact.
These are body conventions, not a generic nested frontmatter schema. Unknown
or inapplicable values are stated explicitly.

### Remote evidence boundary

A remote path is useful location metadata but is not locally verifiable
evidence. A run Entry therefore pins an existing local manifest or pointer
bundle, for example a small Markdown or JSON file that records:

- host, remote path, scheduler job and collection time;
- binary and input identities;
- output file names, sizes and remotely computed digests;
- validation status and any unavailable objects.

The pointer file itself is pinned locally by sha256 or Git. AITP does not
pretend that this proves the remote host was honest; it makes the captured
claim and its provenance auditable.

Rejected alternatives:

- `target: host:/path` with ordinary `sha256:` when the local validator did
  not read those bytes;
- local mutable files with `retrieved:` as if observation time were integrity;
- extension-based "static vs mutable" inference.

#### Illustrative local pointer manifest (non-normative)

An example of the pointer content a run Entry pins (illustrative only — not a
frozen schema; the current runtime does not parse it):

```json
{
  "host": "fish",
  "remote_path": "/data/users/bhj/ai-runs/soc-mag/20260801/",
  "job": "1349",
  "collected_at": "2026-08-01T21:10:00Z",
  "binary": {"name": "abacus", "sha256": "<binary sha256>"},
  "source": {"repo": "abacus-develop/abacus", "commit": "<commit sha>"},
  "build": {"flags": ["ENABLE_LIBRPA=ON"], "sha256": "<build sha256>"},
  "input": {"name": "inputs/", "sha256": "<input manifest sha256>"},
  "outputs": [
    {"name": "OUT.ABACUS/results.dat", "size": 123456,
     "remote_sha256": "<remote digest>"}
  ],
  "validation": {"status": "not_revalidated",
                 "reason": "remote bytes were not re-read from the local host"}
}
```

The example is non-normative: it is not a frozen schema, the current runtime
does not parse it, and it does not prove the remote host was honest. The
pointer file itself remains pinned only by the existing local `sha256`/`git`
schemes, and nothing here changes the frozen M1b candidate contract in
`docs/m1b-spec.md`.

### Existing pin schemes

The explicit schemes remain:

- `sha256` for locally reachable immutable bytes;
- `git` for a path at a repository revision;
- `run` for an existing local run directory identity;
- `version` for an external persistent identifier;
- `retrieved` for an HTTP(S) source observation.

A growing local project-memory document should be pinned at a Git revision,
copied to a stable snapshot/manifest, or allowed to become visibly stale. If
A is selected and shipped, `check` may diagnose that drift; it does not rewrite
old Entries.

## Conditional quick-run experiment

`aitp record quick` is not committed M1b core. It is considered only if the
conformance suite or at least four real sessions show that correctly judged
durable run events are missed primarily because of prepare/fill/save friction.

If triggered, the first experiment is run-only:

```text
aitp record quick --kind run --summary TEXT \
  --limitation TEXT --idempotency-key KEY \
  --ref TARGET --at PIN --command TEXT --status STATUS
```

Additional input/build/job flags may be supplied, but the command must obey:

- caller supplies every semantic statement;
- at least one limitation, stable idempotency key, and complete pinned ref are
  mandatory;
- remote location is metadata and still requires a local pointer manifest;
- the ordinary validator, store lock, and canonical save function are reused;
- a retry with the same key returns the existing logical record;
- a later detailed version is a new Entry that supersedes the quick Entry;
  there is no in-place upgrade.

The experiment is scored for typed recall, precision, non-durable rejection,
and time-to-record. It is removed if it increases filler/noise or provides no
measurable benefit. It is the first item of the M1b cut order in
`docs/m1b-spec.md` §12.4 if the M1b 1,450-line cap is at risk.

## Suite additions after the M0.6 baseline

The already specified M0.6 core, frozen thresholds, hold-out, and anti-gaming
rules remain intact. A dense-ledger scenario modeled on the dogfood failures
may be added as one-off, predeclared evidence for a selected M1 gate, with the
rubric diff recorded; it is not routine session work and is not automatic at
every gate. It contains no private project claims:

- more than 60 Entries and a decisive result outside the recent window;
- a long supersession chain;
- one invalid legacy timestamp that must not crash list/show;
- a stale handoff that is replaced by a later closeout;
- a run whose remote location is useful but whose evidence is a local pointer
  manifest;
- four related Entries that should trigger a working-Note suggestion, plus
  unrelated distractors that should not.

Score action-changing retrieval, exact Entry citation, stale-pin disclosure,
handoff correctness, typed record precision, and cold-start/tool-call cost.

## Safe acceptance on GW_librpa

The real store is read-only compatibility evidence.

Before and after in-place read tests, hash every file under `.aitp`; the maps
must be byte-identical. The following 60/41/19/26/1 values are a historical
compatibility snapshot dated 2026-08-06, not fixed current-count assertions;
current runs record dynamic counts as observed and preserve the read-only
projection and before/after byte-identity invariants:

- 60 structurally readable Entries;
- 41 active and 19 superseded;
- 26 `result` Entries;
- one unresolved active failure;
- `list` and `show` do not fail merely because old evidence has drifted;
- with A selected in M1b-R1, `check` reports missing/mismatched pins honestly
  (the frozen R1 acceptance procedure is in `docs/m1b-r1-spec.md` §Real-store
  acceptance).

All write-path acceptance runs on a `cp -a` temporary copy or a fresh temporary
store:

- valid and missing `based_on` targets;
- reverse `used_by` projection;
- remote run with a locally pinned pointer manifest;
- rejection of an unverifiable remote path used as a local sha256 pin;
- quick-run positive path, missing-key/ref/limitation negative paths, and
  idempotent retry, if the experiment is enabled.

A new Entry is written to the real project only for a genuine research event
with the researcher's approval and real evidence, never to satisfy a software
acceptance checklist.

## Scope and cut order

The fixed caps are M1a ≤ 1,300 and M1b ≤ 1,450 nonblank canonical-runtime
lines; they are ceilings, never adjusted. The reconciliation is recorded in
`docs/m1b-adjudication.md`: actual M1a total 1,256 → M1b headroom **194**.

Use the authoritative A–H + Followup roster/freeze rule in `docs/m1b-spec.md`
§0.1 before cutting scope: no implementation spec follows deferred, moved,
dropped, or no-runtime outcomes. A selected slice gets its own reviewed spec
and must retain required validation, v0.1 compatibility, and the no-index
boundary. If it is over cap, use its spec's cut order:

- M1a — `docs/m1a-spec.md` §Cut order: cosmetic output, `--since` conveniences,
  then the `legacy-derived` text tag (not its JSON field).
- M1b (selected slice) — the **R1 cut order is `docs/m1b-r1-spec.md`
  §Cut order** (residual compact-`enter` display lines first; check
  semantics, the two frozen M1a safety lines, and the text hints are never
  cut; `lineage` is already a deferred candidate). The generic candidate
  cut order in `docs/m1b-spec.md` §12.4 (quick-run, Skill-duplicating
  hints, cosmetic output) remains the historical candidate-level order and
  does not govern the selected slice.

Never cut M1a evidence/relation validation, compatibility, deterministic
projections, or no-index. For M1b, unselected `check`/projections are cuttable;
a check-only slice is valid, and B may be deferred or moved when its required A
`check` is omitted, with the disposition recorded in the freeze revision.
