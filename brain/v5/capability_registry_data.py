"""Static classifications used by the AITP runtime capability registry."""

from __future__ import annotations


READ_ONLY_OPERATIONS = frozenset(
    """
active_claim_focus_reconciliation
active_claim_rebind_proposal
adapter_packet
adapter_pre_tool_event
adapter_registry
aitp_context_pack
audit_claim_trust
audit_failure_mode_coverage
audit_l2_memory_context
build_failure_mode_review_packet
canonical_legacy_l2_seed_audit
canonical_legacy_l2_seed_review_worklist
claim_relation_map
compact_execution_brief
context_profile_draft
context_profile_templates
curated_rag_chunk
curated_rag_corpus
curated_rag_promotion_draft
curated_rag_search
execution_brief
final_engineering_readiness_audit
get_trust_update_record
goal_continuation_latest
goal_continuation_list
host_agnostic_moment_policy
hpc_cockpit
interaction_recording_preview
interaction_recording_worklist
lane_exemplar_manifest
legacy_executable_evidence_packet
legacy_human_checkpoint_packet
legacy_l2_graph_manifest
legacy_l2_typed_migration_packet
legacy_migration_coverage_audit
legacy_runtime_log_marker_audit
legacy_semantic_needs_revision_basis_packet
legacy_semantic_needs_revision_basis_queue
legacy_semantic_repair_manifest
legacy_semantic_repair_plan
legacy_semantic_review_manifest
legacy_semantic_review_packet
legacy_semantic_review_queue
legacy_semantic_review_worklist
legacy_source_metadata_repair_packet
legacy_source_reconstruction_manifest
legacy_source_reconstruction_plan
legacy_source_reconstruction_review_packet
legacy_topic_question_backfill_packet
lightweight_record_write_plan
list_authorities
list_domain_packs
list_knowledge_connector_bindings
list_knowledge_connectors
list_tool_executors
literature_comparison_draft
literature_corpus_extraction_artifact
literature_extraction_report
literature_reading_route
literature_source_extraction_candidates
literature_source_review_handoff
literature_source_set_readiness
note_outline
objective_graph
pre_tool_policy
process_graph_slice
public_surfaces
quiet_checkpoint_preview
record_gate_coverage_audit
record_ref_lookup
recording_candidate_classification
recording_effect_verification
recording_navigation_state
recording_slot_expansion
research_distillation_candidates
research_event_classifier
research_timeline
runtime_bridge_target_manifest
runtime_hook_installation_audit
runtime_hook_installation_paths
runtime_hook_smoke_coverage
runtime_host_lifecycle_audit
runtime_host_production_loop_audit
runtime_host_readiness_audit
runtime_mcp_bridge_acceptance
runtime_payload_profiles
source_reconstruction_audit
source_reconstruction_manifest
source_reconstruction_review_manifest
source_reconstruction_review_packet
source_stack_coverage_manifest
suggest_domain_packs
suggest_literature_intake
summary_orientation
trust_preflight
vnext_readiness_manifest
workspace_file_migration_ledger
workspace_interaction_preview
workspace_migration_health
workspace_old_store_import_plan
workspace_recording_audit
workspace_recovery_audit
workspace_recovery_binding_repair
""".split()
)

RUNTIME_WRITE_OPERATIONS = frozenset(
    """
bind_knowledge_connector
claude_code_hook_installation
claude_code_hook_settings
codex_hook_bridge
codex_hook_installation
domain_skill_shims
goal_continuation_write
ingest_curated_rag_corpus
kimi_code_hook_config
kimi_code_hook_installation
l2_obsidian_view
legacy_human_checkpoint_obsidian_view
legacy_l2_obsidian_view
legacy_semantic_needs_revision_basis_obsidian_view
legacy_semantic_review_obsidian_view
legacy_source_reconstruction_obsidian_view
opencode_hook_installation
opencode_plugin_bridge
qsgw_cockpit
qsgw_cockpit_compact
research_cockpit
research_cockpit_compact
session_summary
source_reconstruction_obsidian_view
topic_status
topic_status_compact
workspace_refresh
workspace_replay
workspace_summary
write_legacy_migration_accounting_run
write_workspace_file_migration_ledger
write_workspace_recording_audit
write_workspace_recovery_audit
""".split()
)

KERNEL_WRITE_OPERATIONS = frozenset(
    """
acquire_arxiv_source_asset
acquire_pdf_source_asset
active_claim_rebind_confirmation
answer_operator_checkpoint
apply_promotion_packet
apply_workspace_old_store_import
apply_workspace_recovery_binding_repair
attach_artifact
attach_artifact_auto
capture_code_state_auto
capture_source_asset_auto
capture_tool_run_auto
create_promotion_packet
create_proof_obligation
create_validation_contract
decide_human_checkpoint
execute_tool
ingest_subagent_result
lane_contract_record
legacy_semantic_repair_apply
legacy_source_reconstruction_apply
materialize_steering_redirect
migrate_legacy_topic
persist_hook_trace_event
quiet_checkpoint_apply
record_authority
record_bounded_numerical_evidence
record_code_state
record_evidence
record_exploratory_record
record_failure_mode_review_result
record_final_output_profile
record_lane_exemplar
record_legacy_l2_seed_group_review_result
record_legacy_semantic_review_result
record_librpa_code_backed_algorithm_exemplar
record_literature_candidate
record_object_relation
record_physics_object
record_qft_qg_source_reconstruction_exemplar
record_reference_location
record_research_intent_packet
record_research_route
record_research_run_event
record_run_iteration
record_sensemaking_report
record_source_reconstruction_review_result
record_strategy_memory
record_tool_run
record_toy_numeric_finite_size_exemplar
record_validation_result
register_source
register_source_asset
register_tool_recipe
request_failure_mode_review_checkpoint
request_human_checkpoint
request_operator_checkpoint
start_research_run
supersede_record
trust_apply
update_claim_status
update_proof_obligation
update_research_run
""".split()
)

CODEX_FACADE_MCP_NAMES = (
    "aitp_v5_codex_tool_catalog",
    "aitp_v5_codex_autoroute",
    "aitp_v5_codex_enter",
    "aitp_v5_codex_expand",
    "aitp_v5_codex_recording_step",
    "aitp_v5_codex_record_apply",
    "aitp_v5_codex_literature_step",
    "aitp_v5_codex_closeout",
)

CODEX_SUPPORT_MCP_NAMES = (
    "aitp_v5_evaluate_pre_tool_policy",
    "aitp_v5_preflight_trust_update",
)

CODEX_MAINTENANCE_MCP_NAMES = (
    "aitp_v5_get_runtime_bridge_target_manifest",
    "aitp_v5_get_runtime_payload_profiles",
    "aitp_v5_audit_runtime_mcp_bridge_acceptance",
    "aitp_v5_audit_hook_installation",
    "aitp_v5_discover_hook_install_paths",
    "aitp_v5_report_hook_smoke_coverage",
)

CODEX_MAINTENANCE_CLI_ROUTES = {
    "aitp_v5_get_runtime_bridge_target_manifest": "aitp-v5 adapter bridge-targets",
    "aitp_v5_get_runtime_payload_profiles": "aitp-v5 adapter payload-profiles",
    "aitp_v5_audit_runtime_mcp_bridge_acceptance": "aitp-v5 adapter bridge-acceptance",
    "aitp_v5_audit_hook_installation": "aitp-v5 adapter install-audit <runtime> <args>",
    "aitp_v5_discover_hook_install_paths": "aitp-v5 adapter install-paths",
    "aitp_v5_report_hook_smoke_coverage": "aitp-v5 adapter smoke-coverage",
}

COMPACT_MCP_NAMES = frozenset(CODEX_FACADE_MCP_NAMES + CODEX_SUPPORT_MCP_NAMES)

COMPACT_SOFT_DEPRECATION_BY_MCP = {
    name: {
        "lifecycle_status": "soft_deprecated_from_compact",
        "compatibility_window": "one_release",
        "decision_date": "2026-07-12",
        "warning": (
            "This maintenance tool was removed from compact; use full MCP or CLI "
            "during the one-release compatibility window."
        ),
        "cli_route": CODEX_MAINTENANCE_CLI_ROUTES[name],
        "removal_condition": "after_vertical_acceptance_and_caller_review",
    }
    for name in CODEX_MAINTENANCE_MCP_NAMES
}

# operation, MCP name, CLI route, public surface, state effect, visibility
MCP_ONLY_CAPABILITIES = (
    ("apply_project_skill", "aitp_v5_apply_project_skill", None, "skill_patch_proposal_record", "kernel_write", "full"),
    ("apply_rehome_plan", "aitp_v5_apply_rehome_plan", None, "lifecycle_event_record", "kernel_write", "full"),
    ("assess_risk", "aitp_v5_assess_risk", None, "risk_assessment", "read_only", "full"),
    ("audit_record_routing", "aitp_v5_audit_record_routing", None, "record_routing_audit", "read_only", "full"),
    ("bind_session", "aitp_v5_bind_session", None, "session_binding_record", "kernel_write", "full"),
    ("harness_feedback_seed_bundle", "aitp_v5_build_harness_feedback_seed_bundle", None, "harness_feedback_bundle", "read_only", "full"),
    ("build_rehome_plan", "aitp_v5_build_rehome_plan", None, "record_rehome_plan", "read_only", "full"),
    ("codex_autoroute", "aitp_v5_codex_autoroute", None, "codex_auto_route_decision", "read_only", "compact"),
    ("codex_closeout", "aitp_v5_codex_closeout", None, "codex_closeout", "kernel_write", "compact"),
    ("codex_enter", "aitp_v5_codex_enter", None, "codex_entry_context", "read_only", "compact"),
    ("codex_expand", "aitp_v5_codex_expand", None, "codex_context_expansion", "read_only", "compact"),
    ("codex_literature_step", "aitp_v5_codex_literature_step", None, "codex_literature_step", "kernel_write", "compact"),
    ("codex_record_apply", "aitp_v5_codex_record_apply", None, "codex_record_apply", "kernel_write", "compact"),
    ("codex_recording_step", "aitp_v5_codex_recording_step", None, "codex_recording_step", "read_only", "compact"),
    ("codex_tool_catalog", "aitp_v5_codex_tool_catalog", None, "codex_mcp_surface_catalog", "read_only", "compact"),
    ("create_claim", "aitp_v5_create_claim", None, "claim_record", "kernel_write", "full"),
    ("create_topic", "aitp_v5_create_topic", None, "topic_record", "kernel_write", "full"),
    ("init_workspace", "aitp_v5_init_workspace", "aitp-v5 init <base>", "workspace_initialization", "kernel_write", "full"),
    ("curated_legacy_topics", "aitp_v5_list_curated_legacy_topics", None, "curated_legacy_topic_catalog", "read_only", "full"),
    ("migrate_curated_legacy_topic", "aitp_v5_migrate_curated_legacy_topic_to_v5", None, "legacy_migration_result", "kernel_write", "full"),
    ("run_dir_provenance_extractor_plan", "aitp_v5_plan_run_dir_provenance_extractor", None, "run_dir_provenance_extractor_plan", "read_only", "full"),
    ("capability_registry", "aitp_v5_get_capability_registry", "aitp-v5 context capability-audit", "capability_registry_audit", "read_only", "full"),
    ("runtime_capability_audit", "aitp_v5_get_runtime_capability_audit", "aitp-v5 context runtime-audit", "runtime_capability_audit", "read_only", "full"),
    ("query_index_build", "aitp_v5_build_query_index", "aitp-v5 query index-build", "query_index_build_report", "runtime_write", "full"),
    ("query_index_status", "aitp_v5_get_query_index_status", "aitp-v5 query index-status", "query_index_status", "read_only", "full"),
    ("exact_record_expansion", "aitp_v5_exact_expand_records", "aitp-v5 query exact --ref claim:c1", "research_retrieval_result", "read_only", "full"),
    ("research_context_compile", "aitp_v5_compile_research_context", "aitp-v5 context compile <session-id>", "research_context_bundle", "read_only", "full"),
    ("propose_detected_procedural_skill", "aitp_v5_propose_detected_procedural_skill", None, "skill_patch_proposal_record", "kernel_write", "full"),
    ("request_skill_install_review", "aitp_v5_request_skill_install_review", None, "human_checkpoint_record", "kernel_write", "full"),
)

# Independently shipped extensions are registered only when their MCP wrapper
# is present in the active runtime.
OPTIONAL_MCP_CAPABILITIES = (
    ("harness_feedback_problem_dossier", "aitp_v5_build_harness_feedback_problem_dossier", None, "harness_feedback_problem_dossier", "read_only", "full"),
)

# host operation, runtime entrypoint key, role, existing bridge state effect
BRIDGE_TARGET_SPECS = (
    ("readProcessGraphSlice", "process_graph_slice", "read", "read_only"),
    ("readMomentPolicy", "host_agnostic_moment_policy", "read", "read_only"),
    ("readRuntimePayloadProfiles", "runtime_payload_profiles", "read", "read_only"),
    ("readWorkspaceRecordingAudit", "workspace_recording_audit", "read", "read_only"),
    ("classifyRecordingCandidate", "recording_candidate_classification", "read", "read_only"),
    ("readRecordingNavigationState", "recording_navigation_state", "read", "read_only"),
    ("expandRecordingSlot", "recording_slot_expansion", "read", "read_only"),
    ("verifyRecordingEffect", "recording_effect_verification", "read", "read_only"),
    ("lookupRecordRefs", "record_ref_lookup", "read", "read_only"),
    ("readCuratedRagCorpus", "curated_rag_corpus", "read", "read_only"),
    ("searchCuratedRagCorpus", "curated_rag_search", "read", "read_only"),
    ("readCuratedRagChunk", "curated_rag_chunk", "read", "read_only"),
    ("draftCuratedRagPromotion", "curated_rag_promotion_draft", "read", "read_only"),
    ("readLiteratureSourceReviewHandoff", "literature_source_review_handoff", "read", "read_only"),
    ("readLiteratureComparisonDraft", "literature_comparison_draft", "read", "read_only"),
    ("readLiteratureReadingRoute", "literature_reading_route", "read", "read_only"),
    ("readLiteratureSourceExtractionCandidates", "literature_source_extraction_candidates", "read", "read_only"),
    ("readLiteratureExtractionReport", "literature_extraction_report", "read", "read_only"),
    ("readLiteratureCorpusExtractionArtifact", "literature_corpus_extraction_artifact", "read", "read_only"),
    ("readLiteratureSourceSetReadiness", "literature_source_set_readiness", "read", "read_only"),
    ("readContextProfileTemplates", "context_profile_templates", "read", "read_only"),
    ("readContextProfileDraft", "context_profile_draft", "read", "read_only"),
    ("materializeDomainSkillShims", "domain_skill_shims", "write", "project_skill_shim_write"),
    ("ingestCuratedRagCorpus", "ingest_curated_rag_corpus", "write", "curated_rag_manifest_write"),
    ("startResearchRun", "start_research_run", "write", "typed_record_write"),
    ("updateResearchRun", "update_research_run", "write", "typed_record_write"),
    ("recordResearchRunEvent", "record_research_run_event", "write", "typed_record_write"),
    ("recordExploratoryRecord", "record_exploratory_record", "write", "typed_record_write"),
    ("registerSourceAsset", "register_source_asset", "write", "typed_record_write"),
    ("captureSourceAssetAuto", "capture_source_asset_auto", "write", "typed_record_write"),
    ("recordEvidence", "record_evidence", "write", "typed_record_write"),
    ("recordToolRun", "record_tool_run", "write", "typed_record_write"),
    ("captureToolRunAuto", "capture_tool_run_auto", "write", "typed_record_write"),
    ("captureCodeStateAuto", "capture_code_state_auto", "write", "typed_record_write"),
    ("attachArtifact", "attach_artifact", "write", "typed_record_write"),
    ("attachArtifactAuto", "attach_artifact_auto", "write", "typed_record_write"),
    ("recordReferenceLocation", "record_reference_location", "write", "typed_record_write"),
    ("createProofObligation", "create_proof_obligation", "write", "typed_record_write"),
    ("createValidationContract", "create_validation_contract", "write", "typed_record_write"),
    ("recordValidationResult", "record_validation_result", "write", "typed_record_write"),
    ("recordSourceReconstructionReviewResult", "record_source_reconstruction_review_result", "write", "typed_record_write"),
    ("requestHumanCheckpoint", "request_human_checkpoint", "write", "typed_record_write"),
    ("preflightTrustUpdate", "trust_preflight", "preflight", "preflight_only"),
)
