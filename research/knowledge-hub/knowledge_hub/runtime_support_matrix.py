from __future__ import annotations

from pathlib import Path
from typing import Any


def _doctor_verification_contract(runtime_id: str) -> dict[str, str]:
    return {
        "doctor_command": "aitp doctor",
        "doctor_json_command": "aitp doctor --json",
        "status_field": f"runtime_support_matrix.runtimes.{runtime_id}.status",
        "expected_status": "ready",
    }


def _full_convergence_command(workspace_root: str) -> str:
    return f'aitp migrate-local-install --workspace-root "{workspace_root}" --json'


def _repair_contract(
    *,
    status: str,
    command: str,
    doc_path: str,
    workspace_root: str,
    issue_hints: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "status": status,
        "command": command,
        "followup_command": "aitp doctor --json",
        "doc_path": doc_path,
        "convergence_command": _full_convergence_command(workspace_root),
        "issue_hints": issue_hints,
    }


def _codex_runtime_row(
    *,
    codex_path: str,
    codex_skill_status: dict[str, Any],
    workspace_root: str,
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
    repair_status = "none_required" if status == "ready" else "required"
    repair_command = "aitp install-agent --agent codex --scope user" if repair_status != "none_required" else ""
    issue_hints: list[dict[str, str]] = []
    for issue in issues:
        if issue in {"using_skill_missing", "runtime_skill_missing", "using_skill_stale", "runtime_skill_stale"}:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Run `aitp install-agent --agent codex --scope user` to refresh the Codex skill surfaces.",
                }
            )
        elif issue == "codex_cli_missing":
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Install Codex CLI and then rerun `aitp install-agent --agent codex --scope user`.",
                }
            )

    return {
        "display_name": "Codex",
        "status": status,
        "maturity_class": "baseline",
        "bootstrap_mode": "native_skill_discovery",
        "preferred_entry": "native `using-aitp` skill discovery",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "verification": _doctor_verification_contract("codex"),
        "remediation": _repair_contract(
            status=repair_status,
            command=repair_command,
            doc_path=".codex/INSTALL.md",
            workspace_root=workspace_root,
            issue_hints=issue_hints,
        ),
        "surface_checks": {
            "codex_cli_path": codex_path,
            **codex_skill_status,
        },
    }


def _claude_runtime_row(
    *,
    claude_hook_status: dict[str, Any],
    legacy_claude_commands: list[str],
    workspace_root: str,
) -> dict[str, Any]:
    issues: list[str] = []
    required_keys = (
        "using_skill",
        "runtime_skill",
        "session_start_hook",
        "session_start_python_hook",
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
        "session_start_python_hook_matches_canonical",
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
    if status == "ready":
        notes.append("Windows-native SessionStart can run through the Python hook sidecar without requiring bash.")
    if status != "ready":
        notes.append("Fallback remains `aitp session-start \"<task>\"` until SessionStart is converged.")
    repair_status = "none_required" if status == "ready" else "required"
    repair_command = "aitp install-agent --agent claude-code --scope user" if repair_status != "none_required" else ""
    issue_hints: list[dict[str, str]] = []
    for issue in issues:
        if issue == "legacy_claude_commands_present":
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Remove legacy `~/.claude/commands/aitp*.md` bundles or run the full migration command.",
                }
            )
        else:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Run `aitp install-agent --agent claude-code --scope user` to refresh Claude Code SessionStart assets.",
                }
            )

    return {
        "display_name": "Claude Code",
        "status": status,
        "maturity_class": "parity_target",
        "bootstrap_mode": "session_start_hook",
        "preferred_entry": "Claude SessionStart bootstrap",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "verification": _doctor_verification_contract("claude_code"),
        "remediation": _repair_contract(
            status=repair_status,
            command=repair_command,
            doc_path="docs/INSTALL_CLAUDE_CODE.md",
            workspace_root=workspace_root,
            issue_hints=issue_hints,
        ),
        "surface_checks": {
            **claude_hook_status,
            "legacy_command_paths": legacy_claude_commands,
        },
    }


def _opencode_runtime_row(
    *,
    opencode_status: dict[str, Any],
    workspace_root: str,
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
    if preferred_ready:
        repair_status = "none_required"
    elif compatibility_ready:
        repair_status = "recommended"
    else:
        repair_status = "required"
    repair_command = ""
    if repair_status == "recommended" or not preferred_ready:
        repair_command = _full_convergence_command(workspace_root)
    issue_hints: list[dict[str, str]] = []
    for issue in issues:
        if issue in {
            "opencode_config_missing",
            "canonical_aitp_plugin_entry_missing",
            "noncanonical_aitp_plugin_entries_present",
        }:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": f"Run `{_full_convergence_command(workspace_root)}` to enable the canonical OpenCode plugin path.",
                }
            )
        elif issue in {"opencode_config_invalid", "opencode_plugin_list_invalid"}:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Repair `~/.config/opencode/opencode.json` so it contains valid JSON with a `plugin` array, then rerun the convergence command.",
                }
            )
        elif issue in {
            "workspace_plugin_missing",
            "workspace_using_skill_missing",
            "workspace_runtime_skill_missing",
            "workspace_plugin_stale",
            "workspace_using_skill_stale",
            "workspace_runtime_skill_stale",
        }:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": f'If you still want workspace-local compatibility assets, run `aitp install-agent --agent opencode --scope project --target-root "{workspace_root}"`.',
                }
            )

    return {
        "display_name": "OpenCode",
        "status": status,
        "maturity_class": "parity_target",
        "bootstrap_mode": "plugin_transform_injection",
        "preferred_entry": "OpenCode plugin bootstrap",
        "fallback_entry": 'aitp session-start "<task>"',
        "issues": issues,
        "notes": notes,
        "verification": _doctor_verification_contract("opencode"),
        "remediation": _repair_contract(
            status=repair_status,
            command=repair_command,
            doc_path="docs/INSTALL_OPENCODE.md",
            workspace_root=workspace_root,
            issue_hints=issue_hints,
        ),
        "surface_checks": {
            **opencode_status,
        },
    }


def _openclaw_runtime_row(
    *,
    openclaw_path: str,
    mcporter_path: str,
    workspace_root: str,
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
    repair_status = "none_required" if status == "ready" else "required"
    repair_command = "aitp install-agent --agent openclaw --scope user" if repair_status != "none_required" else ""
    issue_hints: list[dict[str, str]] = []
    for issue in issues:
        if issue in {"openclaw_command_missing", "mcporter_missing"}:
            issue_hints.append(
                {
                    "issue": issue,
                    "hint": "Install OpenClaw and mcporter, then run `aitp install-agent --agent openclaw --scope user` if you want the specialized lane.",
                }
            )

    return {
        "display_name": "OpenClaw",
        "status": status,
        "maturity_class": "specialized_lane",
        "bootstrap_mode": "bounded_loop_entrypoint",
        "preferred_entry": 'aitp loop --topic-slug <topic_slug> --human-request "<task>"',
        "fallback_entry": 'aitp bootstrap "<task>" then `aitp loop ...`',
        "issues": issues,
        "notes": notes,
        "verification": _doctor_verification_contract("openclaw"),
        "remediation": _repair_contract(
            status=repair_status,
            command=repair_command,
            doc_path="docs/INSTALL_OPENCLAW.md",
            workspace_root=workspace_root,
            issue_hints=issue_hints,
        ),
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
    workspace_root: str,
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
            workspace_root=workspace_root,
        ),
        "claude_code": _claude_runtime_row(
            claude_hook_status=claude_hook_status,
            legacy_claude_commands=legacy_command_rows,
            workspace_root=workspace_root,
        ),
        "opencode": _opencode_runtime_row(
            opencode_status=opencode_status,
            workspace_root=workspace_root,
        ),
        "openclaw": _openclaw_runtime_row(
            openclaw_path=str(openclaw_path or ""),
            mcporter_path=str(mcporter_path or ""),
            workspace_root=workspace_root,
        ),
    }
    return {
        "baseline_runtime": "codex",
        "parity_targets": ["claude_code", "opencode"],
        "specialized_lanes": ["openclaw"],
        "runtimes": runtimes,
    }
