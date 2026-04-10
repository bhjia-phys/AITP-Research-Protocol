from __future__ import annotations

from pathlib import Path
from typing import Any


def _codex_runtime_row(
    *,
    codex_path: str,
    codex_skill_status: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    using_present = bool(codex_skill_status.get("using_skill_present"))
    runtime_present = bool(codex_skill_status.get("runtime_skill_present"))
    using_matches = bool(codex_skill_status.get("using_skill_matches_canonical"))
    runtime_matches = bool(codex_skill_status.get("runtime_skill_matches_canonical"))

    if not using_present:
        issues.append("using_skill_missing")
    if not runtime_present:
        issues.append("runtime_skill_missing")
    if using_present and not using_matches:
        issues.append("using_skill_stale")
    if runtime_present and not runtime_matches:
        issues.append("runtime_skill_stale")
    if not codex_path:
        issues.append("codex_cli_missing")

    if not using_present and not runtime_present:
        status = "missing"
    elif "using_skill_stale" in issues or "runtime_skill_stale" in issues:
        status = "stale"
    elif issues:
        status = "partial"
    else:
        status = "ready"

    notes = [
        "Current cleanest end-to-end AITP runtime path.",
        "This is the baseline lane that deeper execution still assumes most often.",
    ]
    if status != "ready":
        notes.append("Use `aitp session-start \"<task>\"` while repairing the preferred bootstrap surface.")

    return {
        "display_name": "Codex",
        "status": status,
        "maturity_class": "baseline",
        "bootstrap_mode": "native_skill_discovery",
        "preferred_entry": "native `using-aitp` skill discovery",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "surface_checks": {
            "codex_cli_path": codex_path,
            **codex_skill_status,
        },
    }


def _claude_runtime_row(
    *,
    claude_hook_status: dict[str, Any],
    legacy_claude_commands: list[str],
) -> dict[str, Any]:
    issues: list[str] = []
    required_keys = (
        "using_skill",
        "runtime_skill",
        "session_start_hook",
        "hook_wrapper",
        "hooks_manifest",
        "settings",
    )
    present_flags = [bool(claude_hook_status.get(key)) for key in required_keys]
    if not all(present_flags):
        for key in required_keys:
            if not claude_hook_status.get(key):
                issues.append(f"{key}_missing")
    match_keys = (
        "using_skill_matches_canonical",
        "runtime_skill_matches_canonical",
        "session_start_hook_matches_canonical",
        "hook_wrapper_matches_canonical",
        "hooks_manifest_matches_canonical",
    )
    for key in match_keys:
        if claude_hook_status.get(key) is False:
            issues.append(f"{key}_stale")
    if claude_hook_status.get("settings") and not claude_hook_status.get("settings_has_expected_session_start_command"):
        issues.append("settings_session_start_command_mismatch")
    if legacy_claude_commands:
        issues.append("legacy_claude_commands_present")

    if not any(present_flags):
        status = "missing"
    elif any(issue.endswith("_stale") or issue.endswith("_mismatch") for issue in issues) or legacy_claude_commands:
        status = "stale"
    elif all(present_flags):
        status = "ready"
    else:
        status = "partial"

    notes = [
        "Front-door parity target; current bootstrap is SessionStart plus `using-aitp`.",
        "Deep execution maturity still trails the Codex baseline.",
    ]
    if status != "ready":
        notes.append("Fallback remains `aitp session-start \"<task>\"` until SessionStart is converged.")

    return {
        "display_name": "Claude Code",
        "status": status,
        "maturity_class": "parity_target",
        "bootstrap_mode": "session_start_hook",
        "preferred_entry": "Claude SessionStart bootstrap",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "surface_checks": {
            **claude_hook_status,
            "legacy_command_paths": legacy_claude_commands,
        },
    }


def _opencode_runtime_row(
    *,
    opencode_status: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    config_exists = bool(opencode_status.get("config_exists"))
    config_parse_ok = bool(opencode_status.get("config_parse_ok"))
    plugin_list_present = bool(opencode_status.get("plugin_list_present"))
    plugin_list_valid = bool(opencode_status.get("plugin_list_valid"))
    canonical_plugin_entry_present = bool(opencode_status.get("canonical_plugin_entry_present"))
    noncanonical_entries = list(opencode_status.get("noncanonical_aitp_plugin_entries") or [])
    workspace_plugin_present = bool(opencode_status.get("workspace_plugin_present"))
    workspace_using_skill_present = bool(opencode_status.get("workspace_using_skill_present"))
    workspace_runtime_skill_present = bool(opencode_status.get("workspace_runtime_skill_present"))
    workspace_plugin_matches = bool(opencode_status.get("workspace_plugin_matches_canonical"))
    workspace_using_skill_matches = bool(opencode_status.get("workspace_using_skill_matches_canonical"))
    workspace_runtime_skill_matches = bool(opencode_status.get("workspace_runtime_skill_matches_canonical"))

    compatibility_any_present = workspace_plugin_present or workspace_using_skill_present or workspace_runtime_skill_present
    preferred_ready = config_parse_ok and plugin_list_valid and canonical_plugin_entry_present
    compatibility_ready = (
        workspace_plugin_present
        and workspace_using_skill_present
        and workspace_runtime_skill_present
        and workspace_plugin_matches
        and workspace_using_skill_matches
        and workspace_runtime_skill_matches
    )

    if not compatibility_ready:
        if not config_exists:
            issues.append("opencode_config_missing")
        elif not config_parse_ok:
            issues.append("opencode_config_invalid")
        elif plugin_list_present and not plugin_list_valid:
            issues.append("opencode_plugin_list_invalid")
        elif config_parse_ok and not plugin_list_present:
            issues.append("opencode_plugin_list_missing")

        if noncanonical_entries:
            issues.append("noncanonical_aitp_plugin_entries_present")
        if config_parse_ok and plugin_list_valid and not canonical_plugin_entry_present and not noncanonical_entries:
            issues.append("canonical_aitp_plugin_entry_missing")

    if not preferred_ready:
        if compatibility_any_present and not workspace_plugin_present:
            issues.append("workspace_plugin_missing")
        if compatibility_any_present and not workspace_using_skill_present:
            issues.append("workspace_using_skill_missing")
        if compatibility_any_present and not workspace_runtime_skill_present:
            issues.append("workspace_runtime_skill_missing")
        if workspace_plugin_present and not workspace_plugin_matches:
            issues.append("workspace_plugin_stale")
        if workspace_using_skill_present and not workspace_using_skill_matches:
            issues.append("workspace_using_skill_stale")
        if workspace_runtime_skill_present and not workspace_runtime_skill_matches:
            issues.append("workspace_runtime_skill_stale")

    stale_signals = any(
        issue in {
            "opencode_config_invalid",
            "opencode_plugin_list_invalid",
            "noncanonical_aitp_plugin_entries_present",
            "workspace_plugin_stale",
            "workspace_using_skill_stale",
            "workspace_runtime_skill_stale",
        }
        for issue in issues
    )

    if preferred_ready or compatibility_ready:
        status = "ready"
    elif stale_signals:
        status = "stale"
    elif compatibility_any_present or config_exists:
        status = "partial"
    else:
        status = "missing"

    notes = [
        "Front-door parity target; current bootstrap is the OpenCode plugin plus `using-aitp` injection.",
        "Deep execution maturity still trails the Codex baseline.",
    ]
    if preferred_ready:
        notes.append("Preferred plugin-config bootstrap is converged.")
    elif compatibility_ready:
        notes.append("Workspace-local compatibility bootstrap is present even though the preferred config path is not.")
    if status != "ready":
        notes.append("Fallback remains `aitp session-start \"<task>\"` until the plugin bootstrap is enabled.")

    return {
        "display_name": "OpenCode",
        "status": status,
        "maturity_class": "parity_target",
        "bootstrap_mode": "plugin_transform_injection",
        "preferred_entry": "OpenCode plugin bootstrap",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "surface_checks": {
            **opencode_status,
        },
    }


def _openclaw_runtime_row(
    *,
    openclaw_path: str,
    mcporter_path: str,
) -> dict[str, Any]:
    issues: list[str] = []
    if not openclaw_path:
        issues.append("openclaw_command_missing")
    if not mcporter_path:
        issues.append("mcporter_missing")

    status = "ready" if openclaw_path else "missing"
    notes = [
        "Specialized bounded-autonomy lane rather than the default conversational baseline.",
        "Use this when you explicitly want loop-style execution rather than front-door parity with Codex.",
    ]
    if status != "ready":
        notes.append("Primary entry remains `aitp install-agent --agent openclaw` followed by `aitp loop ...`.")

    return {
        "display_name": "OpenClaw",
        "status": status,
        "maturity_class": "specialized_lane",
        "bootstrap_mode": "bounded_loop_entrypoint",
        "preferred_entry": 'aitp loop --topic-slug <topic_slug> --human-request "<task>"',
        "fallback_entry": 'aitp bootstrap "<task>" then `aitp loop ...`',
        "issues": issues,
        "notes": notes,
        "surface_checks": {
            "openclaw_command_path": openclaw_path,
            "mcporter_path": mcporter_path,
        },
    }


def build_runtime_support_matrix(
    *,
    codex_path: str | None,
    openclaw_path: str | None,
    mcporter_path: str | None,
    codex_skill_status: dict[str, Any],
    claude_hook_status: dict[str, Any],
    legacy_claude_commands: list[Path | str],
    opencode_status: dict[str, Any],
) -> dict[str, Any]:
    legacy_command_rows = [str(path) for path in legacy_claude_commands]
    runtimes = {
        "codex": _codex_runtime_row(
            codex_path=str(codex_path or ""),
            codex_skill_status=codex_skill_status,
        ),
        "claude_code": _claude_runtime_row(
            claude_hook_status=claude_hook_status,
            legacy_claude_commands=legacy_command_rows,
        ),
        "opencode": _opencode_runtime_row(
            opencode_status=opencode_status,
        ),
        "openclaw": _openclaw_runtime_row(
            openclaw_path=str(openclaw_path or ""),
            mcporter_path=str(mcporter_path or ""),
        ),
    }
    return {
        "baseline_runtime": "codex",
        "parity_targets": ["claude_code", "opencode"],
        "specialized_lanes": ["openclaw"],
        "runtimes": runtimes,
    }
