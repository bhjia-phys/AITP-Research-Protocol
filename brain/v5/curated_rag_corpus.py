'Curated heuristic RAG corpus contracts for AITP v5 hosts.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/curated_rag_corpus/part_01.py",
    "_compat_shards/curated_rag_corpus/part_02.py",
    "_compat_shards/curated_rag_corpus/part_03.py",
    ),
)
del _load_module_shards


_legacy_curated_rag_corpus = curated_rag_corpus
_legacy_read_curated_rag_chunk = read_curated_rag_chunk
_legacy_search_curated_rag_corpus = search_curated_rag_corpus

def curated_rag_corpus(
    base=None,
    *,
    source_shelf_generation: str = "",
    topic_id: str = "",
):
    """Return the legacy corpus or an exact source-shelf projection."""

    if not source_shelf_generation:
        if topic_id:
            raise ValueError("topic_id requires source_shelf_generation")
        return _legacy_curated_rag_corpus(base)
    from brain.v5 import curated_rag_source_shelf as source_shelf

    return source_shelf._source_shelf_curated_rag_catalog(
        base,
        generation=source_shelf_generation,
        topic_id=topic_id,
        catalog_version=CATALOG_VERSION,
    )


def search_curated_rag_corpus(
    query: str,
    *,
    limit: int = 5,
    base=None,
    source_shelf_generation: str = "",
    topic_id: str = "",
):
    """Search the legacy corpus or an exact source-shelf projection."""

    if not source_shelf_generation:
        if topic_id:
            raise ValueError("topic_id requires source_shelf_generation")
        return _legacy_search_curated_rag_corpus(query, limit=limit, base=base)
    catalog = curated_rag_corpus(
        base,
        source_shelf_generation=source_shelf_generation,
        topic_id=topic_id,
    )
    from brain.v5 import curated_rag_source_shelf as source_shelf

    return source_shelf._search_source_shelf_curated_rag(
        query,
        limit=limit,
        catalog=catalog,
        catalog_version=CATALOG_VERSION,
    )


def read_curated_rag_chunk(
    chunk_id: str,
    *,
    base=None,
    source_shelf_generation: str = "",
    topic_id: str = "",
):
    """Read a legacy chunk or one exact source-shelf passage projection."""

    if not source_shelf_generation:
        if topic_id:
            raise ValueError("topic_id requires source_shelf_generation")
        return _legacy_read_curated_rag_chunk(chunk_id, base=base)
    catalog = curated_rag_corpus(
        base,
        source_shelf_generation=source_shelf_generation,
        topic_id=topic_id,
    )
    from brain.v5 import curated_rag_source_shelf as source_shelf

    return source_shelf._read_source_shelf_curated_rag_chunk(
        chunk_id,
        catalog=catalog,
        catalog_version=CATALOG_VERSION,
    )
