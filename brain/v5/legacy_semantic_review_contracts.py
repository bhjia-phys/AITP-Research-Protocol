'Contracts for legacy migration semantic review queues.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/legacy_semantic_review_contracts/part_01.py",
    "_compat_shards/legacy_semantic_review_contracts/part_02.py",
    ),
)
del _load_module_shards
