# Phase 2: Steering And Checkpoint Durability - Context

**Gathered:** 2026-03-31
**Status:** Retroactively completed
**Mode:** Brownfield reconciliation from completed working-tree changes

<domain>
## Phase Boundary

Make sure a true human steering answer does not stop at "checkpoint answered".
If the answer expresses continue/branch/redirect semantics, the runtime must
materialize durable steering artifacts and refresh the bounded route.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Keep ordinary checkpoint answers lightweight.
- Only materialize steering artifacts automatically for checkpoint kinds whose
  answers genuinely change route semantics.
- Reuse existing steering materialization paths instead of creating a second
  answer-to-steering system.

</decisions>

<specifics>
## Specific Ideas

- Extend `answer_operator_checkpoint()` rather than reworking the whole loop.
- Cover redirect-style answers with an end-to-end service test.

</specifics>
