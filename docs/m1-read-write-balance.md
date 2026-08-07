# M1 Read/Write Balance

Status: design proposal; blocked. This document refines the M1a and M1b design
in `docs/roadmap.md` v3.2. It is not an implementation-level specification and
does not green-light M1 runtime work before the M0.6 gates.

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

## Governing constraints

- Existing v0.1 Entries and Notes are never migrated or rewritten.
- New frontmatter fields are optional and land only in a versioned schema.
- `refs` remain evidence pins; relation fields never replace evidence.
- `enter`, `list`, `show`, and `check` are projections and diagnostics, not
  semantic ranking engines.
- No persistent search index is introduced; Markdown remains canonical.
- Remote paths are metadata unless a locally pinned manifest makes their
  contents auditable.
- Quick capture, if justified, reuses the same validator, lock, idempotency,
  and save path as ordinary records.
- The canonical runtime is only
  `plugins/aitp-research-protocol/scripts/vendor/aitp/`; installed managed or
  cached plugin copies are never hand-maintained.

## Disposition of the ten requests

| Request | Decision | Stage |
|---|---|---|
| `aitp list` | Accept as the primary dense-store retrieval view | M1a |
| optional `based_on` and reverse links | Accept with narrow dependency semantics; never a substitute for `refs` | M1b |
| next-action completion command | Replace with authoritative closeout handoffs; reconsider an append-only closure relation only after suite evidence | M1a discipline, possible M1b follow-up |
| `record quick` | Conditional run-only experiment; not committed core | post-M1b core if measured |
| run/source execution fields | Accept as templates and Skill conventions, not a broad validator schema | M1b |
| raw `host:path` refs | Reject; use local pointer manifests for remote evidence | M1b |
| automatic pin grading | Reject; retain explicit pin schemes and improve diagnostics | M1a/M1b |
| implicit last-enter increment | Reject; use explicit deterministic `--since` | M1a |
| Note trigger and coverage hint | Accept as a Skill trigger plus a structural age count | M1a |
| Skill synchronization | Required in the stage that changes the behavior | every stage |

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
An `enter --since` count may be considered during the M1a specification if it
can reuse the same read-only semantics.

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

Likely implementation surfaces, after M1a is green-lit, are `state.py` (or one
small query module), `cli.py`, `core.py`, the golden fixtures, and
`skills/using-aitp/SKILL.md`. The implementation specification must keep every
module below 400 nonblank lines and the stage total at or below 1,300.

## M1b: structured dependency and remote-run evidence

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
- dependence on a superseded Entry is allowed for history but reported as a
  warning when an active claim still relies on it;
- `show` and `enter` derive `used_by` by scanning canonical Markdown; no
  reverse index is stored;
- `aitp check` validates targets and reports stale dependency boundaries.

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

### Existing pin schemes

The explicit schemes remain:

- `sha256` for locally reachable immutable bytes;
- `git` for a path at a repository revision;
- `run` for an existing local run directory identity;
- `version` for an external persistent identifier;
- `retrieved` for an HTTP(S) source observation.

A growing local project-memory document should be pinned at a Git revision,
copied to a stable snapshot/manifest, or allowed to become visibly stale.
`aitp check` diagnoses that drift; it does not rewrite old Entries.

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
measurable benefit. It is the first feature cut if the M1b 1,450-line cap is
at risk.

## Suite additions after the M0.6 baseline

The already specified M0.6 core and frozen thresholds are run before adding
new M1 scenarios. Between stage runs, with the rubric diff recorded, add a
dense-ledger scenario modeled on the dogfood failures but containing no
private project claims:

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
must be byte-identical. Expected dated baseline assertions are:

- 60 structurally readable Entries;
- 41 active and 19 superseded;
- 26 `result` Entries;
- one unresolved active failure;
- `list` and `show` do not fail merely because old evidence has drifted;
- `check`, when M1b exists, reports missing/mismatched pins honestly.

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

M1a ends at 1,300 nonblank canonical-runtime lines; M1b ends at 1,450. If the
specification does not fit, scope is cut in this order:

1. quick-run command;
2. nonessential save-time hints that duplicate the Skill;
3. cosmetic output features.

Never cut evidence validation, relation validation, v0.1 compatibility,
read-only `check`, deterministic projections, or the no-index rule.
