"""Authority revalidation for source-shelf curated RAG payloads."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractResult


def _json_exact_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_exact_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_exact_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def validate_source_shelf_authority(
    payload: dict[str, Any],
    path: str,
    result: ContractResult,
    *,
    base: Any,
) -> None:
    if base is None:
        result.add(path, "source-shelf authority validation requires the local workspace base")
        return
    generation = payload.get("source_shelf_generation")
    topic_id = payload.get("source_shelf_topic_id")
    if payload.get("kind") == "curated_rag_corpus":
        policy = payload.get("index_policy")
        if not isinstance(policy, dict):
            return
        generation = policy.get("source_shelf_generation")
        topic_id = policy.get("source_shelf_topic_id")
    if not isinstance(generation, str) or not isinstance(topic_id, str):
        result.add(path, "source-shelf authority identity is malformed")
        return

    from brain.v5 import curated_rag_source_shelf as adapter
    from brain.v5.curated_rag_corpus import CATALOG_VERSION

    try:
        catalog = adapter._source_shelf_curated_rag_catalog(
            base,
            generation=generation,
            topic_id=topic_id,
            catalog_version=CATALOG_VERSION,
        )
        kind = payload.get("kind")
        if kind == "curated_rag_corpus":
            expected = catalog
        elif kind == "curated_rag_search_result":
            expected = adapter._search_source_shelf_curated_rag(
                payload.get("query"),
                limit=payload.get("requested_limit"),
                catalog=catalog,
                catalog_version=CATALOG_VERSION,
            )
        elif kind == "curated_rag_chunk":
            expected = adapter._read_source_shelf_curated_rag_chunk(
                payload.get("chunk_id"),
                catalog=catalog,
                catalog_version=CATALOG_VERSION,
            )
        else:
            result.add(path, "source-shelf authority validator does not support this payload kind")
            return
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        result.add(path, f"source-shelf authority revalidation failed: {exc}")
        return
    if not _json_exact_equal(payload, expected):
        result.add(path, "must match the payload rebuilt from the exact local source shelf")


__all__ = ["validate_source_shelf_authority"]
