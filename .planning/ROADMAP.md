# Roadmap: v2.9 Promotion-Review Gate Closure

## Result

Milestone execution complete. Audit / archive is next.

---

# Roadmap: v3.0 E2E Scientific Assistant Completion

## Direction

Close the three remaining gaps that prevent AITP from being a genuinely strong
AI research collaborator:
1. Full L0→L4→L2 promotion for real topics (Jones proof-grade + honest negative result).
2. Sharp thesis/source → bounded question distillation.
3. First complete code-backed research acceptance case (LibRPA/QSGW).

## Phases

- [ ] **Phase 184: Jones L4→L2 E2E Promotion Proof** *(Axis 2)*
- [ ] **Phase 184.1: Negative-Result L4→L2 E2E Promotion Proof** *(Axis 2)*
- [ ] **Phase 185: Thesis-to-Question Distillation Hardening** *(Axis 1)*
- [ ] **Phase 185.1: Lane-Specific First Validation Routes** *(Axis 1)*
- [ ] **Phase 185.2: Global L2 Reuse Context And Capability Plane** *(Axis 1 + Axis 2 + Axis 3)*
- [ ] **Phase 186: Code-Backed Topic Acceptance Case** *(Axis 1 + Axis 5)*
- [ ] **Phase 186.1: Code-Backed Trust State and L2 Writeback** *(Axis 2 + Axis 3)*
- [ ] **Phase 187: Replay Proof Bundle and HCI Observability** *(Axis 4 + Axis 3)*

## Target Outcome

- One real topic completes full L0→L4→L2 promotion (Jones 2015).
- One honest negative-result topic completes L0→L4→L2 promotion.
- The scRPA thesis topic produces a sharp first bounded question with a concrete
  novelty target and validation route.
- One LibRPA/QSGW code-backed topic runs from bootstrap to benchmark inside AITP.
- All four achievements are replayable from fresh-topic bootstrap.

## Detailed Plan

See `.planning/v3.0-E2E-SCIENTIFIC-ASSISTANT-PLAN.md`.

## Next Step

Begin Phase 184 after v2.9 audit / archive is complete.

## Phases

- [x] **Phase 183: Promotion-Review Gate Materialization** *(Axis 2 + Axis 4)*
- [x] **Phase 183.1: Public Promotion-Review Gate Surface** *(Axis 4 + Axis 5)*
- [x] **Phase 183.2: Fresh Promotion-Review Gate Replay Proof** *(Axis 4 + Axis 3)*

## Target Outcome

- once `l2_promotion_review` becomes the selected route, the same topic no
  longer stalls on that promotion-review summary forever
- the bounded loop now materializes one explicit promotion-review gate and
  public `next` / `status` expose that gate
- one replayable fresh-topic proof records the sixth bounded continue step from
  promotion-review summary into the explicit gate

## Next Step

Audit / archive milestone `v2.9`, then plan the next bounded gap after explicit promotion-gate materialization.

### Phase 183: Promotion-Review Gate Materialization

**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human experience)

**Goal:** materialize one explicit promotion-review gate once
`l2_promotion_review` becomes the selected route.

**Requirements:**

- `PRG-01`
- `PRG-02`

**Depends on:** `v2.8`
**Plans:** 1 plan

Plans:

- [x] `183-01` Materialize one explicit promotion-review gate from the selected staged candidate

### Phase 183.1: Public Promotion-Review Gate Surface

**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

**Goal:** make public `next` and `status` advance from promotion-review summary
to the same explicit promotion-review gate.

**Requirements:**

- `PRG-03`

**Depends on:** Phase `183`
**Plans:** 1 plan

Plans:

- [x] `183.1-01` Align public surfaces on the explicit promotion-review gate

### Phase 183.2: Fresh Promotion-Review Gate Replay Proof

**Axis:** Axis 4 (human evidence) + Axis 3 (data recording)

**Goal:** close the milestone with one replayable fresh-topic proof that the
same topic can advance beyond promotion-review summary into one explicit
promotion-review gate.

**Requirements:**

- `PRG-04`

**Depends on:** Phase `183.1`
**Plans:** 1 plan

Plans:

- [x] `183.2-01` Capture the replayable sixth-continue advancement beyond promotion-review summary

## Backlog

### Phase 999.1: AITP run_topic_loop Performance Refactor — Composable Primitives + In-Memory Cache (BACKLOG)

**Goal:** Refactor `run_topic_loop` from a monolithic mega-loop into lightweight composable MCP primitives, reducing orchestrate() calls from ~2N+4 to ~1 per step and cutting disk I/O by 5-10x. Current architecture makes interactive research workflows impractically slow, especially on sync disks (BaiduSync).
**Requirements:**
- Layer 1: Add dirty-flag to skip redundant `orchestrate()` calls when state hasn't mutated
- Layer 2: Expose composable tools: `topic_bootstrap`, `action_peek`, `action_step`, `topic_sync` — agent controls the loop, not the framework
- Layer 3: Introduce `LoopSession` in-memory state cache; flush disk only at loop end or explicit checkpoint
- Philosophy: framework should be thin (state storage + gate check), not a heavyweight orchestrator that second-guesses the agent at every step
**Key files:** `topic_loop_support.py`, `aitp_mcp_server.py`, `aitp_service.py`
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)
