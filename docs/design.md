# AITP Evidence Ledger Design

Status: stable M0 baseline. The schema evolves to `aitp/lite-entry-0.2` in
M1b (new `prediction` and `question` kinds; `resolves` generalized to
failures, predictions, and questions with a typed `resolution` closure
field and target-kind validation; `contradicts` on failure Entries under
strict criteria; `aitp check` whole-store re-validation; Note `supersedes`
validation; optional `citekey`/`trust` on `source` Entries) per
`docs/roadmap.md`; v0.1 records remain valid without migration.

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

### `aitp init`

Operate only on a blank directory, except for an optional `.git`. Create the fixed research layout and one Topic record. Never initialize Git or infer scientific content.

### `aitp enter`

Read the Topic, valid Entries, and Notes. Return:

- memory status;
- recent active Entries with exact source paths;
- limitations and pinned references;
- unresolved active failures;
- current next action;
- recent Notes.

The output must distinguish recorded state from scientific truth and expose missing or malformed memory.

### `aitp record prepare/save`

Prepare exactly one draft from the selected kind-specific template. Save only after fast structural, relation, evidence-pin, and prompt-completion checks.

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

Prepare either:

- `working`: current research line, evidence map, uncertainty, and next actions;
- `theory`: assumptions, conventions, derivation, checks, gaps, and implications.

A Note synthesizes pinned research evidence. It is not the sole evidence for a result.

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
