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
    assert entrypoints["record_validation_result"]["surface"] == "validation_result_record"
    assert entrypoints["record_evidence"]["mcp"] == "aitp_v5_record_evidence"
    assert entrypoints["record_code_state"]["mcp"] == "aitp_v5_record_code_state"
    assert entrypoints["register_tool_recipe"]["mcp"] == "aitp_v5_register_tool_recipe"
    assert entrypoints["record_tool_run"]["mcp"] == "aitp_v5_record_tool_run"
    assert entrypoints["execute_tool"]["mcp"] == "aitp_v5_execute_tool"
    assert entrypoints["list_tool_executors"]["mcp"] == "aitp_v5_list_tool_executors"
    assert entrypoints["migrate_legacy_topic"]["mcp"] == "aitp_v5_migrate_legacy_topic_to_v5"
    assert entrypoints["record_validation_result"]["mcp"] == "aitp_v5_record_validation_result"
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


def test_runtime_entrypoint_validation_reports_bad_mcp_and_cli_targets():
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    entrypoints = runtime_entrypoints()
    entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    entrypoints["adapter_registry"]["cli"] = "aitp-v5 missing registry"

    errors = validate_runtime_entrypoints(entrypoints)

    assert any("public_surfaces.mcp" in error for error in errors)
    assert any("adapter_registry.cli" in error for error in errors)
