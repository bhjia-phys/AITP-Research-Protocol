# Phase 40: Task-Type By Lane Guidance - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `39` task-type-aware interaction bias

<domain>
## Phase Boundary

Expose first reusable `task_type × lane` guidance surfaces so AITP can carry
different first-loop expectations for different kinds of theoretical-physics
work instead of only generic routing heuristics.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Add a dedicated runtime guidance surface rather than overloading
  `topic_skill_projection`, which is for mature reusable route memory.
- Start with bounded guidance templates, not a full orchestration engine.
- Keep the current runtime lane vocabulary visible, but normalize it into a
  higher-level lane family where needed.

### Agent discretion

- The first slice may expose guidance mainly through runtime/topic artifacts and
  markdown, without yet forcing new action-selection logic.

</decisions>

<code_context>
## Existing Code Insights

- `task_type` is now present in runtime and topic artifacts after Phase `38`.
- interaction posture already consults `task_type` after Phase `39`.
- There is still no explicit runtime surface that says, for example, how
  `open_exploration × formal_theory` should differ from
  `target_driven_execution × code_method`.

</code_context>

<specifics>
## Specific Ideas

- Add `task_type_lane_guidance.json/md` under the runtime topic root.
- Include:
  - task type
  - lane
  - normalized lane family
  - summary
  - L0/L1/L3/L4/L2 expectations
  - recommended first moves
  - human interaction bias
- Surface that guidance in the runtime bundle and runtime markdown.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-08-aitp-research-scenario-and-layer-responsibility-freeze-design.md`
- `.planning/backlog/999.42-task-type-by-lane-template-library/`

</canonical_refs>

<deferred>
## Deferred Ideas

- Human override coupling and collaborator-routing policy remain Phase `41`.
- Full automatic lane/task-type-driven queue generation is a later step.

</deferred>
