# Phase 39: Task-Type-Aware Interaction Bias - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `38` task-type runtime seeding

<domain>
## Phase Boundary

Use explicit `task_type` to shape runtime interaction posture so open
exploration and conjectural bridge work are not treated the same way as
target-driven execution.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Keep hard trust gates untouched.
- Use `task_type` as a first-class signal for interaction posture rather than
  relying only on keyword-level exploration cues.
- Blocking checkpoints, pending-decision blockers, and idea-clarification gates
  must still override task-type freedom.

</decisions>

<code_context>
## Existing Code Insights

- `task_type` is now present in runtime and topic artifacts after Phase `38`.
- `_derive_interaction_contract()` still decides mostly through blockers,
  updates, and request-shape cues.
- `free_explore` already exists, so this phase is mainly about routing
  discipline rather than new schema families.

</code_context>

<specifics>
## Specific Ideas

- `open_exploration` should default to `free_explore` when no stronger gate is
  active.
- `conjecture_attempt` should be able to stay exploratory when the request is
  still route-shaping rather than execution-hard.
- `target_driven_execution` should keep preferring ordinary continuation unless
  another gate fires.

</specifics>
