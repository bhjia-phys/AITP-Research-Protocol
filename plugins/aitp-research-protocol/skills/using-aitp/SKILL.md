---
name: using-aitp
description: Use AITP Research Protocol to recover and preserve grounded research state while working in a theoretical-physics repository. Trigger when entering or resuming a project, after a durable result, failure, decision, source assessment, code change, reproducible run, or closeout, and when writing a working or theory note from recorded evidence.
---

# Using AITP

Use the CLI bundled with this plugin. Resolve `../../scripts/aitp.py` relative
to this `SKILL.md` and convert it to an absolute path. Select the first
available compatible interpreter from `python3.13`, `python3.12`, `python3.11`,
and `python3`, verifying that it is Python 3.11 or newer before invoking:

```text
<compatible-python> <absolute-plugin-root>/scripts/aitp.py <command>
```

If no compatible interpreter exists, report that Python 3.11 or newer is
required. Do not require a globally installed `aitp` executable. In
user-facing explanations, the shorter `aitp <command>` spelling is acceptable.
Use ordinary filesystem tools and `rg` for ad hoc reading; there is no
`aitp search`.

## Current command map

Every command accepts `--cwd PATH` (default `.`) and `--json`. No `aitp
search` exists — `rg` over `.aitp/topic/` is the query path.

- `aitp init --topic <slug> --title "<title>"` — blank repository only;
  `--adopt` creates `.aitp/` inside an existing tree without touching
  content; `--dry-run` previews without writing.
- `aitp enter [--recent N]` — orientation at session start and before
  ending; `--recent` defaults to 20 and is a projection, not the whole
  ledger.
- `aitp inventory <path> --name <slug>` — operator-only M0.6 bootstrap tool
  (legacy scan + hash manifest); not part of routine session flow.
- `aitp record prepare --kind <kind> --authority <level> --created-by <id>
  [--idempotency-key <key>]` → `aitp record save <draft-path>`.
- `aitp note prepare --mode working|theory --title "<title>" --created-by
  <id>` → `aitp note save <draft-path>`.

## Future commands — not implemented (sync checklist)

`aitp list`, `aitp show`, `aitp check`, and the `enter` v2 handoff semantics
(M1a/M1b) do not exist yet. Do not invoke them and do not describe them as
available. When M1a or M1b lands, update in the same change:
`docs/roadmap.md` (stage status), `docs/design.md` (command contracts),
`docs/m1-read-write-balance.md` (spec index), `docs/m1a-spec.md` (M1a
implementation-level spec), `docs/m1b-spec.md` (M1b pre-spec — its
implementation-level spec follows after the M1a gate), this command map, and
README's "Current state".

## Start or resume work

1. If `.aitp/topic/TOPIC.md` does not exist and the repository is blank except for `.git`, run `aitp init --topic <slug> --title "<title>"`.
2. At the beginning of every research session, run `aitp enter`.
3. Treat its output as recorded project state, not as scientific truth. Open cited Entries, Notes, code, calculations, and pinned references before relying on a claim.
4. If `memory_status` is `partial` or `not_established`, state what is missing and inspect files directly.

The `enter` recent window is a projection, not the whole ledger: it shows the newest records and omits older active ones (`omitted_active`). Records outside the window are unread, not absent. Before planning, search the store — `rg` over `.aitp/topic/` — for the entries relevant to the current question: the newest record on every topic you will rely on, its `supersedes`/`resolves` chains, and the pinned evidence behind its claims. Before asserting that a record, pin, or relation does not exist, search the store for it.

Never infer the real research state merely from directory names, Git history, or the latest modified file.

## Record a durable moment

Record only information that should survive the current conversation:

```text
aitp record prepare --kind <kind> --authority <level> \
  --created-by agent:<name> --idempotency-key <stable-key>
```

Choose one kind: `observation`, `result`, `failure`, `decision`, `source`, `code-change`, `run`, or `closeout`. Set `authority` to the source of the event: `human` (`--created-by researcher`) when the researcher asserts it, `agent` when you act or observe.

Open the returned draft, replace every inline prompt, add precise relations and pinned references, then run:

```text
aitp record save <draft-path>
```

The CLI template is the schema. Keep claims small, state limitations, and distinguish evidence from interpretation.

- Before preparing a record, check that the ledger does not already contain the same logical event. A restatement, confirmation, or re-verification of an already-recorded convention, decision, or claim is not a durable event: cite the existing record and write nothing new. Never re-issue with `agent` authority a decision the ledger already records as `human`.
- Record a verification only when it changes a live claim or surfaces auditable evidence the ledger lacks; do not wrap an ordinary re-read or an un-triggered check as a durable event.
- Use `resolves` only when this Entry's own evidence directly closes an active failure — first check the failure's state and its `supersedes`/`resolves` chain, and confirm no existing record already settles the failure's subject. A projected counter (such as `unresolved_failures`) is ledger state, not an instruction: do not change a failure's status unless the records support the change.
- Use `supersedes` only when replacing an older Entry; never silently rewrite history.
- Use `git`, `sha256`, `run`, `version`, or `retrieved` pins for evidence that may change.
- Reuse the same idempotency key when retrying the same logical write.

## Write a note from recorded evidence

Use a Note for synthesis, not as the only evidence for a result:

```text
aitp note prepare --mode working --title "<title>" --created-by agent:<name>
aitp note prepare --mode theory --title "<title>" --created-by agent:<name>
```

Fill the generated template, cite supporting pinned sources in `basis_refs`, and save with:

```text
aitp note save <draft-path>
```

A working Note explains the current line of attack. A theory Note gives a derivation or formal argument with assumptions, conventions, checks, and open gaps.

## Work with the researcher

- Before consequential compute — scientifically critical, expensive, or convention-ambiguous — state the setup: Hamiltonian with sign and coupling conventions, boundary, sector, target observable, scale. Get an explicit confirm-or-correct when anything could be misread; a silent assumption costs more than one line of confirmation. Do not pester on routine, cheap steps.
- When the researcher pushes back, genuinely reconsider: restate the prior reasoning, take the objection seriously, change the conclusion if warranted or present both readings for re-ratification. Never capitulate by default; never defend at length. If the exchange changes course, record it as a `decision`.
- Verification that backs the current claim is not optional. Extra verification beyond that is opt-in: when a result is challenged, propose checks along the ladder limits → symmetry/consistency → convergence → cross-method → literature, with rough costs, and run only what the researcher confirms.

## Before ending

Run `aitp enter` again. Confirm that the new record is active, evidence is reachable, unresolved failures are honest, and the next action is concrete. Do not record conversational filler, speculative claims presented as results, duplicate retries, or transient scratch work.
