# Phase 181 Plan: Consultation-Followup Auto Execution

## Objective

Execute one bounded topic-local `consult-l2` step automatically once the same
fresh topic has already reached the post-review consultation surface.

## Plan

1. Add a focused helper for bounded consultation query derivation, staged-hit
   selection, and selection-artifact rendering.
2. Add one service-level `_run_consultation_followup()` executor that records
   consultation receipts and writes the new selection artifact.
3. Teach the auto-action loop to run `consultation_followup` only under the
   narrow post-review continuation gate.
