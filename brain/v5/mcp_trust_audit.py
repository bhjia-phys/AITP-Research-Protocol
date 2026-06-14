"""MCP-facing claim trust audit wrappers for AITP v5."""

from __future__ import annotations

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.trust_audit import audit_claim_trust
from brain.v5.workspace import init_workspace


def aitp_v5_audit_claim_trust(base: str, *, claim_id: str) -> dict:
    payload = audit_claim_trust(init_workspace(resolve_workspace_base(base)), claim_id=claim_id)
    return require_valid_public_surface("claim_trust_audit", payload)
