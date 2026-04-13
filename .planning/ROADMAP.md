# Roadmap: v1.95 L2 Promotion Pipeline Closure

## Result

Milestone in progress.

## Phases

- [x] **Phase 169: L2 Canonical Schema Extension** *(Axis 3 + Axis 2)*
- [ ] **Phase 169.1: L2 Promotion Bridge Code** *(Axis 2 + Axis 3)*
- [ ] **Phase 169.2: HCI Foundation** *(Axis 4)*

## Target Outcome

- L4→L2 promotion pipeline is structurally complete: every unit type that can
  reach L4 (including `negative_result`) has a defined staging→canonical path
- runtime proof schemas (`lean-ready-packet`, `proof-repair-plan`,
  `statement-compilation-packet`) have promotion bridges so validated proof
  artifacts can land in L2 canonical knowledge
- the three promotion support modules load runtime schema context during
  promotion decisions
- one bounded HCI improvement makes the operator experience of AITP's status
  output and first-time bootstrap less hostile

## Next Step

Start Phase 169.1.

### Phase 169: L2 Canonical Schema Extension

**Axis:** Axis 3 (schema evolution, data recording) + Axis 2 (inter-layer
connection)

**Goal:** Extend the canonical schema so every unit type that reaches L4 has a
valid `unit_type` enum entry, and create JSON schemas for the three runtime
proof schemas that currently exist only as Python dicts.

**Motivation:**

- Two Jones E2E runs proved the science works (Lean compilation succeeds at L4)
  but the pipeline breaks at promotion because `canonical-unit.schema.json` does
  not include `negative_result` in its `unit_type` enum
- runtime proof artifacts (`lean-ready-packet`, `proof-repair-plan`,
  `statement-compilation-packet`) exist as ad-hoc Python dicts in the validation
  layer but have no formal schema and no promotion path into canonical L2
- without these schema fixes, no E2E run can ever reach L2 regardless of how
  good the science is

**Requirements:**

- `REQ-PROMO-01`
- `REQ-PROMO-02`

**Depends on:** `v1.94`
**Plans:** 1 plan

Plans:

- [x] `169-01` Add `negative_result` to canonical-unit.schema.json and create
  runtime proof schemas

### Phase 169.1: L2 Promotion Bridge Code

**Axis:** Axis 2 (inter-layer connection) + Axis 3 (data recording)

**Goal:** Wire the three promotion support modules to load and forward runtime
schema context during L4→L2 promotion, and create a dedicated
`runtime_schema_promotion_bridge.py` that translates runtime proof artifacts into
canonical L2 units.

**Motivation:**

- `candidate_promotion_support.py` `_resolve_promotion_context()` (lines 170-230)
  does not load runtime schemas
- `auto_promotion_support.py` `_validate_auto_promotion()` (lines 58-105) does
  not check runtime schema validity
- `promotion_gate_support.py` `request_promotion()` (lines 214-281) does not
  include runtime schema paths in the gate payload
- the promotion pipeline has the schema structure (from Phase 169) but no code
  that actually uses it

**Requirements:**

- `REQ-PROMO-03`
- `REQ-PROMO-04`
- `REQ-PROMO-05`
- `REQ-PROMO-06`

**Depends on:** Phase `169`
**Plans:** 1 plan

Plans:

- [ ] `169.1-01` Add runtime schema loading and bridging to all three promotion
  support modules

### Phase 169.2: HCI Foundation

**Axis:** Axis 4 (global infrastructure, human experience)

**Goal:** Make three targeted HCI improvements so that the next E2E test run
has a better operator experience: structured status output, a zero-config
introductory command, and post-bootstrap action guidance.

**Motivation:**

- BACKLOG 999.60: `aitp status` outputs 40+ sections with no hierarchy —
  impossible to scan
- BACKLOG 999.61: no `aitp hello` or equivalent zero-config entry point for
  new users
- BACKLOG 999.86: after bootstrap, the operator sees no suggested next action
- these are the three highest-severity HCI gaps that directly affect E2E test
  ergonomics

**Requirements:**

- `REQ-HCI-01`
- `REQ-HCI-02`

**Depends on:** `v1.94` (independent of Phase 169/169.1)
**Plans:** 1 plan

Plans:

- [ ] `169.2-01` Add structured status output, hello command, and post-bootstrap
  action guidance
