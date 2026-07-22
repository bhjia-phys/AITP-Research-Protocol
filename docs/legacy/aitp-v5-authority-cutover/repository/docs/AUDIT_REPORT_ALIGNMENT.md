# Protocol-Implementation Alignment Audit Report

Date: 2026-04-17
Status: Phase A1 complete (12/12 protocols audited)
Scope: All protocol documents audited against implementation code

---

## Summary

| Protocol | Coverage | Status | Direction |
|----------|----------|--------|-----------|
| brain_protocol | ~85% | Updated | Minor fixes applied |
| closed_loop | ~55-60% | Updated | Major rewrite complete |
| mode_envelope | ~35-40% | Updated | Major rewrite complete |
| H_human_interaction | ~35-40% | Updated | Major rewrite complete |
| promotion_pipeline | ~35-40% | Updated | Major rewrite complete |
| followup_lifecycle | ~70% | Updated | Rewrite complete |
| L1_intake | ~65% | Updated | Rewrite complete |
| L3_execution | ~65% | Updated | Rewrite complete |
| L4_validation | ~42% | Updated | Rewrite complete |
| adapter_interface | ~65% | Updated | Rewrite complete |
| action_queue | ~55-60% | Updated | Major rewrite complete |
| L2_backend_interface | ~68% | Updated | Major rewrite complete |

**Overall**: All 12 protocols audited and updated. Protocols describe the
intended architecture well but diverge significantly from what the code
actually does. The code is richer in some
areas (gap writeback, literature follow-up, decision contracts, L2_auto layer,
formal theory sub-reviews, popup gate protocol, queue shaping policies,
workspace hygiene, Obsidian mirror) and missing in others
(stuckness detection, mode envelope enforcement, symbolic validation,
conformance checking).

**Strategy applied**:
- Where code is richer than protocol: updated protocol to document actual behavior
- Where protocol describes unimplemented features: flagged as implementation tickets (Phase B)
- Where they fundamentally disagree: aligned protocol to code reality

---

## 1. Brain Protocol (85% coverage) — UPDATED

### Protocol accurately describes
- B2 lifecycle: bootstrap, loop, status, complete, with validation and
  promotion handled as loop-triggered operations
- B3 multi-topic management: topic_index, active_topics, scheduler
- B3 dependencies: blocked status
- B4 session chronicle: all 8 required sections
- B5 collaborator memory: profile, strategy memory, trajectory signals
- B6 control note, popup gates, innovation direction
- B7 progressive disclosure: four tiers
- B8 lightweight runtime profile

### Fixes applied to protocol
1. Clarification model: Changed from multi-round to one-shot
2. DAG cycle detection: Marked as required-but-not-yet-implemented
3. Output contract: Softened to match current behavior

---

## 2. Closed-Loop Protocol (55-60% coverage) — UPDATED

### Fixes applied to protocol
- Added 5th phase (dispatch_execution_task)
- Updated result classification to 3-status + contradiction_detected flag
- Updated ingest routing to 4 decisions (keep/revise/discard/defer)
- Added 4 routing modes (heuristic, control_note, declared_contract, decision_contract)
- Added CL5: Follow-up Gap Writeback System
- Added CL6: Literature Follow-up Query System
- Added CL7: Decision Contract System
- Added CL8: Research Mode Profiles
- Added CL9: Post-Promotion Lifecycle
- Added CL10: Implementation Status section

---

## 3. Mode Envelope Protocol (35-40% coverage) — UPDATED

### Fixes applied to protocol
- Migrated the mode system from legacy 4-mode terminology to the canonical
  3-mode protocol (`explore`, `learn`, `implement`)
- Added explicit legacy mapping: `discussion -> explore`, `verify -> learn`,
  and `promote` becomes an operation inside `learn` or `implement`
- Fixed foreground layers to match the 3-mode protocol: `explore` (L0, L1,
  L3), `learn` (L0, L1, L3, L4), `implement` (L3, L4)
- Added ME3: Mode-specific submodes aligned with the canonical 3-mode protocol
- Added ME4: Context-Refocusing Engine
- Fixed default mode: code defaults to "explore"
- Added ME10: Implementation Status section

---

## 4. H Human Interaction Protocol (35-40% coverage) — UPDATED

### Fixes applied to protocol
- Trigger rules changed to open vocabulary with recommended tags
- Clarification model updated to one-shot
- Control note fields documented as partially enforced
- Innovation direction template softened
- Added H9: Implementation Status section

---

## 5. Promotion Pipeline Protocol (35-40% coverage) — UPDATED

### Fixes applied to protocol
- Rewrote around actual three-step model (pending_human_approval → approved → promoted)
- Kept four-stage counting model as aspirational target
- Added P4: L2 Auto Canonical Layer
- Added P5: Staging Bridge
- Added P6: Continue-Decision Readiness Proxy
- Added P8: Post-Promotion Formalization
- Added P11: Implementation Status section

---

## 6. Followup Lifecycle Protocol (~70% coverage) — UPDATED

### Protocol accurately describes
- Sub-topic spawning with rich spawn contract (14+ fields)
- Child lifecycle with return packet population
- Return shape validation against allowlist
- Reintegration with structured receipt (20+ fields)
- Deferred candidate buffer with reactivation conditions

### Fixes applied to protocol
- Updated spawn contract with 14+ actual fields from code
- Added return shape validation (recovered_units, resolved_gap_update, still_unresolved_packet)
- Updated reintegration receipt with 20+ actual fields
- Updated deferred candidate record with actual code fields (entry_id, source_candidate_id, etc.)
- Noted OR-only logic for reactivation
- Added FL4: Candidate Split Contract
- Added FL5: Consultation Followup
- Added FL6: Gap Writeback Queue
- Added FL9: Implementation Status section

### Not yet implemented
- Blocking/non-blocking child semantics
- Priority and deferred_at fields
- Expiration dates and expired status
- AND logic for reactivation conditions
- Auto-triggered reactivation

---

## 7. L1 Intake Protocol (~65% coverage) — UPDATED

### Fixes applied to protocol
- Updated reading depth grades to match code (skim/full_read/multi_pass)
- Added items 6-9: method specificity, concept graph, source intelligence, evidence sentence anchoring
- Updated vault page types from 4 to 6 (added source-bridge, concept-graph/index)
- Updated flowback rule with implementation details
- Added compatibility projection documentation
- Added 1.8: Implementation Status section

### Not yet implemented
- Derivation sketching
- Assumption sub-categorization
- Canonical notation selection
- Research question contract schema validation
- Per-claim provisional marking

---

## 8. L3 Execution Protocol (~65% coverage) — UPDATED

### Protocol accurately describes
- Three sub-planes (L3-A, L3-R, L3-D)
- Candidate management with split contract
- Scratch mode concept
- L3-L4 iterative loop

### Fixes applied to protocol
- Documented auto-promotion bypass of L3-R as controlled exception
- Documented layer graph state machine
- Documented auto-promotion pipeline inline checks
- Documented TPKN backend
- Documented loop detection
- Documented proof engineering distillation
- Updated run record locations to match actual implementation
- Added 3.12: Implementation Status section

### Not yet implemented
- Mandatory evidence_level field on candidates
- Mandatory validation_requirements field on candidates
- Scratch-to-candidate promotion bridge
- Strategy/collaborator memory (cross-topic persistent store)
- L3/runs/<run_id>/ path structure

---

## 9. L4 Validation Protocol (~42% coverage) — UPDATED

### Fixes applied to protocol
- Added coverage estimates per validation type
- Documented formal theory sub-reviews (faithfulness, comparator, provenance, prerequisite)
- Documented validation review bundle aggregation
- Documented analytical cross-check surface
- Documented comparison validation mode
- Documented actual outcome vocabulary (ready/blocked vs 6-outcome)
- Simplified trust audit to match actual records
- Added 4.13: Implementation Status section

### Not yet implemented
- Symbolic validation (SymPy/Mathematica) — 0%
- Full human validation framework — ~10%
- Six-outcome validation vocabulary (only ready/blocked used)
- Full trust audit fields
- Gap classification as first-class dispatch

---

## 10. Adapter Interface (~65% coverage) — UPDATED

### Fixes applied to protocol
- Added AD4: Popup Gate Protocol (from using-aitp skill)
- Added AD5: Conversation Style Rules
- Added AD6: Clarification Sub-Protocol
- Added AD7: Runtime Support Matrix
- Added AD12: Charter Document (noting it doesn't exist yet)
- Documented OpenClaw front-door bypass
- Documented conformance checking as declared-only
- Added AD13: Implementation Status section

### Not yet implemented
- Operational conformance checking in any adapter
- Front-door routing in OpenClaw
- Session chronicle as hard requirement
- Standalone Charter document
- Conformance verification at session end

---

## 11. Action Queue Protocol (~55-60% coverage) — UPDATED

### Protocol accurately describes
- Three queue sources (heuristic, control_note, declared_contract) with priority
- Auto-runnable decision concept
- Decision trace concept
- Pending decisions concept

### Code implements, protocol does NOT describe (update protocol)
1. **Queue shaping policies** — suppress queue expansion based on operator checkpoints, promotion routing, backedge transitions
2. **Closed-loop execution pipeline** — 5-phase cycle in queue construction
3. **Post-promotion followup routing** — multi-step routing with escalating thresholds
4. **Followup subtopic spawning and reintegration** — child topic management in queue
5. **Auto-promotion pipeline** — automatic promotion actions when gates pass
6. **Candidate split contracts** — decompose wide/mixed candidates
7. **Lean bridge preparation** — refresh formal proof-state sidecars
8. **Topic completion gate** — assess when a topic is done
9. **Literature intake staging** — SHA1 signature deduplication
10. **Obsolete action pruning** — remove stale actions
11. **Decision contract override** — separate override mechanism for next-action decision
12. **Topic loop lifecycle** — entry/exit audit, loop state persistence

### Protocol describes, code does NOT implement
1. **Per-action `layer`, `mode`, `inputs`, `expected_outputs` fields** — not on queue rows
2. **Inter-action `blocked_by`** — only inter-topic blocking exists
3. **Circular dependency detection** — no cycle detection algorithm
4. **Unblocking-throughput optimization** — not in ranking policy
5. **Stuckness detection algorithm** — keyword only, no logic
6. **Time-based and state-based deferred reactivation** — not implemented
7. **Per-action `created_at`, `updated_at`** — not on queue rows

### Vocabulary mismatches
- `description` → `summary`, `decision_id` → `id`, `trigger` → `decision_point_ref`
- `decision` → `decision_summary` + `chosen`, `alternatives_considered` → `options_considered`
- `created_at` → `timestamp`, `bridges_to` → `bridged_to`

### Decision trace schema richer than protocol
Implementation has: `options_considered` with structured `pros`/`cons`/`estimated_effort`/`risk_level`,
`would_change_if`, `output_refs`, `layer_transition`, `related_traces`.

### Pending decisions: aggregate vs. individual
Protocol describes per-decision objects; implementation uses aggregate summary
in `pending_decisions.json` with individual decision points in separate files.

---

## 12. L2 Backend Interface (~68% coverage) — UPDATED

### Protocol accurately describes
- Paired backend architecture (human-readable + typed)
- Unit families concept
- Edge layer concept
- Staging and compilation concept
- Consultation mechanism
- Indexing and retrieval concept

### Code implements, protocol does NOT describe (update protocol)
1. **Workspace knowledge report** — change tracking with contradiction watch
2. **Topic L2 corpus baseline** — source anchor resolution, hub/isolation detection
3. **Obsidian L2 mirror** — full Obsidian-compatible Markdown mirror
4. **Workspace hygiene report** — stale summaries, missing bridges, contradictions, orphaned units
5. **Paired backend audit** — drift detection between brain/TPKN backends
6. **Change fingerprinting** — SHA-1 hashing for incremental updates
7. **Derived navigation pages** — per-unit outgoing/incoming relations
8. **Topic source anchor resolution** — staging entries resolved to source anchors

### Major vocabulary mismatches
- Unit types: `definition` → `definition_card`, `theorem` → `theorem_card`, etc.
- Directory layout: `units/` → family-based dirs, `edges/` → `edges.jsonl`
- Edge relations: only 11 of 24 protocol types implemented
- Backbone field names: `type` → `unit_type`, `source_anchors` → `provenance.source_ids`

### Protocol describes, code does NOT implement
1. **queues/, regressions/, sources/ directories** at L2 level
2. **13 of 24 edge relation types** (workflow and code-theory categories missing)
3. **Missing backbone fields**: `aliases`, `formalization_status`
4. **Named index files** at `indexes/` paths (only `canonical/index.jsonl` exists)
5. **Non-trivial consultation trigger** mechanism
6. **Staging entry status vocabulary alignment** (code vs schema inconsistency)

### Schema significantly richer than protocol
Canonical unit schema has: `origin_topic_refs`, `validation_receipts`, `reuse_receipts`,
`related_consultation_refs`, `applicable_topics`, `failed_topics`, all `promotion.*`
sub-fields beyond the basic five.

---

## Consolidated Action Items

### Protocol updates — COMPLETED
- [x] brain: Fix clarification model, DAG cycle detection, output contract
- [x] closed_loop: Major rewrite with 5th phase, result vocabulary, routing modes, gap writeback, literature follow-up, decision contracts, research mode profiles
- [x] mode_envelope: Submodes, context-refocusing, foreground_layers, default mode
- [x] H_interaction: Open vocabulary triggers, one-shot clarification, control note parsing
- [x] promotion_pipeline: Three-step model, L2_auto, staging bridge, post-promotion
- [x] followup_lifecycle: Spawn contract, return shapes, reintegration receipt, deferred buffer
- [x] L1_intake: Reading depths, vault page types, concept graph, source intelligence
- [x] L3_execution: Auto-promotion bypass, layer graph, TPKN, loop detection
- [x] L4_validation: Sub-reviews, bundles, cross-check, outcome vocabulary
- [x] adapter_interface: Popup gates, conversation style, clarification, support matrix
- [x] action_queue: Queue shaping policies, closed-loop pipeline, post-promotion routing, topic loop lifecycle, decision contract override
- [x] L2_backend: Workspace knowledge report, corpus baseline, Obsidian mirror, hygiene report, paired backend audit, change fingerprinting

### Flagged as implementation tickets (Phase B)
- [ ] Closed-loop: popup gate check at select_route
- [ ] Closed-loop: mode envelope validation at materialize_task
- [ ] Closed-loop: previous-cycle writeback enforcement
- [ ] Closed-loop: stuckness detection system
- [ ] Closed-loop: await_external_result timeout tracking
- [ ] Closed-loop: forbidden proxies guardrail
- [ ] Closed-loop: human checkpoint cycle limit
- [ ] Mode envelope: transition graph enforcement
- [ ] H_interaction: popup gate implementation in H-plane handlers
- [ ] H_interaction: clarification round limit enforcement
- [ ] H_interaction: human edit detection
- [ ] Promotion: wide candidate individual child promotion
- [ ] Brain: multi-round clarification (if desired)
- [ ] Brain: DAG cycle detection
- [ ] L3: mandatory evidence_level and validation_requirements fields
- [ ] L3: scratch-to-candidate promotion bridge
- [ ] L3: strategy/collaborator memory
- [ ] L4: symbolic validation (SymPy/Mathematica)
- [ ] L4: full human validation framework
- [ ] L4: six-outcome validation vocabulary
- [ ] L4: full trust audit fields
- [ ] L4: gap classification dispatch
- [ ] Adapter: operational conformance checking
- [ ] Adapter: front-door routing in OpenClaw
- [ ] Adapter: session chronicle hard requirement
- [ ] Adapter: standalone Charter document
- [ ] Followup: blocking child semantics
- [ ] Followup: AND logic reactivation conditions
- [ ] Followup: auto-triggered reactivation
- [ ] L1: derivation sketching
- [ ] L1: canonical notation selection
- [ ] Action queue: per-action layer, mode, inputs, expected_outputs fields
- [ ] Action queue: inter-action blocked_by
- [ ] Action queue: circular dependency detection
- [ ] Action queue: unblocking-throughput optimization
- [ ] Action queue: stuckness detection algorithm
- [ ] Action queue: time-based and state-based deferred reactivation
- [ ] L2: queues/, regressions/, sources/ directories at canonical level
- [ ] L2: full 24-type edge relation vocabulary
- [ ] L2: missing backbone fields (aliases, formalization_status)
- [ ] L2: named index files at protocol-specified paths
- [ ] L2: non-trivial consultation trigger mechanism
- [ ] L2: staging entry status vocabulary alignment
