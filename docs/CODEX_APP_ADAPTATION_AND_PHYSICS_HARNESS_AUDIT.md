# Codex App Adaptation And Physics Harness Audit

Date: 2026-05-14

Scope: AITP top-level protocol, runtime/adapter surfaces, each L0-L4/H/B
harness layer, and practical fit against real theoretical-physics research
workflow.

This review is deliberately strict. AITP's protocol idea is strong, but the
current checkout is not yet a reliable "fresh clone, install, do physics"
system. The main gap is not the Charter; it is the mismatch between protocol
claims, adapter documentation, package/runtime availability, and the actual
test/harness state.

## Executive Verdict

AITP has the right top-level research architecture:

- evidence must be separated from conjecture,
- important research steps must leave durable artifacts,
- reusable knowledge must be promoted only after validation,
- adapters must execute the protocol rather than redefine it.

From a theoretical physicist's perspective, that is the right spine. It mirrors
how serious theory work actually proceeds: source acquisition, notation
normalization, derivation, internal critique, limit checks, numerical or
experimental comparison when relevant, and only then reuse.

The implementation is behind the protocol:

- Codex app was documented as installable, but the PM script did not support
  Codex before this patch.
- The advertised `aitp-kernel` / `knowledge_hub` package source is absent from
  this checkout.
- The full test suite is still red after localized repairs: `52 failed, 133
  passed`.
- L0/L1/L3 transition tests still show state/gate mismatches.
- L2 graph query/visualization still appears to mix legacy graph nodes with
  entry-derived projections.
- Adapter conformance is declared but not hard-checked at session end.

The practical conclusion: treat AITP today as a promising protocol-first
research harness under active construction, not as a mature autonomous
physicist runtime.

## What Was Changed For Codex App

This audit includes a repository-local Codex app adaptation:

- `scripts/aitp-pm.py` now accepts `--agent codex`.
- Codex installs are deployed through Codex-specific skill roots:
  - `%USERPROFILE%/.codex/skills`
  - `%USERPROFILE%/.codex-home/skills`
  - `%USERPROFILE%/.codex-switcher/skills`
- New Codex-native gateway skills were added:
  - `deploy/codex/skills/using-aitp.md`
  - `deploy/codex/skills/aitp-runtime.md`
- Protocol skills from `skills/` are wrapped at deploy time with a Codex
  adapter preamble that maps Claude/Kimi-only instructions to Codex behavior.
- A best-effort `mcp.json` is written beside Codex skill roots. When `uv` is
  available, the MCP entry uses `uv run --with pyyaml --with jsonschema --with
  fastmcp ...`, which is safer on machines where `python` is a WindowsApps
  placeholder.
- Codex install docs were rewritten to stop advertising invalid package commands
  for this checkout.

The Codex adaptation is still a skill/MCP adapter, not a full hook-level
integration. Codex app does not currently get the same SessionStart,
UserPromptSubmit, PreToolUse, and Stop enforcement that Claude Code receives
through hooks. That is an important conformance difference.

## Validation Performed

Commands run from repository root:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python -m py_compile scripts/aitp-pm.py brain/cli/decorators.py brain/cli/commands/l2.py brain/mcp_server.py brain/state.py
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --help
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli --help
uv run --with pyyaml --with jsonschema --with fastmcp --with pytest python -m pytest tests/test_study_l2_graph.py::TestL2GraphEdges::test_create_edge tests/test_study_l2_graph.py::TestL2GraphEdges::test_edge_rejects_dangling_nodes tests/test_io_contracts.py::TestL2IOContract::test_create_l2_edge_requires_existing_nodes -q
uv run --with pyyaml --with jsonschema --with fastmcp --with pytest python -m pytest tests -q
```

Results:

- Compile: passed.
- `scripts/aitp-pm.py install --help`: passed; shows
  `--agent {claude-code,kimi-code,codex,all}`.
- `python -m brain.cli --help`: passed.
- Targeted L2 edge tests: `3 passed`.
- Full suite after localized fixes: `52 failed, 133 passed`.

Important baseline issue: before the localized decorator/L2 fixes, the suite
was `73 failed, 112 passed`. The repairs removed a large class of direct
harness-call failures, but did not make the runtime conformant.

## Top-Level Protocol Review

### Strengths

The Charter and SPEC are conceptually strong. The authority hierarchy
`Charter > SPEC > sub-protocols > implementation` is the correct way to prevent
adapter drift. In physics terms, the Charter is the "renormalization condition"
for the entire project: it fixes what counts as legitimate AITP work regardless
of platform.

The default route `L0 -> L1 -> L3 -> L4 -> L2` is also right. It prevents the
most common AI research failure mode: a plausible answer jumps directly from
paper snippets or chat memory into reusable "knowledge" without reconstruction
and adversarial validation.

The removal of L5 is defensible. Publication writing should not be confused
with knowledge validation. A paper can be written from L2/L3/L4 surfaces, but
the protocol endpoint being L2 keeps the knowledge graph, not the manuscript,
as the trusted object.

### Gaps

The top-level spec currently overstates implementation maturity. It describes
runtime kernels and adapter support that are not available in this checkout.
That weakens trust because a new user cannot tell which surfaces are
authoritative and which are historical plans.

The phase model is ambitious but lacks measurable gates beyond a short Phase 3
note. AITP should not claim "learning collaborator" or "autonomous physicist"
progress without explicit metrics: cross-topic reuse success rate, validated
prediction rate, failed-autonomy audit count, and human override rate.

Adapter conformance is still declared rather than enforced. Charter Article 9
says conformance is enforceable; the adapter protocol admits that no adapter
currently hard-checks conformance at session end. That contradiction should be
made visible in quickstart/install docs.

## Brain Plane And Runtime Harness

### Current State

The Brain plane is the correct place for MCP tools, skills, gates, and hooks.
The implementation has useful surfaces: topic bootstrap, source registration,
execution brief, L3 activity switching, L4 review, L2 graph operations, and
visualization.

The root enforcement CLI is runnable under `uv`, but the public package path is
not. `scripts/aitp-local.py doctor` fails because the expected
`research/knowledge-hub/build/lib/knowledge_hub/aitp_cli.py` entrypoint is
missing.

### Repairs Made

The `require_stage` and `with_preflight` decorators now preserve positional
calls by binding against the wrapped function signature and then calling the
original function with `*args, **kwargs`. This matters because many MCP-harness
tests and direct Python calls use positional arguments.

L2 edge creation now rejects missing provenance and dangling endpoints before
dispatching to the CLI. This protects the trusted graph from silent invalid
relations.

### Remaining P0 Problems

The full suite still shows L0/L1/L3 transition failures. A representative E2E
failure registers sources, writes `source_registry.md`, calls
`aitp_advance_to_l1`, then still receives an L0 brief saying
`register at least one source in L0/sources/`. That is a practical harness
failure: the user did the expected work, but the gate cannot see it.

The runtime/package story must be resolved. Either restore the
`research/knowledge-hub/knowledge_hub` package and public CLI entrypoints, or
remove those claims from public docs until they exist.

## Codex App Adapter Review

### What Works Now

Codex has a real repository-local install path:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --agent codex --scope user
```

The Codex gateway skills no longer tell Codex to use Claude-only tools. They
map user questions, AITP MCP calls, and fallback diagnostics into Codex app
behavior.

### Remaining Adapter Risks

Codex app still lacks hard hook enforcement in this repository. The adapter is
therefore softer than Claude Code:

- no guaranteed SessionStart injection,
- no guaranteed PreToolUse guard against manual topic-state editing,
- no Stop hook that enforces chronicle/conformance writeback,
- no verified popup UI bridge.

This means Codex can execute AITP, but a Codex run should not claim full
adapter conformance until session-end checks exist.

### Required Codex Acceptance Test

Add an adapter smoke test that installs into a temporary Codex skill root and
verifies:

- `using-aitp/SKILL.md` exists,
- `aitp-runtime/SKILL.md` exists,
- wrapped protocol skills include the Codex adapter preamble,
- `mcp.json` contains an `aitp` server,
- the generated MCP command is executable under `uv`,
- stale Claude-only gateway instructions are absent from Codex gateway skills.

## L0 Harness Review: Source Substrate

### What Is Right

L0 correctly treats papers, PDFs, URLs, notes, conversations, and code
references as provenance objects rather than truth. That is exactly what a
physicist needs: source registration is not belief; it is a trace of what was
looked at and how reliable it is.

The arXiv-first and source-fidelity stance is good. Theory work often relies
on preprints, but the protocol needs to distinguish peer-reviewed, arXiv,
textbook, code, informal note, and verbal guidance.

### Practical Problems

The current harness still has source-registration/gate mismatch failures in
E2E tests. If registered sources do not satisfy the L0 gate reliably, the
front door is not dependable.

L0 source categories are too paper-centric for modern theory work. Real
projects often depend on:

- parameter databases,
- benchmark datasets,
- lattice/model definitions,
- code commits and exact function ranges,
- experimental tables,
- numerical reference outputs,
- conference slides or private notes with weak authority.

### Optimization

Add source classes for `dataset`, `benchmark_table`, `parameter_set`,
`code_commit`, `notebook`, `experimental_result`, and `private_note`, each
with source-fidelity defaults and required provenance fields.

Add an L0 acceptance test: after registering N sources through MCP, the L0
brief must see exactly those N sources and the gate must become ready once
`source_registry.md` is complete.

## L1 Harness Review: Provisional Understanding

### What Is Right

L1 is one of the strongest conceptual layers. The required artifacts map
closely to real theory practice:

- question contract,
- source basis,
- convention snapshot,
- derivation anchor map,
- contradiction register,
- source TOC/intake.

For theoretical physics, notation and convention snapshots are not optional.
Many wrong derivations are convention collisions: metric signature, Fourier
transform normalization, Green-function sign, Chern-Simons level convention,
normalization of generators, or units.

### Practical Problems

The gate is strict but not yet robust. Tests that fill plausible L1 artifacts
still fail because the runtime thinks the topic remains in L0. The issue may
be path resolution, source visibility, or transition state synchronization.
Whatever the cause, the user-facing result is bad: the protocol blocks a valid
workflow for the wrong reason.

The intake model still treats "reading" as mostly document structure. Real
physics reading needs explicit extraction of:

- definitions and their regimes,
- assumptions and small parameters,
- equations with domain of validity,
- theorem/proposition dependencies,
- known limits,
- regularization choices,
- normalization conventions,
- unresolved contradictions across sources.

### Optimization

Make L1 emit a `formal_objects.md` or structured projection with definitions,
equations, assumptions, known limits, and notation mappings. L3 derivation
should consume that projection rather than rereading prose.

Add a contradiction-resolution harness: two sources with conflicting
conventions should force a convention choice or a regime split before L3.

## L2 Harness Review: Trusted Reusable Knowledge

### What Is Right

L2 as a promoted, reusable graph is the right endpoint. Theory research needs
memory that survives chat compaction and does not silently upgrade conjectures.

Typed nodes and typed edges are also correct. Relations such as `limits_to`,
`derives_from`, `assumes`, `contradicts`, `dual_to`, and `invariant_under`
are physically meaningful, not just generic graph edges.

### Repairs Made

This audit added:

- `known_limit` as an L2 node type.
- L2 edge provenance requirement.
- L2 edge dangling-endpoint rejection.
- CLI L2 node/edge type validation now uses central `brain.state` constants
  instead of a stale hardcoded list.

### Practical Problems

L2 still has a store/projection mismatch. Some tools write legacy graph nodes
under `L2/graph/nodes`, while query/visualization can read entry-derived
projections that classify nodes as generic `claim` or `question`. That is why
tests still show type-filter and icon mismatches.

Provenance is hidden in default query output, which is good for context bloat
but risky for trust. A physicist often needs to audit the exact line, paper,
candidate, or validation result behind a reusable claim. Provenance must be
one command away and visually obvious when trust is weak.

The current trust ladder is not rich enough for numerical evidence. A single
`numerical_evidence` tag does not distinguish:

- exploratory one-off run,
- converged run,
- benchmarked against known case,
- independently reproduced,
- experimentally compared.

### Optimization

Unify the L2 graph source of truth. Pick either entry-first with deterministic
graph projection or graph-first with entry projection, then make every query,
visualization, and promotion path use that one model.

Add numerical evidence tiers:

- `exploratory_numeric`
- `converged_numeric`
- `benchmarked_numeric`
- `independently_reproduced_numeric`
- `experiment_compared`

Add first-class `known_limit` handling: every new approximation/method should
declare which known limits it must reproduce and whether those checks passed.

## L3 Harness Review: Candidate Workspace

### What Is Right

L3 correctly avoids a forced linear sequence. Real research moves among
ideation, planning, derivation, gap auditing, integration, and distillation.
A protocol that forced every topic through the same rigid chain would fail in
actual theory work.

L3 is the right place for failed attempts and negative results. Those are not
trash; they are often the most valuable memory for avoiding repeated mistakes.

### Practical Problems

The current implementation still has L3 transition failures. Tests that expect
L3 to start in `ideate` remain blocked in L1/L0. This is a core workflow
failure, not a cosmetic test issue.

The `connect` activity is inconsistent. Some docs/tests expect it removed;
some skill/runtime surfaces still mention it. This matters because L3 activity
vocabulary is part of the adapter contract.

L3 is too weak for iterative numerical theory. Many real workflows are not a
single derivation:

- DMFT self-consistency,
- GW/BSE convergence,
- variational optimization,
- tensor-network bond-dimension sweeps,
- lattice finite-size scaling,
- exact diagonalization benchmark ladders.

These require round records, convergence criteria, failed runs, parameter
updates, and stopping decisions.

### Optimization

Add an explicit `self_consistency_round` artifact family with:

- round id,
- input parameters,
- output observables,
- residual/error metric,
- convergence threshold,
- update rule,
- failed-run classification,
- decision to continue/stop.

Clarify the L3 activity vocabulary in one central constant and regenerate docs
from it. If `connect` is removed, remove it everywhere; if it remains, define
its artifact and gate semantics.

## L4 Harness Review: Validation And Adjudication

### What Is Right

The L4 concept is essential. A theoretical claim must be attacked before it is
trusted. Current physics checks already include important obligations:

- dimensional consistency,
- symmetry compatibility,
- limiting cases,
- conservation,
- correspondence,
- approximation validity,
- unitarity,
- causality,
- scale separation,
- regularization independence.

These are the right checks for many theory domains.

### Practical Problems

Some tests still expect an older physics-check set, so the suite and protocol
constants are out of sync. The protocol has evolved faster than the regression
tests.

L4 can become checklist-like unless it requires independent reconstruction.
For serious physics, "I checked the limit" is not enough. The artifact should
show the calculation, input assumptions, and failure conditions.

Experimental comparison is under-modeled. Even formal theory often needs
phenomenological checks, known constants, spectra, phase boundaries, or
observable consequences.

### Optimization

Separate L4 checks into:

- analytic checks,
- numerical checks,
- formal/proof checks,
- experimental or benchmark comparison,
- adversarial counterargument.

Require every passed L4 review to include at least one independent route:
re-derive, reproduce numerically, compare to known limit, or compare to source
benchmark. If no independent route exists, the result can be "plausible" but
not "validated".

## H Plane Review: Human Interaction

### What Is Right

Human gates are legitimate. The human is not a protocol failure; in Phase 1,
the human is the research lead.

The popup-gate model is correct for promotion and high-impact decisions.

### Practical Problems

The current skills overfit to Claude's `AskUserQuestion`. Codex cannot follow
that literally. The Codex gateway now fixes this at the entry/runtime level,
but many protocol skills still contain Claude wording and rely on the deploy
preamble to reinterpret it.

### Optimization

Extract human-interaction instructions into a platform-neutral vocabulary:

- `ask_human_choice`
- `ask_human_freeform`
- `require_human_approval`
- `record_human_override`

Adapters can map those to Claude `AskUserQuestion`, Codex plain questions,
OpenCode `question`, or future UI mechanisms.

## Comparison With Real Theoretical-Physics Workflow

### Literature Phase

Real workflow: identify canonical papers, textbooks, recent preprints, and
known controversy. Extract definitions, conventions, and known limits before
deriving.

AITP fit: L0/L1 are well-designed for this.

Missing: richer source classes and a stronger L0 gate.

### Blackboard Derivation Phase

Real workflow: write assumptions, choose conventions, derive step by step,
check dimensions, symmetries, and limiting cases while deriving.

AITP fit: L1 convention snapshot plus L3 derivation plus L4 checks is the
right shape.

Missing: derivation-step objects need stronger equation-level dependency and
known-limit references.

### Numerical/Computational Phase

Real workflow: run small tests first, then convergence, then benchmark, then
production. Record exact parameters, code version, failures, and residuals.

AITP fit: compute targets and L4 numerical hooks exist.

Missing: self-consistency rounds, convergence ledgers, run manifests, and
evidence tiers.

### Internal Seminar Phase

Real workflow: present the result to a skeptical colleague. They attack
assumptions, limits, hidden regularization choices, and overclaims.

AITP fit: L4 adversarial review is correct.

Missing: stronger requirement for independent reconstruction and
counterexample search.

### Knowledge Reuse Phase

Real workflow: only after a result survives scrutiny does it become something
you cite, reuse, or build on.

AITP fit: L2 promotion discipline is excellent.

Missing: L2 graph store unification and provenance audit ergonomics.

## Prioritized Remediation Roadmap

### P0: Make The Harness Trustworthy

1. Restore or remove the public runtime package claims.
2. Make the full test suite green, starting with L0 source registration and
   L1/L3 transition failures.
3. Unify L2 graph storage and query/visualization projections.
4. Add Codex adapter smoke tests.
5. Add session-end conformance checks for every adapter.

### P1: Make It Physics-Strong

1. Add known-limit obligations to L3/L4, not just L2 node typing.
2. Add numerical evidence tiers and convergence ledgers.
3. Add self-consistency round artifacts.
4. Add experimental/benchmark comparison protocol.
5. Add formal-theory backend hooks for Lean/Mathematica/SymPy with explicit
   trust boundaries.

### P2: Make It Usable For Daily Research

1. Create a physicist-facing dashboard: current claim, assumptions, blocking
   checks, next action, and unresolved risks.
2. Add importers for arXiv, BibTeX, PDFs, source code ranges, datasets, and
   benchmark tables.
3. Expand domain skills for QFT, condensed matter, electronic structure,
   quantum information, statistical mechanics, and numerical many-body work.
4. Make provenance reveal easy: every L2 query result should have a one-step
   "show evidence" path.

## Final Assessment

As a protocol for disciplined theoretical-physics work, AITP is directionally
right and unusually serious. Its strongest idea is the separation of source
trace, provisional understanding, candidate work, validation, and reusable
knowledge.

As a current harness, it is not yet strict enough to trust unattended. The
remaining red tests are not incidental; they touch core stage transitions,
L2 graph consistency, and adapter conformance. Fix those before claiming that
AITP is a stable research runtime.

As a Codex app integration, the repository now has a real local adapter path,
but it should be described honestly: skill/MCP based, not hook-complete, and
not yet conformance-verified.
