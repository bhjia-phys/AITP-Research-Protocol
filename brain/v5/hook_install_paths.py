"""Runtime hook installation path discovery for AITP v5."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def discover_hook_install_paths(ws: Any) -> dict[str, Any]:
    """Return workspace-local hook install targets without touching them."""

    base = Path(ws.base)
    entries = [
        _entry(
            base,
            runtime="codex",
            preferred=(".codex/hooks.json", "--settings"),
            alternates=[(".codex/AITP_V5_HOOKS.json", "--output")],
        ),
        _entry(
            base,
            runtime="claude_code",
            preferred=(".claude/settings.local.json", "--settings"),
            alternates=[],
            cli_runtime="claude-code",
        ),
        _entry(
            base,
            runtime="kimi_code",
            preferred=(".kimi/config.toml", "--settings"),
            alternates=[(".kimi/AITP_V5_HOOKS.toml", "--output")],
            cli_runtime="kimi-code",
        ),
        _entry(
            base,
            runtime="opencode",
            preferred=(".opencode/plugins/aitp-v5.js", "--plugin"),
            alternates=[(".opencode/AITP_V5_PLUGIN_HOOKS.json", "--output")],
        ),
    ]
    return {
        "kind": "runtime_hook_installation_paths",
        "truth_source": "workspace_conventions",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "workspace_base": str(base),
        "paths": entries,
    }


def _entry(
    base: Path,
    *,
    runtime: str,
    preferred: tuple[str, str],
    alternates: list[tuple[str, str]],
    cli_runtime: str | None = None,
) -> dict[str, Any]:
    runtime_arg = cli_runtime or runtime
    preferred_path, preferred_arg = preferred
    return {
        "runtime": runtime,
        "preferred": _path_payload(base, preferred_path, preferred_arg),
        "alternates": [_path_payload(base, path, arg) for path, arg in alternates],
        "install_command": _command(base, "install-hooks", runtime_arg, preferred_arg, preferred_path),
        "audit_command": _command(base, "install-audit", runtime_arg, preferred_arg, preferred_path),
        "runtime_metadata_only": True,
    }


def _path_payload(base: Path, relative_path: str, install_arg: str) -> dict[str, str]:
    return {
        "path": str(base / Path(relative_path)),
        "relative_path": relative_path,
        "install_arg": install_arg,
    }


def _command(base: Path, command: str, runtime: str, install_arg: str, relative_path: str) -> str:
    session = " <session-id>" if command == "install-hooks" else ""
    return f"aitp-v5 --base {base} adapter {command} {runtime}{session} {install_arg} {relative_path}"
