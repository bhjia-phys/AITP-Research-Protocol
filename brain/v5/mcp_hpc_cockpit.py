"""MCP-facing wrapper for the generalized HPC cockpit."""

from __future__ import annotations

from pathlib import Path

from brain.v5.hpc_cockpit import build_hpc_cockpit
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_hpc_cockpit(base: str, *, topic_id: str) -> dict:
    """Orientation-only HPC cockpit for one compute topic.

    Aggregates tool_run attempts (effective/active/failed), lane distribution,
    provenance gaps, and the topic's lane contract into next-actions and
    allowed/not-allowed conclusions. It cannot update claim trust.
    """

    cockpit = build_hpc_cockpit(_ws(base), topic_id)
    return require_valid_public_surface("hpc_cockpit", cockpit)
