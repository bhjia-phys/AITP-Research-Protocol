# Requirements: v2.8 Selected-Candidate Route Choice Closure

## Milestone Goal

Make post-selection continuation coherent enough that, once a selected staged
candidate becomes the selected route on a fresh topic, the loop derives one
bounded deeper route choice and advances beyond the candidate-summary
placeholder instead of stalling there forever.

## Active Requirements

### Route Choice Beyond Selected Candidate

- [ ] `RCC-01`: once `selected_consultation_candidate_followup` is already the
  selected route and the operator continues again, the bounded loop derives one
  first deeper route choice from the selected staged candidate.

- [ ] `RCC-02`: that deeper route choice is written as a durable runtime
  artifact rather than remaining only a transient queue guess.

### Public Post-Selection Advancement

- [ ] `RCC-03`: public `next`, `status`, and equivalent dashboard surfaces stay
  aligned on the same first deeper route chosen after selected-candidate
  closure.

### Replayable Proof

- [ ] `RCC-04`: one replayable fresh-topic proof shows the same topic can
  advance beyond selected-candidate summary into one bounded deeper route
  choice while the earlier staged-L2 and consultation-selection baselines still
  pass.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Reopening consultation-followup selection from `v2.7` | treat the `v2.7` selected-candidate surface as the new baseline unless a fresh regression appears |
| Executing the chosen deeper route | `v2.8` only chooses and surfaces the next bounded route |
| Automatic global route optimization across all candidate types | keep the milestone bounded to the first deeper route choice from the selected candidate |
| Broad three-lane scientific widening across formal, toy, and first-principles routes | defer until post-selection route choice is mechanically stable |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RCC-01 | Phase 182 | Planned |
| RCC-02 | Phase 182 | Planned |
| RCC-03 | Phase 182.1 | Planned |
| RCC-04 | Phase 182.2 | Planned |

**Coverage:**
- v1 requirements: 4 total
- mapped to phases: 4
- unmapped: 0
