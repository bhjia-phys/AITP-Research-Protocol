# Phase 175 Summary: Staging Provenance And Noise Suppression

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 1 (layer-internal optimization) + Axis 3 (data recording)

## What was done

Phase `175` closed the first hardening slice of milestone `v2.1`.

### Fixes landed

- literature fast-path staging now preserves source provenance per entry
  instead of reusing one batch-level source tag for every staged row
- weak `unspecified_method` rows and clearly generic notation bindings are
  suppressed before they become reusable staging entries
- staging-index rebuilds now preserve richer staging metadata so consultation
  can still see the same provenance and trust-surface fields after manifest
  regeneration

## Acceptance criteria

- [x] Generic notation tokens and weak `unspecified_method` rows are suppressed before staging
- [x] Staged entries preserve true per-entry source provenance in tags and provenance payloads
- [x] Staging-manifest/index rebuilds preserve the richer staging metadata needed by consultation
- [x] Literature-intake and staging support tests pass with the bounded fix

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-literature-intake-support.txt` | `phases/175-staging-provenance-and-noise-suppression/evidence/` | Full literature-intake fast-path support regression receipt |
| `pytest-l2-graph-and-staging.txt` | `phases/175-staging-provenance-and-noise-suppression/evidence/` | Supporting `l2_graph` and `l2_staging` regression receipt |
| `receipt.md` | `phases/175-staging-provenance-and-noise-suppression/evidence/` | Human-readable replay receipt |

## What this phase proved

1. The fast literature-intake path can now keep true per-entry source
   provenance across multi-paper staging.
2. Clearly noisy notation and weak method rows can be filtered before they
   pollute bounded `L2` staging surfaces.
3. Staging manifest regeneration no longer strips the metadata consultation
   needs for later relevance ordering work.
