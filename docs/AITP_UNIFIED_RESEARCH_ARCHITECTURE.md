# AITP Unified Research Architecture

Status: working design synthesis

## Purpose

This document is the top-level design contract for AITP as a research
collaborator.

It exists to unify several design threads that are currently documented
separately:

- the `L0-L4` epistemic layer model,
- lanes,
- runtime modes and backedges,
- progressive-disclosure runtime behavior,
- `L2` trust semantics,
- and the paired human-readable plus typed theoretical-physics knowledge
  network.

The goal is to keep these structures compatible rather than letting them drift
into competing local taxonomies.

## Design problem

AITP currently has strong partial designs, but they live on different axes:

- `layer` says what kind of epistemic object something is;
- `lane` says what kind of bounded research loop is dominant;
- `mode` says how the system should operate right now;
- `transition` says how the system moves over the layer graph;
- `canonical / compiled / staging` says what trust posture an `L2` surface has;
- paired downstream backends say how long-term theoretical-physics knowledge is
  realized for humans and for machines.

These axes are individually useful.
The main problem is not that any one of them is wrong.
The main problem is that AITP still lacks one unified statement of how they fit
together.

## Core decision

AITP should be modeled as six orthogonal axes:

1. `layer`
2. `lane`
3. `mode`
4. `transition`
5. `knowledge trust surface`
6. `knowledge realization`

Short form:

- layer = epistemic meaning
- lane = dominant closure style
- mode = operating posture
- transition = movement law
- trust surface = authoritative vs derived vs provisional `L2`
- realization = where long-term knowledge is stored for humans and machines

These axes must not be collapsed into one mixed taxonomy.

## 1. The six axes

### 1.1 Layer

Layer answers:

- what kind of research-state object is this right now?

AITP keeps the current epistemic layer model:

- `L0` source substrate
- `L1` intake / provisional understanding
- `L3` candidate formation / exploratory notebook
- `L4` validation / adjudication
- `L2` reusable promoted memory

The default forward law remains:

`L0 -> L1 -> L3 -> L4 -> L2`

### 1.2 Lane

Lane answers:

- what kind of bounded research loop is mainly doing the work?

Current primary lanes remain:

- `formal_theory`
- `toy_numeric`
- `code_method`

AITP should also reserve one explicit future extension lane:

- `theory_synthesis`

This extension lane is the natural home for:

- cross-paper comparison,
- assumption reconciliation,
- framework alignment,
- notation unification,
- and concept-network construction that is not well described as proof, toy
  numerics, or implementation.

### 1.3 Mode

Mode answers:

- how should AITP operate for this step?

Keep the current small top-level mode set:

- `discussion`
- `explore`
- `verify`
- `promote`

Keep one bounded conditional submode:

- `iterative_verify`

Do not solve every missing behavior by inventing more top-level modes.
If a new behavior is local and bounded, prefer:

- a submode,
- a trigger,
- or an operation family inside an existing mode.

### 1.4 Transition

Transition answers:

- what move is being made over the layer graph?

Keep the current movement law:

- `forward_transition`
- `backedge_transition`
- `boundary_hold`

Backedges are first-class and normal:

- `L1 -> L0`
- `L3 -> L0`
- `L4 -> L0`
- `L3 -> L2`
- `L4 -> L2`

### 1.5 Knowledge trust surface

This axis applies specifically to `L2`.

Keep the current three trust classes:

1. canonical `L2`
2. compiled `L2`
3. staging `L2`

Short form:

- canonical is authoritative
- compiled is derived
- staging is provisional

This is a trust distinction, not a human-versus-machine distinction.

### 1.6 Knowledge realization

This axis answers:

- where does long-term domain knowledge live as a usable downstream
  realization?

For theoretical physics, AITP should treat the paired downstream knowledge
network as two coordinated realizations:

- `backend:theoretical-physics-brain`
  - operator-facing, human-readable realization
- `backend:theoretical-physics-knowledge-network`
  - typed, structured, machine-strong realization

These are two realizations of the same downstream knowledge network.
They are not separate epistemic layers.

## 2. Unified architecture

### 2.1 Plane A: research process plane

This is the active research process.

It includes:

- `L0`
- `L1`
- `L3`
- `L4`
- cross-layer support surfaces such as `runtime/`, `consultation/`, and
  `schemas/`

Its job is:

- topic progress,
- source grounding,
- candidate formation,
- validation,
- trust gating,
- and bounded promotion decisions.

This plane is where modes and transitions live.

### 2.2 Plane B: L2 governance plane

This is the AITP-governed memory plane.

Its job is:

- assign reusable identity,
- preserve provenance,
- define trust posture,
- expose retrieval profiles,
- materialize compiled helper surfaces,
- materialize hygiene and staging surfaces,
- and record backend bridge intent.

This plane is not the same as a giant downstream knowledge library.
It is the AITP-governed contract and indexing surface for reusable knowledge.

### 2.3 Plane C: downstream knowledge-network plane

This is where theoretical-physics knowledge is realized for long-horizon use.

For the paired theoretical-physics setup, it has two coordinated
implementations:

- the human-readable brain
- the typed knowledge network

These should be treated as:

- paired downstream realizations,
- semantically aligned,
- governed by the same promotion packet,
- and audited for drift.

Neither path alone should silently define truth merely because of file format.

### 2.4 Task-type framing, `H-plane`, and `L3` subplanes

AITP also needs an explicit `task_type` framing on top of layer and lane.

Current bounded task types are:

- `open_exploration`
- `conjecture_attempt`
- `target_driven_execution`

The runtime-facing lane-family language may still group some execution-heavy
routes under `code_and_materials`, but that is a routing convenience rather
than a replacement for the primary AITP lanes.

AITP also needs an explicit `H-plane`.

`H-plane` means the human interaction plane:

- where operator checkpoints happen,
- where steering is injected,
- and where human-readable consultation outputs and result surfaces are shown.

Layer 3 should now be read as three internal subplanes:

- `L3-A` for analysis and route comparison
- `L3-R` for result integration
- `L3-D` for distillation before staging or `L2`

This keeps one crucial return law visible:

- `L4 -> L3-R`

Validation may decide the next move, but reusable-memory preparation should not
skip the `L3-R` result-integration surface.

## 3. Human-readable versus typed backend rule

### 3.1 What remains true

The paired backend design is valid and should remain.

Human-readable and typed knowledge should both exist because they serve
different but equally real needs:

- the human-readable backend supports reading, curation, explanation, and
  operator cognition;
- the typed backend supports graph checks, structured retrieval, alignment,
  and machine rebuilding.

### 3.2 What must be clarified

AITP should not rely on vague words like "canonical" without stating which axis
is meant.

There are at least three different meanings in play:

1. canonical as authoritative `L2` trust posture
2. canonical as the kernel-root contract surface under `research/knowledge-hub/canonical/`
3. canonical as "the machine-strong typed representation"

These meanings must be separated.

### 3.3 Unified rule

Use this rule going forward:

- semantic identity is anchored by the promotion packet, reusable unit id,
  provenance, assumptions, and scope;
- trust status is anchored by the `L2` governance plane;
- human-readable and typed backends are paired realizations of that identity;
- if one realization is richer for a given family, record the reduction
  honestly rather than silently broadening or weakening the claim.

### 3.4 Practical primary roles

To avoid fake equality while still avoiding an absolute hierarchy:

- the human-readable backend is `operator-primary`
  - reading, editing, and domain narrative
- the typed backend is `machine-primary`
  - graph checks, retrieval, relation traversal, and structural rebuilding

But:

- neither backend is globally more authoritative than the other by path alone;
- the authority comes from the paired promotion and alignment contract.

## 4. L2 trust surfaces versus backend realizations

This distinction must stay explicit.

### 4.1 Canonical `L2`

Canonical `L2` means:

- promoted reusable units,
- lightweight authoritative relation/index layers,
- promotion and provenance records,
- backend bridge metadata,
- and the minimum contract surfaces needed for trustworthy retrieval and
  writeback.

### 4.2 Compiled `L2`

Compiled `L2` means:

- derived maps,
- navigation aids,
- consultation helpers,
- replay surfaces,
- and other regenerated views.

Compiled surfaces may be:

- machine-readable,
- human-readable,
- or both.

They are still derived.
They are not the same thing as the human-readable backend.

### 4.3 Staging `L2`

Staging `L2` means:

- quarantine,
- provisional entry,
- pre-promotion capture,
- and explicit not-yet-trusted memory.

Staging is where low-friction capture should land before full canonical
promotion.

### 4.4 Consequence

Do not confuse:

- `compiled markdown` with `human-readable backend`,
- `typed backend` with `canonical truth`,
- or `staging capture` with reusable memory.

These are different axes.

## 5. Operation families

AITP does need more than one kind of local operation.
But these should usually be modeled as operation families inside the existing
mode system rather than as many new top-level modes.

### 5.1 Source intake operation

Primary shape:

- layer: `L0 -> L1`
- dominant mode: `discussion` or `explore`
- output: registered source plus bounded interpretation surface

### 5.2 Consultation operation

Primary shape:

- layer: `L1/L3/L4 -> L2` narrow consult
- dominant mode: depends on caller
- output: consultation receipt and applied summary

Rule:

- consultation is not promotion
- consultation outputs may be human-facing or AI-facing, but they should be
  derived from the same promoted identity and consultation event

### 5.3 Candidate-build operation

Primary shape:

- layer: `L1 -> L3`
- dominant mode: `explore`
- output: candidate packet, blocker note, route choice

### 5.4 Iterative verification operation

Primary shape:

- layer: bounded `L3/L4`
- dominant mode: `verify`
- submode: `iterative_verify`
- output: explicit pass/partial/fail/blocked evidence

### 5.5 Promotion operation

Primary shape:

- layer: `L4 -> L2`
- dominant mode: `promote`
- output: promotion gate, backend receipt, reusable registration

### 5.6 Knowledge-curation operation

Primary shape:

- layer: `L2`
- dominant mode: usually `promote` or operator-invoked maintenance
- output: compiled surfaces, hygiene reports, staging review, pair-alignment
  audit

This is the right place for:

- drift reports between brain and TPKN
- rebuild of compiled maps
- integrity checks over graph and indexes

### 5.7 Trajectory-learning operation

Primary shape:

- spans multiple topics and sessions
- not a new layer
- not a free-form memory dump

Its job is:

- collaborator profile updates,
- recurring taste and reasoning preferences,
- route success/failure history,
- negative-result memory,
- and research-trajectory summaries.

This should eventually feed:

- lane choice,
- mode choice,
- suggestion quality,
- and retrieval ranking.

## 6. How AITP should become a better collaborator

AITP should become more useful through four concrete growth loops.

### 6.1 Knowledge growth loop

Needed capabilities:

- lightweight knowledge capture
- first seeded graph
- graph traversal
- progressive disclosure retrieval

Without this loop, AITP only accumulates runtime traces.
It does not become smarter in a reusable way.

### 6.2 Research judgment loop

Needed capabilities:

- assumption extraction
- reading depth awareness
- symbolic and analytical validation
- research momentum and stuckness detection

Without this loop, AITP behaves like a disciplined workflow runner rather than
a scientific collaborator.

### 6.3 Collaborator memory loop

Needed capabilities:

- collaborator profile
- cross-session context
- research trajectory summary
- remembered negative results and abandoned routes

Without this loop, AITP can resume a topic but does not really remember the
researcher.

### 6.4 Low-bureaucracy exploration loop

Needed capabilities:

- quick exploration mode
- reduced artifact footprint
- later promotion from quick exploration into full topic form

Without this loop, AITP is too heavy for the earliest and most creative stages
of research.

## 7. Current architectural problems

From this unified view, the main current problems are:

1. The paired human-readable plus typed knowledge-network design exists, but
   the graph and retrieval substrate is still too empty to make it truly
   operational.
2. The system has good protocol surfaces for lanes, modes, and transitions, but
   the knowledge-growth path is still underpowered.
3. `L2` trust semantics and backend-realization semantics are both present, but
   they are not yet stated in one place strongly enough to prevent confusion.
4. The runtime control plane is richer than the reusable-memory plane, which
   makes AITP better at process discipline than at becoming wiser over time.
5. The system still lacks a first-class operation for paired-backend alignment,
   drift reporting, and rebuild policy.

## 8. Unified priority order

If AITP is being built first as a theoretical-physics collaborator rather than
first as a publication or packaging system, the next work should prioritize the
following order.

### Priority A: make `L2` actually grow

Recommended cluster:

- graph traversal and search
- progressive disclosure retrieval
- first seeded knowledge graph
- lightweight knowledge entry

### Priority B: make validation look more like theoretical physics

Recommended cluster:

- assumption extraction and reading depth
- symbolic and analytical reasoning path
- analytical validation beyond numerical execution
- research judgment in decision-making

### Priority C: make the agent feel like a long-term collaborator

Recommended cluster:

- cross-session collaborator learning
- research trajectory recording
- quick exploration mode
- source fidelity grading
- citation graph traversal

### Priority D: only then expand publication-facing output

`L5 Publication Factory` should remain downstream of evidence, reusable memory,
and collaborator-quality improvements.

## 9. Rules for future design changes

Use these rules when evaluating new AITP proposals.

### 9.1 Do not add a new core layer lightly

Most current gaps are:

- transition gaps,
- mode gaps,
- retrieval gaps,
- or realization gaps.

They are not evidence that the layer ontology itself is wrong.

### 9.2 Do not turn every operation into a new top-level mode

Prefer:

- four stable top-level modes,
- a small number of submodes,
- and explicit operation families.

### 9.3 Do not let runtime state become the real knowledge base

Runtime is the control plane.
It is not the durable knowledge network.

### 9.4 Do not let the human-readable backend degrade into prose dump

The human-readable backend must still preserve:

- identity,
- evidence anchors,
- assumptions,
- regime limits,
- warnings,
- and unresolved gaps.

### 9.5 Do not let the typed backend silently claim authority by structure alone

Typed structure is valuable, but it is not equivalent to justified truth.

### 9.6 Do not mix compiled surfaces with canonical status

Compiled views help use knowledge.
They do not define what knowledge is.

### 9.7 Lean remains downstream

Lean remains a downstream export path, not the definition of `L2` success.

Formal export matters, but it is not the definition of `L2` success for the
whole AITP kernel.

## 10. One-line doctrine

AITP should separate epistemic layers, operating modes, research lanes, trust
surfaces, and human-versus-machine knowledge realizations, then connect them
through explicit promotion, consultation, and alignment contracts instead of
letting one file format or one runtime surface silently become the whole
system.
