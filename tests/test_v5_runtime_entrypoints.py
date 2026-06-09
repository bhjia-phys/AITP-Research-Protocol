from __future__ import annotations


def test_runtime_entrypoint_validation_confirms_advertised_targets_exist():
    from brain.v5.runtime_entrypoints import validate_runtime_entrypoints

    assert validate_runtime_entrypoints() == []


def test_runtime_entrypoints_advertise_typed_write_surfaces():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    entrypoints = runtime_entrypoints()

    assert entrypoints["record_evidence"]["surface"] == "evidence_record"
    assert entrypoints["record_code_state"]["surface"] == "code_state_record"
    assert entrypoints["register_tool_recipe"]["surface"] == "tool_recipe_record"
    assert entrypoints["record_tool_run"]["surface"] == "tool_run_record"
    assert entrypoints["capture_tool_run_auto"]["surface"] == "tool_run_record"
    assert entrypoints["execute_tool"]["surface"] == "tool_run_record"
    assert entrypoints["list_tool_executors"]["surface"] == "tool_executor_catalog"
    assert entrypoints["migrate_legacy_topic"]["surface"] == "legacy_migration_result"
    assert entrypoints["legacy_migration_coverage_audit"]["surface"] == "legacy_migration_coverage_audit"
    assert entrypoints["legacy_semantic_review_queue"]["surface"] == "legacy_semantic_review_queue"
    assert entrypoints["legacy_semantic_review_worklist"]["surface"] == "legacy_semantic_review_worklist"
    assert entrypoints["legacy_semantic_repair_apply"]["surface"] == "legacy_semantic_repair_apply"
    assert entrypoints["legacy_semantic_repair_plan"]["surface"] == "legacy_semantic_repair_plan"
    assert entrypoints["legacy_semantic_repair_manifest"]["surface"] == "legacy_semantic_repair_manifest"
    assert entrypoints["source_reconstruction_manifest"]["surface"] == "source_reconstruction_manifest"
    assert entrypoints["source_stack_coverage_manifest"]["surface"] == "source_stack_coverage_manifest"
    assert entrypoints["record_legacy_semantic_review_result"]["surface"] == (
        "legacy_semantic_review_result_record"
    )
    assert entrypoints["record_validation_result"]["surface"] == "validation_result_record"
    assert entrypoints["record_exploratory_record"]["surface"] == "exploratory_record"
    assert entrypoints["record_research_route"]["surface"] == "research_route_record"
    assert entrypoints["capture_source_asset_auto"]["surface"] == "source_asset_record"
    assert entrypoints["host_agnostic_moment_policy"]["surface"] == "host_agnostic_moment_policy"
    assert entrypoints["runtime_bridge_target_manifest"]["surface"] == "runtime_bridge_target_manifest"
    assert entrypoints["runtime_payload_profiles"]["surface"] == "runtime_payload_profiles"
    assert entrypoints["record_evidence"]["mcp"] == "aitp_v5_record_evidence"
    assert entrypoints["record_code_state"]["mcp"] == "aitp_v5_record_code_state"
    assert entrypoints["register_tool_recipe"]["mcp"] == "aitp_v5_register_tool_recipe"
    assert entrypoints["record_tool_run"]["mcp"] == "aitp_v5_record_tool_run"
    assert entrypoints["capture_tool_run_auto"]["mcp"] == "aitp_v5_capture_tool_run_auto"
    assert entrypoints["execute_tool"]["mcp"] == "aitp_v5_execute_tool"
    assert entrypoints["list_tool_executors"]["mcp"] == "aitp_v5_list_tool_executors"
    assert entrypoints["migrate_legacy_topic"]["mcp"] == "aitp_v5_migrate_legacy_topic_to_v5"
    assert entrypoints["legacy_migration_coverage_audit"]["mcp"] == "aitp_v5_audit_legacy_migration_coverage"
    assert entrypoints["legacy_semantic_review_queue"]["mcp"] == "aitp_v5_build_legacy_semantic_review_queue"
    assert entrypoints["legacy_semantic_review_worklist"]["mcp"] == (
        "aitp_v5_build_legacy_semantic_review_worklist"
    )
    assert entrypoints["legacy_semantic_repair_apply"]["mcp"] == "aitp_v5_apply_legacy_semantic_repair"
    assert entrypoints["legacy_semantic_repair_plan"]["mcp"] == "aitp_v5_build_legacy_semantic_repair_plan"
    assert entrypoints["legacy_semantic_repair_manifest"]["mcp"] == (
        "aitp_v5_build_legacy_semantic_repair_manifest"
    )
    assert entrypoints["source_reconstruction_manifest"]["mcp"] == "aitp_v5_build_source_reconstruction_manifest"
    assert entrypoints["source_stack_coverage_manifest"]["mcp"] == (
        "aitp_v5_build_source_stack_coverage_manifest"
    )
    assert entrypoints["record_legacy_semantic_review_result"]["mcp"] == (
        "aitp_v5_record_legacy_semantic_review_result"
    )
    assert entrypoints["record_validation_result"]["mcp"] == "aitp_v5_record_validation_result"
    assert entrypoints["record_exploratory_record"]["mcp"] == "aitp_v5_record_exploratory_record"
    assert entrypoints["record_research_route"]["mcp"] == "aitp_v5_record_research_route"
    assert entrypoints["capture_source_asset_auto"]["mcp"] == "aitp_v5_capture_source_asset_auto"
    assert entrypoints["host_agnostic_moment_policy"]["mcp"] == "aitp_v5_get_host_agnostic_moment_policy"
    assert entrypoints["runtime_bridge_target_manifest"] == {
        "cli": "aitp-v5 adapter bridge-targets",
        "mcp": "aitp_v5_get_runtime_bridge_target_manifest",
        "surface": "runtime_bridge_target_manifest",
    }
    assert entrypoints["runtime_payload_profiles"] == {
        "cli": "aitp-v5 adapter payload-profiles",
        "mcp": "aitp_v5_get_runtime_payload_profiles",
        "surface": "runtime_payload_profiles",
    }
    assert entrypoints["curated_rag_chunk"] == {
        "cli": "aitp-v5 adapter curated-rag-chunk <chunk-id>",
        "mcp": "aitp_v5_get_curated_rag_chunk",
        "surface": "curated_rag_chunk",
    }
    assert entrypoints["curated_rag_promotion_draft"] == {
        "cli": "aitp-v5 adapter curated-rag-promotion-draft <chunk-id> <args>",
        "mcp": "aitp_v5_draft_curated_rag_promotion",
        "surface": "curated_rag_promotion_draft",
    }
    assert entrypoints["get_trust_update_record"] == {
        "cli": "aitp-v5 trust update-record <args>",
        "mcp": "aitp_v5_get_trust_update_record",
        "surface": "trust_update_record",
    }
    assert entrypoints["codex_hook_bridge"] == {
        "cli": "aitp-v5 adapter hook-bridge codex <session-id> <args>",
        "mcp": "aitp_v5_write_codex_hook_bridge",
        "surface": "codex_hook_bridge",
    }
    assert entrypoints["codex_hook_installation"] == {
        "cli": "aitp-v5 adapter install-hooks codex <session-id> <args>",
        "mcp": "aitp_v5_install_codex_hook_fixture",
        "surface": "codex_hook_installation",
    }
    assert entrypoints["opencode_plugin_bridge"] == {
        "cli": "aitp-v5 adapter hook-bridge opencode <session-id> <args>",
        "mcp": "aitp_v5_write_opencode_plugin_bridge",
        "surface": "opencode_plugin_bridge",
    }
    assert entrypoints["opencode_hook_installation"] == {
        "cli": "aitp-v5 adapter install-hooks opencode <session-id> <args>",
        "mcp": "aitp_v5_install_opencode_hook_fixture",
        "surface": "opencode_hook_installation",
    }
    assert entrypoints["claude_code_hook_settings"] == {
        "cli": "aitp-v5 adapter hook-settings claude-code <session-id> <args>",
        "mcp": "aitp_v5_write_claude_code_hook_settings",
        "surface": "claude_code_hook_settings",
    }
    assert entrypoints["claude_code_hook_installation"] == {
        "cli": "aitp-v5 adapter install-hooks claude-code <session-id> <args>",
        "mcp": "aitp_v5_install_claude_code_hook_settings",
        "surface": "claude_code_hook_installation",
    }
    assert entrypoints["kimi_code_hook_config"] == {
        "cli": "aitp-v5 adapter hook-settings kimi-code <session-id> <args>",
        "mcp": "aitp_v5_write_kimi_code_hook_config",
        "surface": "kimi_code_hook_config",
    }
    assert entrypoints["kimi_code_hook_installation"] == {
        "cli": "aitp-v5 adapter install-hooks kimi-code <session-id> <args>",
        "mcp": "aitp_v5_install_kimi_code_hook_config",
        "surface": "kimi_code_hook_installation",
    }
    assert entrypoints["persist_hook_trace_event"] == {
        "cli": "aitp-v5 trace hook-event persist <args>",
        "mcp": "aitp_v5_persist_hook_trace_event",
        "surface": "hook_trace_event_record",
    }
    assert entrypoints["pre_tool_policy"] == {
        "cli": "aitp-v5 policy pre-tool <args>",
        "mcp": "aitp_v5_evaluate_pre_tool_policy",
        "surface": "pre_tool_policy_decision",
    }
    assert entrypoints["adapter_pre_tool_event"] == {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
    }
    assert entrypoints["record_gate_coverage_audit"] == {
        "cli": "aitp-v5 adapter record-gate-audit",
        "mcp": "aitp_v5_audit_record_gate_coverage",
        "surface": "record_gate_coverage_audit",
    }
    assert entrypoints["runtime_hook_installation_audit"] == {
        "cli": "aitp-v5 adapter install-audit <runtime> <args>",
        "mcp": "aitp_v5_audit_hook_installation",
        "surface": "runtime_hook_installation_audit",
    }
    assert entrypoints["runtime_host_readiness_audit"] == {
        "cli": "aitp-v5 adapter host-readiness <runtime>",
        "mcp": "aitp_v5_audit_runtime_host_readiness",
        "surface": "runtime_host_readiness_audit",
    }
    assert entrypoints["runtime_host_lifecycle_audit"] == {
        "cli": "aitp-v5 adapter host-lifecycle <runtime>",
        "mcp": "aitp_v5_audit_runtime_host_lifecycle",
        "surface": "runtime_host_lifecycle_audit",
    }
    assert entrypoints["runtime_hook_installation_paths"] == {
        "cli": "aitp-v5 adapter install-paths",
        "mcp": "aitp_v5_discover_hook_install_paths",
        "surface": "runtime_hook_installation_paths",
    }
    assert entrypoints["runtime_hook_smoke_coverage"] == {
        "cli": "aitp-v5 adapter smoke-coverage",
        "mcp": "aitp_v5_report_hook_smoke_coverage",
        "surface": "runtime_hook_smoke_coverage",
    }
    assert entrypoints["interaction_recording_preview"] == {
        "cli": "aitp-v5 interaction preview <session-id>",
        "mcp": "aitp_v5_preview_interaction_recording",
        "surface": "interaction_recording_preview",
    }
    assert entrypoints["workspace_interaction_preview"] == {
        "cli": "aitp-v5 interaction workspace-preview",
        "mcp": "aitp_v5_build_workspace_interaction_preview",
        "surface": "workspace_interaction_preview_bundle",
    }
    assert entrypoints["interaction_recording_worklist"] == {
        "cli": "aitp-v5 interaction worklist",
        "mcp": "aitp_v5_build_interaction_recording_worklist",
        "surface": "interaction_recording_worklist",
    }


def test_hakimi_runtime_bridge_entrypoint_contract_is_stable():
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    entrypoints = runtime_entrypoints()
    manifest = runtime_bridge_target_manifest()

    expected = {
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
        "runtime_payload_profiles": {
            "cli": "aitp-v5 adapter payload-profiles",
            "mcp": "aitp_v5_get_runtime_payload_profiles",
            "surface": "runtime_payload_profiles",
        },
        "curated_rag_chunk": {
            "cli": "aitp-v5 adapter curated-rag-chunk <chunk-id>",
            "mcp": "aitp_v5_get_curated_rag_chunk",
            "surface": "curated_rag_chunk",
        },
        "record_evidence": {
            "cli": "aitp-v5 evidence record <args>",
            "mcp": "aitp_v5_record_evidence",
            "surface": "evidence_record",
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
        "record_reference_location": {
            "cli": "aitp-v5 reference location record <args>",
            "mcp": "aitp_v5_record_reference_location",
            "surface": "reference_location_record",
        },
        "record_validation_result": {
            "cli": "aitp-v5 validation result record <args>",
            "mcp": "aitp_v5_record_validation_result",
            "surface": "validation_result_record",
        },
        "record_exploratory_record": {
            "cli": "aitp-v5 exploration record <args>",
            "mcp": "aitp_v5_record_exploratory_record",
            "surface": "exploratory_record",
        },
        "record_research_route": {
            "cli": "aitp-v5 route record <args>",
            "mcp": "aitp_v5_record_research_route",
            "surface": "research_route_record",
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
        "create_validation_contract": {
            "cli": "aitp-v5 validation contract create <args>",
            "mcp": "aitp_v5_create_validation_contract",
            "surface": "validation_contract_record",
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
    }

    for key, contract in expected.items():
        assert entrypoints[key] == contract

    by_operation = {target["operation"]: target for target in manifest["targets"]}
    assert by_operation["readProcessGraphSlice"] == {
        "operation": "readProcessGraphSlice",
        "entrypoint_key": "process_graph_slice",
        "mcp_tool": "aitp_v5_get_process_graph_slice",
        "cli_fallback": "aitp-v5 graph slice <session-id>",
        "surface": "process_graph_slice",
        "preferred_transport": "mcp",
        "fallback_transport": "cli",
        "mcp_invocation": {
            "tool": "aitp_v5_get_process_graph_slice",
            "argument_style": "json_object",
            "base_argument": "base",
            "payload_key_case": "snake_case",
            "result_surface": "process_graph_slice",
            "result_content_type": "json_object",
            "fallback_policy": "use_cli_when_mcp_transport_unavailable_or_call_fails",
        },
        "execution_role": "read",
        "state_effect": "read_only",
        "canonical_store": ".aitp",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "mcp_arguments": {
            "required": ["base", "session_id"],
            "optional": ["claim_id", "limit"],
            "source": "aitp_v5_get_process_graph_slice",
        },
    }
    assert by_operation["recordEvidence"]["mcp_tool"] == "aitp_v5_record_evidence"
    assert by_operation["recordEvidence"]["cli_fallback"] == "aitp-v5 evidence record <args>"
    assert by_operation["recordEvidence"]["mcp_invocation"] == {
        "tool": "aitp_v5_record_evidence",
        "argument_style": "json_object",
        "base_argument": "base",
        "payload_key_case": "snake_case",
        "result_surface": "evidence_record",
        "result_content_type": "json_object",
        "fallback_policy": "use_cli_when_mcp_transport_unavailable_or_call_fails",
    }
    assert by_operation["captureToolRunAuto"]["mcp_tool"] == "aitp_v5_capture_tool_run_auto"
    assert by_operation["captureToolRunAuto"]["cli_fallback"] == "aitp-v5 tool run capture-auto <args>"
    assert by_operation["captureToolRunAuto"]["surface"] == "tool_run_record"
    assert by_operation["captureSourceAssetAuto"]["mcp_tool"] == "aitp_v5_capture_source_asset_auto"
    assert by_operation["captureSourceAssetAuto"]["cli_fallback"] == "aitp-v5 asset capture-auto <args>"
    assert by_operation["captureSourceAssetAuto"]["surface"] == "source_asset_record"
    assert by_operation["captureCodeStateAuto"]["mcp_tool"] == "aitp_v5_capture_code_state_auto"
    assert by_operation["readRuntimePayloadProfiles"]["entrypoint_key"] == "runtime_payload_profiles"
    assert by_operation["readRuntimePayloadProfiles"]["mcp_tool"] == "aitp_v5_get_runtime_payload_profiles"
    assert by_operation["readRuntimePayloadProfiles"]["cli_fallback"] == "aitp-v5 adapter payload-profiles"
    assert by_operation["readRuntimePayloadProfiles"]["surface"] == "runtime_payload_profiles"
    assert by_operation["readRuntimePayloadProfiles"]["execution_role"] == "read"
    assert by_operation["readRuntimePayloadProfiles"]["state_effect"] == "read_only"
    assert by_operation["readRuntimePayloadProfiles"]["claim_trust_mutation"] == "none"
    assert by_operation["readRuntimePayloadProfiles"]["can_update_claim_trust"] is False
    assert by_operation["readRuntimePayloadProfiles"]["mcp_arguments"] == {
        "required": [],
        "optional": [],
        "source": "aitp_v5_get_runtime_payload_profiles",
    }
    assert by_operation["readCuratedRagChunk"]["entrypoint_key"] == "curated_rag_chunk"
    assert by_operation["readCuratedRagChunk"]["mcp_tool"] == "aitp_v5_get_curated_rag_chunk"
    assert by_operation["readCuratedRagChunk"]["cli_fallback"] == "aitp-v5 adapter curated-rag-chunk <chunk-id>"
    assert by_operation["readCuratedRagChunk"]["surface"] == "curated_rag_chunk"
    assert by_operation["readCuratedRagChunk"]["execution_role"] == "read"
    assert by_operation["readCuratedRagChunk"]["state_effect"] == "read_only"
    assert by_operation["readCuratedRagChunk"]["mcp_arguments"] == {
        "required": ["chunk_id"],
        "optional": ["base"],
        "source": "aitp_v5_get_curated_rag_chunk",
    }
    assert by_operation["preflightTrustUpdate"]["mcp_tool"] == "aitp_v5_preflight_trust_update"
    assert by_operation["preflightTrustUpdate"]["state_effect"] == "preflight_only"
    assert "trustApply" not in by_operation
    assert manifest["excluded_entrypoints"]["trust_apply"].startswith("claim trust mutation")
    assert manifest["preferred_transport"] == "mcp"
    assert manifest["fallback_transport"] == "cli"
    assert manifest["mcp_argument_style"] == "json_object"
    assert manifest["mcp_base_argument"] == "base"
    assert manifest["mcp_payload_key_case"] == "snake_case"
    assert manifest["mcp_result_content_type"] == "json_object"
    assert manifest["fallback_policy"] == "use_cli_when_mcp_transport_unavailable_or_call_fails"
    assert manifest["can_update_claim_trust"] is False


def test_runtime_entrypoint_validation_reports_bad_mcp_and_cli_targets():
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    entrypoints = runtime_entrypoints()
    entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    entrypoints["adapter_registry"]["cli"] = "aitp-v5 missing registry"

    errors = validate_runtime_entrypoints(entrypoints)

    assert any("public_surfaces.mcp" in error for error in errors)
    assert any("adapter_registry.cli" in error for error in errors)
