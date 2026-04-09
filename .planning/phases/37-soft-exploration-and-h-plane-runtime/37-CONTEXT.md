# Phase 37: Soft Exploration And H-Plane Runtime - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `36` consultation memory-map closure

<domain>
## Phase Boundary

Preserve model intelligence during early idea formation by distinguishing
bounded free exploration from ordinary route continuation, while keeping hard
gates for validation, writeback, and blocking human checkpoints.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Do not relax trust, validation, or writeback rules.
- Add `free_explore` as a runtime interaction posture rather than a new
  epistemic layer.
- Record exploration state in a lightweight runtime carrier instead of forcing
  immediate durable layer closure.

### Agent discretion

- The first Phase `37` slice may use bounded heuristic cues for exploration
  detection if they are explicit and testable.

</decisions>

<code_context>
## Existing Code Insights

- Runtime currently distinguishes only:
  - `silent_continue`
  - `non_blocking_update`
  - `checkpoint_question`
- `AITPService._derive_interaction_contract()` is the main decision surface.
- No `exploration_window` artifact currently exists.

</code_context>

<specifics>
## Specific Ideas

- Add `free_explore` to the runtime interaction contract.
- Add `runtime/topics/<topic_slug>/exploration_window.json`
- Add `runtime/topics/<topic_slug>/exploration_window.md`
- Surface the exploration window in the runtime bundle when active.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-09-aitp-soft-exploration-hard-trust-runtime-design.md`
- `docs/superpowers/specs/2026-04-08-aitp-research-scenario-and-layer-responsibility-freeze-design.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- More sophisticated task-type-aware exploration detection can wait for a later
  slice if the first bounded implementation already improves collaborator feel.

</deferred>
