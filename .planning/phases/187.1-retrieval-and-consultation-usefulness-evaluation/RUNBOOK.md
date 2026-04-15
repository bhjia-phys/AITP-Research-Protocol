# RUNBOOK: Phase 187.1 Retrieval And Consultation Usefulness Evaluation

## Purpose

Evaluate whether the bounded Jones-local corpus grown in Phase `187` is now
actually useful for retrieval and consultation.

## Commands

From repo root:

```bash
aitp consult-l2 --query-text "What is the finite-dimensional backbone for the current Jones von Neumann algebra route?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json
aitp consult-l2 --query-text "Which supporting theorem underlies the current Jones finite-product packet?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json
aitp consult-l2 --query-text "Which local proof fragments support the current Jones finite-product packet?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json
aitp consult-l2 --query-text "What limitation or non-goal remains around the stronger Jones product theorem route?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json
aitp consult-l2 --query-text "What remains out of scope relative to the full Chapter 4 type-I classification route?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json
aitp consult-l2 --query-text "Which concepts define the local Jones object neighborhood around the block centralizer packet?" --retrieval-profile l1_provisional_understanding --max-primary-hits 5 --json
```

## Expected success markers

- no unrelated TFIM hit appears in the top-3 for the bounded Jones question set
- at least four of the six questions are rated `useful`
- no question is rated `weak`
- at least one residual weakness remains explicit for Phase `187.2`
