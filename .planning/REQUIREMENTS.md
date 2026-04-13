# Requirements: v1.95 L2 Promotion Pipeline Closure

## Milestone Goal

Close the L4→L2 promotion pipeline gap so that E2E research runs that validate
at L4 can actually land their results in L2 canonical knowledge. The gap was
discovered during two Jones E2E runs: both reached L4 (Lean compilation
succeeded) but could not promote to L2 because the pipeline's engineering is
incomplete — not the science.

## Active Requirements

### Canonical Schema Extension

- [ ] `REQ-PROMO-01`: `canonical-unit.schema.json` includes `negative_result`
  in the `unit_type` enum so that validated negative outcomes have a
  staging→canonical promotion path.

- [ ] `REQ-PROMO-02`: three runtime proof schemas exist as formal JSON schemas
  in `research/knowledge-hub/schemas/`:
  - `lean-ready-packet.schema.json`
  - `proof-repair-plan.schema.json`
  - `statement-compilation-packet.schema.json`
  Each schema defines the minimal fields needed to translate a runtime proof
  artifact into a canonical L2 unit.

### Promotion Bridge Code

- [ ] `REQ-PROMO-03`: `candidate_promotion_support.py` `_resolve_promotion_context()`
  loads runtime proof schemas and includes their field definitions in the
  promotion context payload.

- [ ] `REQ-PROMO-04`: `auto_promotion_support.py` `_validate_auto_promotion()`
  checks that runtime proof schema fields are present and valid before approving
  auto-promotion.

- [ ] `REQ-PROMO-05`: `promotion_gate_support.py` `request_promotion()` includes
  runtime schema paths in the gate payload so downstream consumers can verify
  the promotion provenance.

- [ ] `REQ-PROMO-06`: a new `runtime_schema_promotion_bridge.py` module
  translates runtime proof artifacts (lean-ready-packet, proof-repair-plan,
  statement-compilation-packet) into canonical L2 units by mapping runtime
  fields to canonical fields according to the schemas created in REQ-PROMO-02.

### HCI Foundation

- [ ] `REQ-HCI-01`: `aitp status` output is structured into at most 3 tiers
  (summary → key sections → full detail) instead of a flat 40+ section dump.
  The operator can scan the summary tier in under 5 seconds.

- [ ] `REQ-HCI-02`: an `aitp hello` (or equivalent zero-config introductory
  command) exists and prints: current topic status, suggested next action, and
  a one-line pointer to documentation. After bootstrap, the runtime state
  includes a `next_action_hint` field pointing to the most likely next step.

## v2 Requirements

### Full E2E Proof

- `REQ-PROMO-V2-01`: one complete E2E topic run promotes a validated proof
  artifact all the way from L0 through L4 to L2 canonical knowledge.
- `REQ-PROMO-V2-02`: `negative_result` promotion path is exercised in an E2E
  test where a hypothesis is honestly refuted and the negative outcome lands
  in L2.

### Broader HCI

- `REQ-HCI-V2-01`: PyPI package, 5-minute quickstart, and Windows path
  handling (BACKLOG 999.48–999.51).
- `REQ-HCI-V2-02`: CLI command groups and terminology cleanup (BACKLOG 999.62–999.63).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full E2E proof run | Depends on this milestone's pipeline fixes first |
| PyPI packaging and install verification | BACKLOG 999.48–999.49, separate milestone |
| DeepXiv/Graphify integration | Already routed to Phase 165.5 |
| Symbolic algebra backend | Not a pipeline question |
| Strategy memory seeding | Already done in Phase 165.1 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-PROMO-01 | Phase 169 | Pending |
| REQ-PROMO-02 | Phase 169 | Pending |
| REQ-PROMO-03 | Phase 169.1 | Pending |
| REQ-PROMO-04 | Phase 169.1 | Pending |
| REQ-PROMO-05 | Phase 169.1 | Pending |
| REQ-PROMO-06 | Phase 169.1 | Pending |
| REQ-HCI-01 | Phase 169.2 | Pending |
| REQ-HCI-02 | Phase 169.2 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-04-14*
*Root cause: Jones E2E run gap diagnosis (2026-04-14)*
