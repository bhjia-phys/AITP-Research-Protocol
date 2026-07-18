"""Shared request preparation for route-aware hook installers."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.adapter_protocols import build_adapter_protocols, supported_runtimes
from brain.v5.hook_install_templates import build_runtime_hook_installation
from brain.v5.hook_routing_mode import HookRoutingMode, normalize_hook_routing_mode
from brain.v5.workspace import get_session_binding


@dataclass(frozen=True)
class HookInstallRequest:
    runtime: str
    routing: HookRoutingMode
    project_root: str
    installation: dict
    gate_protocols: dict


def prepare_hook_install_request(
    ws,
    *,
    runtime: str,
    routing_mode: str = "",
    session_id: str = "",
    project_root: str = "",
) -> HookInstallRequest:
    normalized_runtime = runtime.strip().lower().replace("-", "_")
    if normalized_runtime not in supported_runtimes():
        raise ValueError(f"unsupported hook runtime: {runtime}")
    routing = normalize_hook_routing_mode(
        routing_mode,
        session_id,
        legacy_positional=bool(session_id and not routing_mode),
    )
    if routing.pinned_session_id:
        get_session_binding(ws, routing.pinned_session_id)
    resolved_project_root = project_root.strip()
    if not resolved_project_root:
        if not routing.legacy_pinned:
            raise ValueError("dynamic and explicit pinned installation require project_root")
        resolved_project_root = str(ws.base)
    protocols = build_adapter_protocols()
    return HookInstallRequest(
        runtime=normalized_runtime,
        routing=routing,
        project_root=resolved_project_root,
        installation=build_runtime_hook_installation(
            normalized_runtime,
            protocols["runtime_hook_protocols"],
        ),
        gate_protocols=protocols["runtime_gate_protocols"],
    )


__all__ = ["HookInstallRequest", "prepare_hook_install_request"]
