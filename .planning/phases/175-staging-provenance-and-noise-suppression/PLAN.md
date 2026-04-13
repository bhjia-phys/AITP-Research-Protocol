# Plan: 175-01 - Suppress noisy staged rows and preserve true source provenance

**Phase:** 175
**Axis:** Axis 1 (layer-internal optimization) + Axis 3 (data recording)
**Requirements:** L2H-01, L2H-02

## Goal

Make the literature-intake fast path stop staging obviously noisy rows and
carry the true source provenance per staged entry so fresh real-topic `L2`
surfaces start from cleaner inputs.

## Planned Route

### Step 1: Reproduce the staging defects with focused tests

**Files:**
- `research/knowledge-hub/tests/test_literature_intake_support.py`

Add failing coverage for:

- per-entry source provenance in multi-paper staging
- suppression of generic notation and weak `unspecified_method` rows

### Step 2: Fix the fast-path staging pipeline at the source

**Files:**
- `research/knowledge-hub/knowledge_hub/literature_intake_support.py`
- `research/knowledge-hub/knowledge_hub/l2_staging.py`
- `research/knowledge-hub/knowledge_hub/l2_graph.py`
- `research/knowledge-hub/schemas/l2-staging-entry.schema.json`

Minimal implementation:

- attach per-entry source provenance and source tags
- keep staging-index rebuilds from dropping those fields
- suppress clearly generic notation tokens and weak method rows before staging

### Step 3: Re-verify staging and consultation support slices

**Commands to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_literature_intake_support.py -q`
- `python -m pytest research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_l2_staging.py -q`

### Step 4: Leave durable closure artifacts

**Artifacts to write during execution:**
- `.planning/phases/175-staging-provenance-and-noise-suppression/RUNBOOK.md`
- `.planning/phases/175-staging-provenance-and-noise-suppression/SUMMARY.md`
- `.planning/phases/175-staging-provenance-and-noise-suppression/evidence/`

## Acceptance Criteria

- [x] generic notation tokens and weak `unspecified_method` rows are suppressed before staging
- [x] staged entries preserve true per-entry source provenance in tags and provenance payloads
- [x] staging-manifest/index rebuilds preserve the richer staging metadata needed by consultation
- [x] literature-intake and staging support tests pass with the bounded fix
