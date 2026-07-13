"Active-claim focus reconciliation for AITP v5 sessions.\n\nThis module is intentionally conservative.  It can detect and explain that a\nsession's active claim may no longer match the current durable record focus, but\nit never changes the binding unless a caller uses the explicit confirmation\noperation.  Detection is an orientation-only surface; confirmation writes an\naudit record and then updates only the session binding.\n"

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/active_claim_focus/part_01.py",
    "_compat_shards/active_claim_focus/part_02.py",
    ),
)
del _load_module_shards
