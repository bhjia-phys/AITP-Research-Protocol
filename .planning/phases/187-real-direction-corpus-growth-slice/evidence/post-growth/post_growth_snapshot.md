# Jones Corpus Post-Growth Snapshot

Captured on: 2026-04-15
Phase: `187`
Direction: `jones-von-neumann-algebras`

## Post-Growth Summary

The Jones direction is no longer a three-node seed.
It now forms a bounded but non-trivial local corpus.

| Metric | Baseline | Post-growth | Delta |
|---|---:|---:|---:|
| Jones-specific canonical units | `3` | `11` | `+8` |
| Jones-specific graph edges | `0` | `16` | `+16` |
| Jones-specific unit families | `3` | `5` | `+2` |

## Jones-Specific Canonical Units After Growth

Existing before this phase:

1. `theorem:jones-ch4-finite-product`
2. `proof_fragment:jones-codrestrict-comp-subtype-construction-recipe`
3. `topic_skill_projection:fresh-jones-finite-dimensional-factor-closure`

Added in this phase:

4. `concept:jones-block-centralizer`
5. `concept:jones-block-fiber-full-operator-model`
6. `concept:jones-finite-dimensional-type-i-factor`
7. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`
8. `proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares`
9. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
10. `warning_note:jones-stronger-algequiv-product-theorem-deferred`
11. `warning_note:jones-full-chapter4-type-i-classification-out-of-scope`

## Jones-Specific Derived Navigation Pages

- `concept--jones-block-centralizer.md`
- `concept--jones-block-fiber-full-operator-model.md`
- `concept--jones-finite-dimensional-type-i-factor.md`
- `proof_fragment--finite-dimensional-block-centralizer-diagonal-block-compression-decomposition.md`
- `proof_fragment--finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares.md`
- `proof_fragment--jones-codrestrict-comp-subtype-construction-recipe.md`
- `theorem_card--finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors.md`
- `theorem_card--jones-ch4-finite-product.md`
- `topic_skill_projection--fresh-jones-finite-dimensional-factor-closure.md`
- `warning_note--jones-full-chapter4-type-i-classification-out-of-scope.md`
- `warning_note--jones-stronger-algequiv-product-theorem-deferred.md`

## Retrieval Check After Growth

Representative `consult-l2` checks now show a real Jones neighborhood rather
than a nearly empty seed.

### Backbone query

Command:

- `aitp consult-l2 --query-text "What is the finite-dimensional backbone for the current Jones von Neumann algebra route?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json`

Top primary hits are now Jones-local:

1. `theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors`
2. `theorem:jones-ch4-finite-product`
3. `proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition`
4. `proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares`
5. `topic_skill_projection:fresh-jones-finite-dimensional-factor-closure`

No TFIM leak appears in the top-5.

### Limitation query

Command:

- `aitp consult-l2 --query-text "What limitation or non-goal remains around the stronger Jones product theorem route?" --retrieval-profile l3_candidate_formation --max-primary-hits 5 --json`

The query now returns Jones-local warning structure:

- `warning_note:jones-stronger-algequiv-product-theorem-deferred`
- `warning_note:jones-full-chapter4-type-i-classification-out-of-scope`

But these warning notes still trail theorem-facing hits rather than leading the
answer surface.

Interpretation:

- corpus growth succeeded
- retrieval ranking for limitation-style questions still needs honest evaluation
  in Phase `187.1`

## Residual Weaknesses

1. The Jones corpus is now locally connected, but it is still theorem-packet
   centered.
2. Limitation questions still place theorem cards ahead of dedicated warning
   notes.
3. The proof-engineering fragment `jones-codrestrict-comp-subtype-construction-recipe`
   is still isolated from the new Chapter 4 cluster.

## Phase-187 Verdict

This phase succeeded.

It met and exceeded the bounded corpus-growth bar:

- `8` net new Jones units were added
- the Jones cluster now spans `5` unit families
- the Jones-local edge count is `16`

That is enough to justify moving to Phase `187.1`, which should now measure
retrieval and consultation usefulness rather than continuing blind corpus
growth.
