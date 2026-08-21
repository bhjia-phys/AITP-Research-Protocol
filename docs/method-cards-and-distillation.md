# Method cards and distillation (2026-08-15 reviewed Skill-only change; 2026-08-21 0.8.0 amendment)

This document records the 2026-08-15 reviewed Skill-only change (AITP 0.6.0):
automatic session-boundary current-state maintenance in `using-aitp` and the
new implicit `distilling-methods` meta-Skill that turns repeated, stable
research workflows into **Method cards** — local `mode: theory` Notes with a
generic marker, a human-gated publication path, and **no behavioral
runtime/CLI/schema change; version strings synchronized**. The natural-use
evidence is
[`feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md`](../feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md).

The **2026-08-21 0.8.0 amendment** (below) is a further Skill-only change:
method-observation markers, conservative candidate review, post-card exact
trials, two-step human decisions (card approval then publication choice),
the fallback/native lifecycle boundary, and the platform tool/card/Skill
three-layer relationship. It changes **no** runtime, CLI, schema, transport,
or exit code — only Skill text, manifest descriptions, and version strings
(all four surfaces → 0.8.0). It is a reviewed user-requested design change,
not a roadmap stage, natural-use gate, or behavioral evaluation result.

## quantum.harness — scale and adopt/adapt/reject evidence

At the researcher's request, the method-card system of the external
`quantum.harness` repository (read-only study; no file there was touched) was
examined as reference evidence. Measured scale (2026-08-15 snapshot):

| Measure | Value |
|---|---|
| Repository size | ≈ 57 MB, 928 files, 496 Markdown files |
| Skills | 66 under `skills/` (10 `method-*` skills + many `using-*` tool skills), 7 `tracks/` |
| Method-card corpus | `.knowledge/methods/`: 36 `METHOD.md` cards + 12 `INDEX.md` files |
| Supporting reference files | `method-survey.md` (677 lines), `method-property-map.md` (220 lines), `method-property-checklist.md` (M1–M14 axes), `ref.bib`, rendered literature |

Card shape there: a fixed template — "What it is", a Properties table over
the M1–M14 axes (tasks/outputs, regime, accuracy class, dimension fit,
statistics, entanglement, sign problem, symmetry, time/memory cost, control
knob, scale frontier, bias, hard blocker), Cost & scaling, Accuracy &
guarantees, Tasks it computes, Recommended for, Key reference, Benchmarks,
How it is used / Operational (owning skill, default workflow, verification
pointers, cross-links to survey/map/companion methods).

**The quantum.harness method cards are primarily human-curated, not
auto-distilled from session records**: the cards are hand-written prose with
citation keys into `ref.bib` and hand-maintained cross-links; the `INDEX.md`
files are generated headers for `rg`-based KB navigation, not distilled
knowledge. AITP's `distilling-methods` therefore distills cards **from
recorded AITP evidence with explicit human gates**, and does not replicate
the curated-survey machinery.

### Adopted, adapted, rejected (objective adjudication)

Adopted as AITP design constraints:

- **Three-layer separation** — card informs, Skill routes, tool executes; a
  card never dispatches or forces an action.
- **Fixed card shape** — one template over the existing theory-Note headings,
  a generic marker, no per-method bespoke formats.
- **Completeness tests — Skill check, not a runtime check** — the runtime
  save/check gate treats a card Note exactly like any other Note (the same
  deterministic schema and pin checks; it never inspects the marker, the
  title slug, or any section text, and it cannot detect a natural-language
  placeholder). The card-shape requirements are a **Skill-level completeness
  check** the agent must satisfy before saving, relying on, or proposing a
  card: nonempty frontmatter `summary`, nonempty pinned `basis_refs`, the
  `> method-card: <slug>` marker matching the title slug (on revision also a
  valid `supersedes` naming the replaced card Note), every required theory
  section non-empty, pins verified, no unfilled template prompts; a card
  that fails the check is corrected or dropped — the Skill never saves,
  relies on, or proposes an incomplete card.
- **Stop-on-mismatch and verification anchors** — trials pin the exact card
  (`sha256:` ref on the card Note file); when a trial contradicts the card,
  stop and ask instead of forcing the method.
- **Ratification** — a card becomes approved only through a `decision` Entry
  with `authority: human` pinning the card Note file.

Rejected for AITP:

- **Enumerating dispatcher** — any registry/INDEX that routes work by card
  catalog; the marker `rg` is the only retrieval path.
- **Ion/symlink tooling** — the external repo's `Ion.toml`/`Ion.lock` and
  symlink-based tooling; AITP stays CLI + files with no new runtime.
- **Bulk zoo** — a large corpus of bespoke per-method scripts/tools; no bulk
  import or per-method runtime.
- **Duplicate facts** — copying factual content between a card and a Skill;
  the card cites pinned evidence, the Skill routes, and `distilling-methods`
  is the single rule source.
- **Prose-only provenance** — claims without pins; every card claim must
  trace to `basis_refs` or be flagged as a gap.
- **Tests-not-in-CI** — any test added must run in the repository CI.

## AITP-native Method card profile (no new schema)

A Method card is an existing Note profile, nothing new:

- `mode: theory` Note via `aitp note prepare --mode theory --title "Method
  card: <slug>" --created-by agent:<name>`;
- title `Method card: <slug>`; body first line exactly
  `> method-card: <slug>` (the generic marker; `rg "^> method-card:"` is the
  only retrieval path — no registry, no INDEX, no enumeration);
- Topic-local theory Notes: a card lives in the local Topic store and is
  preserved when superseded (revision writes a new Note, never an edit of the
  old card); `list`/`show` project Entries only (`show` takes Entry IDs), so
  cards are never `list`/`show` targets — the Note paths are `enter`'s
  recent-Notes projection and `check`;
- frontmatter uses the shipped v0.1 Note schema only: nonempty `summary`,
  `basis_refs` (required, nonempty, pinned), `created_by`, `review_state`
  (always `agent_draft` — the only legal value; human approval is expressed
  only by an external human `decision` Entry pinning the card), optional
  explicit `workstreams` (never inferred), `supersedes` (canonical Note IDs
  only);
- body keeps the six exact theory headings (question/obstruction, setup/
  assumptions, central construction/argument, main result, checks/examples/
  failure modes, limitations/open questions) with a fixed content mapping
  (triggers + route-elsewhere; inputs/preconditions/applicability/resource/
  tool handoff; steps/routing; outputs/cost/control knobs; stop-now/
  benchmarks/cross-check/failure map/trials; limits/open gaps), per the
  bundled `method-card-template.md`.

Approval is expressed outside the Note schema, exactly like any Note
confirmation: a `decision` Entry with `authority: human` pinning the card
Note file. No new frontmatter field, mode, or review state exists.

## Automatic organization at session boundaries

`using-aitp` now maintains current state automatically:

- **Session start** — `enter` + `check` + evidence review + Method-card
  marker retrieval (`rg "^> method-card:"`), then plan.
- **Session end** — when the session produced a durable delta and the current
  state is behind it, the agent appends the missing closeout and/or an
  agent-authority working Note (superseding the stale record, never editing
  it); **no durable delta ⇒ zero writes** (no closeout, no Note, no record).
- **Pre/post verification** — `enter`/`check` before writing and again after
  any save; the save is not verified until the post-run confirms it.
- Organization is never handed to the researcher. This is Skill judgment over
  the existing write path, not a runtime rule.

## Distillation state chain and human publication gate

1. **Trigger** — explicit request, or the same stable workflow across ≥ 2
   independent sessions/chains, or the same failure + workaround twice;
   otherwise no-op (low-noise rule).
2. **Draft** — a Method card drafted automatically from recorded evidence
   (existing Note prepare/save path); generalization beyond the evidence goes
   to Limitations.
3. **Trial** — each subsequent use records a `run`/`result` Entry that pins
   the exact card (`sha256:` ref, `locator:` the exercised section/step).
   Only **post-card, exact-content** trials count: the Entry must be recorded
   after the card exists and must pin that card Note's current content hash
   (`sha256:` of the card Note file) — Entries recorded before the card was
   drafted are never backfilled into the trial count, and a trial pinning any
   other content does not count.
4. **Revision** — a changed method becomes a **new** card Note whose
   `supersedes` names the old card; old cards are never edited. The new card
   Note has different content and therefore a different hash, so it inherits
   **nothing** from the old card: two pinned exact-revision trials on its own
   hash lead only to a publication proposal; publication additionally
   requires a **fresh** human `decision` Entry pinning the new card and a
   **new** explicit human publish request — the old card's trials and
   approval do not carry over.
5. **Publication proposal** — after ≥ 2 pinned trials, the agent *proposes*
   publication to the researcher (a message, never a write).
6. **Approval gate** — human `decision` Entry pinning the card Note.
7. **Publication gate** — only an explicit, separate human publish request
   turns the approved card into a plugin Skill, as a reviewed Skill change.

`distilling-methods` never auto-publishes, never cross-Topic propagates a
card, never infers `workstreams`, never resolves failures, and never
summarizes in Python (distillation content is Skill work).

## No runtime boundary

This change is **Skill-only**: no behavioral runtime/CLI/schema change;
version strings synchronized; the canonical runtime stays at **1,543
nonblank lines** (target ≤ 1,550 / cap ≤ 1,600, modules < 400); M1b
dispositions, M1c, and M1d frozen contracts are unchanged; M2/M3/M4
statuses are unchanged; no daemon, hook, MCP server, or vector service
is added.

## 0.8.0 amendment (2026-08-21; Skill-only)

The 0.8.0 amendment extends the distillation rule surface without any
runtime, CLI, schema, transport, or exit-code change. The canonical runtime
stays at **1,793 nonblank lines**; plugin version moves to **0.8.0** across
the four release surfaces (`pyproject.toml`, `__init__.py`,
`kimi.plugin.json`, and `.codex-plugin/plugin.json`) and the separate
`aitp.contract.json` adapter surface. The
`aitp/adapter-contract-0.1` schema, commands, flags, transport schemas,
and Skill paths are unchanged. No M1b/M1c/M1d/M1e disposition changes; no
M2/M3/M4 flip. It is a reviewed user-requested design change, not a
natural-use gate or behavioral evaluation result.

### Method-observation marker (candidate, not proof)

A `> method-observation: <slug>` marker in an eligible durable Entry body's
first line is a **low-trust candidate tag** — it signals "worth reviewing as
a method-card candidate" and nothing more. It does not prove the procedure
ran twice, does not prove independent sessions/chains, does not prove a
card/trial/approval exists, and does not allocate a workstream. The runtime
does not validate marker grammar, slug, position, or uniqueness — these are
Skill completeness checks. Detailed grammar, eligible kinds, and the
candidate-review protocol are defined solely in the `distilling-methods`
Skill; this document points at them and does not duplicate the rules.

### Pre-card basis vs post-card exact trial

Pre-card execution Entries can only enter a card's `basis_refs`; they are
never backfilled with a card pin and never counted as trials. A post-card
trial must be created after the card Note was saved and must exact-`sha256:`
pin that exact saved card file at creation. Two qualifying trials of the
same exact revision represent two distinct logical executions — not
automatically independent sessions, independent reproductions, or scientific
correctness. A contradictory trial stops the review; the card never
auto-resolves a failure and is never silent-edited.

### Two-step human decision

The 0.6.0 single approval + publication gate is refined into **two separate
human `decision` Entries**, both recorded by the agent (the researcher does
not run commands or fill YAML):

1. **Card decision** — after two qualifying trials, the main agent assembles
   a proposal packet and offers `Approve` / `Defer` / `Reject`. Only an
   unambiguous answer continues; `Other`, dismiss, timeout, or no answer
   means zero-write. `Defer` and `Reject` are also recorded as human
   decisions (to avoid repeated prompting) but neither constitutes approval.
2. **Publication choice** — only after the approval decision is saved and
   verified, the agent offers `Publish now` / `Keep local` as a separate
   question, saved as an independent human `decision` Entry with a separate
   idempotency key. `Publish now` authorizes the main agent to proceed
   through the normal code-change flow in the AITP repository — it does not
   authorize any agent or runtime to mutate the installed plugin directly.

Both questions are **main-agent-only**: subagents may return candidate or
review results but must not ask or answer approval/publication questions.
No model or preset is hardcoded for distillation.

### Fallback and native lifecycle

The AITP 0.8 lifecycle is a **model/Skill-driven best-effort fallback**, not
a runtime callback, post-save hook, or exactly-once guarantee. `using-aitp`
performs best-effort harvest at session start (observation-marker search
after existing enter/check/card retrieval), at durable Entry creation
(low-noise eligibility judgment), and at session end (review new
observations, cards, and trials). A proposal may be re-raised after an
interrupted/recovered session — no exactly-once claim.

A native host (Hakimi future Feature, planned but not implemented) would
own session/turn checkpoint, deduplication, recovery, question interaction,
and adapter state — but still cannot guarantee procedure-semantic judgment,
scientific correctness, or behavior superior to plain files. AITP always
owns the ledger, evidence, method-card, trial, revision, approval, and
publication semantics; Hakimi always owns agent orchestration, platform
tool invocation, session interaction, and degraded UX. The detailed native
lifecycle, owner scope, and implementation gate are planned for future
Hakimi C6/H6 work; before that, Hakimi docs write planned/unavailable only,
and the 0.8 Skill fallback is independently usable.

### Platform tool, method card, and Skill — three-layer boundary

- **Tool/adapter executes**: Hakimi or an external platform adapter handles
  SSH, Slurm, rsync, job polling, argv, secure cwd/env, timeout, remote
  status, and error classification; AITP Python never implements these.
- **Method card records a stable procedure**: the AITP card summarizes
  dependency order, preconditions, resource limits, verification anchors,
  stop conditions, and the failure map from recorded execution evidence; a
  card never dispatches tools.
- **Skill routes**: a published Skill decides when to use the procedure and
  calls existing deterministic tools/adapters; a Skill never copies
  scheduler/SSH/rsync implementations.
- Remote evidence is expressed through local immutable pointer/report files
  + pins; a bare `host:path` is never accepted as locally verified evidence.
- Host/session Goal belongs to Hakimi's Goal/Research Frame; AITP never
  auto-imports or overrides a Topic Research Goal.

### Harness adjudication boundary (unchanged)

The 2026-08-15 Harness adjudication boundary remains in force: adopt the
card/Skill/tool three-layer separation, fixed card shape, completeness
tests, stop-on-mismatch with verification anchors, and human ratification;
reject enumerated dispatchers/registries/INDEX, Ion/symlink tooling, bulk
card zoos, duplicated facts, prose-only provenance, and tests-not-in-CI.
Never claim behavior superiority over plain files. The 0.8 amendment adds
the two-step decision and the fallback/native boundary within this frame;
it does not relax any existing rule.
