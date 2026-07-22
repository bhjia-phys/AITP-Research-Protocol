# 10-Session Parallel Coordination Plan

Date: 2026-04-17
Status: active
Purpose: Coordinate 10 parallel AI sessions working on AITP implementation

---

## Context

AITP protocol has been rewritten from 4-mode (discussion/explore/verify/promote) to
3-mode (explore/learn/implement). These 10 sessions align implementation with the new
protocol and fill capability gaps identified in COLLABORATOR_IMPLEMENTATION_REVIEW.md.

## How to Identify Your Session

Match your assigned files against the "Owns" column below. That tells you your session ID.

## Session Assignments

### S1: Mode Refactoring — Core Runtime [CAN START NOW]
- **Owns:** mode_registry.py, mode_envelope_support.py, source_distillation_support.py,
  protocol_manifest.py, cli_compat_handler.py
- **Depends on:** nothing
- **Blocks:** S2, S3, S4
- **Key protocol:** docs/protocols/mode_envelope_protocol.md (ME1-ME3)
- **Task:** Verify/fix core mode constants and imports. Fix protocol_manifest.py declared
  states (verifying→learning, promoting→implementing). Fix source_distillation explore
  reading depth (discussion→explore should return skim-level only, not full sections).
- **Do NOT touch:** layer_graph_support.py, runtime_bundle_support.py, topic_loop_support.py,
  aitp_cli.py, decide_next_action.py, orchestrator_contract_support.py, tests/, docs/,
  l2_*.py, l1_*.py, validation_*.py

### S2: Mode Refactoring — Runtime Control [WAIT FOR S1]
- **Owns:** layer_graph_support.py, runtime_bundle_support.py, topic_loop_support.py
- **Depends on:** S1 must complete (imports mode_registry.py)
- **Blocks:** S4
- **Task:** Replace all "verify"/"promote" mode checks with "learn"/"implement".
  L275 in layer_graph: promote→implement. L120 in runtime_bundle: verify+iterative_verify→learn+derivation.
  L212 in topic_loop: same. Import normalize_runtime_mode from mode_registry.
- **Do NOT touch:** mode_registry.py, mode_envelope_support.py, source_distillation_support.py,
  protocol_manifest.py, aitp_cli.py, tests/, docs/

### S3: Mode Refactoring — CLI + Action Routing [WAIT FOR S1]
- **Owns:** aitp_cli.py, runtime/scripts/decide_next_action.py,
  runtime/scripts/orchestrator_contract_support.py
- **Depends on:** S1 must complete (imports mode_registry.py)
- **Blocks:** S4
- **Task:** Map CLI verify→learn, promote→implement (keep old names as deprecated compat).
  Fix decide_next_action L500/508, orchestrator_contract L82/1175.
- **Do NOT touch:** knowledge_hub/*.py (except aitp_cli.py), tests/, docs/

### S4: Test Fix + Acceptance Baseline [WAIT FOR S2 + S3]
- **Owns:** all files under research/knowledge-hub/tests/
- **Depends on:** S2 and S3 must complete
- **Task:** Update test assertions from old mode names to new. Fix 15 pre-existing failures.
  Run full pytest suite and achieve 0 failures.
- **Do NOT touch:** knowledge_hub/*.py, runtime/scripts/, docs/

### S5: L2 Knowledge Store Growth [CAN START NOW]
- **Owns:** l2_compiler.py, l2_graph.py, l2_staging.py, l2_consultation_support.py,
  l2_hygiene.py, l2_reuse_context_support.py, runtime_schema_promotion_bridge.py,
  research/knowledge-hub/canonical/
- **Depends on:** nothing
- **Priority:** #1 per COLLABORATOR_IMPLEMENTATION_REVIEW.md
- **GSD phases:** 169, 169.1
- **Task:** Populate L2 with real physics knowledge (10-20 nodes). Implement progressive-
  disclosure retrieval. Add paired-backend drift audit. Make consult-l2 return useful results.
- **Do NOT touch:** mode_*.py, source_distillation_support.py, l1_*.py, validation_*.py, tests/, docs/

### S6: L1 Deep Reading [CAN START NOW]
- **Owns:** l1_source_intake_support.py, l1_vault_support.py, l1_source_bridge_support.py,
  source_intelligence.py
- **Depends on:** nothing
- **Priority:** #2 per COLLABORATOR_IMPLEMENTATION_REVIEW.md
- **GSD phases:** 167, 167.1
- **Task:** Add reading-depth states. Implement assumption extraction pipeline. Add regime
  tracking and notation alignment. Implement cross-source contradiction detection.
- **Do NOT touch:** source_distillation_support.py (S1 owns!), mode_*.py, l2_*.py,
  validation_*.py, tests/, docs/

### S7: L4 Analytical Validation [CAN START NOW]
- **Owns:** validation_review_service.py, analytical_review_support.py,
  statement_compilation_support.py, proof_engineering_bootstrap.py
- **Depends on:** nothing
- **Priority:** #3 per COLLABORATOR_IMPLEMENTATION_REVIEW.md
- **GSD phases:** 168, 168.1
- **Task:** Add analytical validation families (limiting-case, dimensional, symmetry, source-
  consistency checks). Implement rich partial outcomes. Add derivation-check routes.
- **Do NOT touch:** mode_*.py, l1_*.py, l2_*.py, tests/, docs/

### S8: Protocol Docs + GSD Planning [CAN START NOW]
- **Owns:** docs/protocols/brain_protocol.md, closed_loop_protocol.md,
  L4_validation_protocol.md, AUDIT_REPORT_ALIGNMENT.md, .planning/phases/165.2/PLAN.md,
  .planning/STATE.md, docs/EXECUTION_PLAN.md
- **Depends on:** nothing
- **Task:** Fix old mode names in 3 protocol docs. Rewrite Phase 165.2 PLAN.md for 3-mode.
  Create v3.0 milestone in STATE.md. Update EXECUTION_PLAN.md. Check cross-references.
- **Do NOT touch:** knowledge_hub/*.py, runtime/scripts/, tests/

### S9: Collaborator Memory [CAN START NOW]
- **Owns:** collaborator_profile_support.py, research_trajectory_support.py,
  mode_learning_support.py, research_judgment_support.py,
  research_judgment_runtime_support.py, research_taste_support.py
- **Depends on:** nothing
- **Priority:** #4 per COLLABORATOR_IMPLEMENTATION_REVIEW.md
- **Task:** Implement collaborator profile with preferences. Add research trajectory memory.
  Implement momentum/stuckness/surprise signals. Add mode learning from user behavior.
- **Do NOT touch:** mode_registry.py, mode_envelope_support.py, source_distillation_support.py,
  l1_*.py, l2_*.py, validation_*.py, tests/, docs/

### S10: Acceptance Test Categorization [CAN START NOW]
- **Owns:** creates docs/ACCEPTANCE_TEST_BASELINE.md (read-only everything else)
- **Depends on:** nothing
- **Task:** Run all 71 acceptance scripts + 80+ unit tests. Categorize each failure as
  MODE/INFRA/BUG/DATA. Generate comprehensive baseline report.
- **Do NOT touch:** any production or test code. Only create the report file.

---

## Mode Mapping Reference

All sessions MUST use this mapping when encountering old mode names:

| Old (4-mode) | New (3-mode) | Notes |
|---|---|---|
| discussion | explore | Default mode for new topics |
| explore | explore | Unchanged |
| verify | learn | Verification is an activity within learn |
| promote | implement | Promotion is an operation within implement |

Key rule (ME1): "L2 promotion is NOT a separate mode. It is an operation triggered
within learn or implement."

## Conflict Resolution Rules

1. If you find a file listed under another session's "Owns", DO NOT modify it.
   Report the conflict and wait.
2. If your session depends on another session that hasn't completed, read the current
   state of the files, make your changes compatible with the expected final state,
   and note what may need adjustment after the blocking session completes.
3. If you discover a file that needs changes but is owned by another session, add a
   comment or TODO noting the needed change, and report it.
4. Git: work on main branch. Commit with prefix like `[S1]`, `[S5]`, etc.
   Do NOT push without confirmation.

## Verification

After completing your tasks:
1. Run `python -c "import knowledge_hub"` to verify no import breakage
2. Run pytest on your owned test files (if applicable)
3. Report: what you changed, what passed, what still needs work
