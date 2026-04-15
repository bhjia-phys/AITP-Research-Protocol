# Runtime resume surface

This directory is the cross-layer runtime registry for AITP topics.

It is not a new epistemic layer.
It is a durable control surface that summarizes where a topic currently stands across `L1`, `L3`, `L4`, and `consultation`, so the next agent can resume from disk without reconstructing state by hand.
The same runtime surface should remain usable whether a clone is doing formal
theory work, toy-model numerics, or code-backed algorithm development.

## Purpose

Use `runtime/` to answer three operational questions quickly:

1. what is the latest durable state of a topic,
2. which layer should resume next,
3. which concrete files should be opened first.

The runtime surface should answer those questions with lossless progressive
disclosure.
See `runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`.
The runtime should also keep `RESEARCH_EXECUTION_GUARDRAILS.md` visible so the
next agent cannot quietly replace declared deliverables or substitute proxy
evidence for actual validation.
The generated JSON bundle now also carries a stable public schema contract so
external executors can consume trigger semantics without parsing markdown prose.
When deeper proof, gap, fusion, or verification triggers fire, the runtime
surface must point back to the matching top-level kernel contracts rather than
hiding those rules inside handler code.

## Layout

- `topics/<topic_slug>/runtime/topic_state.json`
  - machine-readable topic snapshot
- `topics/<topic_slug>/runtime/resume.md`
  - human-readable resume brief
- `topics/<topic_slug>/runtime/interaction_state.json`
  - machine-readable human-input, autonomy, and layer-edit contract
- `topics/<topic_slug>/runtime/idea_packet.json`
  - machine-readable research-intent gate for idea-first or vague-topic starts
- `topics/<topic_slug>/runtime/idea_packet.md`
  - human-readable idea packet with novelty target, non-goals, first validation route, and evidence bar
- `topics/<topic_slug>/runtime/operator_checkpoint.active.json`
  - machine-readable active human-checkpoint surface
- `topics/<topic_slug>/runtime/operator_checkpoint.active.md`
  - human-readable active operator checkpoint
- `topics/<topic_slug>/runtime/operator_checkpoints.jsonl`
  - append-only checkpoint ledger across requested/answered/superseded/cancelled states
- `topics/<topic_slug>/runtime/operator_console.md`
  - legacy compatibility operator view of the active loops and editable surfaces
- `topics/<topic_slug>/runtime/topic_synopsis.json`
  - authoritative machine-readable runtime synopsis for operator-facing concerns such as current status summary, next action, human need, dependency posture, and truth-source paths
- `topics/<topic_slug>/runtime/topic_dashboard.md`
  - primary human-readable render of the runtime synopsis and explainability surface
- `topics/<topic_slug>/runtime/validation_review_bundle.active.json`
  - primary machine-readable `L4` review bundle for the active topic/run before specialist review files are inspected
- `topics/<topic_slug>/runtime/validation_review_bundle.active.md`
  - primary human-readable `L4` review bundle
- `topics/<topic_slug>/runtime/research_judgment.active.json`
  - machine-readable momentum / stuckness / surprise judgment surface for the active bounded route
- `topics/<topic_slug>/runtime/research_judgment.active.md`
  - human-readable research judgment summary with durable signal refs
- `topics/<topic_slug>/runtime/collaborator_profile.active.json`
  - machine-readable topic-scoped collaborator profile derived from runtime collaborator memory
- `topics/<topic_slug>/runtime/collaborator_profile.active.md`
  - human-readable collaborator profile summary for restart continuity
- `topics/<topic_slug>/runtime/research_trajectory.active.json`
  - machine-readable recent trajectory continuity surface derived from trajectory memory
- `topics/<topic_slug>/runtime/research_trajectory.active.md`
  - human-readable recent trajectory carryover summary
- `topics/<topic_slug>/runtime/mode_learning.active.json`
  - machine-readable learned route and lane guidance derived from durable strategy-memory rows
- `topics/<topic_slug>/runtime/mode_learning.active.md`
  - human-readable mode-learning guidance for restart and route reuse
- `topics/<topic_slug>/runtime/runtime_protocol.generated.json`
  - derived progressive-disclosure bundle for external executors and session bootstrap
- `topics/<topic_slug>/runtime/runtime_protocol.generated.md`
  - derived human-readable render of the progressive-disclosure bundle
- `topics/<topic_slug>/runtime/topic_skill_projection.active.json`
  - machine-readable reusable execution projection derived from a mature topic when the lane is stable enough
- `topics/<topic_slug>/runtime/topic_skill_projection.active.md`
  - human-readable topic-skill projection with required reads, route rules, and anti-proxy constraints
- `topics/<topic_slug>/runtime/statement_compilation.active.json`
  - machine-readable statement-compilation index for bounded declaration skeletons before proof repair
- `topics/<topic_slug>/runtime/statement_compilation.active.md`
  - human-readable statement-compilation summary with proof-hole counts and packet refs
- `topics/<topic_slug>/runtime/transition_history.jsonl`
  - append-only structured transition log for bounded forward/backward layer moves
- `topics/<topic_slug>/runtime/transition_history.json`
  - machine-readable transition/demotion summary for the active topic
- `topics/<topic_slug>/runtime/transition_history.md`
  - human-readable transition/demotion replay note
- `topics/<topic_slug>/runtime/promotion_gate.json`
  - machine-readable human approval gate including optional `human_modifications`
- `topics/<topic_slug>/runtime/promotion_gate.md`
  - human-readable approval gate note with modification summaries when approval changed the candidate
- `topics/<topic_slug>/runtime/loop_state.json`
  - latest loop-level execution summary
- `topics/<topic_slug>/runtime/loop_history.jsonl`
  - append-only history of loop runs
- `topics/<topic_slug>/runtime/unfinished_work.json`
  - machine-readable ordered unfinished-work index
- `topics/<topic_slug>/runtime/unfinished_work.md`
  - human-readable unfinished-work note
- `topics/<topic_slug>/runtime/next_action_decision.json`
  - authoritative machine-readable next-action decision
- `topics/<topic_slug>/runtime/next_action_decision.md`
  - human-readable next-action decision note
- `topics/<topic_slug>/runtime/action_queue_contract.generated.json`
  - generated queue-contract snapshot showing the current executable queue in declarative form
- `topics/<topic_slug>/runtime/action_queue_contract.generated.md`
  - human-readable queue-contract snapshot
- `schemas/progressive-disclosure-runtime-bundle.schema.json`
  - public JSON contract for `runtime_protocol.generated.json`
- `topics/<topic_slug>/runtime/deferred_candidates.json`
  - machine-readable deferred parking and reactivation buffer
- `topics/<topic_slug>/runtime/deferred_candidates.md`
  - human-readable deferred parking note
- `topics/<topic_slug>/runtime/followup_subtopics.jsonl`
  - append-only parent/child lineage for cited-literature subtopics
- `topics/<topic_slug>/runtime/followup_subtopics.md`
  - human-readable follow-up subtopic index
- `topics/<topic_slug>/runtime/conformance_state.json`
  - machine-readable audit status for AITP runtime conformance
- `topics/<topic_slug>/runtime/conformance_report.md`
  - human-readable conformance report
- `topic_index.jsonl`
  - one-row registry for the latest known state of each topic
- `active_topics.json`
  - authoritative multi-topic registry for one workspace
- `active_topics.md`
  - human-readable registry summary with focus and dependency state
- `topic_family_reuse.json`
  - protocol-native workspace-level catalog of mature reusable route capsules grouped by family/lane
- `topic_family_reuse.md`
  - human-readable topic-family reuse catalog with family rules and anti-proxy boundaries
- `explorations/<exploration_id>/explore_session.json`
  - machine-readable lightweight exploration session that skips full topic bootstrap
- `explorations/<exploration_id>/explore_session.md`
  - human-readable quick-exploration session note
- `explorations/<exploration_id>/promotion_request.json`
  - machine-readable promotion request from quick exploration into full topic work
- `explorations/<exploration_id>/promotion_request.md`
  - human-readable promotion request note
- `collaborator_memory.jsonl`
  - append-only runtime-side collaborator memory ledger for preference, trajectory, and working-style memory
- `collaborator_memory.md`
  - human-readable collaborator-memory projection; not canonical scientific memory
- `current_topic.json`
  - focused-topic compatibility projection for current-topic flows
- `current_topic.md`
  - human-readable focused-topic compatibility note
- `scripts/sync_topic_state.py`
  - helper that materializes the runtime state from existing layer artifacts
- `topics/<topic_slug>/runtime/action_queue.jsonl`
  - typed next-action queue derived from the current topic state
- `topics/<topic_slug>/runtime/agent_brief.md`
  - legacy compatibility execution brief for older external-execution flows
- `topics/<topic_slug>/runtime/selected_validation_route.json`
  - one selected validation lane for the current closed-loop step
- `topics/<topic_slug>/runtime/execution_task.json`
  - concrete execution handoff artifact for the external runtime
- `topics/<topic_slug>/runtime/execution_task.md`
  - human-readable execution handoff note with return-path contract
- `topics/<topic_slug>/runtime/execution_handoff_receipts.jsonl`
  - receipts for auto-dispatched external execution tasks
- `topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session.json`
  - tmux-backed Codex session state for a live external execution handoff
- `topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session_receipts.jsonl`
  - start/wait/submit/kill receipts for the live Codex session
- `scripts/orchestrate_topic.py`
  - internal topic bootstrap + resume orchestrator used by the public loop surface
- `scripts/orchestrator_contract_support.py`
  - focused contract-aware queue shaping, checkpoint append gating, and runtime-appended action assembly support for `orchestrate_topic.py`
- `scripts/interaction_surface_support.py`
  - focused interaction-state assembly plus operator-console and agent-brief rendering support for `orchestrate_topic.py`
- `scripts/sync_topic_state_support.py`
  - focused resume-stage inference, evidence-return explainability, and resume-note rendering support for `sync_topic_state.py`

## Surface role map

Treat runtime surfaces by role, not by filename age.

| Role | Surfaces | Meaning |
|------|----------|---------|
| Primary runtime truth | `topic_synopsis.json`, `topic_dashboard.md` | The main machine/human answer pair for current-topic runtime status |
| Primary review truth | `validation_review_bundle.active.json`, `validation_review_bundle.active.md` | The main `L4` review entry pair before opening deeper review-support surfaces |
| Judgment truth | `research_judgment.active.json`, `research_judgment.active.md` | The bounded momentum / stuckness / surprise pair that keeps decision surfaces reviewable |
| Continuity truth | `collaborator_profile.active.json|md`, `research_trajectory.active.json|md`, `mode_learning.active.json|md` | Restart-facing collaborator continuity surfaces derived from durable runtime memory |
| Quick exploration | `runtime/explorations/<exploration_id>/explore_session.json|md`, `promotion_request.json|md` | Lightweight speculative session carrier and explicit promotion path into full topic work |
| Primary workspace registry | `active_topics.json`, `active_topics.md` | The authoritative multi-topic workspace state |
| Protocol-native reuse surface | `topic_family_reuse.json`, `topic_family_reuse.md` | Workspace-level catalog of mature reusable route capsules grouped by family/lane |
| Derived startup bundle | `runtime_protocol.generated.json`, `runtime_protocol.generated.md` | A startup/read-order bundle derived from the primary runtime truths |
| Compatibility projections | `current_topic.json`, `current_topic.md`, `operator_console.md`, `agent_brief.md` | Legacy or compatibility-oriented surfaces kept to avoid abrupt breakage |
| Supporting slices | `research_question.contract.md`, `validation_contract.active.md`, `promotion_readiness.md`, `gap_map.md`, `topic_completion.md` | Deeper bounded slices that explain one part of the current route |

The practical rule is:

- start from the primary runtime truth
- open the derived startup bundle only to get ordered read guidance
- open compatibility surfaces only when a specific legacy or adapter flow still needs them
- open supporting slices only when the current trigger makes that slice relevant

Migration notes for the demoted surfaces live at:

- `../../docs/MIGRATE_RUNTIME_SURFACES.md`

## Rules

- `runtime/` does not replace layer-local source-of-truth files.
- `runtime/` only summarizes and points to those files.
- `topic_synopsis.json` is the primary machine synopsis for operator-facing runtime concerns.
- `topic_dashboard.md` is the primary human render for that synopsis.
- `runtime_protocol.generated.{json,md}` is a derived startup bundle, not a peer source of truth.
- `validation_review_bundle.active.{json,md}` is the primary `L4` review entry surface; specialist review files remain supporting artifacts.
- `research_judgment.active.json|md` is a derived runtime judgment surface built from durable runtime, strategy-memory, and collaborator-memory artifacts; it is reviewable guidance, not scientific truth.
- `collaborator_profile.active.json|md`, `research_trajectory.active.json|md`, and `mode_learning.active.json|md` are derived continuity surfaces for restart guidance; they are not canonical scientific memory and they do not bypass trust gates.
- `runtime/explorations/<exploration_id>/explore_session.json|md` is a lightweight speculative carrier, not a full topic shell.
- `promotion_request.json|md` under that exploration root is the explicit boundary where quick exploration promotes into normal topic work.
- `current_topic.{json,md}` is a compatibility projection, not the authoritative workspace registry.
- `topic_family_reuse.{json,md}` is the protocol-native reuse surface; it summarizes mature route capsules but does not itself bypass trust gates or current-topic choice.
- `collaborator_memory.jsonl|md` is runtime-side collaborator memory, not canonical scientific memory, not `L2`, and not a promotion surface.
- `operator_console.md` and `agent_brief.md` are compatibility surfaces, not the primary runtime read path.
- `promotion_readiness.md` and `gap_map.md` are supporting slices, not peer summaries competing with `topic_dashboard.md`.
- Every active topic should refresh its runtime state after a meaningful `L1`, `L3`, or `L4` update.
- The resume target should prefer the fallback route implied by the latest decision artifact when one exists.
- Runtime should expose the human-visible operator contract rather than forcing the next agent or human to reconstruct it manually.
- Runtime should expose why the topic is at its current stage, what the last durable evidence return was, and whether an active human checkpoint is blocking the next step.
- Runtime bundles should expose explicit `runtime_mode`, `mode_envelope`, and
  `transition_posture` so mode and backedge policy do not remain hidden inside
  Python heuristics.
- Runtime should keep multi-topic state explicit: the active-topic registry is
  authoritative, while `current_topic.json` is the focused-topic compatibility
  projection.
- If two runtime files answer the same operator question, `topic_synopsis.json`
  should usually own the machine summary while the other file becomes a render
  or a deeper slice.
- Projection-aware routing may consult mature `topic_skill_projection` metadata,
  but only through explicit, inspectable hooks; explicit topic choice and
  durable current-topic focus still outrank projection hints.
- Runtime should make scheduler and dependency state inspectable rather than
  hiding topic selection behind latest-topic heuristics.
- Runtime may materialize a topic-skill projection when the lane is mature enough to reuse, but that projection is not the same thing as the raw live topic state.
- For `formal_theory`, a topic-skill projection only counts as mature enough to
  reuse when theorem-facing trust artifacts are ready; even then it is reusable
  execution memory, not a theorem certificate.
- Runtime should expose the minimum sufficient execution contract first, then defer deeper protocol slices until declared triggers fire.
- Runtime should expose the global research-flow guardrails early enough that
  scope, deliverables, acceptance tests, and forbidden proxies stay visible.
- Runtime should materialize both an unfinished-work index and a next-action decision so the loop is inspectable rather than implicit.
- Runtime should prefer declared contracts when they exist and only fall back to heuristics when they do not.
- Active operator checkpoints or declared `append_runtime_actions=false`
  should block runtime-appended system queue materialization, while explicit
  capability-gap skill append remains separately governed.
- `operator_checkpoint.active.json` is itself an explicit append gate and must
  suppress runtime-appended queue expansion even before a refreshed runtime
  bundle reprojects that checkpoint into `transition_posture`.
- Runtime should also expose a conformance report so non-AITP operation becomes visible rather than implicit.
- Runtime may materialize one thin closed-loop control step, but it must never claim that heavy execution already happened unless a returned execution result artifact is present.
- Runtime should auto-promote theory-formal candidates only after explicit coverage, consensus, and formal-theory review artifacts exist.
- Runtime should also require a ready `formal_theory_review.json`, a regression gate, blocker clearance, and split honesty before theory-formal auto-promotion.
- Runtime should keep `SEMI_FORMAL_THEORY_PROTOCOL.md` visible so theory work is not misread as "Lean-first or it does not count".
- Runtime should keep `FORMAL_THEORY_AUTOMATION_WORKFLOW.md` visible when operators need to know which lane is currently automated and which lane still requires bounded manual judgment.
- Runtime should keep `SECTION_FORMALIZATION_PROTOCOL.md` visible when section-oriented formalization is active so one compiled section is not mistaken for whole-topic closure.
- Runtime should keep wide or mixed candidates out of Layer 2 by splitting or parking them first.
- Runtime may spawn independent follow-up subtopics when cited-literature gaps are explicit enough to deserve a fresh `L0 -> L1 -> L3 -> L4 -> L2` route.
- Runtime should materialize a follow-up return packet for those child subtopics so reintegration is explicit rather than conversational.
- Runtime should detect when a child return packet is no longer `pending_reentry` and queue parent-side reintegration automatically.
- Runtime should also queue topic-completion refreshes and Lean-bridge refreshes when the latest run has outgrown the currently materialized shell surfaces.
- Runtime should expose proof-completion review, gap recovery, family fusion, and verification-bridge triggers as explicit deeper reads when those situations arise.
- Runtime should expose the current semi-formal trust boundary and downstream translation status when theory-formal artifacts are being reviewed.
- Runtime should keep `FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md` visible when formal-theory or Lean-bridge work is active, and topic-local artifacts should record the consulted upstream thread URLs, archive URLs, commits, and file paths explicitly.

## Minimal required pointers

Each `topic_state.json` should point to:

- intake status,
- latest feedback run status,
- latest validation decision,
- next-actions file when present,
- consultation index,
- active control-plane note when present,
- current `innovation_direction.md` when the human has redirected novelty or scope,
- the `innovation_decisions.jsonl` ledger when steering updates have occurred.

Each `topic_state.json` should also remain a machine-readable status answer surface.
In particular, `status_explainability` should summarize:

- why the topic is in its current state,
- the current route choice and bounded next action,
- the last durable evidence return,
- the active human need, if any,
- the current blocker summary.

## Resume semantics

The important distinction is:

- `last_materialized_stage`
  - the latest stage that emitted durable artifacts
- `resume_stage`
  - the stage where the next real work should continue

These are often different.
For example, an `L4` run may end with a `deferred` verdict that sends work back to `L3`.

## Current workflow

1. run `python3 research/adapters/openclaw/scripts/aitp_loop.py --topic-slug <topic_slug> --max-steps 1`
2. open `topics/<topic_slug>/runtime/runtime_protocol.generated.md`
3. read the primary surfaces it points to first, especially `topic_dashboard.md` and `research_question.contract.md` in the light profile; only open `topic_synopsis.json`, control notes, or review surfaces when their declared trigger fires
4. only escalate into deferred or supporting surfaces when a declared trigger fires
5. follow `resume_stage`, `unfinished_work`, and the selected next-action decision
6. after new work lands, advance the loop again instead of hand-maintaining runtime state

When you want to reduce heuristic behavior further, use:

- `topics/<topic_slug>/L3/.../next_actions.contract.json` for an explicit L3 action queue
- `topics/<topic_slug>/runtime/.../next_action_decision.contract.json` for an explicit next-action choice
- `aitp steer-topic --topic-slug <topic_slug> --innovation-direction "<direction>" --decision continue`
  when the operator changes novelty direction or scope and that redirect must be durable before the loop continues

For explicit multi-topic control, use:

```bash
aitp topics
aitp focus-topic --topic-slug <topic_slug>
aitp pause-topic --topic-slug <topic_slug>
aitp resume-topic --topic-slug <topic_slug>
aitp block-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug> --reason "<reason>"
aitp unblock-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug>
aitp clear-topic-dependencies --topic-slug <topic_slug>
```

For internal runtime work, the lower-level orchestrator still exists:

```bash
python3 runtime/scripts/orchestrate_topic.py \
  --topic-slug <topic_slug>
```

For a bounded real-topic acceptance pass that exercises the reviewed controller
bridge on the Witten topological-phases exemplar, run:

```bash
python research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py --json
```

That acceptance script keeps the topic real but the scope bounded: it builds a
Witten Lecture Two theorem candidate, persists coverage and formal-theory
review artifacts, dispatches `assess_topic_completion` and
`prepare_lean_bridge` through the public runtime-controller bridge, and finally
verifies `L2_auto` writeback into a disposable standalone TPKN clone.
The acceptance target is a self-consistent semi-formal theory packet with an
explicit Lean bridge, not a claim that the whole topic has already been fully
formalized in Lean.

For a bounded real-topic acceptance pass that exercises the same controller
bridge on the Jones Chapter 4 finite-dimensional benchmark, run:

```bash
python research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py --json
```

That acceptance script stays on the existing `jones-von-neumann-algebras`
topic, writes a new Chapter 4 finite-product candidate around the current
compile-checked theorem packet, persists coverage and formal-theory review
artifacts, records theorem-facing strategy memory, compiles a
`topic_skill_projection`, human-promotes that projection into
`units/topic-skill-projections/`, dispatches `assess_topic_completion`,
`prepare_lean_bridge`, and `auto_promote_candidate` through the public
runtime-controller bridge, and checks that the resulting `L2_auto` theorem
writeback and `L2` execution projection both keep the stronger algebra-level
product theorem and later whole-book routes explicitly open.

For a bounded code-backed acceptance pass that keeps benchmark-first discipline
inside AITP, run:

```bash
python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json
```

That acceptance script runs the tiny public TFIM exact-diagonalization helper,
opens a `code_method` topic around the resulting benchmark note, records a
baseline-gated coding operation plus strategy memory, and verifies that
operation trust stays visible in AITP runtime surfaces before any broader
workflow claim is allowed.

The analogous future formal-theory seed should follow the same rule: a runtime
projection may tell the next agent what to read and how to enter the route, but
it must not be mistaken for proof closure or theorem certification.

For an isolated bounded `L2` MVP direction acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py --json
```

That acceptance script uses a temporary kernel root, seeds the TFIM MVP
direction through production CLI, retrieves the seeded `physical_picture`,
compiles `workspace_memory_map.json|md`, compiles
`workspace_graph_report.json|md` plus `derived_navigation/index.md`, compiles
`workspace_knowledge_report.json|md`, audits `workspace_hygiene_report.json|md`,
and verifies those artifacts without touching repo runtime state.

For an isolated compiled-knowledge acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l2_knowledge_report_acceptance.py --json
```

That acceptance script seeds bounded canonical plus staging knowledge, runs the
new `compile-l2-knowledge-report` surface twice, and verifies that the compiled
report stays explicitly non-authoritative while still surfacing change summary
and contradiction-watch rows.

For an isolated bounded Layer 0 source-catalog acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_source_catalog_acceptance.py --json
```

That acceptance script uses a temporary kernel root, compiles
`source_catalog.json|md`, traces one bounded citation neighborhood, compiles
one source-family reuse report, exports one bounded BibTeX neighborhood,
imports one bounded BibTeX file back into Layer 0, checks runtime
source-fidelity status output, and verifies those artifacts without touching
repo runtime state.

For an isolated bounded Layer 0 discovery -> registration acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l0_source_discovery_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_enrichment_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_concept_graph_acceptance.py --json
```

That acceptance script uses a temporary kernel root, feeds one bounded
`search_results_json` fixture through
`source-layer/scripts/discover_and_register.py`, verifies that
`candidate_evaluation.json` keeps the winning source explicit, and confirms
that the selected paper is still registered through the normal Layer 0
`source.json` plus Layer 1 projection path, now with integrated enrichment and
concept-graph artifacts.

For an isolated bounded L1 method-specificity acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json`, verifies that `method_specificity_rows` are materialized
inside `l1_source_intake`, and checks that the same surface is visible in
`research_question.contract.md` and the runtime protocol note.

For an isolated bounded L1 assumption and reading-depth acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l1_concept_graph_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json`, verifies that `assumption_rows`, `reading_depth_rows`, and
contradiction signals stay visible through the existing `l1_source_intake`
path, and checks that the same honesty surface is visible in
`research_question.contract.md`, `topic_dashboard.md`, the runtime protocol
note, and the `L1` vault wiki source-intake page.

For an isolated bounded L1 concept-graph acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l1_concept_graph_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json`, verifies that `l1_source_intake.concept_graph` is materialized
from source-local graph artifacts, and checks that the same graph surface is
visible in `research_question.contract.md`, the runtime protocol note, and the
`L1` vault wiki source-intake page.

For an isolated bounded runtime transition and demotion-history acceptance
pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_transition_history_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`request-promotion`, production `reject-promotion`, then production
`status --json` and `replay-topic --json`, verifying that the topic now keeps
durable `transition_history.jsonl|json|md` artifacts and that replay surfaces
the latest demotion reason instead of only the current stage snapshot.

For an isolated bounded human-modification record acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_human_modification_record_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`request-promotion`, then production `approve-promotion --human-modification`,
verifying that `promotion_gate.json|md` records the structured modification
rows and that `replay-topic --json` surfaces the modified approval as a
distinct evaluator-divergence signal.

For an isolated bounded competing-hypotheses acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`research_question.contract.md` and the runtime protocol note both surface the
explicit `competing_hypotheses` rows, and checks that deferred candidates plus
follow-up subtopics remain visible as separate runtime lanes.

For an isolated bounded hypothesis-branch-routing acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_branch_routing_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that each competing
hypothesis now carries explicit branch-routing metadata, and checks that one
hypothesis can stay on the current topic while other routes remain visible
through deferred parking, follow-up subtopics, and steering artifacts.

For an isolated bounded hypothesis-route-activation acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_activation_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that `route_activation`
surfaces the active local hypothesis plus its immediate bounded action, checks
that deferred and follow-up obligations stay explicit, and confirms the bounded
slice does not auto-spawn a follow-up topic directory.

For an isolated bounded hypothesis-route-reentry acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_reentry_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that `route_reentry`
surfaces deferred reactivation conditions plus follow-up return readiness,
checks that one parked route can remain waiting while another becomes
re-entry-ready, and confirms the bounded slice does not write a reintegration
receipt or materialize a reactivated deferred candidate.

For an isolated bounded hypothesis-route-handoff acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_handoff_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that `route_handoff`
surfaces one bounded parked-route handoff candidate plus explicit keep-parked
decisions, checks that one ready parked route can occupy the handoff lane while
another ready parked route remains parked, and confirms the bounded slice does
not write a reintegration receipt or materialize a reactivated deferred
candidate.

For an isolated bounded hypothesis-route-choice acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_choice_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that `route_choice`
surfaces one stay-local versus yield-to-handoff summary, checks that the local
route can stay active while the handoff candidate remains visible as the yield
option, and confirms the bounded slice does not write a reintegration receipt
or materialize a reactivated deferred candidate.

For an isolated bounded hypothesis-route-transition-gate acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_gate_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_gate` surfaces blocked, available, and
checkpoint-required yielding directly, checks that the gate points at the
durable route-choice or operator-checkpoint artifact, and confirms the bounded
slice does not auto-reactivate or auto-reintegrate parked routes.

For an isolated bounded hypothesis-route-transition-intent acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_intent_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_intent` surfaces the declarative source route and target
route after the transition gate, checks that proposed, ready, and
checkpoint-held intent states remain explicit, and confirms the bounded slice
does not auto-reactivate or auto-reintegrate parked routes.

For an isolated bounded hypothesis-route-transition-receipt acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_receipt_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_receipt` surfaces whether the intended handoff has been
durably recorded, checks that pending, recorded, and none states remain
explicit, and confirms the bounded slice does not widen into fresh runtime
mutation.

For an isolated bounded hypothesis-route-transition-resolution acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_resolution_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_resolution` synthesizes transition intent, transition
receipt, and current active-route alignment into one resolved operator outcome,
checks that pending, resolved, and none states remain explicit, and confirms
the bounded slice does not widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-discrepancy acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_discrepancy_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_discrepancy` flags inconsistent transition state when the
resolved outcome disagrees with upstream route artifacts, checks that present
versus none discrepancy states remain explicit, and confirms the bounded slice
does not widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-repair acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_repair_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_repair` surfaces a bounded repair plan when discrepancy is
present, checks that `recommended` versus `none_required` states remain
explicit, and confirms the bounded slice does not widen into fresh runtime
mutation.

For an isolated bounded hypothesis-route-transition-escalation acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_escalation_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_escalation` surfaces `none`, `checkpoint_recommended`, and
`checkpoint_active` states directly, and confirms the bounded slice does not
widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-clearance acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_clearance_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_clearance` surfaces `none`, `awaiting_checkpoint`,
`blocked_on_checkpoint`, and `cleared` states directly, and confirms the
bounded slice does not widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-followthrough acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_followthrough_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_followthrough` surfaces `none`, `held_by_clearance`, and
`ready` states directly, and confirms the bounded slice does not widen into
fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-resumption acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_resumption_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_resumption` surfaces `none`, `waiting_followthrough`,
`pending`, and `resumed` states directly, and confirms the bounded slice does
not widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-commitment acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_commitment_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_commitment` surfaces `none`, `waiting_resumption`,
`pending_commitment`, and `committed` states directly, and confirms the bounded
slice does not widen into fresh runtime mutation.

For an isolated bounded hypothesis-route-transition-authority acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_authority_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json` and `replay-topic --json`, verifies that
`route_transition_authority` surfaces `none`, `waiting_commitment`,
`pending_authority`, and `authoritative` states directly, and confirms the
bounded slice does not widen into fresh runtime mutation.

For an isolated bounded L1 raw/wiki/output vault acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_l1_vault_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`status --json`, verifies that `topics/<topic_slug>/L1/vault/raw|wiki|output`
is materialized on the topic-shell path, checks that the wiki layer stays
Obsidian-compatible, and checks that `output/flowback.jsonl` plus the runtime
bridge are visible through `research_question.contract.md` and the runtime
protocol note.

For an isolated bounded statement-compilation acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_statement_compilation_acceptance.py --json
```

That acceptance script uses a temporary kernel root, seeds one theorem-facing
candidate plus bounded theory-packet inputs, runs production
`statement-compilation --json`, and then production `lean-bridge --json`.
The pass condition is that declaration skeletons, proof-repair plans,
proof-assistant-agnostic downstream targets, and the downstream Lean-bridge
refs all remain explicit instead of being collapsed into one opaque packet.

For an isolated bounded analytical-review plus research-judgment acceptance
pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`analytical-review`, production `verify --mode analytical`, then production
`status --json`, and verifies that `analytical_review` becomes the primary
review bundle while `research_judgment.active.json|md` and runtime momentum /
stuckness / surprise signals are visible.

For an isolated bounded collaborator-continuity acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_collaborator_continuity_acceptance.py --json
```

That acceptance script uses a temporary kernel root, seeds runtime-side
collaborator memory plus strategy memory, then runs production `focus-topic`,
production `status --json`, production `current-topic --json`, and production
`session-start --json`, verifying that `collaborator_profile.active.json|md`,
`research_trajectory.active.json|md`, and `mode_learning.active.json|md` are
all visible through the real continuity surfaces.

For an isolated bounded first-run topic acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json
```

For the next bounded fresh-topic follow-through after first-source registration,
run:

```bash
python research/knowledge-hub/runtime/scripts/run_first_source_followthrough_acceptance.py --json
```

That acceptance script replays the same fresh bootstrap and first-source
registration lane, then executes exactly one bounded `literature_intake_stage`
auto step and proves that runtime status advances onto L2 staging review rather
than repeating the same L1->L2 action forever. It also checks that the
workspace staging manifest becomes the foreground read surface and that
`consult_l2(include_staging=True)` can retrieve the freshly staged topic-local
row.

That acceptance script uses a temporary kernel root, runs production
`bootstrap --json`, production `loop --json`, then production `status --json`,
and checks that the shared `bootstrap -> loop -> status` quickstart path keeps
the topic shell, loop state, and runtime protocol coherent.

For an isolated bounded public-install smoke pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json
```

That acceptance script builds a wheel from the current package root, installs it
into a clean virtualenv, points `AITP_HOME` at an isolated temp home, then runs
the installed package through `aitp --version`, `aitp doctor --json`, and an
isolated `bootstrap -> loop -> status` quickstart path from the wheel-backed
runtime itself. The goal is to prove that the published `aitp-kernel`
distribution works outside a repo checkout instead of only inside editable-
install development flows.

For the shared deep-execution parity harness, run:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime codex --json
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime claude_code --json
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime opencode --json
```

That harness defines the artifact-level bar for `v1.67` runtime parity work.
At this stage it proves the Codex baseline path and now includes the bounded
Claude Code and OpenCode probes. Those reports are intentionally gap-aware:
they verify the runtime-specific bootstrap receipt plus downstream AITP
artifacts, but they do not yet overclaim full live-app parity. The important
boundary is that front-door install readiness and deep-execution parity are
different surfaces: a green `doctor` row is not, by itself, proof that a
runtime matches the Codex execution baseline.

For the shared closure audit across all three runtimes, run:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_audit.py --json
```

That audit reuses the Codex, Claude Code, and OpenCode bounded probes and emits
one closure report naming equivalent surfaces, degraded surfaces, and still-open
gaps.

When you have real Claude Code and/or OpenCode first-turn evidence from a live
front door, place JSON files named
`claude_code.live-first-turn.json` and/or
`opencode.live-first-turn.json` in one directory and rerun:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_audit.py --live-evidence-root <evidence_dir> --json
```

Those files must validate against
`runtime/schemas/runtime-live-first-turn-evidence.schema.json`. The audit only
closes the remaining live-app gap when the evidence marks the bootstrap and
human-control posture checks as explicitly verified.

For an isolated bounded quick-exploration acceptance pass, run:

```bash
python research/knowledge-hub/runtime/scripts/run_quick_exploration_acceptance.py --json
```

That acceptance script uses a temporary kernel root, runs production
`explore --json`, verifies the lightweight artifact-footprint surface, then
runs production `promote-exploration --current-topic --json` and checks that
promotion writes a durable request artifact plus a bounded `session-start`
contract for the current topic.

For the minimal closed-loop v1, the external executor returns one JSON artifact at:

- `topics/<topic_slug>/L4/runs/<run_id>/returned_execution_result.json`
- `topics/<topic_slug>/L4/runs/<run_id>/execution_notes/`
- `topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session.json`
- `topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session_receipts.jsonl`
- `topics/<topic_slug>/L4/runs/<run_id>/literature_followup_receipts.jsonl`

The current OpenClaw adapter launches `codex exec` through a tmux-backed session controller so the
execution lane stays operator-visible even while the runtime waits for the returned result artifact.
External runtimes that do not use the markdown brief should still consume
`runtime_protocol.generated.json` through
`runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`.
Use:

```bash
python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  status --metadata-path topics/<topic_slug>/L4/runs/<run_id>/execution_notes/codex_session.json
```

to inspect that live session, and swap `status` for `log`, `submit`, or `kill` when intervention is needed.

If the external executor leaves durable artifacts but misses the required return JSON, the OpenClaw handoff adapter may recover a truthful `partial` result so the runtime can ingest evidence instead of stalling. That recovery path must remain explicitly non-promotional and limitation-heavy.

The result contract template lives at:

- `validation/templates/execution-result.template.json`

Bounded literature follow-up search can be auto-run from emitted query records:

- `runtime/scripts/run_literature_followup.py`

Those search receipts may then spawn independent follow-up subtopics and may
reactivate parked deferred fragments when the declared conditions are satisfied.
When follow-up subtopics are spawned, the child runtime root should also receive
a durable return packet naming the parent gaps, follow-up tasks, and
reintegration targets. That packet should also declare the expected return
route, acceptable return shapes, unresolved return statuses, and the explicit
rule that the child branch must reintegrate through writeback artifacts rather
than by silently patching the parent topic.

When a capability gap needs external skill discovery, add one or more queries:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py \
  --topic-slug <topic_slug> \
  --skill-query "formal theory source bridging" \
  --max-steps 1
```

Heartbeat should schedule the loop, not maintain a parallel state machine.
Prefer declaring this in the workspace heartbeat policy and running:

```bash
aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

or, when the topic is explicit:

```bash
aitp loop --topic-slug <topic_slug> --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Keep `HEARTBEAT_AITP.md` in the workspace root as the durable note that tells heartbeat when AITP should run.

For compatibility or explicit adapter-owned heartbeat receipts, you can still use:

```bash
python3 research/adapters/openclaw/scripts/heartbeat_bridge.py
```

which resolves the best unfinished topic and delegates to `aitp_loop.py --max-steps 1`.

## Constraint

The runtime surface is only useful if it remains thin and truthful.

Do not store large copied notes here.
Store summaries, stage decisions, and exact file pointers.

Use `runtime/CONTROL_NOTE_CONTRACT.md` when a human wants to redirect or pause
the loop through a durable steering note.

Use `topics/<topic_slug>/runtime/innovation_direction.md` plus
`innovation_decisions.jsonl` when the operator changes novelty direction,
research scope, or acceptance posture and that change must survive a new
session.

Use `RESEARCH_EXECUTION_GUARDRAILS.md` when the selected action starts to drift
scope, mutate deliverables, or confuse proxy-success with real validation.

Use `runtime/DECLARATIVE_RUNTIME_CONTRACTS.md` when you want queue/decision
selection to be authored explicitly instead of inferred.

Use `runtime/DEFERRED_RUNTIME_CONTRACTS.md` when a parked fragment needs a
durable reactivation contract rather than a prose-only TODO.

Use the top-level contracts below when the runtime trigger set says the topic is
now proof-heavy, gap-heavy, fusion-heavy, or verification-heavy:

- `PROOF_OBLIGATION_PROTOCOL.md`
- `GAP_RECOVERY_PROTOCOL.md`
- `FAMILY_FUSION_PROTOCOL.md`
- `VERIFICATION_BRIDGE_PROTOCOL.md`
- `FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md`
