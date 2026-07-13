'Host-agnostic policy for research moments in a process graph slice.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/moment_policy/part_01.py",
    "_compat_shards/moment_policy/part_02.py",
    "_compat_shards/moment_policy/part_03.py",
    ),
)
del _load_module_shards
