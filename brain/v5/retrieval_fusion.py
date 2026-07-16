"""Optional dense retrieval boundary and deterministic reciprocal-rank fusion."""

from __future__ import annotations

from dataclasses import asdict, replace
import math
from typing import Any, Mapping, Protocol, Sequence

from brain.v5.knowledge_retrieval import (
    KnowledgeComponentResult,
    KnowledgeQuery,
    KnowledgeRetrievalCoverage,
    KnowledgeRetrievalHit,
    KnowledgeRetrievalResult,
    _candidate_limit,
    _component_result,
    _eligible_items,
)
from brain.v5.knowledge_snapshot import KnowledgeSnapshot
from brain.v5.source_shelf_storage import hash_json


DEFAULT_FUSION_POLICY = {
    "version": "rrf.v1",
    "rrf_k": 60,
    "component_weights": {"lexical": 1.0, "formula": 1.0, "graph": 1.2, "dense": 0.5},
    "lane_quotas": {"grounded": 6, "insight": 2, "shared": 2, "discovery": 2, "comparison": 2, "source": 2, "orientation": 2},
}


class DenseRetrievalAdapter(Protocol):
    adapter_version: str
    model_id: str
    index_version: str
    deterministic: bool

    def search(self, snapshot: KnowledgeSnapshot, query: KnowledgeQuery, limit: int) -> KnowledgeComponentResult: ...


def search_dense_optional(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    adapter: DenseRetrievalAdapter | None = None,
) -> KnowledgeComponentResult:
    if adapter is None:
        return _component_result(
            component="dense",
            version="absent",
            status="absent",
            snapshot=snapshot,
            hits=(),
            coverage={"reason": "dense_adapter_not_configured"},
            policy={"adapter": "absent"},
        )
    metadata = _dense_metadata(snapshot, query, adapter)
    if query.deterministic and not adapter.deterministic:
        return _component_result(
            component="dense",
            version=str(adapter.adapter_version),
            status="excluded",
            snapshot=snapshot,
            hits=(),
            coverage={
                "reason": "nondeterministic_dense_disabled",
                **metadata,
            },
            policy=metadata,
        )
    try:
        result = adapter.search(snapshot, query, _candidate_limit(query))
    except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
        return _component_result(
            component="dense",
            version=str(adapter.adapter_version),
            status="degraded",
            snapshot=snapshot,
            hits=(),
            coverage={
                **metadata,
                "timeout_policy": "degrade_to_non_dense_components",
            },
            policy=metadata,
            errors=(f"dense adapter failed: {exc}",),
        )
    if result.component != "dense" or result.snapshot_hash != snapshot.lineage.snapshot_hash:
        return _component_result(
            component="dense",
            version=str(adapter.adapter_version),
            status="degraded",
            snapshot=snapshot,
            hits=(),
            coverage={
                **metadata,
                "reason": "incompatible_dense_component_identity",
                "returned_component": result.component,
                "returned_snapshot_hash": result.snapshot_hash,
                "returned_component_hash": result.component_hash,
            },
            policy=metadata,
            errors=("dense adapter returned incompatible component identity",),
        )
    from brain.v5.knowledge_retrieval_contracts import (
        require_valid_knowledge_component,
    )

    try:
        require_valid_knowledge_component(result)
    except (TypeError, ValueError) as exc:
        return _component_result(
            component="dense",
            version=str(adapter.adapter_version),
            status="degraded",
            snapshot=snapshot,
            hits=(),
            coverage={
                **metadata,
                "reason": "invalid_dense_component_contract",
                "adapter_result_hash": result.component_hash,
            },
            policy=metadata,
            errors=(f"dense adapter contract failed: {exc}",),
        )
    if query.deterministic and not result.deterministic:
        return _component_result(
            component="dense",
            version=str(adapter.adapter_version),
            status="degraded",
            snapshot=snapshot,
            hits=(),
            coverage={
                **metadata,
                "reason": "nondeterministic_dense_result",
                "adapter_result_hash": result.component_hash,
            },
            policy=metadata,
            errors=("dense adapter returned a nondeterministic result",),
        )
    eligible = {
        item.record_ref: (item, lane)
        for item, lane in _eligible_items(snapshot, query)[0]
    }
    normalized_hits: list[KnowledgeRetrievalHit] = []
    for hit in sorted(result.hits, key=lambda item: (-item.score, item.record_ref)):
        target = eligible.get(hit.record_ref)
        if target is None:
            return _component_result(
                component="dense",
                version=str(adapter.adapter_version),
                status="degraded",
                snapshot=snapshot,
                hits=(),
                coverage={
                    **metadata,
                    "reason": "dense_hit_outside_authorized_scope",
                    "adapter_result_hash": result.component_hash,
                    "rejected_record_ref": hit.record_ref,
                },
                policy=metadata,
                errors=("dense adapter returned a hit outside authorized scope",),
            )
        item, lane = target
        normalized_hits.append(
            replace(
                hit,
                component="dense",
                rank=len(normalized_hits) + 1,
                lane=lane,
                topic_id=item.topic_id,
                family=item.family,
                exact_expansion_refs=(item.record_ref,),
                orientation_only=lane != "grounded",
                can_update_claim_trust=False,
            )
        )
    tie_handling = "score_desc_then_record_ref"
    return _component_result(
        component="dense",
        version=str(adapter.adapter_version),
        status=result.status,
        snapshot=snapshot,
        hits=normalized_hits,
        coverage={
            **result.coverage,
            **metadata,
            "adapter_result_hash": result.component_hash,
            "tie_handling": tie_handling,
        },
        policy={**metadata, "tie_handling": tie_handling},
        deterministic=result.deterministic,
        errors=result.errors,
    )


def _dense_metadata(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    adapter: DenseRetrievalAdapter,
) -> dict[str, Any]:
    metadata = {
        "adapter_version": str(adapter.adapter_version),
        "model_id": str(adapter.model_id),
        "index_version": str(adapter.index_version),
        "adapter_deterministic": adapter.deterministic,
        "snapshot_hash": snapshot.lineage.snapshot_hash,
        "limit": _candidate_limit(query),
    }
    return {
        **metadata,
        "input_hash": hash_json({"query": asdict(query), **metadata}),
    }


def fuse_knowledge_rankings(
    results: Sequence[KnowledgeComponentResult],
    query: KnowledgeQuery,
    policy: Mapping[str, Any] | None = None,
) -> KnowledgeRetrievalResult:
    from brain.v5.knowledge_retrieval_contracts import (
        require_valid_knowledge_component,
    )

    component_names = [result.component for result in results]
    if len(component_names) != len(set(component_names)):
        raise ValueError("knowledge retrieval components must be unique")
    for result in results:
        require_valid_knowledge_component(result)
    selected = _fusion_policy(policy)
    present = [result for result in results if result.status not in {"absent", "excluded"}]
    baseline_hash = present[0].snapshot_hash if present else (results[0].snapshot_hash if results else "")
    incompatible = [result.component for result in present if result.snapshot_hash != baseline_hash]
    errors = [error for result in results for error in result.errors]
    if incompatible:
        errors.append("incompatible snapshot lineage")
    compatible = [result for result in present if result.snapshot_hash == baseline_hash]
    aggregate: dict[str, dict[str, Any]] = {}
    for result in compatible:
        weight = float(selected["component_weights"].get(result.component, 0.0))
        for hit in result.hits:
            row = aggregate.setdefault(
                hit.record_ref,
                {"hit": hit, "score": 0.0, "ranks": {}, "scores": {}},
            )
            row["score"] += weight / (float(selected["rrf_k"]) + hit.rank)
            row["ranks"][result.component] = hit.rank
            row["scores"][result.component] = hit.score
            if hit.lane == "grounded" and row["hit"].lane != "grounded":
                row["hit"] = hit
    ordered = sorted(
        aggregate.values(),
        key=lambda row: (
            _scope_lane_priority(row["hit"].lane),
            -row["score"],
            row["hit"].record_ref,
        ),
    )
    quotas = {key: int(value) for key, value in selected["lane_quotas"].items()}
    lane_counts: dict[str, int] = {}
    fused_all: list[KnowledgeRetrievalHit] = []
    quota_excluded_refs: list[str] = []
    for row in ordered:
        hit = row["hit"]
        quota = quotas.get(hit.lane, query.max_results)
        if lane_counts.get(hit.lane, 0) >= quota:
            quota_excluded_refs.append(hit.record_ref)
            continue
        lane_counts[hit.lane] = lane_counts.get(hit.lane, 0) + 1
        fused_all.append(
            replace(
                hit,
                component="fusion",
                rank=len(fused_all) + 1,
                score=round(row["score"], 12),
                field_scores={
                    **{f"rank:{key}": float(value) for key, value in sorted(row["ranks"].items())},
                    **{f"score:{key}": float(value) for key, value in sorted(row["scores"].items())},
                },
            )
        )
    page_start = query.page_offset
    page_end = page_start + query.max_results
    fused = fused_all[page_start:page_end]
    not_shown_refs = tuple(
        dict.fromkeys(
            [
                *(hit.record_ref for hit in fused_all[:page_start]),
                *(hit.record_ref for hit in fused_all[page_end:]),
                *quota_excluded_refs,
            ]
        )
    )
    component_truncated = any(
        bool(result.coverage.get("truncated")) for result in compatible
    )
    total_exact = not component_truncated
    has_more = component_truncated or page_end < len(fused_all)
    pagination = {
        "offset": page_start,
        "limit": query.max_results,
        "returned": len(fused),
        "total_observed": len(fused_all),
        "total_exact": total_exact,
        "not_shown_observed": max(0, len(fused_all) - page_end),
        "has_more": has_more,
        "next_offset": page_start + len(fused) if has_more and fused else None,
    }
    component_statuses = {result.component: result.status for result in results}
    required_lexical = component_statuses.get("lexical") == "available"
    snapshot_compatible = not incompatible
    lineage_source = compatible[0] if compatible else (results[0] if results else None)
    lineage_coverage = lineage_source.coverage if lineage_source else {}
    scope_fresh = lineage_coverage.get("snapshot_scope_fresh") is True
    scope_content_verified = (
        lineage_coverage.get("snapshot_scope_content_verified") is True
    )
    complete = (
        snapshot_compatible
        and required_lexical
        and scope_fresh
        and scope_content_verified
        and not errors
    )
    coverage = KnowledgeRetrievalCoverage(
        snapshot_compatible=snapshot_compatible,
        complete=complete,
        component_statuses=component_statuses,
        checked_scope={
            "snapshot_hash": baseline_hash,
            "topic_id": query.topic_id,
            "ordering_policy": "scope_lane_then_rrf_score_then_record_ref",
            "scope_fresh": scope_fresh,
            "scope_content_verified": scope_content_verified,
            "dirty_families": list(
                lineage_coverage.get("snapshot_dirty_families") or []
            ),
            "query_index_generation": lineage_coverage.get(
                "query_index_generation"
            ),
            "query_index_delta_generation": lineage_coverage.get(
                "query_index_delta_generation"
            ),
            "query_index_content_hash": lineage_coverage.get(
                "query_index_content_hash", ""
            ),
            "selected_family_state_tokens": dict(
                lineage_coverage.get("selected_family_state_tokens") or {}
            ),
            "selected_family_content_watermarks": dict(
                lineage_coverage.get("selected_family_content_watermarks") or {}
            ),
            "source_shelf_generation": lineage_coverage.get(
                "source_shelf_generation", ""
            ),
            "source_shelf_passages_hash": lineage_coverage.get(
                "source_shelf_passages_hash", ""
            ),
            "excluded_unscoped_counts": dict(
                lineage_coverage.get("excluded_unscoped_counts") or {}
            ),
            "freshness_mode": lineage_coverage.get("freshness_mode", "strong"),
            "components": {
                result.component: {
                    "version": result.version,
                    "status": result.status,
                    "snapshot_hash": result.snapshot_hash,
                    "component_hash": result.component_hash,
                    "deterministic": result.deterministic,
                }
                for result in results
            },
        },
        excluded_scope={
            key: max(
                (int(result.coverage.get(key, 0)) for result in results),
                default=0,
            )
            for key in (
                "foreign_topic_excluded",
                "foreign_insight_excluded",
                "wrong_framework_excluded",
                "wrong_regime_excluded",
                "convention_mismatch_excluded",
                "insight_lane_excluded",
            )
        },
        pagination=pagination,
        not_shown_refs=not_shown_refs,
        errors=tuple(dict.fromkeys(errors)),
        truncated=(
            component_truncated
            or len(ordered) > len(fused_all)
            or page_end < len(fused_all)
        ),
    )
    basis = {
        "query": asdict(query),
        "hits": [asdict(hit) for hit in fused],
        "coverage": asdict(coverage),
        "policy": selected,
        "component_hashes": {result.component: result.component_hash for result in results},
    }
    deterministic = all(result.deterministic for result in compatible)
    return KnowledgeRetrievalResult(
        query=query,
        hits=tuple(fused),
        coverage=coverage,
        result_hash=hash_json(basis),
        deterministic=deterministic,
        can_claim_no_result=complete and total_exact and not fused_all,
    )


def _fusion_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    selected = {**DEFAULT_FUSION_POLICY, **dict(policy or {})}
    selected["component_weights"] = {
        **DEFAULT_FUSION_POLICY["component_weights"],
        **dict((policy or {}).get("component_weights") or {}),
    }
    selected["lane_quotas"] = {
        **DEFAULT_FUSION_POLICY["lane_quotas"],
        **dict((policy or {}).get("lane_quotas") or {}),
    }
    if selected["version"] != DEFAULT_FUSION_POLICY["version"]:
        raise ValueError("unsupported fusion policy version")
    rrf_k = selected["rrf_k"]
    if isinstance(rrf_k, bool) or not isinstance(rrf_k, int) or rrf_k < 1:
        raise ValueError("rrf_k must be positive")
    component_weights = {
        str(key): float(value)
        for key, value in selected["component_weights"].items()
    }
    if (
        set(component_weights) - set(DEFAULT_FUSION_POLICY["component_weights"])
        or any(
            not math.isfinite(value) or value < 0
            for value in component_weights.values()
        )
        or component_weights.get("lexical", 0) <= 0
    ):
        raise ValueError("fusion component weights must be finite and non-negative")
    lane_quotas = dict(selected["lane_quotas"])
    if set(lane_quotas) - set(DEFAULT_FUSION_POLICY["lane_quotas"]):
        raise ValueError("fusion lane quotas contain unsupported lanes")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in lane_quotas.values()
    ):
        raise ValueError("fusion lane quotas must be non-negative integers")
    selected["component_weights"] = component_weights
    selected["lane_quotas"] = lane_quotas
    return selected


def _scope_lane_priority(lane: str) -> int:
    if lane == "shared":
        return 1
    if lane == "discovery":
        return 2
    if lane == "comparison":
        return 3
    return 0


__all__ = [
    "DEFAULT_FUSION_POLICY",
    "DenseRetrievalAdapter",
    "fuse_knowledge_rankings",
    "search_dense_optional",
]
