# Phase 41: Collaborator Routing And Human Override - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `40` task-type-by-lane guidance

<domain>
## Phase Boundary

Connect the new guidance surfaces to collaborator routing and human override so
the operator can steer AITP through explicit runtime surfaces rather than only
through opaque control-note habits.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Keep collaborator memory noncanonical.
- Use collaborator preferences and human override sources as routing guidance,
  not as automatic truth.
- Expose the routing surface explicitly in runtime and markdown before trying
  to make it fully drive queue generation.

</decisions>

<code_context>
## Existing Code Insights

- `task_type_lane_guidance` now exists after Phase `40`.
- collaborator memory is already available as noncanonical steering context.
- runtime already has editable surfaces and `must_read_now`, but no dedicated
  collaborator-routing summary.

</code_context>

<specifics>
## Specific Ideas

- Add `collaborator_routing_guidance.json/md`
- Include:
  - current task type and lane
  - collaborator preferred lanes
  - alignment status
  - override surfaces the human should edit to redirect the route
  - routing summary / recommended steering action
- When collaborator preference and active route materially disagree, surface the
  routing note in `must_read_now`.

</specifics>
