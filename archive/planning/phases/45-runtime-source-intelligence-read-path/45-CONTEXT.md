# Phase 45: Runtime Source-Intelligence Read Path - Context

**Gathered:** 2026-04-10
**Status:** Ready for execution
**Mode:** Brownfield continuation after Phase `44`

<domain>
## Phase Boundary

Expose the stronger `L0/L1` source intelligence through runtime/topic read paths
so later layers and human operators can actually consume the source-identity,
citation-neighbor, assumption, regime, contradiction, and notation-tension
signals without reopening raw source files.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- treat this as read-path work, not another intake parser phase
- reuse the existing `build_source_intelligence(...)` output and the current
  `l1_source_intake` contract instead of inventing parallel read-path payloads
- prioritize runtime bundle, topic status, and human-readable runtime note
  surfaces over new backend/storage work

</decisions>

<code_context>
## Existing Code Insights

- `source_intelligence.py` already computes canonical source ids, citation
  edges, and source-neighbor signals but those outputs are not yet visible in
  runtime read surfaces
- `runtime_bundle_support.py` already carries `l1_source_intake` into the bundle
  but still under-renders the stronger source-intelligence signals in the human
  runtime note
- `topic_shell_support.py` now owns the conflict-aware `l1_source_intake`
  structure and is the natural place to hand the stronger source-intelligence
  payload into runtime read paths

</code_context>
