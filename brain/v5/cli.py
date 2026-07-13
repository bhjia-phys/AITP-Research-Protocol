'Small JSON CLI for the AITP v5 kernel.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/cli/part_01.py",
    "_compat_shards/cli/part_02.py",
    "_compat_shards/cli/part_03.py",
    "_compat_shards/cli/part_04.py",
    "_compat_shards/cli/part_05.py",
    ),
)
del _load_module_shards
