"""Stable, trust-neutral contracts for bounded physics knowledge context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from brain.v5.context_compiler_support import estimate_context_tokens
from brain.v5.source_shelf_storage import hash_json


MODE_BUDGETS = {
    "startup": (760, 4000, 4),
    "normal": (1400, 8000, 12),
    "exact_expansion": (1500, 9000, 16),
}


@dataclass(frozen=True)
class KnowledgeContextRequest:
    query_text: str
    topic_id: str
    framework: str = ""
    regime: str = ""
    conventions: tuple[str, ...] = ()
    formula: str = ""
    intent: str = "default"
    mode: str = "normal"
    program_id: str = ""
    seed_refs: tuple[str, ...] = ()
    include_discovery: bool = False
    revalidation_decision_refs: tuple[Any, ...] = ()
    source_shelf_generation: str = ""
    source_shelf_topic_id: str = ""
    exact_refs: tuple[str, ...] = ()
    page_offset: int = 0
    max_results: int = 0
    max_tokens: int = 0
    max_bytes: int = 0

    def __post_init__(self) -> None:
        if self.mode not in MODE_BUDGETS:
            raise ValueError("knowledge context mode is unsupported")
        if not self.topic_id.strip():
            raise ValueError("knowledge context topic_id is required")
        if self.mode == "exact_expansion":
            if not self.exact_refs:
                raise ValueError("exact knowledge context requires exact_refs")
        elif not self.query_text.strip() and not self.formula.strip() and not self.seed_refs:
            raise ValueError("knowledge context requires a query, formula, or graph seed")
        if not isinstance(self.include_discovery, bool):
            raise TypeError("knowledge context include_discovery must be boolean")
        for value, label in (
            (self.page_offset, "page_offset"),
            (self.max_results, "max_results"),
            (self.max_tokens, "max_tokens"),
            (self.max_bytes, "max_bytes"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"knowledge context {label} must be non-negative")


@dataclass(frozen=True)
class KnowledgeContextEntry:
    record_ref: str
    record_hash: str
    revision: int
    family: str
    knowledge_lane: str
    scope_lane: str
    grounding_state: str
    speculation_level: str
    framework: str
    regime: str
    conventions: tuple[str, ...]
    framework_compatibility: str
    regime_compatibility: str
    convention_compatibility: str
    score: float
    component_scores: dict[str, float]
    summary: str
    formulas: tuple[str, ...]
    source_anchors: tuple[str, ...]
    graph_path: tuple[str, ...]
    exact_expansion: dict[str, Any]
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class KnowledgeContextSlice:
    mode: str
    topic_id: str
    query: dict[str, Any]
    entries: tuple[KnowledgeContextEntry, ...]
    snapshot_lineage: dict[str, Any]
    coverage: dict[str, Any]
    token_allocation: dict[str, Any]
    not_shown_refs: tuple[str, ...]
    exact_expansion_handles: tuple[dict[str, Any], ...]
    partial: bool
    markdown: str
    byte_count: int
    estimated_tokens: int
    max_bytes: int
    max_tokens: int
    context_hash: str
    orientation_only: bool = True
    summary_inputs_trusted: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def require_valid_knowledge_context(
    value: KnowledgeContextSlice,
) -> KnowledgeContextSlice:
    """Reject malformed, stale, or trust-bearing context projections."""

    if not isinstance(value, KnowledgeContextSlice):
        raise TypeError("knowledge context has the wrong type")
    if value.can_update_claim_trust:
        raise ValueError("knowledge context cannot update claim trust")
    if not value.orientation_only or value.summary_inputs_trusted:
        raise ValueError("knowledge context must remain orientation-only")
    if value.can_update_kernel_state:
        raise ValueError("knowledge context cannot update kernel state")
    if value.byte_count != len(value.markdown.encode("utf-8")):
        raise ValueError("knowledge context byte count is inconsistent")
    if value.estimated_tokens != estimate_context_tokens(value.markdown):
        raise ValueError("knowledge context token estimate is inconsistent")
    if value.byte_count > value.max_bytes or value.estimated_tokens > value.max_tokens:
        raise ValueError("knowledge context exceeds its rendered budget")
    if value.token_allocation.get("used_tokens") != value.estimated_tokens:
        raise ValueError("knowledge context token allocation is inconsistent")
    refs = [entry.record_ref for entry in value.entries]
    if len(refs) != len(set(refs)):
        raise ValueError("knowledge context entries must have unique refs")
    for entry in value.entries:
        if entry.can_update_claim_trust:
            raise ValueError("knowledge context entry cannot update claim trust")
        if not entry.orientation_only:
            raise ValueError("knowledge context entry must remain orientation-only")
        if entry.exact_expansion.get("content_hash") != entry.record_hash:
            raise ValueError("knowledge context expansion hash is inconsistent")
    basis = {
        "mode": value.mode,
        "topic_id": value.topic_id,
        "query": value.query,
        "entries": [asdict(entry) for entry in value.entries],
        "snapshot_lineage": value.snapshot_lineage,
        "coverage": value.coverage,
        "token_allocation": value.token_allocation,
        "markdown": value.markdown,
    }
    if value.context_hash != hash_json(basis):
        raise ValueError("knowledge context hash is inconsistent")
    return value


__all__ = [
    "KnowledgeContextEntry",
    "KnowledgeContextRequest",
    "KnowledgeContextSlice",
    "MODE_BUDGETS",
    "require_valid_knowledge_context",
]
