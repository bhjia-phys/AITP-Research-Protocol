# Phase 142: Pilot M2F Statement-Compilation Pattern For L2 Automated Formalization - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the missing pre-Lean formalization surface:

- compile bounded informal theory statements into structured declaration
  skeletons first
- then make proof-repair work explicit as a separate verifier-guided plan

The phase should build on the existing candidate, theory-packet, and Lean
bridge surfaces instead of opening a parallel formal-theory workflow.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Add one explicit `statement_compilation` production surface before
  `lean_bridge`, not inside it invisibly.
- **D-02:** Keep the statement-compilation packet proof-assistant agnostic:
  Lean 4 is one downstream target, not the only target named in the packet.
- **D-03:** Reuse existing candidate rows and theory-packet inputs
  (`coverage_ledger`, `notation_table`, `derivation_graph`, `regression_gate`)
  rather than inventing a second source of formalization truth.
- **D-04:** Let `prepare_lean_bridge()` consume the compiled statement packet so
  Stage 1 and Stage 2 become visibly distinct but still remain one chain.
- **D-05:** Keep the scope bounded to one minimal pilot path and one isolated
  acceptance lane; do not reopen whole-topic formalization ambitions.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/FORMAL_THEORY_AUTOMATION_WORKFLOW.md`
- `research/knowledge-hub/SEMI_FORMAL_THEORY_PROTOCOL.md`
- `research/knowledge-hub/SECTION_FORMALIZATION_PROTOCOL.md`
- `research/knowledge-hub/knowledge_hub/lean_bridge_support.py`
- `research/knowledge-hub/knowledge_hub/formal_theory_audit_support.py`

</canonical_refs>

<deferred>
## Deferred Ideas

- whole-paper autonomous formalization
- assistant-specific proof-repair automation beyond one bounded repair plan
- L0 source discovery work currently deferred to post-`v1.68`

</deferred>

---

*Phase: 142-m2f-statement-compilation-pilot*
*Context gathered: 2026-04-12*
