# Phase 187.1 Summary: Retrieval And Consultation Usefulness Evaluation

Phase `187.1` converted the Jones corpus growth result into a bounded
usefulness evaluation against a six-question gold set.

## What changed

- created a bounded Jones gold-question set covering backbone, supporting
  theorem, proof-fragment, limitation, out-of-scope, and concept-neighborhood
  queries
- fixed explicit usefulness criteria:
  - `useful`
  - `partial`
  - `weak`
- evaluated the current compiled Jones corpus with `aitp consult-l2`
- wrote the durable evaluation record to
  `.planning/phases/187.1-retrieval-and-consultation-usefulness-evaluation/evidence/gold_question_evaluation.md`

## Results

- `4` questions rated `useful`
- `2` questions rated `partial`
- `0` questions rated `weak`

Useful:

- finite-dimensional backbone retrieval
- supporting theorem retrieval
- proof-fragment retrieval
- full Chapter 4 out-of-scope retrieval

Partial:

- stronger-theorem limitation retrieval
- concept-neighborhood retrieval

## Honest interpretation

The current Jones-local corpus is now genuinely usable for bounded retrieval and
consultation, but not yet uniformly well-ranked across all query types.

The most visible residual bias is:

- warning-style limitation questions can still over-rank theorem-facing packet
  material
- concept-neighborhood questions can still over-rank proof fragments before the
  concept layer itself

## Handoff

Phase `187.2` should now write one honest capability report from:

- the corpus-growth delta
- the gold-question evaluation
- the residual ranking weaknesses
