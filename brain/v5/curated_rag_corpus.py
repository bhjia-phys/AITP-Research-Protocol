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
