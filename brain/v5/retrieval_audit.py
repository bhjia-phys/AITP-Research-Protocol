"""Trust-neutral audit payloads for indexed AITP retrieval."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.research_retrieval import ResearchQuery, RetrievalResult


def build_retrieval_audit(
    query: ResearchQuery,
    result: RetrievalResult,
) -> dict[str, Any]:
    """Return a persistable audit payload without writing canonical state."""

    return {
        "kind": "research_retrieval_audit",
        "query": asdict(query),
        "index_status": result.index_status,
        "returned_refs": [item.record_ref for item in result.items],
        "excluded_candidates": list(result.excluded_candidates),
        "total_count": result.total_count,
        "truncated": result.truncated,
        "coverage": asdict(result.coverage),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
