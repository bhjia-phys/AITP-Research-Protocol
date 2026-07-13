'Batch checkpoint support for low-interruption research bursts.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/quiet_checkpoint/part_01.py",
    "_compat_shards/quiet_checkpoint/part_02.py",
    ),
)
del _load_module_shards
