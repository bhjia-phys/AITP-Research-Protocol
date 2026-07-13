'Curated legacy-topic migration into v5 typed records.\n\nThe generic legacy bridge preserves files and candidate notes.  This module\nadds a small, explicit curation layer for priority theoretical-physics topics\nwhose current scientific status is known well enough to become typed v5\nrecords: active claim, evidence, status, validation contract, open obligations,\nand a topic-local migration index.\n'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/curated_legacy_migration/part_01.py",
    "_compat_shards/curated_legacy_migration/part_02.py",
    ),
)
del _load_module_shards
