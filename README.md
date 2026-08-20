# AITP Research Protocol

AITP is a local-first protocol for long-running collaboration between researchers and AI agents.

Its goal is not merely to save notes. A mature AITP collaborator should remember the details that matter, recover why decisions were made, preserve failed attempts, connect knowledge across Topics, extract reusable physical knowledge and technical Skills, and surface new Insights without confusing them with established results.

## North star

After weeks or years of work, a new session should be able to:

- resume a Topic without asking the researcher to repeat its history;
- trace every remembered claim to its source record, and every
  evidence-bearing record to exact pinned evidence;
- recall conventions, constraints, decisions, failures, and open questions;
- connect a current problem to relevant results from other Topics;
- distinguish physical knowledge, reusable procedure, and speculative Insight;
- propose a reusable Skill with provenance and evaluations;
- work with a researcher across many sessions without losing corrections,
  commitments, or the reasoning behind the current direction.

AITP records project memory, not scientific truth. Evidence and human judgment remain authoritative.

## Architecture

AITP's end state has two kinds of objects: **four stores** and **typed,
provenance-carrying, append-only relation records** between them.

```text
L  literature   external (arXiv / INSPIRE / publishers); mirror: references/
M  AITP memory  .aitp append-only records + reviewed artifacts (agent-facing)
H  researcher   judgment and corrections; leaves attributable traces
D  documents    the research itself: theory/, manuscripts/, notes, Obsidian
```

M is memory; D is the research. Notes live in M; derivations and manuscripts
live in D; M pins D and cites L; H gates promotion. Every durable movement
that M relies on uses one of these relation records — cite, ground,
synthesize, decide, supersede, link, review, publish — each with an author,
a time, and an evidence pin where reachable. Proposals live as drafts;
accepted relations are saved records. Not every movement is recorded:
ordinary D edits live in Git, and unwritten H judgments are invisible by
design.

The protocol has three parts:

1. **Schemas** — append-only Markdown records with evidence pins
   ([ledger design](docs/design.md)), reviewed compiled artifacts, and link
   records.
2. **A small deterministic CLI** — the write gate: validate, persist,
   project, benchmark. Nothing semantic runs in Python.
3. **Methodology Skills** — the research discipline: when to read, how to
   survey literature, when to record, how to distill, when to stop and ask.

The original L0–L4 vision is preserved as cognitive discipline and dissolved
as software. See [Roadmap and Product Design](docs/roadmap.md).

## Roadmap

The normative plan, including complexity budgets and gate definitions, is
[docs/roadmap.md](docs/roadmap.md). This README keeps the public implementation
checkpoint synchronized with it.

| Stage | Status | Outcome | Exit gate |
|---|---|---|---|
| M0 — Ledger | done | Reliable single-Topic records and Notes | Idempotent writes, pinned evidence, grounded `enter`, real-project use |
| M0.5 — Slim core | done | One canonical runtime, deduplicated without net growth | No runtime duplication, no oversized module, unchanged ledger contracts |
| M0.6 — Adopt & bootstrap | **implementation closed; original empirical gate not passed** | Deterministic `init --adopt`/`inventory` implementation and anchored, unexecuted FROZEN v6 packet; no bootstrap-validation or plain-files advantage claim | Narrowed gate review accepted; original bootstrap Notes/decisions, recall/false-import/human-time, held-out S3, paired S1/S2, cold-start, conformance, causal, and treatment-advantage evidence is not measured; deferred; not counted |
| M1a — Memory that restores | **done; deterministic gate passed** | Versioned `list`, `show`, closeout-first `enter` v2, Note-age structural signal, generated public-schema goldens, deterministic S1/S2 regression, read-only GW_librpa acceptance | Deterministic gate passed; this is not a behavioral or treatment-superiority gate. Evidence: [`docs/archive/m1a-stage-notes.md`](docs/archive/m1a-stage-notes.md) |
| M1b — Open items & behavior pilot | **M1b-R1 done; remaining M1b candidates deferred** | Authoritative A–H + Followup roster in `docs/m1b-spec.md` §0.1 and the adjudication in `docs/archive/m1b-adjudication.md`: A and Followups 1/3/4/5 selected in M1b-R1 (`check` v0.1-only + compact `enter` text), implemented per `docs/archive/m1b-r1-spec.md`; B, C–E, Followup 2 (`lineage`), Followup 6 (structured prepare) deferred; F moved to M4 Skill-only; G independent; H dropped | R1 deterministic gate passed (independent review with no S0/S1/S2 blockers; 78 tests; benchmark final PASS; 1,423-line runtime within the 1,425 target and 1,450 cap; goldens; S1/S2 regression; read-only byte-identical real-store acceptance; same-day precision-fix amendment superseding the pre-amendment 77-test/1,421-line run) — evidence in [`docs/archive/m1b-r1-stage-notes.md`](docs/archive/m1b-r1-stage-notes.md). Not a behavioral or treatment-superiority gate; `lineage` is a deferred candidate |
| M1c — Topic workstreams | **done; deterministic gate passed** | Optional explicit `workstreams` membership on Entries/Notes (unscoped legacy visible only in the global view, explicit multi-membership, no registry); repeatable `--workstream` prepare flag (duplicates rejected); single-slug scoped `enter`/`list` (`aitp/enter-0.3`/`aitp/list-0.2` with one additive top-level singular `workstream` key) with global relations computed first and strictly scoped projections including handoff; global warnings/malformed; no flag ⇒ old schemas byte-unchanged; budget target ≤ 1,550 / cap ≤ 1,600 nonblank lines, modules < 400 | Deterministic gate passed 2026-08-13: 107 tests (85 unchanged + 22 new workstream tests); benchmark final PASS (module/plugin help < 250 ms; 1,000-Entry enter/list < 1 s); runtime 1,519 nonblank lines within target/cap; real-store no-flag old-runtime parity and zero-write tree. Evidence: [`docs/m1c-stage-notes.md`](docs/m1c-stage-notes.md); frozen spec [`docs/archive/m1c-workstreams-spec.md`](docs/archive/m1c-workstreams-spec.md). Not a behavioral or treatment-superiority gate |
| M1e — Evidence lifecycle + reviewed backfill | **done; deterministic gate passed** | `sha256-once:` save-strict / check-historical pin scheme; optional `.aitp/local/check-policy.json` reviewed mutable-path policy (legacy strict drift/missing downgraded only on mutable matches; immutable/unmatched stay errors; no policy ⇒ byte-unchanged); new `aitp backfill workstreams --mapping … --decision <human-entry> [--apply]` dry-run-first, idempotent, explicit-only workstream backfill that adds/merges frontmatter membership and preserves body/other fields; budget target ≤ 1,800 / cap ≤ 1,850 nonblank lines, modules < 400 | Deterministic gate passed 2026-08-15: 154 tests passed; runtime 1,793 nonblank lines within target/cap (max module `records.py` 379); no-policy check parity asserted; backfill dry-run/apply/idempotence and human-anchor rejection asserted; `git diff --check` clean. Evidence: [`docs/m1e-stage-notes.md`](docs/m1e-stage-notes.md); frozen spec [`docs/archive/m1e-evidence-lifecycle-backfill-spec.md`](docs/archive/m1e-evidence-lifecycle-backfill-spec.md). Not a behavioral or treatment-superiority gate |
| M1d — Scoped `check` workstream health | **done; deterministic gate passed** | Single-occurrence `--workstream <slug>` on `check` (repeated flags parser-rejected) emitting the scoped `aitp/check-report-0.2`: strict admitted explicit-membership attribution (malformed, duplicate-ID, unscoped, out-of-scope, and `TOPIC.md` findings never scoped), whole-store scan and global relations computed first with the scoped report a strict subset projection (same findings, levels, codes, `(path, code, message)` order), scoped counts `entries, notes, errors, warnings, by_code, outside_scope` (per-level `by_code` buckets; `outside_scope` a pure global−scoped level delta that never affects `status`/exit), exactly four human-only scoped text lines, empty scope legal (exit 0); no flag ⇒ `aitp/check-report-0.1` byte-unchanged (JSON, text, exit, zero-write); budget target ≤ 1,550 / cap ≤ 1,600 nonblank lines, modules < 400 | Deterministic gate passed 2026-08-14: 126 tests (107 unchanged + 19 new scoped-check tests); benchmark final PASS (module/plugin `--help` < 250 ms; 1,000-Entry `enter`/`list` < 1 s); runtime 1,543 nonblank lines within target/cap (max module `records.py` 348); `git diff --check` clean. Evidence: [`docs/m1d-stage-notes.md`](docs/m1d-stage-notes.md); frozen spec [`docs/archive/m1d-workstream-health-spec.md`](docs/archive/m1d-workstream-health-spec.md). Not a behavioral or treatment-superiority gate |
| M2 — Reviewed artifacts | design option; blocked | No pre-design: triggers on natural-demand evidence that Entries/Notes are inadequate for recurring synthesis; until then, synthesis files + `authority: human` decision Entries | A no-runtime M1b decision does not authorize M2; its own natural-demand review must show Entries/Notes are inadequate first |
| M3 — Cross-topic links | design option; blocked | No pre-design: triggers on ≥ 3 real Topics and a real cross-Topic `rg`/citation failure; until then, ordinary citations, no `catalog`/`link` runtime | Natural cross-Topic use shows `rg` plus ordinary citations are inadequate, then human-confirmed links answer a real question with provenance |
| M4 — Collaborator protocol | blocked design option; Skill-only | Long-horizon question → hypothesis → prediction → test loop | M1b pilot evidence only if that pilot is selected; otherwise M4's own natural-demand and prospective-evidence adjudication against the plain-files baseline. It does not depend on the dormant FROZEN v6 suite |

The 2026-08-10 M0.6 gate-review decision is applied in
[`docs/archive/m0.6-gate-review.md`](docs/archive/m0.6-gate-review.md): M0.6
implementation is closed only under the approved narrowed reviewed claim; the
original empirical gate was **not passed**. M1a is **done; deterministic gate
passed**; see [`docs/archive/m1a-stage-notes.md`](docs/archive/m1a-stage-notes.md). This is not a
behavioral or treatment-superiority gate. The original empirical M0.6 conditions
remain not measured, deferred, and not counted.

The 2026-08-15 reviewed Skill-only change ships as **0.6.0**: automatic
session-boundary current-state maintenance (enter/check, evidence review,
method-card retrieval at session start; agent-authority closeout/working-Note
upkeep at session end, superseding stale records, with **no-delta zero-write**
and pre/post verification) and method-card distillation — stable repeated
procedures become **method-card theory Notes** (the existing `mode: theory`
Note profile, body-first-line marker `> method-card: <slug>`, fixed six
headings), drafted automatically on trigger but gated through pinned trials,
a human `decision` Entry approval, and an explicit human publish request.
It is not a roadmap stage: **no behavioral runtime/CLI/schema change; version
strings synchronized** (runtime stays 1,543 nonblank lines) and no M2/M3/M4 flip. The natural-use
feedback is [`feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md`](feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md);
the design record is [`docs/method-cards-and-distillation.md`](docs/method-cards-and-distillation.md).
The same-day GW/LibRPA feedback
([`feedback/2026-08-15-gw-librpa-natural-use.md`](feedback/2026-08-15-gw-librpa-natural-use.md))
is folded in as template/Skill guidance only: `record`/`note` prepare
prompts now show the required `target`/`at` ref shape (the key is `at`,
never `pin`), and `using-aitp` teaches evidence-lifecycle pin choice,
immutable pointer manifests, old-pin drift interpretation,
`malformed`-vs-warning terminology, and session-start handoff/goal checks. No CLI flag, schema, exit code, or runtime line changed.

### Current checkpoint

M1a is done; M1b-R1 is done (remaining M1b candidates deferred); M1c
(Topic workstreams) is **done; deterministic gate passed**
(see item 6 below), M1d (scoped `check` workstream health) is
**done; deterministic gate passed** (see item 7 below), M1e
(evidence lifecycle + reviewed backfill) is **done; deterministic gate passed**
(see item 9 below), and the 2026-08-15 reviewed Skill-only **0.6.0** slice
(automatic session-boundary maintenance + method-card distillation) is
shipped (see item 8 below). The
two-session ordinary natural-use pause is **complete**, the
M1b reviewed freeze revision is recorded, and the selected M1b-R1 read-side
slice is implemented per [`docs/archive/m1b-r1-spec.md`](docs/archive/m1b-r1-spec.md) with
its **deterministic gate passed** (evidence in
[`docs/archive/m1b-r1-stage-notes.md`](docs/archive/m1b-r1-stage-notes.md)):

1. `aitp init --adopt` is implemented and tested, and has been exercised on
   real trees; preserved operator before/after hash evidence is incomplete per
   [`docs/archive/m0.6-gate-review.md`](docs/archive/m0.6-gate-review.md). This is a documented
   real-tree evidence gap, not a claim of complete bootstrap validation.
2. `aitp inventory` is implemented with deterministic traversal, ordering, and
   content hashing in a timestamped local manifest. Bootstrap Notes, human
   decision Entries, recall, false-import rate, and human-time evidence are not
   measured; deferred; not counted.
3. The conformance suite core is implemented and frozen as
   [`suite/FROZEN.md`](suite/FROZEN.md) v6. It is **dormant**: an anchored,
   unexecuted preregistration, not an active gate, and it has never produced a
   score. Its hashes are self-consistent and its identity-contract
   bytes are anchored by commit `145261805d5205d2150dca18c6c42d5a18a628f2`.
   A no-turn preflight verified preparation, then stopped before S3 because
   exact model/prompt identity and two-machine/account isolation were
   unavailable. It produced no score. Held-out S3, paired S1/S2 scores,
   cold-start, conformance, causal, and treatment-advantage evidence are not
   measured; deferred; not counted under the approved closure.

   The optional future automation handoff is specified in
   [`docs/external-evaluation-harness.md`](docs/external-evaluation-harness.md).
   It is a separate project, not AITP scope or a runtime dependency; it cannot
   retroactively satisfy M0.6 or replace the human gate decision.
4. M1a implementation and its deterministic gate are complete; the auditable
   evidence is in [`docs/archive/m1a-stage-notes.md`](docs/archive/m1a-stage-notes.md). The
   current CLI is `init`, `enter`, `inventory`, `record`, `note`, `list`,
   `show`, and `check`; `enter` uses `aitp/enter-0.2`, `list` uses
   `aitp/list-0.1`, `show` uses `aitp/show-0.1`, and `check` is shipped and
   gated with two read-only transports: the no-flag `aitp/check-report-0.1`
   per [`docs/archive/m1b-r1-spec.md`](docs/archive/m1b-r1-spec.md) with its deterministic
   gate **passed** (evidence in [`docs/archive/m1b-r1-stage-notes.md`](docs/archive/m1b-r1-stage-notes.md)),
   and the M1d scoped `aitp/check-report-0.2` (`--workstream <slug>`) per
   [`docs/archive/m1d-workstream-health-spec.md`](docs/archive/m1d-workstream-health-spec.md)
   with its deterministic gate **passed** (evidence in
   [`docs/m1d-stage-notes.md`](docs/m1d-stage-notes.md)).
   [`docs/m1b-spec.md`](docs/m1b-spec.md)
   records the 2026-08-12 reviewed freeze revision; the natural-use pause is
   complete and the M1b-R1 read-side slice is implemented and gated.
   `lineage` is a deferred candidate, absent from the CLI.
5. The natural-use evidence: the first feedback arrived 2026-08-11
   ([`feedback/2026-08-11-gw-librpa-natural-use-feedback.md`](feedback/2026-08-11-gw-librpa-natural-use-feedback.md),
   one long session chain) and the second ordinary session on 2026-08-12
   ([`feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md`](feedback/2026-08-12-power-law-heisenberg-natural-use-feedback.md),
   an independent real-Topic correction session); the researcher's six
   followup suggestions are archived in
   [`feedback/2026-08-12-gw-librpa-followup-feedback.md`](feedback/2026-08-12-gw-librpa-followup-feedback.md).
   The reviewed freeze revision and dispositions are in
   [`docs/archive/m1b-adjudication.md`](docs/archive/m1b-adjudication.md). Neither session is a
   controlled experiment.
6. M1c (Topic workstreams) is **done; deterministic gate passed**: the
   2026-08-13 natural-use feedback
   ([`feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md`](feedback/2026-08-13-gw-librpa-workstreams-natural-use-feedback.md))
   records observable facts from a GW_librpa store that shares
   source/build/provenance across three research lines (crpa,
   magnetic-symmetry, qsgw-semiconductor); the frozen implementation spec
   is [`docs/archive/m1c-workstreams-spec.md`](docs/archive/m1c-workstreams-spec.md)
   (optional `workstreams` list, unscoped legacy visible only in the global
   view, explicit multi-membership, repeatable `--workstream` prepare flag,
   single-slug scoped `aitp/enter-0.3`/`aitp/list-0.2` with global relations
   computed first and strictly scoped projections including handoff, global
   warnings, no registry). M1c is independent of the frozen M1b roster (§0.1
   dispositions unchanged) and of M3; its deterministic gate **passed** and
   the evidence is recorded in [`docs/m1c-stage-notes.md`](docs/m1c-stage-notes.md).

7. M1d (scoped `check` workstream health) is **done; deterministic gate
   passed**: the 2026-08-14 feedback chain — three ordinary real-Topic
   sessions, none of them an AITP gate or a controlled experiment
   ([`feedback/2026-08-14-gw-librpa-natural-use.md`](feedback/2026-08-14-gw-librpa-natural-use.md),
   [`feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md`](feedback/2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md),
   [`feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md`](feedback/2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md))
   drove the frozen implementation spec
   [`docs/archive/m1d-workstream-health-spec.md`](docs/archive/m1d-workstream-health-spec.md)
   (single-occurrence `--workstream <slug>` on `check`; scoped
   `aitp/check-report-0.2` with strict admitted explicit-membership
   attribution, global scan and relations computed first with the scoped
   report a strict subset projection, scoped counts with per-level
   `by_code` and the derived `outside_scope` level delta, exactly four
   human-only scoped text lines, empty scope legal; no flag ⇒
   `aitp/check-report-0.1` byte-unchanged). M1d additively supersedes the
   M1c "`check` has no scope flag" clause for the flag variant only; every
   other M1c clause and all M1b dispositions (§0.1) are unchanged, and M1d
   selects no M1b candidate. Its deterministic gate **passed** and the
   evidence is recorded in [`docs/m1d-stage-notes.md`](docs/m1d-stage-notes.md).
   The same change ships the `using-aitp` Skill guidance (pin/ref
   lifecycle, fail-closed exit-code handling, reviewed manual backfill,
   working-note judgment) and the bundled natural-use feedback template
   (`plugins/aitp-research-protocol/skills/using-aitp/natural-use-session-template.md`).

8. The 2026-08-15 reviewed Skill-only slice ships as **0.6.0** — no behavioral
   runtime/CLI/schema change; version strings synchronized (runtime stays at
   1,543 nonblank lines; every M1b/M1c/M1d contract is unchanged). The natural-use
   feedback ([`feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md`](feedback/2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md))
   records observable facts from a two-workspace session: the two-store
   handoff tidying cost, the researcher's refusal of future manual tidying,
   and the request to study the `quantum.harness` reference repo — no
   controlled comparison, no superiority claim. The slice adds:
   automatic **session-boundary current-state maintenance** in `using-aitp`
   (session start: `enter`/`check`, evidence review, method-card retrieval
   via the generic marker search `rg "^> method-card:"`; session end:
   agent-authority closeout/working-Note upkeep superseding stale records,
   **no-delta zero-write**, pre/post `check`/`enter` verification — the agent
   maintains, never the researcher); a new implicit meta-Skill
   **`distilling-methods`** (draft a method-card theory Note automatically
   only on trigger — explicit request, or a stable procedure across ≥ 2
   sessions, or the same failure twice with the same workaround; trial
   Entries pin the exact card; revisions supersede; **two pinned trials**
   then a publication **proposal**; a human `decision` Entry pinning the
   card is the approval gate; an explicit later human publish request is the
   publication gate — never auto-publish, never cross-Topic propagate, never
   infer workstreams, never resolve failures on a card's authority, no
   Python summarization). Method cards reuse the existing `mode: theory`
   Note profile (title `Method card: <slug>`, body-first-line marker
   `> method-card: <slug>`, fixed six theory headings) — no new schema,
   mode, or review state; cards inform, Skills route, and there is no card
   registry or INDEX. The design record is
   [`docs/method-cards-and-distillation.md`](docs/method-cards-and-distillation.md)
   (quantum.harness scale and adopt/adapt/reject evidence; the reference
   repo's cards are predominantly human-curated, not auto-distilled).
   A same-day follow-up from
   [`feedback/2026-08-15-gw-librpa-natural-use.md`](feedback/2026-08-15-gw-librpa-natural-use.md)
   stays Skill/template-only: `record`/`note` prepare prompts show the
   required `target`/`at` ref shape, and `using-aitp` adds
   evidence-lifecycle pin choice, pointer-manifest immutability, old-pin
   drift interpretation, `malformed`-vs-warning terminology, and
   session-start handoff/goal checks. No runtime/CLI/schema changed.

9. **M1e (evidence lifecycle + reviewed backfill)** ships as **0.7.0** and
   is a runtime stage slice, not a Skill-only change. It adds
   `sha256-once:` mutable-observation pins; optional
   `.aitp/local/check-policy.json` reviewed mutable-path policy for legacy
   strict pins; and `aitp backfill workstreams` with a dry-run default and a
   mandatory human decision Entry that sha256-pins the mapping. No policy
   file means check remains byte-unchanged. The frozen spec is
   [`docs/archive/m1e-evidence-lifecycle-backfill-spec.md`](docs/archive/m1e-evidence-lifecycle-backfill-spec.md)
   and gate evidence is [`docs/m1e-stage-notes.md`](docs/m1e-stage-notes.md).

### Simplicity ratchet and implementation order

The binding evidence-before-complexity ratchet, gate order, fixed-cap rule,
natural-use pause, exhaustive A–H disposition process, and no-runtime/M2 rule
are normative in [`docs/roadmap.md` §Simplicity and stage authorization](docs/roadmap.md#simplicity-and-stage-authorization)
and [`docs/m1b-spec.md` §0.1](docs/m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions).
In brief: M1a is done with its deterministic gate passed; the two-session
ordinary natural-use pause is complete (2026-08-11 GW session chain +
2026-08-12 Power-law Heisenberg session); the 2026-08-12 reviewed freeze
revision selected the read-side slice M1b-R1 (`aitp check` v0.1-only +
compact `enter` text), implemented per `docs/archive/m1b-r1-spec.md` with its
deterministic gate passed (evidence in `docs/archive/m1b-r1-stage-notes.md`).
M1c (Topic workstreams) and M1d (scoped `check`) are done with their
deterministic gates passed. The 2026-08-15 reviewed Skill-only slice (0.6.0:
automatic session-boundary maintenance + method-card distillation) is shipped
with **no behavioral runtime/CLI/schema change; version strings synchronized**
— no new stage, no stage flip. M2/M3 remain
design options.

### README maintenance contract

This README is the public roadmap and current-state entry point. Any change
that alters stage status, roadmap scope, CLI surface, gate evidence, spec
paths, runtime budgets, installation, or user-facing operation must update the
corresponding README sections in the **same change**. `docs/roadmap.md` remains
the normative detailed plan; README maintenance must never be deferred to a
later session.

Multi-user synchronization, permissions, and remote federation are off the
roadmap. For the default single-researcher, non-adversarial model, Git and
author/reviewer provenance are sufficient until a concrete collaboration
failure disproves it.

## Complexity budget

AITP must remain a protocol with a small deterministic tool, not grow into an
agent framework.

- Keep one canonical copy of runtime source. Plugin packaging must not create a
  second hand-maintained implementation.
- Keep each Python module below 400 nonblank lines. Split by stable
  responsibility, not by abstract framework layers.
- Freeze the M0 command surface: `init`, `enter`, `record`, and `note`.
  Later commands are additive and must not weaken these contracts.
- Cumulative runtime budget: stage-end caps in `docs/roadmap.md`; about
  2,000 lines total maximum. M0.5 must deduplicate without net growth.
- Python may parse, validate, persist, project, and benchmark records. Physical
  reasoning, synthesis, literature judgment, and collaboration policy belong in
  Skills and reviewed artifacts.
- Default to no index: `rg` over Markdown is the query path. Add a derived
  cache only if a reproducible realistic benchmark demonstrates the need, and
  only as a disposable artifact.
- Do not add a required database, vector service, MCP server, hook, daemon,
  scheduler, event bus, dependency-injection system, or plugin framework.
- Target installed-plugin startup below 250 ms for `--help` and below one
  second for `enter` on a 1,000-Entry fixture.
- A new feature must include a measured use case, an acceptance test, and its
  effect on code size and startup time.
- Agent behavior conformance is measured by an external suite, never enforced
  by the runtime.

If a milestone cannot fit these constraints, reduce its scope before expanding
the runtime.

## Current state

M0 (Evidence Ledger) and M0.5 (slim core) are done. M0.6 (adopt and
bootstrap) is **done under the approved narrowed reviewed claim**: `init
--adopt` and `inventory` are implemented, while the original bootstrap and
scored-suite evidence is not measured; deferred; not counted. FROZEN v6 remains
an anchored, unexecuted preregistration. M1a is **done; deterministic gate
passed**; its auditable evidence is in [`docs/archive/m1a-stage-notes.md`](docs/archive/m1a-stage-notes.md).
M1b is **done; deterministic gate passed (M1b-R1)**: the natural-use pause is
complete, the 2026-08-12 reviewed freeze revision selected the read-side
slice M1b-R1, implemented per `docs/archive/m1b-r1-spec.md`, and its deterministic
gate passed — auditable evidence in
[`docs/archive/m1b-r1-stage-notes.md`](docs/archive/m1b-r1-stage-notes.md)
(`docs/archive/m1b-adjudication.md`, `docs/archive/m1b-r1-spec.md`). Total M1b denotes only
that this selected slice completed; all other roster rows keep their
dispositions (B, C–E, Followup 2 `lineage`, Followup 6 deferred; F → M4;
G independent; H dropped).
M1c (Topic workstreams) is **done; deterministic gate passed** per the
frozen spec
[`docs/archive/m1c-workstreams-spec.md`](docs/archive/m1c-workstreams-spec.md):
optional explicit `workstreams` membership on Entries/Notes (unscoped legacy
visible only in the global view), repeatable `--workstream` prepare flag
(duplicates rejected), and single-slug scoped
`enter`/`list` (`aitp/enter-0.3`/`aitp/list-0.2`, no flag ⇒ old schemas
byte-unchanged) with global relations computed first and strictly scoped
projections including handoff; global warnings; no
registry. The deterministic gate passed and the evidence is recorded in
[`docs/m1c-stage-notes.md`](docs/m1c-stage-notes.md).
M1d (scoped `check` workstream health) is **done; deterministic gate
passed** per the frozen spec
[`docs/archive/m1d-workstream-health-spec.md`](docs/archive/m1d-workstream-health-spec.md):
the single-occurrence `--workstream <slug>` flag on `check` emits the
scoped `aitp/check-report-0.2` — strict admitted explicit-membership
attribution (malformed, duplicate-ID, unscoped, out-of-scope, and `TOPIC.md`
findings are never scoped), whole-store scan and global relations computed
first with the scoped report a strict subset projection, scoped counts with
per-level `by_code` and the derived `outside_scope` level delta (never a
finding, never affecting `status`/exit), exactly four human-only scoped
text lines, and empty scope legal (exit 0). Without the flag every `check`
surface is byte-unchanged `aitp/check-report-0.1`. The deterministic gate
passed and the evidence is recorded in
[`docs/m1d-stage-notes.md`](docs/m1d-stage-notes.md).
The 2026-08-15 **0.6.0** release is a Skill/template slice, not a roadmap stage:
it adds automatic session-boundary current-state maintenance and method-card
distillation through Skills and documentation only, and the same-day
GW/LibRPA feedback adds prepare-template ref hints plus pin-lifecycle and
pointer-immutability guidance. It changes **no** CLI
command, flag, file schema, transport schema, exit code, or runtime line —
the installed skills drive the same `init`/`enter`/`record`/`note`/`list`/
`show`/`check` surface. Session start runs `enter`/`check`, reviews the
evidence, and retrieves method cards by marker; session end keeps the ledger
current automatically (agent-authority closeout/working Note, superseding
stale records; **no-delta zero-write**; post-save verification), and stable
repeated procedures may be distilled into method-card theory Notes through
the human-gated chain in `distilling-methods` (draft → trial → revision →
proposal → human approval → explicit publication). See
[`docs/method-cards-and-distillation.md`](docs/method-cards-and-distillation.md).

Implemented command groups (the complete current CLI surface):

```text
aitp init [--adopt]
aitp enter [--workstream <slug>]          # M1c: scoped enter-0.3 with flag
aitp inventory <path> --name <name>
aitp record prepare ... [--workstream <slug>]... -> aitp record save <draft>   # M1c: repeatable prepare flag
aitp note prepare ... [--workstream <slug>]... -> aitp note save <draft>       # M1c: repeatable prepare flag
aitp list [--workstream <slug>]           # M1c: scoped list-0.2 with flag
aitp show <entry-id>
aitp check [--workstream <slug>]  # M1d: scoped check-report-0.2 with flag; no flag ⇒ 0.1 byte-unchanged
aitp backfill workstreams --mapping <path> --decision <entry-id> [--apply]  # M1e
```

`enter`, `list`, and `show` expose the versioned read contracts
`aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`; the M1c scoped
variants `aitp/enter-0.3` and `aitp/list-0.2` are emitted **only when the
single-occurrence `--workstream <slug>` flag is passed** (shipped;
deterministic gate passed). `check` is the
read-only store-health command with two read-only transports — the no-flag
`aitp/check-report-0.1` (byte-unchanged; the M1b-R1 baseline, shipped
per `docs/archive/m1b-r1-spec.md` with its deterministic gate passed,
evidence in `docs/archive/m1b-r1-stage-notes.md`) and the M1d single-slug
scoped `aitp/check-report-0.2` (`--workstream <slug>`, shipped;
deterministic gate passed, evidence in `docs/m1d-stage-notes.md`) — while
the diagnosed file schemas remain the shipped v0.1 ones
(`aitp/lite-entry-0.1`/`aitp/lite-note-0.1`). Both modes: exit 0 clean /
1 findings / 2 cannot run or misuse; read-only, zero-write. `lineage` is a
deferred candidate and is absent from the CLI — it may return only through
a new reviewed freeze revision.

### Scoped health checks (`check --workstream`)

`check` always scans the whole store once and computes the global report
exactly as a no-flag run; the flag restricts only the report. A finding is
scoped only when its path is an **admitted** record (parse and structure
passed, and the ID was unique) whose frontmatter `workstreams` explicitly
lists the slug — strict exact membership, never inferred: malformed,
duplicate-ID, unscoped, out-of-scope, and `TOPIC.md` findings are never
attributed to any scope. Relations validate against the global `entry_map`
first, so an in-scope resolver may target an out-of-scope record without a
finding, and the scoped `findings` list is the globally sorted list
restricted to in-scope paths — same levels, codes, messages, and order.

```text
# whole store (no flag): `aitp/check-report-0.1`; one line per finding, then the summary
aitp check
warning[empty_topic_goal]: .aitp/topic/TOPIC.md: Research Goal is not established
check: 0 error(s), 1 warning(s)

# scoped: exactly four text lines, always — details live in --json
aitp check --workstream crpa
workstream: crpa
check: 1 error(s), 1 warning(s)
by_code: {"hash_mismatch": {"errors": 1, "warnings": 0}, "invalid_timestamp": {"errors": 0, "warnings": 1}}
outside_scope: 3 error(s), 1 warning(s) (run "aitp check" for the whole store)

# empty scope: a legacy store whose records carry no `workstreams` is in no scope
aitp check --workstream crpa
workstream: crpa
check: 0 error(s), 0 warning(s)
by_code: {}
outside_scope: 0 error(s), 1 warning(s) (run "aitp check" for the whole store)
```

`aitp check --workstream <slug> --json` emits `aitp/check-report-0.2`: the
complete 0.1 payload plus one additive top-level `workstream` key and two
additive `counts` keys — `by_code` (per-level tally `code → {"errors": n,
"warnings": m}` over the scoped findings, keys sorted by code, always
present) and `outside_scope` (global totals minus scoped totals, per level;
a pure level delta that never appears in `findings` and never affects
`status` or the exit code). Scoped `counts.entries`/`counts.notes` count
**admitted in-scope** records. Without the flag every surface is
byte-unchanged `aitp/check-report-0.1`.

Read the empty scope correctly: a well-formed slug with no admitted
in-scope records is a valid scope — counts 0, `by_code: {}`, status
`clean`, exit 0. Records without a `workstreams` field are in **no** scope,
so on a legacy store every scoped run is empty and a scoped `clean`/exit 0
means **nothing is attributable, not health**; scoped health is meaningful
only once records explicitly carry `workstreams` (new scoped records, or a
reviewed manual backfill — the runtime never backfills). A scoped `clean`
is never a whole-store health certificate: the no-flag run remains the
whole-store instrument, and `outside_scope` keeps the global remainder
visible. In scripts, exit 2 means the store state is unknown — capture the
exit code and fail closed (the `using-aitp` Skill shows the pattern).

The Hakimi integration handoff baseline (compatibility matrix, versioned
envelope decisions, red lines, phased H0/H1/H2 plan) lives in
[`docs/hakimi/`](docs/hakimi/README.md).

### Cross-harness adapter sync (Hakimi + DeepSeek Harness)

AITP owns the CLI, Skills, and the machine-readable adapter surface
`plugins/aitp-research-protocol/aitp.contract.json`; Hakimi and the dsh
AITP mode consume that surface and must not fork AITP semantics. Before
closing any AITP development change that alters the CLI surface, a
transport schema, a model-facing tool description, or a Skill surface,
confirm the two external adapters in the same change:

1. Update `aitp.contract.json` and run
   `pytest tests/ledger/test_adapter_contract.py`; an out-of-date contract
   must fail CI, never be repaired later.
2. Hakimi: update `docs/hakimi/` (README and compatibility matrix) and
   confirm its adapter loads the new contract version or fails closed on an
   unknown schema — never silently falls back to an old command surface.
3. DeepSeek Harness: confirm the dsh AITP mode (the external
   `anchored-aitp` preset, see [`docs/dsh-adapters.md`](docs/dsh-adapters.md))
   still builds its `aitp_*` tools from `aitp.contract.json`, reads Skills
   from the AITP checkout, and passes its preflight (`contractSchema`,
   `contractSha256`, launcher hash) and smoke tests.
4. Record the exact AITP commit, contract sha256, launcher sha256, and
   delivered Skill hashes with the run; a run may not silently mix an old
   adapter with a new AITP surface.

Additive, contract-described changes propagate to both adapters on their
next load. Breaking or semantic changes require an explicitly reviewed
adapter revision in the same change, per the Hakimi compatibility matrix
and the external evaluation-harness contract.


Properties:

- Markdown and filesystem are canonical;
- no database, vector service, MCP server, hook, or daemon is required;
- the Codex plugin bundles `$aitp`, `$using-aitp` (pin/ref/exit-code,
  evidence-lifecycle and pointer-immutability guidance, `sha256-once` and
  check-policy rules, reviewed `backfill workstreams`, automatic
  session-boundary maintenance, session-start handoff/goal checks, and the
  bundled natural-use feedback template), and the implicit
  `$distilling-methods` meta-Skill (method-card distillation with human
  publication gates);
- the M0 ledger contracts have been exercised against a real theoretical-physics workspace;
- all current tests pass.

The master plan is [docs/roadmap.md](docs/roadmap.md).

## Branch policy

```text
main            stable integrated protocol, roadmap, and released capabilities
ledger-core     immutable M0 ledger baseline
slim-core       M0.5 runtime simplification; gate passed, kept as a historical baseline
research-graph  archived; superseded by the M3 cross-topic-links design
```

The former repository implementation is retained separately as `legacy/v5-final` during repository cutover. Old authority and experimental branches are archival evidence, not active product lines.

Feature branches should be short-lived. Stable milestones land on `main`; permanent branches exist only for explicit historical baselines.

## Repository layout

```text
.agents/plugins/                                        local Codex marketplace
docs/                                                   concise active designs
plugins/aitp-research-protocol/                         installable Codex plugin
plugins/aitp-research-protocol/aitp.contract.json       machine-readable Hakimi/dsh adapter surface
plugins/aitp-research-protocol/scripts/vendor/aitp/     canonical single runtime
tests/ledger/                                           ledger and plugin contracts
```

The repository contains no compatibility runtime for former implementations.

## Use the current ledger

The same bundle under `plugins/aitp-research-protocol/` installs on both
supported agent platforms (CLI + per-platform manifest; no MCP, hooks, or
daemon).

Install the local Codex plugin:

```bash
codex plugin marketplace add /absolute/path/to/AITP-Research-Protocol
codex plugin add aitp-research-protocol@aitp-protocol
```

Start a new Codex session and invoke:

```text
$aitp
```

Use `/skills` to inspect installed Skills. `$aitp` is a Skill invocation; `/aitp` is not a Codex slash command.

Install the same bundle in Kimi Code:

```text
/plugins install /absolute/path/to/AITP-Research-Protocol/plugins/aitp-research-protocol
/reload
```

Kimi Code runs from its managed copy (`~/.kimi-code/plugins/managed/`), so
re-run the install after the bundle changes. Invoke with `/skill:aitp`.

Since 0.6.0 the installed Skills maintain the ledger automatically at session
boundaries (enter/check + evidence review + method-card retrieval at start;
closeout/working-Note upkeep with no-delta zero-write at end) and may draft
method-card theory Notes for stable repeated procedures. No extra commands are
needed — every write goes through the existing `record`/`note` prepare/save
path, publication stays human-gated, and nothing runs in the background
(no daemon, hook, or MCP).

For standalone development:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pytest -q
```

## Invariants

- Evidence before abstraction.
- Append history; do not silently rewrite it.
- Preserve provenance through every derived layer.
- Distinguish fact, decision, interpretation, and hypothesis.
- Keep local files readable without AITP.
- Make indexes disposable and rebuildable.
- Require explicit human gates for publication and sharing.
- Add complexity only after a real research workflow demonstrates the need.

## What AITP is not

- not a transcript archive;
- not a vector database presented as memory;
- not an autonomous scientific authority;
- not a general-purpose team permissions or synchronization platform;
- not a replacement for Git, notebooks, papers, or human review;
- not a reason to record every conversational detail.

AITP succeeds when it helps humans and agents think together over time while making it easier—not harder—to inspect why they believe something.
