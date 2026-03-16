# Promotion policy

This file defines the first-pass promotion rules into Layer 2.

## Core rule

Layer 2 stores settled reusable units, not coordination debt.

Keep outside Layer 2:
- promotion queues,
- unresolved prerequisite backlogs,
- bridge backlogs,
- research blockers,
- run-local TODOs,
- active conjecture piles,
- scratch derivation fragments that still need adjudication.

Those belong in Layer 3.

## Allowed promotion routes

### Default route: `L3 -> L4 -> L2`

This is the normal path for anything that required:
- active research interpretation,
- derivation work,
- execution,
- contradiction checking,
- numerical or formal validation,
- or explicit adjudication.

Required conditions:
- a candidate object exists in Layer 3,
- the validation target is explicit,
- a Layer 4 record captures the checks performed,
- provenance is preserved back to the relevant source and run artifacts,
- the promoted unit is smaller and more reusable than the whole run summary.

### Exception route: `L1 -> L2`

Allow direct promotion only when all of the following are true:
- the item is already reusable across runs,
- the abstraction level is appropriate for canonical storage,
- source anchoring is explicit,
- assumptions and regime are explicit,
- no additional Layer 3 exploration or Layer 4 execution is needed,
- the item is low-risk enough that direct promotion will not create canonical debt.

Typical candidates:
- a clean concept definition,
- a narrow source-anchored claim card,
- a small warning note about a documented limitation.

Do not treat `L1 -> L2` as the default.

## Forbidden route

Direct `L1 -> L4 -> L2` is not allowed.

If Layer 4 is involved, Layer 3 must exist first as the explicit staging surface.

## Promotion gate

Before promoting any unit, ask:
- Is the object reusable beyond this source or run?
- Are the assumptions explicit?
- Is the regime of validity explicit?
- Is provenance structural rather than decorative?
- Is the object better represented as a typed unit than as a run summary?
- Has the needed `L3` or `L4` scrutiny actually happened?
- If this depends on a numerical method, has an appropriate public or analytic baseline been reproduced first?
- If this depends on a non-trivial theory method, has the method been decomposed into atomic concepts and dependency links first?
- Is this settled enough for the canonical layer, or is it still coordination debt?

If the answer to any of these is no, keep the item out of Layer 2.

## Decision outcomes

Use one of these outcomes at the end of a promotion review:
- `accepted`: promote to Layer 2 now
- `deferred`: keep in Layer 3 until more work exists
- `rejected`: do not canonicalize in the current form
- `needs_revision`: reshape the object, then review again

## Writeback rule

Do not write back one monolithic summary when the actual reusable output is multiple typed units.

Prefer decomposed promotion such as:
- one `concept`,
- one `claim_card`,
- one `derivation_object`,
- one `validation_pattern`,
- one `warning_note`.

This is how Layer 2 compounds without turning into a report graveyard.
