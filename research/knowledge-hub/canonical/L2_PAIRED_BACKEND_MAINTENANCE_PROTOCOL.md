# L2 paired backend maintenance protocol

This file defines the maintenance operation for paired downstream backends.

It exists so that paired backends do not remain only a conceptual promise.
If AITP says that one human-readable backend and one typed backend are paired
realizations of the same downstream knowledge object, then drift audit,
backend-debt recording, rebuild, and post-rebuild verification must all be
explicit operations.

## 1. Purpose

This protocol keeps four things separate:

- canonical `L2` identity,
- downstream backend realizations,
- compiled helper surfaces,
- and backend debt.

The paired backends may drift in representation, but they may not silently
rewrite canonical truth by file format alone.

## 2. Required operations

Every paired-backend configuration must support:

1. drift audit
2. backend-debt recording
3. bounded rebuild or resynchronization
4. post-rebuild verification

## 3. Drift audit

A drift audit asks:

- which promoted ids exist on both sides,
- whether assumptions, regime limits, and unresolved boundaries still align,
- whether one side has lost source anchors or provenance detail,
- and whether one side has reduced structure that the other still carries.

The output is a drift report, not an automatic rewrite.

## 4. Backend debt

Backend debt is the explicit record that the pair is not fully aligned.

### Non-blocking backend debt

Examples:

- the typed side lacks a richer narrative explanation that still exists in the
  human-facing side;
- the human-facing side omits a machine-only helper field that does not change
  assumptions or trust posture.

### Blocking backend debt

Examples:

- one side is missing a source anchor used by the other;
- one side has lost an unresolved caveat or warning that changes scientific
  interpretation;
- one side merges two identities that the other keeps distinct;
- one side materially changes scope, regime, or assumption boundaries.

Blocking backend debt must stop any claim that the pair is fully aligned.

## 5. Rebuild

Rebuild is the bounded resynchronization step.

Rebuild may:

- regenerate helper structure on the typed side from promoted identity,
- rebuild human-readable summaries from promoted identity plus explicit notes,
- or refresh one side after an honest reduction was recorded.

Rebuild may not:

- silently overwrite unresolved mismatches,
- silently discard richer structure from one side,
- or treat one backend as globally authoritative by file format alone.

## 6. Verification

After rebuild, verify at minimum:

- shared promoted id,
- source anchors,
- assumptions,
- regime limits,
- warning or caveat status,
- unresolved boundaries,
- and any recorded honest reduction.

## 7. One-sided materialization

Sometimes only one paired realization exists.

That is allowed, but:

- the missing realization remains backend debt if it matters for the current
  work,
- the available side must not pretend the pair is complete,
- and later rebuild must keep the same promoted identity rather than inventing
  a second object silently.

## 8. Relation to canonical `L2`

This maintenance protocol is downstream of canonical `L2`.

It does not replace:

- promotion packets,
- canonical units,
- canonical edges,
- or provenance records.

It governs how paired downstream backends stay aligned with those authoritative
surfaces.
