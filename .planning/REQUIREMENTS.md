# Requirements: v2.9 Promotion-Review Gate Closure

## Milestone Goal

Make post-route continuation coherent enough that, once `l2_promotion_review`
becomes the selected route on a fresh topic, the loop materializes one explicit
promotion-review gate and advances beyond the summary placeholder instead of
stalling there forever.

## Active Requirements

### Explicit Promotion-Review Gate

- [ ] `PRG-01`: once `l2_promotion_review` is already the selected route and
  the operator continues again, the bounded loop materializes one explicit
  promotion-review gate from the selected staged candidate.

- [ ] `PRG-02`: that promotion-review gate is written as a durable runtime
  artifact rather than remaining only a transient queue guess.

### Public Promotion-Review Advancement

- [ ] `PRG-03`: public `next`, `status`, and equivalent dashboard surfaces stay
  aligned on the same explicit promotion-review gate.

### Replayable Proof

- [ ] `PRG-04`: one replayable fresh-topic proof shows the same topic can
  advance beyond promotion-review summary into one explicit promotion-review
  gate while the earlier staged-L2, consultation-selection, and route-choice
  baselines still pass.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reopening selected-candidate route choice from `v2.8` | treat the `v2.8` chosen-route surface as the new baseline unless a fresh regression appears |
| Automatically promoting the selected staged candidate into canonical `L2` | `v2.9` only materializes the explicit promotion-review gate |
| Broad route optimization across split/validate/promote branches | keep the milestone bounded to the promotion-review gate already chosen on the baseline |
| Broad three-lane scientific widening across formal, toy, and first-principles routes | defer until promotion-review gate materialization is mechanically stable |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRG-01 | Phase 183 | Planned |
| PRG-02 | Phase 183 | Planned |
| PRG-03 | Phase 183.1 | Planned |
| PRG-04 | Phase 183.2 | Planned |

**Coverage:**
- v1 requirements: 4 total
- mapped to phases: 4
- unmapped: 0
