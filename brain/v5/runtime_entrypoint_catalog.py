"""Runtime entrypoint catalog data and CLI sample arguments."""
from __future__ import annotations

from typing import Any

RUNTIME_ENTRYPOINTS: dict[str, dict[str, Any]] = {
    "public_surfaces": {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    },
    "adapter_registry": {
        "cli": "aitp-v5 adapter registry",
        "mcp": "aitp_v5_get_adapter_protocol_registry",
        "surface": "adapter_protocol_registry",
    },
    "runtime_bridge_target_manifest": {
        "cli": "aitp-v5 adapter bridge-targets",
        "mcp": "aitp_v5_get_runtime_bridge_target_manifest",
        "surface": "runtime_bridge_target_manifest",
    },
    "runtime_payload_profiles": {
        "cli": "aitp-v5 adapter payload-profiles",
        "mcp": "aitp_v5_get_runtime_payload_profiles",
        "surface": "runtime_payload_profiles",
    },
    "record_ref_lookup": {
        "cli": "aitp-v5 adapter record-ref-lookup <args>",
        "mcp": "aitp_v5_lookup_record_refs",
        "surface": "record_ref_lookup",
    },
    "curated_rag_corpus": {
        "cli": "aitp-v5 adapter curated-rag-corpus",
        "mcp": "aitp_v5_get_curated_rag_corpus",
        "surface": "curated_rag_corpus",
    },
    "curated_rag_search": {
        "cli": "aitp-v5 adapter curated-rag-search <query> <args>",
        "mcp": "aitp_v5_search_curated_rag_corpus",
        "surface": "curated_rag_search_result",
    },
    "curated_rag_chunk": {
        "cli": "aitp-v5 adapter curated-rag-chunk <chunk-id>",
        "mcp": "aitp_v5_get_curated_rag_chunk",
        "surface": "curated_rag_chunk",
    },
    "curated_rag_promotion_draft": {
        "cli": "aitp-v5 adapter curated-rag-promotion-draft <chunk-id> <args>",
        "mcp": "aitp_v5_draft_curated_rag_promotion",
        "surface": "curated_rag_promotion_draft",
    },
    "ingest_curated_rag_corpus": {
        "cli": "aitp-v5 curated-rag ingest <args>",
        "mcp": "aitp_v5_ingest_curated_rag_corpus",
        "surface": "curated_rag_ingest_result",
    },
    "record_gate_coverage_audit": {
        "cli": "aitp-v5 adapter record-gate-audit",
        "mcp": "aitp_v5_audit_record_gate_coverage",
        "surface": "record_gate_coverage_audit",
    },
    "runtime_hook_installation_audit": {
        "cli": "aitp-v5 adapter install-audit <runtime> <args>",
        "mcp": "aitp_v5_audit_hook_installation",
        "surface": "runtime_hook_installation_audit",
    },
    "runtime_host_lifecycle_audit": {"cli": "aitp-v5 adapter host-lifecycle <runtime>", "mcp": "aitp_v5_audit_runtime_host_lifecycle", "surface": "runtime_host_lifecycle_audit"},
    "runtime_host_readiness_audit": {"cli": "aitp-v5 adapter host-readiness <runtime>", "mcp": "aitp_v5_audit_runtime_host_readiness", "surface": "runtime_host_readiness_audit"},
    "runtime_hook_installation_paths": {
        "cli": "aitp-v5 adapter install-paths",
        "mcp": "aitp_v5_discover_hook_install_paths",
        "surface": "runtime_hook_installation_paths",
    },
    "runtime_hook_smoke_coverage": {"cli": "aitp-v5 adapter smoke-coverage", "mcp": "aitp_v5_report_hook_smoke_coverage", "surface": "runtime_hook_smoke_coverage"},
    "final_engineering_readiness_audit": {"cli": "aitp-v5 adapter final-readiness", "mcp": "aitp_v5_audit_final_engineering_readiness", "surface": "final_engineering_readiness_audit"},
    "vnext_readiness_manifest": {"cli": "aitp-v5 status vnext-readiness", "mcp": "aitp_v5_build_vnext_readiness_manifest", "surface": "vnext_readiness_manifest"},
    "adapter_packet": {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    "runtime_host_production_loop_audit": {
        "cli": "aitp-v5 adapter host-production-loop",
        "mcp": "aitp_v5_audit_priority_host_production_loops",
        "surface": "runtime_host_production_loop_audit",
    },
    "codex_hook_bridge": {"cli": "aitp-v5 adapter hook-bridge codex <session-id> <args>", "mcp": "aitp_v5_write_codex_hook_bridge", "surface": "codex_hook_bridge"},
    "codex_hook_installation": {"cli": "aitp-v5 adapter install-hooks codex <session-id> <args>", "mcp": "aitp_v5_install_codex_hook_fixture", "surface": "codex_hook_installation"},
    "opencode_plugin_bridge": {"cli": "aitp-v5 adapter hook-bridge opencode <session-id> <args>", "mcp": "aitp_v5_write_opencode_plugin_bridge", "surface": "opencode_plugin_bridge"},
    "opencode_hook_installation": {"cli": "aitp-v5 adapter install-hooks opencode <session-id> <args>", "mcp": "aitp_v5_install_opencode_hook_fixture", "surface": "opencode_hook_installation"},
    "claude_code_hook_settings": {"cli": "aitp-v5 adapter hook-settings claude-code <session-id> <args>", "mcp": "aitp_v5_write_claude_code_hook_settings", "surface": "claude_code_hook_settings"},
    "claude_code_hook_installation": {"cli": "aitp-v5 adapter install-hooks claude-code <session-id> <args>", "mcp": "aitp_v5_install_claude_code_hook_settings", "surface": "claude_code_hook_installation"},
    "kimi_code_hook_config": {"cli": "aitp-v5 adapter hook-settings kimi-code <session-id> <args>", "mcp": "aitp_v5_write_kimi_code_hook_config", "surface": "kimi_code_hook_config"},
    "kimi_code_hook_installation": {"cli": "aitp-v5 adapter install-hooks kimi-code <session-id> <args>", "mcp": "aitp_v5_install_kimi_code_hook_config", "surface": "kimi_code_hook_installation"},
    "adapter_pre_tool_event": {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
    },
    "execution_brief": {
        "cli": "aitp-v5 brief <session-id>",
        "mcp": "aitp_v5_get_execution_brief",
        "surface": "execution_brief",
    },
    "process_graph_slice": {
        "cli": "aitp-v5 graph slice <session-id>",
        "mcp": "aitp_v5_get_process_graph_slice",
        "surface": "process_graph_slice",
    },
    "host_agnostic_moment_policy": {
        "cli": "aitp-v5 graph moment-policy <session-id>",
        "mcp": "aitp_v5_get_host_agnostic_moment_policy",
        "surface": "host_agnostic_moment_policy",
    },
    "record_exploratory_record": {
        "cli": "aitp-v5 exploration record <args>",
        "mcp": "aitp_v5_record_exploratory_record",
        "surface": "exploratory_record",
    },
    "register_source_asset": {
        "cli": "aitp-v5 asset register <args>",
        "mcp": "aitp_v5_register_source_asset",
        "surface": "source_asset_record",
    },
    "capture_source_asset_auto": {
        "cli": "aitp-v5 asset capture-auto <args>",
        "mcp": "aitp_v5_capture_source_asset_auto",
        "surface": "source_asset_record",
    },
    "record_research_route": {
        "cli": "aitp-v5 route record <args>",
        "mcp": "aitp_v5_record_research_route",
        "surface": "research_route_record",
    },
    "interaction_recording_preview": {"cli": "aitp-v5 interaction preview <session-id>", "mcp": "aitp_v5_preview_interaction_recording", "surface": "interaction_recording_preview"},
    "workspace_interaction_preview": {
        "cli": "aitp-v5 interaction workspace-preview",
        "mcp": "aitp_v5_build_workspace_interaction_preview",
        "surface": "workspace_interaction_preview_bundle",
    },
    "interaction_recording_worklist": {
        "cli": "aitp-v5 interaction worklist",
        "mcp": "aitp_v5_build_interaction_recording_worklist",
        "surface": "interaction_recording_worklist",
    },
    "suggest_literature_intake": {
        "cli": "aitp-v5 literature suggest-intake <args>",
        "mcp": "aitp_v5_suggest_literature_intake",
        "surface": "literature_intake_suggestion",
    },
    "record_literature_candidate": {
        "cli": "aitp-v5 literature record-candidate <args>",
        "mcp": "aitp_v5_record_literature_candidate",
        "surface": "literature_intake_record_result",
    },
    "literature_source_review_handoff": {
        "cli": "aitp-v5 literature source-review-handoff <args>",
        "mcp": "aitp_v5_build_literature_source_review_handoff",
        "surface": "literature_source_review_handoff",
    },
    "literature_comparison_draft": {
        "cli": "aitp-v5 literature comparison-draft <args>",
        "mcp": "aitp_v5_build_literature_comparison_draft",
        "surface": "literature_comparison_draft",
    },
    "record_final_output_profile": {
        "cli": "aitp-v5 output profile record <args>",
        "mcp": "aitp_v5_record_final_output_profile",
        "surface": "final_output_profile",
    },
    "request_operator_checkpoint": {
        "cli": "aitp-v5 operator checkpoint request <args>",
        "mcp": "aitp_v5_request_operator_checkpoint",
        "surface": "operator_checkpoint_record",
    },
    "answer_operator_checkpoint": {
        "cli": "aitp-v5 operator checkpoint answer <args>",
        "mcp": "aitp_v5_answer_operator_checkpoint",
        "surface": "operator_checkpoint_record",
    },
    "record_strategy_memory": {
        "cli": "aitp-v5 strategy memory record <args>",
        "mcp": "aitp_v5_record_strategy_memory",
        "surface": "strategy_memory_record",
    },
    "record_lane_exemplar": {
        "cli": "aitp-v5 exemplar lane record <args>",
        "mcp": "aitp_v5_record_lane_exemplar",
        "surface": "lane_exemplar_record",
    },
    "lane_exemplar_manifest": {
        "cli": "aitp-v5 exemplar lane manifest",
        "mcp": "aitp_v5_build_lane_exemplar_manifest",
        "surface": "lane_exemplar_manifest",
    },
    "record_research_intent_packet": {
        "cli": "aitp-v5 intent packet record <args>",
        "mcp": "aitp_v5_record_research_intent_packet",
        "surface": "research_intent_packet",
    },
    "record_run_iteration": {
        "cli": "aitp-v5 run iteration record <args>",
        "mcp": "aitp_v5_record_run_iteration",
        "surface": "run_iteration_record",
    },
    "start_research_run": {
        "cli": "aitp-v5 run research start <args>",
        "mcp": "aitp_v5_start_research_run",
        "surface": "research_run_record",
    },
    "update_research_run": {
        "cli": "aitp-v5 run research update <args>",
        "mcp": "aitp_v5_update_research_run",
        "surface": "research_run_record",
    },
    "record_research_run_event": {
        "cli": "aitp-v5 run event record <args>",
        "mcp": "aitp_v5_record_research_run_event",
        "surface": "research_run_event_record",
    },
    "materialize_steering_redirect": {
        "cli": "aitp-v5 intent steering materialize <args>",
        "mcp": "aitp_v5_materialize_steering_redirect",
        "surface": "steering_decision_record",
    },
    "record_code_state": {
        "cli": "aitp-v5 code state record <args>",
        "mcp": "aitp_v5_record_code_state",
        "surface": "code_state_record",
    },
    "capture_code_state_auto": {
        "cli": "aitp-v5 code state auto <args>",
        "mcp": "aitp_v5_capture_code_state_auto",
        "surface": "code_state_record",
    },
    "record_evidence": {
        "cli": "aitp-v5 evidence record <args>",
        "mcp": "aitp_v5_record_evidence",
        "surface": "evidence_record",
    },
    "register_source": {
        "cli": "aitp-v5 research-state register-source <args>",
        "mcp": "aitp_v5_register_source",
        "surface": "reference_location_record",
    },
    "attach_artifact": {
        "cli": "aitp-v5 research-state attach-artifact <args>",
        "mcp": "aitp_v5_attach_artifact",
        "surface": "artifact_record",
    },
    "attach_artifact_auto": {
        "cli": "aitp-v5 research-state attach-artifact-auto <args>",
        "mcp": "aitp_v5_attach_artifact_auto",
        "surface": "artifact_record",
    },
    "update_claim_status": {
        "cli": "aitp-v5 research-state update-claim-status <args>",
        "mcp": "aitp_v5_update_claim_status",
        "surface": "claim_status_record",
    },
    "create_proof_obligation": {
        "cli": "aitp-v5 research-state create-proof-obligation <args>",
        "mcp": "aitp_v5_create_proof_obligation",
        "surface": "proof_obligation_record",
    },
    "update_proof_obligation": {
        "cli": "aitp-v5 research-state update-proof-obligation <args>",
        "mcp": "aitp_v5_update_proof_obligation",
        "surface": "proof_obligation_record",
    },
    "research_event_classifier": {
        "cli": "aitp-v5 research-state classify-event <args>",
        "mcp": "aitp_v5_classify_research_event",
        "surface": "research_event_classification",
    },
    "record_bounded_numerical_evidence": {
        "cli": "aitp-v5 research-state bounded-evidence <args>",
        "mcp": "aitp_v5_record_bounded_numerical_evidence",
        "surface": "bounded_numerical_evidence_bundle",
    },
    "register_tool_recipe": {
        "cli": "aitp-v5 tool recipe register <args>",
        "mcp": "aitp_v5_register_tool_recipe",
        "surface": "tool_recipe_record",
    },
    "record_tool_run": {
        "cli": "aitp-v5 tool run record <args>",
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
    },
    "capture_tool_run_auto": {
        "cli": "aitp-v5 tool run capture-auto <args>",
        "mcp": "aitp_v5_capture_tool_run_auto",
        "surface": "tool_run_record",
    },
    "execute_tool": {
        "cli": "aitp-v5 tool execute <args>",
        "mcp": "aitp_v5_execute_tool",
        "surface": "tool_run_record",
    },
    "list_tool_executors": {
        "cli": "aitp-v5 tool executors",
        "mcp": "aitp_v5_list_tool_executors",
        "surface": "tool_executor_catalog",
    },
    "list_knowledge_connectors": {
        "cli": "aitp-v5 knowledge connectors",
        "mcp": "aitp_v5_list_knowledge_connectors",
        "surface": "knowledge_connector_catalog",
    },
    "source_reconstruction_audit": {
        "cli": "aitp-v5 source reconstruction-audit <args>",
        "mcp": "aitp_v5_audit_source_reconstruction",
        "surface": "source_reconstruction_audit",
    },
    "source_reconstruction_manifest": {
        "cli": "aitp-v5 source reconstruction-manifest",
        "mcp": "aitp_v5_build_source_reconstruction_manifest",
        "surface": "source_reconstruction_manifest",
    },
    "source_stack_coverage_manifest": {
        "cli": "aitp-v5 source coverage-manifest",
        "mcp": "aitp_v5_build_source_stack_coverage_manifest",
        "surface": "source_stack_coverage_manifest",
    },
    "source_reconstruction_review_manifest": {
        "cli": "aitp-v5 source reconstruction-review-manifest",
        "mcp": "aitp_v5_build_source_reconstruction_review_manifest",
        "surface": "source_reconstruction_review_manifest",
    },
    "source_reconstruction_obsidian_view": {
        "cli": "aitp-v5 source reconstruction-obsidian-view",
        "mcp": "aitp_v5_write_source_reconstruction_obsidian_view",
        "surface": "source_reconstruction_obsidian_view_bundle",
    },
    "source_reconstruction_review_packet": {
        "cli": "aitp-v5 source reconstruction-review <args>",
        "mcp": "aitp_v5_build_source_reconstruction_review_packet",
        "surface": "source_reconstruction_review_packet",
    },
    "record_source_reconstruction_review_result": {
        "cli": "aitp-v5 source reconstruction-review-result <args>",
        "mcp": "aitp_v5_record_source_reconstruction_review_result",
        "surface": "source_reconstruction_review_result_record",
    },
    "persist_hook_trace_event": {
        "cli": "aitp-v5 trace hook-event persist <args>",
        "mcp": "aitp_v5_persist_hook_trace_event",
        "surface": "hook_trace_event_record",
    },
    "record_reference_location": {
        "cli": "aitp-v5 reference location record <args>",
        "mcp": "aitp_v5_record_reference_location",
        "surface": "reference_location_record",
    },
    "migrate_legacy_topic": {
        "cli": "aitp-v5 legacy migrate <args>",
        "mcp": "aitp_v5_migrate_legacy_topic_to_v5",
        "surface": "legacy_migration_result",
    },
    "legacy_migration_coverage_audit": {
        "cli": "aitp-v5 legacy migration-audit <args>",
        "mcp": "aitp_v5_audit_legacy_migration_coverage",
        "surface": "legacy_migration_coverage_audit",
    },
    "legacy_l2_graph_manifest": {
        "cli": "aitp-v5 legacy l2-graph-manifest <args>",
        "mcp": "aitp_v5_build_legacy_l2_graph_manifest",
        "surface": "legacy_l2_graph_manifest",
    },
    "legacy_l2_typed_migration_packet": {
        "cli": "aitp-v5 legacy l2-typed-migration-packet <args>",
        "mcp": "aitp_v5_build_legacy_l2_typed_migration_packet",
        "surface": "legacy_l2_typed_migration_packet",
    },
    "legacy_l2_obsidian_view": {
        "cli": "aitp-v5 legacy l2-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_l2_obsidian_view",
        "surface": "legacy_l2_obsidian_view_bundle",
    },
    "legacy_runtime_log_marker_audit": {
        "cli": "aitp-v5 legacy runtime-log-marker-audit <args>",
        "mcp": "aitp_v5_build_legacy_runtime_log_marker_audit",
        "surface": "legacy_runtime_log_marker_audit",
    },
    "legacy_semantic_review_queue": {
        "cli": "aitp-v5 legacy semantic-review-queue <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_queue",
        "surface": "legacy_semantic_review_queue",
    },
    "legacy_semantic_review_manifest": {
        "cli": "aitp-v5 legacy semantic-review-manifest <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_manifest",
        "surface": "legacy_semantic_review_manifest",
    },
    "legacy_semantic_review_worklist": {
        "cli": "aitp-v5 legacy semantic-review-worklist <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_worklist",
        "surface": "legacy_semantic_review_worklist",
    },
    "legacy_semantic_needs_revision_basis_queue": {
        "cli": "aitp-v5 legacy semantic-needs-revision-basis <args>",
        "mcp": "aitp_v5_build_legacy_semantic_needs_revision_basis_queue",
        "surface": "legacy_semantic_needs_revision_basis_queue",
    },
    "legacy_semantic_needs_revision_basis_packet": {
        "cli": "aitp-v5 legacy semantic-needs-revision-basis-packet <args>",
        "mcp": "aitp_v5_build_legacy_semantic_needs_revision_basis_packet",
        "surface": "legacy_semantic_needs_revision_basis_packet",
    },
    "legacy_semantic_needs_revision_basis_obsidian_view": {
        "cli": "aitp-v5 legacy semantic-needs-revision-basis-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_semantic_needs_revision_basis_obsidian_view",
        "surface": "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
    },
    "legacy_semantic_review_obsidian_view": {
        "cli": "aitp-v5 legacy semantic-review-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_semantic_review_obsidian_view",
        "surface": "legacy_semantic_review_obsidian_view_bundle",
    },
    "legacy_semantic_review_packet": {
        "cli": "aitp-v5 legacy semantic-review-packet <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_packet",
        "surface": "legacy_semantic_review_packet",
    },
    "legacy_semantic_repair_plan": {
        "cli": "aitp-v5 legacy semantic-repair-plan <args>",
        "mcp": "aitp_v5_build_legacy_semantic_repair_plan",
        "surface": "legacy_semantic_repair_plan",
    },
    "legacy_semantic_repair_manifest": {
        "cli": "aitp-v5 legacy semantic-repair-manifest <args>",
        "mcp": "aitp_v5_build_legacy_semantic_repair_manifest",
        "surface": "legacy_semantic_repair_manifest",
    },
    "legacy_semantic_repair_apply": {
        "cli": "aitp-v5 legacy semantic-repair-apply <args>",
        "mcp": "aitp_v5_apply_legacy_semantic_repair",
        "surface": "legacy_semantic_repair_apply",
    },
    "legacy_source_reconstruction_plan": {
        "cli": "aitp-v5 legacy source-reconstruction-plan <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_plan",
        "surface": "legacy_source_reconstruction_plan",
    },
    "legacy_source_reconstruction_manifest": {
        "cli": "aitp-v5 legacy source-reconstruction-manifest <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_manifest",
        "surface": "legacy_source_reconstruction_manifest",
    },
    "legacy_source_reconstruction_obsidian_view": {
        "cli": "aitp-v5 legacy source-reconstruction-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_source_reconstruction_obsidian_view",
        "surface": "legacy_source_reconstruction_obsidian_view_bundle",
    },
    "legacy_source_reconstruction_review_packet": {
        "cli": "aitp-v5 legacy source-reconstruction-review <args>",
        "mcp": "aitp_v5_build_legacy_source_reconstruction_review_packet",
        "surface": "legacy_source_reconstruction_review_packet",
    },
    "legacy_source_metadata_repair_packet": {
        "cli": "aitp-v5 legacy source-metadata-repair-packet <args>",
        "mcp": "aitp_v5_build_legacy_source_metadata_repair_packet",
        "surface": "legacy_source_metadata_repair_packet",
    },
    "legacy_executable_evidence_packet": {
        "cli": "aitp-v5 legacy executable-evidence-packet <args>",
        "mcp": "aitp_v5_build_legacy_executable_evidence_packet",
        "surface": "legacy_executable_evidence_packet",
    },
    "legacy_human_checkpoint_packet": {
        "cli": "aitp-v5 legacy human-checkpoint-packet <args>",
        "mcp": "aitp_v5_build_legacy_human_checkpoint_packet",
        "surface": "legacy_human_checkpoint_packet",
    },
    "legacy_topic_question_backfill_packet": {
        "cli": "aitp-v5 legacy topic-question-backfill-packet <args>",
        "mcp": "aitp_v5_build_legacy_topic_question_backfill_packet",
        "surface": "legacy_topic_question_backfill_packet",
    },
    "legacy_human_checkpoint_obsidian_view": {
        "cli": "aitp-v5 legacy human-checkpoint-obsidian-view <args>",
        "mcp": "aitp_v5_write_legacy_human_checkpoint_obsidian_view",
        "surface": "legacy_human_checkpoint_obsidian_view_bundle",
    },
    "legacy_source_reconstruction_apply": {
        "cli": "aitp-v5 legacy source-reconstruction-apply <args>",
        "mcp": "aitp_v5_apply_legacy_source_reconstruction_repair",
        "surface": "legacy_source_reconstruction_apply",
    },
    "record_legacy_semantic_review_result": {
        "cli": "aitp-v5 legacy semantic-review-result <args>",
        "mcp": "aitp_v5_record_legacy_semantic_review_result",
        "surface": "legacy_semantic_review_result_record",
    },
    "summary_orientation": {
        "cli": "aitp-v5 summary orientation <session-id>",
        "mcp": "aitp_v5_read_summary_orientation",
        "surface": "summary_orientation",
    },
    "session_summary": {
        "cli": "aitp-v5 summary session <session-id>",
        "mcp": "aitp_v5_write_session_summary",
        "surface": "session_summary_bundle",
    },
    "workspace_summary": {"cli": "aitp-v5 summary workspace", "mcp": "aitp_v5_write_workspace_summary", "surface": "workspace_summary_bundle"},
    "workspace_replay": {"cli": "aitp-v5 summary replay", "mcp": "aitp_v5_write_workspace_replay_packet", "surface": "workspace_replay_packet"},
    "workspace_refresh": {"cli": "aitp-v5 summary refresh", "mcp": "aitp_v5_refresh_workspace_views", "surface": "workspace_refresh_bundle"},
    "topic_status": {"cli": "aitp-v5 status topic <session-id>", "mcp": "aitp_v5_write_topic_status_surfaces", "surface": "topic_status_bundle"},
    "topic_status_compact": {"cli": "aitp-v5 status topic <session-id> --compact", "mcp": "aitp_v5_write_topic_status_surfaces_compact", "surface": "topic_status_bundle"},
    "qsgw_cockpit": {"cli": "aitp-v5 status qsgw-cockpit", "mcp": "aitp_v5_write_qsgw_cockpit_surfaces", "surface": "qsgw_cockpit_bundle"},
    "qsgw_cockpit_compact": {"cli": "aitp-v5 status qsgw-cockpit --compact", "mcp": "aitp_v5_write_qsgw_cockpit_surfaces_compact", "surface": "qsgw_cockpit_bundle"},
    "research_cockpit": {"cli": "aitp-v5 status research-cockpit", "mcp": "aitp_v5_write_research_cockpit_surfaces", "surface": "research_cockpit_bundle"},
    "research_cockpit_compact": {"cli": "aitp-v5 status research-cockpit --compact", "mcp": "aitp_v5_write_research_cockpit_surfaces_compact", "surface": "research_cockpit_bundle"},
    "trust_preflight": {
        "cli": "aitp-v5 trust preflight <args>",
        "mcp": "aitp_v5_preflight_trust_update",
        "surface": "trust_update_preflight",
    },
    "trust_apply": {
        "cli": "aitp-v5 trust apply <args>",
        "mcp": "aitp_v5_apply_trust_update",
        "surface": "trust_update_apply",
    },
    "get_trust_update_record": {
        "cli": "aitp-v5 trust update-record <args>",
        "mcp": "aitp_v5_get_trust_update_record",
        "surface": "trust_update_record",
    },
    "audit_claim_trust": {
        "cli": "aitp-v5 trust audit <args>",
        "mcp": "aitp_v5_audit_claim_trust",
        "surface": "claim_trust_audit",
    },
    "pre_tool_policy": {
        "cli": "aitp-v5 policy pre-tool <args>",
        "mcp": "aitp_v5_evaluate_pre_tool_policy",
        "surface": "pre_tool_policy_decision",
    },
    "record_physics_object": {
        "cli": "aitp-v5 object record <args>",
        "mcp": "aitp_v5_record_physics_object",
        "surface": "physics_object_record",
    },
    "record_object_relation": {
        "cli": "aitp-v5 relation record <args>",
        "mcp": "aitp_v5_record_object_relation",
        "surface": "object_relation_record",
    },
    "record_sensemaking_report": {
        "cli": "aitp-v5 sensemaking report <args>",
        "mcp": "aitp_v5_record_sensemaking_report",
        "surface": "sensemaking_report_record",
    },
    "ingest_subagent_result": {
        "cli": "aitp-v5 subagent ingest-result <args>",
        "mcp": "aitp_v5_ingest_subagent_result",
        "surface": "sensemaking_report_record",
    },
    "create_validation_contract": {
        "cli": "aitp-v5 validation contract create <args>",
        "mcp": "aitp_v5_create_validation_contract",
        "surface": "validation_contract_record",
    },
    "record_validation_result": {
        "cli": "aitp-v5 validation result record <args>",
        "mcp": "aitp_v5_record_validation_result",
        "surface": "validation_result_record",
    },
    "request_human_checkpoint": {
        "cli": "aitp-v5 checkpoint request <args>",
        "mcp": "aitp_v5_request_human_checkpoint",
        "surface": "human_checkpoint_record",
    },
    "decide_human_checkpoint": {
        "cli": "aitp-v5 checkpoint decide <args>",
        "mcp": "aitp_v5_decide_human_checkpoint",
        "surface": "human_checkpoint_record",
    },
    "create_promotion_packet": {
        "cli": "aitp-v5 promotion packet create <args>",
        "mcp": "aitp_v5_create_promotion_packet",
        "surface": "promotion_packet_record",
    },
    "apply_promotion_packet": {
        "cli": "aitp-v5 promotion packet apply <args>",
        "mcp": "aitp_v5_apply_promotion_packet",
        "surface": "memory_entry_record",
    },
    "audit_l2_memory_context": {"cli": "aitp-v5 memory audit <args>", "mcp": "aitp_v5_audit_l2_memory_context", "surface": "l2_memory_audit"},
    "l2_obsidian_view": {"cli": "aitp-v5 memory obsidian-view", "mcp": "aitp_v5_write_l2_obsidian_view", "surface": "l2_obsidian_view_bundle"},
    "audit_failure_mode_coverage": {"cli": "aitp-v5 memory failure-modes <args>", "mcp": "aitp_v5_audit_failure_mode_coverage", "surface": "failure_mode_audit"},
    "build_failure_mode_review_packet": {"cli": "aitp-v5 memory failure-mode-review <args>", "mcp": "aitp_v5_build_failure_mode_review_packet", "surface": "failure_mode_review_packet"},
    "request_failure_mode_review_checkpoint": {"cli": "aitp-v5 memory request-failure-mode-review <args>", "mcp": "aitp_v5_request_failure_mode_review_checkpoint", "surface": "human_checkpoint_record"},
    "record_failure_mode_review_result": {"cli": "aitp-v5 memory failure-mode-review-result <args>", "mcp": "aitp_v5_record_failure_mode_review_result", "surface": "failure_mode_review_result_record"},
    "goal_continuation_write": {"cli": "aitp-v5 goal write <args>", "mcp": "aitp_v5_write_goal_continuation", "surface": "goal_continuation_packet"},
    "goal_continuation_latest": {"cli": "aitp-v5 goal latest", "mcp": "aitp_v5_read_latest_goal_continuation", "surface": "goal_continuation_packet"},
    "goal_continuation_list": {"cli": "aitp-v5 goal list", "mcp": "aitp_v5_list_goal_continuations", "surface": "goal_continuation_list"},
}


def sample_args_for_template(template: str) -> list[str]:
    from brain.v5.runtime_entrypoint_samples import sample_args_for_template as _sample_args

    return _sample_args(template)
