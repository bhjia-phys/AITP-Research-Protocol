# AITP Transition And Backedge Protocol

Status: draft working doctrine

## Decision

AITP should keep a simple default forward law:

`L0 -> L1 -> L3 -> L4 -> L2`

But it must also treat several backedges as normal research behavior rather
than rare exceptions.

Short form:

- forward motion is the default
- backedges are legitimate
- each transition needs an explicit trigger and writeback meaning

## Why This Document Exists

AITP already has a strong layer ontology.

What remained under-specified was:

- when a layer jump is legitimate,
- when a return is required,
- what artifacts should record that move,
- and when the human must be asked before crossing the boundary.

Without that, the runtime risks two opposite failures:

- fake linear progress that ignores missing source or memory debt,
- or arbitrary bouncing between layers with no stable meaning.

This document exists to define the law of motion over the layer graph.

## 1. Transition Kinds

AITP should distinguish three transition kinds:

1. `forward_transition`
2. `backedge_transition`
3. `boundary_hold`

### 1.1 Forward Transition

Move to the next epistemic layer because the current one produced the required
bounded object.

Examples:

- `L0 -> L1` after source intake becomes a usable interpretation packet
- `L1 -> L3` after the question is bounded enough to form a candidate
- `L3 -> L4` after a candidate is concrete enough to validate
- `L4 -> L2` after validation and gate review justify reusable writeback

### 1.2 Backedge Transition

Return to an earlier or supporting layer because the honest blocker is not
solvable inside the current local loop.

Examples:

- `L1 -> L0` for missing citation or definition recovery
- `L3 -> L0` for missing derivation anchor or source basis
- `L4 -> L0` when validation exposes missing source support
- `L3 -> L2` for reusable method or warning-note consultation
- `L4 -> L2` for terminology, bridge, or prior validated-route consultation

### 1.3 Boundary Hold

Remain in the current layer because the current local task is still honest and
bounded.

Not every incomplete step needs a transition.

## 2. Default Forward Law

The default non-trivial research path remains:

`L0 -> L1 -> L3 -> L4 -> L2`

This law should remain the simplest explanation of a healthy topic.

It protects:

- evidence before interpretation,
- interpretation before candidate claim,
- candidate claim before validation,
- validation before reusable memory.

AITP should therefore remain conservative about adding new core layers.

## 3. Legal Backedges

The following backedges should be treated as first-class:

- `L1 -> L0`
- `L3 -> L0`
- `L4 -> L0`
- `L3 -> L2`
- `L4 -> L2`

They are not workflow failures.
They are normal scientific honesty moves.

## 4. Trigger Rule

Every transition should have an explicit trigger family.

### 4.1 Forward Triggers

Forward transitions are legitimate when the current layer has produced the
required bounded artifact.

Examples:

- `L0 -> L1`: selected sources are registered and interpreted enough to support
  a bounded question
- `L1 -> L3`: a candidate route or bounded action is concrete enough to try
- `L3 -> L4`: a candidate is concrete enough to validate or adjudicate
- `L4 -> L2`: validation plus promotion gate both allow reusable writeback

### 4.2 Backedge Triggers

Backedges are legitimate when the blocker belongs elsewhere.

Examples:

- `missing_source_anchor`
- `missing_definition_anchor`
- `missing_prior_work_comparison`
- `missing_reusable_method_memory`
- `missing_warning_or_bridge_note`
- `execution_lane_not_decided`
- `resource_commitment_not_approved`
- `contradiction_requires_reframing`

If a blocker is already classified in one of these families, AITP should not
pretend more local work will solve it.

## 5. Writeback Rule

Transitions should not be silent.

Every meaningful transition should update at least one durable artifact that
records:

- what moved,
- why it moved,
- what remains blocked,
- and what the next bounded task is.

In practice, that can be expressed through:

- runtime synopsis updates,
- gap or blocker notes,
- validation review notes,
- decision surfaces,
- consultation receipts,
- or promotion-gate artifacts.

The key rule is:

- transition meaning must live on disk, not only in temporary model state

## 6. Human Checkpoint Rule

Human checkpoints should appear at transition boundaries when trust or cost
changes materially.

Typical checkpoint cases:

- execution lane choice is still open
- server or resource commitment is required
- multiple adjudication routes remain live
- promotion or writeback is being requested
- contradiction resolution would materially redirect the topic

Human checkpoints should not appear for every ordinary `boundary_hold`.

## 7. Relationship To Mode

Mode does not replace transition law.

Mode specifies:

- what context is mandatory now,
- what stays deferred,
- what backedges are allowed in the current posture,
- and what writeback is required for this step.

Transition law specifies:

- what kind of move is being made over the layer graph,
- and what justifies that move.

So:

- mode = operating envelope
- transition protocol = movement law

## 8. Relationship To Iterative Verify

The `iterative_verify` submode is allowed only inside bounded `L3-L4` work.

When that loop discovers the real blocker is:

- missing `L0`,
- missing `L2`,
- or unresolved human route choice,

it should exit through a real backedge or checkpoint rather than silently
continuing.

## 9. Runtime Consequence

AITP runtime artifacts should increasingly expose:

- current layer,
- selected next action,
- active blockers,
- allowed deeper reads,
- and explicit trigger-based backedges.

This implies:

- `must_read_now` should stay small,
- deeper surfaces should be trigger-bounded,
- and machine or control surfaces should become mandatory only when the active
  transition law requires them.

## 10. Current Consequence

AITP should now formalize transitions and backedges explicitly in both doctrine
and runtime behavior.

That means:

- keep the core layer list stable
- make backedges normal rather than apologetic
- tie deeper context to explicit trigger families
- and require durable writeback whenever a real boundary crossing occurs

That is the intended transition law.
