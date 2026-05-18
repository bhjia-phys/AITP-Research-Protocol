"""Canonical runtime entrypoint names for AITP v5 adapters."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_RUNTIME_ENTRYPOINTS = {
    "public_surfaces": {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    },
    "adapter_registry": {
        "cli": "aitp-v5 adapter registry",
        "mcp": "aitp_v5_get_adapter_protocol_registry",
        "surface": "adapter_protocol_registry",
    },
    "adapter_packet": {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    "execution_brief": {
        "cli": "aitp-v5 brief <session-id>",
        "mcp": "aitp_v5_get_execution_brief",
        "surface": "execution_brief",
    },
    "summary_orientation": {
        "cli": "aitp-v5 summary orientation <session-id>",
        "mcp": "aitp_v5_read_summary_orientation",
        "surface": "summary_orientation",
    },
    "session_summary": {
        "cli": "aitp-v5 summary session <session-id>",
        "mcp": "aitp_v5_write_session_summary",
        "surface": "session_summary_bundle",
    },
    "trust_preflight": {
        "cli": "aitp-v5 trust preflight <args>",
        "mcp": "aitp_v5_preflight_trust_update",
        "surface": "trust_update_preflight",
    },
    "trust_apply": {
        "cli": "aitp-v5 trust apply <args>",
        "mcp": "aitp_v5_apply_trust_update",
        "surface": "trust_update_apply",
    },
}


def runtime_entrypoints() -> dict[str, dict[str, Any]]:
    """Return canonical CLI/MCP entrypoints advertised to runtime adapters."""

    return deepcopy(_RUNTIME_ENTRYPOINTS)


def runtime_entrypoint_surfaces() -> set[str]:
    """Return the public surfaces named by advertised runtime entrypoints."""

    return {entrypoint["surface"] for entrypoint in _RUNTIME_ENTRYPOINTS.values()}
