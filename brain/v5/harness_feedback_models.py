"""Typed records for review-only Harness Feedback cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class HarnessFeedbackCaseRecord:
    """One observed AITP or host friction case awaiting human review."""

    case_id: str
    topic_id: str
    source_fingerprint: str
    content_fingerprint: str
    problem_type: str
    friction: str
    expected_behavior: str
    actual_behavior: str
    impact: str
    reproduction_steps: tuple[str, ...]
    host_id: str
    runtime_context: dict[str, Any]
    source_refs: tuple[str, ...]
    proposed_direction: str
    affected_capability: str
    affected_record_family: str
    status: str
    reviewer: str
    duplicate_of_refs: tuple[str, ...]
    related_case_refs: tuple[str, ...]
    supersedes_case_refs: tuple[str, ...]
    created_at: str
    updated_at: str
    requires_human_review: bool = True
    orientation_only: bool = True
    can_modify_harness: bool = False
    can_emit_skill_artifacts: bool = False
    can_install_skill_artifacts: bool = False
    can_update_claim_trust: bool = False
    kind: str = "harness_feedback_case"

    def __post_init__(self) -> None:
        for field_name in (
            "reproduction_steps",
            "source_refs",
            "duplicate_of_refs",
            "related_case_refs",
            "supersedes_case_refs",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name) or ()))
        if isinstance(self.runtime_context, Mapping):
            object.__setattr__(self, "runtime_context", dict(self.runtime_context))

