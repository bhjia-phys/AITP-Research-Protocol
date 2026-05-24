"""Thin MCP wrappers for v5 summary surfaces."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.replay import write_workspace_replay_packet
from brain.v5.summaries import read_summary_orientation, write_session_summary, write_workspace_summary
from brain.v5.workspace_refresh import refresh_workspace_views
from brain.v5.workspace import init_workspace


def aitp_v5_write_session_summary(base: str, *, session_id: str) -> dict:
    bundle = write_session_summary(init_workspace(base), session_id)
    return {"ok": True, **require_valid_public_surface("session_summary_bundle", asdict(bundle))}


def aitp_v5_read_summary_orientation(base: str, *, session_id: str) -> dict:
    payload = read_summary_orientation(init_workspace(base), session_id)
    return {"ok": True, **require_valid_public_surface("summary_orientation", payload)}


def aitp_v5_write_workspace_summary(base: str) -> dict:
    bundle = write_workspace_summary(init_workspace(base))
    return {"ok": True, **require_valid_public_surface("workspace_summary_bundle", asdict(bundle))}


def aitp_v5_write_workspace_replay_packet(base: str) -> dict:
    bundle = write_workspace_replay_packet(init_workspace(base))
    return {"ok": True, **require_valid_public_surface("workspace_replay_packet", asdict(bundle))}


def aitp_v5_refresh_workspace_views(base: str) -> dict:
    return {"ok": True, **require_valid_public_surface("workspace_refresh_bundle", refresh_workspace_views(init_workspace(base)))}
