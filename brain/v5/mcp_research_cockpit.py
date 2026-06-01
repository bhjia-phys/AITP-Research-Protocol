"""MCP wrappers for workspace-level research cockpit surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_cockpit import compact_research_cockpit_bundle, write_research_cockpit_surfaces
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_write_research_cockpit_surfaces(base: str) -> dict:
    return require_valid_public_surface(
        "research_cockpit_bundle",
        write_research_cockpit_surfaces(_ws(base)),
    )


def aitp_v5_write_research_cockpit_surfaces_compact(base: str) -> dict:
    bundle = aitp_v5_write_research_cockpit_surfaces(base)
    return compact_research_cockpit_bundle(bundle)
