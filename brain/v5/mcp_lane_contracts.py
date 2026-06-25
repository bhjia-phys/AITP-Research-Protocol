"""MCP-facing wrapper for typed lane contracts.

Only the write path is exposed as a contracted MCP surface; lane-contract
listing is consumed directly by the HPC cockpit (orientation-only) rather than
through a separate public surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.lane_contracts import lane_contract_payload, record_lane_contract
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_record_lane_contract(
    base: str,
    *,
    topic_id: str,
    campaign: str = "",
    claim_id: str = "",
    forbidden_roots: list[str] | None = None,
    preferred_clean_roots: list[str] | None = None,
    final_allowlist: list[str] | None = None,
    final_rules: list[str] | None = None,
    default_lane: str = "diagnostic",
    trust_update_forbidden: bool = False,
    notes: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Record a typed lane contract (forbidden/preferred roots, final rules).

    Promotes cockpit lane discipline into an auditable record so a compute
    topic's forbidden roots, preferred clean roots, final allowlist, and
    final-evidence rules survive as typed kernel state. Orientation-only; it
    cannot update claim trust.
    """

    record = record_lane_contract(
        _ws(base),
        topic_id=topic_id,
        campaign=campaign,
        claim_id=claim_id,
        forbidden_roots=forbidden_roots,
        preferred_clean_roots=preferred_clean_roots,
        final_allowlist=final_allowlist,
        final_rules=final_rules,
        default_lane=default_lane,
        trust_update_forbidden=trust_update_forbidden,
        notes=notes,
        metadata=metadata,
    )
    return require_valid_public_surface("lane_contract_record", lane_contract_payload(record))
