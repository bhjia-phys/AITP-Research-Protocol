# Phase 36 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

`L2` consultation now emits a latest-consultation memory map that is readable
for the human and stays aligned with the AI-facing consultation packet.

## What changed

- Extended consultation call artifacts with:
  - `memory_map.json`
  - `memory_map.md`
- Extended runtime `l2_memory.consultation_surface` with:
  - `latest_memory_map_path`
  - `latest_memory_map_note_path`
- Kept the memory map derived from the same consultation selection used by the
  existing AI-facing consultation result:
  - primary canonical hits
  - expanded canonical hits
  - warning notes
  - staged hits
  - canonical graph status

## Verification

- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "consult_topic_l2_records_consultation_and_returns_trust_aware_packet" -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "surfaces_latest_topic_consultation_details" -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `132 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical physicist using AITP, this is the first
consultation slice that reads more like a collaborator memory view than a raw
protocol receipt:

1. the human can now inspect the latest consultation as a compact memory map;
2. warning notes and staged tensions stay visible rather than disappearing into
   a friendlier summary;
3. the memory map and the AI-facing packet remain tied to the same selected
   ids, so the system is more transparent about what memory actually shaped the
   route.

## Next Step

Phase `37` should now focus on runtime behavior rather than more memory
surfaces:

- bounded free exploration,
- hard trust and writeback gates,
- and clearer continue/update/checkpoint timing for the human.
