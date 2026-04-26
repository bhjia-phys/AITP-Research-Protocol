# Phase 44: Contradiction And Notation Alignment - Context

**Gathered:** 2026-04-10
**Status:** Ready for execution
**Mode:** Brownfield continuation after Phase `43`

<domain>
## Phase Boundary

Strengthen `L1` intake so contradiction candidates and notation-alignment
tension become durable intake artifacts instead of remaining implicit in source
prose.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- build on the stronger `l1_source_intake` structure landed in Phase `43`
- reuse existing source-intelligence helpers for contradiction and notation
  detection instead of inventing a second parser stack
- keep this phase focused on intake honesty and conflict surfacing, not runtime
  read-path expansion yet

</decisions>

<code_context>
## Existing Code Insights

- `source_intelligence.py` already contains dormant contradiction and notation
  candidate detectors that are not yet wired into intake materialization
- `topic_shell_support.py` is the current home of research-contract assembly and
  is the right place to persist new intake-side conflict signals
- `kernel_markdown_renderers.py` can expose the new intake conflict surfaces in
  the human-readable research-question contract note without pushing more logic
  back into `aitp_service.py`

</code_context>
