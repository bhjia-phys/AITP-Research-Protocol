# Phase 42: Source Identity And Citation Graph - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing `v1.35`

<domain>
## Phase Boundary

Strengthen `L0` by giving sources more durable identity across topics and by
exposing better citation/source-neighbor signals.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Start with explicit, bounded source-identity and citation metadata rather
  than a giant graph backend.
- Prefer source intelligence that later layers can actually read and use.
- Keep this phase focused on `L0`; deeper `L1` intake structure follows in the
  next phases.

</decisions>

<code_context>
## Existing Code Insights

- AITP already has minimal source-fidelity and citation-graph summary signals.
- Those signals are still too weak for real cross-topic literature reuse.
- Runtime and intake already know how to render `L0` projections once the
  underlying fields become stronger.

</code_context>
