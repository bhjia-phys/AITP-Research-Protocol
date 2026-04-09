# AITP Task-Type, Layer Responsibility, And H-Plane Freeze Design

Status: working design freeze

Date: 2026-04-08

## Goal

Freeze the top-level AITP collaborator framework around real theoretical
physics research practice rather than only around protocol cleanliness.

This document defines:

- the top-level task types AITP must support,
- the lane families AITP must support,
- the frozen responsibility matrix for `L0/L1/L3/L4/L2/runtime`,
- the internal subdivision of the overloaded current `L3`,
- the human interaction plane that can intervene across the whole research
  graph,
- the mandatory movement law over the layer graph,
- the distinction between domain memory and collaborator memory,
- and the roadmap consequences for the current milestone plan.

Short form:

- classify the research job correctly,
- keep `L0-L4` as epistemic layers,
- split `L3` internally instead of overloading it,
- treat `Human` as a cross-cutting plane rather than a normal layer,
- and let `L2` grow as a compiled research brain instead of a raw retrieval
  store.

## Why This Freeze Is Needed

The current design stack is already strong on:

- layer discipline,
- lane and transition semantics,
- paired backend doctrine,
- progressive runtime disclosure,
- and the emerging `L2` governance plane.

But it still risks building a system that is:

- excellent at exposing protocol state,
- good at bounded runtime control,
- and still weaker than a real theoretical-physics collaborator at:
  - open-ended research exploration,
  - conjecture refinement,
  - implementation-driven algorithm work,
  - canonical literature learning,
  - and long-horizon reusable scientific memory.

The missing step is a freeze of the whole collaborator frame:

- what kinds of research AITP is actually for,
- what each layer is responsible for,
- what movement through the graph is mandatory,
- where human interaction belongs,
- and how reusable memory grows without replacing fresh work.

## Core Decision

AITP is frozen as eight orthogonal structures:

1. `task_type`
2. `lane`
3. `layer`
4. `mode`
5. `transition`
6. `H-plane`
7. `knowledge_trust_surface`
8. `knowledge_realization`

Short form:

- task type = what kind of research job is this?
- lane = what broad research direction and evidence base dominates?
- layer = what epistemic object is this right now?
- mode = how should AITP operate for this step?
- transition = how is it moving over the layer graph?
- H-plane = where and how humans can intervene or receive results
- trust surface = canonical vs compiled vs staging in `L2`
- realization = human-readable vs typed downstream realization

`L3` remains a top-level layer, but it is now frozen as an umbrella layer with
three internal subplanes.

## Task-Type Axis

The top-level task types are now:

- `open_exploration`
- `conjecture_attempt`
- `target_driven_execution`

These are not cosmetic tags.
They change:

- how broad `L0` source gathering should be,
- how `L1` should read,
- how much `L3` should compare routes versus harden one route,
- what kind of `L4` checks are expected,
- and what sort of `L2` memory object is likely to emerge.

### `open_exploration`

Use when:

- the user wants free exploration or high-level structural discussion,
- the initial object is under-bounded,
- or the job is to search the nearby research space honestly.

Primary behavior:

- broad `L0`,
- comparative `L1`,
- route-heavy `L3`,
- and `L4` often yields partial or blocking outcomes.

### `conjecture_attempt`

Use when:

- the user has a real but not yet closed conjectural bridge,
- the question can be sharpened into candidate objects,
- and the main job is to turn suspicion into a checked research candidate.

Primary behavior:

- tighter `L1`,
- explicit bridge and route comparison in `L3`,
- and `L4` is expected to try meaningful checks rather than only survey.

### `target_driven_execution`

Use when:

- the user has a concrete goal,
- the route is partially known,
- and the main question is whether AITP can execute, derive, implement, or
  validate that target honestly.

Examples:

- implement finite-temperature GW inside LibRPA,
- derive a specific theorem-family closure target,
- or verify a concrete numerical/materials workflow.

Primary behavior:

- narrower `L0`,
- highly technical `L1`,
- route-hardening in `L3`,
- and a heavy `L4` burden.

## Lane Axis

The main lane families are now frozen as:

- `formal_theory`
- `model_numeric`
- `code_and_materials`

### `formal_theory`

Use for:

- derivation-heavy,
- proof-like,
- algebraic,
- and conceptually formal theoretical work.

### `model_numeric`

Use for:

- reduced models,
- toy Hamiltonians,
- tractable benchmark systems,
- and numerically aided physical-property checks.

### `code_and_materials`

Use for:

- large codebase algorithm implementation,
- scientific software modification,
- backend-heavy workflow validation,
- and actual-material computation flows.

This lane is intentionally broad at the top level.
Later milestones may refine it internally into algorithm-implementation versus
production-materials subtracks, but the frozen framework keeps one combined lane
for now because both share a code-and-artifact-heavy validation structure.

## Why Task Type And Lane Are Separate

This distinction is mandatory.

The same lane can appear under different task types:

- `open_exploration × formal_theory`
- `conjecture_attempt × model_numeric`
- `target_driven_execution × code_and_materials`

Likewise, the same task type can traverse different lanes.

Without this separation:

- literature learning and target execution get mixed,
- open exploration gets treated like a proof task,
- or code implementation gets mistaken for a mere reading problem.

## Primary Research Scenarios

The framework must satisfy at least the following two canonical scenarios.

### Scenario A: Idea-Driven Open Research

Example:

- whether measurement-induced phase transitions might connect structurally to
  background-independent algebraic formulations of quantum gravity.

Expected frame:

- task type begins as `open_exploration` or `conjecture_attempt`,
- lane may move across `formal_theory` and `model_numeric`,
- and the route must stay backedge-friendly.

Required flow:

1. start from `L0`,
2. gather literature and other sources with real tools,
3. read them carefully in `L1`,
4. combine them with the user's idea in `L3-A`,
5. consult `L2` as an active brain,
6. run theory or numerical checks in `L4`,
7. return to earlier layers whenever the blocker lives there,
8. route `L4` output through `L3-R`,
9. decide in `L3-D` what is actually reusable,
10. and only then write to `L2`.

### Scenario B: Canonical Literature Learning

Expected frame:

- task type is usually `target_driven_execution` or a tightly bounded
  `conjecture_attempt`,
- lane depends on the literature family,
- but the learning path must still go through `L4`.

Required flow:

1. gather and register the source basis in `L0`,
2. reconstruct assumptions, notation, and dependencies in `L1`,
3. organize candidate understanding in `L3-A`,
4. run reconstruction and consistency checks in `L4`,
5. return through `L3-R`,
6. decide in `L3-D` what becomes reusable memory,
7. and then store it in `L2`.

Frozen rule:

- classical or canonical literature does not bypass `L4`.

AITP must learn papers the way a real researcher learns them:

- by reconstructing and checking,
- not by only summarizing.

## Frozen Layer Responsibility Matrix

### `L0` Source Substrate

Primary job:

- gather, register, and organize the source basis for later reasoning.

Primary outputs:

- source registry,
- citation graph,
- source fidelity grade,
- source packet,
- and source-followup tasks.

Mandatory qualities:

- source provenance is explicit,
- citation traversal remains possible,
- fidelity is visible,
- and concrete artifacts are registered before strong downstream reuse.

Must not do:

- treat retrieved snippets as conclusions,
- treat source presence as understanding,
- or bypass source registration when later work materially depends on a source.

Backedge triggers:

- missing upstream source,
- weak fidelity,
- broken citation closure,
- or unresolved historical dependency chain.

### `L1` Technical Understanding

Primary job:

- read sources like a physicist, not like a summarizer.

Primary outputs:

- assumption table,
- notation table,
- regime table,
- claim extraction packet,
- reading-depth record,
- contradiction candidates,
- and source-faithful technical notes.

Must consult `L2` for:

- terminology alignment,
- reusable warnings,
- nearby concept structure,
- and known scope traps.

Must not do:

- promote directly into canonical `L2`,
- compress technical reading into generic prose,
- or confuse remembered background with what the current sources established.

Backedge triggers:

- shallow understanding,
- notation conflict,
- implicit assumptions,
- or an under-reconstructed source argument.

### `L3` Umbrella Layer

`L3` remains a top-level layer, but it is now frozen as three internal
subplanes:

- `L3-A` topic analysis
- `L3-R` result integration
- `L3-D` distillation

This is not a new top-level layer family.
It is the internal decomposition of the current overloaded `L3`.

#### `L3-A` Topic Analysis Plane

Primary job:

- analyze the live research topic,
- compare routes,
- combine literature with the user's idea,
- and decide what should be checked next.

Primary outputs:

- route comparison artifact,
- bridge candidate,
- analysis note,
- candidate packet,
- and next-step routing choice.

This is the default destination after:

- `L1`,
- and after any `L2` consultation.

Frozen connectivity:

- `L0 -> L1 -> L3-A`
- `L2 consult -> L3-A`

`L3-A` may send work to:

- `L4`
- `L0`
- `L1`

#### `L3-R` Result Integration Plane

Primary job:

- receive `L4` results,
- interpret what they mean for the research question,
- and translate raw checking outcomes into reusable analysis.

Primary outputs:

- result integration note,
- check interpretation artifact,
- scope update,
- failure classification,
- and route-return recommendation.

Frozen rule:

- `L4` returns to `L3-R`, not directly to `L2`.

`L3-R` may send work to:

- `L3-A`
- `L3-D`
- `L0`
- `L1`

#### `L3-D` Distillation Plane

Primary job:

- decide what from the current topic is worth preserving as reusable memory,
- prepare staging writes,
- and prepare canonical promotion candidates.

Primary outputs:

- staged insight candidate,
- distilled reusable packet,
- promotion-ready memory candidate,
- and memory-scope summary.

`L3-D` may send work to:

- `staging`
- `L2`
- `L3-A`
- `L1`

### `L4` Validation And Adjudication

Primary job:

- perform real checks rather than only describe validation posture.

Required validation families include:

- symbolic sanity checks,
- limiting-case checks,
- dimensional checks,
- symmetry checks,
- notation and definition consistency checks,
- source-consistency checks,
- toy-model checks,
- numerical checks,
- and code-and-artifact validation when relevant.

Required outcome postures include:

- `pass`
- `partial`
- `blocked`
- `interesting_failure`
- `regime_mismatch`
- `needs_source_recovery`

Must not do:

- collapse everything into pass/fail,
- replace real checks with prose,
- or directly promote fresh `L4` output into `L2`.

## Mandatory Movement Law

The frozen movement law is now:

- `L0 -> L1 -> L3-A`
- `L2 consult -> L3-A`
- `L3-A -> L4 | L0 | L1`
- `L4 -> L3-R`
- `L3-R -> L3-A | L3-D | L0 | L1`
- `L3-D -> staging | L2 | L3-A | L1`

The old shorthand:

- `L0 -> L1 -> L3 -> L4 -> L2`

is no longer sufficient as the top-level target.

The essential frozen points are:

- `L0/L1/L3-A` is the mandatory front-side research chain,
- `L2` always re-enters through `L3-A`,
- and `L4` always re-enters through `L3-R`.

## `H-plane` Human Interaction Plane

Human interaction is not a normal epistemic layer.
It is a cross-cutting interaction plane.

The system should therefore model:

- `H-plane`, not `H-layer`.

Why:

- `Human` does not represent a research object state,
- it represents intervention, review, steering, checkpointing, and
  interpretation exchange.

Frozen rule:

- `H-plane` may interact with `L0`, `L1`, `L3-A`, `L3-R`, `L3-D`, `L4`, and
  `L2`.

It should govern:

- when the system stops,
- when it only reports,
- when it must ask for route choice,
- when a promotion or staging decision needs review,
- and when a result summary should be surfaced without blocking.

## `L2` As Active Research Brain

`L2` remains:

- governed reusable scientific memory,
- not a raw RAG layer,
- and not a shortcut that replaces fresh work.

But `L2` must now explicitly support three memory roles:

- active consultation memory,
- staged provisional memory,
- and distilled reusable scientific memory.

This is the frozen answer to the external pattern:

- retrieval alone is not enough,
- AITP must compile and integrate.

## Knowledge Compilation Operation

This framework adds one frozen operation family:

- `knowledge_compilation_operation`

It is not:

- a new top-level mode,
- a new lane,
- or a new layer.

It is the operation by which repeated reading, discussion, and checking become
durable research memory.

The frozen loop is:

1. new source or discussion enters,
2. `L1` extracts assumptions, notation, claims, and tension,
3. `L3-A` combines that with the active topic,
4. `L4` checks the right bounded object when needed,
5. `L3-R` interprets the check result,
6. `L3-D` decides what is worth preserving,
7. staging records provisional reusable memory,
8. and only later may canonical `L2` writeback happen.

## Trust Surfaces

The trust split remains:

- canonical `L2`
- compiled `L2`
- staging `L2`

But staging is now frozen more sharply as:

- the provisional memory surface produced by `L3-D` and knowledge compilation,
- not just a scratch inbox.

## Domain Memory Versus Collaborator Memory

This distinction is frozen.

### Domain memory

Domain memory stores:

- reusable scientific concepts,
- methods,
- workflows,
- route capsules,
- warning notes,
- physical pictures,
- and later theory-synthesis objects.

This belongs in governed `L2`.

### Collaborator memory

Collaborator memory stores:

- user preference,
- route history,
- taste signals,
- long-horizon concerns,
- and personal research trajectory.

It must be durable, but it must not be confused with canonical scientific
memory.

Frozen rule:

- collaborator memory is not canonical domain memory.

## Roadmap Consequences

The current roadmap direction is mostly right, but it needs the following
frozen additions.

### Addition 1: task type must become explicit

The system must explicitly model:

- `open_exploration`
- `conjecture_attempt`
- `target_driven_execution`

### Addition 2: `H-plane` must become explicit

Interaction should be modeled as a cross-cutting plane rather than as ad hoc
runtime text.

### Addition 3: `L3` must be internally decomposed

The roadmap must treat `L3` as:

- `L3-A`
- `L3-R`
- `L3-D`

while preserving top-level `L3` continuity.

### Addition 4: `L4 -> L3-R` is mandatory

The system must stop acting as if `L4 -> L2` is the normal direct move.

### Addition 5: `L3-D -> staging -> L2` is the preferred memory growth path

Memory should usually grow through distillation and staged compilation, not
through direct raw promotion.

## Milestone Translation

### `v1.28`

Must carry:

- task-type semantics,
- `H-plane` framing,
- consultation versus promotion separation,
- and honest stop/backedge meaning.

### `v1.29`

Must carry:

- seeded `L2`,
- lightweight entry,
- `L3-D` to staging flow,
- and the first compiled active-brain behavior.

### `v1.30`

Must carry:

- runtime consultation hookup,
- `H-plane` interaction semantics,
- `L3-A/L3-R/L3-D` aware result displays,
- and richer retrieval/report surfaces.

### `v1.31`

Must carry:

- task-type by lane templates,
- source intelligence,
- and physicist-grade `L4` validation.

### `v1.32`

Must carry:

- collaborator memory,
- negative-result retention,
- and low-bureaucracy exploration.

### `M5` collaborator-core target

Must carry:

- `theory_synthesis` lane,
- paired backend maturity,
- cross-paper reconciliation,
- and auditable higher-level synthesis.

## Acceptance Standard

The framework is only successful when AITP can repeatedly support:

- free exploration,
- conjecture attempts,
- and target-driven execution,

across:

- formal theory,
- model numerics,
- and code-and-materials work,

while staying honest about:

- source basis,
- synthesis state,
- check state,
- memory growth,
- and human decision points.

## One-Line Doctrine

AITP should organize theoretical-physics work by `task_type × lane × layer`,
route every fresh source or memory return through analysis, route every `L4`
output through result integration, distill reusable knowledge before storing it,
and let the human interaction plane intervene anywhere without collapsing that
interaction into the epistemic layer model.
