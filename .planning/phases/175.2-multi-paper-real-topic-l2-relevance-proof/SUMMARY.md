# Phase 175.2 Summary: Multi-Paper Real-Topic L2 Relevance Proof

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

## What was done

Phase `175.2` closed milestone `v2.1` with one replayable fresh-topic,
multi-paper acceptance lane.

### Fixes landed

- a dedicated runtime acceptance wrapper now builds an isolated kernel, seeds
  one unrelated canonical carryover row, stages two entries from two distinct
  source papers, and replays the bounded relevance proof end to end
- the replay explicitly checks that per-entry staging provenance preserves the
  true source ids across the multi-paper intake lane
- the replay explicitly checks that the fresh-topic staged bridge note wins the
  primary consultation surface while unrelated canonical carryover remains
  visible but lower-ranked
- durable evidence now exists for the isolated acceptance script and the
  supporting bounded `v2.1` regression slice

## Acceptance criteria

- [x] one replayable multi-paper real-topic acceptance lane proves per-entry
      provenance correctness
- [x] one replayable multi-paper real-topic acceptance lane proves local staged
      relevance can win the primary consultation surface
- [x] the phase leaves durable receipts, runbook, and explicit non-claims

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-runtime-script.txt` | `phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/` | Isolated runtime-script acceptance receipt |
| `run-multi-paper-l2-relevance.json` | `phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/` | Raw replay payload showing primary hit, trust surface, and staged source ids |
| `pytest-v2.1-regression-slice.txt` | `phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/` | Supporting bounded regression slice across the earlier `v2.1` hardening surfaces |
| `receipt.md` | `phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/` | Human-readable replay receipt |

## What this phase proved

1. Fresh-topic multi-paper staging can preserve distinct per-paper provenance
   instead of collapsing everything into one batch identity.
2. The topic-local staged bridge note can now outrank unrelated canonical
   carryover on the primary consultation surface for the bounded fresh-topic
   query.
3. The `v2.1` hardening slice is mechanically replayable instead of depending
   on remembered manual inspection.

## Explicit non-claims

- This phase does not prove full authoritative canonical `L2` promotion for
  the new topic.
- This phase does not redesign global consultation ranking beyond the bounded
  explicit-topic staging case.
- This phase does not clean every inherited staged row from copied package
  state; it proves the primary surface ordering remains correct despite that
  secondary-surface noise.
