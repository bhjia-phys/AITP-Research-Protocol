"""MCP wrappers for AITP v5 hook installation."""

from __future__ import annotations

from brain.v5.adapters import build_adapter_packet
from brain.v5.hook_codex_install import install_codex_hooks_json
from brain.v5.hook_fixture_templates import install_codex_hook_fixture, install_opencode_hook_fixture
from brain.v5.hook_opencode_install import install_opencode_plugin_file
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_install_codex_hook_fixture(
    base: str,
    *,
    session_id: str,
    output_path: str = "",
    bridge_output_path: str = "",
    hooks_path: str = "",
) -> dict:
    ws = init_workspace(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="codex"))
    if hooks_path:
        installed = {
            "ok": True,
            **install_codex_hooks_json(
                hooks_path,
                packet["runtime_hook_installation"],
                packet["runtime_gate_protocols"],
                workspace_base=str(ws.base),
                session_id=session_id,
                bridge_path=bridge_output_path or None,
            ),
        }
    else:
        installed = {
            "ok": True,
            **install_codex_hook_fixture(
                output_path,
                packet["runtime_hook_installation"],
                packet["runtime_gate_protocols"],
                workspace_base=str(ws.base),
                session_id=session_id,
                bridge_path=bridge_output_path or None,
            ),
        }
    return require_valid_public_surface("codex_hook_installation", installed)


def aitp_v5_install_opencode_hook_fixture(
    base: str,
    *,
    session_id: str,
    output_path: str = "",
    bridge_output_path: str = "",
    plugin_path: str = "",
) -> dict:
    ws = init_workspace(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="opencode"))
    if plugin_path:
        installed = {
            "ok": True,
            **install_opencode_plugin_file(
                plugin_path,
                packet["runtime_hook_installation"],
                packet["runtime_gate_protocols"],
                workspace_base=str(ws.base),
                session_id=session_id,
                bridge_path=bridge_output_path or None,
            ),
        }
    else:
        installed = {
            "ok": True,
            **install_opencode_hook_fixture(
                output_path,
                packet["runtime_hook_installation"],
                packet["runtime_gate_protocols"],
                workspace_base=str(ws.base),
                session_id=session_id,
                bridge_path=bridge_output_path or None,
            ),
        }
    return require_valid_public_surface("opencode_hook_installation", installed)
