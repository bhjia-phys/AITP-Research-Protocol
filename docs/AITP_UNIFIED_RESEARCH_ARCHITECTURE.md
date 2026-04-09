# AITP Unified Research Architecture

Status: working design synthesis

## Purpose

This document is the top-level architecture contract for AITP as a
theoretical-physics collaborator.

It is the architecture-facing companion to:

- `docs/superpowers/specs/2026-04-08-aitp-research-scenario-and-layer-responsibility-freeze-design.md`
- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `docs/superpowers/specs/2026-04-08-aitp-collaborator-capability-tracks-design.md`

Its job is not to replace those specs.
Its job is to give one architectural statement of how the major axes fit
together.

## Core Decision

AITP is now treated as eight orthogonal structures:

1. `task_type`
2. `lane`
3. `layer`
4. `mode`
5. `transition`
6. `H-plane`
7. `knowledge trust surface`
8. `knowledge realization`

Short form:

- task type = what kind of research job is being attempted?
- lane = what broad research direction and evidence base dominates?
- layer = what epistemic object is this right now?
- mode = how should the system operate for this step?
- transition = how is it moving over the research graph?
- H-plane = how and when humans intervene, review, steer, or receive results
- trust surface = canonical vs compiled vs staging inside `L2`
- realization = where long-horizon knowledge is materialized for humans and for machines

These structures must not be collapsed into one mixed taxonomy.

## 1. Task Type

The top-level task types are:

- `open_exploration`
- `conjecture_attempt`
- `target_driven_execution`

These are the primary orchestration classes for real research work.

They affect:

- `L0` source breadth,
- `L1` reading posture,
- `L3` route comparison intensity,
- `L4` validation selection,
- and the shape of the reusable result expected in `L2`.

The old coarse `scenario` framing should now be read as acceptance use cases
rather than the main orchestration axis.

## 2. Lane

The main lane families are:

- `formal_theory`
- `model_numeric`
- `code_and_materials`

The reserved future lane remains:

- `theory_synthesis`

These lanes should be understood as broad research directions, not as literal
filesystem roots and not as replacements for the epistemic layer model.

## 3. Layer

The epistemic layers remain:

- `L0` source substrate
- `L1` technical understanding
- `L3` research synthesis
- `L4` validation and adjudication
- `L2` reusable promoted memory

### 3.1 The current `L3` correction

Top-level `L3` remains valid, but it is no longer treated as one undifferentiated
bucket.

It is frozen as an umbrella layer with three internal subplanes:

- `L3-A` topic analysis
- `L3-R` result integration
- `L3-D` distillation

This lets AITP keep top-level continuity while stopping `L3` from carrying
analysis, raw result interpretation, and `L2` preparation as one muddled role.

## 4. Mode

The small top-level mode set remains:

- `discussion`
- `explore`
- `verify`
- `promote`

And the bounded submode remains:

- `iterative_verify`

The architecture rule stays the same:

- do not solve every missing behavior by inventing more top-level modes.

## 5. Transition

The movement law remains transition-based rather than pipeline-only:

- `forward_transition`
- `backedge_transition`
- `boundary_hold`

But the frozen research law is now sharper than the older shorthand.

The older shorthand:

- `L0 -> L1 -> L3 -> L4 -> L2`

is no longer sufficient.

The new frozen target is:

- `L0 -> L1 -> L3-A`
- `L2 consult -> L3-A`
- `L3-A -> L4 | L0 | L1`
- `L4 -> L3-R`
- `L3-R -> L3-A | L3-D | L0 | L1`
- `L3-D -> staging | L2 | L3-A | L1`

This means:

- `L0/L1/L3-A` is the mandatory front-side research chain
- `L2` never replaces fresh analysis and always re-enters through `L3-A`
- `L4` never writes directly to `L2`
- `L4` outputs must return to `L3-R`

## 6. H-Plane

Human interaction is not a normal epistemic layer.

It is a cross-cutting interaction plane:

- `H-plane`

It may intervene at:

- `L0`
- `L1`
- `L3-A`
- `L3-R`
- `L3-D`
- `L4`
- `L2`

Its job is to govern:

- stop versus continue,
- non-blocking update versus blocking checkpoint,
- route choice,
- promotion review,
- contradiction review,
- and user-facing result delivery.

This keeps human interaction explicit without collapsing it into the layer model.

## 7. Knowledge Trust Surface

The `L2` trust split remains:

1. canonical `L2`
2. compiled `L2`
3. staging `L2`

Short form:

- canonical = authoritative reusable memory
- compiled = derived helper surface
- staging = provisional durable memory candidate

This is a trust distinction, not a human-versus-machine distinction.

## 8. Knowledge Realization

For theoretical physics, long-horizon downstream knowledge remains paired:

- `backend:theoretical-physics-brain`
  - operator-primary, human-readable realization
- `backend:theoretical-physics-knowledge-network`
  - machine-primary, typed realization

These are paired downstream realizations of the same promoted identity.

They are not:

- separate epistemic layers,
- and not separate truth systems.

Authority remains with:

- promotion identity,
- provenance,
- assumptions,
- scope,
- and the `L2` governance plane.

## 9. Plane View

### Plane A: research process plane

This plane contains:

- `L0`
- `L1`
- `L3`
- `L4`
- `runtime/`
- `consultation/`
- `schemas/`

It is where:

- reading,
- synthesis,
- checking,
- backedges,
- and human-steered progress happen.

### Plane B: `L2` governance plane

This plane contains:

- canonical memory,
- compiled memory,
- staging memory,
- promotion records,
- edge/index layers,
- and backend bridge metadata.

This plane is further consolidated by:

- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md`
- `research/knowledge-hub/canonical/L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md`

### Plane C: downstream knowledge realizations

This plane contains:

- the human-readable brain
- the typed knowledge network

They remain paired downstream realizations of the same governed knowledge.

## 10. Layer Outputs That Other Parts Read

This is the architectural read contract.
These outputs are the minimum durable handoff surface across `L0/L1/L3/L4/L2`.
If a later layer, runtime surface, or operator report depends on work from an
earlier layer, that dependency should resolve through these artifacts rather
than through chat-only memory.

### `L0` outputs

Expected outputs:

- source registry
- citation graph
- source fidelity metadata
- source packets
- source-followup tasks

Read by:

- `L1`
- `L3-A`
- `L4` when source recovery is needed
- `H-plane` when the operator needs the source basis exposed explicitly

### `L1` outputs

Expected outputs:

- assumption table
- notation table
- regime table
- claim extraction packet
- reading-depth record
- contradiction candidates

Read by:

- `L3-A`
- `L4`
- `L3-D` when distilling reusable memory
- `H-plane` when assumptions or notation conflicts need review

### `L3-A` outputs

Expected outputs:

- analysis workspace
- route comparison
- bridge candidate
- candidate packet
- next-step routing choice

Read by:

- `L4`
- `L0/L1` through backedge choice
- `H-plane`

### `L3-R` outputs

Expected outputs:

- validation return
- post-check interpretation
- scope update
- failure classification
- route-return recommendation

Read by:

- `L3-A`
- `L3-D`
- `H-plane`

### `L3-D` outputs

Expected outputs:

- distilled memory candidate
- staged insight candidate
- promotion-ready packet
- memory-scope summary

Read by:

- `staging`
- canonical `L2`
- `H-plane`

### `L4` outputs

Expected outputs:

- symbolic sanity report
- limit/symmetry/dimensional report
- source-consistency report
- numerical or code/materials validation record
- adjudication outcome

These outputs must return to `L3-R` before any memory writeback.
They should never be consumed as direct `L2` promotion input without that
interpretive pass.

### `L2` outputs

Expected outputs:

- consultation outputs
- compiled helper views
- staged candidates
- reusable canonical units
- downstream realization inputs

Human-facing and AI-facing consultation outputs may differ in rendering, but
must be derived from the same promoted identity.

## 11. `L2` As Active Research Brain

`L2` should function as:

- active consultation memory,
- compiled reusable memory,
- staged provisional memory,
- and long-horizon research accumulation.

It must not function as:

- raw RAG over unexplained corpus text,
- a shortcut that bypasses fresh reading or checking,
- or a hidden promotion path.

This is the architectural version of the shift from retrieval-only memory
toward persistent wiki-style knowledge compilation.

## 12. Collaborator Memory Versus Domain Memory

This distinction is now architectural.

### Domain memory

Stores:

- reusable scientific concepts
- methods
- workflows
- warnings
- route capsules
- physical pictures
- theory-synthesis objects

This belongs in governed `L2`.

### Collaborator memory

Stores:

- route history
- preference
- style and taste
- trajectory
- negative-result reuse posture

This must remain durable, but it is not the same thing as canonical scientific
memory.

## 13. Lean Reserve

Lean remains a downstream export path.

It is not the definition of `L2` success.

The architecture therefore keeps:

- Lean as a downstream export path,
- not the definition of `L2` success.

## 14. Architectural Priority Order

If AITP is being built first as a theoretical-physics collaborator, the priority
order remains:

1. make `L2` actually grow
2. make intake and validation look like real theoretical physics
3. make the agent feel like a long-horizon collaborator
4. only then push reliability polish and publication output

## One-Line Doctrine

AITP should organize theoretical-physics work by `task_type × lane × layer`,
route all fresh source or memory returns through analysis, route all `L4`
results through result integration, distill reusable knowledge before storing
it, and let the human interaction plane intervene anywhere without collapsing
that interaction into the epistemic layer model.
