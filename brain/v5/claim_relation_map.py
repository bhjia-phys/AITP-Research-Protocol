'Derived claim/evidence relation map for recovery briefs.\n\nThis surface is deliberately read-only.  It compiles existing typed records into\nan explicit conclusion-boundary view, but it is never a source of claim trust.\n'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/claim_relation_map/part_01.py",
    "_compat_shards/claim_relation_map/part_02.py",
    "_compat_shards/claim_relation_map/part_03.py",
    ),
)
del _load_module_shards
