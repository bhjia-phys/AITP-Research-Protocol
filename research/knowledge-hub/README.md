# AITP Kernel

This folder contains the installable public AITP kernel.

It should be understood as the current **public reference implementation** of
the AITP research protocol, not as the only possible implementation of that
protocol.

It is the repo-local source-of-truth behind:

- `aitp`
- `aitp-mcp`
- the repository `skills/` bootstrap surfaces
- the fixed `L0-L4` protocol surfaces shipped in this repository

The repository remains protocol-first, but a fresh clone is now both readable
and runnable.
The fixed directories are public governance surfaces.
The scientific content inside them is expected to remain user-extensible so one
clone can emphasize formal theory while another emphasizes toy-model numerics or
code-backed method development.

Short form:

- protocol docs and contracts define the durable AITP model
- this kernel is the current runnable implementation of that model
- Codex / OpenCode / Claude Code / OpenClaw are front doors over this kernel,
  not separate research protocols

## Quick Start

For the public package path:

```bash
python -m pip install aitp-kernel
aitp --version
aitp doctor
aitp --help
```

Maintainers can verify that a published-style wheel really installs and runs in
an isolated environment with:

```bash
python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json
```

Contributor / local-dev lane from the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

For a Windows-native smoke test from a fresh clone, the repo-local launchers do
not require WSL or a copied global `aitp` shim:

```cmd
scripts\aitp-local.cmd doctor
```

The public runtime now has two honest defaults:

- repo checkout: `research/knowledge-hub`
- installed package: `~/.aitp/kernel`

So a normal standalone clone does not need the original private integration
workspace just to run `aitp`, and a public `pip install aitp-kernel` does not
need a git checkout to materialize the static kernel bundle.
On Windows, the local launchers inject `research\knowledge-hub` onto
`PYTHONPATH`, so the repo can run natively even before you choose a permanent
Python install layout.
The runtime requirements now use bounded version ranges in `requirements.txt`
instead of fully open-ended dependency specifiers.

`aitp doctor` should also report the fixed layer roots and key contract files so
you can verify that the standalone install is structurally complete.
That protocol report now includes the deeper proof/gap/fusion/verification
governance surfaces in addition to the layer map and routing basics.
Topic-completion and regression-governed promotion are part of that public
surface rather than topic-local convention.
Its human-readable form now summarizes the Codex/Claude Code/OpenCode front
door first, and its JSON form now exposes `runtime_convergence`,
`full_convergence_repair`, and per-runtime `remediation` contracts.
`aitp doctor --json` now also exposes `control_plane_contracts` and
`control_plane_surfaces` so operators can find the unified architecture docs
and the audit/status commands that inspect live control-plane state.

## Kernel Boundaries

Recent maintainability work has started turning the kernel back into a thin
façade plus focused helper modules instead of one giant service file.

Current extracted boundaries include:

- `knowledge_hub/frontdoor_support.py`
  - doctor, migration, and runtime/front-door readiness support
- `knowledge_hub/agent_install_support.py`
  - agent install, bootstrap, plugin, and MCP setup support
- `knowledge_hub/kernel_templates.py`
  - install/bootstrap skill templates and session-start note rendering
- `knowledge_hub/kernel_markdown_renderers.py`
  - pure markdown and note renderers for contracts, promotion/gap notes, Lean packets, and control/current-topic surfaces
- `knowledge_hub/runtime_bundle_support.py`
  - progressive-disclosure runtime bundle and session-start contract materialization
- `knowledge_hub/control_plane_support.py`
  - unified control-plane payload assembly plus markdown and audit helpers
- `knowledge_hub/paired_backend_support.py`
  - paired-backend alignment, drift-audit, and backend-bridge enrichment helpers
- `knowledge_hub/h_plane_support.py`
  - explicit `H-plane` payload assembly plus audit artifact writers
- `knowledge_hub/topic_shell_support.py`
  - topic-shell assembly, shell-surface derivation, and dashboard materialization
- `knowledge_hub/source_distillation_support.py`
  - source-backed idea distillation, preview fallback recovery, novelty extraction, and lane/first-route inference
- `knowledge_hub/topic_loop_support.py`
  - topic-loop bootstrap, auto-step iteration, loop-state persistence, and runtime-bundle closure
- `knowledge_hub/chat_session_support.py`
  - Codex chat routing, projection/current-topic fallback, management-route handling, and session-start orchestration
- `knowledge_hub/capability_audit_support.py`
  - runtime/layer/integration capability audit assembly, recommendation synthesis, and capability report persistence
- `knowledge_hub/followup_support.py`
  - follow-up subtopic orchestration, deferred-buffer management, and reintegration/writeback flows
- `knowledge_hub/auto_promotion_support.py`
  - auto-promotion approval gating, report assembly, and handoff into the main promotion path
- `knowledge_hub/formal_theory_audit_support.py`
  - formal-theory audit normalization, blocker evaluation, review artifact writing, and candidate ledger updates
- `knowledge_hub/candidate_promotion_support.py`
  - candidate promotion preparation, TPKN writeback materialization, consultation logging, and promotion-state finalization
- `knowledge_hub/lean_bridge_support.py`
  - Lean-bridge packet construction, proof-obligation materialization, and active index synthesis
- `knowledge_hub/statement_compilation_support.py`
  - statement-compilation packet construction plus proof-repair-plan and active-index synthesis
- `knowledge_hub/theory_coverage_audit_support.py`
  - theory-coverage normalization, packet artifact construction, regression-gate assembly, and candidate ledger updates
- `knowledge_hub/topic_skill_projection_support.py`
  - topic-skill projection context derivation, route/read guidance assembly, and lane-specific availability gating
- `knowledge_hub/promotion_gate_support.py`
  - shared promotion-gate markdown, persistence, logging, and human approval lifecycle support
- `knowledge_hub/cli_frontdoor_handler.py`
  - the front-door CLI command family:
    `session-start`, `install-agent`, `migrate-local-install`, and `doctor`
- `hooks/session-start.py`
  - Python SessionStart sidecar used by the Windows-native Claude Code hook path before any bash fallback
- `runtime/scripts/orchestrator_contract_support.py`
  - contract-aware queue shaping, checkpoint append gating, and runtime-appended action assembly support for `orchestrate_topic.py`
- `runtime/scripts/interaction_surface_support.py`
  - interaction-state assembly plus operator-console and agent-brief rendering support for `orchestrate_topic.py`
- `runtime/scripts/sync_topic_state_support.py`
  - resume-stage inference, evidence-return explainability, and resume-note rendering support for `sync_topic_state.py`

`knowledge_hub/aitp_service.py` and `knowledge_hub/aitp_cli.py` still act as
public entry façades, but new work should prefer extracted modules over adding
more unrelated behavior back into those hotspot files.

## Core Commands

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
aitp session-start "<task>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp current-topic
aitp collaborator-memory --topic-slug <topic_slug>
aitp record-collaborator-memory --memory-kind preference --summary "<summary>"
aitp replay-topic --topic-slug <topic_slug>
aitp stage-l2-provisional --topic-slug <topic_slug> --entry-kind <kind> --title "<title>" --summary "<summary>"
aitp seed-l2-direction --direction tfim-benchmark-first
aitp consult-l2 --query-text "TFIM exact diagonalization benchmark workflow" --retrieval-profile l3_candidate_formation
aitp compile-l2-map
aitp compile-l2-graph-report
aitp compile-l2-knowledge-report
aitp audit-l2-hygiene
aitp compile-source-catalog
aitp trace-source-citations --canonical-source-id source_identity:doi:10-1000-shared-paper
aitp compile-source-family --source-type paper
aitp statement-compilation --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp export-source-bibtex --canonical-source-id source_identity:doi:10-1000-shared-paper --include-neighbors
aitp import-bibtex-sources --topic-slug <topic_slug> --bibtex-path <path-to-bib-file>
aitp topics
aitp focus-topic --topic-slug <topic_slug>
aitp pause-topic --topic-slug <topic_slug>
aitp resume-topic --topic-slug <topic_slug>
aitp block-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug> --reason "<reason>"
aitp unblock-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug>
aitp clear-topic-dependencies --topic-slug <topic_slug>
aitp audit --topic-slug <topic_slug> --phase exit
aitp ci-check --topic-slug <topic_slug>
aitp baseline --topic-slug <topic_slug> --run-id <run_id> --title "<baseline title>" --reference "<source>" --agreement-criterion "<criterion>"
aitp atomize --topic-slug <topic_slug> --run-id <run_id> --method-title "<method title>"
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical

For one isolated proof of the compiled-knowledge surface itself, run:

```bash
python runtime/scripts/run_l2_knowledge_report_acceptance.py --json
```
aitp operation-update --topic-slug <topic_slug> --run-id <run_id> --operation "<operation>" --baseline-status passed
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp capability-audit --topic-slug <topic_slug>
aitp paired-backend-audit --topic-slug <topic_slug>
aitp h-plane-audit --topic-slug <topic_slug>
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp formal-theory-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --formal-theory-role trusted_target --statement-graph-role target_statement
aitp analytical-review --topic-slug <topic_slug> --candidate-id <candidate_id> --check limiting_case=weak-coupling:passed:Matches-the-known-limit
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp install-agent --agent all --scope user
```

`aitp session-start "<task>"` still writes a durable startup contract under
`runtime/topics/<topic_slug>/session_start.contract.json` plus the human-readable
`session_start.generated.md`, but outer agent UX should treat that as internal
routing state. The first user-facing runtime checklist remains
`runtime_protocol.generated.md`.

## Fixed Layout

```text
research/knowledge-hub/
  LAYER_MAP.md
  ROUTING_POLICY.md
  COMMUNICATION_CONTRACT.md
  AUTONOMY_AND_OPERATOR_MODEL.md
  MODE_AND_LAYER_OPERATING_MODEL.md
  L2_CONSULTATION_PROTOCOL.md
  RESEARCH_EXECUTION_GUARDRAILS.md
  PROOF_OBLIGATION_PROTOCOL.md
  GAP_RECOVERY_PROTOCOL.md
  FAMILY_FUSION_PROTOCOL.md
  VERIFICATION_BRIDGE_PROTOCOL.md
  L5_PUBLICATION_FACTORY_PROTOCOL.md
  SEMI_FORMAL_THEORY_PROTOCOL.md
  FORMAL_THEORY_AUTOMATION_WORKFLOW.md
  SECTION_FORMALIZATION_PROTOCOL.md
  FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md
  TOPIC_COMPLETION_PROTOCOL.md
  TOPIC_REPLAY_PROTOCOL.md
  INDEXING_RULES.md
  L0_SOURCE_LAYER.md
  canonical/L2_STAGING_PROTOCOL.md
  setup.py
  requirements.txt
  schemas/
  knowledge_hub/
  source-layer/
  intake/
  canonical/
  feedback/
  consultation/
  runtime/
  validation/
  tests/
```

Formal roots:

- `L0` -> `source-layer/`
- `L1` -> `intake/`
- `L2` -> `canonical/`
- `L3` -> `feedback/`
- `L4` -> `validation/`

Public layer semantics:

- `L0`: source entry, survey, and acquisition
- `L1`: analysis and provisional understanding
- `L2`: long-term reusable knowledge and execution projections
- `L3`: exploratory conclusions and candidate reusable material
- `L4`: planning, execution, validation, and adjudication

The current filesystem keeps the `validation/` directory name for continuity,
but the public `L4` role is broader than a narrow pass/fail checker.

Cross-layer protocol surfaces:

- `consultation/`
- `runtime/`
- `schemas/`

Runtime-facing control notes:

- `runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`

Deeper governance contracts surfaced through `aitp doctor`:

- `RESEARCH_EXECUTION_GUARDRAILS.md`
- `PROOF_OBLIGATION_PROTOCOL.md`
- `GAP_RECOVERY_PROTOCOL.md`
- `FAMILY_FUSION_PROTOCOL.md`
- `VERIFICATION_BRIDGE_PROTOCOL.md`
- `L5_PUBLICATION_FACTORY_PROTOCOL.md`
- `SEMI_FORMAL_THEORY_PROTOCOL.md`
- `FORMAL_THEORY_AUTOMATION_WORKFLOW.md`
- `SECTION_FORMALIZATION_PROTOCOL.md`
- `FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md`
- `TOPIC_COMPLETION_PROTOCOL.md`

## Runtime Rule

AITP should not hide research control logic inside Python when a durable
contract file is sufficient.

AITP does not require one fixed Python implementation or one fixed agent
workflow. Scripts, handlers, prompts, and execution strategy may evolve, but
the contract surface must stay stable: layer semantics, runtime artifacts,
candidate and review objects, evidence traces, and backend writeback rules.

- Python remains responsible for state materialization, audits, and explicit handler execution.
- Agents may adapt execution strategy freely inside that boundary as long as the resulting artifacts remain protocol-compatible and auditable.
- Research routing, layer delivery, and queue overrides should prefer durable protocol artifacts.
- Each bootstrap or loop materializes:
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.json`
  - `runtime/topics/<topic_slug>/runtime_protocol.generated.md`
  - optional `runtime/topics/<topic_slug>/promotion_gate.json`
  - optional `runtime/topics/<topic_slug>/promotion_gate.md`
  - schema contract: `runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`

Agents should read that runtime bundle before acting on heuristic queue rows.
That runtime bundle should follow the lossless progressive-disclosure rule in
`runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md`: show the minimum sufficient
execution contract first, defer deeper details until declared triggers fire,
and never hide hard constraints.
It should also surface the global research-flow guardrails that ban proxy
success signals and require explicit research contracts for non-trivial work.
External runtimes should consume its trigger semantics from the JSON bundle and
its schema contract rather than scraping markdown prose.

The layer contracts above remain the higher-priority governance surface.
External backends such as a separate formal-theory knowledge network, a
software repository, or a result store should enter through the documented
`L2` backend bridge rather than through hidden path assumptions.
When proof-grade theory work is active, deeper protocol slices should expose
proof obligations, unresolved-gap routing, multi-source family fusion, the
semi-formal trust boundary, and the selected verification bridge explicitly
instead of collapsing them into one opaque prompt.

The current runtime shell now also materializes:

- `runtime/topics/<topic_slug>/topic_completion.json|md`
- `runtime/topics/<topic_slug>/lean_bridge.active.json|md`
- `runtime/topics/<child_topic_slug>/followup_return_packet.json|md`
- `runtime/topics/<topic_slug>/followup_reintegration.jsonl|md`
- `runtime/topics/<topic_slug>/followup_gap_writeback.jsonl|md`

and Lean-ready exports now carry local `proof_obligations.json` and
`proof_state.json` artifacts for each candidate packet.

The v1.3 runtime now also supports multiple active topics in one workspace.

- `runtime/active_topics.json` is the authoritative active-topic registry
- `runtime/current_topic.json` is the focused-topic compatibility projection
- `aitp loop` may resolve through a deterministic scheduler when no explicit
  topic is supplied

See:

- `../docs/MULTI_TOPIC_RUNTIME.md`
- `../docs/MIGRATE_MULTI_TOPIC.md`

Layer 2 now has two governed writeback paths:

1. Human-reviewed `L2`:
   - `aitp request-promotion ...`
   - human `aitp approve-promotion ...` or `aitp reject-promotion ...`
   - `aitp promote ...`
2. Theory-formal `L2_auto`:
   - `aitp coverage-audit ...`
   - `aitp formal-theory-audit ...`
   - `aitp auto-promote ...`

For theory-formal `L2_auto`, coverage and consensus are necessary but not
sufficient.
Auto-promotion should also remain blocked until the candidate has a ready
`formal_theory_review.json` plus regression-backed, blocker-clear,
split/gap-honest, semi-formal theory packets.

The current public external writeback path targets the standalone
`Theoretical-Physics-Knowledge-Network` repository through the backend card:

- `canonical/backends/theoretical-physics-knowledge-network.json`

Layer 2 now also has three operator-facing derived or quarantine surfaces:

- compiled helper surfaces under `canonical/compiled/`
  - current seed: `workspace_memory_map.json|md`
  - current seed: `workspace_graph_report.json|md`
  - current seed: `derived_navigation/index.md`
- hygiene reports under `canonical/hygiene/`
  - current seed: `workspace_hygiene_report.json|md`
- provisional staging under `canonical/staging/`
  - current seed: `workspace_staging_manifest.json|md`

These do not replace canonical promoted units.
They respectively mean:

- compiled: easier navigation and consultation
- hygiene: audit-only structural review
- staging: durable quarantine for provisional `L2`-adjacent output

For human-readable topic study, runtime topics may also materialize:

- `runtime/topics/<topic_slug>/topic_replay_bundle.json|md`

That replay bundle is derived and points back to authoritative topic artifacts.

Runtime also has a collaborator-side memory ledger that stays outside canonical
scientific memory:

- `runtime/collaborator_memory.jsonl`
- `runtime/collaborator_memory.md`
- `runtime/topics/<topic_slug>/collaborator_profile.active.json|md`
- `runtime/topics/<topic_slug>/research_trajectory.active.json|md`
- `runtime/topics/<topic_slug>/mode_learning.active.json|md`
- `runtime/topics/<topic_slug>/research_judgment.active.json|md`

Those surfaces are for collaborator preference, trajectory, and working-style
memory, restart continuity, reusable route learning, plus the derived judgment
summary that feeds runtime decision surfaces. They are not `L2`, not promotion
input, and not scientific truth.

For low-bureaucracy speculative work, the runtime now also supports a separate
lightweight exploration carrier:

- `runtime/explorations/<exploration_id>/explore_session.json|md`
- `runtime/explorations/<exploration_id>/promotion_request.json|md`

Use:

- `aitp explore "<task>"`
- `aitp promote-exploration --exploration-id <exploration_id> --current-topic`

when you want a first-class speculative path before deciding whether the idea
deserves full topic bootstrap.

## Validation

Run the bundled tests:

```bash
python -m unittest discover -s research/knowledge-hub/tests -v
```

Public bounded smoke tests:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
research/knowledge-hub/runtime/scripts/run_tpkn_formal_promotion_smoke.sh
research/knowledge-hub/runtime/scripts/run_tpkn_formal_auto_promotion_smoke.sh
python research/knowledge-hub/runtime/scripts/run_witten_topological_phases_formal_closure_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_jones_chapter4_finite_product_formal_closure_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_scrpa_control_plane_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_discovery_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_enrichment_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l0_source_concept_graph_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_source_catalog_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l1_vault_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_statement_compilation_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_l1_concept_graph_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_transition_history_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_human_modification_record_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_hypothesis_branch_routing_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_collaborator_continuity_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_quick_exploration_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_dependency_contract_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json
python research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py --json
```

The Witten acceptance script is the bounded real-topic closure check for the
current semi-formal theory runtime lane: it seeds a real Lecture Two theorem
candidate, runs coverage + formal-theory review, dispatches the reviewed
controller actions for `topic_completion` and `lean_bridge`, and then validates
`L2_auto` writeback into a disposable TPKN copy while keeping Lean export as a
downstream bridge rather than the primary meaning of `L2` success.

The Jones Chapter 4 acceptance script is the bounded formal-theory acceptance
for the current Jones benchmark topic: it reuses the active
`jones-von-neumann-algebras` topic, seeds a new Chapter 4 finite-dimensional
finite-product candidate around the compile-checked theorem packet, runs
coverage + formal-theory review, records theorem-facing strategy memory,
compiles a formal-theory `topic_skill_projection`, human-promotes that
projection into `units/topic-skill-projections/`, dispatches the reviewed
controller actions for `topic_completion`, `lean_bridge`, and
`auto_promote_candidate`, and verifies that both the projection and the theorem
packet stay honest about still missing the stronger algebra-level product
theorem and the later whole-book routes.

The scRPA thesis acceptance script is a real-topic shell acceptance for the
formal-theory lane: it opens a topic from the master's-thesis scRPA chapter,
introduction, abstract, and conclusion, verifies that the topic lands in the
formal-theory lane, stays in the light runtime profile, materializes the new
projection surfaces, and keeps the first honest next step at the thesis-to-L0
source-recovery boundary instead of pretending numerical closure already
exists.

The scRPA control-plane acceptance script is the real-topic governance closure
check for the current control-plane milestone: it opens the same thesis-backed
topic class, materializes steering plus registry state, verifies
`aitp doctor --json` control-plane fields, and then runs production
`status`, `capability-audit`, `paired-backend-audit`, and `h-plane-audit`
surfaces while checking their durable runtime artifacts.

The isolated L2 MVP direction acceptance script is the bounded knowledge-memory
closure check for the current `v1.45` milestone: it seeds the TFIM MVP
direction through production CLI, retrieves the seeded `physical_picture`,
compiles the workspace memory map, compiles the human-facing graph report and
derived navigation pages, audits L2 hygiene, and verifies those artifacts on an
isolated temp kernel root instead of mutating repo runtime state.

The L0 source-discovery acceptance script is the bounded `v1.69` search ->
evaluate -> register check for the missing pre-registration entry lane: it
feeds one isolated search-results fixture into
`source-layer/scripts/discover_and_register.py`, verifies that the selected
candidate stays explicit through `candidate_evaluation.json`, and confirms that
canonical registration still lands in the usual Layer 0 plus Layer 1
projection surfaces, now with `deepxiv_enrichment.json`,
`concept_graph.json`, and `concept_graph_receipt.json`, on an isolated temp
kernel root.

The source catalog acceptance script is the bounded Layer 0 reuse check for the
current `v1.46` plus `v1.63` BibTeX surface: it compiles the global source
catalog, traces one bounded citation neighborhood, compiles one source-family
reuse report, exports one bounded BibTeX neighborhood, imports one bounded
BibTeX file back into Layer 0, checks runtime `status --json` source-fidelity
output, and verifies those artifacts on an isolated temp kernel root.

For bounded pre-registration discovery, the current operator entrypoint is:

```bash
python research/knowledge-hub/source-layer/scripts/discover_and_register.py \
  --topic-slug <topic_slug> \
  --query "<natural-language query>"
```

For direct arXiv registration, `source-layer/scripts/register_arxiv_source.py`
now attempts source acquisition by default. Use `--metadata-only` only when the
lightweight registration path is explicitly desired.

The L1 method-specificity acceptance script is the bounded `v1.64` intake
surface check: it uses production `status --json` on an isolated temp kernel
root, verifies that `method_specificity_rows` are materialized inside
`l1_source_intake`, and checks that the same surface is visible in
`research_question.contract.md` and the runtime protocol note.

The L1 assumption/depth acceptance script is the bounded `v1.70` intake-honesty
closure path: it uses production `status --json` on an isolated temp kernel
root, verifies that `assumption_rows`, `reading_depth_rows`, and contradiction
signals are materialized through the existing `l1_source_intake` path, and
checks that the same honesty surface stays visible in
`research_question.contract.md`, `topic_dashboard.md`, the runtime protocol
note, and the `L1` vault wiki page.

The L1 concept-graph acceptance script is the bounded `165.5-02` graph-intake
bridge: it uses production `status --json` on an isolated temp kernel root,
verifies that `l1_source_intake.concept_graph` is materialized from
source-local `concept_graph.json`, and checks that the same graph surface stays
visible in `research_question.contract.md`, the runtime protocol note, and the
`L1` vault wiki source-intake page.

The runtime transition-history acceptance script is the bounded `v1.71`
runtime-history closure path: it uses production `request-promotion`,
production `reject-promotion`, then production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that forward
and backward layer moves become durable `transition_history` artifacts instead
of remaining implicit in overwritten current-stage state.

The human-modification-record acceptance script is the bounded `v1.72`
promotion-gate evaluator-divergence closure path: it uses production
`request-promotion`, then production `approve-promotion --human-modification`
on an isolated temp kernel root, verifying that `promotion_gate.json|md` keeps
structured modification records and that `replay-topic --json` surfaces the
modified approval instead of flattening it into an undifferentiated approval.

The competing-hypotheses acceptance script is the bounded `v1.73`
research-question closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`research_question.contract.md`, the runtime protocol note, and replay all
surface explicit `competing_hypotheses` while deferred candidates and follow-up
subtopics remain visible as separate runtime lanes.

The hypothesis-branch-routing acceptance script is the bounded `v1.74`
post-`v1.73` routing closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that each
competing hypothesis now carries explicit branch-routing metadata, that the
active local branch hypothesis is visible directly, and that deferred parking,
follow-up subtopics, and steering artifacts still coexist as separate runtime
surfaces.

The hypothesis-route-activation acceptance script is the bounded `v1.75`
activation-surface closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_activation` surfaces the active local hypothesis plus its immediate
bounded action, that deferred and follow-up parked obligations remain explicit,
and that this slice does not auto-spawn a follow-up topic directory.

The hypothesis-route-reentry acceptance script is the bounded `v1.76`
re-entry-surface closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_reentry` surfaces deferred reactivation conditions plus follow-up return
readiness, that one parked route can remain waiting while another becomes
re-entry-ready, and that this slice does not write a reintegration receipt or
materialize a reactivated deferred candidate.

The hypothesis-route-handoff acceptance script is the bounded `v1.77`
handoff-surface closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_handoff` surfaces one bounded parked-route handoff candidate plus
explicit keep-parked decisions, that one ready parked route can occupy the
handoff lane while another ready parked route remains parked, and that this
slice does not write a reintegration receipt or materialize a reactivated
deferred candidate.

The hypothesis-route-choice acceptance script is the bounded `v1.78`
choice-surface closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_choice` surfaces one stay-local versus yield-to-handoff summary, that
the local route can stay active while the handoff candidate remains visible as
the yield option, and that this slice does not write a reintegration receipt or
materialize a reactivated deferred candidate.

The hypothesis-route-transition-gate acceptance script is the bounded `v1.79`
transition-gate closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_gate` now surfaces whether yielding is blocked, available, or
checkpoint-gated, that the gate points at the durable route-choice or operator
checkpoint artifact, and that this slice still does not auto-reactivate or
auto-reintegrate parked routes.

The hypothesis-route-transition-intent acceptance script is the bounded
`v1.80` transition-intent closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_intent` now surfaces the proposed source route and target
route after the transition gate, that the intent stays explicit across
proposed, ready, and checkpoint-held states, and that this slice still does not
auto-reactivate or auto-reintegrate parked routes.

The hypothesis-route-transition-receipt acceptance script is the bounded
`v1.81` transition-receipt closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_receipt` now surfaces whether the intended source-to-target
handoff has been durably recorded, that the receipt points at transition-history
artifacts, and that this slice still does not widen into fresh runtime
mutation.

The hypothesis-route-transition-resolution acceptance script is the bounded
`v1.82` transition-resolution closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_resolution` now synthesizes transition intent, transition
receipt, and current active-route state into one resolved operator outcome, and
that this slice still does not widen into fresh runtime mutation.

The hypothesis-route-transition-discrepancy acceptance script is the bounded
`v1.83` transition-discrepancy closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_discrepancy` now flags inconsistent transition state when the
resolved handoff outcome disagrees with upstream route artifacts, and that this
slice still does not widen into fresh runtime mutation.

The hypothesis-route-transition-repair acceptance script is the bounded
`v1.84` transition-repair closure path: it uses production `status --json` and
`replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_repair` now turns transition discrepancy into one bounded
repair plan for the operator, and that this slice still does not widen into
fresh runtime mutation.

The hypothesis-route-transition-escalation acceptance script is the bounded
`v1.85` transition-escalation closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_escalation` now makes it explicit when bounded transition
repair should escalate into a human checkpoint, and that this slice still does
not widen into fresh runtime mutation.

The hypothesis-route-transition-clearance acceptance script is the bounded
`v1.86` transition-clearance closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_clearance` now makes it explicit whether an escalated
transition is still checkpoint-blocked, still awaiting a checkpoint, or has
been released back into bounded follow-through, and that this slice still does
not widen into fresh runtime mutation.

The hypothesis-route-transition-followthrough acceptance script is the bounded
`v1.87` transition-followthrough closure path: it uses production
`status --json` and `replay-topic --json` on an isolated temp kernel root,
verifying that `route_transition_followthrough` now makes it explicit what
bounded transition work should resume after clearance, and that this slice
still does not widen into fresh runtime mutation.

The hypothesis-route-transition-resumption acceptance script is the bounded
`v1.88` transition-resumption closure path: it uses production
`status --json` and `replay-topic --json` on an isolated temp kernel root,
verifying that `route_transition_resumption` now makes it explicit whether
ready follow-through has actually been resumed on the bounded route, and that
this slice still does not widen into fresh runtime mutation.

The hypothesis-route-transition-commitment acceptance script is the bounded
`v1.89` transition-commitment closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_commitment` now makes it explicit whether a resumed route has
become the durable committed bounded lane, and that this slice still does not
widen into fresh runtime mutation.

The hypothesis-route-transition-authority acceptance script is the bounded
`v1.90` transition-authority closure path: it uses production `status --json`
and `replay-topic --json` on an isolated temp kernel root, verifying that
`route_transition_authority` now makes it explicit whether a committed route
has become the authoritative bounded truth across current-topic runtime
surfaces, and that this slice still does not widen into fresh runtime
mutation.

The L1 vault acceptance script is the bounded `v1.68` intake-compilation check:
it uses production `status --json` on an isolated temp kernel root, verifies
that `intake/topics/<topic_slug>/vault/raw|wiki|output` are materialized on the
topic-shell path, and checks that the wiki flowback ledger plus runtime bridge
stay visible in both `research_question.contract.md` and the runtime protocol
note.

The statement-compilation acceptance script is the bounded `v1.68` formalization
pilot check: it seeds one theorem-facing candidate plus minimal theory-packet
inputs on an isolated temp kernel root, runs production
`statement-compilation --json`, then production `lean-bridge --json`, and
checks that declaration skeletons, proof-repair plans, and downstream
Lean-bridge refs all stay explicit and auditable.

The analytical-judgment acceptance script is the bounded `v1.47` closure path
for the new analytical-review plus research-judgment surfaces: it runs
production `analytical-review`, production `verify --mode analytical`, then
production `status --json` on an isolated temp kernel root and checks that
`analytical_review` becomes the primary review bundle while
`research_judgment.active.json|md` and runtime judgment signals are visible.

The collaborator-continuity acceptance script is the bounded `v1.48` closure
path for collaborator profile, trajectory continuity, and mode learning: it
seeds runtime-side collaborator memory plus strategy memory on an isolated temp
kernel root, then runs production `focus-topic`, `status --json`,
`current-topic --json`, and `session-start --json`, checking that the three
continuity surfaces remain visible through real restart paths.

The first-run topic acceptance script is the bounded install-to-use proof for
the shared quickstart path: it uses an isolated temp kernel root, runs
production `bootstrap --json`, production `loop --json`, then production
`status --json`, and checks that a real topic shell, loop state, and runtime
protocol all survive the first-run `bootstrap -> loop -> status` path.

The quick-exploration acceptance script is the bounded `v1.49` closure path for
low-bureaucracy exploration: it runs production `explore --json`, verifies the
lightweight artifact-footprint surface, then runs production
`promote-exploration --current-topic --json`, checking that quick exploration
promotes through a durable request artifact into a bounded `session-start`
contract instead of silently bootstrapping the full topic loop.

The dependency-contract acceptance script is the bounded `v1.50` packaging
closure path: it builds the kernel wheel and sdist, then checks that the
generated distribution metadata exposes bounded `Requires-Dist` entries, the
declared `Requires-Python` floor, and the packaged runtime bundle roots.

The public-install smoke script is the bounded `v1.66` closure path for the
publishable-package milestone: it builds a wheel, installs it into a clean
virtualenv, points `AITP_HOME` at an isolated temp root, then checks
`aitp --version`, `aitp doctor --json`, and the real `bootstrap -> loop ->
status` path through the installed wheel under an isolated virtualenv rather
than through a repo checkout.

The TFIM code-method acceptance script is the bounded code-backed benchmark
lane: it runs the public exact-diagonalization helper on the tiny TFIM config,
opens a `code_method` topic around that workflow, records a baseline-gated
coding operation plus strategy memory, compiles a `topic_skill_projection`, and
verifies that operation trust and runtime surfaces stay inside AITP instead of
turning into an untracked coding side quest.

`topic_skill_projection` is reusable execution memory. When the lane is
`formal_theory`, that means the projection tells the next agent what theorem-
facing artifacts to read and what bounded route is safe to reuse; it is not a
theorem certificate and it does not stand in for proof closure.

## AITP And GSD

This repository may be developed with `GSD`, but active research topics still
belong to `AITP`.

Use `GSD` when the job is changing this repository itself: runtime code, docs,
tests, adapters, packaging, and acceptance scripts.

Use `AITP` when the job is advancing a topic, even when that topic includes
code, benchmarks, or method validation.

The explicit coexistence rule is documented here:

- `../docs/AITP_GSD_WORKFLOW_CONTRACT.md`
