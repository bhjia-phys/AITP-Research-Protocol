# Phase 43: Assumption And Regime Intake - Context

**Gathered:** 2026-04-10
**Status:** Ready for execution
**Mode:** Brownfield continuation after Phase `42`

<domain>
## Phase Boundary

Strengthen `L1` intake so assumptions, regimes, and reading-depth structure are
explicit enough for later `L3/L4` work to trust.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- build on the stronger `L0` source identity and citation signals from Phase `42`
- keep this phase centered on `L1` intake quality rather than contradiction or notation alignment
- prefer bounded, durable intake fields over broad prose summaries

</decisions>

<code_context>
## Existing Code Insights

- the remediation branch already has extracted source/intake/runtime helpers
- `source_distillation_support.py` is the primary home for source-backed intake shaping
- runtime bundle and topic-shell surfaces already know how to expose richer `L1`
  structure once the intake payload becomes stronger

</code_context>
