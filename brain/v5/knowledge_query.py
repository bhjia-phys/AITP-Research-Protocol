"""One lineage-bound entrypoint for hybrid physics-knowledge retrieval."""

from __future__ import annotations

from brain.v5.formula_retrieval import search_formula
from brain.v5.graph_retrieval import search_graph
from brain.v5.knowledge_retrieval import KnowledgeQuery, search_fielded_lexical
from brain.v5.knowledge_snapshot import KnowledgeSnapshot, build_knowledge_snapshot
from brain.v5.paths import WorkspacePaths
from brain.v5.retrieval_fusion import (
    DenseRetrievalAdapter,
    fuse_knowledge_rankings,
    search_dense_optional,
)


def retrieve_knowledge(
    ws: WorkspacePaths,
    query: KnowledgeQuery,
    *,
    source_shelf_generation: str = "",
    source_shelf_topic_id: str = "",
    freshness_mode: str = "strong",
    dense_adapter: DenseRetrievalAdapter | None = None,
):
    """Run every retrieval component against one immutable snapshot."""

    snapshot = build_knowledge_snapshot(
        ws,
        source_shelf_generation=source_shelf_generation,
        source_shelf_topic_id=source_shelf_topic_id,
        freshness_mode=freshness_mode,
    )
    return retrieve_knowledge_snapshot(
        snapshot,
        query,
        workspace=ws,
        dense_adapter=dense_adapter,
    )


def retrieve_knowledge_snapshot(
    snapshot: KnowledgeSnapshot,
    query: KnowledgeQuery,
    *,
    workspace: WorkspacePaths,
    dense_adapter: DenseRetrievalAdapter | None = None,
):
    """Run every component against a caller-owned immutable snapshot."""

    components = (
        search_fielded_lexical(snapshot, query),
        search_formula(snapshot, query),
        search_graph(snapshot, query, workspace=workspace),
        search_dense_optional(snapshot, query, dense_adapter),
    )
    return fuse_knowledge_rankings(components, query)


__all__ = ["retrieve_knowledge", "retrieve_knowledge_snapshot"]
