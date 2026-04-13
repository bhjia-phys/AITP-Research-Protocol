# Phase 178.1 Plan: Fresh First-Source Follow-Through Acceptance

## Objective

Prove the repaired first L1->L2 follow-through on one isolated fresh-topic
lane.

## Plan

1. Add a dedicated runtime acceptance script for the fresh-topic
   `register -> literature_intake_stage -> staging review` lane.
2. Verify the script checks both route advancement and topic-local staged
   retrieval through `consult_l2(include_staging=True)`.
3. Add runtime-script and CLI-facing regression coverage so the proof is
   replayable.
4. Update runtime runbooks so the new bounded proof has an operator entrypoint.
