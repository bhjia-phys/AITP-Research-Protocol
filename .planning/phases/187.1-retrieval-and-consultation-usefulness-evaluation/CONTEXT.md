# Phase 187.1 Context: Retrieval And Consultation Usefulness Evaluation

## Phase Identity

- Phase: `187.1`
- Milestone: `v2.13` `L2 Content Quality Baseline`
- Requirements: `L2Q-02`, `L2Q-03`
- Axis: Axis 4 (human evidence) + Axis 3 (evaluation recording)

## Locked Inputs

Use the Jones-local corpus produced by Phase `187`.

Required starting artifacts:

- `.planning/phases/187-real-direction-corpus-growth-slice/evidence/baseline/current_corpus_snapshot.md`
- `.planning/phases/187-real-direction-corpus-growth-slice/evidence/post-growth/post_growth_snapshot.md`
- `.planning/phases/187-real-direction-corpus-growth-slice/HANDOFF-TO-187.1.md`
- `research/knowledge-hub/canonical/compiled/workspace_graph_report.md`
- `research/knowledge-hub/canonical/compiled/derived_navigation/index.md`

## Evaluation Goal

This phase does not grow the corpus further unless evaluation proves that the
current Jones corpus is still too thin to measure honestly.

The job here is to measure usefulness, not to keep "improving" the corpus until
all questions look perfect.

## Gold-Question Rule

Use a small bounded question set derived from the `187` handoff.

Each question must name:

- query text
- retrieval profile
- expected answer shape
- gold anchor unit ids

## Usefulness Criteria

Use these verdicts only:

- `useful`
  - at least one gold anchor appears in the top-2 primary hits
  - no unrelated non-Jones hit appears in the top-3
  - the hit set is strong enough that a human could answer without raw-source
    rereading
- `partial`
  - at least one gold anchor appears in the top-5
  - but ranking or answer-shape is still misaligned with the query intent
- `weak`
  - no gold anchor appears in the top-5, or unrelated material dominates the
    answer surface

## Current Hypothesis

The enriched Jones corpus should now be good enough to answer bounded
theorem-structure and proof-support questions usefully.

The most likely remaining weakness is query-type sensitivity:

- limitation questions may still over-rank theorem cards before warning notes
- concept-neighborhood questions may still over-rank proof fragments before
  concept units

## Non-Goals

- do not widen the corpus again in this phase
- do not redesign retrieval ranking globally in this phase
- do not claim "AITP retrieval is generally solved" from one bounded direction
