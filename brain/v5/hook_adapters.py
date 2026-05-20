"""Machine-readable adapters for AITP v5 hook decisions."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.hooks import HookDecision


def hook_decision_payload(decision: HookDecision, *, hook_name: str) -> dict[str, Any]:
    """Render a hook decision as short JSON-friendly output."""

    return {
        "kind": "hook_decision",
        "hook_name": hook_name,
        **asdict(decision),
        "exit_code": hook_exit_code(decision),
        "summary_inputs_trusted": False,
    }


def hook_exit_code(decision: HookDecision) -> int:
    """Return the shell exit code for a hook decision."""

    return 2 if decision.block else 0
