# Issue Ledger

Use this ledger during the real-topic E2E run.

One row per discovered issue.

Severity:

- `P0` blocks the real-topic run completely or corrupts trust-critical state
- `P1` allows partial progress but blocks the intended bounded route
- `P2` creates serious friction, confusion, or wrong defaults without full blockage
- `P3` is polish or clarity debt discovered during the run

Destination rule:

- `current-milestone-decimal` for urgent blockers that should be fixed before the E2E milestone closes
- `next-milestone-candidate` for important but non-blocking follow-up
- `backlog` for useful but deferred work

Status rule:

- `open`
- `triaged`
- `routed`
- `resolved`
- `deferred`

| issue_id | severity | category | front_door | topic_slug | summary | expected | actual | evidence_ref | discovered_during | proposed_gsd_destination | status |
|----------|----------|----------|------------|------------|---------|----------|--------|--------------|-------------------|--------------------------|--------|
| issue:e2e-proof-engineering-knowledge-gap | P1 | protocol | opencode | jones-von-neumann-algebras | 7 rounds of Lean proof iteration produced zero reusable proof engineering artifacts (construction recipes, tactic workarounds, failure logs). All discoveries live only in conversation handoff context. This violates Phase 165 acceptance criterion "no discovered issue is left only in chat memory". | Proof engineering knowledge should be durably captured as reusable AITP objects. | No canonical L2 family for proof engineering exists with schema and instances. `proof_fragment` is reserved but has no schema. | `evidence/jones-von-neumann-algebras/POSTMORTEM.md` sections "Key Proof Engineering Discoveries" and "What Created Friction" | Lean theorem implementation (rounds 1-7) | v1.91 / Phase 165.1 — define proof_fragment schema + strategy_memory seeding | triaged |
| issue:e2e-strategy-memory-empty | P2 | runtime | opencode | jones-von-neumann-algebras | `strategy_memory.jsonl` mechanism is fully implemented in code (reader in aitp_service.py:954, consumer in mode_learning_support.py) but has zero rows on disk. No strategy lessons were recorded during the entire Jones topic run. | strategy_memory should capture reusable strategy patterns during topic runs. | Code exists but is never called. No rows written. `mode_learning.active` artifacts are never derived from actual proof engineering experience. | `research/knowledge-hub/knowledge_hub/aitp_service.py:954`, `research/knowledge-hub/knowledge_hub/mode_learning_support.py`, acceptance test fixture in `runtime/scripts/run_collaborator_continuity_acceptance.py:161-194` | Post-run analysis of strategy_memory mechanism | v1.91 / Phase 165.1 — seed strategy_memory.jsonl with Jones discoveries | triaged |
| issue:e2e-proof-fragment-no-schema | P2 | protocol | opencode | jones-von-neumann-algebras | `proof_fragment` is listed as one of 23 canonical unit_type families in LAYER2_OBJECT_FAMILIES.md but has no JSON schema file, no payload contract, and zero instances. This is the root cause of issue:e2e-proof-engineering-knowledge-gap. | proof_fragment should have a schema defining construction_steps, common_pitfalls, reuse_conditions fields. | `canonical-unit.schema.json` lists proof_fragment in the enum, but `schemas/proof-fragment.schema.json` does not exist. No payload guidance beyond free-form object. | `research/knowledge-hub/canonical/LAYER2_OBJECT_FAMILIES.md`, `research/knowledge-hub/canonical/canonical-unit.schema.json` | Schema audit for proof engineering capture options | v1.91 / Phase 165.1 — define proof-fragment.schema.json | triaged |
| issue:e2e-negative-result-inactive | P2 | protocol | opencode | jones-von-neumann-algebras | `negative_result` is reserved in L2_MVP_CONTRACT.md and appears in l2-staging-entry.schema.json, but is NOT in the canonical-unit.schema.json unit_type enum and is NOT active. Failed proof approaches (wrong codRestrict, non-existent lemmas) are valuable negative knowledge with no home. | Failed approaches should be recorded as canonical knowledge to prevent re-discovery of the same dead ends. | 6 failed Lean proof rounds produced no negative_result entries. Staging schema has failure_kind/failed_route fields but staging→canonical promotion for negative_result is not implemented. | `research/knowledge-hub/canonical/L2_MVP_CONTRACT.md`, `research/knowledge-hub/schemas/l2-staging-entry.schema.json` | Lean theorem implementation (rounds 1-6 failures) | BACKLOG 999.52 — subsumed by proof-fragment distillation work | triaged |
| issue:e2e-runtime-to-l2-no-promotion | P2 | protocol | opencode | jones-von-neumann-algebras | Runtime proof schemas (`lean-ready-packet`, `proof-repair-plan`, `statement-compilation-packet`) capture proof-level detail but have no promotion pathway to canonical L2. Proof engineering knowledge discovered at runtime stays at runtime. | Runtime proof engineering discoveries should be promotable to canonical L2 as reusable proof_fragment objects. | No promotion route exists from runtime/schemas/ to canonical/. The only promotion paths are L3→L4→L2 and L1→L2, which don't cover runtime proof repair artifacts. | `research/knowledge-hub/runtime/schemas/lean-ready-packet.schema.json`, `research/knowledge-hub/runtime/schemas/proof-repair-plan.schema.json`, `research/knowledge-hub/canonical/PROMOTION_POLICY.md` | Schema audit for promotion path gaps | BACKLOG 999.52 — subsumed by proof-fragment distillation work | triaged |
| issue:template-001 | P2 | ux / runtime / protocol / docs / adapter | codex / claude-code / opencode | demo-topic | Describe the issue clearly. | What should have happened. | What actually happened. | path/to/artifact | command or step | backlog / current-milestone-decimal / next-milestone-candidate | open |

## Notes

- Keep one issue per row.
- Do not merge unrelated symptoms into one row just because they were discovered in the same session.
- Always prefer durable artifact refs over prose-only descriptions.
- If one issue causes another, keep separate rows and link them in the summary text.
