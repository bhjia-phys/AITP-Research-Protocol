# AITP Soft Exploration And Hard Trust Runtime Design

Status: working design

Date: 2026-04-09

## Goal

Preserve model intelligence inside AITP by letting the system explore freely
for a bounded window before forcing protocol closure, while keeping hard trust
gates for validation, writeback, and blocking operator decisions.

Short form:

- exploration should be flexible,
- trust should be strict,
- and the runtime should support thought without prematurely interrupting it.

## Problem

AITP now has much better layer visibility than before:

- `L0` source basis,
- `L1` understanding basis,
- `L3-A/L3-R/L3-D`,
- `L4` validation surface,
- and `L2` memory surfaces

are all materially represented in the runtime bundle.

That is necessary, but it also introduces a real risk:

- the runtime may begin forcing the model to satisfy protocol surfaces before
  the model has been allowed to think usefully.

For a real theoretical-physics collaborator, that would be a regression.

Good research behavior is usually:

1. notice a promising intuition,
2. explore it for a few steps,
3. compare alternatives,
4. identify the blocker or best route,
5. then write the durable layer artifact.

Bad behavior is:

1. force contract completion,
2. then allow the idea to continue.

AITP must therefore distinguish:

- freedom to think,
- from permission to claim,
- and from permission to store.

## Core Principle

AITP should constrain trust and writeback, not constrain intelligence and
exploration.

That means:

- use soft constraints for `L0/L1/L3-A` exploration,
- use hard constraints for `L4`, `L3-D`, `L2` writeback, and blocking
  `H-plane` decisions,
- and treat runtime protocol as a recovery and alignment system, not as a
  prerequisite for every useful thought.

## Runtime Model

The runtime should operate in two modes:

1. `exploration_window`
2. `commit_window`

These are runtime postures, not new epistemic layers.

## `exploration_window`

### Purpose

Allow the model to test a bounded number of new physical ideas, bridges,
comparisons, or route choices before durable protocol closure is required.

### Allowed zone

The exploration window is primarily for:

- `L0`
- `L1`
- `L3-A`

Typical examples:

- trying a new bridge idea,
- sketching a possible analogy,
- comparing two literature clusters,
- proposing multiple route candidates,
- or noting a likely but not yet verified structural correspondence.

### Rules

- The model may think ahead without first updating all durable topic contracts.
- The model may produce provisional route hypotheses.
- The model may gather small local evidence before deciding which layer should
  own the result.
- The model may revise or discard a route without treating every partial idea
  as a canonical topic state change.

### Limits

The exploration window is not unbounded.
It should remain:

- bounded in step count,
- bounded in scope,
- and bounded in downstream commitments.

The runtime must eventually force closure when the thought becomes durable.

## `commit_window`

### Purpose

Force explicit layer closure only when the work has crossed from useful
thinking into something that affects trust, validation, writeback, or blocking
human coordination.

### Mandatory triggers

The system must leave `exploration_window` and enter `commit_window` when any
of the following happens:

1. the model wants to enter real validation:
   - `L3-A -> L4`
2. the model wants to distill or write back durable memory:
   - `L3-D -> staging`
   - `L3-D -> L2`
3. the model wants to present a high-stakes claim as if it were settled
4. the model needs a blocking human decision
5. the model wants to declare a new main route rather than a speculative branch

Once any of these triggers fires, the runtime must require explicit handoff
into the correct formal layer surface.

## Exploration Surface

The runtime should gain one lightweight exploration carrier:

- `runtime/topics/<topic_slug>/exploration_window.json`
- `runtime/topics/<topic_slug>/exploration_window.md`

This is not a new layer.
It is a transient working-memory projection that records:

- current exploration question,
- recent candidate intuitions,
- local blockers,
- likely next target layer,
- whether the window is still open,
- and whether closure is now required.

It should stay lighter than:

- research contract,
- validation contract,
- or canonical memory surfaces.

Its purpose is to preserve promising model thought without forcing premature
formalization.

## Layer Re-entry Rule

Once an exploration window has generated something durable enough to keep, the
result must be re-entered through the appropriate layer:

- source expansion or recovery goes to `L0`
- notation / assumptions / regime / extracted claim structure goes to `L1`
- route comparison / bridge candidate / topic candidate goes to `L3-A`
- validation result interpretation goes to `L3-R`
- reusable-memory preparation goes to `L3-D`
- canonical memory still requires `L3-D -> staging/L2`

This rule keeps AITP flexible while preserving the layer ontology.

## Anti-Rigidity Rules

To keep AITP from becoming dead:

### Rule 1. `must_read_now` stays minimal

`must_read_now` should contain only the smallest set needed to safely resume or
continue.
The existence of many protocol surfaces does not justify forcing the model to
read them all before it can think.

### Rule 2. Checkpoints are exceptional

`H-plane` blocking checkpoints should fire only when:

- a real human choice is needed,
- a contradiction must be adjudicated,
- a route boundary is consequential,
- or promotion/writeback needs review.

They should not be used as the default response to every uncertain idea.

### Rule 3. Runtime summaries do not replace analysis

Runtime projections summarize layer state.
They must not replace:

- actual `L1` reading,
- actual `L3-A` route comparison,
- or actual `L4` reasoning.

### Rule 4. Heuristic thought is allowed before durable closure

The model should be allowed to:

- propose,
- compare,
- abandon,
- and redirect

inside the exploration window without treating every micro-step as protocol
debt.

### Rule 5. Hard gates remain hard

The system must not soften:

- writeback rules,
- promotion rules,
- validation honesty,
- or blocking human review.

This is where protocol discipline belongs.

## Interaction Consequence

The runtime interaction contract should distinguish:

- `free_explore`
- `silent_continue`
- `checkpoint_question`

`free_explore` means:

- the model is allowed to continue bounded speculative analysis without first
  satisfying a stronger contract surface,
- but the runtime still records the current exploration carrier.

This is different from `silent_continue`, which means:

- continue the currently established route.

## Expected Effect

If implemented correctly, AITP should become:

- less bureaucratic during early idea formation,
- more natural for open theoretical-physics discussion,
- better at preserving promising intuitions,
- and still strict when evidence, validation, or memory promotion matter.

## Non-Goals

This design does not:

- remove layer discipline,
- remove auditability,
- remove promotion gates,
- or turn AITP into unconstrained chat memory.

It changes when formal closure becomes mandatory, not whether formal closure
exists.

## Acceptance Standard

This design is successful only if all of the following are true:

1. The model can explore several bounded candidate ideas before filling formal
   protocol surfaces.
2. The runtime preserves those candidate ideas durably enough that they are not
   lost.
3. Moving into `L4`, `L3-D`, or `L2` still forces correct closure.
4. Human blocking checkpoints become less frequent in ordinary exploration but
   remain strict where trust requires them.
5. AITP feels more like a real collaborator and less like a workflow form
   engine.

## One-Line Doctrine

AITP should think first in a bounded exploration window, commit only when trust
or memory requires it, and use protocol to protect scientific honesty rather
than to interrupt every promising line of thought.
