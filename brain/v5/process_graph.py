'Read-only process graph slice over AITP v5 typed records.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/process_graph/part_01.py",
    "_compat_shards/process_graph/part_02.py",
    "_compat_shards/process_graph/part_03.py",
    "_compat_shards/process_graph/part_04.py",
    "_compat_shards/process_graph/part_05.py",
    "_compat_shards/process_graph/part_06.py",
    ),
)
del _load_module_shards
