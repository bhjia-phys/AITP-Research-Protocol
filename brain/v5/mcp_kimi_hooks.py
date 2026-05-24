"""Kimi Code hook MCP wrappers for AITP v5."""

from __future__ import annotations

from pathlib import Path

from brain.v5.adapters import build_adapter_packet
from brain.v5.hook_kimi_install import install_kimi_code_hook_config, write_kimi_code_hook_config
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_write_kimi_code_hook_config(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="kimi_code"))
    config = {"ok": True, **write_kimi_code_hook_config(
        output_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("kimi_code_hook_config", config)


def aitp_v5_install_kimi_code_hook_config(base: str, *, session_id: str, settings_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="kimi_code"))
    installed = {"ok": True, **install_kimi_code_hook_config(
        settings_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("kimi_code_hook_installation", installed)
