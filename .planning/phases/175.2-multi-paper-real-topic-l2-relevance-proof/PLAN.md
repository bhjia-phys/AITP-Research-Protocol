# Plan: 175.2-01 - Replay the multi-paper real-topic proof and close the milestone honestly

**Phase:** 175.2
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)
**Requirements:** L2H-04, L2H-05

## Goal

Close milestone `v2.1` with one replayable multi-paper real-topic acceptance
lane proving both provenance correctness and topic-local consultation relevance
ordering on the hardened `L2` surfaces.

## Planned Route

### Step 1: Add the isolated multi-paper proof wrapper

**Files:**
- `research/knowledge-hub/runtime/scripts/run_multi_paper_l2_relevance_acceptance.py`
- `research/knowledge-hub/tests/test_runtime_scripts.py`

The script should:

- construct an isolated kernel root
- seed one unrelated canonical carryover row
- stage multiple entries from distinct source papers under one fresh topic
- materialize staging and compiled knowledge artifacts
- prove the top primary consultation hit is the topic-local staged row

### Step 2: Preserve replay receipts

**Commands to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "multi_paper_l2_relevance_acceptance_script_runs_on_isolated_work_root" -q`
- `python research/knowledge-hub/runtime/scripts/run_multi_paper_l2_relevance_acceptance.py --json`

### Step 3: Leave durable closure artifacts

**Artifacts to write during execution:**
- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/RUNBOOK.md`
- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/SUMMARY.md`
- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/`

## Acceptance Criteria

- [ ] one replayable multi-paper real-topic acceptance lane proves per-entry
      provenance correctness
- [ ] one replayable multi-paper real-topic acceptance lane proves local staged
      relevance can win the primary consultation surface
- [ ] the phase leaves durable receipts, runbook, and explicit non-claims
