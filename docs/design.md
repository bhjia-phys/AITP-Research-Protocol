# AITP Evidence Ledger Design

Status: stable M0 baseline, with the M0.6 adopt/inventory additions documented
below. The schema evolves to `aitp/lite-entry-0.2` in
M1b (new `prediction` and `question` kinds; `resolves` generalized to
failures, predictions, and questions with a typed `resolution` closure
field and target-kind validation; `contradicts` on failure Entries under
strict criteria; `aitp check` whole-store re-validation; Note `supersedes`
validation; optional `citekey`/`trust` on `source` Entries) per
`docs/roadmap.md`; v0.1 records remain valid without migration. `list`,
`show`, and `check` are planned M1 commands and are not implemented (see
"Planned commands" below).

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
current implemented surface; the "Planned commands" subsection lists what is
not implemented.

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

The output must distinguish recorded state from scientific truth and expose missing or malformed memory.

### `aitp record prepare/save`

`aitp record prepare --kind <kind> --authority <level> --created-by <id>
[--idempotency-key <key>]` prepares exactly one draft from the selected
kind-specific template. `aitp record save <draft>` saves only after fast
structural, relation, evidence-pin, and prompt-completion checks.

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

`aitp note save <draft>` saves the filled draft. A Note synthesizes pinned
research evidence. It is not the sole evidence for a result.

### Planned commands (blocked)

Not implemented; do not invoke them. Designed in
`docs/m1-read-write-balance.md` and gated by `docs/roadmap.md` (M0.6 gate,
then the M1a/M1b spec freezes):

- `aitp list [--kind KIND] [--since DATE]` — M1a retrieval projection over
  all canonical Entries;
- `aitp show <entry-id>` — M1a exact-record read with full frontmatter and
  body;
- `aitp check` — M1b whole-store, read-only diagnostics over schema, pins,
  and relation targets.

## Evidence pins

Every mutable reference uses:

```yaml
target: relative/path
at: sha256:<digest> | git:<revision> | run:<id> | version:<id> | retrieved:<time>
locator: exact section, equation, line, or object
```

Saving verifies pins that can be checked locally.

## Agent behavior

The installed `$aitp` Skill:

1. runs `enter` at the start of research work;
2. opens cited evidence before relying on a claim;
3. records only durable moments;
4. fills the CLI-generated template rather than inventing a format;
5. runs `enter` again before ending.

Conversational filler, scratch work, and unverified speculation are not durable memory.
