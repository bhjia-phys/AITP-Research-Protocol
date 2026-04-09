# Phase 38: Task-Type Runtime Seeding - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing `v1.34`

<domain>
## Phase Boundary

Seed the frozen `task_type` axis into runtime and topic artifacts so AITP can
explicitly distinguish exploratory, conjectural, and target-driven work.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Start with the minimal frozen set:
  - `open_exploration`
  - `conjecture_attempt`
  - `target_driven_execution`
- Make `task_type` visible before trying to fully optimize routing around it.
- Use bounded heuristic inference first, with later room for human override.

### Agent discretion

- The first slice may infer `task_type` from request text and current runtime
  context if that is explicit and testable.

</decisions>

<code_context>
## Existing Code Insights

- Runtime already infers `interaction_class` and has a bounded
  `free_explore` posture.
- Topic artifacts such as research contract, idea packet, and topic synopsis do
  not yet persist `task_type`.
- The scenario-freeze spec already defines the target categories and expected
  examples.

</code_context>

<specifics>
## Specific Ideas

- Add `task_type` to:
  - research contract
  - idea packet
  - active research contract in runtime bundle
  - topic synopsis
- Add a small inference helper from human request and active context.
- Make `free_explore` prefer `task_type == open_exploration` rather than only
  direct keyword cues.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-08-aitp-research-scenario-and-layer-responsibility-freeze-design.md`
- `.planning/backlog/999.38-task-type-axis-and-orchestration-templates/`

</canonical_refs>

<deferred>
## Deferred Ideas

- Full task-type-by-lane template library remains later phases.
- Human override UX and collaborator-routing coupling remain later phases.

</deferred>
