"""Stable facade for bounded host-neutral research moments."""

from brain.v5.research_moment_application import (
    ResearchMomentApplicationError,
    apply_research_moment_decision,
    research_moment_receipt_path,
)
from brain.v5.research_moment_contracts import (
    MomentReceipt,
    ResearchEvent,
    ResearchMomentDecision,
)
from brain.v5.research_moment_policy import decide_research_moment


__all__ = [
    "MomentReceipt",
    "ResearchEvent",
    "ResearchMomentApplicationError",
    "ResearchMomentDecision",
    "apply_research_moment_decision",
    "decide_research_moment",
    "research_moment_receipt_path",
]
