# AITP test runbook

Use this runbook for the next honest AITP tests.

## 1. Platform gate

Check the host and chat surfaces first:

```bash
openclaw status
openclaw channels status --probe --json
systemctl --user status openclaw-gateway.service --no-pager
```

Pass condition:
- gateway running
- Feishu probe healthy
- intended agent/session visible

## 2. Kernel gate

Check that the kernel itself is healthy:

```bash
aitp doctor
aitp state --topic-slug <topic_slug>
aitp capability-audit --topic-slug <topic_slug>
```

Pass condition:
- CLI installed
- runtime state readable
- capability audit not obviously broken

## 3. Single-step loop smoke test

Run one bounded step only:

```bash
aitp loop \
  --topic-slug <topic_slug> \
  --updated-by manual-smoke \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- `runtime/topics/<topic_slug>/loop_state.json` updates
- conformance remains truthful
- no fake scientific success is claimed

## 4. Heartbeat semantic test

The heartbeat policy should now prefer:

```bash
aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Test either by:
- waiting for the scheduled heartbeat,
- or manually sending the configured heartbeat prompt through the bound chat surface.

Pass condition:
- heartbeat follows `HEARTBEAT.md`
- if AITP is selected, it follows `HEARTBEAT_AITP.md`
- ack stays short and truthful

## 5. Feishu end-to-end test

From Feishu DM, ask for:
- a small runtime read
- one bounded execution step

Suggested checks:
- read `loop_state`
- run the generic OpenClaw plugin smoke script:
  - `research/adapters/openclaw/scripts/run_openclaw_plugin_smoke.sh`

Pass condition:
- transport works
- runtime state is readable
- bounded OpenClaw/AITP handoff is truthful

## 6. L2 backend bridge test: note-library backend

Pick one real note from a backend that you have already registered under
`canonical/backends/`.

For the public formal-theory example route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
```

That script creates one temporary external formal-theory note backend, realizes
the public example backend card against it, registers one note into `L0`, and
runs one bounded `aitp loop`.

Register it into `L0`:

```bash
python3 research/knowledge-hub/source-layer/scripts/register_local_note_source.py \
  --topic-slug <topic_slug> \
  --path "<absolute-note-path>" \
  --registered-by backend-bridge-smoke
```

Then run one bounded loop step that explicitly mentions the backend:

```bash
aitp loop \
  --topic-slug <topic_slug> \
  --human-request "Use the registered human-note backend as a bounded knowledge bridge, but keep all conclusions operator-visible." \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- note is registered in `L0`
- runtime artifacts remain operator-visible
- no direct folder-level canonicalization happens

## 7. L2 backend bridge test: software backend

Do not start with heavy execution.
Start with docs/tests/method context.

Use a registered software backend card from `canonical/backends/`.

Goal:
- seed one `method`, `workflow`, or `validation_pattern` candidate from software knowledge
- keep reproducibility paths explicit

Pass condition:
- AITP can reference the backend coherently
- no black-box code claims
- paths to code/tests/results remain durable

For the public toy-model numeric starter route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_toy_model_numeric_backend_smoke.sh
```

That script creates one temporary external toy-model backend, runs a tiny
public TFIM exact-diagonalization helper on a fixed config, registers the
generated run note into `L0`, and runs one bounded `aitp loop`.

## 8. Exit gate

Close with:

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

The run only counts if exit conformance is still honest.

## 9. Real-topic acceptance: scRPA thesis lane

Use this when you want a real formal-theory topic acceptance that starts from
the master's-thesis scRPA material instead of a synthetic smoke payload.

```bash
python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json
```

Pass condition:
- the topic lands in the `formal_theory` lane
- the runtime stays in the `light` profile
- `topic_synopsis.json`, `pending_decisions.json`, and `promotion_readiness.json` are materialized
- the topic remains honest about still needing thesis-grounded source/candidate tightening before any stronger closure claim

## 10. Real-topic acceptance: Jones Chapter 4 finite-product lane

Use this when you want a real formal-theory acceptance pass on the active Jones
benchmark topic rather than on a disposable synthetic theorem card.

```bash
python research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py --json
```

Pass condition:
- the active `jones-von-neumann-algebras` topic gets a new bounded Chapter 4 candidate run
- `coverage_ledger.json`, `formal_theory_review.json`, `proof_obligations.json`, and `proof_state.json` are materialized for that candidate
- `topic_skill_projection.active.json|md` is materialized and surfaced through runtime status as a `formal_theory` projection
- the projection is human-promoted into `units/topic-skill-projections/`
- the Lean bridge packet is `ready`
- `promotion_gate.json` ends in `promoted` and the promoted unit lands in `L2_auto`
- the resulting packet stays honest about not yet proving the stronger algebra-level product theorem or the later whole-book routes

## 11. Real-topic acceptance: code-backed benchmark-first lane

Use this when you want a real code-backed topic acceptance that keeps a tiny
exact benchmark in front of broader workflow claims.

```bash
python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json
```

Pass condition:
- the topic lands in the `code_method` lane
- the runtime stays in the `light` profile
- a coding operation manifest exists and passes the baseline-first trust audit
- run-local strategy memory is recorded and surfaced through runtime status

## 12. Isolated acceptance: L2 MVP direction

Use this when you want a bounded proof that the MVP `L2` memory surface is
operational without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py --json
```

Pass condition:
- the TFIM MVP direction is seeded through production CLI
- `consult-l2` returns the seeded `physical_picture`
- `compile-l2-map` writes `workspace_memory_map.json|md`
- `compile-l2-graph-report` writes `workspace_graph_report.json|md`
- `compile-l2-graph-report` writes `derived_navigation/index.md`
- `compile-l2-knowledge-report` writes `workspace_knowledge_report.json|md`
- `audit-l2-hygiene` writes `workspace_hygiene_report.json|md`
- the acceptance runs on an isolated temp kernel root

## 12.5. Isolated acceptance: compiled knowledge report

Use this when you want one bounded proof that the compiled-knowledge surface is
operational without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_l2_knowledge_report_acceptance.py --json
```

Pass condition:
- `compile-l2-knowledge-report` writes `workspace_knowledge_report.json|md`
- the report includes canonical and non-authoritative staging rows
- the second compile detects the previous compiled snapshot
- the report surfaces at least one contradiction-watch row after a staged
  negative result
- the acceptance runs on an isolated temp kernel root

## 13. Isolated acceptance: source catalog and citation reuse

Use this when you want a bounded proof that the Layer 0 source-reuse surface is
operational without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_source_catalog_acceptance.py --json
```

Pass condition:
- `compile-source-catalog` writes `source_catalog.json|md`
- `trace-source-citations` writes one bounded traversal artifact
- `compile-source-family` writes one family reuse artifact
- `export-source-bibtex` writes one bounded `.bib` export artifact
- `import-bibtex-sources` writes one bounded Layer 0 import report and source row
- `status --json` surfaces source fidelity for the active topic
- the acceptance runs on an isolated temp kernel root

## 13.25. Isolated acceptance: source discovery -> registration

Use this when you want one bounded proof that `L0` can start from a
natural-language search query, evaluate candidates explicitly, and still land
on the canonical registration path without mutating repo runtime state.

```bash
python research/knowledge-hub/runtime/scripts/run_l0_source_discovery_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_enrichment_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_concept_graph_acceptance.py --json
```

Pass condition:
- `discover_and_register.py` writes a durable `discoveries/<discovery_id>/` receipt set
- `candidate_evaluation.json` keeps the winning arXiv candidate explicit
- `registration_receipt.json` points back to the usual Layer 0 source paths
- integrated enrichment writes `deepxiv_enrichment.json`
- integrated concept-graph build writes `concept_graph.json` and `concept_graph_receipt.json`
- `source-layer/topics/<topic_slug>/source_index.jsonl` and `source-layer/global_index.jsonl` are updated
- the intake projection mirrors the selected registered source
- the acceptance runs on an isolated temp kernel root

## 13.5. Isolated acceptance: L1 method specificity

Use this when you want one bounded proof that source-backed method specificity
is visible through the real runtime status surface.

```bash
python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `method_specificity_rows` inside `l1_source_intake`
- at least one `formal_derivation` or `numerical_benchmark` row appears
- `research_question.contract.md` includes a `## Method specificity` section
- the runtime protocol note also includes `## Method specificity`
- the acceptance runs on an isolated temp kernel root

## 13.6. Isolated acceptance: L1 assumptions and reading depth

Use this when you want one bounded proof that source-backed assumptions,
reading-depth limits, and conflict honesty are visible through the real runtime
status surface.

```bash
python research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `assumption_rows` and `reading_depth_rows` inside `l1_source_intake`
- `status --json` keeps contradiction or weak-evidence honesty explicit on the same surface
- `research_question.contract.md` includes `## Source-backed assumptions` plus `## Reading-depth limits`
- `topic_dashboard.md` keeps the derived reading-depth/conflict ambiguity explicit
- the runtime protocol note keeps the same assumption/depth honesty visible
- `intake/topics/<topic_slug>/vault/wiki/source-intake.md` keeps assumptions and reading depth visible
- the acceptance runs on an isolated temp kernel root

## 13.7. Isolated acceptance: L1 concept graph

Use this when you want one bounded proof that source-local concept-graph
artifacts are visible through the real runtime status surface.

```bash
python research/knowledge-hub/runtime/scripts/run_l1_concept_graph_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `l1_source_intake.concept_graph`
- `research_question.contract.md` includes `## Concept graph`
- the runtime protocol note includes `## Concept graph`
- `intake/topics/<topic_slug>/vault/wiki/source-intake.md` includes `## Concept graph`
- the acceptance runs on an isolated temp kernel root

## 13.65. Isolated acceptance: runtime transition and demotion history

Use this when you want one bounded proof that runtime history can show how a
topic moved across layers, including a bounded backtrack/demotion, without
reconstructing the path from scattered notes.

```bash
python research/knowledge-hub/runtime/scripts/run_transition_history_acceptance.py --json
```

Pass condition:
- production `request-promotion` and `reject-promotion` leave durable history rows
- `status --json` materializes `transition_history.jsonl|json|md`
- the history includes at least one backedge / demotion row with an explicit reason
- `replay-topic --json` surfaces the latest demotion reason and includes transition history in the reading path
- the acceptance runs on an isolated temp kernel root

## 13.7. Isolated acceptance: promotion-gate human modification record

Use this when you want one bounded proof that a human approval can record what
changed and why, instead of flattening all approvals into the same surface.

```bash
python research/knowledge-hub/runtime/scripts/run_human_modification_record_acceptance.py --json
```

Pass condition:
- production `approve-promotion --human-modification` records structured modification rows
- `promotion_gate.json|md` keeps the modification record durable and readable
- replay surfaces distinguish `approved_as_submitted` from `approved_with_modifications`
- the acceptance runs on an isolated temp kernel root

## 13.72. Isolated acceptance: competing hypotheses on the active question

Use this when you want one bounded proof that multiple plausible answers stay
visible on the active research-question surface instead of being reconstructed
indirectly from other runtime artifacts.

```bash
python research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `competing_hypotheses` on the active research contract
- `research_question.contract.md` and the runtime protocol note both include a
  `## Competing hypotheses` section
- `replay-topic --json` surfaces the competing-hypothesis count plus the
  current leading hypothesis
- deferred candidates and follow-up subtopics remain visible as separate
  runtime surfaces
- the acceptance runs on an isolated temp kernel root

## 13.73. Isolated acceptance: hypothesis branch routing

Use this when you want one bounded proof that each competing hypothesis can
carry explicit branch intent instead of forcing operators to infer routing from
separate runtime surfaces.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_branch_routing_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `active_branch_hypothesis_id`,
  `deferred_branch_hypothesis_ids`, and `followup_branch_hypothesis_ids`
- `research_question.contract.md` and the runtime protocol note both show route
  kind plus target summary for each hypothesis
- `replay-topic --json` surfaces the active branch hypothesis plus deferred and
  follow-up route counts
- deferred parking, follow-up subtopics, and steering artifacts remain present
  as separate runtime surfaces
- the acceptance runs on an isolated temp kernel root

## 13.74. Isolated acceptance: hypothesis route activation

Use this when you want one bounded proof that the active local route and the
parked-route obligations are visible directly, without auto-spawning a new
branch execution lane.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_activation_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_activation.active_local_hypothesis_id`,
  `active_local_action_summary`, and both parked-obligation lanes
- `runtime_protocol.generated.md` includes `## Route activation` plus the
  deferred/follow-up obligation sections
- `replay-topic --json` surfaces `route_activation` and the parked-route count
- deferred parking and follow-up obligations stay explicit without auto-spawning
  a follow-up topic directory
- the acceptance runs on an isolated temp kernel root

## 13.75. Isolated acceptance: hypothesis route re-entry

Use this when you want one bounded proof that parked-route reactivation
conditions and child follow-up return readiness are visible directly, without
auto-reactivating candidates or mutating the parent topic.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_reentry_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_reentry.reentry_ready_count` plus both
  deferred and follow-up parked-route lanes
- `runtime_protocol.generated.md` includes `## Route re-entry` plus per-route
  re-entry status and condition summaries
- `replay-topic --json` surfaces `route_reentry` and the re-entry-ready count
- deferred reactivation conditions and follow-up return contracts stay explicit
  without writing a reintegration receipt or materializing a reactivated
  deferred candidate
- the acceptance runs on an isolated temp kernel root

## 13.76. Isolated acceptance: hypothesis route handoff

Use this when you want one bounded proof that ready parked routes turn into one
explicit handoff candidate plus explicit keep-parked decisions, without
auto-reactivating or auto-reintegrating anything.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_handoff_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_handoff.primary_handoff_candidate_id`,
  `handoff_candidate_count`, and both handoff-candidate / keep-parked lanes
- `runtime_protocol.generated.md` includes `## Route handoff` plus per-route
  handoff status and condition summaries
- `replay-topic --json` surfaces `route_handoff` and the handoff-candidate
  count
- one ready parked route can occupy the bounded handoff lane while another
  ready parked route stays explicitly parked
- the bounded slice does not write a reintegration receipt or materialize a
  reactivated deferred candidate
- the acceptance runs on an isolated temp kernel root

## 13.77. Isolated acceptance: hypothesis route choice

Use this when you want one bounded proof that the current local route can stay
explicitly local while the primary handoff candidate remains visible as the
yield option, without automatic route mutation.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_choice_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_choice.choice_status`,
  `active_local_hypothesis_id`, and `primary_handoff_candidate_id`
- `runtime_protocol.generated.md` includes `## Route choice` plus the
  stay-local and yield-to-handoff options
- `replay-topic --json` surfaces `route_choice` and the route-choice status
- the bounded slice stays on the local route while keeping the handoff
  candidate visible, without writing a reintegration receipt or materializing a
  reactivated deferred candidate
- the acceptance runs on an isolated temp kernel root

## 13.78. Isolated acceptance: hypothesis route transition gate

Use this when you want one bounded proof that AITP makes route-transition
eligibility explicit instead of leaving blocked versus available yielding
implicit across separate route-choice and checkpoint artifacts.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_gate_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_gate.transition_status`,
  `gate_kind`, and the durable gate artifact ref
- `runtime_protocol.generated.md` includes `## Route transition gate`
- `replay-topic --json` surfaces `route_transition_gate` and the
  route-transition-gate status on both current-position and conclusions lanes
- the acceptance proves blocked, available, and checkpoint-required yielding on
  an isolated temp kernel root
- the bounded slice does not auto-reactivate or auto-reintegrate parked routes

## 13.79. Isolated acceptance: hypothesis route transition intent

Use this when you want one bounded proof that AITP makes the declarative
source-to-target handoff explicit after route-transition gating, instead of
leaving the intended transition implicit across separate route-choice and
gate artifacts.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_intent_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_intent.intent_status`, the source
  hypothesis, and the target hypothesis
- `runtime_protocol.generated.md` includes `## Route transition intent`
- `replay-topic --json` surfaces `route_transition_intent` and the
  route-transition-intent status on both current-position and conclusions lanes
- the acceptance proves proposed, ready, and checkpoint-held transition intent
  on an isolated temp kernel root
- the bounded slice does not auto-reactivate or auto-reintegrate parked routes

## 13.80. Isolated acceptance: hypothesis route transition receipt

Use this when you want one bounded proof that AITP makes completed bounded
handoff receipt explicit instead of leaving enacted route change implicit after
transition intent.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_receipt_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_receipt.receipt_status`, the
  source hypothesis, and the target hypothesis
- `runtime_protocol.generated.md` includes `## Route transition receipt`
- `replay-topic --json` surfaces `route_transition_receipt` and the
  route-transition-receipt status on both current-position and conclusions lanes
- the acceptance proves pending, recorded, and none transition-receipt states
  on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.81. Isolated acceptance: hypothesis route transition resolution

Use this when you want one bounded proof that AITP makes the resolved handoff
outcome explicit instead of leaving operators to compare transition intent,
transition receipt, and active-route state manually.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_resolution_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_resolution.resolution_status`,
  `receipt_status`, and `active_route_alignment`
- `runtime_protocol.generated.md` includes `## Route transition resolution`
- `replay-topic --json` surfaces `route_transition_resolution` and the
  route-transition-resolution status on both current-position and conclusions lanes
- the acceptance proves pending, resolved, and none transition-resolution
  states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.82. Isolated acceptance: hypothesis route transition discrepancy

Use this when you want one bounded proof that AITP makes inconsistent
route-transition state explicit instead of leaving operators to compare
resolution and upstream route artifacts manually.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_discrepancy_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_discrepancy.discrepancy_status`,
  `discrepancy_kind`, and `severity`
- `runtime_protocol.generated.md` includes `## Route transition discrepancy`
- `replay-topic --json` surfaces `route_transition_discrepancy` directly
- the acceptance proves present versus none transition-discrepancy states on an
  isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83. Isolated acceptance: hypothesis route transition repair

Use this when you want one bounded proof that AITP turns transition discrepancy
into one explicit bounded repair plan instead of leaving the operator to infer
how to reconcile the affected route artifacts.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_repair_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_repair.repair_status`,
  `repair_kind`, and the repair artifact refs
- `runtime_protocol.generated.md` includes `## Route transition repair`
- `replay-topic --json` surfaces `route_transition_repair` directly
- the acceptance proves `recommended` versus `none_required`
  transition-repair states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.5. Isolated acceptance: hypothesis route transition escalation

Use this when you want one bounded proof that AITP makes it explicit when
transition repair should stay local, recommend a checkpoint, or acknowledge
that the checkpoint is already active.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_escalation_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_escalation.escalation_status`,
  repair state, and checkpoint refs
- `runtime_protocol.generated.md` includes `## Route transition escalation`
- `replay-topic --json` surfaces `route_transition_escalation` directly
- the acceptance proves `none`, `checkpoint_recommended`, and
  `checkpoint_active` states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.6. Isolated acceptance: hypothesis route transition clearance

Use this when you want one bounded proof that AITP makes it explicit whether an
escalated transition is still awaiting a checkpoint, currently blocked on one,
or has already been cleared back into bounded follow-through.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_clearance_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_clearance.clearance_status`,
  clearance kind, and follow-through refs
- `runtime_protocol.generated.md` includes `## Route transition clearance`
- `replay-topic --json` surfaces `route_transition_clearance` directly
- the acceptance proves `none`, `awaiting_checkpoint`,
  `blocked_on_checkpoint`, and `cleared` states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.7. Isolated acceptance: hypothesis route transition followthrough

Use this when you want one bounded proof that AITP makes it explicit what
transition work should resume after clearance, while still keeping any
pre-clearance hold state visible instead of silently resuming.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_followthrough_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_followthrough.followthrough_status`,
  follow-through kind, and authoritative follow-through refs
- `runtime_protocol.generated.md` includes `## Route transition follow-through`
- `replay-topic --json` surfaces `route_transition_followthrough` directly
- the acceptance proves `none`, `held_by_clearance`, and `ready` states on an
  isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.8. Isolated acceptance: hypothesis route transition resumption

Use this when you want one bounded proof that AITP makes it explicit whether
ready follow-through is still waiting, still pending on the bounded route, or
has already been durably resumed.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_resumption_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_resumption.resumption_status`,
  resumption kind, and durable resumption refs
- `runtime_protocol.generated.md` includes `## Route transition resumption`
- `replay-topic --json` surfaces `route_transition_resumption` directly
- the acceptance proves `none`, `waiting_followthrough`, `pending`, and
  `resumed` states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.9. Isolated acceptance: hypothesis route transition commitment

Use this when you want one bounded proof that AITP makes it explicit whether a
resumed route is still not ready for commitment, still pending commitment, or
has already become the durable committed bounded lane.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_commitment_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_commitment.commitment_status`,
  commitment kind, and durable commitment refs
- `runtime_protocol.generated.md` includes `## Route transition commitment`
- `replay-topic --json` surfaces `route_transition_commitment` directly
- the acceptance proves `none`, `waiting_resumption`,
  `pending_commitment`, and `committed` states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.83.10. Isolated acceptance: hypothesis route transition authority

Use this when you want one bounded proof that AITP makes it explicit whether a
committed route is still waiting on commitment, still not authoritative across
current-topic truth surfaces, or has already become the authoritative bounded
truth.

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_authority_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `route_transition_authority.authority_status`,
  authority kind, and the current commitment/authority refs
- `runtime_protocol.generated.md` includes `## Route transition authority`
- `replay-topic --json` surfaces `route_transition_authority` directly
- the acceptance proves `none`, `waiting_commitment`,
  `pending_authority`, and `authoritative` states on an isolated temp kernel root
- the bounded slice does not widen into fresh runtime mutation

## 13.84. Isolated acceptance: L1 raw/wiki/output vault

Use this when you want one bounded proof that the `L1` three-layer vault is
live on the real topic-shell/status path.

```bash
python research/knowledge-hub/runtime/scripts/run_l1_vault_acceptance.py --json
```

Pass condition:
- `status --json` surfaces `l1_vault` inside the active research contract
- `intake/topics/<topic_slug>/vault/raw|wiki|output` is materialized on an
  isolated temp kernel root
- the wiki home page has frontmatter and wikilinks
- `output/flowback.jsonl` records explicit applied flowback receipts
- `research_question.contract.md` and the runtime protocol note both include
  a `## L1 vault` section

## 13.9. Isolated acceptance: statement compilation and proof repair

Use this when you want one bounded proof that AITP compiles bounded theory
statements before trying to repair proofs or export them downstream.

```bash
python research/knowledge-hub/runtime/scripts/run_statement_compilation_acceptance.py --json
```

Pass condition:
- production `statement-compilation --json` writes `statement_compilation.active.json|md`
- one candidate packet writes `statement_compilation.json` and
  `proof_repair_plan.json`
- the packet exposes declaration skeletons plus proof-assistant-agnostic
  downstream targets
- production `lean-bridge --json` consumes those upstream packet refs instead
  of hiding statement compilation inside the Lean packet

## 14. Isolated acceptance: analytical review and research judgment

Use this when you want one bounded proof that analytical review and
research-judgment runtime surfaces are both live through production CLI.

```bash
python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json
```

Pass condition:
- `analytical-review` writes a durable `analytical_review.json`
- `verify --mode analytical` makes `analytical_review` the primary review bundle surface
- `status --json` surfaces `research_judgment.active.json|md`
- runtime focus exposes `momentum`, `stuckness`, and `surprise`
- the acceptance runs on an isolated temp kernel root

## 15. Isolated acceptance: collaborator continuity

Use this when you want one bounded proof that collaborator continuity surfaces
are live through production CLI restart paths.

```bash
python research/knowledge-hub/runtime/scripts/run_collaborator_continuity_acceptance.py --json
```

Pass condition:
- `focus-topic` materializes current-topic compatibility state
- `status --json` surfaces `collaborator_profile.active.json|md`
- `status --json` surfaces `research_trajectory.active.json|md`
- `status --json` surfaces `mode_learning.active.json|md`
- `current-topic --json` exposes continuity summaries for all three surfaces
- `session-start --json` carries continuity note paths into session-start artifacts
- the acceptance runs on an isolated temp kernel root

## 16. Isolated acceptance: quick exploration

Use this when you want one bounded proof that lightweight exploration is a
first-class path and can promote into normal topic work explicitly.

```bash
python research/knowledge-hub/runtime/scripts/run_quick_exploration_acceptance.py --json
```

Pass condition:
- `explore --json` writes `runtime/explorations/<exploration_id>/explore_session.json|md`
- quick exploration reports a lighter artifact footprint than full topic bootstrap
- `promote-exploration --current-topic --json` writes `promotion_request.json|md`
- promotion materializes a bounded `session-start` contract for the target topic
- the acceptance runs on an isolated temp kernel root

## 17. Isolated acceptance: first-run topic quickstart

Use this when you want one bounded proof that a fresh user can pass through the
shared first-run CLI path without jumping straight into deeper runtime work.

```bash
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json
```

Pass condition:
- `bootstrap --json` creates a real topic shell for a non-synthetic topic
- `loop --json` keeps the topic in the light runtime profile and writes `loop_state.json`
- `status --json` exposes the same topic slug plus the next bounded action
- the runtime protocol survives all three commands
- the acceptance runs on an isolated temp kernel root

## 17.1 Isolated acceptance: first-source follow-through into staged L2

Use this when you want one bounded proof that the same fresh-topic lane can
continue one honest step past first-source registration and surface the staged
L2 review point instead of repeating literature-intake staging forever.

```bash
python research/knowledge-hub/runtime/scripts/run_first_source_followthrough_acceptance.py --json
```

Pass condition:
- the fresh-topic lane still reaches the post-registration
  `literature_intake_stage` follow-through step
- one bounded `literature_intake_stage` auto action completes successfully
- `status --json` then advances to `Inspect the current L2 staging manifest
  before continuing.`
- the workspace staging manifest exists under `canonical/staging/`
- `consult_l2(include_staging=True)` returns at least one staged hit from the
  current fresh topic

## 18. Isolated acceptance: public install smoke

Use this when you want one bounded proof that the published-style
`aitp-kernel` wheel really installs and runs outside the repository.

```bash
python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json
```

Pass condition:
- a clean virtualenv installs the locally built `aitp-kernel` wheel
- `aitp --version` returns the expected semver from the installed CLI
- `aitp doctor --json` materializes the bundle into isolated `AITP_HOME/kernel`
- `bootstrap --json`, `loop --json`, and `status --json` all succeed from the
  installed wheel under isolated roots, not through repo-local `PYTHONPATH`

## 19. Shared acceptance: runtime deep-execution parity baseline

Use this when you want one bounded proof of the current Codex baseline for
deep-execution parity work.

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime codex --json
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime claude_code --json
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime opencode --json
```

Pass condition:
- the report status is `baseline_ready`
- the report records Codex as the baseline runtime for parity work
- the checked artifacts include `topic_state`, `loop_state`, and
  `runtime_protocol.generated.json|md`
- the report stays explicit that front-door readiness and deep-execution parity
  are different surfaces

For the Claude Code slice:
- the report status is `probe_completed_with_gap`
- the checked artifacts include the installed Claude SessionStart assets plus
  durable AITP runtime artifacts for the bounded topic
- the report includes both `matches_codex_baseline` and
  `falls_short_of_codex_baseline`
- the report stays explicit that the live Claude chat turn itself is not yet
  closed as full parity

For the OpenCode slice:
- the report status is `probe_completed_with_gap`
- the checked artifacts include the installed OpenCode plugin assets plus
  durable AITP runtime artifacts for the bounded topic
- the report includes both `matches_codex_baseline` and
  `falls_short_of_codex_baseline`
- the report stays explicit that the live OpenCode app session itself is not
  yet closed as full parity

## 20. Shared closure audit: cross-runtime parity summary

Use this when you want the final `v1.67` closure report across Codex, Claude
Code, and OpenCode.

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_audit.py --json
```

Pass condition:
- the report status is `audited_with_open_gaps` or `parity_verified`
- the report contains all three runtime reports
- the report names `equivalent_surfaces`
- the report names `degraded_surfaces`
- the report names `open_gaps` rather than hiding them

When you have real live-app first-turn evidence for Claude Code and/or
OpenCode, write one file per runtime using
`runtime/schemas/runtime-live-first-turn-evidence.schema.json` and name them:

- `claude_code.live-first-turn.json`
- `opencode.live-first-turn.json`

Then rerun the closure audit with:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_audit.py --live-evidence-root <evidence_dir> --json
```

Additional pass condition for live closure:
- the audit reports `runtime_live_first_turn_evidence` under the supplied evidence
- the audit only removes `live_first_turn_bootstrap_consumption` from degraded surfaces when the evidence status is `verified`
- the evidence checks explicitly confirm the bootstrap was consumed before the first substantive action and that the human-control/autonomy posture remained visible
