# AITP Ontology And Mode Completeness

Status: draft working doctrine

## Decision

AITP should distinguish three different kinds of structure:

- `lane`
- `layer`
- `mode`

They are related, but they are not the same thing.

Short form:

- lane = research-loop type
- layer = epistemic state
- mode = operating posture

AITP should not collapse these into one mixed taxonomy.

## Why This Document Exists

AITP keeps running into the same design question in different forms:

- are the current research types complete,
- are the current layers complete,
- should `mode` just be a rearrangement of layers,
- and what would it mean for the framework to feel "complete enough" to count
  as a serious research harness?

This document exists to answer that cleanly.

## 1. Three Ontology Axes

### 1.1 Lane

A lane answers:

- what kind of bounded research loop is doing the main work here?

Examples:

- proof or derivation loop
- toy-model or benchmark loop
- code-backed implementation loop
- theory-comparison or synthesis loop

A lane is about the dominant way the topic advances.

### 1.2 Layer

A layer answers:

- what kind of epistemic object is this right now?

Examples:

- source
- provisional understanding
- candidate exploratory object
- validation or adjudication object
- reusable promoted memory

A layer is about research-state semantics, not workflow comfort.

### 1.3 Mode

A mode answers:

- how should AITP operate for this step?

That includes:

- what context is minimally required now,
- what context must stay deferred,
- which backedges are allowed,
- what outputs are allowed,
- when human checkpoints are required.

A mode is therefore an operating policy over the layer graph.

It is not simply a layer permutation.

## 2. Lane Completeness

### 2.1 Current Judgment

The current three primary AITP lanes are:

- formal theory
- toy numerics
- code-backed method

These are not a complete ontology of all theoretical-physics research.

But they are a strong and practical `v1` operating basis because they capture
three major bounded closure styles:

- proof or derivation closure,
- benchmark or toy-model closure,
- implementation or method closure.

### 2.2 What They Miss

The current three lanes do not fully cover at least:

- comparative theory synthesis across multiple papers or frameworks,
- large-scale computational theory beyond toy benchmarks,
- phenomenology-like theory routes whose main closure surface is not a toy
  benchmark and not a proof packet.

So the right judgment is:

- not ontologically complete,
- but operationally complete enough for `v1`.

### 2.3 Practical Consequence

AITP should keep the current three lanes as the primary operating set.

But it should also leave room for a bounded fallback or extension lane such as:

- `theory_synthesis`

That lane would cover:

- cross-paper comparison,
- framework alignment,
- concept or notation reconciliation,
- prior-work integration that is not well modeled as pure proof, toy numerics,
  or code method.

## 3. Layer Completeness

### 3.1 Current Judgment

The current core layer model is:

- `L0` source substrate
- `L1` intake or provisional understanding
- `L3` candidate formation or exploratory work
- `L4` validation or adjudication
- `L2` reusable promoted memory

This is already close to complete as an epistemic-state ontology.

AITP should be conservative about adding new core layers.

### 3.2 Why The Current Layers Are Strong

They already separate:

- evidence from interpretation,
- provisional understanding from candidate claims,
- candidate claims from adjudicated results,
- adjudicated results from reusable memory.

That is the core scientific honesty boundary.

### 3.3 What Is Still Missing

What is incomplete is not mainly the layer list.

What is incomplete is:

- the backedge graph,
- and the transition law.

AITP must explicitly support real research backedges such as:

- `L1 -> L0`
- `L3 -> L0`
- `L4 -> L0`
- `L3 -> L2`
- `L4 -> L2`

These are not edge cases.
They are normal theoretical-physics research behavior.

The formal movement law for those returns should live in:

- [`AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md`](AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md)

### 3.4 Consequence

AITP should keep the current layer ontology stable.

It should invest future work in:

- transition rules,
- backedge rules,
- and mode-specific loading envelopes.

## 4. Mode Completeness

### 4.1 Current Judgment

Mode should not be defined as a sequence or permutation of layers.

Instead, mode should be defined as:

- a local operating envelope over the layer graph.

Each mode should say:

- what the foreground task is,
- what the minimal context is,
- what must remain deferred,
- what layer backedges are legal,
- what writeback is required,
- what human interaction policy applies.

### 4.2 Recommended Primary Modes

AITP does not need many top-level modes if they are defined well.

A strong default set is:

- `discussion`
- `explore`
- `verify`
- `promote`

And one important conditional submode:

- `iterative_verify`

### 4.3 Discussion

Use for:

- new ideas,
- framing comparison,
- early direction shaping,
- bounded clarification before hard crystallization.

Foreground:

- `L0`
- `L1`
- early `L3`

Backedges:

- `L1 -> L0`
- narrow consult into `L2`

### 4.4 Explore

Use for:

- real topic advancement,
- candidate formation,
- route generation,
- bounded derivation or benchmark shaping.

Foreground:

- `L1`
- `L3`

Backedges:

- `L3 -> L0`
- `L3 -> L2`

### 4.5 Verify

Use for:

- explicit `L4` validation,
- contradiction checks,
- benchmark adjudication,
- execution planning,
- proof-obligation review.

Foreground:

- `L4`

Backedges:

- `L4 -> L0`
- `L4 -> L2`

### 4.6 Promote

Use for:

- `L2` writeback consideration,
- gate review,
- canonical target selection,
- backend bridge execution.

Foreground:

- `L4 -> L2` boundary

Backedges:

- back to `L4` when validation is still incomplete,
- back to `L0` when source recovery is still missing,
- consult `L2` only in a narrow target-aware way.

### 4.7 Iterative Verify

This is the Ralph-like submode for bounded `L3-L4` work.

Use it when:

- the objective is narrow,
- the completion test is clear,
- failure can produce explicit feedback,
- and multiple short loops are safer than one large pass.

It is not a general replacement for all of AITP.

## 5. Transition Law

Even if lane, layer, and mode are individually strong, AITP is still not
complete unless the transition law is clear.

AITP must say explicitly:

- when a vague idea stops being `discussion` and becomes `explore`,
- when `explore` has enough structure to become `verify`,
- when `verify` must return to `L0`,
- when `verify` may consult `L2`,
- when `verify` may enter `promote`,
- when a bounded `L3-L4` task may enter `iterative_verify`,
- and when human confirmation is required.

This transition law is a first-class part of completeness.

## 6. Completeness Conditions For AITP

AITP should count as structurally complete enough only when:

1. the lane set is operationally sufficient for the intended research domain,
2. the layer model is epistemically stable,
3. the mode set is operationally stable,
4. the transition law is explicit,
5. human interaction boundaries are explicit,
6. `L2` behaves like callable memory rather than a default answer,
7. progressive disclosure is real rather than rhetorical,
8. acceptance topics prove that the system behaves correctly across lanes,
   layers, backedges, and checkpoints.

## 7. Implementation Completeness Is Still Required

Ontology alone is not enough.

Even if lane, layer, mode, and transition law are conceptually complete, AITP
is still not operationally complete if the implementation remains too
centralized, too implicit, or too fragile.

So continuing to reduce giant hotspot files and replace hidden coupling with
clear support boundaries is still part of making AITP complete.

The single-file problem is no longer the only bottleneck.
But it remains a real completeness condition because:

- opaque implementation hides protocol meaning,
- fragile kernels distort future protocol work,
- and over-centralized logic quietly turns operating policy into hidden code.

## 8. Current Judgment

So the current AITP answer is:

- lane: not globally complete, but `v1`-complete enough
- layer: close to complete; do not add more core layers lightly
- mode: can be made complete, but not by treating mode as layer permutation
- transition law: still needs to be made explicit
- implementation: still needs continued decomposition even after recent wins

That is the current completeness posture.
