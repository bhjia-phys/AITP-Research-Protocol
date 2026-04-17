# AITP Protocol Completion and Implementation Plan

Status: active
Created: 2026-04-17
Scope: Complete the protocol architecture, align with implementation, fill gaps, test.

---

## Phase A: Protocol Completion

### A1. Protocol-Implementation Alignment Audit
- [x] brain_protocol.md vs frontdoor_support.py + topic_loop_support.py + control_plane_support.py (~85% coverage)
- [x] action_queue_protocol.md vs orchestrate_topic.py + decide_next_action.py (~55-60% coverage)
- [x] closed_loop_protocol.md vs closed_loop_v1.py (~55-60% coverage)
- [x] mode_envelope_protocol.md vs mode_envelope_support.py (~35-40% coverage)
- [x] promotion_pipeline.md vs promotion_gate_support.py + auto_promotion_support.py (~35-40% coverage)
- [x] followup_lifecycle.md vs followup_support.py (~70% coverage)
- [x] H_human_interaction.md vs decision_point_handler.py + h_plane_support.py (~35-40% coverage)
- [x] L1_intake_protocol.md vs l1_source_intake_support.py + l1_vault_support.py (~65% coverage)
- [x] L2_backend_interface.md vs l2_compiler.py + l2_graph.py + l2_staging.py (~68% coverage)
- [x] L3_execution_protocol.md vs candidate handling in orchestrate_topic.py (~65% coverage)
- [x] L4_validation_protocol.md vs validation_review_service.py + execution scripts (~42% coverage)
- [x] adapter_interface.md vs adapter skills and hooks (~65% coverage)

**Audit report**: `docs/AUDIT_REPORT_ALIGNMENT.md`
**Protocol updates completed**: all 12 protocols updated to match implementation

### A2. Legacy Protocol Cleanup
- [ ] Add redirect/consolidation notices to merged legacy protocols
- [ ] Verify cross-references from SPEC S14 are accurate
- [ ] Update LAYER_MAP.md if needed

### A3. Formal Theory Protocols (keep as-is, verify completeness)
- [ ] PROOF_OBLIGATION_PROTOCOL.md
- [ ] SEMI_FORMAL_THEORY_PROTOCOL.md
- [ ] SECTION_FORMALIZATION_PROTOCOL.md
- [ ] FORMAL_THEORY_AUTOMATION_WORKFLOW.md
- [ ] FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md

## Phase B: Missing Implementation

### B1. Uncovered Functionality (from earlier audit)
- [ ] Strategy/collaborator memory — cross-topic failure pattern extraction
- [ ] Research scratchpad — lightweight exploration without full topic lifecycle
- [ ] Topic dependency DAG — multi-topic scheduling with blocking
- [ ] Exploration sessions — speculative quick investigations

### B2. Protocol-Required But Not Implemented
- [ ] From each protocol: identify required surfaces that don't exist in code
- [ ] Prioritize by impact on real research workflows

### B3. Implementation-Protocol Gaps
- [x] Code that does things the protocol doesn't describe — all 12 protocols updated to document actual behavior
- [x] Protocol describes things the code doesn't do — flagged as implementation tickets (see audit report)
- [x] SPEC updated to reflect three-step promotion model, 5-phase closed loop, corrected mode foreground layers
- [x] All 12 protocols now include Implementation Status sections

## Phase C: Testing

### C1. Existing Acceptance Tests
- [ ] Run 71 acceptance test scripts, categorize pass/fail
- [ ] Fix failures
- [ ] Update tests that test old protocol behavior

### C2. New Protocol Conformance Tests
- [ ] Test that SPEC S16 charter coverage is enforceable
- [ ] Test mode envelope transitions
- [ ] Test promotion pipeline stages
- [ ] Test closed-loop cycle produces artifacts
- [ ] Test followup lifecycle (spawn, return, reintegrate)

### C3. Integration Tests
- [ ] End-to-end topic lifecycle with a real research subject
- [ ] Cross-topic L2 consultation and reuse
- [ ] Multi-topic scheduling
- [ ] Adapter conformance for each platform

## Execution Order

1. A1 (alignment audit) — understand the real gaps
2. A3 (formal theory check) — quick verification, likely minimal changes
3. B3 (fix protocol-implementation mismatches) — either update protocol or file implementation tickets
4. A2 (legacy cleanup) — mechanical, can do in parallel
5. B1 + B2 (missing implementation) — the heavy lifting
6. C1 (existing tests) — establish baseline
7. C2 + C3 (new tests) — validate new work
