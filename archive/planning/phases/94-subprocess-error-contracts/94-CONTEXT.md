# Phase 94: Subprocess Error Contracts - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.54`

<domain>
## Phase Boundary

Open `v1.54` by locking the subprocess failure contract so operator-facing
errors keep command and return-code context.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- use one shared subprocess failure formatter instead of duplicating string
  assembly in each caller
- guard both generic service execution and migrate-local-install with focused
  tests

</decisions>

---

*Phase: 94-subprocess-error-contracts*
*Context captured on 2026-04-11 after Phase 94 implementation and verification*
