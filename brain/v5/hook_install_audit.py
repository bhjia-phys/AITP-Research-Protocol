"""Read-only audit helpers for installed AITP v5 runtime hooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_STATUS_ORDER = {"installed": 0, "partial": 1, "missing": 2, "conflict": 3}


def audit_hook_installation(
    ws: Any,
    *,
    runtime: str,
    settings_path: str = "",
    plugin_path: str = "",
    output_path: str = "",
) -> dict[str, Any]:
    """Inspect runtime hook files without treating them as kernel state."""

    normalized = _normalize_runtime(runtime)
    finding = _audit_runtime_path(
        normalized,
        workspace_base=str(ws.base),
        settings_path=settings_path,
        plugin_path=plugin_path,
        output_path=output_path,
    )
    required_actions = [] if finding["status"] == "installed" else [_required_action(normalized, finding)]
    return {
        "kind": "runtime_hook_installation_audit",
        "runtime": normalized,
        "truth_source": "runtime_files",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "status": finding["status"],
        "checked_paths": [finding["path"]],
        "findings": [finding],
        "required_actions": required_actions,
    }


def _audit_runtime_path(
    runtime: str,
    *,
    workspace_base: str,
    settings_path: str,
    plugin_path: str,
    output_path: str,
) -> dict[str, Any]:
    if runtime == "codex":
        if settings_path:
            return _audit_text_path(
                settings_path,
                expected=[
                    ("PreToolUse pre-tool runner", ["PreToolUse", "hooks/aitp_v5_adapter_event_runner.py", "pre-tool", "--bridge-path", workspace_base]),
                    ("PostToolUse post-tool runner", ["PostToolUse", "hooks/aitp_v5_adapter_event_runner.py", "post-tool", workspace_base]),
                ],
            )
        return _audit_text_path(
            output_path or str(Path(workspace_base) / ".codex" / "AITP_V5_HOOKS.json"),
            expected=[
                ("fixture pre-tool runner", ["pre_tool", "hooks/aitp_v5_adapter_event_runner.py", "pre-tool", "--bridge-path", workspace_base]),
                ("fixture post-tool runner", ["post_tool", "hooks/aitp_v5_adapter_event_runner.py", "post-tool", workspace_base]),
            ],
        )
    if runtime == "claude_code":
        return _audit_text_path(
            settings_path or str(Path(workspace_base) / ".claude" / "settings.local.json"),
            expected=[
                ("PreToolUse Claude hook", ["PreToolUse", "hooks/aitp_v5_claude_hook.py", "pre-tool", workspace_base]),
                ("PostToolUse Claude hook", ["PostToolUse", "hooks/aitp_v5_claude_hook.py", "post-tool", workspace_base]),
            ],
        )
    if runtime == "opencode":
        if plugin_path:
            return _audit_text_path(
                plugin_path,
                expected=[
                    ("tool.execute.before pre-tool runner", ["tool.execute.before", "hooks/aitp_v5_adapter_event_runner.py", "pre-tool", "--bridge-path", workspace_base]),
                    ("tool.execute.after post-tool runner", ["tool.execute.after", "hooks/aitp_v5_adapter_event_runner.py", "post-tool", workspace_base]),
                ],
            )
        return _audit_text_path(
            output_path or str(Path(workspace_base) / ".opencode" / "AITP_V5_PLUGIN_HOOKS.json"),
            expected=[
                ("fixture pre-tool runner", ["plugin_hooks", "pre_tool", "hooks/aitp_v5_adapter_event_runner.py", "pre-tool", "--bridge-path", workspace_base]),
                ("fixture post-tool runner", ["plugin_hooks", "post_tool", "hooks/aitp_v5_adapter_event_runner.py", "post-tool", workspace_base]),
            ],
        )
    raise ValueError(f"unsupported runtime: {runtime}")


def _audit_text_path(path: str, *, expected: list[tuple[str, list[str]]]) -> dict[str, Any]:
    target = Path(path)
    expected_labels = [label for label, _ in expected]
    if not target.exists():
        return _finding(target, False, "missing", expected_labels, [], ["file does not exist"])
    text = target.read_text(encoding="utf-8")
    observed = [label for label, tokens in expected if all(_contains(text, token) for token in tokens)]
    if len(observed) == len(expected):
        status = "installed"
        messages: list[str] = []
    elif observed:
        status = "partial"
        messages = ["some AITP lifecycle hooks are missing"]
    else:
        status = "conflict"
        messages = ["file exists but does not contain AITP v5 lifecycle hooks"]
    return _finding(target, True, status, expected_labels, observed, messages)


def _finding(
    path: Path,
    exists: bool,
    status: str,
    expected: list[str],
    observed: list[str],
    messages: list[str],
) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": exists,
        "status": status,
        "expected": expected,
        "observed": observed,
        "messages": messages,
        "runtime_metadata_only": True,
    }


def _contains(text: str, token: str) -> bool:
    escaped = json.dumps(token, ensure_ascii=False)[1:-1]
    return token in text or escaped in text


def _required_action(runtime: str, finding: dict[str, Any]) -> str:
    if finding["status"] == "missing":
        return f"install AITP v5 {runtime} hooks at {finding['path']}"
    if finding["status"] == "partial":
        return f"reinstall AITP v5 {runtime} hooks to add missing lifecycle entries"
    return f"inspect {finding['path']} before overwriting non-AITP hook configuration"


def _normalize_runtime(runtime: str) -> str:
    normalized = runtime.strip().lower().replace("-", "_")
    if normalized == "claude":
        return "claude_code"
    if normalized in {"codex", "claude_code", "opencode"}:
        return normalized
    raise ValueError(f"unsupported runtime: {runtime}")
