# Phase 169 Summary

Status: implemented in working tree

## Goal

Extend the canonical schema surface so the first blocked `L4 -> L2` promotion
gap is removed: `negative_result` is now a legal canonical unit family, and
the runtime proof packet contracts are available on the package schema surface
that later promotion code will load.

## What Landed

- `canonical-unit.schema.json` now includes `negative_result` in the
  `unit_type` enum
- Layer 2 backend schema targets now also admit `negative_result`
- canonical graph/index materialization now recognizes
  `canonical/negative-results/` as a legal canonical unit directory
- the runtime proof packet schemas now exist under
  `research/knowledge-hub/schemas/` as package-local mirrors:
  - `lean-ready-packet.schema.json`
  - `proof-repair-plan.schema.json`
  - `statement-compilation-packet.schema.json`
- contract and Layer 2 graph tests now cover the new canonical family and the
  package schema mirrors

## Verification

- focused red-green regression slice:
  - `3 passed`
- related schema and Layer 2 graph regression slice:
  - `18 passed`
- statement-compilation / lean-bridge durability regression slice:
  - `2 passed`

## Outcome

`REQ-PROMO-01` and `REQ-PROMO-02` are now satisfied:

- validated negative outcomes now have a canonical contract path instead of
  stopping at staging-only vocabulary
- the three runtime proof packet schemas are now available on the package
  schema surface that downstream promotion helpers can consume explicitly

## Next Step

Proceed to Phase `169.1` to wire promotion context, gate payloads, and bridge
code onto these schema surfaces.
