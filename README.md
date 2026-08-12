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
| M0.6 — Adopt & bootstrap | **done under the approved narrowed reviewed claim** | Deterministic `init --adopt`/`inventory` implementation and anchored, unexecuted FROZEN v6 packet; no bootstrap-validation or plain-files advantage claim | Narrowed gate review accepted; original bootstrap Notes/decisions, recall/false-import/human-time, held-out S3, paired S1/S2, cold-start, conformance, causal, and treatment-advantage evidence is not measured; deferred; not counted |
| M1a — Memory that restores | **done; deterministic gate passed** | Versioned `list`, `show`, closeout-first `enter` v2, Note-age structural signal, generated public-schema goldens, deterministic S1/S2 regression, read-only GW_librpa acceptance | Deterministic gate passed; this is not a behavioral or treatment-superiority gate. Evidence: [`docs/m1a-stage-notes.md`](docs/m1a-stage-notes.md) |
| M1b — Open items & behavior pilot | **done; deterministic gate passed (M1b-R1)** | Authoritative A–H + Followup roster in `docs/m1b-spec.md` §0.1 and the adjudication in `docs/m1b-adjudication.md`: A and Followups 1/3/4/5 selected in M1b-R1 (`check` v0.1-only + compact `enter` text), implemented per `docs/m1b-r1-spec.md`; B, C–E, Followup 2 (`lineage`), Followup 6 (structured prepare) deferred; F moved to M4 Skill-only; G independent; H dropped. Total M1b denotes only the selected R1 slice | R1 deterministic gate passed (independent review with no S0/S1/S2 blockers; 78 tests; benchmark final PASS; 1,423-line runtime within the 1,425 target and 1,450 cap; goldens; S1/S2 regression; read-only byte-identical real-store acceptance; same-day precision-fix amendment superseding the pre-amendment 77-test/1,421-line run) — evidence in [`docs/m1b-r1-stage-notes.md`](docs/m1b-r1-stage-notes.md). Not a behavioral or treatment-superiority gate; `lineage` is a deferred candidate |
| M2 — Reviewed artifacts | design option; blocked | Optional Knowledge, Skill, Insight, Hypothesis artifacts with hash-bound human review | A no-runtime M1b decision does not authorize M2; its own natural-demand review must show Entries/Notes are inadequate before the reviewed-artifact gate |
| M3 — Cross-topic links | design option; blocked | Optional catalog plus explicit links; `rg` discovery, no index | Natural cross-Topic use shows `rg` plus ordinary citations are inadequate, then human-confirmed links answer a real question with provenance |
| M4 — Collaborator protocol | blocked design option; Skill-only | Long-horizon question → hypothesis → prediction → test loop | M1b pilot evidence only if that pilot is selected; otherwise M4's own natural-demand and prospective-evidence adjudication passes vs. the plain-files baseline |

The 2026-08-10 M0.6 gate-review decision is applied in
[`docs/m0.6-gate-review.md`](docs/m0.6-gate-review.md): M0.6 is closed only under
the approved narrowed reviewed claim. M1a is now **done; deterministic gate
passed**; see [`docs/m1a-stage-notes.md`](docs/m1a-stage-notes.md). This is not a
behavioral or treatment-superiority gate. The original empirical M0.6 conditions
remain not measured, deferred, and not counted.

### Current checkpoint

M1a is done. The two-session ordinary natural-use pause is **complete**, the
M1b reviewed freeze revision is recorded, and the selected M1b-R1 read-side
slice is implemented per [`docs/m1b-r1-spec.md`](docs/m1b-r1-spec.md) with
its **deterministic gate passed** (evidence in
[`docs/m1b-r1-stage-notes.md`](docs/m1b-r1-stage-notes.md)):

1. `aitp init --adopt` is implemented and tested, and has been exercised on
   real trees; preserved operator before/after hash evidence is incomplete per
   [`docs/m0.6-gate-review.md`](docs/m0.6-gate-review.md). This is a documented
   real-tree evidence gap, not a claim of complete bootstrap validation.
2. `aitp inventory` is implemented with deterministic traversal, ordering, and
   content hashing in a timestamped local manifest. Bootstrap Notes, human
   decision Entries, recall, false-import rate, and human-time evidence are not
   measured; deferred; not counted.
3. The conformance suite core is implemented and frozen as
   [`suite/FROZEN.md`](suite/FROZEN.md) v6. It is an anchored, unexecuted
   preregistration: its hashes are self-consistent and its identity-contract
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
   evidence is in [`docs/m1a-stage-notes.md`](docs/m1a-stage-notes.md). The
   current CLI is `init`, `enter`, `inventory`, `record`, `note`, `list`,
   `show`, and `check`; `enter` uses `aitp/enter-0.2`, `list` uses
   `aitp/list-0.1`, `show` uses `aitp/show-0.1`, and `check` (schema
   `aitp/check-report-0.1`) is shipped and gated per
   [`docs/m1b-r1-spec.md`](docs/m1b-r1-spec.md) with its deterministic gate
   **passed** (evidence in [`docs/m1b-r1-stage-notes.md`](docs/m1b-r1-stage-notes.md)).
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
   [`docs/m1b-adjudication.md`](docs/m1b-adjudication.md). Neither session is a
   controlled experiment.

### Simplicity ratchet and implementation order

The binding evidence-before-complexity ratchet, gate order, fixed-cap rule,
natural-use pause, exhaustive A–H disposition process, and no-runtime/M2 rule
are normative in [`docs/roadmap.md` §Simplicity and stage authorization](docs/roadmap.md#simplicity-and-stage-authorization)
and [`docs/m1b-spec.md` §0.1](docs/m1b-spec.md#01-authoritative-candidate-roster-and-current-dispositions).
In brief: M1a is done with its deterministic gate passed; the two-session
ordinary natural-use pause is complete (2026-08-11 GW session chain +
2026-08-12 Power-law Heisenberg session); the 2026-08-12 reviewed freeze
revision selected the read-side slice M1b-R1 (`aitp check` v0.1-only +
compact `enter` text), implemented per `docs/m1b-r1-spec.md` with its
deterministic gate passed (evidence in `docs/m1b-r1-stage-notes.md`).
M2/M3 remain design options.

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
passed**; its auditable evidence is in [`docs/m1a-stage-notes.md`](docs/m1a-stage-notes.md).
M1b is **done; deterministic gate passed (M1b-R1)**: the natural-use pause is
complete, the 2026-08-12 reviewed freeze revision selected the read-side
slice M1b-R1, implemented per `docs/m1b-r1-spec.md`, and its deterministic
gate passed — auditable evidence in
[`docs/m1b-r1-stage-notes.md`](docs/m1b-r1-stage-notes.md)
(`docs/m1b-adjudication.md`, `docs/m1b-r1-spec.md`). Total M1b denotes only
that this selected slice completed; all other roster rows keep their
dispositions (B, C–E, Followup 2 `lineage`, Followup 6 deferred; F → M4;
G independent; H dropped).

Implemented command groups (the complete current CLI surface):

```text
aitp init [--adopt]
aitp enter
aitp inventory <path> --name <name>
aitp record prepare|save
aitp note prepare|save
aitp list
aitp show <entry-id>
aitp check            # M1b-R1: shipped; deterministic gate passed
```

`enter`, `list`, and `show` expose the versioned read contracts
`aitp/enter-0.2`, `aitp/list-0.1`, and `aitp/show-0.1`. `check` is the
M1b-R1 read-only store-health command (schema `aitp/check-report-0.1`,
exit 0 clean / 1 findings / 2 cannot run; read-only, zero-write), shipped
per `docs/m1b-r1-spec.md` with its deterministic gate passed (evidence in
`docs/m1b-r1-stage-notes.md`); `lineage` is a deferred candidate and is
absent from the CLI — it may return only through a new reviewed freeze
revision.

The Hakimi integration handoff baseline (compatibility matrix, versioned
envelope decisions, red lines, phased H0/H1/H2 plan) lives in
[`docs/hakimi/`](docs/hakimi/README.md).

Properties:

- Markdown and filesystem are canonical;
- no database, vector service, MCP server, hook, or daemon is required;
- the Codex plugin bundles `$aitp` and `$using-aitp`;
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
