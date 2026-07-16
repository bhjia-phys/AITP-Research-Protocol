"""Fail-closed contracts for trust-neutral knowledge retrieval projections."""

from __future__ import annotations

import math

from brain.v5.knowledge_retrieval import KnowledgeComponentResult


_COMPONENTS = {"lexical", "formula", "graph", "dense"}
_STATUSES = {"available", "absent", "excluded", "degraded"}
_LANES = {
    "grounded",
    "insight",
    "orientation",
    "source",
    "shared",
    "discovery",
    "comparison",
}


def require_valid_knowledge_component(
    result: KnowledgeComponentResult,
) -> KnowledgeComponentResult:
    """Reject malformed or trust-bearing component results before fusion."""

    if not isinstance(result, KnowledgeComponentResult):
        raise TypeError("knowledge retrieval component has the wrong type")
    if result.component not in _COMPONENTS:
        raise ValueError("knowledge retrieval component is unsupported")
    if result.status not in _STATUSES:
        raise ValueError("knowledge retrieval component status is unsupported")
    if not _digest(result.snapshot_hash) or not _digest(result.component_hash):
        raise ValueError("knowledge retrieval component hashes must be sha256 digests")
    if result.can_update_claim_trust:
        raise ValueError("knowledge retrieval component cannot update claim trust")
    if result.status in {"absent", "excluded"} and result.hits:
        raise ValueError("absent or excluded knowledge component cannot contain hits")
    seen: set[str] = set()
    for expected_rank, hit in enumerate(result.hits, start=1):
        if hit.component != result.component:
            raise ValueError("knowledge retrieval hit component identity is inconsistent")
        if hit.rank != expected_rank:
            raise ValueError("knowledge retrieval hit ranks must be contiguous")
        if hit.record_ref in seen:
            raise ValueError("knowledge retrieval component refs must be unique")
        seen.add(hit.record_ref)
        if hit.lane not in _LANES:
            raise ValueError("knowledge retrieval hit lane is unsupported")
        if not math.isfinite(hit.score) or hit.score < 0:
            raise ValueError("knowledge retrieval hit score must be finite and non-negative")
        if hit.can_update_claim_trust:
            raise ValueError("knowledge retrieval hit cannot update claim trust")
        if hit.lane != "grounded" and not hit.orientation_only:
            raise ValueError("non-grounded knowledge hit must remain orientation-only")
        if hit.record_ref not in hit.exact_expansion_refs:
            raise ValueError("knowledge retrieval hit must expose its exact record ref")
    return result


def _digest(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )


__all__ = ["require_valid_knowledge_component"]
