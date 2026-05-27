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
    assert entrypoints["execute_tool"]["surface"] == "tool_run_record"
    assert entrypoints["list_tool_executors"]["surface"] == "tool_executor_catalog"
    assert entrypoints["migrate_legacy_topic"]["surface"] == "legacy_migration_result"
    assert entrypoints["legacy_migration_coverage_audit"]["surface"] == "legacy_migration_coverage_audit"
    assert entrypoints["legacy_semantic_review_queue"]["surface"] == "legacy_semantic_review_queue"
    assert entrypoints["legacy_semantic_review_worklist"]["surface"] == "legacy_semantic_review_worklist"
    assert entrypoints["legacy_semantic_repair_apply"]["surface"] == "legacy_semantic_repair_apply"
    assert entrypoints["legacy_semantic_repair_plan"]["surface"] == "legacy_semantic_repair_plan"
    assert entrypoints["source_reconstruction_manifest"]["surface"] == "source_reconstruction_manifest"
    assert entrypoints["record_legacy_semantic_review_result"]["surface"] == (
        "legacy_semantic_review_result_record"
    )
    assert entrypoints["record_validation_result"]["surface"] == "validation_result_record"
    assert entrypoints["record_evidence"]["mcp"] == "aitp_v5_record_evidence"
    assert entrypoints["record_code_state"]["mcp"] == "aitp_v5_record_code_state"
    assert entrypoints["register_tool_recipe"]["mcp"] == "aitp_v5_register_tool_recipe"
    assert entrypoints["record_tool_run"]["mcp"] == "aitp_v5_record_tool_run"
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
    assert entrypoints["source_reconstruction_manifest"]["mcp"] == "aitp_v5_build_source_reconstruction_manifest"
    assert entrypoints["record_legacy_semantic_review_result"]["mcp"] == (
        "aitp_v5_record_legacy_semantic_review_result"
    )
    assert entrypoints["record_validation_result"]["mcp"] == "aitp_v5_record_validation_result"
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


def test_runtime_entrypoint_validation_reports_bad_mcp_and_cli_targets():
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    entrypoints = runtime_entrypoints()
    entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    entrypoints["adapter_registry"]["cli"] = "aitp-v5 missing registry"

    errors = validate_runtime_entrypoints(entrypoints)

    assert any("public_surfaces.mcp" in error for error in errors)
    assert any("adapter_registry.cli" in error for error in errors)
