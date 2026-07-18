"""Contracts for generic, review-only Harness Feedback cases."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from brain.v5.harness_feedback_models import HarnessFeedbackCaseRecord


_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(
    {
        "pending_review",
        "accepted",
        "rejected",
        "resolved",
        "duplicate",
        "superseded",
    }
)


@dataclass(frozen=True)
class HarnessFeedbackCaseRequest:
    """Observed facts from research runtime, before canonical persistence."""

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
    topic_id: str = ""
    status: str = "pending_review"
    reviewer: str = ""
    duplicate_of_refs: tuple[str, ...] = ()
    related_case_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "reproduction_steps",
            "source_refs",
            "duplicate_of_refs",
            "related_case_refs",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name) or ()))
        if isinstance(self.runtime_context, Mapping):
            object.__setattr__(self, "runtime_context", dict(self.runtime_context))


def validate_harness_feedback_request(request: HarnessFeedbackCaseRequest) -> tuple[str, ...]:
    errors: list[str] = []
    for field_name in (
        "problem_type",
        "friction",
        "expected_behavior",
        "actual_behavior",
        "impact",
        "host_id",
        "proposed_direction",
        "affected_capability",
        "affected_record_family",
    ):
        if not str(getattr(request, field_name) or "").strip():
            errors.append(f"{field_name} must be non-empty")
    if not request.reproduction_steps or any(
        not str(item).strip() for item in request.reproduction_steps
    ):
        errors.append("reproduction_steps must contain non-empty steps")
    if not isinstance(request.runtime_context, Mapping):
        errors.append("runtime_context must be a mapping")
    if not request.source_refs or any(not _is_typed_ref(item) for item in request.source_refs):
        errors.append("source_refs must contain typed record refs")
    if request.status not in _STATUSES:
        errors.append(f"status must be one of {', '.join(sorted(_STATUSES))}")
    for field_name in ("duplicate_of_refs", "related_case_refs"):
        if any(not _is_typed_ref(item) for item in getattr(request, field_name)):
            errors.append(f"{field_name} must contain typed record refs")
    return tuple(errors)


def require_valid_harness_feedback_request(
    request: HarnessFeedbackCaseRequest,
) -> HarnessFeedbackCaseRequest:
    errors = validate_harness_feedback_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    return request


def validate_harness_feedback_case(record: HarnessFeedbackCaseRecord) -> tuple[str, ...]:
    request = HarnessFeedbackCaseRequest(
        topic_id=record.topic_id,
        problem_type=record.problem_type,
        friction=record.friction,
        expected_behavior=record.expected_behavior,
        actual_behavior=record.actual_behavior,
        impact=record.impact,
        reproduction_steps=record.reproduction_steps,
        host_id=record.host_id,
        runtime_context=record.runtime_context,
        source_refs=record.source_refs,
        proposed_direction=record.proposed_direction,
        affected_capability=record.affected_capability,
        affected_record_family=record.affected_record_family,
        status=record.status,
        reviewer=record.reviewer,
        duplicate_of_refs=record.duplicate_of_refs,
        related_case_refs=record.related_case_refs,
    )
    errors = list(validate_harness_feedback_request(request))
    if not record.case_id.startswith("harness-feedback-"):
        errors.append("case_id must use the harness-feedback namespace")
    for field_name in ("source_fingerprint", "content_fingerprint"):
        if not _FINGERPRINT_RE.fullmatch(str(getattr(record, field_name) or "")):
            errors.append(f"{field_name} must be a lowercase SHA-256 hex digest")
    for field_name in ("created_at", "updated_at"):
        try:
            datetime.fromisoformat(str(getattr(record, field_name) or ""))
        except ValueError:
            errors.append(f"{field_name} must be an ISO-8601 timestamp")
    if record.kind != "harness_feedback_case":
        errors.append("kind must be harness_feedback_case")
    if not record.requires_human_review:
        errors.append("requires_human_review must remain true")
    if not record.orientation_only:
        errors.append("orientation_only must remain true")
    for field_name in (
        "can_modify_harness",
        "can_emit_skill_artifacts",
        "can_install_skill_artifacts",
        "can_update_claim_trust",
    ):
        if getattr(record, field_name) is not False:
            errors.append(f"{field_name} must remain false")
    if any(not _is_typed_ref(item) for item in record.supersedes_case_refs):
        errors.append("supersedes_case_refs must contain typed or pinned record refs")
    return tuple(errors)


def require_valid_harness_feedback_case(
    record: HarnessFeedbackCaseRecord,
) -> HarnessFeedbackCaseRecord:
    errors = validate_harness_feedback_case(record)
    if errors:
        raise ValueError("; ".join(errors))
    return record


def _is_typed_ref(value: Any) -> bool:
    candidate = str(value or "").strip()
    if not candidate or ":" not in candidate:
        return False
    base = candidate.split("@sha256:", 1)[0]
    kind, separator, record_id = base.partition(":")
    return bool(separator and kind.strip() and record_id.strip())

