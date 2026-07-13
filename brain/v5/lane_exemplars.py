'vNext lane-specific exemplar records and closure manifest.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/lane_exemplars/part_01.py",
    "_compat_shards/lane_exemplars/part_02.py",
    "_compat_shards/lane_exemplars/part_03.py",
    ),
)
del _load_module_shards
