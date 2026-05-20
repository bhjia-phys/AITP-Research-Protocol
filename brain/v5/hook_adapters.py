"""Machine-readable adapters for AITP v5 hook decisions."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.hooks import HookDecision
from brain.v5.policy import PolicyDecision, PolicyReason


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


def policy_decision_from_payload(payload: dict[str, Any], *, fallback_action: str) -> PolicyDecision:
    """Convert adapter JSON into a typed policy decision without re-evaluating policy."""

    reasons = [
        PolicyReason(
            policy_id=str(item.get("policy_id") or "policy_violation"),
            message=str(item.get("message") or ""),
            severity=str(item.get("severity") or "block"),
        )
        for item in payload.get("reasons", [])
        if isinstance(item, dict)
    ]
    required_actions = [
        str(item)
        for item in payload.get("required_actions", [])
        if isinstance(item, str) and item
    ]
    return PolicyDecision(
        allowed=bool(payload.get("allowed", True)),
        action=str(payload.get("action") or fallback_action),
        reasons=reasons,
        required_actions=required_actions,
    )
