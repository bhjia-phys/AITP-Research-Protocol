# AITP Evidence Ledger Design

Status: stable M0 baseline with M0.6 adopt/inventory additions and completed M1a
read projections documented below. M1a is **done; deterministic gate passed**;
see [`docs/archive/m1a-stage-notes.md`](archive/m1a-stage-notes.md). The current persistent
schema remains `aitp/lite-entry-0.1`; M1a transport schemas are
`aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`. The M1b natural-use
pause is complete; the 2026-08-12 reviewed freeze revision
([`docs/archive/m1b-adjudication.md`](archive/m1b-adjudication.md)) selected the read-side
slice **M1b-R1** — `aitp check` (v0.1-only) is implemented per
[`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md) and its deterministic gate **passed**
(evidence in [`docs/archive/m1b-r1-stage-notes.md`](archive/m1b-r1-stage-notes.md));
`lineage` is a deferred candidate. M2/M3 remain design options.

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
current implemented surface; the conditional M1b subsection lists what is not
yet implemented.

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

`aitp enter [--recent N] [--json]` reads the Topic, valid Entries, and Notes;
`--recent` defaults to 20, the window is a projection, and `omitted_active`
reports what it leaves out. Return:

- memory status;
- recent active Entries with exact source paths;
- limitations and pinned references;
- unresolved active failures;
- current next action;
- recent Notes.

The output must distinguish recorded state from scientific truth and expose missing or malformed memory. The M1a JSON payload is `aitp/enter-0.2`; it uses closeout-first handoff selection, recorded-time Note ordering, the exact legacy-derived marker, and the structural Note-age count.

### `aitp record prepare/save`

`aitp record prepare --kind <kind> --authority <level> --created-by <id>
[--idempotency-key <key>]` prepares exactly one draft from the selected
kind-specific template. `--created-by` is required for `authority: agent`
(missing provenance is `missing_provenance`); `aitp record save <draft>`
saves only after fast structural, relation, evidence-pin, and
prompt-completion checks.

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

`aitp note prepare --mode working|theory --title "<title>" --created-by <id>`
prepares either:

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

### `aitp list`

`aitp list [--kind KIND] [--since DATE] [--json]` is the M1a read-only
projection over canonical Entries. Its JSON payload is `aitp/list-0.1`; it
supports kind and inclusive timestamp filters, preserves superseded records,
and writes no cursor, cache, lock, or local state.

### `aitp show`

`aitp show <entry-id> [--json]` is the M1a exact-record read projection. Its
JSON payload is `aitp/show-0.1`; for a valid Entry it returns the complete
structurally valid Entry and active/superseded status without revalidating
evidence pins. If the target file exists but fails validation, `show` still
renders it: `status: "malformed"`, `frontmatter: null`, `body` is the raw
file text, and `warning` carries the validation finding (code/path/message).
`check` remains the whole-store diagnostic; `show` never hides a broken
record.

### `aitp check` (M1b-R1; shipped, deterministic gate passed)

`aitp check [--cwd PATH] [--json]` is the M1b-R1 read-only whole-store
diagnostic (schema `aitp/check-report-0.1`). It validates every canonical
Entry/Note against the shipped v0.1 contracts and reports deterministic
findings sorted by `(path, code, message)`; exit 0 clean / 1 findings /
2 cannot run (not a workspace, unreadable store metadata, or CLI misuse);
zero-write (no lock, cache, index, repair, or migration) with frozen
no-crash mappings (invalid UTF-8 records and refs become findings; no path
raises a traceback). Finding codes produced today: structural/validation
codes from the save path plus `duplicate_id`; relation codes
`invalid_relation`/`missing_relation` apply to Entry `resolves`/`supersedes`
targets and Note `supersedes` targets (no `invalid_supersession` — the
2026-08-12 stability revision removed the `created_at` ordering rule);
pin grades `hash_mismatch`, `unreadable_ref`, `invalid_run_ref`,
`invalid_version_ref`, `invalid_retrieved_ref`, `invalid_ref_pin`, and
`invalid_git_ref` (error when Git verifies wrong, warning when Git is
unavailable); warnings `invalid_timestamp` and
`empty_topic_goal`. The frozen implementation contract is in
[`docs/archive/m1b-r1-spec.md`](archive/m1b-r1-spec.md); the implementation is complete and
its deterministic gate passed (evidence in
[`docs/archive/m1b-r1-stage-notes.md`](archive/m1b-r1-stage-notes.md)). `aitp lineage` is a deferred
candidate (Followup 2, re-deferred at the 2026-08-12 budget
reconciliation). `enter`'s text rendering is compact in R1 with two frozen
M1a safety lines; its `aitp/enter-0.2` JSON contract is unchanged.

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
