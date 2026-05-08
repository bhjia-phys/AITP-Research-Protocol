---
artifact_kind: l4_review
stage: L4
candidate_id: cand-incorrect-gap
outcome: fail
l4_cycle: 1
reviewed_at: 2026-04-20T13:00:00Z
check_results:
  dimensional_consistency: 'pass: energy units consistent'
  correspondence_check: 'fail: predicted gap 3.2 eV vs experimental 1.1 eV (Si band gap)'
  limiting_case_check: 'pass: free-electron limit recovered'
devils_advocate: 'Incorrect pseudopotential may have been used for Si. Check L0 source registration.'
---

# Review: cand-incorrect-gap

## Outcome
fail

## Notes
The predicted band gap of 3.2 eV for silicon is far from the well-established
experimental value of 1.1 eV. Dimensional consistency and limiting cases pass,
but the correspondence check against experimental data fails decisively.
Candidate should return to L3 for revision — likely an incorrect pseudopotential
or insufficient k-point sampling.

## Check Results
- dimensional_consistency: pass: energy units consistent
- correspondence_check: fail: predicted gap 3.2 eV vs experimental 1.1 eV (Si band gap)
- limiting_case_check: pass: free-electron limit recovered
