from __future__ import annotations

from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_versioned_matrix_characterizes_installed_automatic_events_from_real_owners():
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability_matrix

    matrix = host_lifecycle_capability_matrix()

    assert matrix.schema_version == "host_lifecycle_capability_matrix/v1"
    assert tuple(matrix.hosts) == ("claude_code", "kimi_code", "codex", "opencode")

    claude = matrix.hosts["claude_code"]
    kimi = matrix.hosts["kimi_code"]
    codex = matrix.hosts["codex"]
    opencode = matrix.hosts["opencode"]

    assert [(event.logical_event, event.native_event) for event in claude.automatic_events] == [
        ("session_start", "SessionStart"),
        ("pre_tool", "PreToolUse"),
        ("post_tool", "PostToolUse"),
    ]
    assert [(event.logical_event, event.native_event) for event in kimi.automatic_events] == [
        ("session_start", "SessionStart"),
        ("pre_tool", "PreToolUse"),
        ("post_tool", "PostToolUse"),
    ]
    assert [(event.logical_event, event.native_event) for event in codex.automatic_events] == [
        ("pre_tool", "PreToolUse"),
        ("post_tool", "PostToolUse"),
    ]
    assert [(event.logical_event, event.native_event) for event in opencode.automatic_events] == [
        ("pre_tool", "tool.execute.before"),
        ("post_tool", "tool.execute.after"),
    ]

    claude_owner = (_REPO_ROOT / "brain/v5/hook_install_templates.py").read_text(encoding="utf-8")
    kimi_owner = (_REPO_ROOT / "brain/v5/hook_kimi_install.py").read_text(encoding="utf-8")
    codex_owner = (_REPO_ROOT / "brain/v5/hook_codex_install.py").read_text(encoding="utf-8")
    opencode_owner = (_REPO_ROOT / "brain/v5/hook_opencode_install.py").read_text(encoding="utf-8")
    opencode_template = (_REPO_ROOT / "deploy/templates/opencode/aitp-plugin.js").read_text(encoding="utf-8")

    for event_name in ("SessionStart", "PreToolUse", "PostToolUse"):
        assert event_name in claude_owner
        assert event_name in kimi_owner
    assert "SessionStart" not in codex_owner
    assert "PreToolUse" in codex_owner and "PostToolUse" in codex_owner
    assert "tool.execute.before" in opencode_owner and "tool.execute.after" in opencode_owner
    assert "experimental.chat.system.transform" in opencode_template
    assert opencode.legacy_injection_conflicts == (
        "experimental.chat.system.transform: stale full-skill injection; not a lifecycle start capability",
    )


def test_matrix_keeps_unavailable_lifecycle_events_and_explicit_fallbacks_honest():
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability, host_lifecycle_capability_matrix

    matrix = host_lifecycle_capability_matrix()
    codex = host_lifecycle_capability("codex")
    opencode = host_lifecycle_capability("opencode")

    assert {"prompt_submit", "session_end"} <= set(codex.unsupported_events)
    assert "session_start" in codex.unsupported_events
    assert codex.fallback_operations["first_research_prompt"] == "aitp_v5_codex_enter"
    assert codex.fallback_operations["closeout"] == "aitp_v5_codex_closeout"
    assert "prompt_submit" in opencode.unsupported_events
    assert "session_end" in opencode.unsupported_events
    assert opencode.fallback_operations["closeout"] == "apply_session_closeout"
    assert "system_transform" not in {event.logical_event for event in opencode.automatic_events}
    assert all("session_end" not in {event.logical_event for event in host.automatic_events} for host in matrix.hosts.values())

    with pytest.raises(ValueError, match="unsupported host"):
        host_lifecycle_capability("unknown-host")


def test_matrix_records_current_output_trace_failure_and_timeout_contracts_without_dispatching():
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability

    claude = host_lifecycle_capability("claude_code")
    codex = host_lifecycle_capability("codex")
    opencode = host_lifecycle_capability("opencode")

    assert claude.event("session_start").output_contract == "suppressed_continue_with_compact_workspace_refresh"
    assert claude.event("post_tool").trace_contract == "append_hook_trace_event"
    assert claude.event("pre_tool").failure_contract == "hook_failure_propagates_to_host"
    assert claude.event("pre_tool").timeout_contract == "no_owner_timeout"
    assert codex.event("pre_tool").output_contract == "pre_tool_policy_decision"
    assert codex.event("post_tool").trace_contract == "append_hook_trace_event"
    assert opencode.event("pre_tool").failure_contract == "nonzero_or_block_throws_to_host"
    assert opencode.event("post_tool").failure_contract == "failure_is_logged_and_suppressed"
    assert opencode.event("pre_tool").timeout_contract == "no_owner_timeout"
