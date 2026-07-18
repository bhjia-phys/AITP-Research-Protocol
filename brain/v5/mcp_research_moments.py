"""Full-surface MCP ingress for explicit Research Moment events."""

from __future__ import annotations

import json
from typing import Any, Mapping

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.record_envelope import RecordActor
from brain.v5.research_moment_facade import process_research_moment_request


def aitp_v5_process_research_moment(
    base: str,
    *,
    request_json: str,
    actor_type: str = "model",
    actor_id: str = "aitp-research-moment-mcp",
    host: str = "mcp",
) -> dict[str, Any]:
    """Decide and optionally apply one complete, explicit research event."""

    request = json.loads(request_json)
    if not isinstance(request, Mapping):
        raise ValueError("request_json must decode to an object")
    payload = process_research_moment_request(
        WorkspacePaths(resolve_workspace_base(base)),
        request,
        actor=RecordActor(actor_type=actor_type, actor_id=actor_id, host=host),
    )
    return require_valid_public_surface("research_moment_process_result", payload)


__all__ = ["aitp_v5_process_research_moment"]
