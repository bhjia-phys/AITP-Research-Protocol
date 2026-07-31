# AITP Roadmap and Product Design

Status: active master plan, v3.1. Revised after a second and third external
adversarial review and a study of the QuantumBFS `quantum.harness`
repository.
Changes in v3.1: the `created_at` ordering claim removed — target existence
at save time is the only causal proof, and `aitp check` validates final
state without reconstructing history; `resolves` limited to one target;
`falsified` dropped (outcome fit is expressed by the match vocabulary);
`aitp check` given a hard read-only contract; run conventions scoped to
expensive/remote runs; `verified-run` renamed `run-backed`; four-source
matrix directions corrected.
Changes from v2 (v3): `receipts.jsonl` removed; trust-model wording
downgraded to what is actually checkable; open-item closures typed
(`resolution` field with per-kind and resolver-kind rules); contradiction
criteria tightened so competing hypotheses are not mislabeled; `question`
template extended; M0.6 gate split, with its suite deliverable upgraded from
skeleton to executable core; budgets stated in nonblank lines, with M0.5 as
deduplication without net growth; versioned `--json` moved to M1a; harness
lessons absorbed (basis-kind tags on quantitative anchors,
source/why/risk/fix parameter rows, estimate-vs-actual cost, honest match
verdicts, confirm-the-setup and pushback norms).
Base: M0 ledger (`docs/design.md`), M0.5 (`docs/slim-core-plan.md`).

## Product definition

AITP is a local-first research-memory protocol for long-running collaboration
between a researcher and AI agents.

The end state has exactly two kinds of objects:

1. **Four stores** — the canonical knowledge sources;
2. **Relation records** — typed, provenance-carrying, append-only movements
   between them.

The four stores:

```text
L  literature   external (arXiv / INSPIRE / publishers); local mirror: references/
M  AITP memory  .aitp append-only records and reviewed artifacts (agent-facing)
H  researcher   judgment, taste, corrections; never stored, leaves attributable traces
D  documents    the research itself: theory/, manuscripts/, reading notes, Obsidian
```

M is memory; D is the research. Notes live in M; derivations and manuscripts
live in D; M pins D and cites L. H gates promotion.

Every durable cross-store movement is a relation record with `created_by`,
`created_at`, and an evidence pin where reachable. One universal state
pattern: **proposals live as drafts; accepted relations are saved records.**

| Relation | Direction | Carrier | Gate |
|---|---|---|---|
| reading & citation | L → D | `references/reading-notes/<citekey>.md`; citekeys in manuscripts | Git |
| source assessment | L → M | `source` Entry (`retrieved`/`version` pin, optional `trust`, optional `citekey`); retraction or refutation recorded by a newer Entry superseding the old | open the original before citing |
| claim grounding | D → M | any Entry's `sha256`/`git` pin on a D artifact | validated at save |
| distillation | D → M | Note (`basis_refs`), compiled artifact (`source_records`) | human review for artifacts |
| writing | M → D | manuscripts and notes assembled from reviewed material | Skill discipline |
| new-claim capture | D → M | new claims in D reflow as Entries | Skill discipline |
| correction / decision | H → M | `decision` Entry (`authority: human`) | human |
| temporal evolution | M → M | `supersedes` / `resolves` / `contradicts` | validated at save |
| cross-topic link | M → M | link record (rationale + author + pin) | human-confirmed save |
| literature need | M → L | `next_action`, open questions, hypothesis Planned Tests | none; acted on by Skills |
| publication | D → world | manuscripts; `compile export` for reviewed skills | human |

Scope honesty: not every movement is recorded. Ordinary D edits live in Git;
but once a record in M depends on a D artifact, it pins the exact revision.
H judgments that were never written down are invisible — that is a human
discipline problem, measured (not solved) by the conformance suite.

## Trust model

AITP provides **auditability, not tamper-proofing**. The default threat model
is a single researcher with non-adversarial agents.

With writes going through the CLI and an intact Git history, the following
are checkable:

- Append-oriented history. Content is plain Markdown, so post-hoc edits are
  visible in Git. `aitp check` (M1b) re-validates the whole store — schema,
  pins, relation targets, closure rules — and surfaces inconsistency in the
  final state; it does not reconstruct history.
- Prediction order as **write-time causality**: a resolving Entry can only
  reference a prediction that already exists when it is saved; the save-time
  target-existence check is the causal proof. `created_at` is a CLI-stamped,
  editable record time, not an ordering proof. This proves protocol record
  order at write time — not that the agent had not seen the outcome.
- Reviews bind content: every `reviews.jsonl` line carries the artifact's
  sha256; editing an artifact after review makes the review visibly stale.
- `created_by`, `authority`, and timestamps are attributable *claims*; Git
  makes post-hoc edits visible, but cannot detect a first write that was
  already false.

Not guaranteed:

- that the agent had not seen a result before writing a prediction;
- that `authority: human` was a real human act;
- that Git history was never amended;
- that nobody edited canonical files directly (visible in Git, not
  prevented).

An optional high-trust mode (independent human signing key, protected remote
branch, external timestamps) may be added later; it is out of the default
scope.

Honesty about automation: read/write judgment, contradiction discovery, and
next-step suggestion are **Skill behaviors**. The protocol makes them aided
and auditable, not automatic. The conformance suite below measures how often
they actually happen — that measurement, not runtime enforcement, is the
answer to the v5 adoption gap.

## What L0–L4 became

The original L0–L4 architecture described **cognitive states of research
objects**, not software layers. The v5 failure (a 128 MB typed store, 7,400+
registry files, 495 stalled review groups, "adoption gap is the core
bottleneck") came from implementing that cognitive state machine as a
software state machine. The states are preserved; the software is gone.

| Original | Failed implementation | Current form |
|---|---|---|
| L0 source acquisition | bridges, adapters | `references/` conventions + `source` Entry + literature Skills |
| L1 provisional understanding | intake schemas | `drafts/`, reading notes, working Notes |
| L3 exploratory output | candidate objects, state machine | ordinary Entries + open items (failure / prediction / question) + `agent_draft` insight and hypothesis artifacts |
| L4 validation & adjudication | validation runtime, promotion flow | open-item lifecycle (`resolves` + typed closures, automatic reopen) + write-time order checks + `compile check` + hash-bound human review |
| L2 trusted memory | typed kernel, schema sync | `human_reviewed` compiled artifacts; sharing via `compile export` |
| routing policy L0→L1→L3→L4→L2 | kernel enforcement | Skill discipline + the write gate |
| source trust levels A–E | source schema field | optional `trust` field on `source` Entries |
| decision_point blocking | control-plane runtime | the conversation itself; outcome recorded as `decision` |
| reset test | persistent kernel state | ledger + closeout + `enter` |
| three research lanes | lane runtimes | methodology Skills over one ledger |

Cognitive state becomes data (record kinds + `review_state`). Transition
discipline becomes Skills. The only software enforcement is the write gate:
evidence-bearing and compiled claims require provenance at save; review
transitions are human-gated.

## Python boundary

Python does exactly four verbs: **validate**, **persist** (atomic,
idempotent), **project** (`enter`/`show`/`list`/`check`), **benchmark**.

Deterministic constraints belong in the gate, not in Skills: target-existence
and closure validation at save, whole-store re-validation (`check`),
review↔hash binding, relation existence, pin verification, template
completion.

`aitp check` (M1b) is read-only diagnostics over the whole store: no cache,
no repair, no migration, no new canonical files. It cannot detect missed
records, forged first-write attribution, or whether an agent saw a result
early — those remain suite- and Git-visible concerns.

- Cumulative runtime budget: stage-end caps below, counted as **nonblank
  lines** of the canonical package (`grep -c '\S'` per module, summed);
  ~2,000 lines absolute maximum; each module below 400 nonblank lines; no
  new dependencies beyond the vendored YAML. Caps are planning allowances: a
  stage that exceeds its allowance cuts scope, per the invariants.
- Agent behavior conformance is measured by an external suite; the runtime
  never tries to enforce research behavior.

Never in Python: semantic selection or ranking, summarization, distillation
content, contradiction detection, next-step suggestion, durable-event
judgment, literature retrieval, PDF parsing, embeddings.

## Open items

`failure`, `prediction`, and `question` are **open items** — one lifecycle:

- `resolves` names exactly one open item and closes it. The resolving Entry
  carries a `resolution` closure field; the validator enforces target
  existence, target kind (`failure` | `prediction` | `question`), and a
  closure value allowed for that kind:

  | Target kind | Allowed closures |
  |---|---|
  | `failure` | `fixed`, `cancelled`, `invalidated` |
  | `prediction` | `observed`, `cancelled`, `invalidated` |
  | `question` | `answered`, `cancelled`, `invalidated` |

  `cancelled` means the test or work was abandoned — it must not masquerade
  as an outcome; `invalidated` means the item itself was ill-posed or based
  on an error. To close two items with one piece of work, write two
  resolving Entries; both may pin the same evidence.
- A prediction closed as `observed` must be resolved by an `observation`,
  `result`, or `run` Entry with evidence, and its body states the outcome
  against the written expectation — matched, partly matched, or did not
  match, and why. A hypothesis excluded by a did-not-match outcome is
  settled by superseding the hypothesis or opening a failure, not by a
  second prediction-closure state.
- An item reopens when its resolving Entry is superseded and no other
  active resolver remains (existing M0 mechanism).
- A contradiction is not a kind: it is a `failure` Entry carrying
  `contradicts: [A, B]`, allowed only when both sides share one validity
  domain and one set of conventions, are expected to hold simultaneously,
  and are logically or numerically incompatible. Its template requires:
  overlapping validity domain, shared conventions, why coexistence is
  impossible, and pinned evidence for both sides. Competing hypotheses not
  yet discriminated, or claims in disjoint validity domains, are not
  contradictions — they live as hypothesis artifacts or open questions.
- `enter` groups all unresolved open items by kind: unresolved failures,
  open predictions, unanswered questions, unsettled contradictions.

`prediction` sections: Prediction And Basis, Distinguishing Power, Planned
Test (refs and limitations required). An Entry resolving a prediction can
only be saved after the prediction exists; the save-time target-existence
check is the order guarantee.

`question` sections: Precise Question Or Obligation; Context, Assumptions,
And Dependencies; Why It Matters; Discharge Criterion And Evidence Required.
An agent-authored question states its basis in Context — a ref, or an
explicit note that the researcher posed it.

## Agent conformance suite

An external evaluation suite (scenario scripts + scoring rubrics), **not
part of the runtime**, built before M1 and run at every gate. It scripts
research sessions against agent + Skills and scores:

- `enter` executed unprompted at session start;
- resolved failures not re-proposed;
- corrections recorded, and behavior changed in later sessions;
- durable-event miss rate and filler false-record rate, scored jointly;
- prediction saved before the run it constrains;
- stale or missing pins disclosed;
- contradiction scenarios retrieve evidence for both sides.

The suite is built to resist gaming: it scores outcomes, not rituals.
Scenarios hide decisive conventions and resolved failures that change a
concrete action only if the memory was actually used, and require citing the
decisive record with an evidence locator; seeded record counts exceed the
`enter` recent window to force `list`/`show`/`rg`; typed-event recall and
precision are scored jointly, and a one-size closeout counts as a type
error. IDs, paths, phrasings, and numbers are randomized, with held-out
scenarios whose gold labels never enter the repository; assessors are blind
to condition. The control group runs a *hash-identical* semantic policy with
two short I/O appendixes — the AITP CLI vs. direct Markdown writes under the
same templates — in isolated environments (the control has no AITP on PATH),
so the comparison isolates the write gate rather than the templates. If the
CLI shows no measurable advantage, simplify toward conventions.

Suite scores are necessary, not sufficient. Dogfooding stages also record
longitudinal adoption metrics — share of active sessions that ran `enter`,
human review minutes, draft abandonment, records-per-session noise —
because the v5 failure was abandonment under maintenance cost, not low
scores.

Each stage gate reports suite scores alongside code tests. Rubric thresholds
are defined in the suite, not negotiated per stage.

## Stages

One gate at a time. A stage that does not fit its budget is cut, not
expanded. Budgets are cumulative end-of-stage caps for the canonical runtime,
in nonblank lines.

### Stage status

Implementation prompts must respect this table: only a green-lit stage may
be implemented, and only from its implementation-level spec. Stages marked
"design only" must not be implemented or "helpfully" started early.

| Stage | Status | What stands between it and implementation |
|---|---|---|
| M0 — Ledger | done; stable baseline (`ledger-core` branch) | — |
| M0.5 — Slim core | **done** (gate passed 2026-07-30; addendum in `docs/slim-core-plan.md`) | — |
| M0.6 — Adopt & bootstrap | **green-lit**; three independent gate items, per-item implementation specs ready: item 1 `docs/m0.6-init-adopt.md`, item 2 `docs/m0.6-bootstrap.md`, item 3 `docs/m0.6-suite.md` | nothing — implement per item, in any order |
| M1a — Memory that restores | design only; blocked | M0.5 + M0.6 gates; executable suite; `--json` schema freeze before golden fixtures |
| M1b — Open items & pilot | design only; blocked | M1a gate; freeze `aitp/lite-entry-0.2` (single-target `resolves`, `resolution` enum, contradiction criteria, `aitp check` contract) |
| M2 — Reviewed artifacts | design only; blocked | M1b gate; real reviewed material in the dogfood Topics |
| M3 — Cross-topic links | design complete (`docs/cross-topic-links.md`); blocked | ≥ 3 real Topics; M2 gate |
| M4 — Collaborator protocol | design complete (`docs/collaborator-design.md`); Skill-only, +0 runtime lines | M1b pilot evidence; suite thresholds |
| Hakimi contract | not an AITP stage | after M4 |

### M0.5 — Slim core (end ≤ 1,000)

Per `docs/slim-core-plan.md`. One canonical runtime — the duplicate copy is
removed — with **zero net growth**: the surviving package stays at or below
its current ≈ 980 nonblank lines, plus at most benchmark scaffolding.
Golden parity, benchmarks, no new features.

### M0.6 — Adopt and bootstrap (~1 week; end ≤ 1,100)

Three independent gate items; the `topics.toml` convention itself is a plain
file, not a gate condition. Implementation specs: item 1
`docs/m0.6-init-adopt.md`, item 2 `docs/m0.6-bootstrap.md`, item 3
`docs/m0.6-suite.md`.

- `aitp init --adopt`: create `.aitp/` inside an existing research tree
  without touching content or imposing the fixed layout. Gate item 1: works
  on both dogfood trees without modifying any existing file, verified by
  before/after tree hashes; dry-run, conflict, and rollback paths are
  tested.
- Workspace `topics.toml` file convention (portable Topic IDs vs. local
  paths); no catalog CLI. Its minimal example and portable-ID rules are
  frozen before M1a.
- Lazy bootstrap for legacy stores: read-only inventory and hash manifest
  (fixed location and format) plus a `source` Entry per legacy corpus; one
  bootstrap working Note per active Topic, marked legacy-derived in its body
  with exact legacy locators. The Note stays provisional — a `decision`
  Entry (`authority: human`, pinning the Note's content hash) records that
  the researcher confirmed it as recovery orientation, not as revalidated
  science. Legacy decisions, failures, and conventions enter only as
  individually confirmed drafts marked legacy-derived — never as new
  verification. Gate item 2: bootstrap Notes confirmed by human decision
  Entries on both dogfood Topics; key-fact recall is scored against a
  researcher-written gold set; false-import rate uses judgeable atomic
  claims in the bootstrap Note as its denominator; human time is recorded
  with explicit start/stop points and reported as a median.
- Executable conformance core (not a skeleton): a minimal but runnable
  suite — scenario scripts, the scoring rubric, one plain-files control
  adapter, at least one held-out scenario — plus cold-start metrics. Gate
  item 3: the core suite runs end-to-end in both isolated conditions (the
  control has no AITP on PATH) with pre-registered scoring thresholds.

### M1a — Memory that restores (~2 weeks; end ≤ 1,300)

- `enter` v2 (deterministic structural sections, no semantic ranking;
  labels legacy-derived material as orientation-only); `aitp show`;
  `aitp list`; closeout and correction discipline; `using-aitp` update.
- `enter`/`show`/`list` emit versioned `--json` with golden fixtures.
- `enter` performance work: the 1,000-Entry `enter` sits at ≈ 0.94 s on the
  recorded machine (~6% under the 1 s threshold; fails under load), with
  per-record YAML frontmatter parsing ≈ 80% of the cost. M1a must widen
  that margin — faster frontmatter loading or a cheaper projection path —
  without changing output semantics.

Gate: suite-scored resumption checklist on both dogfood Topics, against the
control group; all ledger tests pass unchanged; `--help` < 250 ms and
1,000-Entry `enter` < 1 s.

### M1b — Open items and behavior pilot (~2 weeks; end ≤ 1,450)

- Schema `aitp/lite-entry-0.2`: `prediction` and `question` kinds;
  single-target `resolves` with the typed `resolution` closure field and
  target-kind/resolver-kind validation; `contradicts` on failures under the
  strict criteria; `aitp check` whole-store re-validation; Note `supersedes`
  validation; optional `citekey`/`trust` on `source` Entries. v0.1 records
  remain valid without migration.
- Run conventions: `run` Entries record host, remote path, scheduler ID,
  seed, and partial/cancelled states, and pin an existing local manifest or
  pointer bundle (manifest + validation + output digests + index) rather
  than a fixed new bundle shape. For expensive or remote runs they also
  record estimated vs. actual cost (wall, memory); consequential parameters
  are recorded as source/why/risk/fix rows so a later session can see what
  can drift — a template convention, not validator schema. Lean-specific
  fields are deferred until the first real Lean Topic.
- `aitp-collaborator` alpha pilot; `surveying-literature` and
  `analyzing-a-source` land here as use-driven increments.

Gate: suite shows prediction order respected and corrections persisting
across sessions; the pilot advances one real question over ≥ 2 sessions;
v0.1 records untouched.

### M2 — Reviewed artifacts (~3–4 weeks; end ≤ 1,700)

- `.aitp/topic/compiled/`: four artifact types (`knowledge`, `skill`,
  `insight`, `hypothesis`) with `basis_refs`, `source_records`,
  `supersedes`; type-specific sections (validity domain, failure modes,
  evals for skills, competing alternatives for hypotheses). In `knowledge`
  artifacts, quantitative anchors live in a table with a per-row basis-kind
  tag — `literal` (verbatim from a cited source, with locator), `analytic`
  (derived from stated premises, with premise refs), or `run-backed` (from a
  pinned `run` Entry, with the cross-check named) — and each row carries its
  own basis ref. `compile check` requires tags from this enum and validates
  that the declared refs exist; it checks structure, not honesty. Untagged
  numbers cannot be published as reviewed quantitative anchors. The `brief`
  type is dropped as redundant with working Note + closeout + `enter`.
- `aitp compile prepare|save|check|review|export`; append-only
  `reviews.jsonl` binds each transition to the artifact's sha256;
  post-review edits make the review visibly stale; `compile export` refuses
  unreviewed or stale artifacts and never overwrites.
- Skills: `synthesizing-knowledge`, `comparing-with-memory`; `writing-it-up`
  follows once reviewed material exists. Existing distilled technical skills
  are back-annotated with provenance, evals, and review status.

Gate: ≥ 1 reviewed knowledge artifact + 1 reviewed skill with passing evals
+ 1 visibly-marked draft insight from a real Topic; provenance gaps block
`compile check`; post-review edits detected; unreviewed export refused.

### M3 — Cross-topic links (~2 weeks; end ≤ 1,900; start only with ≥ 3 real Topics)

- `aitp catalog init|add|list` over `topics.toml`; `aitp link prepare|save`.
- Saving a link requires explicit human confirmation; as with `decision`
  Entries, an agent may execute the save on the human's behalf, attributed
  via `created_by`. Inferred links remain drafts.
- `aitp-catalog` Skill; discovery via `rg`; no sync, no projection, no index.

Gate: ≥ 5 human-confirmed links answer a real cross-topic question with
exact provenance; zero index; discovery recall compared against an `rg`
baseline.

### M4 — Collaborator protocol (~1 month; +0 lines)

- `aitp-collaborator` full protocol: competing hypotheses, discriminating
  tests, predictions before outcomes, immediate correction capture, visible
  uncertainty.
- Prospective evaluation via the conformance suite: ≥ 4 real sessions, with
  the plain-files baseline.

Gate: suite rubric thresholds pass — an active question advances, proposed
tests discriminate specific hypotheses, predictions precede outcomes,
corrections persist, uncertainty stays visible.

### Hakimi contract (after M4; hakimi's milestone, not an AITP stage)

AITP hardens the contract: schema versioning discipline and versioned
`--json` (from M1a), extended golden fixtures that any agent integration
must pass. The interface is CLI + files — no API server, no SDK. hakimi
owns web retrieval, PDF reading, reasoning, and any private caches (never
written back).

## Workspace ground-truth decisions

Decisions forced by the real workspace survey
(`/home/bhjia/AI_workspace/Theoretical-Physics`):

1. **Topics are not blank directories** — `init --adopt` (M0.6) initializes
   `.aitp/` inside existing trees without imposing a layout.
2. **Many Topics share one workspace** — per-topic stores plus a
   workspace-level `topics.toml` convention (M0.6); link machinery stays in
   M3. Portable Topic IDs decouple memory from local paths.
3. **Execution is remote-first** — run Entries pin local pointer bundles
   with output digests and record host, remote path, scheduler ID, and seed.
4. **Obsidian stays the human-facing D pole** — AITP memory is the
   agent-facing M pole; they cross-link via pins and citekeys; AITP does not
   absorb the vault.
5. **Literature keys** — the citekey is the universal human handle and
   foreign key; arXiv ID, DOI, ISBN, and INSPIRE texkeys are identifiers
   inside the bib, not keys. One canonical `library.bib` per Topic.
6. **Legacy is bootstrapped lazily, not migrated** (M0.6) — inventory,
   hash manifest, human-confirmed bootstrap working Notes, individually
   confirmed `legacy-derived` drafts; inactive Topics bootstrap on first
   resumption.
7. **Guard hooks and the v5 MCP server are retired, not replaced** —
   orientation is absorbed by `enter` + Skills; the write path is owned by
   the CLI. All agent platforms integrate via CLI + per-platform Skills.
8. **Skill governance gains a per-skill review state** (M2).

## Methodology skill library

Each Skill encodes one research activity in six sections: triggers → read
protocol → method → record protocol → compare protocol → stop conditions
(when to pause and ask the human).

| Skill | Stage | Responsibility |
|---|---|---|
| `using-aitp` | M0→M1a | session lifecycle: when to read, durable-event judgment, closeout |
| `surveying-literature` | M1b | literature need → search → triage → reading notes + source Entries |
| `analyzing-a-source` | M1b | deep-read one source: reproduce, bounded claims, assumptions, killers |
| `comparing-with-memory` | M2 | check failures/conventions before proposing; contradictions after results |
| `synthesizing-knowledge` | M2 | draft compiled artifacts with evidence maps; request human review |
| `writing-it-up` | post-M2 | assemble notes/manuscripts from reviewed material; reflow new claims |
| `aitp-catalog` | M3 | cross-topic discovery and link proposals |
| `aitp-collaborator` | M1b alpha → M4 | long-horizon question→hypothesis→prediction→test loop |

## Non-goals

Vector stores or embeddings; graph databases; sync/projection engines;
`enter --task` semantic selection; Python-generated distillation content;
required hooks, daemons, MCP servers, or schedulers; transcript or
chain-of-thought storage; auto-saved inferred links; automatic
insight→knowledge promotion; multi-user permissions or federation (Git plus
author/authority/review provenance until a concrete failure disproves it);
task management; tamper-proofing or signing infrastructure beyond the
optional high-trust mode; validation-status ladders on `result` Entries — a
`result` is a recorded project outcome with an evidence boundary, not a
credibility rank, and `enter` never uses `kind` as a credibility signal;
the `brief` artifact type (redundant); a dedicated referee-comment kind
(handled by `source` + `decision` conventions until real pain demonstrates
otherwise).

## Non-negotiable invariants

- Evidence before abstraction; append history, never silently rewrite.
- Claims stay within the trust model: auditable and tamper-evident, not
  tamper-proof. Documentation must not promise more.
- Markdown files stay readable without AITP; any future index is disposable.
- Review transitions are human-gated; a compliant agent never promotes its
  own output — attribution makes violations visible, not impossible.
- Canonical runtime exists exactly once; Python only validates, persists,
  projects, benchmarks; behavior conformance is measured, not enforced.
- Every new capability is justified by a real research workflow, with an
  acceptance test and a complexity/performance cost statement.
