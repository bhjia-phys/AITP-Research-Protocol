'Codex App facade surfaces for compact, progressive AITP v5 use.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/codex_facade/part_01.py",
    "_compat_shards/codex_facade/part_02.py",
    "_compat_shards/codex_facade/part_03.py",
    "_compat_shards/codex_facade/part_04.py",
    "_compat_shards/codex_facade/part_05.py",
    ),
)
del _load_module_shards
