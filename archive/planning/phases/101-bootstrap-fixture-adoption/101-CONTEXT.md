# Phase 101: Bootstrap Fixture Adoption - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Second implementation phase for `v1.56`

<domain>
## Phase Boundary

Continue `v1.56` by adopting the shared temp-kernel helper in representative
integration-style tests.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- adopt the helper in three representative test files that previously hand-rolled
  temp-kernel bootstrap logic
- keep bootstrap-path import behavior explicit in each file so test discovery
  stays predictable

</decisions>

---

*Phase: 101-bootstrap-fixture-adoption*
*Context captured on 2026-04-11 after Phase 101 implementation and verification*
