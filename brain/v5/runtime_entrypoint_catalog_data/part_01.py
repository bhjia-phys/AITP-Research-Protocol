"""Runtime entrypoint catalog part 1."""

from __future__ import annotations

RUNTIME_ENTRYPOINTS_01 = {
    'public_surfaces': {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    },
    'adapter_registry': {
        "cli": "aitp-v5 adapter registry",
        "mcp": "aitp_v5_get_adapter_protocol_registry",
        "surface": "adapter_protocol_registry",
    },
    'runtime_bridge_target_manifest': {
        "cli": "aitp-v5 adapter bridge-targets",
        "mcp": "aitp_v5_get_runtime_bridge_target_manifest",
        "surface": "runtime_bridge_target_manifest",
    },
    'runtime_mcp_bridge_acceptance': {
        "cli": "aitp-v5 adapter bridge-acceptance",
        "mcp": "aitp_v5_audit_runtime_mcp_bridge_acceptance",
        "surface": "runtime_mcp_bridge_acceptance",
    },
    'runtime_payload_profiles': {
        "cli": "aitp-v5 adapter payload-profiles",
        "mcp": "aitp_v5_get_runtime_payload_profiles",
        "surface": "runtime_payload_profiles",
    },
    'record_ref_lookup': {
        "cli": "aitp-v5 adapter record-ref-lookup <args>",
        "mcp": "aitp_v5_lookup_record_refs",
        "surface": "record_ref_lookup",
    },
    'curated_rag_corpus': {
        "cli": "aitp-v5 adapter curated-rag-corpus",
        "mcp": "aitp_v5_get_curated_rag_corpus",
        "surface": "curated_rag_corpus",
    },
    'curated_rag_search': {
        "cli": "aitp-v5 adapter curated-rag-search <query> <args>",
        "mcp": "aitp_v5_search_curated_rag_corpus",
        "surface": "curated_rag_search_result",
    },
    'curated_rag_chunk': {
        "cli": "aitp-v5 adapter curated-rag-chunk <chunk-id>",
        "mcp": "aitp_v5_get_curated_rag_chunk",
        "surface": "curated_rag_chunk",
    },
    'curated_rag_promotion_draft': {
        "cli": "aitp-v5 adapter curated-rag-promotion-draft <chunk-id> <args>",
        "mcp": "aitp_v5_draft_curated_rag_promotion",
        "surface": "curated_rag_promotion_draft",
    },
    'ingest_curated_rag_corpus': {
        "cli": "aitp-v5 curated-rag ingest <args>",
        "mcp": "aitp_v5_ingest_curated_rag_corpus",
        "surface": "curated_rag_ingest_result",
    },
    'record_gate_coverage_audit': {
        "cli": "aitp-v5 adapter record-gate-audit",
        "mcp": "aitp_v5_audit_record_gate_coverage",
        "surface": "record_gate_coverage_audit",
    },
    'runtime_hook_installation_audit': {
        "cli": "aitp-v5 adapter install-audit <runtime> <args>",
        "mcp": "aitp_v5_audit_hook_installation",
        "surface": "runtime_hook_installation_audit",
    },
    'runtime_host_lifecycle_audit': {"cli": "aitp-v5 adapter host-lifecycle <runtime>", "mcp": "aitp_v5_audit_runtime_host_lifecycle", "surface": "runtime_host_lifecycle_audit"},
    'runtime_host_readiness_audit': {"cli": "aitp-v5 adapter host-readiness <runtime>", "mcp": "aitp_v5_audit_runtime_host_readiness", "surface": "runtime_host_readiness_audit"},
    'runtime_hook_installation_paths': {
        "cli": "aitp-v5 adapter install-paths",
        "mcp": "aitp_v5_discover_hook_install_paths",
        "surface": "runtime_hook_installation_paths",
    },
    'runtime_hook_smoke_coverage': {"cli": "aitp-v5 adapter smoke-coverage", "mcp": "aitp_v5_report_hook_smoke_coverage", "surface": "runtime_hook_smoke_coverage"},
    'final_engineering_readiness_audit': {"cli": "aitp-v5 adapter final-readiness", "mcp": "aitp_v5_audit_final_engineering_readiness", "surface": "final_engineering_readiness_audit"},
    'vnext_readiness_manifest': {"cli": "aitp-v5 status vnext-readiness", "mcp": "aitp_v5_build_vnext_readiness_manifest", "surface": "vnext_readiness_manifest"},
    'adapter_packet': {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    'runtime_host_production_loop_audit': {
        "cli": "aitp-v5 adapter host-production-loop",
        "mcp": "aitp_v5_audit_priority_host_production_loops",
        "surface": "runtime_host_production_loop_audit",
    },
    'codex_hook_bridge': {"cli": "aitp-v5 adapter hook-bridge codex <session-id> <args>", "mcp": "aitp_v5_write_codex_hook_bridge", "surface": "codex_hook_bridge"},
    'codex_hook_installation': {"cli": "aitp-v5 adapter install-hooks codex <session-id> <args>", "mcp": "aitp_v5_install_codex_hook_fixture", "surface": "codex_hook_installation"},
    'opencode_plugin_bridge': {"cli": "aitp-v5 adapter hook-bridge opencode <session-id> <args>", "mcp": "aitp_v5_write_opencode_plugin_bridge", "surface": "opencode_plugin_bridge"},
    'opencode_hook_installation': {"cli": "aitp-v5 adapter install-hooks opencode <session-id> <args>", "mcp": "aitp_v5_install_opencode_hook_fixture", "surface": "opencode_hook_installation"},
    'claude_code_hook_settings': {"cli": "aitp-v5 adapter hook-settings claude-code <session-id> <args>", "mcp": "aitp_v5_write_claude_code_hook_settings", "surface": "claude_code_hook_settings"},
    'claude_code_hook_installation': {"cli": "aitp-v5 adapter install-hooks claude-code <session-id> <args>", "mcp": "aitp_v5_install_claude_code_hook_settings", "surface": "claude_code_hook_installation"},
    'kimi_code_hook_config': {"cli": "aitp-v5 adapter hook-settings kimi-code <session-id> <args>", "mcp": "aitp_v5_write_kimi_code_hook_config", "surface": "kimi_code_hook_config"},
    'kimi_code_hook_installation': {"cli": "aitp-v5 adapter install-hooks kimi-code <session-id> <args>", "mcp": "aitp_v5_install_kimi_code_hook_config", "surface": "kimi_code_hook_installation"},
    'adapter_pre_tool_event': {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
    },
    'execution_brief': {
        "cli": "aitp-v5 brief <session-id>",
        "mcp": "aitp_v5_get_execution_brief",
        "surface": "execution_brief",
    },
    'claim_relation_map': {
        "cli": "aitp-v5 relation-map <session-id>",
        "mcp": "aitp_v5_get_claim_relation_map",
        "surface": "claim_relation_map",
    },
    'research_timeline': {
        "cli": "aitp-v5 timeline <session-id>",
        "mcp": "aitp_v5_get_research_timeline",
        "surface": "research_timeline",
    },
    'active_claim_focus_reconciliation': {
        "cli": "aitp-v5 relation-map <session-id>",
        "mcp": "aitp_v5_detect_active_claim_focus_drift",
        "surface": "active_claim_focus_reconciliation",
    },
    'active_claim_rebind_proposal': {
        "cli": "aitp-v5 relation-map <session-id>",
        "mcp": "aitp_v5_propose_active_claim_rebind",
        "surface": "active_claim_rebind_proposal",
    },
    'active_claim_rebind_confirmation': {
        "cli": "aitp-v5 session bind <session-id> <args>",
        "mcp": "aitp_v5_confirm_active_claim_rebind",
        "surface": "active_claim_rebind_confirmation",
    },
    'process_graph_slice': {
        "cli": "aitp-v5 graph slice <session-id>",
        "mcp": "aitp_v5_get_process_graph_slice",
        "surface": "process_graph_slice",
    },
    'host_agnostic_moment_policy': {
        "cli": "aitp-v5 graph moment-policy <session-id>",
        "mcp": "aitp_v5_get_host_agnostic_moment_policy",
        "surface": "host_agnostic_moment_policy",
    },
    'recording_candidate_classification': {
        "cli": "aitp-v5 recording classify-candidate <args>",
        "mcp": "aitp_v5_classify_recording_candidate",
        "surface": "recording_candidate_classification",
    },
    'lightweight_record_write_plan': {
        "cli": "aitp-v5 recording plan-lightweight-write <args>",
        "mcp": "aitp_v5_plan_lightweight_record_write",
        "surface": "lightweight_record_write_plan",
    },
    'recording_navigation_state': {
        "cli": "aitp-v5 recording navigation-state <session-id>",
        "mcp": "aitp_v5_get_recording_navigation_state",
        "surface": "recording_navigation_state",
    },
    'recording_slot_expansion': {
        "cli": "aitp-v5 recording expand-slot <session-id> <args>",
        "mcp": "aitp_v5_expand_recording_slot",
        "surface": "recording_slot_expansion",
    },
    'recording_effect_verification': {
        "cli": "aitp-v5 recording verify-effect <session-id> <args>",
        "mcp": "aitp_v5_verify_recording_effect",
        "surface": "recording_effect_verification",
    },
    'record_exploratory_record': {
        "cli": "aitp-v5 exploration record <args>",
        "mcp": "aitp_v5_record_exploratory_record",
        "surface": "exploratory_record",
    },
    'register_source_asset': {
        "cli": "aitp-v5 asset register <args>",
        "mcp": "aitp_v5_register_source_asset",
        "surface": "source_asset_record",
    },
    'capture_source_asset_auto': {
        "cli": "aitp-v5 asset capture-auto <args>",
        "mcp": "aitp_v5_capture_source_asset_auto",
        "surface": "source_asset_record",
    },
    'acquire_pdf_source_asset': {
        "cli": "aitp-v5 asset acquire-pdf <args>",
        "mcp": "aitp_v5_acquire_pdf_source_asset",
        "surface": "source_asset_record",
    },
    'acquire_arxiv_source_asset': {
        "cli": "aitp-v5 asset acquire-arxiv <args>",
        "mcp": "aitp_v5_acquire_arxiv_source_asset",
        "surface": "source_asset_record",
    },
    'record_research_route': {
        "cli": "aitp-v5 route record <args>",
        "mcp": "aitp_v5_record_research_route",
        "surface": "research_route_record",
    },
    'interaction_recording_preview': {"cli": "aitp-v5 interaction preview <session-id>", "mcp": "aitp_v5_preview_interaction_recording", "surface": "interaction_recording_preview"},
    'workspace_interaction_preview': {
        "cli": "aitp-v5 interaction workspace-preview",
        "mcp": "aitp_v5_build_workspace_interaction_preview",
        "surface": "workspace_interaction_preview_bundle",
    },
    'interaction_recording_worklist': {
        "cli": "aitp-v5 interaction worklist",
        "mcp": "aitp_v5_build_interaction_recording_worklist",
        "surface": "interaction_recording_worklist",
    },
    'suggest_literature_intake': {
        "cli": "aitp-v5 literature suggest-intake <args>",
        "mcp": "aitp_v5_suggest_literature_intake",
        "surface": "literature_intake_suggestion",
    },
    'record_literature_candidate': {
        "cli": "aitp-v5 literature record-candidate <args>",
        "mcp": "aitp_v5_record_literature_candidate",
        "surface": "literature_intake_record_result",
    },
    'literature_source_review_handoff': {
        "cli": "aitp-v5 literature source-review-handoff <args>",
        "mcp": "aitp_v5_build_literature_source_review_handoff",
        "surface": "literature_source_review_handoff",
    },
    'literature_comparison_draft': {
        "cli": "aitp-v5 literature comparison-draft <args>",
        "mcp": "aitp_v5_build_literature_comparison_draft",
        "surface": "literature_comparison_draft",
    },
    'literature_reading_route': {
        "cli": "aitp-v5 literature reading-route <args>",
        "mcp": "aitp_v5_build_literature_reading_route",
        "surface": "literature_reading_route",
    },
    'literature_source_extraction_candidates': {
        "cli": "aitp-v5 literature source-extraction <args>",
        "mcp": "aitp_v5_build_literature_source_extraction_candidates",
        "surface": "literature_source_extraction_candidates",
    },
    'literature_extraction_report': {
        "cli": "aitp-v5 literature extraction-report <args>",
        "mcp": "aitp_v5_build_literature_extraction_report",
        "surface": "literature_extraction_report",
    },
    'literature_corpus_extraction_artifact': {
        "cli": "aitp-v5 literature corpus-extraction-artifact <args>",
        "mcp": "aitp_v5_build_literature_corpus_extraction_artifact",
        "surface": "literature_corpus_extraction_artifact",
    },
    'literature_source_set_readiness': {
        "cli": "aitp-v5 literature source-set-readiness <args>",
        "mcp": "aitp_v5_build_literature_source_set_readiness",
        "surface": "literature_source_set_readiness",
    },
    'record_final_output_profile': {
        "cli": "aitp-v5 output profile record <args>",
        "mcp": "aitp_v5_record_final_output_profile",
        "surface": "final_output_profile",
    },
    'request_operator_checkpoint': {
        "cli": "aitp-v5 operator checkpoint request <args>",
        "mcp": "aitp_v5_request_operator_checkpoint",
        "surface": "operator_checkpoint_record",
    },
    'answer_operator_checkpoint': {
        "cli": "aitp-v5 operator checkpoint answer <args>",
        "mcp": "aitp_v5_answer_operator_checkpoint",
        "surface": "operator_checkpoint_record",
    },
    'record_strategy_memory': {
        "cli": "aitp-v5 strategy memory record <args>",
        "mcp": "aitp_v5_record_strategy_memory",
        "surface": "strategy_memory_record",
    },
    'record_lane_exemplar': {
        "cli": "aitp-v5 exemplar lane record <args>",
        "mcp": "aitp_v5_record_lane_exemplar",
        "surface": "lane_exemplar_record",
    },
    'record_librpa_code_backed_algorithm_exemplar': {
        "cli": "aitp-v5 exemplar lane record-librpa-code <args>",
        "mcp": "aitp_v5_record_librpa_code_backed_algorithm_exemplar",
        "surface": "lane_exemplar_record",
    },
    'record_qft_qg_source_reconstruction_exemplar': {
        "cli": "aitp-v5 exemplar lane record-qft-qg-source <args>",
        "mcp": "aitp_v5_record_qft_qg_source_reconstruction_exemplar",
        "surface": "lane_exemplar_record",
    },
    'record_toy_numeric_finite_size_exemplar': {
        "cli": "aitp-v5 exemplar lane record-toy-numeric <args>",
        "mcp": "aitp_v5_record_toy_numeric_finite_size_exemplar",
        "surface": "lane_exemplar_record",
    },
    'lane_exemplar_manifest': {
        "cli": "aitp-v5 exemplar lane manifest",
        "mcp": "aitp_v5_build_lane_exemplar_manifest",
        "surface": "lane_exemplar_manifest",
    },
    'record_research_intent_packet': {
        "cli": "aitp-v5 intent packet record <args>",
        "mcp": "aitp_v5_record_research_intent_packet",
        "surface": "research_intent_packet",
    },
    'record_run_iteration': {
        "cli": "aitp-v5 run iteration record <args>",
        "mcp": "aitp_v5_record_run_iteration",
        "surface": "run_iteration_record",
    },
    'start_research_run': {
        "cli": "aitp-v5 run research start <args>",
        "mcp": "aitp_v5_start_research_run",
        "surface": "research_run_record",
    },
    'update_research_run': {
        "cli": "aitp-v5 run research update <args>",
        "mcp": "aitp_v5_update_research_run",
        "surface": "research_run_record",
    },
    'record_research_run_event': {
        "cli": "aitp-v5 run event record <args>",
        "mcp": "aitp_v5_record_research_run_event",
        "surface": "research_run_event_record",
    },
    'materialize_steering_redirect': {
        "cli": "aitp-v5 intent steering materialize <args>",
        "mcp": "aitp_v5_materialize_steering_redirect",
        "surface": "steering_decision_record",
    },
    'record_code_state': {
        "cli": "aitp-v5 code state record <args>",
        "mcp": "aitp_v5_record_code_state",
        "surface": "code_state_record",
    },
    'capture_code_state_auto': {
        "cli": "aitp-v5 code state auto <args>",
        "mcp": "aitp_v5_capture_code_state_auto",
        "surface": "code_state_record",
    },
    'record_evidence': {
        "cli": "aitp-v5 evidence record <args>",
        "mcp": "aitp_v5_record_evidence",
        "surface": "evidence_record",
    },
    'supersede_record': {
        "cli": "aitp-v5 record supersede <args>",
        "mcp": "aitp_v5_supersede_record",
        "surface": "lifecycle_event_record",
    },
    'register_source': {
        "cli": "aitp-v5 research-state register-source <args>",
        "mcp": "aitp_v5_register_source",
        "surface": "reference_location_record",
    },
    'attach_artifact': {
        "cli": "aitp-v5 research-state attach-artifact <args>",
        "mcp": "aitp_v5_attach_artifact",
        "surface": "artifact_record",
    },
    'attach_artifact_auto': {
        "cli": "aitp-v5 research-state attach-artifact-auto <args>",
        "mcp": "aitp_v5_attach_artifact_auto",
        "surface": "artifact_record",
    },
    'update_claim_status': {
        "cli": "aitp-v5 research-state update-claim-status <args>",
        "mcp": "aitp_v5_update_claim_status",
        "surface": "claim_status_record",
    },
    'create_proof_obligation': {
        "cli": "aitp-v5 research-state create-proof-obligation <args>",
        "mcp": "aitp_v5_create_proof_obligation",
        "surface": "proof_obligation_record",
    },
    'update_proof_obligation': {
        "cli": "aitp-v5 research-state update-proof-obligation <args>",
        "mcp": "aitp_v5_update_proof_obligation",
        "surface": "proof_obligation_record",
    },
    'research_event_classifier': {
        "cli": "aitp-v5 research-state classify-event <args>",
        "mcp": "aitp_v5_classify_research_event",
        "surface": "research_event_classification",
    },
    'record_bounded_numerical_evidence': {
        "cli": "aitp-v5 research-state bounded-evidence <args>",
        "mcp": "aitp_v5_record_bounded_numerical_evidence",
        "surface": "bounded_numerical_evidence_bundle",
    },
    'register_tool_recipe': {
        "cli": "aitp-v5 tool recipe register <args>",
        "mcp": "aitp_v5_register_tool_recipe",
        "surface": "tool_recipe_record",
    },
    'record_tool_run': {
        "cli": "aitp-v5 tool run record <args>",
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
    },
    'capture_tool_run_auto': {
        "cli": "aitp-v5 tool run capture-auto <args>",
        "mcp": "aitp_v5_capture_tool_run_auto",
        "surface": "tool_run_record",
    },
    'execute_tool': {
        "cli": "aitp-v5 tool execute <args>",
        "mcp": "aitp_v5_execute_tool",
        "surface": "tool_run_record",
    },
    'list_tool_executors': {
        "cli": "aitp-v5 tool executors",
        "mcp": "aitp_v5_list_tool_executors",
        "surface": "tool_executor_catalog",
    },
    'list_knowledge_connectors': {
        "cli": "aitp-v5 knowledge connectors",
        "mcp": "aitp_v5_list_knowledge_connectors",
        "surface": "knowledge_connector_catalog",
    },
    'list_knowledge_connector_bindings': {
        "cli": "aitp-v5 knowledge bindings",
        "mcp": "aitp_v5_list_knowledge_connector_bindings",
        "surface": "knowledge_connector_binding_registry",
    },
    'bind_knowledge_connector': {
        "cli": "aitp-v5 knowledge bind <args>",
        "mcp": "aitp_v5_bind_knowledge_connector",
        "surface": "knowledge_connector_binding_registry",
    },
    'list_domain_packs': {
        "cli": "aitp-v5 domain-pack catalog",
        "mcp": "aitp_v5_list_domain_packs",
        "surface": "domain_pack_catalog",
    },
    'suggest_domain_packs': {
        "cli": "aitp-v5 domain-pack suggest <args>",
        "mcp": "aitp_v5_suggest_domain_packs_for_claim",
        "surface": "domain_pack_catalog",
    },
    'domain_skill_shims': {
        "cli": "aitp-v5 domain-pack skill-shims <args>",
        "mcp": "aitp_v5_build_domain_skill_shim_manifest",
        "surface": "domain_skill_shim_manifest",
    },
    'source_reconstruction_audit': {
        "cli": "aitp-v5 source reconstruction-audit <args>",
        "mcp": "aitp_v5_audit_source_reconstruction",
        "surface": "source_reconstruction_audit",
    },
}
