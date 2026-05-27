"""MCP wrappers for vNext topic status surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.topic_status import write_topic_status_surfaces
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_write_topic_status_surfaces(base: str, *, session_id: str) -> dict:
    return require_valid_public_surface(
        "topic_status_bundle",
        write_topic_status_surfaces(_ws(base), session_id=session_id),
    )
