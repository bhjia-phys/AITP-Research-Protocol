# AITP L3-L4 Iterative Verify Loop Protocol

Status: draft working doctrine

## Decision

AITP should allow a Ralph-like iterative loop for bounded `L3-L4` work.

But this loop should be:

- conditional,
- bounded,
- artifact-driven,
- and able to exit into `L0`, `L2`, or human review when local iteration is no
  longer the honest next move.

Short form:

- use iterative loops for bounded refinement and verification
- do not turn all of AITP into one endless loop

## Why This Document Exists

Some research work is best handled by repeated short cycles:

- try,
- inspect,
- classify failure,
- update,
- retry.

That is especially true for bounded `L3-L4` tasks such as:

- benchmark mismatch refinement,
- proof-obligation closure,
- contradiction-resolution subproblems,
- code-backed validation loops,
- execution-result review and reroute.

AITP needs a formal way to support that behavior without collapsing into blind
iteration.

## 1. Scope

This protocol applies only to bounded tasks inside:

- `L3`
- `L4`

It does not replace:

- early idea discussion,
- broad literature scouting,
- large-scale topic reframing,
- promotion,
- publication.

## 2. Entry Conditions

AITP may enter an iterative verify loop only when all of the following are
true:

1. the objective is narrow enough to be stated explicitly,
2. the expected output of one iteration is bounded,
3. a concrete completion check exists,
4. failure can produce explicit feedback,
5. the task is not obviously blocked by missing `L0` or missing `L2`,
6. the operator is not waiting on a real route-changing question.

If any of these are false, do not enter the loop.

## 3. Typical Valid Uses

Valid `L3-L4` iterative loop targets include:

- refine one derivation packet until the current proof obligation set closes
- debug one benchmark mismatch until the current route is either validated or
  explicitly blocked
- compare one contradiction pair until the mismatch is classified
- iterate one code-backed validation patch until the current bounded benchmark
  either passes or fails honestly
- re-run one selected validation route after explicit feedback

## 4. Typical Invalid Uses

Do not use this loop for:

- deciding what the research question should be
- free-form new-idea generation
- broad literature exploration
- whole-topic "keep going until done"
- promotion or writeback itself
- publication drafting

## 5. Required Loop Contract

Each iterative loop should materialize at least:

- `loop_objective`
- `unit_of_iteration`
- `completion_check`
- `failure_classifier`
- `max_iterations`
- `current_iteration`
- `iteration_receipts`
- `exit_reason`

These may live inside an existing runtime artifact or a dedicated loop artifact,
but they must be durable.

## 6. Iteration Steps

Each iteration should follow this shape:

1. Load only the current bounded objective and the minimum relevant artifacts.
2. Execute one bounded unit of work.
3. Write the resulting artifacts or failure evidence.
4. Run the completion check.
5. If incomplete, classify the failure.
6. Choose one of:
   - local retry,
   - backedge to `L0`,
   - consult `L2`,
   - human checkpoint,
   - hard stop.

The loop must not silently continue after a failure classification that already
implies a different route.

## 7. Failure Classification

Failures should be classified into at least these families:

- `local_refinement_needed`
- `blocked_by_missing_L0_source`
- `blocked_by_missing_L2_memory`
- `blocked_by_execution_lane_choice`
- `blocked_by_human_decision`
- `blocked_by_resource_limit`
- `hard_failure`

Only the first one should default to another local loop iteration.

## 8. Backedge Policy

An iterative loop must exit to `L0` when the real blocker is:

- missing citation,
- missing source,
- missing definition anchor,
- missing prior-work comparison,
- missing derivation anchor.

An iterative loop must exit to `L2` consultation when the real blocker is:

- missing reusable method memory,
- missing warning note,
- missing bridge note,
- missing terminology alignment,
- missing prior validated route capsule.

An iterative loop must not keep retrying locally once such a blocker is known.

## 9. Human Checkpoint Policy

The loop must ask the human when:

- the execution lane is still materially open,
- the next step changes cost or trust significantly,
- multiple adjudication routes remain live,
- or the loop has reached its bounded retry limit without an honest automatic
  reroute.

Human checkpoints should appear at route boundaries, not after every failed
iteration.

## 10. Fresh Session Policy

Fresh-session iteration is allowed when it helps avoid context pollution.

But it is not required for every loop.

The rule is:

- if reusing the same session would mainly accumulate noise, prefer a fresh
  bounded pass
- if the current local context is still small and coherent, reuse is acceptable

The important invariant is not fresh session by itself.
It is durable state between iterations.

## 11. Completion Rule

A loop may end in only one of these ways:

- `completed`
- `blocked_to_L0`
- `blocked_to_L2`
- `blocked_to_human`
- `stopped_by_limit`
- `hard_failed`

"The model feels done" is not a valid completion signal.

## 12. Relationship To Mode

This protocol is not a top-level replacement for AITP modes.

It is a conditional submode inside:

- `explore`
- `verify`

Most often it should be entered from `verify`.

## 13. Relationship To Intelligence Preservation

This loop exists partly to preserve effective model intelligence.

It helps by:

- reducing context pollution,
- preventing fake closure,
- forcing explicit feedback,
- preserving bounded exploration,
- and making backedges explicit instead of implicit.

But it becomes harmful if:

- it is applied to vague or unbounded tasks,
- it is used when the real issue is missing `L0` or `L2`,
- or it becomes a ritualized retry engine.

## 14. Current Consequence

AITP should eventually support a real `L3-L4` iterative verify loop.

That loop should:

- be bounded,
- be artifact-driven,
- classify failures explicitly,
- support fresh-session passes when useful,
- and route out to `L0`, `L2`, or human checkpoints when local iteration stops
  being honest.

That is the intended Ralph-like role inside AITP.
