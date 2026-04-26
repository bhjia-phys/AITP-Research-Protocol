# Phase 35 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

Runtime `l2_memory` now exposes the activation state of the canonical `L2`
graph, so AITP can distinguish a genuinely seeded graph from an empty
consultation shell.

## What changed

- Added `graph_surface` to the runtime `l2_projection` schema contract.
- Extended `AITPService._derive_l2_memory_projection()` to compute:
  - canonical index path
  - canonical edge path
  - unit count
  - edge count
  - available unit types
  - seeded versus empty status
  - activation summary
- Extended the human-readable `l2_memory.md` rendering with a canonical-graph
  section.

## Verification

- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q`
  - `11 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `132 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical-physics collaborator, this phase matters
because it makes `L2` honesty better:

1. AITP can now say whether canonical graph memory is actually populated.
2. The human no longer has to infer from raw repo files whether `L2` is alive.
3. Later consultation phases can use this surface to decide whether AITP is
   consulting substantive reusable memory or only local topic artifacts.

## Remaining Limit

This still does not make consultation fully mature.

AITP can now expose seeded canonical memory honestly, but it still needs a more
operator-usable consultation and memory-map layer in Phase `36`.
