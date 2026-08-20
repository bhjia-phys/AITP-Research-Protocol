# AITP Evidence Ledger Design

Status: stable M0 baseline with M0.6 adopt/inventory additions and completed M1a
read projections documented below. M1a is **done; deterministic gate passed**;
see [`docs/archive/m1a-stage-notes.md`](archive/m1a-stage-notes.md). The current persistent
schema remains `aitp/lite-entry-0.1`; M1a transport schemas are
`aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`. The M1b natural-use
pause is complete; the 2026-08-12 reviewed freeze revision
([`docs/archive/m1b-adjudication.md`](archive/m1b-adjudication.md)) selected the read-side
slice **M1b-R1** — `aitp check` (no-flag transport `aitp/check-report-0.1`)
is implemented per [`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md)
and its deterministic gate **passed** (evidence in
[`docs/archive/m1b-r1-stage-notes.md`](archive/m1b-r1-stage-notes.md));
`lineage` is a deferred candidate. **M1c (Topic workstreams) is
done; deterministic gate passed** — frozen
implementation spec [`docs/archive/m1c-workstreams-spec.md`](archive/m1c-workstreams-spec.md):
optional `workstreams` membership (unscoped legacy visible only in the global
view), repeatable `--workstream` prepare flag (duplicates rejected),
single-slug scoped `aitp/enter-0.3`/`aitp/list-0.2` (no flag ⇒ old schemas
byte-unchanged), global relations computed first with strictly scoped
projections including handoff, global warnings, no
registry. The deterministic gate passed (evidence in
[`docs/m1c-stage-notes.md`](m1c-stage-notes.md)).
**M1d (scoped `check` workstream health) is done; deterministic gate
passed** — frozen implementation spec
[`docs/archive/m1d-workstream-health-spec.md`](archive/m1d-workstream-health-spec.md):
`check` gains a single-occurrence `--workstream <slug>` flag emitting the
scoped transport **`aitp/check-report-0.2`** (global scan first, scoped
subset projection; admission + strict exact membership; scoped counts with
per-level `by_code` and derived `outside_scope`; exactly-four-line scoped
text; exit 0/1/2 on the scoped report; zero-write); without the flag
`aitp/check-report-0.1` JSON/text/exit/zero-write is byte-unchanged; the
diagnosed file schemas remain the shipped v0.1 ones
(`aitp/lite-entry-0.1`/`aitp/lite-note-0.1`). **M1e (Evidence lifecycle +
reviewed backfill) is done; deterministic gate passed** — frozen spec
[`docs/archive/m1e-evidence-lifecycle-backfill-spec.md`](archive/m1e-evidence-lifecycle-backfill-spec.md):
`sha256-once:` pins, optional `.aitp/local/check-policy.json`, and
`aitp backfill workstreams`; no policy file means check remains
byte-unchanged. Plugin version 0.7.0. The 2026-08-15 reviewed 0.6.0 change is Skill-only
(automatic session-boundary current-state maintenance in `using-aitp`;
method-card distillation in `distilling-methods`; design record
[`docs/method-cards-and-distillation.md`](method-cards-and-distillation.md))
and changes **no behavioral runtime, CLI, schema, transport, or exit code** —
only the version strings (all four surfaces) were bumped from M1d's 0.5.0 to
0.6.0; the historical M1d 0.5.0 gate record stands unchanged.
Gate evidence in [`docs/m1d-stage-notes.md`](m1d-stage-notes.md).
M2/M3 remain design options.

## Purpose

AITP preserves the small amount of research state that must survive across conversations:

- what was observed or derived;
- which evidence supports it;
- what failed and whether it remains unresolved;
- which decision or result replaced an older record;
- what should happen next;
- which synthesis Notes are grounded in those records.

It records project evidence and working state, not scientific truth.

## Repository model

One repository is one research Topic.

```text
.aitp/
├── STORE.toml
├── topic/
│   ├── TOPIC.md
│   ├── entries/
│   └── notes/
└── local/
    ├── config.toml
    ├── drafts/
    ├── locks/
    └── scratch/

theory/
software/
calculations/
data/
figures/
references/
manuscripts/
```

`.aitp/topic/` is durable and versioned. `.aitp/local/` is machine-local and ignored.

## Commands

Every command accepts `--cwd PATH` (default `.`) and `--json`; `--json`
emits the same payload as machine-readable JSON. The commands below are the
current implemented surface. Deferred M1b roster items — B (dependency
links), C–E, Followup 2 (`lineage`), and Followup 6 (structured prepare) —
are **not** implemented and absent from the CLI; F moved to M4, G moved to
the independent Skill track, and H dropped (dispositions in
`docs/m1b-spec.md` §0.1).

### `aitp init`

Without `--adopt`, operate only on a blank directory, except for an optional
`.git`. Create the fixed research layout and one Topic record. `--adopt`
(M0.6) initializes `.aitp/` inside an existing research tree without touching
content or imposing the fixed layout. `--dry-run` reports the intended
changes without writing. Never initialize Git or infer scientific content.

### `aitp inventory`

`aitp inventory <path> --name <slug>` scans a legacy tree and writes a
read-only hash manifest (`aitp/legacy-inventory-0.1`) under
`.aitp/local/legacy/`. It is an operator-only M0.6 bootstrap tool for legacy
stores; it is not part of the routine session flow.

### `aitp enter`

`aitp enter [--recent N] [--workstream <slug>] [--json]` reads the Topic,
valid Entries, and Notes; `--recent` defaults to 20, the window is a
projection, and `omitted_active` reports what it leaves out. Return:

- memory status;
- recent active Entries with exact source paths;
- limitations and pinned references;
- unresolved active failures;
- current next action;
- recent Notes.

The output must distinguish recorded state from scientific truth and expose missing or malformed memory. The M1a JSON payload is `aitp/enter-0.2`; it uses closeout-first handoff selection, recorded-time Note ordering, the exact legacy-derived marker, and the structural Note-age count.

### `aitp record prepare/save`

`aitp record prepare --kind <kind> --authority <level> --created-by <id>
[--idempotency-key <key>] [--workstream <slug>]...` prepares exactly one
draft from the selected
kind-specific template. `--created-by` is required for `authority: agent`
(missing provenance is `missing_provenance`); `aitp record save <draft>`
saves only after fast structural, relation, evidence-pin, and
prompt-completion checks. The M1c `--workstream` flag (shipped;
deterministic gate passed) is repeatable and seeds the draft's optional
`workstreams` list in flag order; a repeated identical slug is rejected as a
duplicate (no silent dedup); without the flag the draft is byte-identical to
today.

Kinds:

```text
observation  result  failure  decision
source       code-change  run  closeout
```

A `result` records a project outcome with its evidence boundary — it is not
a credibility rank; trust gradients live in reviewed artifacts (M2).

Relations are append-only:

- `resolves` closes an active failure;
- `supersedes` replaces an older Entry without rewriting history.

Logical retries use one idempotency key and must not create duplicates.

### `aitp note prepare/save`

`aitp note prepare --mode working|theory --title "<title>" --created-by <id>
[--workstream <slug>]...` prepares either:

- `working`: current research line, evidence map, uncertainty, and next actions;
- `theory`: assumptions, conventions, derivation, checks, gaps, and implications.

`--created-by` is required (Notes are agent artifacts; missing provenance is
`missing_provenance`). `aitp note save <draft>` saves the filled draft; a
Note `supersedes` targets must exist among canonical Notes. A Note
synthesizes pinned research evidence. It is not the sole evidence for a
result.

`review_state` currently has exactly one legal value, `agent_draft`: the
Note lifecycle has no built-in "reviewed" transition. Researcher
confirmation of a Note's content is expressed outside the Note schema — by a
`decision` Entry with `authority: human` pinning the Note file. Do not read
`review_state` as a promise of a future review mechanism.

Method cards (0.6 Skill-only) are a Skill-level profile on this exact Note
contract, not a new schema, mode, or review state: a card is a `mode:
theory` Note titled `Method card: <slug>` whose body first line is the
generic marker `> method-card: <slug>`, with the six theory headings filled
per a fixed content mapping. It adds no frontmatter field, no mode, and no
`review_state` value — cards flow through the existing prepare/save
validation and `check` diagnostics — and approval is the same
`authority: human` decision-Entry pin as any Note confirmation. The
distillation chain and its human publication gates are defined in the
`distilling-methods` Skill; see
[`docs/method-cards-and-distillation.md`](method-cards-and-distillation.md).

### `aitp list`

`aitp list [--kind KIND] [--since DATE] [--workstream <slug>] [--json]` is the M1a read-only
projection over canonical Entries. Its JSON payload is `aitp/list-0.1`; it
supports kind and inclusive timestamp filters, preserves superseded records,
and writes no cursor, cache, lock, or local state. With the M1c
single-occurrence `--workstream` flag (shipped; deterministic gate passed)
the payload is `aitp/list-0.2`: the `aitp/list-0.1` fields plus one
additive top-level singular `workstream` key, entries and count filtered to
strict exact membership (unscoped records are excluded); without the flag the
`aitp/list-0.1` payload is byte-unchanged.

### `aitp show`

`aitp show <entry-id> [--json]` is the M1a exact-record read projection. Its
JSON payload is `aitp/show-0.1`; for a valid Entry it returns the complete
structurally valid Entry and active/superseded status without revalidating
evidence pins. If the target file exists but fails validation, `show` still
renders it: `status: "malformed"`, `frontmatter: null`, `body` is the raw
file text, and `warning` carries the validation finding (code/path/message).
`check` remains the whole-store diagnostic; `show` never hides a broken
record.

### `aitp check` (M1b-R1 no-flag; M1d scoped variant; M1e evidence lifecycle; shipped, deterministic gates passed)

`aitp check [--cwd PATH] [--json] [--workstream <slug>]` is the read-only
store-health diagnostic with **two read-only transports**: the no-flag
global report **`aitp/check-report-0.1`** (M1b-R1) and the M1d
single-slug scoped report **`aitp/check-report-0.2`** (below). Both
transports validate every canonical Entry/Note against the same shipped
v0.1 file schemas — `aitp/lite-entry-0.1`/`aitp/lite-note-0.1` only, never
any other schema — and report deterministic findings sorted by
`(path, code, message)`; exit 0 clean / 1 findings / 2 cannot run (not a
workspace, unreadable store metadata, or CLI misuse); zero-write in both
modes (no lock, cache, index, repair, or migration) with frozen no-crash
mappings (invalid UTF-8 records and refs become findings; no path raises a
traceback). Finding codes produced: structural/validation codes from the
save path plus `duplicate_id`; `invalid_workstreams` (not-a-list, empty
list, empty element, invalid slug, or duplicate element in a `workstreams`
list, on save and in `check`); relation codes
`invalid_relation`/`missing_relation` apply to Entry `resolves`/`supersedes`
targets and Note `supersedes` targets (no `invalid_supersession` — the
2026-08-12 stability revision removed the `created_at` ordering rule);
pin grades `hash_mismatch`, `historical_pin_drift`/`historical_ref_missing` (M1e `sha256-once` and mutable policy), `unreadable_ref`, `invalid_run_ref`,
`invalid_version_ref`, `invalid_retrieved_ref`, `invalid_sha256_once_ref`, `invalid_ref_pin`,
`invalid_check_policy`, and `invalid_git_ref` (error when Git verifies wrong, warning when Git is
unavailable); warnings `invalid_timestamp` and
`empty_topic_goal`. The frozen implementation contracts are in
[`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md) (M1b-R1) and
[`docs/archive/m1d-workstream-health-spec.md`](archive/m1d-workstream-health-spec.md) (M1d), and
[`docs/archive/m1e-evidence-lifecycle-backfill-spec.md`](archive/m1e-evidence-lifecycle-backfill-spec.md) (M1e);
all deterministic gates passed (evidence in
[`docs/archive/m1b-r1-stage-notes.md`](archive/m1b-r1-stage-notes.md) and
[`docs/m1d-stage-notes.md`](m1d-stage-notes.md)). `aitp lineage` is a deferred
candidate (Followup 2, re-deferred at the 2026-08-12 budget
reconciliation). `enter`'s text rendering is compact in R1 with two frozen
M1a safety lines; its `aitp/enter-0.2` JSON contract is unchanged.

#### Scoped `--workstream` variant (M1d; done, deterministic gate passed)

The flag is **single-occurrence** — a repeated `--workstream` is parser
misuse (argparse "may only be given once"), exit 2; slug validation reuses
the M1c rule verbatim (`_validate_scope` → `_validate_workstreams([slug])`),
so an invalid slug raises `invalid_workstreams` (exit 2, standard JSON
error envelope under `--json`). With the flag, `check --json` emits
**`aitp/check-report-0.2`**: the complete 0.1 payload plus exactly three
additive changes — one top-level singular `workstream` key (no
`workstreams` key anywhere), `counts.by_code`, and `counts.outside_scope`.
Key order is frozen: top level `schema, status, root, counts, findings,
workstream`; inside `counts`: `entries, notes, errors, warnings, by_code,
outside_scope` (no `malformed` key). Without the flag every output surface
is byte-unchanged — `aitp/check-report-0.1` JSON and text, exit 0/1/2,
zero-write; the API default `check_workspace(cwd, *, workstream=None)`
short-circuits before any scoped computation.

Frozen semantics:

- **Global pass first, then subset projection.** Every run, scoped or not,
  scans and validates the whole store exactly once, exactly as the no-flag
  run does — same per-file rule (parse → structure → duplicate → timestamp
  warning → relations → refs), same global `entry_map`, same global
  `(path, code, message)` sort. The scoped report is the global report
  **restricted** to attributable in-scope findings; the scope flag performs
  no validation beyond the global run.
- **Admission.** A finding on path P is scoped iff P's record was
  **admitted** — parse and structural validation passed **and** the ID was
  unique (the record is in the `entries`/`notes` item lists, not the
  warning list) — **and** the admitted record's frontmatter `workstreams`
  list explicitly contains the slug (strict exact membership, never
  inferred; unscoped records are in no scope). Malformed records (parse or
  structural failure, including an invalid `workstreams` field),
  duplicate-ID files (their `duplicate_id` finding is never scoped), and
  TOPIC.md findings (`empty_topic_goal`) are **not attributable** and are
  excluded from every scoped view; out-of-scope and unscoped records'
  step-4–6 findings (legacy `invalid_timestamp` warning, relations, graded
  refs, Note-side `missing_refs`) are excluded too. All of these stay in
  the no-flag global report and appear in the scoped report only through
  the derived `outside_scope` totals.
- **Subset invariant.** The scoped `findings` list is element-wise equal to
  the global `findings` restricted to the scoped paths — same findings,
  levels, codes, messages, and order; no finding is re-sorted, re-graded,
  or re-worded.
- **Relations are global first.** Relations validate against the
  whole-store `entry_map`, built once from the single global parse pass: an
  in-scope Entry whose `resolves`/`supersedes` target exists out-of-scope or
  unscoped validates cleanly (`missing_relation` never fires because the
  target exists globally — a cross-workstream resolver still closes its
  target, mirroring M1c); `missing_relation`/`invalid_relation` fire only
  for store-absent or self targets, and the finding is scoped iff the
  resolving record is in scope.
- **Scoped counts.** `counts.entries`/`counts.notes` count **admitted
  in-scope** records — deliberately different from the global "count every
  canonical file" rule, because malformed files cannot be attributed to any
  scope (the asymmetry is intentional and frozen). `counts.errors`/
  `counts.warnings` are scoped findings by level; `status` is `"findings"`
  iff the scoped findings list is non-empty. A scoped report with findings
  always satisfies `counts.entries + counts.notes >= 1` (every scoped
  finding sits on an admitted in-scope record).
- **`by_code`** (always present): a map `code → {"errors": n, "warnings":
  m}` over the scoped findings, keys sorted lexicographically, `{}` when
  there are no scoped findings. Buckets are per-level, so a code graded as
  error on one finding and warning on another (e.g. `invalid_git_ref`) is
  tallied separately; the buckets sum exactly to `counts.errors`/
  `counts.warnings`/`len(findings)`.
- **`outside_scope`** (always present): `{"errors": n, "warnings": m}`, the
  derived level totals of all global findings **not** in the scoped view —
  exactly global totals minus scoped totals per level (`{"errors": 0,
  "warnings": 0}` when the scoped view contains every finding). It is a
  **pure level delta**: no paths, no codes, no `by_code` contribution,
  never appears in `findings`, never affects `status` or the exit code —
  it exists so a scoped report can never silently mask global findings, and
  it does not label any other workstream's (or unscoped, malformed,
  duplicate, TOPIC) findings as "debt" or "damage".
- **Scoped text is exactly four lines, always** — including a clean scope —
  all on stdout with stderr empty, and never per-finding lines (details
  live in `--json` only):

```text
workstream: <slug>
check: <e> error(s), <w> warning(s)
by_code: <compact JSON>
outside_scope: <e> error(s), <w> warning(s) (run "aitp check" for the whole store)
```

  `by_code:` is the compact JSON serialization of `counts["by_code"]` (no
  indent), `by_code: {}` on a clean scope. The text is human-facing only;
  machine output is the versioned JSON. The unscoped text path is
  byte-unchanged (one line per finding + exactly one summary line).
- **Exit codes evaluate on the scoped report** (`outside_scope` never
  affects `status` or the exit code): `0` clean — zero scoped findings,
  which claims nothing about other workstreams or the whole store; `1`
  findings — at least one attributable in-scope error or warning; `2`
  cannot run — not a workspace, unreadable/invalid store metadata
  (`not_initialized`, `malformed_store`, `invalid_root`), or CLI misuse
  (repeated `--workstream`, invalid slug). Payload and exit are mutually
  consistent: scoped `findings` non-empty ⇔ exit 1.
- **Empty scope is legal.** A well-formed slug with no admitted in-scope
  records is a valid **empty scope** (counts 0, `findings` `[]`, `by_code`
  `{}`, `outside_scope` = the global totals, `status` `clean`, exit 0) —
  never an error. On an all-unscoped legacy store every scope is empty; the
  empty scope is the signal, not a health certificate — scoped health is
  meaningful only once records explicitly carry `workstreams` (new scoped
  records or a reviewed manual backfill; M1d never backfills).
- **Determinism and zero-write.** Two runs on the same store are
  byte-identical in both modes (no volatile fields; scoped order is the
  global order restricted). Both modes write nothing — a test asserts the
  `.aitp` tree is byte-identical before and after scoped and unscoped runs.

#### M1e evidence lifecycle and reviewed backfill

`sha256-once:` is the mutable-observation pin: save verifies the current
bytes exactly like `sha256:`; later check drift/missing produce the warning
codes above. Optional `.aitp/local/check-policy.json` (schema
`aitp/check-policy-0.1`) carries reviewed `mutable` and `immutable`
path-pattern lists. A mutable match downgrades legacy strict
`hash_mismatch`/`missing_ref` to the historical warning codes; immutable and
unmatched paths stay errors; no policy file leaves the pre-M1e check output
byte-unchanged. `aitp backfill workstreams` (dry-run by default; `--apply`
writes) is the explicit reviewed backfill path: a mapping file lists slugs
and Entry/Note IDs, a human `decision` Entry must sha256-pin the mapping,
and apply only adds/merges the frontmatter `workstreams` block.

Judgment boundary (frozen): scoped projection is deterministic runtime
work — a per-record predicate, never an inference. `by_code` is a tally,
**not** a drift-vs-damage classification: whether a `hash_mismatch` is
"expected historical pin drift" or "current evidence damage" is a human
judgment (Skill matter), never a runtime call. A scoped `clean`/exit 0
claims only "no attributable findings for this workstream", not whole-store
health; the no-flag run remains the whole-store instrument. The `using-aitp`
Skill teaches the scoped surface with these boundaries (incl. that scoped
`enter` warnings stay global while scoped `check-0.2` `counts.warnings` is
scoped, with `outside_scope` carrying the difference).

### Topic workstreams (M1c; done, deterministic gate passed)

The frozen implementation-level contract is
[`docs/archive/m1c-workstreams-spec.md`](archive/m1c-workstreams-spec.md). Summary:

- Entries and Notes may carry an **optional `workstreams` list** in
  frontmatter (file schemas `aitp/lite-entry-0.1`/`aitp/lite-note-0.1`
  unchanged). Absence means **unscoped legacy**: valid and visible only in
  the unfiltered global view — unscoped records are excluded from every
  scoped view. A present field must be a **non-empty, no-duplicate** list.
  Membership is **explicit and multi-valued**, never inferred; cross-line
  records list all their workstreams. Slugs reuse the Topic slug rule
  `[a-z0-9][a-z0-9-]{0,62}`; violations (including an empty list) are
  `invalid_workstreams` on save and in `check`.
- `record prepare`/`note prepare` accept a **repeatable `--workstream`**
  flag that seeds the draft's list in flag order; a repeated identical slug
  is rejected as a duplicate (no silent dedup); prepare/save envelopes are
  unchanged.
- `enter --workstream <slug>` emits **`aitp/enter-0.3`** and
  `list --workstream <slug>` emits **`aitp/list-0.2`**: the old payload plus
  one additive top-level **singular `workstream`** key, with entries/notes/
  counts filtered to strict exact membership. The flag is **single-occurrence**
  on both read commands (a repeated flag is parser-rejected misuse).
  **Relations run on the whole store first** — the superseded set, the
  resolved set, and their effect on `unresolved_failures`/superseded status
  are global, so a cross-line resolver/superseder still closes/replaces its
  target; then the projections (`recent_entries`, `unresolved_failures`,
  `next_action` handoff, `recent_notes`, `latest_working_note`, Note age,
  active/superseded/omitted counts) are **strictly scoped** — an out-of-scope
  handoff is never shown. `warnings`,
  `counts.malformed`, `memory_status`, and `check` are **global** — scoping
  never hides validation state (M1c rule: `check` has no scope flag; M1d
  additively supersedes that sentence for the flag variant only — scoped
  `check-0.2` `counts.warnings` is **scoped**, with `outside_scope`
  carrying the global−scoped remainder; the Skill teaches both).
- **No flag ⇒ byte-identical old schemas** (`aitp/enter-0.2`,
  `aitp/list-0.1`). No registry: no new file or command; membership lives
  only in record frontmatter. `show` is unchanged (`aitp/show-0.1`);
  `check` gains only the M1d additive flag variant — without the flag
  `aitp/check-report-0.1` stays byte-unchanged (`aitp/check-report-0.2`
  scoped per the `aitp check` section).
- Deterministic gate **passed** (2026-08-13) — evidence recorded in
  `docs/m1c-stage-notes.md`.

## Evidence pins

Every mutable reference uses:

```yaml
target: relative/path
at: sha256:<digest> | git:<revision> | run:<id> | version:<id> | retrieved:<time>
locator: exact section, equation, line, or object
```

Saving verifies pins that can be checked locally. Remote evidence is
location metadata, not a pin: a durable result that depends on remote
immutable runs first lands a local pointer manifest (host, remote path, job
id, SHAs, verification time, and the "remote bytes not re-verified since"
boundary) inside the workspace, and the Entry pins that manifest with
`sha256:`. This is a Skill convention with no runtime support (roster D is
deferred).

## Agent behavior

The installed `$aitp` Skill:

1. runs `enter` at the start of research work;
2. opens cited evidence before relying on a claim;
3. records only durable moments;
4. fills the CLI-generated template rather than inventing a format;
5. runs `enter` again before ending.

Conversational filler, scratch work, and unverified speculation are not durable memory.
