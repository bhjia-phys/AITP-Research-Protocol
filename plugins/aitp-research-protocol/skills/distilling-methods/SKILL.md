---
name: distilling-methods
description: Distill a repeated, stable research procedure from recorded evidence into a local method-card Note, keep cards current with pinned trials and supersession, and gate promotion into a plugin Skill behind two explicit human decisions. Observe eligible procedures with a low-trust method-observation marker, review candidates conservatively, pin post-card exact trials, and route through a card decision (Approve/Defer/Reject) then a separate publication choice (Publish now/Keep local). Trigger when a stable procedure recurs (explicit request, two or more independent sessions, or the same failure plus workaround twice) and when trial evidence arrives for an existing card.
---

# Distilling Methods

A method card is a ledger Note that records one repeated, stable research
procedure. Cards inform; Skills route. A card is evidence in the store — never
a dispatcher, registry, or index. Draft, revise, approve, and publish a card
only through the gates below; every step stays inside the existing Note and
Entry schema.

## Method observations

A method observation is a low-trust candidate marker placed in an ordinary
durable Entry. It signals "this Entry is worth reviewing as a method-card
candidate" — nothing more. It does not prove the procedure ran twice, does
not prove independent sessions/chains, does not prove a card/trial/approval
exists, and does not allocate a workstream.

### Marker grammar

```text
> method-observation: <slug>

## ... ordinary Entry sections ...
```

- If the marker is present it must be the Entry body's first line; the next
  line must be blank; at most one marker per Entry.
- `<slug>` reuses `[a-z0-9][a-z0-9-]{0,62}`.
- The runtime does not validate the marker, slug, position, or uniqueness;
  these are Skill completeness checks, and tests must not fabricate runtime
  validation for them.

### Eligible observation

Add the marker only to a newly created ordinary durable Entry whose body
directly records one actual execution of a non-trivial, reusable procedure —
its inputs, steps, outputs, verification, and limitations:

- `run`, `result`, `observation` are preferred kinds;
- `code_change` only when the same Entry also records the procedure's actual
  execution and verification;
- `failure` alone is not a successful workaround occurrence; a repeated
  failure+workaround must consist of two distinct attempts' failure and
  direct resolver/execution evidence, with the marker on the Entry recording
  the actual workaround execution;
- `source`, `decision`, `closeout` are not eligible;
- never backfill or rewrite an old Entry, never mark a legacy-derived record,
  and never split one campaign, retry, or logical event to inflate the count.

Before writing a marker, search the current Topic for existing observations
and cards:

```text
rg "^> method-observation:" .aitp/topic/entries/
rg "^> method-card:" .aitp/topic/notes/
```

When an applicable card already exists, do not write a same-slug candidate
marker; instead, create the Entry as a post-card trial that exact-`sha256:`
pins that card (§Record protocol). When the new use falls outside the card's
applicability, compare overlap first — only a genuinely different procedure
gets a new slug.

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

## Candidate review

Conservative harvest of method-observation markers into card drafts:

1. Only the current workspace's single `.aitp/topic/` — never cross-Topic
   scan, merge, or propagate.
2. Before harvesting, run `aitp enter` and `aitp check --json`: exit 2 means
   the store state is unknown — fail closed immediately; exit 1 requires
   reading the findings, and any malformed/duplicate/missing/hash error on a
   candidate Entry, card, or pin blocks the draft.
3. `rg` is discovery only. For every Entry hit, read the canonical record with
   `aitp show <entry-id> --json`; never simulate `show` with an ad-hoc
   Markdown parser. Card/Note files are still read directly at
   `.aitp/topic/notes/<note-id>.md`, because `list`/`show` project Entries
   only.
4. Verify marker grammar, eligible kind, non-legacy-derived, refs/pins, and
   the Entry's own execution evidence. Exclude plans, examples, restatements,
   retries, campaign sub-steps, and duplicate indices of the same evidence.
5. Two same-slug markers only nominate review. The Skill must conservatively
   judge whether they represent two distinct logical execution roots; when
   the current schema cannot prove it, no-op or ask the researcher. Never
   auto-draft by marker count, and never claim "two independent sessions have
   been deterministically proven."
6. When the trigger holds and no existing card covers the procedure, proceed
   through the normal `aitp note prepare → fill → aitp note save` path, using
   exact `sha256:` `basis_refs` to pin the pre-card Entry files that triggered
   the draft. Write the generalization gap into Limitations.
7. After card save, that round of pre-card harvest ends: do not modify the
   triggering Entries, do not backfill a card pin into them, and do not count
   them as trials. Pre-card Entries can only enter the card's `basis_refs`;
   they are never retroactively reinterpreted as post-card trials.

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
  Entry never counts as a pinned trial. `run`/`result` are the preferred
  trial kinds; `observation`/`failure` count only when the Entry body itself
  directly records one card execution and its outcome — not because it
  references or summarizes a similar procedure. Two qualifying trials of
  the same exact card revision represent two distinct logical executions;
  they do not automatically equal independent sessions, independent
  reproductions, or scientific correctness. Entries with a different Note
  ID, a different hash, pre-card Entries, old-revision trials, and backfill
  pins do not count for the current revision. A contradictory trial is
  recorded as an ordinary `failure` Entry or revision evidence, and the
  review stops — the card never auto-resolves a failure and is never
  silent-edited. An auto-drafted card always stays `review_state:
  agent_draft`; without at least one qualifying post-card trial it must not
  be adopted as a validated method. Two qualifying trials trigger a
  publication proposal only — never approval, never publication.
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
  When the proposal gate (below) is reached, the main agent assembles a
  proposal packet — exact card Note ID, path, and SHA; the two qualifying
  trial IDs and their exact pins; applicability, limitations, and
  contradictions; and the proposed Skill routing boundary and its
  tool/adapter dependency — then offers `Approve` / `Defer` / `Reject`.
  Natural-language answers are allowed, but only an unambiguous mapping to
  one outcome continues; `Other`, dismiss, timeout, or no answer means
  zero-write. On a clear answer the agent itself executes
  `aitp record prepare --kind decision --authority human --created-by
  researcher --idempotency-key <card-revision-approval-outcome>`, fills the
  decision body, exact-`sha256:` pins the card revision, saves, and runs
  `check`/`enter` to verify. The researcher does not run commands, edit
  drafts, or fill YAML. Only an Entry whose content is clearly an approval,
  whose `authority` is `human`, that pins the current exact revision, and
  whose post-save verification succeeded satisfies the approval gate.
  `Defer` and `Reject` are also recorded as human `decision` Entries to
  avoid repeated prompting, but neither constitutes approval. `Defer`
  re-prompts only on new qualifying evidence, an explicit researcher
  request, or a new revision; `Reject` re-prompts only on a new revision or
  an explicit researcher reopen. A save/check failure, a changed hash, or an
  ambiguous choice all block progression to the next question.
- **Publication gate (human).** Only after approval **and** an explicit human
  instruction to publish may the card move into the plugin Skill library as a
  `SKILL.md` with provenance preserved. Publishing is a separate human act,
  never automatic and never a consequence of approval alone. Only after the
  first approval `decision` Entry is saved and verified does the agent offer
  `Publish now` / `Keep local` as a separate second question. Again, only an
  unambiguous answer continues. The agent saves the second choice as an
  independent human `decision` Entry with a separate stable idempotency key,
  exact-pinning the same card revision. `Keep local` records the choice and
  stops — no re-prompt until the researcher explicitly reopens or a new
  revision appears. `Publish now` is a durable, recoverable explicit human
  publish request; only after its post-save verification succeeds may a
  subsequent plugin-Skill publication task begin. `Publish now` does not
  authorize Hakimi runtime or any agent to mutate the installed plugin
  directly — it authorizes the main agent to proceed through the normal
  code-change flow in the AITP protocol/plugin repository, preserving
  card/trials/decisions provenance and running tests; that is a separate
  reviewed repository task, not a native coordinator file-write side effect.
  Both questions are initiated by the main agent only. Subagents may return
  candidate or review results but must not ask the researcher
  approval/publication questions, must not answer on the researcher's
  behalf, and must not bypass the existing preset/profile routing; this
  feature hardcodes no model or new preset.
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

## Platform tool, method card, and Skill — three-layer boundary

- **Tool/adapter executes**: Hakimi or an external platform adapter handles
  SSH, Slurm, rsync, job polling, argv, secure cwd/env, timeout, remote
  status, and error classification; AITP Python never implements these
  platform mechanisms.
- **Method card records a stable procedure**: the AITP card summarizes
  dependency order, preconditions, resource limits, verification anchors,
  stop conditions, and the failure map from recorded real execution
  evidence; a card never dispatches tools.
- **Skill routes**: a published Skill decides when to use the procedure and
  calls existing deterministic tools/adapters; a Skill never copies
  scheduler/SSH/rsync implementations.
- Remote evidence continues to be expressed through local immutable
  pointer/report files + pins; a bare `host:path` is never accepted as
  locally verified evidence.
- Host/session Goal belongs to Hakimi's Goal/Research Frame; AITP never
  auto-imports or overrides a Topic Research Goal. Only a
  researcher-confirmed durable research goal/decision is recorded through
  the existing AITP path.

"Auto-distill into a Skill" therefore does not mean generating Slurm/SSH
logic into Python; it means producing a card from AITP evidence, passing
through trials and two human gates, then publishing a routing Skill that
calls deterministic platform tools.

## Fallback and native orchestration

The AITP 0.8 lifecycle is a **model/Skill-driven best-effort fallback**, not
a runtime callback, post-save hook, or exactly-once guarantee. When no
native host orchestration is present, the `using-aitp` Skill performs
best-effort harvest at session start (after the existing enter/check/card
retrieval, search observation markers), at durable Entry creation (low-noise
judgment of eligibility), and at session end (review new observations, new
cards, and new trials). A proposal may be re-raised after an
interrupted/recovered session; no exactly-once claim is made.

A native host (Hakimi future Feature, planned but not implemented) would
own session/turn checkpoint, deduplication, recovery, question interaction,
and adapter state — but still cannot guarantee procedure-semantic judgment,
scientific correctness, or behavior superior to plain files. AITP always
owns the ledger, evidence, method-card, trial, revision, approval, and
publication semantics; Hakimi always owns agent orchestration, platform
tool invocation, session interaction, and degraded UX. Hakimi never copies
the AITP parser/validator and never writes `.aitp` canonical files directly.

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
build a card index, registry, or enumerating dispatcher; auto-draft a card
by marker count alone; count a pre-card Entry as a post-card trial; let a
subagent ask or answer approval/publication questions; hardcode a model or
preset for distillation; accept a bare `host:path` as locally verified
evidence; claim exactly-once, runtime auto-discovery, scientific
correctness, or behavior superiority over plain files as verified.
