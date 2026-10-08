# Plans for a stage of work

A plan says how an agreed stage of work will proceed; the main note says what is known
and why. Keep the two apart, so that the argument does not fill with phases and the plan
does not pretend to be a result.

## Where a plan lives

A detailed phased plan is a separate, reviewable document. Reuse the topic's `plan/`
folder when it exists; otherwise write a supporting note named for its stage, for example
`otoc-finite-size-plan.md`, not `plan-v3.md`, and create `plan/` only when several
substantial plans justify it. The main note's next step links the active plan in one
sentence, and the plan links back to the question it serves. A plan of a few routine
actions can stay in that sentence.

## What a plan contains

- The stage objective, stated as the question it advances in the main note.
- Phases, each with its inputs, its output, its acceptance condition and what a failure
  would mean. Mark which phases can run in parallel and which depend on others.
- For calculations: the cases and why each was chosen, and the tolerances, fixed before
  any result is seen, as in [computational work](../../aitp-research/references/computational-work.md#design-the-experiment-before-running-it).
- Expected compute, memory and time for expensive phases.
- Stop and reconsider conditions: what would make the stage pointless or change it.
- Choices that still need the researcher.

## Review before running

Explain and review a substantial phased plan before execution, honouring any review the
researcher reserves for themselves or for another model. Check that each acceptance
condition can actually discriminate, and that complete success of the stage would advance
the main question. Judge another model's findings on the evidence, as
[aitp-verify](../../aitp-verify/SKILL.md#assess-another-models-review) describes.
Drafting a plan or receiving a favourable review does not authorize executing it; an
existing reviewed authorization carries across its phases.

## Keep the plan current, then retire it

Revise a retained plan when its objective, dependencies, acceptance conditions or agreed
next action change, and say why. Link each phase's evidence and state its outcome against
the agreed acceptance, failure or stopping condition; a link alone does not establish
completion. Run reports keep job states. Completing execution, accepting a result
scientifically and the researcher's confirmation remain distinct. When the stage ends, record its outcome and reason at the top (completed,
stopped or superseded, with a link to the resulting account), remove it from the main
note's active next step, and integrate its scientific implication into the backbone.
Link another plan only when further work has actually been chosen. Retired plans stay
reachable as history.
