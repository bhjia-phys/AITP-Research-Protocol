'Read-only bridge from legacy AITP topic folders into v5 seeds.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/legacy_bridge/part_01.py",
    "_compat_shards/legacy_bridge/part_02.py",
    ),
)
del _load_module_shards
