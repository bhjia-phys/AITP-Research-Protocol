---
artifact_kind: l4_review
stage: L4
candidate_id: cand-hpc-timeout
outcome: timeout
l4_cycle: 1
reviewed_at: 2026-04-20T14:30:00Z
l4_background_status: completed
l4_job_result: timeout
l4_job_completed_at: 2026-04-20T14:28:00Z
check_results:
  execution_status: 'timeout: Slurm job 47281 exceeded walltime 48:00:00 on dongfang'
devils_advocate: >-
  The 12×12×12 k-point grid may be unnecessarily fine. A 6×6×6 grid would
  complete within walltime and may be sufficient for convergence testing.
---

# Review: cand-hpc-timeout

## Outcome
timeout

## Notes
The Slurm job (ID 47281) on host dongfang exceeded the 48-hour walltime limit
before the self-consistent GW loop converged. The calculation was for a 12×12×12
k-point grid on a 64-atom supercell.

Recovery options:
1. Reduce k-point grid to 6×6×6 and resubmit
2. Increase walltime to 96 hours if queue policy permits
3. Switch to a lighter screening approximation (e.g., G0W0 instead of scGW)

## Devil's Advocate
The 12×12×12 k-point grid may be unnecessarily fine. A 6×6×6 grid would
complete within walltime and may be sufficient for convergence testing.

## Check Results
- execution_status: timeout: Slurm job 47281 exceeded walltime 48:00:00 on dongfang
