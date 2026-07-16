"""Focused full-MCP wrappers for promotion checkpoint requests."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.memory import request_promotion_checkpoint
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_request_promotion_checkpoint(
    base: str,
    *,
    packet_id: str,
    reason: str,
    requested_by: str,
    expires_at: str,
    options: list[str] | None = None,
) -> dict:
    ws = init_workspace(resolve_workspace_base(base))
    checkpoint = request_promotion_checkpoint(
        ws,
        packet_id=packet_id,
        reason=reason,
        requested_by=requested_by,
        expires_at=expires_at,
        options=options or ["approve", "reject"],
    )
    return require_valid_public_surface(
        "human_checkpoint_record",
        {"ok": True, **asdict(checkpoint)},
    )
