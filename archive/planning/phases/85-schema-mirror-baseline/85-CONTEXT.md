# Phase 85: Schema Mirror Baseline - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.51`

<domain>
## Phase Boundary

Open `v1.51` by restoring the installable runtime mirror for
`promotion-or-reject.schema.json` and locking the `follow_up_actions` contract
against future drift.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- keep the root `schemas/` copy as the public authority
- add an explicit runtime mirror under `research/knowledge-hub/schemas/`
- guard the mirror with an isolated schema-tree contract test

</decisions>

---

*Phase: 85-schema-mirror-baseline*
*Context captured on 2026-04-11 after Phase 85 implementation and verification*
