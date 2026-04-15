# Gold Question Evaluation

Direction: `jones-von-neumann-algebras`
Captured on: 2026-04-15

## Usefulness Criteria

- `useful`: a gold anchor appears in the top-2 primary hits, no unrelated
  non-Jones hit appears in the top-3, and the answer looks actionable without
  rereading raw sources
- `partial`: a gold anchor appears in the top-5, but ranking or answer-shape is
  still misaligned with the query intent
- `weak`: no gold anchor appears in the top-5, or unrelated material dominates
  the answer surface

## Question Set

| Q# | Query | Profile | Gold anchors | Verdict |
|---|---|---|---|---|
| 1 | What is the finite-dimensional backbone for the current Jones von Neumann algebra route? | `l3_candidate_formation` | `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`, `theorem:jones-ch4-finite-product` | `useful` |
| 2 | Which supporting theorem underlies the current Jones finite-product packet? | `l3_candidate_formation` | `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors` | `useful` |
| 3 | Which local proof fragments support the current Jones finite-product packet? | `l3_candidate_formation` | `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`, `proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares` | `useful` |
| 4 | What limitation or non-goal remains around the stronger Jones product theorem route? | `l3_candidate_formation` | `warning_note:jones-stronger-algequiv-product-theorem-deferred` | `partial` |
| 5 | What remains out of scope relative to the full Chapter 4 type-I classification route? | `l3_candidate_formation` | `warning_note:jones-full-chapter4-type-i-classification-out-of-scope` | `useful` |
| 6 | Which concepts define the local Jones object neighborhood around the block centralizer packet? | `l1_provisional_understanding` | `concept:jones-block-centralizer`, `concept:jones-block-fiber-full-operator-model`, `concept:jones-finite-dimensional-type-i-factor` | `partial` |

## Detailed Notes

### Q1 Backbone

Top primary hits:

1. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
2. `theorem:jones-ch4-finite-product`
3. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`

Why `useful`:
- the top-2 are exactly the backbone theorem-facing anchors
- no unrelated TFIM hit leaks into the top-3

### Q2 Supporting theorem

Top primary hits:

1. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
2. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`
3. `theorem:jones-ch4-finite-product`

Why `useful`:
- the supporting theorem lands at rank 1

### Q3 Proof fragments

Top primary hits:

1. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`
2. `proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares`
3. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`

Why `useful`:
- the two gold proof fragments occupy ranks 1 and 2

### Q4 Stronger-theorem limitation

Top primary hits:

1. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
2. `theorem:jones-ch4-finite-product`
3. `topic_skill_projection:fresh-jones-finite-dimensional-factor-closure`
4. `warning_note:jones-stronger-algequiv-product-theorem-deferred`

Why `partial`:
- the correct warning note is present
- but it appears only at rank 4, behind theorem-facing packet material

### Q5 Full Chapter 4 out-of-scope

Top primary hits:

1. `warning_note:jones-full-chapter4-type-i-classification-out-of-scope`
2. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
3. `theorem:jones-ch4-finite-product`

Why `useful`:
- the dedicated out-of-scope warning note leads the query

### Q6 Local concept neighborhood

Top primary hits:

1. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`
2. `concept:jones-block-centralizer`
3. `proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares`
4. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
5. `theorem:jones-ch4-finite-product`

Why `partial`:
- one gold concept lands at rank 2
- but the answer shape is still theorem/proof biased instead of concept-first

## Scorecard

- `useful`: `4`
- `partial`: `2`
- `weak`: `0`

## Honest Result

The Jones corpus is now genuinely useful for bounded theorem-structure,
supporting-theorem, proof-fragment, and explicit out-of-scope queries.

The remaining weakness is query-type sensitivity:

- warning-style questions about the stronger deferred theorem do not yet put the
  warning note first
- concept-neighborhood questions still over-rank proof fragments before the
  concept neighborhood itself
