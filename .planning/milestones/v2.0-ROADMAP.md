# Roadmap: v2.0 Three-Lane Real-Topic Natural-Language E2E

## Result

All milestone phases are complete; lifecycle handling is next.

## Phases

- [x] **Phase 174: Formal-Theory Real-Topic Natural-Language Dialogue Proof** *(Axis 2 + Axis 5)*
- [x] **Phase 174.1: Toy-Model Real-Topic Natural-Language Dialogue Proof** *(Axis 2 + Axis 5)*
- [x] **Phase 174.2: First-Principles Real-Topic Natural-Language Dialogue Proof And Cross-Lane Report** *(Axis 4 + Axis 5)*

## Target Outcome

- one real natural-language dialogue proof closes the formal-theory baseline
- one real natural-language dialogue proof closes the toy-model baseline
- one real natural-language dialogue proof closes the first-principles /
  code-method baseline
- the milestone ends with one cross-lane comparative report of readiness,
  bounded blockers, and next widening decisions

## Next Step

Run milestone lifecycle: audit -> complete -> cleanup.

### Phase 174: Formal-Theory Real-Topic Natural-Language Dialogue Proof

**Axis:** Axis 2 (inter-layer connection) + Axis 5 (agent-facing steering)

**Goal:** prove the public AITP front door can steer the closed formal-theory
baseline through a real natural-language dialogue without hidden seed state.

**Requirements:**

- `REQ-E2E-01`

**Depends on:** `v1.99`
**Plans:** 1 plan

Plans:

- [x] `174-01` Run one real natural-language dialogue proof for the formal-theory baseline

### Phase 174.1: Toy-Model Real-Topic Natural-Language Dialogue Proof

**Axis:** Axis 2 (inter-layer connection) + Axis 5 (agent-facing steering)

**Goal:** prove the public AITP front door can steer the closed toy-model
baseline through a real natural-language dialogue without hidden seed state.

**Requirements:**

- `REQ-E2E-02`

**Depends on:** Phase `174`
**Plans:** 1 plan

Plans:

- [x] `174.1-01` Run one real natural-language dialogue proof for the toy-model baseline

### Phase 174.2: First-Principles Real-Topic Natural-Language Dialogue Proof And Cross-Lane Report

**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing roadmap clarity)

**Goal:** prove the public AITP front door can steer the closed
first-principles baseline through a real natural-language dialogue, then write
the cross-lane comparative report.

**Requirements:**

- `REQ-E2E-03`
- `REQ-E2E-04`
- `REQ-E2E-05`

**Depends on:** Phase `174.1`
**Plans:** 1 plan

Plans:

- [x] `174.2-01` Run the first-principles dialogue proof and write the cross-lane comparative report
