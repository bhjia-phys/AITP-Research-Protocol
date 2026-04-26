# Phase 109: Runtime Compat Surface Prune Contract - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.59`

<domain>
## Phase Boundary

Open `v1.59` by locking the compatibility-surface pruning contract in service
tests.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- prune only compatibility surfaces that are already superseded by the primary
  read path
- block pruning when the corresponding primary surfaces are missing

</decisions>

---

*Phase: 109-runtime-compat-surface-prune-contract*
*Context captured on 2026-04-11 after Phase 109 implementation and verification*
