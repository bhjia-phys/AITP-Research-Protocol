# Phase 92: Registry And Current-Topic Path Normalization - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Second implementation phase for `v1.53`

<domain>
## Phase Boundary

Continue `v1.53` by making active-topics and current-topic runtime state
serialize repo-relative topic roots while keeping old absolute-path registry
rows readable.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- normalize `runtime_root` on write for both `active_topics` and
  `current_topic`
- keep a dedicated helper module for runtime-path resolution so
  `aitp_service.py` stays inside the maintainability watch budget
- preserve backward compatibility by resolving both absolute and relative path
  rows on read

</decisions>

---

*Phase: 92-registry-and-current-topic-path-normalization*
*Context captured on 2026-04-11 after Phase 92 implementation and verification*
