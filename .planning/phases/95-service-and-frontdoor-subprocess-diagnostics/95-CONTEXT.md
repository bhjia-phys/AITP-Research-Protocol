# Phase 95: Service And Frontdoor Subprocess Diagnostics - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Second implementation phase for `v1.54`

<domain>
## Phase Boundary

Continue `v1.54` by routing service-level and migrate-local-install subprocess
failures through one shared diagnostic formatter.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- add a focused helper module rather than bloating `aitp_service.py`
- improve `AITPService._run()` and `frontdoor_support.migrate_local_install()`
  first; wider subprocess adoption can be a later slice if needed

</decisions>

---

*Phase: 95-service-and-frontdoor-subprocess-diagnostics*
*Context captured on 2026-04-11 after Phase 95 implementation and verification*
