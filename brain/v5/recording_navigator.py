'Progressive read-only navigator for AITP v5 recording decisions.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/recording_navigator/part_01.py",
    "_compat_shards/recording_navigator/part_02.py",
    "_compat_shards/recording_navigator/part_03.py",
    ),
)
del _load_module_shards

from brain.v5.recording_batches import recording_batch_handoff
