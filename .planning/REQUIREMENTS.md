# Requirements: v1.96 Real Topic Promotion E2E Proof

## Milestone Goal

Prove that the repaired promotion path works on real bounded topic work by
landing one positive result and one honest negative result into canonical `L2`
through the public AITP route.

## Active Requirements

### Positive Promotion Proof

- [ ] `REQ-E2E-01`: one fresh public-front-door topic run travels from
  `bootstrap` through bounded validation and promotes one validated bounded
  result into canonical `L2` with a durable backend receipt.

- [ ] `REQ-E2E-02`: runtime/read-path surfaces (`status`, runtime protocol,
  dashboard, replay, and promotion gate) expose the same positive promotion
  receipt so the operator can see that the real-topic result actually landed.

### Negative-Result Proof

- [ ] `REQ-E2E-03`: one bounded failed route promotes into canonical
  `negative_result` with durable receipt instead of stopping in runtime-only or
  chat-only state.

### Verification And Evidence

- [ ] `REQ-E2E-04`: the milestone closes with automated or runbook-backed
  proof lanes for both the positive and negative-result promotion routes, plus
  durable postmortem evidence that records what still failed or remained manual.

## v2 Requirements

### Broader Knowledge-Extraction Alignment

- `REQ-BENCH-01`: source relevance tiers and role labels align AITP's `L0/L1`
  extraction quality with the AI Scientist benchmark proposal.
- `REQ-BENCH-02`: candidate knowledge types, conditions, sentence-level
  evidence, and multi-reviewer L4 checks are promoted after the real promotion
  proof is closed.

## Out of Scope

| Feature | Reason |
|---------|--------|
| AI Scientist benchmark-alignment rollout | Keep this milestone focused on proving the repaired promotion route first |
| Broad HCI or packaging cleanup | `v1.95` already handled the bounded front-door improvements |
| New symbolic or formal backends | This milestone is about route proof, not backend expansion |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-E2E-01 | Phase 170 | Pending |
| REQ-E2E-02 | Phase 170 | Pending |
| REQ-E2E-03 | Phase 170.1 | Pending |
| REQ-E2E-04 | Phase 170.2 | Pending |

**Coverage:**
- v1 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0

---
*Requirements defined: 2026-04-14 after closing milestone v1.95*
