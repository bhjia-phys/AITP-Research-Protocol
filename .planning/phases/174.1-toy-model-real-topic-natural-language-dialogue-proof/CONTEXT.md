# Phase 174.1: Toy-Model Real-Topic Natural-Language Dialogue Proof - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove that the public AITP front door can steer the closed toy-model baseline
through one real natural-language dialogue without hidden seed state or
authority drift.

</domain>

<decisions>
## Implementation Decisions

### Real-topic target
- Use the user-requested toy-model direction centered on the HS-like /
  Haldane-Shastry chaos-window route.
- Keep the real dialogue tied to the already-closed bounded positive toy-model
  route from `v1.98`, rather than reopening wider finite-size or
  thermodynamic-limit claims.

### Honesty constraints
- The run must start from a fresh natural-language toy-model request and use
  the public entry surfaces first.
- Do not bypass the front door by seeding hidden runtime or source-layer state.
- Keep the route bounded to the robust finite-size positive core, not to the
  excluded shoulder or exact-HS negative comparator.

### the agent's Discretion
The exact wording may vary, but it must remain recognizably in the HS-like
toy-model lane and stay bounded to the already-proved positive baseline.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_hs_positive_l2_acceptance.py` is the bounded positive-L2 toy-model
  baseline from `v1.98`.
- `claim:hs-like-chaos-window-finite-size-core` is the canonical positive
  toy-model route already known to land honestly in authoritative `L2`.

### Established Patterns
- Real-topic E2E tests should begin from natural language and then prove that
  the route remains bounded and honest all the way through the runtime
  surfaces.
- This milestone is not about widening the HS-like theory claim; it is about
  proving real natural-language steering fidelity for the closed toy-model
  baseline.

### Integration Points
- Phase `174.1` establishes the toy-model leg of the three-lane dialogue E2E.
- Phase `174.2` will mirror the same philosophy for the first-principles lane
  and then write the cross-lane report.

</code_context>

<specifics>
## Specific Ideas

- Likely natural-language prompt family:
  “Help me study a bounded HS-like chaos-window toy-model result and keep the
  route tied to the already-proved finite-size positive core.”
- The proof should record where the front door still asks for human steering
  and where it can proceed mechanically.

</specifics>

<deferred>
## Deferred Ideas

- Do not expand this phase into the first-principles lane.
- Do not reopen positive-L2 closure mechanics already settled in `v1.98`.

</deferred>
