# Roadmap: v1.96 Real Topic Promotion E2E Proof

## Result

Milestone in progress.

## Phases

- [ ] **Phase 170: Positive Promotion Proof Lane** *(Axis 2 + Axis 4)*
- [ ] **Phase 170.1: Negative-Result Promotion Proof Lane** *(Axis 2 + Axis 1)*
- [ ] **Phase 170.2: E2E Evidence And Regression Closure** *(Axis 4 + Axis 3)*

## Target Outcome

- one fresh public-front-door topic run lands a real bounded result in
  canonical `L2`
- one honest failed route lands in canonical `negative_result`
- both promotion lanes expose durable receipts on runtime/read-path surfaces
- both proof lanes end with automated or runbook-backed replay evidence

## Next Step

Start Phase 170.

### Phase 170: Positive Promotion Proof Lane

**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human evidence and
read-path trust)

**Goal:** Prove one fresh public-front-door topic can travel from bounded topic
bootstrap through validation and land a real bounded result into canonical `L2`
with durable runtime and backend receipts.

**Motivation:**

- `v1.95` repaired the promotion pipe but did not yet prove it on a real topic
- the next honest step is evidence, not more latent infrastructure
- if this lane fails, the failure should become the next bounded backlog or
  milestone input rather than staying in chat

**Requirements:**

- `REQ-E2E-01`
- `REQ-E2E-02`

**Depends on:** `v1.95`
**Plans:** 1 plan

Plans:

- [ ] `170-01` Run one fresh public-front-door positive promotion proof into
  canonical `L2`

### Phase 170.1: Negative-Result Promotion Proof Lane

**Axis:** Axis 2 (inter-layer connection) + Axis 1 (layer capability/honesty)

**Goal:** Prove one bounded failed route can land as canonical
`negative_result` with the same honesty and durability as a positive promotion.

**Motivation:**

- `negative_result` now has a schema and promotion path, but no full route has
  yet proven that the path works in an honest failure case
- the milestone should prove that AITP learns from failed bounded routes rather
  than only from successful ones

**Requirements:**

- `REQ-E2E-03`

**Depends on:** Phase `170`
**Plans:** 1 plan

Plans:

- [ ] `170.1-01` Run one honest negative-result promotion proof into canonical
  `L2`

### Phase 170.2: E2E Evidence And Regression Closure

**Axis:** Axis 4 (human evidence) + Axis 3 (durable regression surfaces)

**Goal:** Turn both proof lanes into durable replayable acceptance evidence,
with postmortem artifacts that make future regression checking mechanical.

**Motivation:**

- even a successful proof lane is weak if it cannot be replayed or audited
- the milestone should close on durable evidence, not just a one-off successful
  shell session

**Requirements:**

- `REQ-E2E-04`

**Depends on:** Phase `170` and Phase `170.1`
**Plans:** 1 plan

Plans:

- [ ] `170.2-01` Close both proof lanes with durable receipts, replay evidence,
  and postmortem surfaces
