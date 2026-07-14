'Plan-only completeness audit for Codex closeout and quiet checkpoints.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/closeout_completeness/part_01.py",
    "_compat_shards/closeout_completeness/part_02.py",
    "_compat_shards/closeout_completeness/part_03.py",
    ),
)
del _load_module_shards

from brain.v5.recording_batches import coalesce_closeout_recording_batch
