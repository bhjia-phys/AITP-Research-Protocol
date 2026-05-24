"""Kimi Code hook configuration installers for AITP v5."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


_KIMI_BEGIN_MARKER = "# BEGIN AITP V5 KIMI HOOKS"
_KIMI_END_MARKER = "# END AITP V5 KIMI HOOKS"


def write_kimi_code_hook_config(
    path: str | Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    """Write standalone Kimi Code hook TOML derived from hook metadata."""

    config_path = Path(path)
    payload = _kimi_config_payload(
        config_path,
        installation,
        workspace_base=workspace_base,
        session_id=session_id,
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(payload["config_text"], encoding="utf-8")
    return payload


def install_kimi_code_hook_config(
    path: str | Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    """Merge AITP v5 Kimi hooks into an existing TOML config without clobbering it."""

    config_path = Path(path)
    generated = _kimi_config_payload(
        config_path,
        installation,
        workspace_base=workspace_base,
        session_id=session_id,
    )
    created = not config_path.exists()
    existing_text = "" if created else config_path.read_text(encoding="utf-8")
    merged_text, changed = _merge_kimi_config_text(existing_text, generated["config_text"])
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(merged_text, encoding="utf-8")
    return {
        **generated,
        "kind": "kimi_code_hook_installation",
        "config_kind": generated["kind"],
        "created": created,
        "merged": True,
        "added_hooks": 2 if changed else 0,
        "config_text": merged_text,
    }


def _kimi_config_payload(
    config_path: Path,
    installation: dict[str, Any],
    *,
    workspace_base: str,
    session_id: str,
) -> dict[str, Any]:
    hook_script = (Path(__file__).resolve().parents[2] / "hooks" / "aitp_v5_kimi_hook.py").as_posix()
    python_exe = Path(sys.executable).as_posix()
    command_base = (
        f'"{python_exe}" "{hook_script}" {{command}} '
        f'--base "{workspace_base}" --session-id {session_id}'
    )
    events = [
        {
            "hook_event_name": "PreToolUse",
            "matcher": "*",
            "protocol_hook": "pre_tool",
            "command": command_base.format(command="pre-tool"),
        },
        {
            "hook_event_name": "PostToolUse",
            "matcher": "*",
            "protocol_hook": "post_tool",
            "command": command_base.format(command="post-tool"),
        },
    ]
    return {
        "kind": "kimi_code_hook_config",
        "runtime": "kimi_code",
        "source_protocol_field": "runtime_hook_installation",
        "installation_mode": installation["installation_mode"],
        "native_installer_available": installation["native_installer_available"],
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_trace_events": True,
        "path": str(config_path),
        "events": events,
        "config_text": _kimi_hooks_toml(events),
    }


def _kimi_hooks_toml(events: list[dict[str, str]]) -> str:
    lines = [_KIMI_BEGIN_MARKER]
    for event in events:
        lines.extend(
            [
                "[[hooks]]",
                f"event = {_toml_string(event['hook_event_name'])}",
                f"matcher = {_toml_string(event['matcher'])}",
                f"command = {_toml_string(event['command'])}",
                "",
            ]
        )
    lines.append(_KIMI_END_MARKER)
    lines.append("")
    return "\n".join(lines)


def _merge_kimi_config_text(existing_text: str, generated_block: str) -> tuple[str, bool]:
    trimmed_existing = existing_text.rstrip()
    without_old = _remove_marked_kimi_block(trimmed_existing)
    merged = generated_block if not without_old.strip() else without_old.rstrip() + "\n\n" + generated_block
    return merged, merged.rstrip() != trimmed_existing.rstrip()


def _remove_marked_kimi_block(text: str) -> str:
    begin = text.find(_KIMI_BEGIN_MARKER)
    if begin == -1:
        return text
    end = text.find(_KIMI_END_MARKER, begin)
    if end == -1:
        return text
    end += len(_KIMI_END_MARKER)
    return (text[:begin] + text[end:]).strip()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
