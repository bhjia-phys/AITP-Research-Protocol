# AITP M0.5 Classification Audit

Date: 2026-07-11

Status: reviewed classification baseline plus accepted vertical extensions;
CR1 changed compact visibility for six maintenance capabilities, and the
new-software vertical added three full-surface human-gated Skill lifecycle
capabilities. M1 then added six host-neutral lifecycle capabilities and six
trust-neutral core record families. M3 added reviewed physics knowledge and
source-memory capabilities/families; M4 Tasks 1-3 added procedural Skill
candidate, readiness, package-artifact, and proposal families without compact
or install authority. M4 Task 4 adds one immutable deployment-plan family and
one immutable deployment-receipt family; host intent transitions remain runtime
journals rather than canonical research families.

Writer scan status: all 161 current named-helper rows (111 at the M0 baseline)
and all 173 current direct
mutation rows are classified; scan coverage remains explicitly incomplete.

Source baseline: accepted M0 staged core plus reviewed M1-M4 vertical extensions.
The protected Harness Feedback problem-dossier extension is listed separately
and is not counted as core.

## 1. Classification Rules

The proposed lifecycle classes are:

- `core`: universal research-memory or trust-boundary behavior;
- `vertical_extension`: retained only if a required research vertical owns it;
- `maintenance`: host installation, diagnostics, generated views, or release
  administration, never default research context;
- `migration`: legacy read/audit/reconstruction/migration behavior, never the
  production lifecycle;
- `soft_deprecated`: compatibility forwarding with a documented removal
  condition.

This report is a review worksheet. The compatibility decision and vertical
evidence may move entries between classes. Name patterns were used to find
candidates, but every entry below was reviewed against its state effect,
surface, and intended owner.

## 2. Capability Candidates

### 2.1 Core (59)

```text
active_claim_focus_reconciliation
active_claim_rebind_confirmation
active_claim_rebind_proposal
aitp_context_pack
answer_operator_checkpoint
apply_promotion_packet
assess_risk
attach_artifact
attach_artifact_auto
audit_claim_trust
audit_failure_mode_coverage
audit_l2_memory_context
bind_session
build_failure_mode_review_packet
claim_relation_map
codex_autoroute
codex_closeout
codex_enter
codex_expand
codex_literature_step
codex_record_apply
codex_recording_step
codex_tool_catalog
compact_execution_brief
create_claim
create_promotion_packet
create_topic
create_validation_contract
decide_human_checkpoint
exact_record_expansion
execution_brief
get_trust_update_record
init_workspace
pre_tool_policy
query_index_build
query_index_status
quiet_checkpoint_apply
quiet_checkpoint_preview
recall_audit
record_evidence
record_failure_mode_review_result
record_ref_lookup
record_reference_location
record_validation_result
recording_batch
recording_stage
register_source
register_source_asset
request_failure_mode_review_checkpoint
request_human_checkpoint
request_operator_checkpoint
research_context_compile
session_closeout_apply
session_closeout_plan
session_start
supersede_record
trust_apply
trust_preflight
update_claim_status
```

Review notes:

- `codex_literature_step` is core as a facade operation, not as evidence that
  every literature sub-tool is core.
- promotion and trust operations remain full/human-gated even when their
  underlying invariant is core.
- query index build is derived state and core infrastructure, not a scientific
  write.

### 2.2 Vertical Extension (112)

```text
acquire_arxiv_source_asset
acquire_pdf_source_asset
apply_project_skill
bind_knowledge_connector
capture_code_state_auto
capture_source_asset_auto
capture_tool_run_auto
context_profile_draft
context_profile_templates
create_proof_obligation
curated_rag_chunk
curated_rag_corpus
curated_rag_promotion_draft
curated_rag_search
execute_tool
execution_apply_bound_action
execution_assess_baseline_readiness
execution_assess_scope
execution_build_compute_intake
execution_build_formula_code_capsule
execution_decide_bound_checkpoint
execution_get_record_version
execution_project_derivation_status
execution_project_maturity
execution_request_bound_checkpoint
execution_resolve_effective_attempt
harness_feedback_seed_bundle
host_agnostic_moment_policy
hpc_cockpit
ingest_curated_rag_corpus
ingest_subagent_result
interaction_recording_preview
interaction_recording_worklist
knowledge_build_discovery_request
knowledge_build_source_shelf
knowledge_compile_context
knowledge_diagnose_candidate
knowledge_get_source_shelf
knowledge_normalize_discovery_result
knowledge_promote_candidate
knowledge_query
knowledge_record_review
lane_contract_record
lane_exemplar_manifest
lightweight_record_write_plan
list_authorities
list_domain_packs
list_knowledge_connector_bindings
list_knowledge_connectors
list_monitor_history
list_tool_executors
literature_comparison_draft
literature_corpus_extraction_artifact
literature_extraction_report
literature_reading_route
literature_source_extraction_candidates
literature_source_review_handoff
literature_source_set_readiness
materialize_steering_redirect
note_outline
objective_graph
process_graph_slice
propose_detected_procedural_skill
qsgw_cockpit
qsgw_cockpit_compact
record_authority
record_bounded_numerical_evidence
record_code_state
record_exploratory_record
record_final_output_profile
record_lane_exemplar
record_librpa_code_backed_algorithm_exemplar
record_literature_candidate
record_monitor_snapshot_v2
record_object_relation
record_physics_object
record_qft_qg_source_reconstruction_exemplar
record_research_intent_packet
record_research_route
record_research_run_event
record_run_iteration
record_sensemaking_report
record_source_reconstruction_review_result
record_strategy_memory
record_tool_run
record_toy_numeric_finite_size_exemplar
recording_candidate_classification
recording_effect_verification
recording_navigation_state
recording_slot_expansion
register_tool_recipe
research_cockpit
research_cockpit_compact
research_distillation_candidates
research_event_classifier
research_timeline
request_promotion_checkpoint
request_skill_install_review
run_dir_provenance_extractor_plan
source_reconstruction_audit
source_reconstruction_manifest
source_reconstruction_review_manifest
source_reconstruction_review_packet
source_stack_coverage_manifest
start_research_run
suggest_domain_packs
suggest_literature_intake
summary_orientation
topic_status
topic_status_compact
update_proof_obligation
update_research_run
```

Proposed vertical owners:

- LibRPA/HPC: code state, recipes, tool runs/execution, research runs/events,
  bounded numerical evidence, QSGW/HPC cockpit, run-dir intake;
- QFT/QG: sources, literature route/extraction/review, physics objects and
  relations, proof obligations, source reconstruction, grounded RAG;
- new software: source acquisition, environment/recipe/run capture, validation,
  failure recording, and eventual reviewed skill candidate;
- multi-topic: authorities, relations, strategy/sensemaking, domain-pack
  suggestion, and explicitly reviewed reuse.

Review candidates with no proven final owner yet:

- `harness_feedback_seed_bundle` because the final problem-dossier extension is
  independent and protected;
- compact cockpit duplicates;
- lane exemplars and toy-specific exemplar writers;
- context profiles, interaction worklists, and host-agnostic moment policy;
- `record_final_output_profile` until a vertical proves it cannot be represented
  by artifact, validation, and closeout records.

### 2.3 Maintenance (43)

```text
adapter_packet
adapter_pre_tool_event
adapter_registry
audit_record_routing
capability_registry
claude_code_hook_installation
claude_code_hook_settings
codex_hook_bridge
codex_hook_installation
domain_skill_shims
final_engineering_readiness_audit
goal_continuation_latest
goal_continuation_list
goal_continuation_write
kimi_code_hook_config
kimi_code_hook_installation
l2_obsidian_view
opencode_hook_installation
opencode_plugin_bridge
persist_hook_trace_event
public_surfaces
record_gate_coverage_audit
runtime_bridge_target_manifest
runtime_capability_audit
runtime_hook_installation_audit
runtime_hook_installation_paths
runtime_hook_smoke_coverage
runtime_host_lifecycle_audit
runtime_host_production_loop_audit
runtime_host_readiness_audit
runtime_mcp_bridge_acceptance
runtime_payload_profiles
session_summary
source_reconstruction_obsidian_view
vnext_readiness_manifest
workspace_interaction_preview
workspace_recording_audit
workspace_recovery_audit
workspace_refresh
workspace_replay
workspace_summary
write_workspace_recording_audit
write_workspace_recovery_audit
```

All six current compact maintenance tools belong here:

- `runtime_bridge_target_manifest`
- `runtime_hook_installation_audit`
- `runtime_hook_installation_paths`
- `runtime_hook_smoke_coverage`
- `runtime_mcp_bridge_acceptance`
- `runtime_payload_profiles`

The approved soft-deprecation design removes only their compact visibility; it
keeps full/CLI maintenance access for one compatibility release.

#### Compact Maintenance Caller Evidence

Definitions/catalog rows were excluded from these static counts:

| Operation | Production refs/files | Host instructions/files | Tests/files | Real canonical mentions |
|---|---:|---:|---:|---:|
| `runtime_bridge_target_manifest` | 1 / 1 | 0 / 0 | 6 / 4 | 0 |
| `runtime_hook_installation_audit` | 0 / 0 | 1 / 1 | 3 / 2 | 0 |
| `runtime_hook_installation_paths` | 0 / 0 | 1 / 1 | 3 / 2 | 0 |
| `runtime_hook_smoke_coverage` | 0 / 0 | 1 / 1 | 3 / 2 | 0 |
| `runtime_mcp_bridge_acceptance` | 3 / 2 | 0 / 0 | 7 / 3 | 0 |
| `runtime_payload_profiles` | 1 / 1 | 0 / 0 | 8 / 2 | 0 |

The wider theoretical-physics workspace contains one historical audit-note
mention of `aitp_v5_get_runtime_bridge_target_manifest` and no mention of the
other five names. The canonical topic store contains none of the six names.

Static references are coupling evidence, not runtime telemetry, and cannot
prove that an unknown external host never calls a tool. They support removing
these six operations from default compact discovery while preserving full/CLI
access and deprecation telemetry; they do not support immediate deletion.

`goal_continuation_*` remains maintenance because goal persistence belongs to
the Codex/host runtime, not canonical scientific memory. It may remain as an
optional bridge but must not become a second task orchestrator.

### 2.4 Migration (43)

```text
apply_rehome_plan
apply_workspace_old_store_import
apply_workspace_recovery_binding_repair
build_rehome_plan
canonical_legacy_l2_seed_audit
canonical_legacy_l2_seed_review_worklist
curated_legacy_topics
legacy_executable_evidence_packet
legacy_human_checkpoint_obsidian_view
legacy_human_checkpoint_packet
legacy_l2_graph_manifest
legacy_l2_obsidian_view
legacy_l2_typed_migration_packet
legacy_migration_coverage_audit
legacy_runtime_log_marker_audit
legacy_semantic_needs_revision_basis_obsidian_view
legacy_semantic_needs_revision_basis_packet
legacy_semantic_needs_revision_basis_queue
legacy_semantic_repair_apply
legacy_semantic_repair_manifest
legacy_semantic_repair_plan
legacy_semantic_review_manifest
legacy_semantic_review_obsidian_view
legacy_semantic_review_packet
legacy_semantic_review_queue
legacy_semantic_review_worklist
legacy_source_metadata_repair_packet
legacy_source_reconstruction_apply
legacy_source_reconstruction_manifest
legacy_source_reconstruction_obsidian_view
legacy_source_reconstruction_plan
legacy_source_reconstruction_review_packet
legacy_topic_question_backfill_packet
migrate_curated_legacy_topic
migrate_legacy_topic
record_legacy_l2_seed_group_review_result
record_legacy_semantic_review_result
workspace_file_migration_ledger
workspace_migration_health
workspace_old_store_import_plan
workspace_recovery_binding_repair
write_legacy_migration_accounting_run
write_workspace_file_migration_ledger
```

These capabilities are explicit full/CLI migration surfaces. None belongs in
compact research context. Write/apply operations require a separate migration
checkpoint and are not evidence that the legacy L0-L4 write lifecycle remains
supported.

### 2.5 Soft Deprecated

No core capability is assigned `soft_deprecated` before the user selects the
compatibility policy and the four verticals run. Candidate entries are noted
above but remain available.

### 2.6 Independent Protected Extension

`harness_feedback_problem_dossier` is present only through protected user work
in the primary worktree. It is excluded from the 257-capability staged core and from
this staging scope. Its intended lifecycle is a vertical extension with human
review, not a reason to retain `harness_feedback_seed_bundle` automatically.

Capability accounting:

| Class | Count |
|---|---:|
| Core | 59 |
| Vertical extension | 112 |
| Maintenance | 43 |
| Migration | 43 |
| Soft deprecated classification | 0 |
| Maintenance tools soft-deprecated from compact | 6 |
| Current staged core | 257 |
| Current classified core plus verticals | 257 |

## 3. Record-Family Candidates

### 3.1 Core (25)

```text
active_claim_rebind_audits
artifacts
checkpoints
claim_statuses
claims
contexts
cross_topic_relations
evidence
failure_mode_reviews
lifecycle_events
memory_entries
promotion_packets
quiet_checkpoints
recall_audits
recording_candidate_batches
reference_locations
research_programs
session_closeouts
session_focus_sets
sessions
source_assets
topics
trust_updates
validation_contracts
validation_results
```

### 3.2 Vertical Extension (39)

```text
authorities
artifact_blob_receipts
benchmarks
checkpoint_application_receipts
code_patch_manifests
code_states
code_workspaces
derivation_chains
derivation_reviews
derivation_steps
execution_baselines
execution_environments
exploratory_records
insights
knowledge_review_decisions
lane_contracts
monitor_snapshots
object_relations
physics_assertions
physics_objects
proof_obligations
questions
research_run_events
research_runs
routes
scope_revalidation_decisions
sensemaking_reports
skill_distillation_candidates
skill_install_plans
skill_install_receipts
skill_package_artifacts
skill_patch_proposals
skill_proposals
skill_readiness_reports
source_acquisition_decisions
source_acquisition_receipts
source_reconstruction_reviews
tool_recipes
tool_runs
```

M3/M4 additions stay vertical-owned: source/knowledge families require the
QFT/QG source-memory journey, while procedural Skill families require repeated
validated execution and the reviewed package lifecycle. Registration alone
does not justify a new public tool or automatic write.

### 3.3 Migration (4)

```text
legacy_l2_seed_group_reviews
legacy_semantic_repairs
legacy_semantic_reviews
legacy_source_reconstruction_repairs
```

`legacy_source_reconstruction_repairs` has two real records but no record class.
It requires a read/migration compatibility decision, not automatic promotion to
a new general-purpose family.

### 3.4 Soft-Deprecation Candidates (4)

```text
attempts
ideas
intents
outputs
```

All four are zero-record `unimplemented_layout` families with no record class.
Their concepts overlap existing exploratory records, research routes/intents,
artifacts, validation, and closeout. They remain registered/readable during the
review but may not receive new writes or be used to justify new APIs.

Family accounting totals 72 with no unclassified family.

## 4. Writer Classification

The current runtime audit reports 161 recognized semantic repository writes
and low-level helper calls. Every reported call is classified below by its current storage role,
not by the capability name or intended future architecture. A canonical row is
a writer-convergence target even when it writes a non-registry canonical family
or a topic-local mirror. A migration row may write a typed migration record but
does not belong to the production research lifecycle.

### 4.1 Canonical Record Or Repository (85)

~~~text
brain/v5/_compat_shards/active_claim_focus/part_02.py:_write_rebind_audit:273:write_record | families=active_claim_rebind_audits | dynamic=false
brain/v5/_compat_shards/lifecycle_events/part_01.py:create_lifecycle_event:137:write_record | families=- | dynamic=false
brain/v5/_compat_shards/lifecycle_events/part_01.py:_rewrite_subject_frontmatter:197:write_record | families=- | dynamic=false
brain/v5/_compat_shards/lifecycle_events/part_01.py:_append_cross_topic_pointer:215:write_record | families=- | dynamic=false
brain/v5/_compat_shards/research_state/part_01.py:update_claim_status:211:write_record | families=claim_statuses | dynamic=false
brain/v5/authorities.py:record_authority:76:write_record | families=authorities | dynamic=false
brain/v5/artifact_blobs.py:_record_local_blob:98:repository_write | families=artifact_blob_receipts | dynamic=false
brain/v5/artifact_blobs.py:record_external_artifact_receipt:187:repository_write | families=artifact_blob_receipts | dynamic=false
brain/v5/bound_execution.py:_execute_and_write:294:repository_write | families=tool_runs | dynamic=false
brain/v5/bound_execution.py:_execute_and_write:328:repository_write | families=validation_results | dynamic=false
brain/v5/checkpoint_bindings.py:request_bound_checkpoint:157:repository_write | families=checkpoints | dynamic=false
brain/v5/checkpoint_transactions.py:apply_bound_checkpoint_action:199:repository_write | families=checkpoint_application_receipts | dynamic=false
brain/v5/checkpoint_transactions.py:_record_failed_application:241:repository_write | families=checkpoint_application_receipts | dynamic=false
brain/v5/code.py:record_code_workspace:55:write_record | families=code_workspaces | dynamic=false
brain/v5/code_patch_manifests.py:_write_manifest:170:repository_write | families=code_patch_manifests | dynamic=false
brain/v5/derivation_reviews.py:_write_review:346:repository_write | families=derivation_reviews | dynamic=false
brain/v5/derivations.py:record_derivation_step:43:repository_write | families=derivation_steps | dynamic=false
brain/v5/derivations.py:record_derivation_chain:70:repository_write | families=derivation_chains | dynamic=false
brain/v5/exploration.py:record_exploratory_record:102:repository_write | families=exploratory_records | dynamic=false
brain/v5/execution_baselines.py:write_result:175:repository_write | families=execution_baselines | dynamic=false
brain/v5/execution_environments.py:record_execution_environment:43:repository_write | families=execution_environments | dynamic=false
brain/v5/execution_writers.py:record_code_state_v2:49:repository_write | families=code_states | dynamic=false
brain/v5/execution_writers.py:record_tool_recipe_compat:62:repository_write | families=tool_recipes | dynamic=false
brain/v5/execution_writers.py:write_tool_run_compat:78:repository_write | families=tool_runs | dynamic=false
brain/v5/execution_writers.py:record_tool_recipe_v2:91:repository_write | families=tool_recipes | dynamic=false
brain/v5/execution_writers.py:record_tool_run_v2:121:repository_write | families=tool_runs | dynamic=false
brain/v5/formula_code_map.py:record_formula_code_relation:83:repository_write | families=object_relations | dynamic=false
brain/v5/harness_feedback.py:record_monitor_snapshot:29:write_record | families=monitor_snapshots | dynamic=false
brain/v5/harness_feedback.py:record_skill_patch_proposal:49:write_record | families=skill_patch_proposals | dynamic=false
brain/v5/lane_contracts.py:record_lane_contract:67:write_record | families=lane_contracts | dynamic=false
brain/v5/memory.py:create_promotion_packet:118:repository_write | families=promotion_packets | dynamic=false
brain/v5/memory.py:apply_promotion_packet:170:repository_write | families=memory_entries | dynamic=false
brain/v5/memory.py:apply_promotion_packet:183:repository_write | families=promotion_packets | dynamic=false
brain/v5/memory.py:apply_promotion_packet:194:repository_write | families=memory_entries | dynamic=false
brain/v5/monitor_snapshots.py:record_monitor_snapshot_v2:86:repository_write | families=monitor_snapshots | dynamic=false
brain/v5/monitor_snapshots.py:record_monitor_snapshot_v2:103:repository_write | families=monitor_snapshots | dynamic=false
brain/v5/physics_objects.py:record_physics_object:41:repository_write | families=physics_objects | dynamic=false
brain/v5/physics_objects.py:record_object_relation:93:repository_write | families=object_relations | dynamic=false
brain/v5/proof_obligations.py:create_proof_obligation:81:repository_write | families=proof_obligations | dynamic=false
brain/v5/proof_obligations.py:update_proof_obligation:150:repository_write | families=proof_obligations | dynamic=false
brain/v5/recall_audit.py:run_recall_audit:106:repository_write | families=recall_audits | dynamic=false
brain/v5/record_repository.py:_write_canonical_locked:238:write_text_atomic | families=- | dynamic=false
brain/v5/record_repository.py:_write_canonical_locked:250:write_md | families=- | dynamic=false
brain/v5/record_repository.py:_write_canonical_locked:270:write_md | families=- | dynamic=false
brain/v5/recording_batches.py:coalesce_recording_batch:172:repository_write | families=recording_candidate_batches | dynamic=false
brain/v5/recording_batches.py:coalesce_recording_batch:235:repository_write | families=recording_candidate_batches | dynamic=false
brain/v5/research_scope.py:record_research_program:62:repository_write | families=research_programs | dynamic=false
brain/v5/research_scope.py:record_session_focus_set:78:repository_write | families=session_focus_sets | dynamic=false
brain/v5/research_scope.py:record_cross_topic_relation:97:repository_write | families=cross_topic_relations | dynamic=false
brain/v5/research_runs.py:record_research_run_event:251:write_record | families=- | dynamic=false
brain/v5/research_runs.py:_write_run:281:write_record | families=- | dynamic=false
brain/v5/routes.py:_write_route:135:write_record | families=routes | dynamic=false
brain/v5/scope_revalidation.py:write_result:179:repository_write | families=scope_revalidation_decisions | dynamic=false
brain/v5/sensemaking.py:record_sensemaking_report:39:write_record | families=sensemaking_reports | dynamic=false
brain/v5/session_lifecycle.py:record_session_closeout:186:repository_write | families=session_closeouts | dynamic=false
brain/v5/source_reconstruction_review.py:record_source_reconstruction_review_result:171:write_record | families=source_reconstruction_reviews | dynamic=false
brain/v5/trust_updates.py:_write_claim:160:write_record | families=claims | dynamic=false
brain/v5/trust_updates.py:_write_trust_update_record:239:write_record | families=trust_updates | dynamic=false
brain/v5/workspace.py:create_context:40:write_record | families=- | dynamic=false
brain/v5/workspace.py:create_topic:66:write_record | families=- | dynamic=false
brain/v5/workspace.py:bind_session:112:write_record | families=- | dynamic=false
brain/v5/workspace.py:create_claim:157:write_record | families=claims | dynamic=false
brain/v5/_compat_shards/quiet_checkpoint/part_01.py:apply_quiet_checkpoint_batch:337:repository_write | families=quiet_checkpoints | dynamic=false
brain/v5/_compat_shards/source_assets/part_01.py:register_source_asset:176:repository_write | families=source_assets | dynamic=false
brain/v5/checkpoints.py:request_human_checkpoint:42:repository_write | families=checkpoints | dynamic=false
brain/v5/checkpoints.py:decide_human_checkpoint:97:repository_write | families=checkpoints | dynamic=false
brain/v5/evidence.py:record_artifact_ref:71:repository_write | families=artifacts | dynamic=false
brain/v5/evidence.py:record_evidence:147:repository_write | families=evidence | dynamic=false
brain/v5/failure_mode_review.py:record_failure_mode_review_result:127:repository_write | families=failure_mode_reviews | dynamic=false
brain/v5/references.py:record_reference_location:60:repository_write | families=reference_locations | dynamic=false
brain/v5/skill_candidates.py:propose_procedural_skill:84:repository_write | families=skill_patch_proposals | dynamic=false
brain/v5/skill_install_materialization.py:materialize_plan:156:repository_write | families=skill_install_receipts | dynamic=false
brain/v5/skill_install_planning.py:_record_plan:232:repository_write | families=skill_install_plans | dynamic=false
brain/v5/validation.py:create_validation_contract:62:repository_write | families=validation_contracts | dynamic=false
brain/v5/validation.py:record_validation_result:137:repository_write | families=validation_results | dynamic=false
brain/v5/knowledge_lifecycle.py:record_knowledge_lifecycle_event:78:repository_write | families=lifecycle_events | dynamic=false
brain/v5/knowledge_promotion.py:promote_knowledge_candidate:90:repository_write | families=insights | dynamic=false
brain/v5/knowledge_review.py:_record_knowledge_review_decision:152:repository_write | families=knowledge_review_decisions | dynamic=false
brain/v5/physics_assertions.py:record_physics_assertion:28:repository_write | families=physics_assertions | dynamic=false
brain/v5/project_skill_packages.py:record_skill_proposal:212:repository_write | families=skill_proposals | dynamic=false
brain/v5/skill_distillation_records.py:record_skill_distillation_candidate:127:repository_write | families=skill_distillation_candidates | dynamic=false
brain/v5/skill_package_artifacts.py:record_skill_package_artifact:79:repository_write | families=skill_package_artifacts | dynamic=false
brain/v5/skill_readiness.py:record_skill_readiness_report:135:repository_write | families=skill_readiness_reports | dynamic=false
brain/v5/source_acquisition.py:record_source_acquisition_decision:91:repository_write | families=source_acquisition_decisions | dynamic=false
brain/v5/source_acquisition.py:record_source_acquisition_receipt:157:repository_write | families=source_acquisition_receipts | dynamic=false
~~~

### 4.2 Derived Index Or Surface (29)

~~~text
brain/v5/_compat_shards/cli/part_04.py:_dispatch_workspace_02:116:write_text_atomic | families=- | dynamic=false
brain/v5/obsidian_views.py:write_l2_obsidian_view:40:write_md | families=- | dynamic=false
brain/v5/obsidian_views.py:write_l2_obsidian_view:47:write_md | families=- | dynamic=false
brain/v5/obsidian_views.py:write_l2_obsidian_view:48:write_md | families=- | dynamic=false
brain/v5/query_index.py:_build_query_index_locked:268:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_delta.py:_project_record_delta_locked:156:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_delta_repair.py:_write_repair_rows:206:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_delta_storage.py:_publish_delta_manifest:115:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_generation.py:write_immutable_generation:51:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_generation.py:write_immutable_generation:55:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_generation.py:write_immutable_generation:59:write_text_atomic | families=- | dynamic=false
brain/v5/query_index_generation.py:write_immutable_generation:63:write_text_atomic | families=- | dynamic=false
brain/v5/replay.py:write_workspace_replay_packet:76:write_md | families=- | dynamic=false
brain/v5/research_runs.py:_write_run:283:write_md | families=- | dynamic=false
brain/v5/routes.py:_write_route:137:write_record | families=- | dynamic=false
brain/v5/source_reconstruction_obsidian.py:write_source_reconstruction_obsidian_view:23:write_md | families=- | dynamic=false
brain/v5/summaries.py:write_session_summary:85:write_md | families=- | dynamic=false
brain/v5/summaries.py:write_workspace_summary:142:write_md | families=- | dynamic=false
brain/v5/trust_updates.py:_write_claim:161:write_record | families=- | dynamic=false
brain/v5/workspace.py:create_claim:159:write_record | families=- | dynamic=false
brain/v5/workspace_inventory.py:write_workspace_inventory_report:173:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recording_audit.py:write_workspace_recording_audit:199:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recording_audit.py:write_workspace_recording_audit:203:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recovery_audit.py:write_workspace_recovery_audit:165:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recovery_audit.py:write_workspace_recovery_audit:169:write_text_atomic | families=- | dynamic=false
brain/v5/project_skill_packages.py:_write_preview:323:write_text_atomic | families=- | dynamic=false
brain/v5/source_shelf_storage.py:_write_shelf_files:247:write_text_atomic | families=- | dynamic=false
brain/v5/source_shelf_storage.py:_write_shelf_files:251:write_text_atomic | families=- | dynamic=false
brain/v5/source_shelf_storage.py:_write_shelf_files:255:write_text_atomic | families=- | dynamic=false
~~~

### 4.3 Host Or Runtime (17)

~~~text
brain/v5/_compat_shards/lane_exemplars/part_01.py:record_lane_exemplar:119:write_md | families=- | dynamic=false
brain/v5/checkpoint_transactions.py:_write_journal:367:write_text_atomic | families=- | dynamic=false
brain/v5/domain_packs.py:register_domain_pack:150:write_record | families=- | dynamic=false
brain/v5/knowledge_connector_bindings.py:_write_bindings:158:write_text_atomic | families=- | dynamic=false
brain/v5/operator_checkpoint.py:_write_active:174:write_md | families=- | dynamic=false
brain/v5/output_stability.py:record_final_output_profile:61:write_md | families=- | dynamic=false
brain/v5/research_intent.py:record_research_intent_packet:78:write_md | families=- | dynamic=false
brain/v5/research_intent.py:materialize_steering_redirect:121:write_md | families=- | dynamic=false
brain/v5/recording_batch_storage.py:write_candidate:70:write_text_atomic | families=- | dynamic=false
brain/v5/recording_batch_storage.py:write_recording_batch_receipt:128:write_text_atomic | families=- | dynamic=false
brain/v5/run_iterations.py:_write_iteration_files:134:write_md | families=- | dynamic=false
brain/v5/run_iterations.py:_write_iteration_files:136:write_md | families=- | dynamic=false
brain/v5/run_iterations.py:_write_iteration_files:138:write_md | families=- | dynamic=false
brain/v5/run_iterations.py:_write_journal:156:write_md | families=- | dynamic=false
brain/v5/skill_install_materialization.py:write_journal:322:write_text_atomic | families=- | dynamic=false
brain/v5/workspace.py:init_workspace:27:write_md | families=- | dynamic=false
brain/v5/human_approval.py:persist_human_approval_receipt:95:write_text_atomic | families=- | dynamic=false
~~~

### 4.4 Migration Or Legacy Compatibility (28)

~~~text
brain/v5/_compat_shards/cli/part_04.py:_dispatch_workspace_02:135:write_text_atomic | families=- | dynamic=false
brain/v5/_compat_shards/cli/part_04.py:_dispatch_workspace_02:152:write_text_atomic | families=- | dynamic=false
brain/v5/_compat_shards/curated_legacy_migration/part_01.py:_write_curated_index:344:write_md | families=- | dynamic=false
brain/v5/_compat_shards/legacy_bridge/part_02.py:_write_generic_migration_index:59:write_text_atomic | families=- | dynamic=false
brain/v5/_compat_shards/legacy_l2_seed_audit/part_01.py:record_legacy_l2_seed_group_review_result:311:write_record | families=legacy_l2_seed_group_reviews | dynamic=false
brain/v5/_compat_shards/workspace_file_migration_ledger/part_01.py:write_workspace_file_migration_ledger:221:write_text_atomic | families=- | dynamic=false
brain/v5/_compat_shards/workspace_file_migration_ledger/part_01.py:write_workspace_file_migration_ledger:225:write_text_atomic | families=- | dynamic=false
brain/v5/legacy_human_checkpoint_obsidian.py:write_legacy_human_checkpoint_obsidian_view:25:write_md | families=- | dynamic=false
brain/v5/legacy_l2_obsidian.py:write_legacy_l2_obsidian_view:31:write_md | families=- | dynamic=false
brain/v5/legacy_l2_obsidian.py:write_legacy_l2_obsidian_view:36:write_md | families=- | dynamic=false
brain/v5/legacy_l2_obsidian.py:write_legacy_l2_obsidian_view:41:write_md | families=- | dynamic=false
brain/v5/legacy_l2_obsidian.py:write_legacy_l2_obsidian_view:46:write_md | families=- | dynamic=false
brain/v5/legacy_migration_accounting.py:_write_json:331:write_text_atomic | families=- | dynamic=false
brain/v5/legacy_migration_records.py:migrate_legacy_l2_memory:277:write_record | families=- | dynamic=false
brain/v5/legacy_semantic_needs_revision_obsidian.py:write_legacy_semantic_needs_revision_basis_obsidian_view:24:write_md | families=- | dynamic=false
brain/v5/legacy_semantic_repair.py:_write_claim:431:write_record | families=claims | dynamic=false
brain/v5/legacy_semantic_repair.py:_write_claim:434:write_record | families=- | dynamic=false
brain/v5/legacy_semantic_repair.py:_apply_payload:468:write_record | families=legacy_semantic_repairs | dynamic=false
brain/v5/legacy_semantic_review.py:record_legacy_semantic_review_result:204:write_record | families=legacy_semantic_reviews | dynamic=false
brain/v5/legacy_semantic_review_obsidian.py:write_legacy_semantic_review_obsidian_view:24:write_md | families=- | dynamic=false
brain/v5/legacy_source_reconstruction.py:_apply_payload:400:write_record | families=legacy_source_reconstruction_repairs | dynamic=false
brain/v5/legacy_source_reconstruction_obsidian.py:write_legacy_source_reconstruction_obsidian_view:24:write_md | families=- | dynamic=false
brain/v5/workspace_migration_plan.py:write_workspace_migration_plan_report:200:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_old_store_import.py:write_workspace_old_store_import_result:182:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_old_store_import.py:write_workspace_old_store_import_result:186:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_old_store_manifest.py:write_workspace_old_store_manifest_report:126:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recovery_binding_repair.py:write_workspace_recovery_binding_repair:172:write_text_atomic | families=- | dynamic=false
brain/v5/workspace_recovery_binding_repair.py:write_workspace_recovery_binding_repair:176:write_text_atomic | families=- | dynamic=false
~~~

### 4.5 Shared Storage Primitive (2)

~~~text
brain/v5/markdown.py:write_md:83:write_text_atomic | families=- | dynamic=false
brain/v5/store.py:write_record:45:write_md | families=- | dynamic=false
~~~

The first writer-convergence slice now covers the LibRPA vertical only:

- source assets and reference locations;
- code state;
- tool recipe and tool run;
- artifact and validation;
- validation contract/result;
- claim status and closeout links.

All ten canonical families exercised by its acceptance test now traverse
`RecordRepository`. Repeated source/artifact registration reuses immutable
identity without implicit revision; validation and evidence identity includes
its complete immutable basis; tool-run supersession is a hash-protected forward
edge and never patches the prior attempt. The automated vertical leaves its
human checkpoint open and proves that it cannot unlock an adversarial trust
change. Run-iteration journals, acquired blobs, and patch files remain
derived/runtime or canonical-blob outputs rather than registry records.

Trust/promotion, migration, theory-object, optional Harness Feedback, and
host/runtime writers remain measured but are not rewritten in the first slice.
After the accepted M1 lifecycle extension, the canonical/repository class has
56 visible responsibility rows. Its seven new semantic rows are one recall
audit, two idempotent recording-batch paths, three research-scope sidecars, and
one session closeout; all traverse `RecordRepository` and have no claim-trust
effect. Topic-local mirrors remain derived and cannot become a second truth
source.

The 111-row static audit is an under-approximation of filesystem mutation. It
recognizes semantic `RecordRepository.write` calls plus calls named
`write_record`, `write_md`, `write_text_atomic`, and `write_json_atomic` under
`brain/`, `hooks/`, and `deploy/hooks/`, but it does
not yet cover direct `Path.write_text`, `Path.open` append/write modes, JSONL
helpers, copies, renames, SQLite writes, or writer calls in `scripts/` and other
trees. The classifications above close the current scanner output but cannot
yet prove complete writer closure. CR0 must expand and test scanner coverage
before any repository-wide canonical-bypass claim is accepted.

A second conservative AST scanner is now represented separately by
`direct_mutation_candidates`. It excludes tests and recognizes direct
`write_text`/`write_bytes`, literal write-mode `open`, write-flag `os.open`,
`shutil` copy/move, `os` rename/replace, and literal SQL mutations. On the
current repository it finds 173 additional mutation candidates across 66
production files:

- 119 direct path writes, 24 write-mode opens, 15 copy/move calls, and 15
  rename/replace calls;
- 66 calls in 28 `brain/v5` files;
- 40 calls in 20 legacy `brain` files;
- 59 calls in 12 `scripts` files;
- seven calls in five host-hook files;
- one plugin-launcher write.

Some are low-level primitive implementations, derived outputs, downloads, or
host installation rather than canonical research writers. They must be
classified by target path and role after scanner expansion; they must not be
silently added to the canonical-bypass count or ignored because they are not
named helpers.

The expanded runtime-audit contract now publishes two distinct closure facts.
All 716 Python files under the declared production source prefixes are
enumerated and parsed with zero errors, so
`writer_scan_policy.bounded_coverage_complete` is true. Dynamic/aliased APIs,
non-literal database mutations, unrecognized helpers, reflection, and native
extensions are explicitly excluded mechanisms, so the unbounded
`writer_scan_policy.coverage_complete` remains false. This closes the M0.5
scanner-policy decision without fabricating a repository-wide no-bypass proof.

### 4.6 Direct Mutation Candidate Classification

These classes describe current target ownership. They do not authorize a
mutation, make a derived file canonical, or make an archived legacy writer part
of the production lifecycle.

### 4.6.1 Canonical Blob Or Record (7)

~~~text
brain/v5/artifact_blobs.py:_stage_source_blob:239:NamedTemporaryFile | families=- | dynamic=false
brain/v5/artifact_blobs.py:_stage_source_blob:263:replace | families=- | dynamic=false
brain/v5/artifact_blobs.py:_store_blob_content:284:NamedTemporaryFile | families=- | dynamic=false
brain/v5/artifact_blobs.py:_store_blob_content:296:replace | families=- | dynamic=false
brain/v5/_compat_shards/source_assets/part_02.py:_store_acquired_blob:369:copyfile | mechanism=copy_or_move | target=tmp_path
brain/v5/_compat_shards/source_assets/part_02.py:_store_acquired_blob:370:replace | mechanism=rename_or_replace | target=destination
brain/v5/code.py:_write_patch_artifact_file:288:write_text | mechanism=direct_path_write | target=patch_path
~~~

The blob and patch bytes require receipt/hash ownership in the LibRPA and
source-acquisition verticals. Their metadata records remain separate canonical
records; copying bytes alone cannot create evidence or trust.

### 4.6.2 Derived Index Or Surface (24)

~~~text
brain/v5/_compat_shards/curated_rag_corpus/part_01.py:ingest_curated_rag_corpus:141:write_text | mechanism=direct_path_write | target=corpus_path
brain/v5/_compat_shards/curated_rag_corpus/part_01.py:ingest_curated_rag_corpus:151:write_text | mechanism=direct_path_write | target=index_path
brain/v5/qsgw_cockpit.py:write_qsgw_cockpit_surfaces:78:write_text | mechanism=direct_path_write | target=Path(files['dashboard_dry_run'])
brain/v5/qsgw_cockpit.py:write_qsgw_cockpit_surfaces:79:write_text | mechanism=direct_path_write | target=Path(files['plot_guard'])
brain/v5/qsgw_cockpit.py:_write_json:813:write_text | mechanism=direct_path_write | target=path
brain/v5/research_cockpit.py:write_research_cockpit_surfaces:50:write_text | mechanism=direct_path_write | target=Path(files['dashboard'])
brain/v5/research_cockpit.py:write_research_cockpit_surfaces:51:write_text | mechanism=direct_path_write | target=Path(files['queue'])
brain/v5/research_cockpit.py:_write_json:788:write_text | mechanism=direct_path_write | target=path
brain/v5/research_runs.py:_write_run:284:write_text | mechanism=direct_path_write | target=runtime_dir / f'{record.run_id}.json'
brain/v5/research_runs.py:_append_topic_timeline:292:open | mechanism=direct_open_write | target=runtime_dir / 'research_run_events.jsonl'
brain/v5/topic_status.py:write_topic_status_surfaces:41:write_text | mechanism=direct_path_write | target=Path(files['topic_dashboard'])
brain/v5/topic_status.py:write_topic_status_surfaces:42:write_text | mechanism=direct_path_write | target=Path(files['operator_console'])
brain/v5/topic_status.py:write_topic_status_surfaces:43:write_text | mechanism=direct_path_write | target=Path(files['claim_relation_map'])
brain/v5/topic_status.py:write_topic_status_surfaces:47:write_text | mechanism=direct_path_write | target=Path(files['runtime_protocol'])
brain/v5/topic_status.py:write_topic_status_surfaces:48:write_text | mechanism=direct_path_write | target=Path(files['session_start'])
brain/v5/source_shelf_storage.py:publish_source_shelf:71:rename | mechanism=rename_or_replace | target=target
brain/v5/topic_status.py:_write_json:375:write_text | mechanism=direct_path_write | target=path
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:65:write_text | mechanism=direct_path_write | target=Path(files['topic_state'])
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:69:write_text | mechanism=direct_path_write | target=Path(files['topic_dashboard'])
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:70:write_text | mechanism=direct_path_write | target=Path(files['operator_console'])
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:71:write_text | mechanism=direct_path_write | target=Path(files['claim_relation_map'])
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:75:write_text | mechanism=direct_path_write | target=Path(files['runtime_protocol'])
brain/v5/topic_status_startup.py:write_topic_status_startup_surfaces:76:write_text | mechanism=direct_path_write | target=Path(files['session_start'])
scripts/demo_example_output.py:main:100:write_text | mechanism=direct_path_write | target=tex_path
~~~

### 4.6.3 Host Runtime Or Maintenance (61)

~~~text
brain/v5/_compat_shards/lane_exemplars/part_03.py:_append_jsonl:54:open | mechanism=direct_open_write | target=path
brain/v5/goal_continuation.py:write_goal_continuation:73:write_text | mechanism=direct_path_write | target=json_path
brain/v5/goal_continuation.py:write_goal_continuation:77:write_text | mechanism=direct_path_write | target=md_path
brain/v5/goal_continuation.py:_update_latest:360:write_text | mechanism=direct_path_write | target=latest_json
brain/v5/goal_continuation.py:_update_latest:361:write_text | mechanism=direct_path_write | target=latest_md
brain/v5/hook_codex_install.py:install_codex_hooks_json:59:write_text | mechanism=direct_path_write | target=hooks_path
brain/v5/hook_fixture_templates.py:_write_fixture:208:write_text | mechanism=direct_path_write | target=fixture_path
brain/v5/hook_install_templates.py:write_codex_hook_bridge:108:write_text | mechanism=direct_path_write | target=bridge_path
brain/v5/hook_install_templates.py:write_opencode_plugin_bridge:163:write_text | mechanism=direct_path_write | target=bridge_path
brain/v5/hook_install_templates.py:write_claude_code_hook_settings:180:write_text | mechanism=direct_path_write | target=settings_path
brain/v5/hook_install_templates.py:install_claude_code_hook_settings:225:write_text | mechanism=direct_path_write | target=settings_path
brain/v5/hook_install_templates.py:_write_payload_sidecar:374:write_text | mechanism=direct_path_write | target=sidecar_path
brain/v5/hook_kimi_install.py:write_kimi_code_hook_config:33:write_text | mechanism=direct_path_write | target=config_path
brain/v5/hook_kimi_install.py:install_kimi_code_hook_config:57:write_text | mechanism=direct_path_write | target=config_path
brain/v5/hook_opencode_install.py:install_opencode_plugin_file:64:write_text | mechanism=direct_path_write | target=plugin_path
brain/v5/native_mcp.py:_log:55:open | mechanism=direct_open_write | target=_DIAG
brain/v5/operator_checkpoint.py:_append_ledger:179:open | mechanism=direct_open_write | target=path
brain/v5/operator_checkpoint.py:_write_json:190:write_text | mechanism=direct_path_write | target=path
brain/v5/output_stability.py:_write_json:97:write_text | mechanism=direct_path_write | target=path
brain/v5/output_stability.py:_append_jsonl:101:open | mechanism=direct_open_write | target=path
brain/v5/research_intent.py:_write_json:193:write_text | mechanism=direct_path_write | target=path
brain/v5/research_intent.py:_append_jsonl:197:open | mechanism=direct_open_write | target=path
brain/v5/run_iterations.py:_write_json:349:write_text | mechanism=direct_path_write | target=path
brain/v5/skill_install_host_safety.py:replace:63:replace | mechanism=rename_or_replace | target=target
brain/v5/skill_install_host_safety.py:replace:65:replace | mechanism=rename_or_replace | target=target.name
brain/v5/skill_install_host_safety.py:materialize_stage:160:write_bytes | mechanism=direct_path_write | target=stage_guard
brain/v5/skill_install_host_safety.py:_write_relative_posix:350:open | mechanism=direct_open_write | target=parts[-1]
brain/v5/strategy_memory.py:record_strategy_memory:69:open | mechanism=direct_open_write | target=path
brain/v5/trace.py:append_trace_event:34:open | mechanism=direct_open_write | target=trace_path
hooks/aitp_event.py:record_event:45:write_text | mechanism=direct_path_write | target=log_path
hooks/aitp_l4_watchdog.py:record_completion:205:write_text | mechanism=direct_path_write | target=state_path
hooks/aitp_l4_watchdog.py:_append_log:222:write_text | mechanism=direct_path_write | target=log_path
hooks/compact.py:main:136:write_text | mechanism=direct_path_write | target=sessions_path
hooks/hook_utils.py:_atomic_write_text:146:fdopen | mechanism=direct_open_write | target=fd
hooks/hook_utils.py:_atomic_write_text:148:replace | mechanism=rename_or_replace | target=path
hooks/session_start.py:_record_session_start:220:write_text | mechanism=direct_path_write | target=marker
plugins/aitp-research-protocol/scripts/launch_aitp_mcp.py:_write_config:57:write_text | mechanism=direct_path_write | target=CONFIG_PATH
scripts/aitp-pm.py:_register_cli:123:write_text | mechanism=direct_path_write | target=wrapper
scripts/aitp-pm.py:_register_cli:129:write_text | mechanism=direct_path_write | target=wrapper
scripts/aitp-pm.py:_atomic_write:612:fdopen | mechanism=direct_open_write | target=fd
scripts/aitp-pm.py:_atomic_write:614:replace | mechanism=rename_or_replace | target=path
scripts/aitp-pm.py:_deploy_claude_code:1299:write_text | mechanism=direct_path_write | target=dst
scripts/aitp-pm.py:_deploy_claude_code:1308:write_text | mechanism=direct_path_write | target=dst_dir / 'SKILL.md'
scripts/aitp-pm.py:cmd_update:1958:copy2 | mechanism=copy_or_move | target=dest
scripts/split_domain_pack_data.py:main:26:write_text | mechanism=direct_path_write | target=package / '__init__.py'
scripts/split_domain_pack_data.py:main:40:write_text | mechanism=direct_path_write | target=module
scripts/split_domain_pack_data.py:main:55:write_text | mechanism=direct_path_write | target=target.parent / 'domain_pack_types.py'
scripts/split_domain_pack_data.py:main:84:write_text | mechanism=direct_path_write | target=target
scripts/split_runtime_entrypoint_catalog.py:main:52:write_text | mechanism=direct_path_write | target=package / '__init__.py'
scripts/split_runtime_entrypoint_catalog.py:main:60:write_text | mechanism=direct_path_write | target=package / f'{name}.py'
scripts/split_runtime_entrypoint_catalog.py:main:88:write_text | mechanism=direct_path_write | target=target
scripts/split_runtime_entrypoint_samples.py:main:50:write_text | mechanism=direct_path_write | target=package / f'part_{index:02d}.py'
scripts/split_runtime_entrypoint_samples.py:main:60:write_text | mechanism=direct_path_write | target=package / '__init__.py'
scripts/split_runtime_entrypoint_samples.py:main:88:write_text | mechanism=direct_path_write | target=target
scripts/split_shared_v5_facades.py:main:33:write_text | mechanism=direct_path_write | target=temp / 'user-overlap.patch'
scripts/split_shared_v5_facades.py:main:62:write_text | mechanism=direct_path_write | target=target
scripts/split_shared_v5_facades.py:main:69:copy2 | mechanism=copy_or_move | target=real_target
scripts/split_shared_v5_facades.py:main:70:copytree | mechanism=copy_or_move | target=real_shards
scripts/split_v5_cli_functions.py:main:183:write_text | mechanism=direct_path_write | target=target
scripts/split_v5_compat_modules.py:split_module:57:write_text | mechanism=direct_path_write | target=shard_path
scripts/split_v5_compat_modules.py:split_module:80:write_text | mechanism=direct_path_write | target=module_path
~~~

### 4.6.4 Migration Or Archived Legacy (75)

~~~text
brain/cli/__init__.py:cmd_topic_init:274:write_text | mechanism=direct_path_write | target=root / 'MEMORY.md'
brain/cli/__init__.py:cmd_topic_init:277:write_text | mechanism=direct_path_write | target=root / 'research.md'
brain/cli/__init__.py:cmd_topic_init:287:write_text | mechanism=direct_path_write | target=root / 'compute' / 'targets.yaml'
brain/cli/__init__.py:cmd_topic_init:298:write_text | mechanism=direct_path_write | target=root / 'runtime' / 'log.md'
brain/cli/commands/compute.py:_append_research_md:130:write_text | mechanism=direct_path_write | target=path
brain/cli/commands/compute.py:_append_research_md:132:write_text | mechanism=direct_path_write | target=path
brain/cli/commands/compute.py:cmd_compute_prepare:151:write_text | mechanism=direct_path_write | target=script_path
brain/cli/commands/compute.py:cmd_compute_prepare:179:write_text | mechanism=direct_path_write | target=audit_path
brain/cli/commands/compute.py:cmd_compute_submit:240:write_text | mechanism=direct_path_write | target=root / 'state.md'
brain/cli/commands/compute.py:cmd_compute_check:284:write_text | mechanism=direct_path_write | target=root / 'state.md'
brain/cli/commands/compute.py:cmd_compute_validate:350:write_text | mechanism=direct_path_write | target=val_path
brain/cli/commands/compute.py:cmd_compute_report:428:write_text | mechanism=direct_path_write | target=report_path
brain/cli/commands/l2.py:_write_md:38:write_text | mechanism=direct_path_write | target=path
brain/cli/commands/l2.py:cmd_l2_merge:126:copy2 | mechanism=copy_or_move | target=dst
brain/cli/commands/l3_workflow.py:cmd_quick_compute:290:NamedTemporaryFile | mechanism=direct_open_write | target=-
brain/cli/commands/l3_workflow.py:_atomic_write:47:replace | mechanism=rename_or_replace | target=path
brain/cli/commands/memory_cmd.py:_atomic_write:22:replace | mechanism=rename_or_replace | target=path
brain/cli/commands/source.py:_write_md:43:write_text | mechanism=direct_path_write | target=path
brain/cli/commands/source.py:_atomic_write:55:replace | mechanism=rename_or_replace | target=path
brain/cli/commands/source.py:_download_file:78:open | mechanism=direct_open_write | target=dest
brain/cli/commands/source.py:cmd_source_add:142:copy2 | mechanism=copy_or_move | target=dest
brain/cli/commands/source.py:cmd_source_add:151:copy2 | mechanism=copy_or_move | target=dest
brain/cli/commands/sympy_check.py:cmd_sympy_execute:155:write_text | mechanism=direct_path_write | target=report_path
brain/cli/commands/sympy_check.py:cmd_sympy_execute:163:write_text | mechanism=direct_path_write | target=rp
brain/cli/commands/verify.py:_atomic_write:47:replace | mechanism=rename_or_replace | target=path
brain/cli/migrate.py:migrate_topic:81:write_text | mechanism=direct_path_write | target=fp
brain/cli/migrate_v1_1.py:_write_md:69:write_text | mechanism=direct_path_write | target=path
brain/cli/observability.py:log_event:33:open | mechanism=direct_open_write | target=session_path
brain/cli/observability.py:log_event:43:write_text | mechanism=direct_path_write | target=current_path
brain/cli/state.py:atomic_write:208:replace | mechanism=rename_or_replace | target=path
brain/flow_notebook/hashing.py:_save_hash_state:37:write_text | mechanism=direct_path_write | target=p
brain/gates.py:evaluate_l1_stage:400:write_text | mechanism=direct_path_write | target=index_path
brain/l2_graph_rebuild.py:_write_md:46:write_text | mechanism=direct_path_write | target=path
brain/l2_graph_rebuild.py:_rebuild_graph_html:398:write_text | mechanism=direct_path_write | target=html_path
brain/mcp_minimal.py:<module>:9:open | mechanism=direct_open_write | target=LOG
brain/mcp_server.py:_atomic_write_text:343:fdopen | mechanism=direct_open_write | target=fd
brain/mcp_server.py:_atomic_write_text:345:replace | mechanism=rename_or_replace | target=path
brain/native_mcp.py:_log:33:open | mechanism=direct_open_write | target=_DIAG
brain/native_mcp_wrapper.py:log:8:open | mechanism=direct_open_write | target=LOG
brain/tools/l4_code_method.py:analyze_l4_run:648:write_text | mechanism=direct_path_write | target=output_path
brain/v5/workspace_old_store_import.py:apply_workspace_old_store_import_plan:97:copy2 | mechanism=copy_or_move | target=target
scripts/convert_legacy_to_v2.py:convert_l0:217:write_text | mechanism=direct_path_write | target=l0_v2 / f'{safe_id}.md'
scripts/convert_legacy_to_v2.py:convert_l0:249:write_text | mechanism=direct_path_write | target=target
scripts/convert_legacy_to_v2.py:convert_l1:273:write_text | mechanism=direct_path_write | target=l1_v2 / 'question_contract.md'
scripts/convert_legacy_to_v2.py:convert_l1:298:write_text | mechanism=direct_path_write | target=l1_v2 / 'source_basis.md'
scripts/convert_legacy_to_v2.py:convert_l1:307:write_text | mechanism=direct_path_write | target=l1_v2 / 'convention_snapshot.md'
scripts/convert_legacy_to_v2.py:convert_l1:319:write_text | mechanism=direct_path_write | target=l1_v2 / 'derivation_anchor_map.md'
scripts/convert_legacy_to_v2.py:convert_l1:324:write_text | mechanism=direct_path_write | target=l1_v2 / 'contradiction_register.md'
scripts/convert_legacy_to_v2.py:convert_l3:355:write_text | mechanism=direct_path_write | target=ideation_dir / 'active_idea.md'
scripts/convert_legacy_to_v2.py:convert_l3:395:write_text | mechanism=direct_path_write | target=plan_dir / 'active_plan.md'
scripts/convert_legacy_to_v2.py:convert_l3:457:write_text | mechanism=direct_path_write | target=analysis_dir / 'active_analysis.md'
scripts/convert_legacy_to_v2.py:convert_l3:495:write_text | mechanism=direct_path_write | target=integration_dir / 'active_integration.md'
scripts/convert_legacy_to_v2.py:convert_l3:524:write_text | mechanism=direct_path_write | target=distill_dir / 'active_distillation.md'
scripts/convert_legacy_to_v2.py:convert_l3:563:write_text | mechanism=direct_path_write | target=cand_dir / f'{safe_cid}.md'
scripts/convert_legacy_to_v2.py:convert_l3:572:copy2 | mechanism=copy_or_move | target=tex_dir / 'flow_notebook.tex'
scripts/convert_legacy_to_v2.py:convert_l3:577:copy2 | mechanism=copy_or_move | target=tex_dir / 'flow_notebook.tex'
scripts/convert_legacy_to_v2.py:convert_l3:594:write_text | mechanism=direct_path_write | target=tex_dir / 'flow_notebook.tex'
scripts/convert_legacy_to_v2.py:convert_l4:624:write_text | mechanism=direct_path_write | target=l4_v2 / 'validation_contract.md'
scripts/convert_legacy_to_v2.py:convert_l4:654:write_text | mechanism=direct_path_write | target=reviews_dir / f'{safe_rid}.md'
scripts/convert_legacy_to_v2.py:update_runtime:668:write_text | mechanism=direct_path_write | target=log_path
scripts/convert_legacy_to_v2.py:update_runtime:671:write_text | mechanism=direct_path_write | target=log_path
scripts/convert_legacy_to_v2.py:update_runtime:684:write_text | mechanism=direct_path_write | target=runtime_dir / 'index.md'
scripts/convert_legacy_to_v2.py:main:780:write_text | mechanism=direct_path_write | target=manifest_path
scripts/create_topics_from_scattered.py:_write_md:38:write_text | mechanism=direct_path_write | target=path
scripts/create_topics_from_scattered.py:register_source:89:write_text | mechanism=direct_path_write | target=state_path
scripts/create_topics_from_scattered.py:copy_to_runtime:205:copy2 | mechanism=copy_or_move | target=dest
scripts/create_topics_from_scattered.py:copy_to_runtime:212:copy2 | mechanism=copy_or_move | target=dest
scripts/create_topics_from_scattered.py:merge_hs_like_chaos_window:469:copy2 | mechanism=copy_or_move | target=dest
scripts/generate_l2_viz.py:generate_html:435:write_text | mechanism=direct_path_write | target=output_path
scripts/migrate_legacy_topics.py:migrate_topic:215:write_text | mechanism=direct_path_write | target=v2_topic / 'state.md'
scripts/migrate_legacy_topics.py:migrate_topic:235:write_text | mechanism=direct_path_write | target=l0_dir / f'{safe_id}.md'
scripts/migrate_legacy_topics.py:migrate_topic:241:copytree | mechanism=copy_or_move | target=legacy_dest
scripts/migrate_legacy_topics.py:migrate_topic:247:write_text | mechanism=direct_path_write | target=runtime_dir / 'log.md'
scripts/migrate_legacy_topics.py:migrate_topic:251:write_text | mechanism=direct_path_write | target=runtime_dir / 'index.md'
scripts/migrate_legacy_topics.py:main:311:write_text | mechanism=direct_path_write | target=manifest_path
~~~

All 40 direct mutations below `brain/` but outside `brain/v5/` are classified
here. This is an anti-drift boundary: their presence supports read/migration or
historical diagnostics only and does not make old candidate, stage, L3/L4,
promotion, or graph-write workflows release requirements.

### 4.6.5 Shared Storage Primitive (3)

~~~text
brain/v5/markdown.py:write_text_atomic:65:NamedTemporaryFile | mechanism=direct_open_write | target=str(p.parent)
brain/v5/markdown.py:write_text_atomic:74:replace | mechanism=rename_or_replace | target=p
brain/v5/query_index_locking.py:__enter__:88:open | mechanism=direct_open_write | target=self.path
~~~

### 4.6.6 Transient External IO (3)

~~~text
brain/v5/_compat_shards/source_assets/part_02.py:_fetch_pdf_to_temp:266:NamedTemporaryFile | mechanism=direct_open_write | target=tmp_dir
brain/v5/_compat_shards/source_assets/part_02.py:_fetch_pdf_to_temp:273:copyfile | mechanism=copy_or_move | target=tmp_path
brain/v5/_compat_shards/source_assets/part_02.py:_download_pdf_to_temp:313:open | mechanism=direct_open_write | target=tmp_path
~~~

Direct mutation accounting totals 173 with no unclassified row. The three
transient rows may create only temporary acquisition files; the final blob move
and its typed metadata/receipt have separate ownership. Host/maintenance and
derived rows remain outside canonical trust, while migration or archived legacy
rows remain outside normal production research writes.

### 4.7 Current Verification

- `runtime_audit.py`: 496 lines;
- focused `writer_scan.py`: 496 lines;
- final M1 foundation lane: 186 passed, 1 skipped;
- exact capability/family and writer/direct-mutation classification tests:
  2 passed;
- current direct-mutation classification: 173 of 173 rows, no duplicate or
  unclassified signature;
- current named-helper classification: 161 of 161 rows; the preserved M0
  lower-bound baseline was 111;
- production-tree probe: no filesystem import aliases, dynamic open modes, or
  SQL execute calls were found;
- `writer_scan_policy.bounded_coverage_complete`: true for 716/716 declared
  production Python files with zero parse errors;
- `writer_scan_policy.coverage_complete`: false, because absence of arbitrary
  dynamic, reflected, custom, or native mutation helpers is not statically
  proven;
- M0.5 compact-import snapshot: 237 `brain.v5` modules, including 41 legacy-named
  modules; both `runtime_audit` and `writer_scan` are loaded even though they
  are maintenance-only;
- M0 staged patch hash remains
  `067d20e97571822538833aacdf7c5bfbcaaa5713`;
- protected user-diff hashes remain unchanged;
- no real canonical record was read for mutation or written by this work.

This evidence accepts the current CR0 inventory implementation, not the
compatibility policy or any compact/API deletion.

## 5. Real-Data Pressure

- generation 11/schema v2: 9,850 records, malformed 0, fresh;
- canonical watermark:
  `cd83cdad3f14cab0a822ae4f42066299bd789cc6b7be1535e59757bcba812452`;
- the 9,850-file canonical before/after rebuild snapshots are byte-identical
  with SHA-256
  `247912fcebb9f8b331cce07ad688898664e57979416de92fbc66e019121acf59`;
- 34 populated and 12 zero-record families;
- 2,356 legacy memory entries from 248 unique source packets;
- 2,108 duplicate legacy memory rows;
- all 2,356 entries remain `legacy_seed` with
  `legacy_migration_review_required`;
- canonical records mention only 11 registered MCP names;
- broader workspace scan found 27 AITP tool spellings but encountered two
  inaccessible temporary paths.

These observations support reduction and derived deduplication, but they do not
authorize canonical deletion or prove that an unmentioned capability has no
external caller.

## 6. Resolved Review Decisions

1. Policy A is selected: one-release soft deprecation removes six maintenance
   tools from compact while preserving full MCP/CLI compatibility.
2. The 59 core capabilities remain the current kernel/trust-boundary set; this
   is a retention decision, not permission to load every operation in compact.
3. `goal_continuation_*` remains host maintenance rather than canonical
   research memory.
4. The four zero-record `unimplemented_layout` families remain readable
   compatibility registrations but are frozen from new writes and enter the
   soft-deprecation candidate set.
5. `harness_feedback_seed_bundle` is postponed. It is not automatically
   replaced by, merged with, or allowed to modify the protected problem-dossier
   extension.

## 7. Vertical Retention Disposition

The exact classification lists in sections 2-4 are the item-level inventory.
Their reviewed dispositions are:

- retain all 59 core capabilities as kernel/trust contracts;
- retain all 43 maintenance capabilities on full/CLI surfaces, with six
  maintenance tools soft-deprecated from compact for one release;
- retain all 43 migration capabilities only in explicit read/audit/migration
  lanes;
- 77 retained vertical extensions stay at their current full-surface
  fixture/vertical contract, without treating fixture coverage as real
  scientific acceptance;
- postpone the 12 entries below: keep compatibility, add no new behavior, and
  require a later real vertical or independent review before expansion;
- delete no public capability during the one-release compatibility window.

### 7.1 Postponed Vertical Extensions (12)

```text
context_profile_draft
context_profile_templates
harness_feedback_seed_bundle
host_agnostic_moment_policy
interaction_recording_preview
interaction_recording_worklist
lane_exemplar_manifest
qsgw_cockpit_compact
record_final_output_profile
record_lane_exemplar
record_toy_numeric_finite_size_exemplar
research_cockpit_compact
```

For record families, retain the 25 core, 37 vertical, and four migration
registrations under their existing write/read policies. New vertical families
remain owned by their M3/M4 acceptance journeys; four zero-record
unimplemented-layout families remain soft-deprecation candidates.
All 161 helper-writer and 173 direct-mutation rows retain the ownership classes
in section 4. Migration/archived rows do not re-enter production, and bounded
scanner closure does not convert candidate counts into a no-bypass proof.
