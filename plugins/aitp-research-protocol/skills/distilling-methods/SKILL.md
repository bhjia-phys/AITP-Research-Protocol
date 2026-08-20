---
name: distilling-methods
description: Distill a repeated, stable research procedure from recorded evidence into a local method-card Note, keep cards current with pinned trials and supersession, and gate promotion into a plugin Skill behind explicit human approval. Trigger when a stable procedure recurs (explicit request, two or more independent sessions, or the same failure plus workaround twice) and when trial evidence arrives for an existing card.
---

# Distilling Methods

A method card is a ledger Note that records one repeated, stable research
procedure. Cards inform; Skills route. A card is evidence in the store — never
a dispatcher, registry, or index. Draft, revise, approve, and publish a card
only through the gates below; every step stays inside the existing Note and
Entry schema.

## Triggers

Draft a method card only when the procedure is stable and repeated — any one
of:

1. the researcher explicitly asks for a card;
2. the same procedure ran in at least two independent sessions or chains;
3. the same failure plus its workaround recurred twice.

Triggers are satisfied by recorded evidence, never by a plan, proposal, or
speculation.

No card (no-op) when:

- the procedure is single-use, one-off, or trivial;
- an existing card, Skill, or CLI command already covers it;
- the procedure has not actually been performed yet;
- the session produced no durable records to base the card on.

Low-noise rule: one card per stable procedure. Do not split one procedure into
micro-variant cards, and do not draft a card for a procedure that belongs in
an ordinary Note.

## Read protocol

Retrieve cards only by their generic marker — never enumerate them:

```text
rg "^> method-card:" .aitp/topic/
```

There is no card INDEX, registry, catalog, or dispatcher: cards are Notes
discovered by `rg`, exactly like any other content. Before adopting a card,
read the full card Note and the records its `basis_refs` pins. A card informs
the approach; the calling Skill decides routing. When the current situation
falls outside the card's stated applicability, route elsewhere instead of
stretching the card.

## Method

A method card is the existing **theory Note profile** — no new file schema,
Note mode, or review state:

- `mode: theory`, title `Method card: <slug>` (slug rule
  `[a-z0-9][a-z0-9-]{0,62}`);
- body first line exactly `> method-card: <slug>`;
- body keeps the six fixed theory headings, filled for the method:
  - **Question And Obstruction** — the recurring question or obstruction the
    card answers, and when to route elsewhere;
  - **Setup And Assumptions** — inputs, preconditions, conventions,
    applicability, resources, and the tool/CLI handoff;
  - **Central Construction Or Argument** — the dependency-ordered steps and
    how to route through them;
  - **Main Result** — outputs with exact scope, expected cost, and the control
    knobs that set it;
  - **Checks, Examples, And Failure Modes** — stop-now triggers, benchmarks,
    cross-checks, the known failure map, and pinned trial evidence;
  - **Limitations And Open Questions** — limits and what remains open.

Frontmatter uses only existing Note fields: `summary` is a nonempty plain
statement of what the card captures, `basis_refs` pins the records the card
generalizes (nonempty, exact pin shapes), `created_by: agent:<name>` (Notes
carry `created_by`, never `authority`), `review_state` stays the
CLI-generated `agent_draft` — the save gate accepts no other value, so a
card Note can never be anything but `agent_draft`; approval is expressed
only by an external human `decision` Entry (§Record protocol) —
`workstreams` only when the card belongs to explicit research lines (never
inferred), `supersedes` names the replaced card Note on revision.

Use the bundled
[`method-card-template.md`](method-card-template.md): it keeps the six exact
headings and is directly usable as replacement content for a prepared draft.
Draft, replace, fill, and save:

```text
aitp note prepare --mode theory --title "Method card: <slug>" --created-by agent:<name>
```

Replace the generated draft body with the template body (marker line included),
remove the template's usage blockquote, keep the six headings exactly, and
fill every section from recorded, pinned evidence — the template carries no
`<!-- aitp:` prompts. Slug substitution and placeholder removal are Skill
completion checks, not runtime gates: substitute the real slug into the
title and the `> method-card: <slug>` marker line, and replace each
section's placeholder text with actual content — no placeholder survives in
the saved Note. The runtime save gate enforces only the fields that exist:
no `<!-- aitp:` prompt comments, nonempty required sections, nonempty
`summary`, nonempty pinned reachable `basis_refs`, `review_state:
agent_draft`, and valid existing `supersedes` targets — it never checks the
title, the marker line, or leftover placeholder text.

## Record protocol

- **Trial pins the exact card.** Every session that performs the method
  records its ordinary durable Entry (`run`, `result`, `observation`,
  `failure`, as appropriate) and pins the exact card it exercised:
  `target: .aitp/topic/notes/<card-note-id>.md` with `at: sha256:<digest>`.
  Card pins verify at save and at every `check`, like all pins. A trial
  counts toward the two pinned trials only when its Entry is created after
  the card Note was saved and, at creation, sha256-pins that exact saved
  card file. Entries recorded before the card Note existed never pin it:
  never backfill or rewrite a pre-card Entry to add a pin, and such an
  Entry never counts as a pinned trial.
- **Revision supersedes.** When the procedure changes, write a new card Note
  that `supersedes` the old card's Note ID; never edit the old card. A
  revision is a new Note with a new file and a new hash, and pins carry no
  revision: trials pinned to the old revision do not count for the new one,
  and the old revision's approval does not inherit. Proposing the new
  revision requires two pinned trials on that exact new revision — a
  proposal needs no approval and no publish request. Publishing the new
  revision additionally requires a fresh human `decision` pin on it and a
  new explicit publish request. The old card Note stays on disk and remains
  discoverable by the marker `rg`
  and by direct file reads at `.aitp/topic/notes/<note-id>.md` —
  `list`/`show` project Entries only and never show Notes, so superseded
  cards are read from the file or via `rg`, not through `list`/`show`.
- **Approval gate (human).** The card Note is always `review_state:
  agent_draft` — the save gate accepts no other value and no agent step
  changes it. Approval exists only as an external human `decision` Entry
  (`authority: human`) that pins the card Note file — the exact revision it
  names; that Entry is the sole expression of approval. Approval does not
  carry across revisions: a superseding Note is a different file and needs
  its own approval. Until then the card is an ordinary `agent_draft` Note.
- **Publication gate (human).** Only after approval **and** an explicit human
  instruction to publish may the card move into the plugin Skill library as a
  `SKILL.md` with provenance preserved. Publishing is a separate human act,
  never automatic and never a consequence of approval alone.
- **Proposal after two pinned trials.** Two pinned trials of the same exact
  card revision — same Note ID, same pinned `sha256:` digest — are enough
  only to *propose* a publication decision to the researcher; proposing is
  drafting, never publishing. A proposal needs no prior approval and no
  publish request — the two pinned trials alone are the whole proposal
  gate, whether the card is a first draft or a new revision.

## Compare protocol

Before drafting or revising, compare the recorded procedure against every
card the marker search returns:

- same procedure or overlapping applicability → update or supersede the
  existing card instead of duplicating;
- genuinely different procedure → new card.

Compare trial outcomes against the card's stated outputs, cost, and control
knobs: a trial that contradicts the card is evidence for a revision or a
`failure` Entry — never a silent edit of the card. Compare the card against
the Skill that routes it: a card that must decide which Skill runs has turned
into a dispatcher, which is a design failure — split the procedure back into
the Skill (workflow) and the card (facts).

Completeness before relying on a card: all six headings filled, every
input/precondition defined, outputs and cost stated, a failure map present,
and at least one pinned trial recorded. The one-pinned-trial minimum is for
reliance only — proposing always requires two post-card pins of the same
exact revision (the proposal gate above): a single pinned trial never
proposes. A proposal still needs no approval and no publish request;
publication still requires the human `decision` pin and an explicit publish
request. Verification anchors
(pins, cross-checks, benchmarks) back every step that can be verified;
an unanchored step is a gap, not a judgment call. Ratification is human
only: a card is ratified by the approval-gate `decision` Entry, never by
the agent that drafted it. The reviewed harness adjudication behind these
rules — adopt three-layer separation, fixed card shape, completeness tests,
stop-on-mismatch and verification anchors, human ratification; reject the
enumerated dispatcher, the Ion tool/symlink management, bulk card zoos,
duplicated facts, prose-only provenance, and tests-not-in-CI — is recorded
in [`../../../../docs/method-cards-and-distillation.md`](../../../../docs/method-cards-and-distillation.md).

## Stop conditions

Stop and ask the researcher when:

- the trigger rests only on a plan or speculation with no recorded repetition;
- the procedure spans multiple Topics — cross-Topic propagation is
  prohibited: never copy or port a card into another store;
- drafting would need a new frontmatter field, file schema, Note mode, or
  review state — the card profile must stay inside the existing schema;
- the researcher rejects a draft or a revision — record the rejection as a
  `decision` and stop;
- publication is requested before an approval exists.

Never: auto-publish; propagate cards across Topics; infer `workstreams`;
resolve a `failure` with a card (resolution needs direct evidence under the
ordinary `resolves` rules); generate or summarize card content in Python;
build a card index, registry, or enumerating dispatcher.
