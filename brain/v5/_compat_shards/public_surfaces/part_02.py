# Compatibility shard 2 for public_surfaces.
from __future__ import annotations

def _validators() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    from brain.v5.active_claim_focus_contracts import (
        require_valid_active_claim_focus_reconciliation,
        require_valid_active_claim_rebind_confirmation,
        require_valid_active_claim_rebind_proposal,
    )
    from brain.v5.contracts import (
        require_valid_adapter_packet,
        require_valid_adapter_protocol_registry,
        require_valid_artifact_record,
        require_valid_authority_record,
        require_valid_authority_registry,
        require_valid_claim_status_record,
        require_valid_claim_relation_map,
        require_valid_claim_trust_audit,
        require_valid_codex_hook_bridge,
        require_valid_code_state_record,
        require_valid_domain_pack_catalog,
        require_valid_domain_skill_shim_manifest,
        require_valid_evidence_record,
        require_valid_lifecycle_event_record,
        require_valid_execution_brief,
        require_valid_exploratory_record,
        require_valid_failure_mode_audit,
        require_valid_failure_mode_review_packet,
        require_valid_failure_mode_review_result_record,
        require_valid_final_engineering_readiness_audit,
        require_valid_human_checkpoint_record,
        require_valid_knowledge_connector_binding_registry,
        require_valid_knowledge_connector_catalog,
        require_valid_l2_memory_audit,
        require_valid_memory_entry_record,
        require_valid_object_relation_record,
        require_valid_physics_object_record,
        require_valid_process_graph_slice,
        require_valid_promotion_packet_record,
        require_valid_proof_obligation_record,
        require_valid_record_gate_coverage_audit,
        require_valid_record_ref_lookup,
        require_valid_reference_location_record,
        require_valid_research_route_record,
        require_valid_research_run_event_record,
        require_valid_research_run_record,
        require_valid_runtime_bridge_target_manifest,
        require_valid_runtime_mcp_bridge_acceptance,
        require_valid_runtime_hook_installation_audit,
        require_valid_runtime_hook_installation_paths,
        require_valid_runtime_hook_smoke_coverage,
        require_valid_sensemaking_report_record,
        require_valid_source_asset_record,
        require_valid_session_summary_bundle,
        require_valid_source_reconstruction_audit,
        require_valid_summary_orientation,
        require_valid_tool_executor_catalog,
        require_valid_tool_recipe_record,
        require_valid_tool_run_record,
        require_valid_trust_update_record,
        require_valid_trust_update_apply,
        require_valid_trust_update_preflight,
        require_valid_validation_contract_record,
        require_valid_validation_result_record,
        require_valid_workspace_summary_bundle,
        require_valid_workspace_replay_packet,
    )
    from brain.v5.research_state_contracts import (
        require_valid_bounded_numerical_evidence_bundle,
        require_valid_research_event_classification,
    )
    from brain.v5.research_timeline_contracts import require_valid_research_timeline
    from brain.v5.research_intent_contracts import (
        require_valid_research_intent_packet,
        require_valid_steering_decision_record,
    )
    from brain.v5.run_iteration_contracts import require_valid_run_iteration_record
    from brain.v5.output_stability_contracts import require_valid_final_output_profile
    from brain.v5.operator_checkpoint_contracts import require_valid_operator_checkpoint_record
    from brain.v5.strategy_memory_contracts import require_valid_strategy_memory_record
    from brain.v5.topic_status_contracts import require_valid_topic_status_bundle
    from brain.v5.legacy_contracts import require_valid_legacy_migration_result
    from brain.v5.legacy_executable_evidence_contracts import require_valid_legacy_executable_evidence_packet
    from brain.v5.legacy_human_checkpoint_obsidian_contracts import require_valid_legacy_human_checkpoint_obsidian_view_bundle
    from brain.v5.legacy_human_checkpoint_packet_contracts import require_valid_legacy_human_checkpoint_packet
    from brain.v5.legacy_topic_question_backfill_contracts import require_valid_legacy_topic_question_backfill_packet
    from brain.v5.legacy_l2_graph_contracts import require_valid_legacy_l2_graph_manifest
    from brain.v5.legacy_l2_seed_audit_contracts import require_valid_canonical_legacy_l2_seed_audit
    from brain.v5.legacy_l2_seed_review_worklist_contracts import (
        require_valid_canonical_legacy_l2_seed_review_worklist,
        require_valid_legacy_l2_seed_group_review_result_record,
    )
    from brain.v5.legacy_l2_obsidian_contracts import require_valid_legacy_l2_obsidian_view_bundle
    from brain.v5.legacy_l2_typed_migration_contracts import require_valid_legacy_l2_typed_migration_packet
    from brain.v5.legacy_migration_audit_contracts import require_valid_legacy_migration_coverage_audit
    from brain.v5.legacy_runtime_log_audit_contracts import require_valid_legacy_runtime_log_marker_audit
    from brain.v5.legacy_source_metadata_repair_contracts import require_valid_legacy_source_metadata_repair_packet
    from brain.v5.legacy_source_reconstruction_contracts import (
        require_valid_legacy_source_reconstruction_apply,
        require_valid_legacy_source_reconstruction_manifest,
        require_valid_legacy_source_reconstruction_plan,
        require_valid_legacy_source_reconstruction_review_packet,
    )
    from brain.v5.legacy_source_reconstruction_obsidian_contracts import require_valid_legacy_source_reconstruction_obsidian_view_bundle
    from brain.v5.source_reconstruction_contracts import (
        require_valid_source_reconstruction_manifest,
        require_valid_source_reconstruction_review_manifest,
        require_valid_source_reconstruction_review_packet,
        require_valid_source_reconstruction_review_result_record,
        require_valid_source_stack_coverage_manifest,
    )
    from brain.v5.source_reconstruction_obsidian_contracts import require_valid_source_reconstruction_obsidian_view_bundle
    from brain.v5.legacy_semantic_review_contracts import (
        require_valid_legacy_semantic_review_manifest,
        require_valid_legacy_semantic_review_packet,
        require_valid_legacy_semantic_repair_apply,
        require_valid_legacy_semantic_repair_plan,
        require_valid_legacy_semantic_review_queue,
        require_valid_legacy_semantic_review_result_record,
    )
    from brain.v5.legacy_semantic_repair_manifest_contracts import require_valid_legacy_semantic_repair_manifest
    from brain.v5.legacy_semantic_needs_revision_packet_contracts import require_valid_legacy_semantic_needs_revision_basis_packet
    from brain.v5.legacy_semantic_needs_revision_contracts import require_valid_legacy_semantic_needs_revision_basis_queue
    from brain.v5.legacy_semantic_needs_revision_obsidian_contracts import require_valid_legacy_semantic_needs_revision_basis_obsidian_view_bundle
    from brain.v5.legacy_semantic_worklist_contracts import require_valid_legacy_semantic_review_worklist
    from brain.v5.legacy_semantic_review_obsidian_contracts import require_valid_legacy_semantic_review_obsidian_view_bundle
    from brain.v5.host_readiness_contracts import (
        require_valid_runtime_host_production_loop_audit,
        require_valid_runtime_host_readiness_audit,
    )
    from brain.v5.host_lifecycle_contracts import require_valid_runtime_host_lifecycle_audit
    from brain.v5.runtime_payload_profile_contracts import require_valid_runtime_payload_profiles
    from brain.v5.curated_rag_contracts import (
        require_valid_curated_rag_chunk,
        require_valid_curated_rag_corpus,
        require_valid_curated_rag_ingest_result,
        require_valid_curated_rag_promotion_draft,
        require_valid_curated_rag_search_result,
    )
    from brain.v5.interaction_preview_contracts import require_valid_interaction_recording_preview
    from brain.v5.interaction_worklist_contracts import require_valid_interaction_recording_worklist
    from brain.v5.workspace_interaction_preview_contracts import require_valid_workspace_interaction_preview_bundle
    from brain.v5.vnext_readiness_contracts import require_valid_vnext_readiness_manifest
    from brain.v5.literature_intake_contracts import (
        require_valid_literature_intake_record_result,
        require_valid_literature_intake_suggestion,
    )
    from brain.v5.literature_comparison_draft_contracts import (
        require_valid_literature_comparison_draft,
    )
    from brain.v5.literature_corpus_extraction_artifact_contracts import (
        require_valid_literature_corpus_extraction_artifact,
    )
    from brain.v5.literature_extraction_report_contracts import (
        require_valid_literature_extraction_report,
    )
    from brain.v5.literature_source_extraction_contracts import (
        require_valid_literature_source_extraction_candidates,
    )
    from brain.v5.literature_reading_route_contracts import (
        require_valid_literature_reading_route,
    )
    from brain.v5.literature_source_set_readiness_contracts import (
        require_valid_literature_source_set_readiness,
    )
    from brain.v5.literature_source_review_handoff_contracts import (
        require_valid_literature_source_review_handoff,
    )
    from brain.v5.context_profile_template_contracts import (
        require_valid_context_profile_template_catalog,
    )
    from brain.v5.context_profile_draft_contracts import (
        require_valid_context_profile_draft,
    )
    from brain.v5.lane_exemplar_contracts import (
        require_valid_lane_exemplar_manifest,
        require_valid_lane_exemplar_record,
    )
    from brain.v5.obsidian_view_contracts import require_valid_l2_obsidian_view_bundle
    from brain.v5.workspace_refresh_contracts import require_valid_workspace_refresh_bundle
    from brain.v5.workspace_file_migration_ledger_contracts import (
        require_valid_workspace_file_migration_ledger,
        require_valid_workspace_file_migration_ledger_progress,
    )
    from brain.v5.workspace_migration_health_contracts import require_valid_workspace_migration_health
    from brain.v5.workspace_old_store_import_contracts import require_valid_workspace_old_store_import_result
    from brain.v5.workspace_recovery_binding_repair_contracts import require_valid_workspace_recovery_binding_repair
    from brain.v5.workspace_recovery_audit_contracts import (
        require_valid_workspace_recovery_audit,
        require_valid_workspace_recovery_audit_progress,
    )
    from brain.v5.workspace_recording_audit_contracts import require_valid_workspace_recording_audit
    from brain.v5.qsgw_cockpit_contracts import require_valid_qsgw_cockpit_bundle
    from brain.v5.research_cockpit_contracts import require_valid_research_cockpit_bundle
    from brain.v5.moment_policy_contracts import require_valid_host_agnostic_moment_policy
    from brain.v5.goal_continuation_contracts import (
        require_valid_goal_continuation_list,
        require_valid_goal_continuation_packet,
    )
    from brain.v5.harness_feedback_contracts import (
        require_valid_harness_feedback_bundle,
        require_valid_monitor_snapshot_record,
        require_valid_run_dir_provenance_extractor_plan,
        require_valid_skill_patch_proposal_record,
    )
    from brain.v5.hpc_cockpit_contracts import require_valid_hpc_cockpit
    from brain.v5.lane_contracts_contracts import require_valid_lane_contract_record
    from brain.v5.context_pack_contracts import require_valid_aitp_context_pack
    from brain.v5.objective_graph_contracts import (
        require_valid_compact_execution_brief,
        require_valid_objective_graph,
    )
    from brain.v5.research_distillation_contracts import require_valid_research_distillation_candidates
    from brain.v5.note_outline_contracts import require_valid_note_outline
    from brain.v5.quiet_checkpoint_contracts import (
        require_valid_quiet_checkpoint_batch,
        require_valid_quiet_checkpoint_preview,
    )
    from brain.v5.hook_protocol_contracts import (
        require_valid_claude_code_hook_installation,
        require_valid_claude_code_hook_settings,
        require_valid_hook_trace_event_record,
        require_valid_opencode_plugin_bridge,
        require_valid_pre_tool_policy_decision,
    )
    from brain.v5.hook_kimi_contracts import (
        require_valid_kimi_code_hook_config,
        require_valid_kimi_code_hook_installation,
    )
    from brain.v5.hook_install_contracts import (
        require_valid_codex_hook_installation,
        require_valid_opencode_hook_installation,
    )
    from brain.v5.recording_navigator_contracts import (
        require_valid_recording_candidate_classification,
        require_valid_recording_effect_verification,
        require_valid_recording_navigation_state,
        require_valid_recording_slot_expansion,
    )
    from brain.v5.lightweight_record_router_contracts import (
        require_valid_lightweight_record_write_plan,
    )

    validators = {
        "active_claim_focus_reconciliation": require_valid_active_claim_focus_reconciliation,
        "active_claim_rebind_confirmation": require_valid_active_claim_rebind_confirmation,
        "active_claim_rebind_proposal": require_valid_active_claim_rebind_proposal,
        "adapter_packet": require_valid_adapter_packet,
        "adapter_protocol_registry": require_valid_adapter_protocol_registry,
        "aitp_context_pack": require_valid_aitp_context_pack,
        "artifact_record": require_valid_artifact_record,
        "authority_record": require_valid_authority_record,
        "authority_registry": require_valid_authority_registry,
        "bounded_numerical_evidence_bundle": require_valid_bounded_numerical_evidence_bundle,
        "claim_status_record": require_valid_claim_status_record,
        "claim_relation_map": require_valid_claim_relation_map,
        "claim_trust_audit": require_valid_claim_trust_audit,
        "claude_code_hook_installation": require_valid_claude_code_hook_installation,
        "claude_code_hook_settings": require_valid_claude_code_hook_settings,
        "codex_hook_bridge": require_valid_codex_hook_bridge,
        "codex_hook_installation": require_valid_codex_hook_installation,
        "code_state_record": require_valid_code_state_record,
        "compact_execution_brief": require_valid_compact_execution_brief,
        "context_profile_draft": require_valid_context_profile_draft,
        "context_profile_template_catalog": require_valid_context_profile_template_catalog,
        "curated_rag_chunk": require_valid_curated_rag_chunk,
        "curated_rag_corpus": require_valid_curated_rag_corpus,
        "curated_rag_ingest_result": require_valid_curated_rag_ingest_result,
        "curated_rag_promotion_draft": require_valid_curated_rag_promotion_draft,
        "curated_rag_search_result": require_valid_curated_rag_search_result,
        "domain_pack_catalog": require_valid_domain_pack_catalog,
        "domain_skill_shim_manifest": require_valid_domain_skill_shim_manifest,
        "evidence_record": require_valid_evidence_record,
        "lifecycle_event_record": require_valid_lifecycle_event_record,
        "lightweight_record_write_plan": require_valid_lightweight_record_write_plan,
        "execution_brief": require_valid_execution_brief,
        "exploratory_record": require_valid_exploratory_record,
        "failure_mode_audit": require_valid_failure_mode_audit,
        "failure_mode_review_packet": require_valid_failure_mode_review_packet,
        "failure_mode_review_result_record": require_valid_failure_mode_review_result_record,
        "final_engineering_readiness_audit": require_valid_final_engineering_readiness_audit,
        "final_output_profile": require_valid_final_output_profile,
        "harness_feedback_bundle": require_valid_harness_feedback_bundle,
        "human_checkpoint_record": require_valid_human_checkpoint_record,
        "hook_trace_event_record": require_valid_hook_trace_event_record,
        "interaction_recording_preview": require_valid_interaction_recording_preview,
        "interaction_recording_worklist": require_valid_interaction_recording_worklist,
        "workspace_interaction_preview_bundle": require_valid_workspace_interaction_preview_bundle,
        "literature_comparison_draft": require_valid_literature_comparison_draft,
        "literature_corpus_extraction_artifact": require_valid_literature_corpus_extraction_artifact,
        "literature_extraction_report": require_valid_literature_extraction_report,
        "literature_intake_record_result": require_valid_literature_intake_record_result,
        "literature_intake_suggestion": require_valid_literature_intake_suggestion,
        "literature_reading_route": require_valid_literature_reading_route,
        "literature_source_extraction_candidates": require_valid_literature_source_extraction_candidates,
        "literature_source_set_readiness": require_valid_literature_source_set_readiness,
        "literature_source_review_handoff": require_valid_literature_source_review_handoff,
        "kimi_code_hook_config": require_valid_kimi_code_hook_config,
        "kimi_code_hook_installation": require_valid_kimi_code_hook_installation,
        "knowledge_connector_binding_registry": require_valid_knowledge_connector_binding_registry,
        "knowledge_connector_catalog": require_valid_knowledge_connector_catalog,
        "lane_exemplar_manifest": require_valid_lane_exemplar_manifest,
        "lane_exemplar_record": require_valid_lane_exemplar_record,
        "l2_obsidian_view_bundle": require_valid_l2_obsidian_view_bundle,
        "l2_memory_audit": require_valid_l2_memory_audit,
        "legacy_executable_evidence_packet": require_valid_legacy_executable_evidence_packet,
        "legacy_human_checkpoint_obsidian_view_bundle": require_valid_legacy_human_checkpoint_obsidian_view_bundle,
        "legacy_human_checkpoint_packet": require_valid_legacy_human_checkpoint_packet,
        "legacy_topic_question_backfill_packet": require_valid_legacy_topic_question_backfill_packet,
        "legacy_l2_graph_manifest": require_valid_legacy_l2_graph_manifest,
        "canonical_legacy_l2_seed_audit": require_valid_canonical_legacy_l2_seed_audit,
        "canonical_legacy_l2_seed_review_worklist": require_valid_canonical_legacy_l2_seed_review_worklist,
        "legacy_l2_seed_group_review_result_record": require_valid_legacy_l2_seed_group_review_result_record,
        "legacy_l2_obsidian_view_bundle": require_valid_legacy_l2_obsidian_view_bundle,
        "legacy_l2_typed_migration_packet": require_valid_legacy_l2_typed_migration_packet,
        "legacy_migration_coverage_audit": require_valid_legacy_migration_coverage_audit,
        "legacy_migration_result": require_valid_legacy_migration_result,
        "legacy_runtime_log_marker_audit": require_valid_legacy_runtime_log_marker_audit,
        "legacy_source_metadata_repair_packet": require_valid_legacy_source_metadata_repair_packet,
        "legacy_source_reconstruction_apply": require_valid_legacy_source_reconstruction_apply,
        "legacy_source_reconstruction_manifest": require_valid_legacy_source_reconstruction_manifest,
        "legacy_source_reconstruction_obsidian_view_bundle": require_valid_legacy_source_reconstruction_obsidian_view_bundle,
        "legacy_source_reconstruction_plan": require_valid_legacy_source_reconstruction_plan,
        "legacy_source_reconstruction_review_packet": require_valid_legacy_source_reconstruction_review_packet,
        "legacy_semantic_needs_revision_basis_obsidian_view_bundle": require_valid_legacy_semantic_needs_revision_basis_obsidian_view_bundle,
        "legacy_semantic_needs_revision_basis_packet": require_valid_legacy_semantic_needs_revision_basis_packet,
        "legacy_semantic_needs_revision_basis_queue": require_valid_legacy_semantic_needs_revision_basis_queue,
        "legacy_semantic_review_manifest": require_valid_legacy_semantic_review_manifest,
        "legacy_semantic_review_obsidian_view_bundle": require_valid_legacy_semantic_review_obsidian_view_bundle,
        "legacy_semantic_review_packet": require_valid_legacy_semantic_review_packet,
        "legacy_semantic_review_worklist": require_valid_legacy_semantic_review_worklist,
        "legacy_semantic_repair_apply": require_valid_legacy_semantic_repair_apply,
        "legacy_semantic_repair_manifest": require_valid_legacy_semantic_repair_manifest,
        "legacy_semantic_repair_plan": require_valid_legacy_semantic_repair_plan,
        "legacy_semantic_review_result_record": require_valid_legacy_semantic_review_result_record,
        "legacy_semantic_review_queue": require_valid_legacy_semantic_review_queue,
        "memory_entry_record": require_valid_memory_entry_record,
        "monitor_snapshot_record": require_valid_monitor_snapshot_record,
        "note_outline": require_valid_note_outline,
        "objective_graph": require_valid_objective_graph,
        "object_relation_record": require_valid_object_relation_record,
        "operator_checkpoint_record": require_valid_operator_checkpoint_record,
        "opencode_hook_installation": require_valid_opencode_hook_installation,
        "opencode_plugin_bridge": require_valid_opencode_plugin_bridge,
        "host_agnostic_moment_policy": require_valid_host_agnostic_moment_policy,
        "physics_object_record": require_valid_physics_object_record,
        "pre_tool_policy_decision": require_valid_pre_tool_policy_decision,
        "process_graph_slice": require_valid_process_graph_slice,
        "promotion_packet_record": require_valid_promotion_packet_record,
        "proof_obligation_record": require_valid_proof_obligation_record,
        "quiet_checkpoint_batch": require_valid_quiet_checkpoint_batch,
        "quiet_checkpoint_preview": require_valid_quiet_checkpoint_preview,
        "qsgw_cockpit_bundle": require_valid_qsgw_cockpit_bundle,
        "record_gate_coverage_audit": require_valid_record_gate_coverage_audit,
        "recording_candidate_classification": require_valid_recording_candidate_classification,
        "recording_effect_verification": require_valid_recording_effect_verification,
        "recording_navigation_state": require_valid_recording_navigation_state,
        "recording_slot_expansion": require_valid_recording_slot_expansion,
        "record_ref_lookup": require_valid_record_ref_lookup,
        "reference_location_record": require_valid_reference_location_record,
        "research_route_record": require_valid_research_route_record,
        "research_run_event_record": require_valid_research_run_event_record,
        "research_run_record": require_valid_research_run_record,
        "run_dir_provenance_extractor_plan": require_valid_run_dir_provenance_extractor_plan,
        "research_event_classification": require_valid_research_event_classification,
        "research_cockpit_bundle": require_valid_research_cockpit_bundle,
        "research_distillation_candidates": require_valid_research_distillation_candidates,
        "research_intent_packet": require_valid_research_intent_packet,
        "research_timeline": require_valid_research_timeline,
        "run_iteration_record": require_valid_run_iteration_record,
        "runtime_hook_installation_audit": require_valid_runtime_hook_installation_audit,
        "runtime_host_lifecycle_audit": require_valid_runtime_host_lifecycle_audit,
        "runtime_host_production_loop_audit": require_valid_runtime_host_production_loop_audit,
        "runtime_host_readiness_audit": require_valid_runtime_host_readiness_audit,
        "runtime_bridge_target_manifest": require_valid_runtime_bridge_target_manifest,
        "runtime_mcp_bridge_acceptance": require_valid_runtime_mcp_bridge_acceptance,
        "runtime_payload_profiles": require_valid_runtime_payload_profiles,
        "runtime_hook_installation_paths": require_valid_runtime_hook_installation_paths,
        "runtime_hook_smoke_coverage": require_valid_runtime_hook_smoke_coverage,
        "sensemaking_report_record": require_valid_sensemaking_report_record,
        "session_summary_bundle": require_valid_session_summary_bundle,
        "skill_patch_proposal_record": require_valid_skill_patch_proposal_record,
        "source_reconstruction_audit": require_valid_source_reconstruction_audit,
        "source_asset_record": require_valid_source_asset_record,
        "source_stack_coverage_manifest": require_valid_source_stack_coverage_manifest,
        "source_reconstruction_manifest": require_valid_source_reconstruction_manifest,
        "source_reconstruction_obsidian_view_bundle": require_valid_source_reconstruction_obsidian_view_bundle,
        "source_reconstruction_review_manifest": require_valid_source_reconstruction_review_manifest,
        "source_reconstruction_review_packet": require_valid_source_reconstruction_review_packet,
        "source_reconstruction_review_result_record": require_valid_source_reconstruction_review_result_record,
        "steering_decision_record": require_valid_steering_decision_record,
        "strategy_memory_record": require_valid_strategy_memory_record,
        "summary_orientation": require_valid_summary_orientation,
        "tool_executor_catalog": require_valid_tool_executor_catalog,
        "topic_status_bundle": require_valid_topic_status_bundle,
        "tool_recipe_record": require_valid_tool_recipe_record,
        "tool_run_record": require_valid_tool_run_record,
        "trust_update_record": require_valid_trust_update_record,
        "trust_update_apply": require_valid_trust_update_apply,
        "trust_update_preflight": require_valid_trust_update_preflight,
        "validation_contract_record": require_valid_validation_contract_record,
        "validation_result_record": require_valid_validation_result_record,
        "vnext_readiness_manifest": require_valid_vnext_readiness_manifest,
        "workspace_summary_bundle": require_valid_workspace_summary_bundle,
        "workspace_replay_packet": require_valid_workspace_replay_packet,
        "workspace_refresh_bundle": require_valid_workspace_refresh_bundle,
        "workspace_file_migration_ledger": require_valid_workspace_file_migration_ledger,
        "workspace_file_migration_ledger_progress": require_valid_workspace_file_migration_ledger_progress,
        "workspace_migration_health": require_valid_workspace_migration_health,
        "workspace_old_store_import_result": require_valid_workspace_old_store_import_result,
        "workspace_recovery_binding_repair": require_valid_workspace_recovery_binding_repair,
        "workspace_recovery_audit": require_valid_workspace_recovery_audit,
        "workspace_recovery_audit_progress": require_valid_workspace_recovery_audit_progress,
        "workspace_recording_audit": require_valid_workspace_recording_audit,
        "goal_continuation_packet": require_valid_goal_continuation_packet,
        "goal_continuation_list": require_valid_goal_continuation_list,
        "lane_contract_record": require_valid_lane_contract_record,
        "hpc_cockpit": require_valid_hpc_cockpit,
    }
    from brain.v5.capability_surface_contracts import capability_surface_validators

    validators.update(capability_surface_validators())
    return validators
