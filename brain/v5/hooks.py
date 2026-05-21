"""Hook decision helpers for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.ids import prefixed_id
from brain.v5.policy import PolicyDecision
from brain.v5.trace import TraceEvent


@dataclass
class HookDecision:
    mode: str
    block: bool
    message: str
    required_actions: list[str] = field(default_factory=list)


_HIGH_RISK_LEVELS = {"rigorous", "adversarial"}
_CRITICAL_ACTIONS = {
    "create_promotion_packet",
    "apply_promotion_packet",
    "decide_human_checkpoint",
    "promote_to_l2",
    "apply_harness_patch",
    "destructive_action",
    "remote_execution",
    "expensive_compute",
}


def decide_pre_tool_use(
    *,
    action: str,
    risk_level: str,
    policy_decision: PolicyDecision,
) -> HookDecision:
    """Decide whether a pre-tool hook should log, warn, or block."""

    if policy_decision.allowed:
        return HookDecision(
            mode="log",
            block=False,
            message=_short(f"logged {action}; no policy block"),
        )

    required = list(policy_decision.required_actions)
    reason = _reason_summary(policy_decision)
    should_block = _has_hard_block(policy_decision) or risk_level in _HIGH_RISK_LEVELS or action in _CRITICAL_ACTIONS
    if should_block:
        return HookDecision(
            mode="block",
            block=True,
            message=_short(f"blocked {action}; {reason}; required: {', '.join(required)}"),
            required_actions=required,
        )
    return HookDecision(
        mode="warn",
        block=False,
        message=_short(f"warn {action}; {reason}; required soon: {', '.join(required)}"),
        required_actions=required,
    )


def post_tool_use_trace_event(
    *,
    session_id: str,
    topic_id: str,
    risk_level: str,
    claim_id: str,
    tool_name: str,
    evidence_status: str,
) -> TraceEvent:
    """Create a compact trace event after tool use."""

    summary = _short(f"{tool_name} completed with evidence_status={evidence_status}", limit=120)
    event_id = prefixed_id("event", f"{session_id}:{topic_id}:{claim_id}:{tool_name}:{evidence_status}", max_slug=64)
    return TraceEvent(
        event_id=event_id,
        session_id=session_id,
        topic_id=topic_id,
        event_type="tool_run_recorded",
        risk_level=risk_level,
        claim_id=claim_id,
        payload={
            "tool_name": tool_name,
            "evidence_status": evidence_status,
            "summary": summary,
        },
    )


def decide_pre_commit(
    *,
    changed_files: list[str],
    test_refs: list[str],
    evolution_note: str,
) -> HookDecision:
    """Require tests and an evolution note when committing harness changes."""

    if not any(_is_harness_file(path) for path in changed_files):
        return HookDecision(mode="log", block=False, message="logged non-harness commit")

    required: list[str] = []
    if not test_refs:
        required.append("add_regression_test")
    if not evolution_note.strip():
        required.append("add_evolution_note")

    if required:
        return HookDecision(
            mode="block",
            block=True,
            message=_short(f"blocked harness commit; required: {', '.join(required)}"),
            required_actions=required,
        )
    return HookDecision(
        mode="log",
        block=False,
        message="logged harness commit with tests and evolution note",
    )


def _is_harness_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith("brain/v5/") or normalized.startswith("docs/superpowers/plans/")


def _has_hard_block(decision: PolicyDecision) -> bool:
    return any(reason.severity == "hard_block" for reason in decision.reasons)


def _reason_summary(decision: PolicyDecision) -> str:
    if not decision.reasons:
        return "policy violation"
    return "; ".join(reason.policy_id for reason in decision.reasons)


def _short(message: str, *, limit: int = 160) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3].rstrip() + "..."
