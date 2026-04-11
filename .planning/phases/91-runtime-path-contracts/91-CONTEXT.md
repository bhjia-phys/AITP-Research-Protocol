# Phase 91: Runtime Path Contracts - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.53`

<domain>
## Phase Boundary

Open `v1.53` by locking the runtime path contract so checked-in compatibility
artifacts and newly materialized current-topic state no longer leak
workstation-specific Windows paths.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- treat `runtime/topics/<topic_slug>` as the stable serialized form for
  `runtime_root`
- guard the checked-in `runtime/current_topic.{json,md}` fixture directly with
  a contract test

</decisions>

---

*Phase: 91-runtime-path-contracts*
*Context captured on 2026-04-11 after Phase 91 implementation and verification*
