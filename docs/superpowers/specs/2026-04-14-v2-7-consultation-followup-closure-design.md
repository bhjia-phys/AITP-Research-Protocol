# AITP v2.7 Consultation-Followup Selection Closure Design

Status: working design

Date: 2026-04-14

## Goal

Close the first post-review consultation gap after `v2.6` by turning
`consultation_followup` from a visible but non-executable prompt into a real,
bounded runtime step that:

- runs one topic-local `consult-l2`,
- records durable consultation receipts,
- selects exactly one bounded staged candidate when the evidence is good
  enough,
- and advances `next` / `status` onto that chosen candidate instead of
  repeating generic consultation language forever.

## Problem

`v2.6` repaired route wording, but not route closure.

Today the system can already:

- append `consultation_followup` in `orchestrate_topic.py`,
- show it on public `next` / `status`,
- and run `consult-l2` successfully when called directly.

But the loop still dead-ends because `topic_loop -> execute_auto_actions()`
has no `consultation_followup` handler.

That leaves one structural failure:

- the surface points to consultation,
- the loop cannot execute consultation,
- no durable selected-candidate artifact is written,
- and the same topic remains stuck on the same bounded summary.

## Boundary

This milestone stays narrow.

It closes only the first consult-and-select handoff after staged-`L2` review.
It does **not**:

- auto-run deeper validation,
- auto-promote to canonical `L2`,
- auto-split candidates,
- or auto-select from unrelated global canonical hits.

## Required Outcome

After a fresh topic reaches the `v2.6` state:

1. the loop may auto-run one bounded consultation follow-up,
2. that consultation must be recorded durably,
3. the system must either:
   - select one bounded topic-local staged candidate honestly, or
   - record an explicit no-selection outcome,
4. and `next` / `status` must stop repeating the generic consultation prompt
   once a bounded candidate has been selected.

## Chosen Approach

### Add a dedicated selection artifact

Introduce one new runtime artifact pair under the topic runtime root:

- `consultation_followup_selection.active.json`
- `consultation_followup_selection.active.md`

This artifact records:

- which query was used,
- which retrieval profile was used,
- which consultation receipt/result was produced,
- whether a bounded candidate was selected,
- which staged candidate won,
- and why it was selected.

### Make `consultation_followup` auto-runnable only for this narrow lane

For `v2.7`, `consultation_followup` becomes auto-runnable only when:

- runtime mode is still exploratory literature work,
- topic-local staged entries already exist,
- the route has already advanced past static staged-`L2` review,
- and no accepted consultation-followup selection artifact already exists for
  the current consult cycle.

## Query And Retrieval Policy

The auto step must not invent an unconstrained query.

It should derive a bounded query in this order:

1. current research-question title or statement,
2. topic title,
3. de-slugified topic slug.

The retrieval profile should stay conservative:

- `l1_provisional_understanding`
- `include_staging=True`
- small primary-hit budget
- topic-local staged rows preferred over broad canonical wandering

## Candidate Selection Rule

`v2.7` should auto-select candidates only from topic-local staged evidence.

Selection policy:

1. prefer staged rows whose `topic_slug` matches the current topic,
2. preserve consult order as final tie-breaker,
3. choose at most one candidate,
4. if no topic-local staged row exists, record `status = no_selection` and do
   not silently fall back to unrelated canonical memory.

That is the honesty boundary of the milestone.

## New Runtime Transition

The new bounded transition is:

`consultation_followup`
→ auto-run one topic-local `consult-l2(record_consultation=True)`
→ write consultation-followup selection artifact
→ advance to one new manual bounded action:

`Review the selected staged candidate <id> and decide whether to split, validate, or promote it before deeper execution.`

That new action remains human-visible and non-auto-runnable in `v2.7`.

## Files And Responsibilities

### New helper module

Create:

- `research/knowledge-hub/knowledge_hub/consultation_followup_support.py`

Responsibilities:

- derive bounded query text,
- decide retrieval defaults,
- choose one bounded staged candidate from consultation payload,
- build the durable selection payload,
- render the markdown note.

### Service integration

Modify:

- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/auto_action_support.py`

Responsibilities:

- run the consultation-followup auto step,
- call `consult_l2(record_consultation=True)`,
- materialize the selection artifact,
- return a durable result to the auto-action loop.

### Queue and routing integration

Modify:

- `research/knowledge-hub/runtime/scripts/orchestrate_topic.py`
- `research/knowledge-hub/runtime/scripts/orchestrator_contract_support.py`

Responsibilities:

- mark the consult-followup step auto-runnable in the narrow `v2.7` lane,
- suppress the generic consult prompt once a selection artifact already exists,
- append the candidate-specific bounded next action after a successful
  selection.

### Runtime state and read surfaces

Modify:

- `research/knowledge-hub/runtime/scripts/sync_topic_state.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`

Responsibilities:

- expose a pointer to the new selection artifact,
- foreground that artifact in `must_read_now` when it becomes the active
  bounded object,
- keep `next` / `status` aligned on the candidate-specific follow-up summary.

## Artifact Shape

The selection artifact should include at least:

- `topic_slug`
- `run_id`
- `status` (`selected` or `no_selection`)
- `query_text`
- `retrieval_profile`
- `consultation_index_path`
- `consultation_result_path`
- `selected_candidate_id`
- `selected_candidate_title`
- `selected_candidate_path`
- `selected_candidate_trust_surface`
- `selected_candidate_topic_slug`
- `selection_reason`
- `updated_at`
- `updated_by`

## Surface Consequences

After a successful `v2.7` consult-followup run:

- `loop` should show one completed auto action for consultation follow-up,
- `next.selected_action_type` should no longer be `consultation_followup`,
- `next.selected_action_summary` and `status.selected_action_summary` should
  name the chosen candidate,
- and runtime pointers should expose the selection artifact path.

After a no-selection outcome:

- the consultation-followup receipt must still exist,
- the selection artifact must say `no_selection`,
- and the route must remain honest rather than fabricating a candidate.

## Testing Standard

The milestone is successful only if all of the following are proven:

1. One isolated fresh-topic replay reaches `v2.6`, auto-runs consultation
   follow-up, writes the selection artifact, and advances `next` / `status` to
   a candidate-specific summary.
2. The same isolated replay still records consultation receipts durably.
3. Existing `v2.4`, `v2.5`, and `v2.6` acceptance slices still pass.
4. A no-selection path is either tested directly or mechanically guarded so
   the runtime cannot fabricate a candidate.

## Non-Goals

This design does not include:

- automatic validation-route choice for the selected candidate,
- statement compilation,
- Lean bridge preparation,
- promotion request generation,
- or global consultation-query learning.

## One-Line Doctrine

`v2.7` should make post-review consultation executable and durable, but stop at
one honestly chosen staged candidate rather than pretending that consultation
already solved deeper execution.
