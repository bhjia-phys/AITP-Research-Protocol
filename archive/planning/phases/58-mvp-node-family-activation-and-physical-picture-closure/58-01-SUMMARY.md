# Phase 58 Summary

Status: implemented on `main`

## Goal

Activate the bounded MVP `L2` node-family surface in production code and close
the reserved-only gap around `physical_picture`.

## What Landed

- `physical_picture` is now an active production family in:
  - `canonical-unit.schema.json`
  - `feedback/schemas/candidate.schema.json`
  - `schemas/l2-backend.schema.json`
  - active backend cards and backend index rows
- `L2_MVP_CONTRACT.md` now treats the MVP family surface as active production
  vocabulary instead of leaving `physical_picture` in reserved-only limbo
- `LAYER2_OBJECT_FAMILIES.md`, `canonical/README.md`, and
  `CANONICAL_UNIT.md` now document the real `physical_picture` family and its
  storage projection
- `l2_graph.py` now seeds a real TFIM `physical_picture` unit plus edges that
  make it retrievable through the current bounded consultation path
- retrieval profiles now recognize `physical_picture` as part of the MVP
  retrieval surface
- TPKN bridge mapping now classifies `physical_picture` explicitly instead of
  failing on the new family

## Outcome

Phase `58` is complete.
The next active milestone step is Phase `59`
`lightweight-l2-entry-and-seed-command-family`.
