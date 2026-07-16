"""Bounded typed graph traversal over one knowledge snapshot."""

from __future__ import annotations

from collections import deque
import math
from typing import Any, Mapping

from brain.v5.knowledge_retrieval import (
    KnowledgeQuery,
    _candidate_limit,
    _component_result,
    _eligible_items,
    _hit,
)
from brain.v5.knowledge_snapshot import KnowledgeSnapshot
from brain.v5.paths import WorkspacePaths


DEFAULT_GRAPH_POLICY = {
    "version": "typed-graph.v1",
    "max_depth": 2,
    "max_visited": 64,
    "depth_decay": 0.6,
}
_REVERSIBLE_EDGE_TYPES = {
    "formula_code_formula",
    "relation_subject",
    "relation_object",
}


def search_graph(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    policy: Mapping[str, Any] | None = None,
    *,
    workspace: WorkspacePaths | None = None,
):
    selected = _graph_policy(policy)
    max_depth = min(int(selected["max_depth"]), query.graph_depth)
    max_visited = int(selected["max_visited"])
    if not 0 <= max_depth <= 3 or not 1 <= max_visited <= 10000:
        raise ValueError("graph retrieval bounds are invalid")
    eligible, excluded = _eligible_items(snapshot, query)
    by_ref = {item.record_ref: (item, lane) for item, lane in eligible}
    reverse_edges: dict[str, list[tuple[str, str]]] = {}
    for source_ref, (item, _lane) in by_ref.items():
        for target_ref, edge_types in item.link_types.items():
            if target_ref not in by_ref:
                continue
            for edge_type in edge_types:
                if edge_type in _REVERSIBLE_EDGE_TYPES:
                    reverse_edges.setdefault(target_ref, []).append(
                        (source_ref, f"reverse:{edge_type}")
                    )
    seeds = tuple(dict.fromkeys(ref for ref in query.seed_refs if ref in by_ref))
    if not seeds or max_depth == 0:
        return _component_result(
            component="graph",
            version=str(selected["version"]),
            status="absent",
            snapshot=snapshot,
            hits=(),
            coverage={
                **excluded,
                "reason": "no_graph_seeds",
                "max_depth": max_depth,
                "projection_source": "bounded_snapshot_typed_edges",
                "sidecar_status": "not_configured",
            },
            policy=selected,
        )
    queue = deque((seed, (seed,), (), 0) for seed in seeds)
    visited = set(seeds)
    reached = []
    truncated = False
    cross_topic_edges_blocked = 0
    cross_topic_edges_authorized = 0
    scope_reasons: list[str] = []
    scope_errors: list[str] = []
    while queue:
        current_ref, path, edge_path, depth = queue.popleft()
        if depth >= max_depth:
            continue
        current = by_ref[current_ref][0]
        neighbors: dict[str, list[str]] = {
            target_ref: list(current.link_types.get(target_ref, ("related",)))
            for target_ref in current.links
        }
        for target_ref, edge_type in reverse_edges.get(current_ref, []):
            neighbors.setdefault(target_ref, []).append(edge_type)
        for target_ref in sorted(neighbors):
            if target_ref not in by_ref or target_ref in visited:
                continue
            target_item = by_ref[target_ref][0]
            if target_item.topic_id != query.topic_id:
                allowed, reasons, errors = _cross_topic_edge_allowed(
                    workspace,
                    target_item,
                    query,
                )
                scope_reasons.extend(reasons)
                scope_errors.extend(errors)
                if not allowed:
                    cross_topic_edges_blocked += 1
                    continue
                cross_topic_edges_authorized += 1
            if len(visited) >= max_visited:
                truncated = True
                queue.clear()
                break
            visited.add(target_ref)
            target_path = (*path, target_ref)
            target_edge_path = (
                *edge_path,
                sorted(set(neighbors[target_ref]))[0],
            )
            target_depth = depth + 1
            item, lane = by_ref[target_ref]
            score = float(selected["depth_decay"]) ** (target_depth - 1)
            reached.append(
                (
                    round(score, 12),
                    target_depth,
                    item,
                    lane,
                    target_path,
                    target_edge_path,
                )
            )
            queue.append((target_ref, target_path, target_edge_path, target_depth))
    reached.sort(key=lambda row: (-row[0], row[1], row[2].record_ref))
    hits = tuple(
        _hit(
            item,
            component="graph",
            rank=index,
            score=score,
            lane=lane,
            field_scores={"path_score": score, "depth": float(depth)},
            anchors={
                "seed_ref": path[0],
                "target_ref": item.record_ref,
                "edge_path": list(edge_path),
            },
            path=path,
        )
        for index, (score, depth, item, lane, path, edge_path) in enumerate(
            reached[: _candidate_limit(query)], start=1
        )
    )
    return _component_result(
        component="graph",
        version=str(selected["version"]),
        status="available",
        snapshot=snapshot,
        hits=hits,
        coverage={
            **excluded,
            "seed_refs": list(seeds),
            "visited_count": len(visited),
            "reached_count": len(reached),
            "max_depth": max_depth,
            "max_visited": max_visited,
            "truncated": truncated or len(reached) > len(hits),
            "cross_topic_edges_blocked": cross_topic_edges_blocked,
            "cross_topic_edges_authorized": cross_topic_edges_authorized,
            "scope_policy": "exact_target_revalidation_required",
            "scope_reasons": list(dict.fromkeys(scope_reasons)),
            "reverse_edge_count": sum(len(items) for items in reverse_edges.values()),
            "projection_source": "bounded_snapshot_typed_edges",
            "sidecar_status": "not_configured",
        },
        policy=selected,
        errors=tuple(dict.fromkeys(scope_errors)),
    )


def _cross_topic_edge_allowed(
    workspace: WorkspacePaths | None,
    item,
    query: KnowledgeQuery,
) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    if workspace is None or not query.revalidation_decision_refs:
        return False, ("cross-topic graph edge lacks target-side revalidation",), ()
    from brain.v5.execution_scope_policy import assess_execution_scope
    from brain.v5.pinned_record_refs import PinnedRecordRef

    try:
        decision = assess_execution_scope(
            workspace,
            operation="knowledge_graph_traversal",
            consumer_scope=(f"topic:{query.topic_id}",),
            dependency_refs=(
                PinnedRecordRef(
                    record_ref=item.record_ref,
                    content_hash=item.record_hash,
                    revision=item.revision,
                ),
            ),
            revalidation_decision_refs=query.revalidation_decision_refs,
        )
    except (OSError, TypeError, ValueError) as exc:
        return False, (), (f"cross-topic graph scope check failed: {exc}",)
    return (
        decision.decision == "allowed",
        decision.reasons,
        decision.read_errors,
    )


def _graph_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    selected = {**DEFAULT_GRAPH_POLICY, **dict(policy or {})}
    if selected["version"] != DEFAULT_GRAPH_POLICY["version"]:
        raise ValueError("unsupported graph policy version")
    max_depth = selected["max_depth"]
    max_visited = selected["max_visited"]
    depth_decay = float(selected["depth_decay"])
    if (
        isinstance(max_depth, bool)
        or not isinstance(max_depth, int)
        or not 0 <= max_depth <= 3
        or isinstance(max_visited, bool)
        or not isinstance(max_visited, int)
        or not 1 <= max_visited <= 10000
        or not math.isfinite(depth_decay)
        or not 0 < depth_decay <= 1
    ):
        raise ValueError("graph retrieval bounds are invalid")
    return {**selected, "depth_decay": depth_decay}


__all__ = ["DEFAULT_GRAPH_POLICY", "search_graph"]
