"""MCP wrappers for AITP v5 hook installation."""

from __future__ import annotations

from brain.v5.hook_codex_install import install_codex_hooks_json
from brain.v5.hook_fixture_templates import install_codex_hook_fixture, install_opencode_hook_fixture
from brain.v5.hook_install_request import prepare_hook_install_request
from brain.v5.hook_opencode_install import install_opencode_plugin_file
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_install_codex_hook_fixture(
    base: str,
    *,
    session_id: str = "",
    routing_mode: str = "",
    project_root: str = "",
    output_path: str = "",
    bridge_output_path: str = "",
    hooks_path: str = "",
) -> dict:
    ws = init_workspace(base)
    request = prepare_hook_install_request(
        ws,
        runtime="codex",
        routing_mode=routing_mode,
        session_id=session_id,
        project_root=project_root,
    )
    if hooks_path:
        installed = {
            "ok": True,
            **install_codex_hooks_json(
                hooks_path,
                request.installation,
                request.gate_protocols,
                workspace_base=str(ws.base),
                routing=request.routing,
                project_root=request.project_root,
                bridge_path=bridge_output_path or None,
            ),
        }
    else:
        installed = {
            "ok": True,
            **install_codex_hook_fixture(
                output_path,
                request.installation,
                request.gate_protocols,
                workspace_base=str(ws.base),
                routing=request.routing,
                project_root=request.project_root,
                bridge_path=bridge_output_path or None,
            ),
        }
    return require_valid_public_surface("codex_hook_installation", installed)


def aitp_v5_install_opencode_hook_fixture(
    base: str,
    *,
    session_id: str = "",
    routing_mode: str = "",
    project_root: str = "",
    output_path: str = "",
    bridge_output_path: str = "",
    plugin_path: str = "",
) -> dict:
    ws = init_workspace(base)
    request = prepare_hook_install_request(
        ws,
        runtime="opencode",
        routing_mode=routing_mode,
        session_id=session_id,
        project_root=project_root,
    )
    if plugin_path:
        installed = {
            "ok": True,
            **install_opencode_plugin_file(
                plugin_path,
                request.installation,
                request.gate_protocols,
                workspace_base=str(ws.base),
                routing=request.routing,
                project_root=request.project_root,
                bridge_path=bridge_output_path or None,
            ),
        }
    else:
        installed = {
            "ok": True,
            **install_opencode_hook_fixture(
                output_path,
                request.installation,
                request.gate_protocols,
                workspace_base=str(ws.base),
                routing=request.routing,
                project_root=request.project_root,
                bridge_path=bridge_output_path or None,
            ),
        }
    return require_valid_public_surface("opencode_hook_installation", installed)
