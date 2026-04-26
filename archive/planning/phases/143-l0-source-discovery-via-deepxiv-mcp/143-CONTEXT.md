# Phase 143: L0 Source Discovery Via DeepXiv MCP Integration - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the missing pre-registration discovery path in `L0`.

The phase should:

- let operators start from a natural-language search query instead of an
  already-known `arxiv_id`
- bridge search results into the existing `register_arxiv_source.py` path
- keep search as an external MCP dependency, not an embedded L0 protocol
  primitive

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Keep DeepXiv search outside `L0` core state and treat it as one
  external MCP-backed provider.
- **D-02:** Build one thin adapter into the existing registration path rather
  than replacing `register_arxiv_source.py`.
- **D-03:** Document a fallback chain so discovery remains usable if DeepXiv is
  unavailable.
- **D-04:** Keep the first scope bounded to search -> candidate evaluation ->
  registration; do not broaden into generic literature-automation features.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/L0_SOURCE_LAYER.md`
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`
- `.planning/phases/143-l0-source-discovery-via-deepxiv-mcp/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- broader non-arXiv search providers as first-class production routes
- large-scale literature triage beyond bounded source registration
- embedding any external search dependency into the `L0` core protocol

</deferred>

---

*Phase: 143-l0-source-discovery-via-deepxiv-mcp*
*Context gathered: 2026-04-12*
