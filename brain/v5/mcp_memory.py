"""MCP-facing L2 memory audit wrappers for AITP v5."""

from __future__ import annotations

from pathlib import Path

from brain.v5.memory_audit import audit_l2_memory_context
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_audit_l2_memory_context(base: str, *, claim_id: str) -> dict:
    payload = audit_l2_memory_context(init_workspace(Path(base)), claim_id=claim_id)
    return require_valid_public_surface("l2_memory_audit", payload)
