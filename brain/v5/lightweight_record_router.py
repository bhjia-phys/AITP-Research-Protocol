'Lightweight record router — plan-only surface for short research events.\n\nThis surface reads typed records and a short event summary, then returns a\n*typed write plan*. It never writes records and never applies trust updates.\n\nHard trust boundaries (enforced everywhere, including the contract):\n- ``can_update_claim_trust`` is always False\n- ``summary_inputs_trusted`` is always False\n- ``orientation_only`` is always True\n- the relation-map may be consulted for *locating* a claim, never as evidence\n- runtime failure is recorded as runtime/environment failure, never auto-judged\n  as an algorithm failure\n- an old plot/old convention is never promoted to new-report evidence\n- mentioning a claim in ``event_summary`` does not raise its confidence\n- when one ``sensemaking_report`` is enough, the plan is minimal — do not split\n  into five redundant records\n'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/lightweight_record_router/part_01.py",
    "_compat_shards/lightweight_record_router/part_02.py",
    "_compat_shards/lightweight_record_router/part_03.py",
    ),
)
del _load_module_shards
