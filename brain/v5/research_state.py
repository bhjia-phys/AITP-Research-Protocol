'Conservative research-state helpers for theory projects.\n\nThese helpers compose existing typed records into a small physics-facing surface.\nThey do not mutate claim trust, topic_state, or L2 memory.\n'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/research_state/part_01.py",
    "_compat_shards/research_state/part_02.py",
    ),
)
del _load_module_shards
