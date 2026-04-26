# Phase 100: Shared Test Kernel Helper - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.56`

<domain>
## Phase Boundary

Open `v1.56` by introducing a shared temp-kernel helper for integration-style
tests that repeatedly bootstrap schemas, runtime schemas, and canonical assets.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- keep the helper at package-root test support level so test modules can import
  it after adding `research/knowledge-hub` to `sys.path`
- provide small focused copy/write helpers rather than one giant magic fixture

</decisions>

---

*Phase: 100-shared-test-kernel-helper*
*Context captured on 2026-04-11 after Phase 100 implementation and verification*
