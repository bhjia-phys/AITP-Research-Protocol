"""Stable compact-context boundary shared by generated startup surfaces."""

from __future__ import annotations

from typing import Any


def compact_context_boundary(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "compact_context_boundary",
        "fingerprint": str(pack.get("fingerprint") or ""),
        "pack_id": str(pack.get("pack_id") or ""),
        "index_status": str(pack.get("index_status") or ""),
        "source_index_generation": int(pack.get("source_index_generation") or 0),
        "retrieval_coverage": dict(pack.get("retrieval_coverage") or {}),
        "byte_count": int(pack.get("byte_count") or 0),
        "estimated_tokens": int(pack.get("estimated_tokens") or 0),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_compact_context_section(boundary: dict[str, Any]) -> str:
    if not boundary:
        return ""
    coverage = boundary.get("retrieval_coverage") or {}
    return (
        "## Compact Context Boundary\n\n"
        f"Fingerprint: `{boundary.get('fingerprint', '')}`\n\n"
        f"Index: {boundary.get('index_status', '')} generation "
        f"{boundary.get('source_index_generation', 0)}\n\n"
        f"Coverage exhaustive: {bool(coverage.get('exhaustive'))}\n\n"
        "Orientation only; exact-expand typed refs before trust-sensitive conclusions.\n\n"
    )
