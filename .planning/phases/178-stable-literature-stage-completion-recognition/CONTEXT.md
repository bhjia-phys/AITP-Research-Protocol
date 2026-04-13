# Phase 178 Context: Stable Literature-Stage Completion Recognition

## Why this phase exists

`v2.3` repaired post-registration route selection, but the first fresh-topic
L1->L2 follow-through still had one remaining coherence gap: after
`literature_intake_stage` completed once, the route could requeue the same
action as though staged `L2` had not changed anything.

## Bounded goal

Make one completed fresh-topic `literature_intake_stage` durable enough that:

- the same candidate set is recognized as already staged
- the queue no longer repeats the identical L1->L2 action forever
- the next bounded action advances onto staged-`L2` review

## Constraints

- stay within provisional staged `L2`; do not overclaim promotion or
  authoritative writeback
- preserve the current fresh-topic first-use baseline from `v2.3`
- keep the fix durable across runtime queue regeneration, not only inside one
  in-memory service call
