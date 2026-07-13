'Record lifecycle operations: rehome and supersede.\n\nEvery lifecycle change produces exactly one append-only ``lifecycle_event`` record under\n``registry/lifecycle_events/``. Records themselves are never deleted; they gain lazy-\ncompatible frontmatter fields (see ``ClaimRecord`` / ``EvidenceRecord``). The relation-map\nfilters on ``lifecycle_status`` to exclude non-active records from the current conclusion.\n'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/lifecycle_events/part_01.py",
    "_compat_shards/lifecycle_events/part_02.py",
    ),
)
del _load_module_shards
