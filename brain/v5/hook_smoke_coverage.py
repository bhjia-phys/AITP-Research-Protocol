"""Read-only coverage report for AITP v5 runtime hook smoke checks."""

from __future__ import annotations

from typing import Any


def runtime_hook_smoke_coverage_report() -> dict[str, Any]:
    """Report which generated hook paths have test-backed smoke coverage."""

    runtimes = [
        {
            "runtime": "codex",
            "status": "partial",
            "checks": [
                _check(
                    "fixture_runner_contract",
                    "Generated Codex fixture runners execute pre-tool policy and post-tool trace persistence.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_codex_install_fixture_runner_executes_from_declared_cwd",
                        "tests/test_v5_adapter_event_runner.py::test_codex_install_fixture_post_tool_runner_persists_trace_event",
                    ],
                ),
                _check(
                    "native_hooks_json_workspace_cwd",
                    "Generated Codex hooks.json command strings execute from a user workspace cwd.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_codex_native_hooks_json_pre_tool_command_executes_from_workspace_cwd",
                        "tests/test_v5_adapter_event_runner.py::test_codex_native_hooks_json_post_tool_command_executes_from_workspace_cwd",
                    ],
                ),
                _host_readiness_check(),
                _host_lifecycle_check(),
            ],
            "gaps": ["real_interactive_lifecycle_event_smoke"],
        },
        {
            "runtime": "claude_code",
            "status": "partial",
            "checks": [
                _check(
                    "settings_generation_and_merge_contract",
                    "Generated and merged Claude Code settings preserve hook contracts.",
                    [
                        "tests/test_v5_adapters.py::test_cli_adapter_hook_settings_writes_claude_code_settings_from_packet",
                        "tests/test_v5_adapters.py::test_claude_code_hook_installer_merges_existing_settings_without_clobbering",
                    ],
                ),
                _check(
                    "session_start_workspace_refresh",
                    "Generated Claude Code SessionStart command refreshes workspace review views.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_claude_code_hook_session_start_refreshes_workspace_views",
                    ],
                ),
                _host_readiness_check(),
                _host_lifecycle_check(),
            ],
            "gaps": ["real_interactive_lifecycle_event_smoke"],
        },
        {
            "runtime": "kimi_code",
            "status": "partial",
            "checks": [
                _check(
                    "config_generation_and_merge_contract",
                    "Generated Kimi Code TOML hooks preserve existing config while installing AITP lifecycle commands.",
                    [
                        "tests/test_v5_adapters.py::test_cli_adapter_hook_settings_writes_kimi_code_config_from_packet",
                        "tests/test_v5_adapters.py::test_kimi_code_hook_config_installer_merges_existing_config",
                    ],
                ),
                _check(
                    "native_hook_process_smoke",
                    "Generated Kimi Code hook commands execute from a user workspace cwd and block unsafe summary-truth writes.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_kimi_code_hook_pre_tool_command_executes_from_workspace_cwd",
                        "tests/test_v5_adapter_event_runner.py::test_kimi_code_hook_post_tool_command_persists_trace_event",
                    ],
                ),
                _check(
                    "session_start_workspace_refresh",
                    "Generated Kimi Code SessionStart command refreshes workspace review views.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_kimi_code_hook_session_start_refreshes_workspace_views",
                    ],
                ),
                _host_readiness_check(),
                _host_lifecycle_check(),
            ],
            "gaps": ["real_interactive_lifecycle_event_smoke"],
        },
        {
            "runtime": "opencode",
            "status": "partial",
            "checks": [
                _check(
                    "fixture_runner_contract",
                    "Generated OpenCode fixture runners execute pre-tool policy and post-tool trace persistence.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_opencode_install_fixture_runner_executes_from_declared_cwd",
                        "tests/test_v5_adapter_event_runner.py::test_opencode_install_fixture_post_tool_runner_persists_trace_event",
                    ],
                ),
                _check(
                    "local_plugin_node_lifecycle",
                    "Generated OpenCode local plugin module loads in Node and runs before/after lifecycle handlers.",
                    [
                        "tests/test_v5_adapter_event_runner.py::test_opencode_local_plugin_runner_argv_is_cwd_independent",
                        "tests/test_v5_adapter_event_runner.py::test_opencode_local_plugin_lifecycle_smoke_executes_generated_plugin",
                    ],
                ),
            ],
            "gaps": ["real_host_process_smoke"],
        },
    ]
    return {
        "kind": "runtime_hook_smoke_coverage",
        "truth_source": "v5_test_contract_registry",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "overall_status": "partial",
        "runtimes": runtimes,
    }


def _check(name: str, description: str, test_ids: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "status": "test_backed",
        "description": description,
        "test_ids": test_ids,
        "runtime_metadata_only": True,
    }


def _host_readiness_check() -> dict[str, Any]:
    return _check(
        "dynamic_host_readiness_audit_surface",
        "A dynamic runtime surface can launch the host command, audit installed hook files, and optionally smoke SessionStart.",
        [
            "tests/test_v5_host_readiness.py::test_runtime_host_readiness_runs_process_without_trusting_summaries",
            "tests/test_v5_host_readiness.py::test_runtime_host_readiness_cli_and_mcp",
        ],
    )


def _host_lifecycle_check() -> dict[str, Any]:
    return _check(
        "dynamic_host_lifecycle_audit_surface",
        "A dynamic runtime surface can run a host command and audit stdout/stderr plus hook trace deltas for lifecycle-event evidence.",
        [
            "tests/test_v5_host_readiness.py::test_runtime_host_lifecycle_probe_detects_trace_delta_and_hook_output",
            "tests/test_v5_host_readiness.py::test_runtime_host_lifecycle_probe_cli_and_mcp",
        ],
    )
