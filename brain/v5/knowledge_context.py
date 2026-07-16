"""Budgeted, trust-neutral physics knowledge context slices."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Sequence

from brain.v5.context_compiler_support import estimate_context_tokens
from brain.v5.formula_retrieval import search_formula
from brain.v5.graph_retrieval import search_graph
from brain.v5.knowledge_retrieval import (
    KnowledgeQuery,
    KnowledgeRetrievalHit,
    eligible_knowledge_items,
    search_fielded_lexical,
)
from brain.v5.knowledge_context_contracts import (
    KnowledgeContextEntry,
    KnowledgeContextRequest,
    KnowledgeContextSlice,
    MODE_BUDGETS,
    require_valid_knowledge_context,
)
from brain.v5.knowledge_context_render import render_knowledge_entries
from brain.v5.knowledge_snapshot import (
    KnowledgeSnapshot,
    KnowledgeSnapshotItem,
    build_knowledge_snapshot,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.retrieval_fusion import (
    DEFAULT_FUSION_POLICY,
    DenseRetrievalAdapter,
    fuse_knowledge_rankings,
    search_dense_optional,
)
from brain.v5.source_shelf_storage import hash_json


def compile_knowledge_context(
    ws: WorkspacePaths,
    request: KnowledgeContextRequest,
    *,
    dense_adapter: DenseRetrievalAdapter | None = None,
) -> KnowledgeContextSlice:
    """Compile one bounded slice from a coherent knowledge snapshot."""

    max_tokens, max_bytes, max_results = _effective_budget(request)
    snapshot = build_knowledge_snapshot(
        ws,
        source_shelf_generation=request.source_shelf_generation,
        source_shelf_topic_id=request.source_shelf_topic_id,
    )
    if request.mode == "exact_expansion":
        candidates, coverage = _exact_candidates(snapshot, request, max_results)
    else:
        query = _retrieval_query(request, max_results)
        components = (
            search_fielded_lexical(snapshot, query),
            search_formula(snapshot, query),
            search_graph(snapshot, query, workspace=ws),
            search_dense_optional(snapshot, query, dense_adapter),
        )
        fused = fuse_knowledge_rankings(components, query)
        candidates = _entries_from_hits(snapshot, fused.hits, request)
        coverage = asdict(fused.coverage)
        coverage["lane_quotas"] = dict(DEFAULT_FUSION_POLICY["lane_quotas"])
    shown, markdown, token_allocation, not_shown = render_knowledge_entries(
        request,
        candidates,
        max_tokens=max_tokens,
        max_bytes=max_bytes,
    )
    byte_count = len(markdown.encode("utf-8"))
    estimated_tokens = estimate_context_tokens(markdown)
    token_allocation["used_tokens"] = estimated_tokens
    token_allocation["remaining_tokens"] = max(0, max_tokens - estimated_tokens)
    coverage["render_not_shown_count"] = len(not_shown)
    coverage["render_not_shown_refs"] = list(not_shown)
    coverage["max_tokens"] = max_tokens
    coverage["max_bytes"] = max_bytes
    partial = bool(
        not coverage.get("complete", False)
        or not_shown
        or coverage.get("truncated", False)
    )
    basis = {
        "mode": request.mode,
        "topic_id": request.topic_id,
        "query": asdict(request),
        "entries": [asdict(entry) for entry in shown],
        "snapshot_lineage": asdict(snapshot.lineage),
        "coverage": coverage,
        "token_allocation": token_allocation,
        "markdown": markdown,
    }
    result = KnowledgeContextSlice(
        mode=request.mode,
        topic_id=request.topic_id,
        query=asdict(request),
        entries=shown,
        snapshot_lineage=asdict(snapshot.lineage),
        coverage=coverage,
        token_allocation=token_allocation,
        not_shown_refs=not_shown,
        exact_expansion_handles=tuple(entry.exact_expansion for entry in shown),
        partial=partial,
        markdown=markdown,
        byte_count=byte_count,
        estimated_tokens=estimated_tokens,
        max_bytes=max_bytes,
        max_tokens=max_tokens,
        context_hash=hash_json(basis),
    )
    return require_valid_knowledge_context(result)


def _effective_budget(request: KnowledgeContextRequest) -> tuple[int, int, int]:
    token_cap, byte_default, result_default = MODE_BUDGETS[request.mode]
    max_tokens = min(request.max_tokens or token_cap, token_cap)
    max_bytes = min(request.max_bytes or byte_default, byte_default)
    max_results = min(request.max_results or result_default, result_default)
    if max_tokens < 128 or max_bytes < 512 or max_results < 1:
        raise ValueError("knowledge context budget is too small")
    return max_tokens, max_bytes, max_results


def _retrieval_query(
    request: KnowledgeContextRequest,
    max_results: int,
) -> KnowledgeQuery:
    return KnowledgeQuery(
        text=request.query_text,
        topic_id=request.topic_id,
        framework=request.framework,
        regime=request.regime,
        conventions=request.conventions,
        formula=request.formula,
        intent=request.intent,
        program_id=request.program_id,
        seed_refs=request.seed_refs,
        include_discovery=request.include_discovery,
        revalidation_decision_refs=request.revalidation_decision_refs,
        max_results=max_results,
        page_offset=request.page_offset,
    )


def _entries_from_hits(
    snapshot: KnowledgeSnapshot,
    hits: Sequence[KnowledgeRetrievalHit],
    request: KnowledgeContextRequest,
) -> tuple[KnowledgeContextEntry, ...]:
    by_ref = {item.record_ref: item for item in snapshot.items}
    return tuple(
        _entry(by_ref[hit.record_ref], hit, request, snapshot)
        for hit in hits
        if hit.record_ref in by_ref
    )


def _entry(
    item: KnowledgeSnapshotItem,
    hit: KnowledgeRetrievalHit,
    request: KnowledgeContextRequest,
    snapshot: KnowledgeSnapshot,
) -> KnowledgeContextEntry:
    knowledge_lane = item.lane
    scope_lane = (
        hit.lane if hit.lane in {"shared", "discovery", "comparison"} else "primary"
    )
    return KnowledgeContextEntry(
        record_ref=item.record_ref,
        record_hash=item.record_hash,
        revision=item.revision,
        family=item.family,
        knowledge_lane=knowledge_lane,
        scope_lane=scope_lane,
        grounding_state=_grounding_state(knowledge_lane),
        speculation_level=_first(item.fields.get("speculation", ()))
        or ("exploratory" if knowledge_lane == "insight" else "none"),
        framework=item.framework,
        regime=item.regime,
        conventions=item.conventions,
        framework_compatibility=_compatibility(request.framework, item.framework),
        regime_compatibility=_compatibility(request.regime, item.regime),
        convention_compatibility=_convention_compatibility(
            request.conventions,
            item.conventions,
        ),
        score=hit.score,
        component_scores=dict(hit.field_scores),
        summary=_summary(item),
        formulas=item.fields.get("formula", ()),
        source_anchors=item.fields.get("source_anchors", ()),
        graph_path=hit.path,
        exact_expansion=_expansion_handle(item, snapshot),
        orientation_only=True,
    )


def _exact_candidates(
    snapshot: KnowledgeSnapshot,
    request: KnowledgeContextRequest,
    max_results: int,
) -> tuple[tuple[KnowledgeContextEntry, ...], dict[str, Any]]:
    by_ref = {item.record_ref: item for item in snapshot.items}
    scope_query = KnowledgeQuery(
        text="exact expansion scope",
        topic_id=request.topic_id,
        framework=request.framework,
        regime=request.regime,
        conventions=request.conventions,
        intent=("comparison" if request.intent == "comparison" else "insight"),
        program_id=request.program_id,
        include_discovery=request.include_discovery,
        revalidation_decision_refs=request.revalidation_decision_refs,
        max_results=max_results,
    )
    eligible, excluded = eligible_knowledge_items(snapshot, scope_query)
    eligible_by_ref = {item.record_ref: (item, lane) for item, lane in eligible}
    resolved = [
        eligible_by_ref[ref]
        for ref in request.exact_refs
        if ref in eligible_by_ref
    ]
    page_end = request.page_offset + max_results
    found = resolved[request.page_offset:page_end]
    hits = tuple(
        KnowledgeRetrievalHit(
            record_ref=item.record_ref,
            component="exact",
            rank=index,
            score=1.0,
            lane=lane,
            topic_id=item.topic_id,
            family=item.family,
            exact_expansion_refs=(item.record_ref,),
            orientation_only=True,
        )
        for index, (item, lane) in enumerate(found, start=1)
    )
    entries = _entries_from_hits(snapshot, hits, request)
    not_found = [ref for ref in request.exact_refs if ref not in by_ref]
    blocked = [
        ref
        for ref in request.exact_refs
        if ref in by_ref and ref not in eligible_by_ref
    ]
    coverage = {
        "complete": bool(
            not not_found
            and not blocked
            and snapshot.lineage.scope_fresh
            and snapshot.lineage.scope_content_verified
        ),
        "component_statuses": {"exact": "available"},
        "checked_scope": {
            "snapshot_hash": snapshot.lineage.snapshot_hash,
            "topic_id": request.topic_id,
            "scope_fresh": snapshot.lineage.scope_fresh,
            "scope_content_verified": snapshot.lineage.scope_content_verified,
            "ordering_policy": "requested_exact_ref_order",
        },
        "excluded_scope": excluded,
        "pagination": {
            "offset": request.page_offset,
            "limit": max_results,
            "returned": len(entries),
            "total_observed": len(resolved),
            "total_exact": True,
            "not_shown_observed": max(0, len(resolved) - page_end),
            "has_more": page_end < len(resolved),
            "next_offset": (
                request.page_offset + len(entries)
                if page_end < len(resolved) and entries
                else None
            ),
        },
        "errors": list(snapshot.lineage.errors),
        "not_found_refs": not_found,
        "blocked_refs": blocked,
        "truncated": request.page_offset > 0 or page_end < len(resolved),
    }
    return entries, coverage


def _expansion_handle(
    item: KnowledgeSnapshotItem,
    snapshot: KnowledgeSnapshot,
) -> dict[str, Any]:
    if item.family == "source_shelf_passages":
        anchor_kinds = item.fields.get("anchor_kinds", ())
        return {
            "kind": (
                "source_equation" if "equation" in anchor_kinds else "source_passage"
            ),
            "source_passage_ref": item.record_ref,
            "source_asset_ref": _first(item.fields.get("source_asset_ref", ())),
            "text_hash": item.record_hash,
            "content_hash": item.record_hash,
            "source_shelf_generation": snapshot.lineage.source_shelf_generation,
            "source_shelf_passages_hash": snapshot.lineage.source_shelf_passages_hash,
            "source_location_refs": list(item.fields.get("source_anchors", ())),
            "anchor_kinds": list(anchor_kinds),
            "anchor_labels": list(item.fields.get("anchor_labels", ())),
        }
    formula_ref = _linked_ref(item, "formula_code_formula")
    code_state_ref = _linked_ref(item, "formula_code_code_state")
    if item.family == "object_relations" and formula_ref and code_state_ref:
        return {
            "kind": "formula_code_relation",
            "record_ref": item.record_ref,
            "content_hash": item.record_hash,
            "revision": item.revision,
            "formula_ref": formula_ref,
            "code_state_ref": code_state_ref,
            "edge_types": {
                record_ref: list(edge_types)
                for record_ref, edge_types in item.link_types.items()
            },
        }
    return {
        "kind": _expansion_kind(item.family),
        "record_ref": item.record_ref,
        "content_hash": item.record_hash,
        "revision": item.revision,
    }


def _expansion_kind(family: str) -> str:
    return {
        "source_assets": "source_asset",
        "reference_locations": "reference_location",
        "physics_assertions": "physics_assertion",
        "physics_objects": "physics_object",
        "object_relations": "object_relation",
        "derivation_chains": "derivation_chain",
        "derivation_steps": "derivation_step",
        "insights": "insight",
        "code_states": "code_state",
    }.get(family, "canonical_record")


def _linked_ref(item: KnowledgeSnapshotItem, edge_type: str) -> str:
    return next(
        (
            record_ref
            for record_ref, edge_types in item.link_types.items()
            if edge_type in edge_types
        ),
        "",
    )


def _summary(item: KnowledgeSnapshotItem) -> str:
    for field_name in (
        "canonical_name",
        "statement",
        "relation",
        "formula",
        "passage_text",
    ):
        value = _first(item.fields.get(field_name, ()))
        if value:
            return value[:320]
    return item.record_ref


def _grounding_state(lane: str) -> str:
    return {
        "grounded": "reviewed_grounded",
        "source": "source_orientation",
        "insight": "speculative_non_evidence",
    }.get(lane, "orientation_unreviewed")


def _compatibility(requested: str, actual: str) -> str:
    if not requested or not actual:
        return "unspecified"
    return "compatible" if _norm(requested) == _norm(actual) else "incompatible"


def _convention_compatibility(
    requested: Sequence[str],
    actual: Sequence[str],
) -> str:
    if not requested or not actual:
        return "unspecified"
    requested_set = {_norm(value) for value in requested}
    actual_set = {_norm(value) for value in actual}
    return "compatible" if requested_set <= actual_set else "incompatible"


def _first(values: Sequence[str]) -> str:
    return str(values[0]) if values else ""


def _norm(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


__all__ = [
    "KnowledgeContextEntry",
    "KnowledgeContextRequest",
    "KnowledgeContextSlice",
    "compile_knowledge_context",
]
