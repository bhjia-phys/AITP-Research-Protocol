# Verification Bridge Protocol

This file defines the public AITP contract between proof-grade theoretical
knowledge and closed-loop verification work.

Verification here is broader than numerical testing.
It includes any bounded external lane that checks a claim honestly and returns
durable evidence.

## 1. Why this exists

Theory-heavy work often fails at the handoff point:

- proofs are written but no validation route is selected,
- an execution route is selected but its return contract is vague,
- external evidence arrives but is not connected back to the theorem family.

This protocol makes that bridge explicit.

## 2. Verification lane types

Projects may define concrete lane names, but common AITP bridge families are:

- theory-formal proof review,
- symbolic or algebraic derivation replay,
- bounded numerical toy-model check,
- code-backed algorithm or simulation check,
- source-consistency audit,
- regression-suite question audit.

The bridge contract must say which lane is active and why it is appropriate for
the current claim.

## 3. Minimal bridge content

Every selected verification route should state:

- the bounded claim or family under review,
- the chosen lane,
- required prerequisite artifacts,
- what counts as success, partial success, or failure,
- what evidence files must be returned,
- what writeback is allowed after return,
- what remains out of scope even if the check passes.

## 4. Non-equivalence rule

A successful bounded verification result does not automatically mean:

- the whole theorem family is complete,
- all cited prerequisites are recovered,
- the claim is ready for unrestricted reuse,
- or the result deserves promotion.

Verification returns evidence.
Promotion remains a separate protocol-governed decision.

## 5. Runtime trigger handshake

The runtime progressive-disclosure bundle names this path through:

- `verification_route_selection`

When that trigger fires, the next agent must open:

- `VERIFICATION_BRIDGE_PROTOCOL.md`,
- the selected validation route artifact,
- the execution task or audit handoff artifact,
- any returned execution result and its receipts.

If the route is theory-formal rather than numerical, the same trigger still
applies.
The selected lane simply points to theory-packet and proof-obligation evidence
instead of a numeric benchmark.

## 6. Result categories

Returned bridge evidence should remain honest about outcome:

- pass
- partial
- fail
- blocked

Projects may refine these, but must preserve a non-promotional partial outcome.

## 7. Script boundary

Scripts may:

- select from already-declared lanes,
- scaffold execution tasks,
- ingest returned artifacts,
- materialize route summaries and receipts.

Scripts may not decide:

- that a partial route result is scientifically decisive,
- that a missing prerequisite can be ignored,
- or that route success alone justifies `L2` promotion.

That judgment belongs to the surrounding validation and promotion surfaces.
