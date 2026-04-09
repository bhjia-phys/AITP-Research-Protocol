# Phase 36: Consultation And Human-Facing Memory Maps - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `35` graph-activation visibility

<domain>
## Phase Boundary

Improve `L2` consultation so the same seeded canonical graph becomes more
useful both to the model and to the human operator, without letting the two
views drift apart semantically.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Human-facing and AI-facing consultation must remain derived from the same
  selected canonical identities and warning boundaries.
- The next step should improve usability, not invent a second authority layer.
- Memory maps should expose graph neighborhood, warnings, and staged tensions
  in a form a working physicist can scan quickly.

### Agent discretion

- The first Phase `36` slice may focus on latest-consultation memory maps
  rather than on a full wiki browser if that yields a stronger daily-use
  surface sooner.

</decisions>

<code_context>
## Existing Code Insights

- `consult_topic_l2()` already produces machine-facing retrieval refs and a
  human-readable summary note.
- Runtime `l2_memory` already exposes the latest consultation summary and now
  also exposes canonical graph activation status.
- There is still no dedicated human-facing memory-map artifact that makes the
  selected primary hits, expanded neighbors, warning notes, and staged tensions
  easy to inspect as one coherent snapshot.

</code_context>

<specifics>
## Specific Ideas

- Add a derived latest-consultation memory map in JSON and Markdown.
- Include:
  - primary canonical hits
  - expanded graph neighbors
  - warning notes
  - staged hits
  - graph activation summary
- Surface that artifact path in both consultation outputs and runtime
  `l2_memory`.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md`
- `research/knowledge-hub/README.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- `H-plane` continue/update/stop semantics remain Phase `37`.
- Full Obsidian/wiki-style graph navigation can remain a later extension if the
  first memory-map slice already gives clear daily-use value.

</deferred>
