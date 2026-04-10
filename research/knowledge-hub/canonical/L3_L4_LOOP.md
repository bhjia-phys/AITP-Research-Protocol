# Layer 3 / Layer 4 loop

This file defines the working loop between the research notebook surface and the execution-validation surface.

## Layer roles

### Layer 3
Layer 3 is the place for:
- active interpretation,
- candidate derivations,
- conjectures,
- promotion candidates,
- unresolved issues,
- research blockers,
- bridge backlog,
- pre-validation reasoning.

### Layer 4
Layer 4 is the place for:
- explicit checks,
- numerical runs,
- symbolic checks,
- formalization attempts,
- contradiction tests,
- benchmark comparisons,
- promotion decisions.

## Default loop

1. Start in Layer 3.
   Create a candidate with a clear question, target object type, and expected evidence.

2. Design the check boundary.
   State which parts require execution or explicit adjudication and therefore must move to Layer 4.

3. Run Layer 4 checks.
   Record the plan, inputs, procedures, pass conditions, and outcomes.

4. Return the result to Layer 3 if unresolved.
   Failed checks, contradictions, partial support, and new ambiguities go back to Layer 3 as new research work.
   When the unresolved point depends on external cited literature, the loop may
   also spawn a fresh follow-up subtopic that restarts at `L0`.

5. Promote to Layer 2 only when the result has become a reusable typed object.
   The promoted object should be smaller and more portable than the full run.
   If only part of the candidate is reusable, split it and park the remainder in
   the deferred runtime buffer instead of forcing one mixed promotion.

## Canonical participation

Layer 2 participates in the loop in two ways:
- Layer 2 concepts, methods, and workflows seed Layer 3 candidate formation.
- Layer 2 validation patterns and warning notes shape Layer 4 checks.

So the productive loop is:

`L2 -> L3 -> L4 -> L2`

When starting from a new source, the full path is usually:

`L0 -> L1 -> L3 -> L4 -> L2`

## Failure handling

When Layer 4 does not support promotion:
- do not force canonicalization,
- record why the promotion failed,
- move the unresolved work back to Layer 3,
- create a warning note only if the failure mode itself is reusable.

## Non-negotiable constraint

Direct `L1 -> L4 -> L2` is not allowed.

Layer 4 is not a shortcut around Layer 3.
It is an adjudication surface for explicit Layer 3 candidates.
