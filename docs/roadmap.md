# AITP Roadmap and Product Design

Status: active master plan. Current state: M0.5 gate passed; **M0.6
implementation closed; original empirical gate not passed** (approved
narrowed reviewed claim; review packet in `docs/archive/m0.6-gate-review.md`);
M1a **done; deterministic gate passed** (evidence in
`docs/archive/m1a-stage-notes.md`); **M1b-R1 done; remaining M1b candidates
deferred** — the 2026-08-12 reviewed freeze revision
(`docs/archive/m1b-adjudication.md`) selected the read-side slice M1b-R1
(`aitp check` v0.1-only + compact `enter` text), implemented per
`docs/archive/m1b-r1-spec.md`, deterministic gate passed (evidence in
`docs/archive/m1b-r1-stage-notes.md`). M2/M3/M4 remain blocked design
options. Completed specs, adjudications, and stage notes are frozen in
`docs/archive/` and take no part in any sync discipline. Earlier revisions
of this file are Git history, not duplicated changelog entries.


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
M  AITP memory  .aitp append-only records (agent-facing)
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
| distillation | D → M | Note (`basis_refs`); a reviewed-artifact form only if M2 is authorized on natural demand | human review |
| writing | M → D | manuscripts and notes assembled from recorded material | Skill discipline |
| new-claim capture | D → M | new claims in D reflow as Entries | Skill discipline |
| correction / decision | H → M | `decision` Entry (`authority: human`) | human |
| temporal evolution | M → M | `supersedes` / `resolves` / `contradicts` | validated at save |
| cross-topic link | M → M | link record (rationale + author + pin) | human-confirmed save |
| literature need | M → L | `next_action`, open questions, hypothesis Planned Tests | none; acted on by Skills |
| publication | D → world | manuscripts; an export mechanism only if M2 is authorized | human |

Scope honesty: not every movement is recorded. Ordinary D edits live in Git;
but once a record in M depends on a D artifact, it pins the exact revision.
H judgments that were never written down are invisible — that is a human
discipline problem, measured (not solved) by any future predeclared
evaluation; the conformance suite is dormant.

## Simplicity and stage authorization

The following evidence-before-complexity rules are binding on AITP design and
stage decisions.

For the M0.6→M1a transition, the approved 2026-08-10 M0.6 gate review was
the sole M1a authorization transition. It flipped the M1a roadmap row to ready;
the deterministic implementation gate is now passed and M1a is done. The
implementation and gate evidence are recorded in `docs/archive/m1a-stage-notes.md`;
no behavioral or treatment-superiority claim is implied.

1. A predecessor gate closes only its own claim. It makes the next stage
   eligible for adjudication; it never automatically green-lights all designed
   scope.
2. Runtime work requires an explicit roadmap status flip and a separately
   reviewed implementation-level spec selecting the smallest coherent,
   evidence-backed slice.
3. Line caps are ceilings, not targets. Spare budget never justifies scope.
   If a future selected slice needs headroom, the pre-declared first release
   is deduplicating the three repeated scan/validate loops in `query.py`/
   `state.py`/`diagnostics.py` into one shared reader — deduplication, not
   validator compression.
4. If scope lacks evidence or does not fit, split, revise, defer, or drop it
   before code; never compress validators, weaken compatibility, or expand caps.
5. After the M1a gate, run a deliberately small natural-use pause: at least two
   ordinary, unscripted real-Topic sessions plus a short review of actual use,
   unmet pain, workarounds, and maintenance cost. “No M1b runtime yet” is a
   valid result; no new gold set or synthetic suite is required for this pause.
6. The M1b candidate-inventory pre-spec is frozen. Every row
   receives exactly one disposition — selected, deferred, moved to a named
   slice, or dropped — in a reviewed freeze revision recording the full revised
   roster and dependencies; all candidates need not ship together. Deferred,
   moved, dropped, and no-runtime outcomes produce no implementation spec. Only
   after that review may a selected implementation spec be drafted, separately
   reviewed, and green-lit. Selecting no M1b runtime slice is a valid outcome. Selected
   schema/payload versions are re-frozen before implementation.
7. M2/M3 are design options, not commitments. Their predecessor gates and
   minimum Topic counts are necessary but insufficient; natural workflow must
   first show that Entries/Notes or `rg`/ordinary citations are inadequate.
8. Suite runs and researcher-written gold sets are episodic, predeclared gate
   instruments—not routine session work or automatic work at every gate.

## Trust model

AITP provides **auditability, not tamper-proofing**. The default threat model
is a single researcher with non-adversarial agents.

With writes going through the CLI and an intact Git history, the following
are checkable:

- Append-oriented history. Content is plain Markdown, so post-hoc edits are
  visible in Git. The shipped M1b-R1 `aitp check` (v0.1-only, read-only,
  zero-write) re-validates the whole store — schema, pins, relation targets,
  closure rules — and surfaces inconsistency in the final state; it does not
  reconstruct history and never repairs. Prior to M1b-R1 no such whole-store
  diagnostic was a current command.
- Prediction order as **write-time causality**: a resolving Entry can only
  reference a prediction that already exists when it is saved; the save-time
  target-existence check is the causal proof. `created_at` is a CLI-stamped,
  editable record time, not an ordering proof. This proves protocol record
  order at write time — not that the agent had not seen the outcome.
- Reviews would bind content only if a reviewed-artifact stage ships: a
  review record binds the artifact's sha256, and editing after review makes
  the review visibly stale. No such mechanism is shipped today (M2 is an
  unpre-designed option).
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
and auditable, not automatic. A future predeclared evaluation would measure
how often they actually happen — that measurement, not runtime enforcement,
is the answer to the v5 adoption gap; the conformance suite is **dormant**
and has never scored.

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
| L4 validation & adjudication | validation runtime, promotion flow | open-item lifecycle (`resolves` + typed closures, automatic reopen) + write-time order checks + human review via Skills (a reviewed-artifact mechanism only if M2 is authorized) |
| L2 trusted memory | typed kernel, schema sync | reviewed synthesis as ordinary D files pinned by human decision Entries (an artifact store only if M2 is authorized) |
| routing policy L0→L1→L3→L4→L2 | kernel enforcement | Skill discipline + the write gate |
| source trust levels A–E | source schema field | optional `trust` field on `source` Entries |
| decision_point blocking | control-plane runtime | the conversation itself; outcome recorded as `decision` |
| reset test | persistent kernel state | ledger + closeout + `enter` |
| three research lanes | lane runtimes | methodology Skills over one ledger |

Cognitive state becomes data (record kinds + `review_state`). Transition
discipline becomes Skills. The only software enforcement is the write gate:
evidence-bearing claims require provenance at save; review
transitions are human-gated.

## Python boundary

Python's current implementation boundary has exactly five verbs:
**validate**, **persist** (atomic, idempotent), **project** (`enter`/`show`/`list`),
**diagnose** (`check`), **benchmark**. `check` is the shipped M1b-R1
read-only whole-store diagnostic (v0.1-only, schema `aitp/check-report-0.1`).

Deterministic constraints belong in the gate, not in Skills: target-existence
and closure validation at save, relation existence, pin verification, template
completion, and — as shipped in M1b-R1 — whole-store re-validation via
`check`. Review↔hash binding remains a deterministic check where the
relevant reviewed-artifact capability is selected.

The shipped `aitp check` is read-only diagnostics over the whole
store: no cache, no repair, no migration, no new canonical files. It cannot
detect missed records, forged first-write attribution, or whether an agent saw
a result early — those remain suite- and Git-visible concerns.

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
part of the runtime**, built before M1 and used as predeclared, episodic gate
evidence only where a stage's gate calls for it. It is not routine session work
or automatic work at every gate. It scripts research sessions against agent +
Skills and scores:

For this evaluation boundary, orchestration infrastructure belongs to a
separate optional future project. AITP contains only the frozen suite inputs
and the [external evaluation-harness contract](external-evaluation-harness.md);
no harness is implemented or required here. That contract is the normative
requirements and ownership handoff. FROZEN v6 remains **dormant** — an
anchored, unexecuted preregistration — and does not retroactively satisfy the narrowed M0.6 closure;
any future external output requires its own review/revision/refreeze before it
could be considered evidence. No external output is needed for current M1a
authorization.

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
decisive record with an evidence locator; portable seeds hold ≥ 28 active
Entries — more than `enter`'s top-20 window (counted on active Entries),
with at least one decisive memory-gated fact outside that window — forcing
`rg`/direct file reads, the M0.6 retrieval path (`list`/`show` arrive in
M1a); typed-event recall and precision are scored jointly, and a one-size
closeout counts as a type error. IDs, paths, phrasings, and numbers are
randomized. Held-out scenarios are never used for prompt/Skill iteration
once the agent config is frozen (pre-first-run structural fixture fixes are
recorded in the stage notes), and their gold labels never enter a seed or
the agent-readable run environment — gold stays assessor-side and may live
in the repo; assessors are blind to condition. The control group runs a
*hash-identical* semantic policy with two short I/O appendixes — the AITP
CLI vs. direct Markdown writes under the same templates — in isolated
environments (the control has no AITP on PATH), so any measured difference
is attributed to the full AITP I/O layer — commands, validation, `enter`
projection, template mechanics — not to policy content or template wording.
If the CLI shows no measurable advantage, simplify toward conventions.

Suite scores are necessary, not sufficient. Dogfooding stages also record
longitudinal adoption metrics — share of active sessions that ran `enter`,
human review minutes, draft abandonment, records-per-session noise —
because the v5 failure was abandonment under maintenance cost, not low
scores.

When a gate predeclares suite evidence, it reports those suite scores alongside
code tests. Rubric thresholds are defined in the suite, not negotiated per
stage; a gate without a predeclared suite instrument does not invent a routine
suite run.

## Stages

One gate at a time. A stage that does not fit its budget is cut, not
expanded. Budgets are cumulative end-of-stage caps for the canonical runtime,
in nonblank lines; caps are ceilings, not targets.

### Stage status

Implementation prompts must respect this table: only a green-lit stage may
be implemented, and only from a separately reviewed implementation-level spec
that selects the smallest coherent, evidence-backed slice. Stages marked
"design only" or "design option" must not be implemented or "helpfully"
started early; a predecessor gate never authorizes later scope automatically.

| Stage | Status | What stands between it and implementation |
|---|---|---|
| M0 — Ledger | done; stable baseline (`ledger-core` branch) | — |
| M0.5 — Slim core | **done** (gate passed 2026-07-30; addendum in `docs/archive/slim-core-plan.md`) | — |
| M0.6 — Adopt & bootstrap | **implementation closed; original empirical gate not passed** — item 1 (`init --adopt`) and item 2 deterministic inventory implementation are complete; item 3 is an anchored, unexecuted FROZEN v6 packet. Specs: item 1 `docs/archive/m0.6-init-adopt.md`, item 2 `docs/archive/m0.6-bootstrap.md`, item 3 `docs/archive/m0.6-suite.md` | The approved narrowed gate review closes M0.6. Original bootstrap Notes/decisions, recall/false-import/human-time, held-out S3, paired S1/S2, cold-start, conformance, causal, and treatment-advantage evidence is not measured; deferred; not counted, and does not block M1a |
| M1a — Memory that restores | **done; deterministic gate passed** (`docs/archive/m1a-spec.md`, evidence in `docs/archive/m1a-stage-notes.md`) | Versioned read projections: `list`, `show`, and `enter` v2; closeout-first handoff; Note-age structural signal; generated goldens; deterministic S1/S2 regression; read-only GW_librpa acceptance; all tests and performance/line caps. This is not a behavioral or treatment-superiority gate |
| M1b — Open items & pilot | **M1b-R1 done; remaining M1b candidates deferred** — 2026-08-12 reviewed freeze revision recorded in `docs/archive/m1b-adjudication.md`; the selected read-side slice M1b-R1 is implemented per `docs/archive/m1b-r1-spec.md` and its deterministic gate passed (evidence in `docs/archive/m1b-r1-stage-notes.md`). B, C–E, Followup 2 (`lineage`), and Followup 6 (structured prepare) remain deferred; F → M4; G independent Skill track; H dropped | The R1 gate is closed. Deferred/dropped rows produce no implementation spec and may return only through a new reviewed freeze revision; M2/M3 require their own natural-demand evidence. This is not a behavioral or treatment-superiority gate |
| M2 — Reviewed artifacts | design option; blocked | M1b selected-slice gate, if any; natural workflow must show Entries/Notes are inadequate before scheduling, then real reviewed material in the dogfood Topics |
| M3 — Cross-topic links | design option (`docs/archive/cross-topic-links.md`); blocked | M2 gate, ≥ 3 real Topics, and a natural cross-Topic failure of `rg` plus ordinary citations before scheduling |
| M4 — Collaborator protocol | blocked design option (`docs/archive/collaborator-design.md`); Skill-only, +0 runtime lines | If a reviewed freeze revision selects F in M1b, its separately reviewed selected-slice spec and pilot evidence; otherwise M4's own natural-demand and prospective-evidence adjudication against the plain-files baseline. The dormant FROZEN v6 suite is not a dependency |
| Hakimi contract | not an AITP stage | after M4 |

### M0.5 — Slim core (end ≤ 1,000)

Per `docs/archive/slim-core-plan.md`. One canonical runtime — the duplicate copy is
removed — with **zero net growth**: the surviving package stays at or below
its current ≈ 980 nonblank lines, plus at most benchmark scaffolding.
Golden parity, benchmarks, no new features.

### M0.6 — Adopt and bootstrap (~1 week; end ≤ 1,100)

Three independent gate items; the `topics.toml` convention itself is a plain
file, not a gate condition. Implementation specs: item 1
`docs/archive/m0.6-init-adopt.md`, item 2 `docs/archive/m0.6-bootstrap.md`, item 3
`docs/archive/m0.6-suite.md`.

Current status (`docs/archive/m0.6-stage-notes.md`): item 1 runtime is implemented —
`aitp init --adopt` has dry-run/conflict/rollback coverage. Recovery evidence
records byte-identical before/after evidence for the heavy legacy tree; GW_librpa
adoption succeeded but its original session preserved no before/after tree-hash
record. Exact repository/Git-history locators are unavailable, so no claim of
two preserved real-tree hash records is made. Item 2's runtime inventory is
implemented: it deterministically traverses and orders paths and hashes content
in a timestamped local manifest; its `generated_at` and absolute `root` make
repeated manifest bytes non-identical. Bootstrap Notes, human decision Entries,
recall, false-import rate, and human-time evidence are not measured; deferred;
not counted.
Item 3's suite core and static repair are complete. A 2026-08-09 no-turn
preflight verified the v6 hashes/anchor, S3 seed, clean treatment export, and
packet neutralization, then stopped before S3 because exact model/prompt
identity and two-machine/account isolation were unavailable. That preflight is
preparation and an explicit invalid-start decision, not a held-out report or
score. FROZEN v6 is therefore **dormant** — an anchored, unexecuted
preregistration; held-out
S3, paired S1/S2, cold-start, conformance, causal, and treatment-advantage
evidence is not measured; deferred; not counted.

The approved 2026-08-10 narrowed gate review
([review packet](archive/m0.6-gate-review.md)) closes M0.6 under the narrowed reviewed
claim. M1a has since completed its deterministic implementation gate; the
implementation evidence and current counts are recorded in
[`docs/archive/m1a-stage-notes.md`](archive/m1a-stage-notes.md). The original full-gate
acceptance descriptions below remain for provenance, but are not complete and
their empirical items are deferred/not counted. The unscored 2026-08-06 dry
run's projection-aware sweep, check-before-record, and evidence-backed
`resolves` lessons remain Skill-only preparation (+0 runtime lines).

- `aitp init --adopt`: create `.aitp/` inside an existing research tree
  without touching content or imposing the fixed layout. The local
  implementation and tests cover dry-run, conflict, rollback, and fixture
  byte-identity; the recorded real-tree evidence is asymmetric as described
  above.
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
  verification. **Original gate item 2 acceptance (not complete;
  deferred/not counted):** bootstrap Notes confirmed by human decision
  Entries on both dogfood Topics; key-fact recall is scored against a
  researcher-written gold set; false-import rate uses judgeable atomic
  claims in the bootstrap Note as its denominator; human time is recorded
  with explicit start/stop points and reported as a median.
- Executable conformance core (not a skeleton): a minimal but runnable
  suite — scenario scripts, portable per-scenario seeds, the scoring rubric,
  one plain-files control adapter, at least one held-out scenario — plus
  cold-start metrics. **Original gate item 3 acceptance (not complete;
  deferred/not counted):** the core suite runs end-to-end in both isolated
  conditions (the control has no AITP on PATH) with pre-registered scoring
  thresholds.

### Dense-ledger dogfood input to M1

A read-only audit of `/home/bhjia/physics/GW_librpa` on 2026-08-06 found a
real 60-Entry store: 41 active, 19 superseded, 26 results, three closeouts,
and no Notes. The store made the M1 priorities concrete:

- `enter` is an orientation view, not a sufficient retrieval interface for a
  dense store; kind/date filtering and exact record opening are required.
- a newest-timestamp scan can surface a stale handoff when sessions omit or do
  not replace closeouts; the source Entry and time must stay visible.
- mutable local evidence had drifted (37 missing and 78 hash-mismatched local
  pins in that dated snapshot). Reading must survive stale evidence; a selected
  and shipped `check` may report it, but save-time pin discipline must not be
  weakened.
- remote runs need host/path/job/build metadata, but unverifiable `host:path`
  strings are not evidence pins. A local manifest or pointer bundle remains
  the evidence boundary.
- the real store is a compatibility corpus, not a scratch fixture: read-path
  acceptance is run in place with a before/after hash check; write-path tests
  use a temporary copy unless a genuine research event is being recorded.

These findings refine the implemented and deterministically gated M1a design;
they do not authorize M1b, M2, or M3. See `docs/archive/m1-read-write-balance.md` and
`docs/archive/m1a-stage-notes.md`.

### M1a — Memory that restores (~2 weeks; end ≤ 1,300)

- Retrieval-first `aitp list [--kind KIND] [--since DATE] [--json]` over all
  canonical Entries, including visible active/superseded status, plus `aitp
  show <entry-id>`. Text summaries are bounded; machine output keeps complete
  values. Invalid legacy timestamps are surfaced without crashing reads.
- `enter` v2 keeps deterministic structural sections and no semantic ranking;
  labels legacy-derived material as orientation-only; treats the latest active
  closeout as the authoritative handoff (falling back to another active Entry
  only when no closeout establishes one); and retains exact source ID, time,
  and path. It sorts Notes by record time and reports only the structural count
  of active Entries newer than the latest working Note.
- No implicit last-enter cursor: incremental inspection is an explicit,
  reproducible `--since` query and `enter` remains free of local cursor writes.
- `enter`/`show`/`list` emit versioned `--json` with deliberately regenerated
  golden fixtures. `using-aitp` adds dense-store retrieval and requires each
  session closeout to replace the previous handoff; four or more related
  durable Entries are a Skill trigger to consider a working Note, not a
  runtime semantic rule.
- Error messages for stale or invalid pins provide actionable remediation
  (including the actual local digest where available) without accepting the
  changed evidence.
- `enter` performance work: the 1,000-Entry `enter` sits at ≈ 0.94 s on the
  recorded machine (~6% under the 1 s threshold; fails under load), with
  per-record YAML frontmatter parsing ≈ 80% of the cost. M1a must widen
  that margin — faster frontmatter loading or a cheaper projection path —
  without adding a persistent index or changing output semantics.

The approved 2026-08-10 M0.6 gate review authorized the M1a implementation.
M1a is now **done; deterministic gate passed** under the frozen
implementation-level spec `docs/archive/m1a-spec.md`; the auditable evidence is in
`docs/archive/m1a-stage-notes.md`. This is not a behavioral or treatment-superiority
gate.

M1a gate evidence passed: deterministic S1/S2 seed-regression checks, generated
goldens, all ledger tests, read-only byte-identical GW_librpa acceptance,
`--help` < 250 ms, 1,000-Entry `enter`/`list` < 1 s, and cumulative/per-module
line caps. A paired treatment-control evaluation remains optional future
evidence, not an M1a gate.

### M1b — Open items and behavior pilot (~2 weeks; end ≤ 1,450)

This section only indexes the authoritative A–H roster and process in
`docs/m1b-spec.md` §0.1; it is not an implementation commitment. Candidate
semantics bind only for selected rows. Nonselected outcomes produce no spec;
selected rows require the §0.1 review before a separately reviewed, green-lit
implementation spec. Any selected capability that changes an unversioned save
envelope must first freeze a versioned envelope or explicitly revise the Hakimi
adapter contract in the same change; no silent key addition is allowed.

- Candidate schema `aitp/lite-entry-0.2`: `prediction` and `question` kinds; optional
  `based_on` with the narrow meaning that the durable claim materially depends
  on existing Entries (never a substitute for evidence `refs`); single-target
  `resolves` with the typed `resolution` closure field and target-kind/
  resolver-kind validation; `check` whole-store re-validation only if the A
  store-health row is selected and shipped; Note `supersedes` validation;
  optional `citekey`/`trust` on `source` Entries. v0.1 records remain valid
  without migration. `show`/`enter` derive reverse `used_by` views from
  Markdown only if the relevant B capability is selected; no reverse index is
  written.
- Run/source templates record host, remote path, scheduler ID, command/config,
  binary digest or version, consequential build flags, input directory, exit
  status, seed, partial/cancelled state, and estimated vs. actual cost where
  relevant. Remote results pin an existing local manifest or pointer bundle
  (validation + output digests + index); naked remote paths and retrieval
  timestamps do not masquerade as integrity pins. Consequential parameters
  remain source/why/risk/fix rows — a template convention, not validator
  schema. Lean-specific fields wait for the first real Lean Topic.
- A one-command quick run capture is a suite-gated addendum, not committed core
  scope. If evidence shows that write friction, rather than event judgment,
  causes durable-event misses, its first version accepts only complete caller-
  supplied run content, requires a stable idempotency key, limitations and
  pinned evidence, and can only be expanded by a superseding Entry. It is the
  first feature cut if the 1,450-line cap is threatened.
- `aitp-collaborator` alpha behavior pilot is roster F, whose current
  disposition is **moved to M4**. It is Skill-only and is not an M1b runtime or
  gate prerequisite. Only an explicit reviewed freeze revision could select it
  for M1b.
- Roster G moves `surveying-literature` and `analyzing-a-source` to an
  independent use-driven Skill track, not tied to M1b runtime, schema, or gate.
  Each Skill may land only after real use separately justifies it and its own
  reviewed Skill change is ready.
- Roster H is the next-action closure relation, **dropped from M1b** because
  closeout-first is the selected M1a solution and no evidence yet justifies
  another task lifecycle. It may return only as a new reviewed proposal after
  natural-use evidence, never through silent M1b scope growth.

M1b-R1 is implemented per its implementation-level spec
`docs/archive/m1b-r1-spec.md` (`docs/m1b-spec.md` remains the frozen
candidate-inventory pre-spec — a design freeze, not an
implementation-level spec). Its deterministic gate **passed** on 2026-08-12;
the auditable evidence is in `docs/archive/m1b-r1-stage-notes.md`: independent code
review with no S0/S1/S2 blockers, **78 tests**, benchmark final PASS
(`--help` < 250 ms; 1,000-Entry `enter`/`list` < 1 s), a 1,423-line runtime
within the 1,425 target and the 1,450 cap, the `check.json`/`enter.txt`
goldens with M1a `enter` JSON unchanged, deterministic S1/S2 seed regression,
and GW_librpa / Power-law Heisenberg read-only acceptance with byte-identical
`.aitp` trees and exit codes consistent with the reports. **Total M1b denotes
only that the selected R1 slice completed**: B, C–E, Followup 2 (`lineage`),
and Followup 6 (structured prepare) remain deferred, F → M4, G independent,
H dropped — no later change may grow M1b scope silently. No new
gold set or synthetic suite was required for the pause.

Pause progress: the first natural-use feedback arrived 2026-08-11
(`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`, one long session
chain); the second ordinary session arrived 2026-08-12
(`feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md`, an
independent real-Topic correction session). The pause is therefore
complete; the researcher's six followup suggestions are archived in
`feedback/2026-08-12-gw-librpa-followup-feedback.md` and adjudicated in
`docs/archive/m1b-adjudication.md`.

After the pause, the actual M1a total (1,256) was reconciled against the
fixed caps in `docs/archive/m1b-candidates-1-14.md` §12.3 (M1b headroom **194**) and the `docs/m1b-spec.md` §0.1
roster process applied. Selected rows retain their validation, v0.1
compatibility, and no-index boundary; only the R1 read slice is selected.
F is moved to M4 and does not
force any A–E selection now; M4 adjudication must resolve dependencies. If the
selected collaborator protocol requires typed `prediction`/`question` records,
C or an explicitly reviewed equivalent contract must first be selected and
shipped under a separately reviewed selected-slice spec. G and H stay outside
M1b runtime/schema/gate scope. v0.1 records and GW_librpa remain untouched.

### M2 — Reviewed artifacts (design option; ~3–4 weeks; end ≤ 1,700)

M2 is not a promised stage. A no-runtime M1b result — or the completion of
the selected M1b-R1 slice — closes only the M1b decision point, produces no
implementation spec beyond it, and does not authorize M2.
Scheduling M2 requires its own natural-demand evidence showing Entries/Notes
are inadequate for recurring synthesis work; that evidence and any M1b
selected-slice gate do not authorize any design bullet. No artifact schema,
command surface, or skill is pre-designed here: if the evidence arrives, the
minimal design is derived then under the simplicity ratchet, not restored
from earlier drafts. Until then, reviewed synthesis is expressed with the
existing tools — a synthesis written in `theory/`/notes files, pinned and
superseded by an `authority: human` decision Entry.

### M3 — Cross-topic links (design option; ~2 weeks; end ≤ 1,900; start only with ≥ 3 real Topics)

M3 is not a promised stage. Scheduling requires ≥ 3 real Topics and a real
cross-Topic failure showing that `rg` plus ordinary citations cannot answer a
recurring question with sufficient provenance. The M2 gate, three real
Topics, and this natural demand are necessary but not sufficient. No
`catalog`/`link` runtime exists or is pre-designed: if the evidence arrives,
the minimal design is derived then under the ratchet. Until then, cross-Topic
references stay ordinary citations in Markdown.

### M4 — Collaborator protocol (~1 month; +0 lines)

M4 is a blocked design option and remains Skill-only (+0 runtime lines). F is
moved to M4 and does not force any A–E selection now; M4 adjudication must resolve
dependencies. If a reviewed freeze revision selects F in M1b, its separately
reviewed selected-slice spec and gate resolve dependencies; otherwise M4 has its
own natural-demand review followed by prospective evidence adjudication.

- `aitp-collaborator` full protocol: competing hypotheses, discriminating
  tests, predictions before outcomes, immediate correction capture, visible
  uncertainty.
- Prospective evaluation: ≥ 4 real sessions with the plain-files baseline,
  judged by predeclared criteria. The conformance suite is **dormant** (never
  scored) and is not a gate dependency; any future evaluation must use a
  runnable, predeclared design.

Gate: M4's natural-demand and prospective-evidence adjudication against the
plain-files baseline — an active question advances, proposed tests
discriminate specific hypotheses, predictions precede outcomes, corrections
persist, uncertainty stays visible.

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
| `surveying-literature` | G: independent use-driven Skill track | literature need → search → triage → reading notes + source Entries; lands only after real use separately justifies it and its reviewed Skill change |
| `analyzing-a-source` | G: independent use-driven Skill track | deep-read one source: reproduce, bounded claims, assumptions, killers; lands only after real use separately justifies it and its reviewed Skill change |
| `comparing-with-memory` | M2 (design option) | check failures/conventions before proposing; contradictions after results — lands only if M2 is authorized on natural demand |
| `synthesizing-knowledge` | M2 (design option) | synthesis with evidence maps and human review — lands only if M2 is authorized on natural demand |
| `writing-it-up` | post-M2 | assemble notes/manuscripts from reviewed material; reflow new claims |
| `aitp-catalog` | M3 (design option) | cross-topic discovery and link proposals — lands only if M3 is authorized on natural demand |
| `aitp-collaborator` | F: moved to M4 | separate Skill-only behavior track for the long-horizon question→hypothesis→prediction→test loop; not an M1b runtime/schema/gate dependency |

## Non-goals

Vector stores or embeddings; graph databases; sync/projection engines;
`enter --task` semantic selection; an implicit shared "last enter" cursor;
Python-generated distillation content; required hooks, daemons, MCP servers,
or schedulers; transcript or chain-of-thought storage; auto-saved inferred
links; automatic insight→knowledge promotion; multi-user permissions or
federation (Git plus author/authority/review provenance until a concrete
failure disproves it); task management or a next-action status dashboard;
unverifiable remote paths presented as evidence pins; in-place expansion of a
quick record; tamper-proofing or signing infrastructure beyond the optional
high-trust mode; validation-status ladders on `result` Entries — a `result` is
a recorded project outcome with an evidence boundary, not a credibility rank,
and `enter` never uses `kind` as a credibility signal; the `brief` artifact
type (redundant); a dedicated referee-comment kind (handled by `source` +
`decision` conventions until real pain demonstrates otherwise).

## Non-negotiable invariants

The binding simplicity ratchet is defined once in §Simplicity and stage
authorization; the trust boundary is §Trust model. This section adds only the
remaining standing invariants:

- Markdown remains readable and canonical; any future index is disposable.
- Review transitions are human-gated; attribution makes violations visible, not
  impossible.
- The canonical runtime exists exactly once; Python validates, persists,
  projects, and benchmarks, while behavior conformance is measured externally.
- Every new capability needs a real workflow, acceptance test, and
  complexity/performance cost statement.
