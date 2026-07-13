"""Validation and deterministic helpers for canonical session closeouts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

from brain.v5.lifecycle_models import CloseoutBoundaryItem, SessionCloseoutRecord
from brain.v5.research_scope_contracts import canonical_typed_ref


BOUNDARY_CLASSES = frozenset(
    {"proved", "conditional", "finite_evidence", "open_gap", "process_only"}
)
CAN_SAY_BOUNDARY_CLASSES = frozenset(
    {"proved", "conditional", "finite_evidence", "process_only"}
)


@dataclass(frozen=True)
class BoundaryClassification:
    accepted: tuple[CloseoutBoundaryItem, ...]
    unverified: tuple[CloseoutBoundaryItem, ...]
    missing_requirements: tuple[str, ...]


def validate_closeout_request_shape(request: object) -> None:
    session_id = str(getattr(request, "session_id", "") or "").strip()
    milestone_id = str(getattr(request, "milestone_id", "") or "").strip()
    if not session_id:
        raise ValueError("session_id must be non-empty")
    if not milestone_id:
        raise ValueError("milestone_id must be non-empty")
    for field_name in (
        "completed_work",
        "can_say",
        "cannot_say",
        "open_gaps",
        "failed_routes",
        "next_actions",
        "source_record_refs",
        "pending_candidate_batch_refs",
        "reusable_workflow_candidate_refs",
    ):
        if not isinstance(getattr(request, field_name, None), tuple):
            raise TypeError(f"{field_name} must be a tuple")
    for field_name in ("can_say", "cannot_say", "open_gaps", "failed_routes"):
        if any(
            not isinstance(item, CloseoutBoundaryItem)
            for item in getattr(request, field_name)
        ):
            raise TypeError(f"{field_name} must contain CloseoutBoundaryItem values")
    for field_name in (
        "completed_work",
        "next_actions",
        "source_record_refs",
        "pending_candidate_batch_refs",
        "reusable_workflow_candidate_refs",
    ):
        if any(not str(value or "").strip() for value in getattr(request, field_name)):
            raise ValueError(f"{field_name} must contain non-empty values")


def deterministic_closeout_id(session_id: str, milestone_id: str) -> str:
    payload = json.dumps(
        {"milestone_id": milestone_id, "session_id": session_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"session-closeout-{digest}"


def classify_boundary_items(
    items: Iterable[CloseoutBoundaryItem],
    *,
    lane: str,
    resolved_refs: dict[str, str],
) -> BoundaryClassification:
    accepted: list[CloseoutBoundaryItem] = []
    unverified: list[CloseoutBoundaryItem] = []
    missing: list[str] = []
    allowed_classes = CAN_SAY_BOUNDARY_CLASSES if lane == "can_say" else BOUNDARY_CLASSES
    for index, item in enumerate(items):
        text = str(item.text or "").strip()
        source_refs = [resolved_refs.get(ref, "") for ref in item.source_refs]
        valid_refs = [ref for ref in source_refs if ref]
        valid = bool(text) and item.boundary_class in allowed_classes
        if item.requires_exact_expansion is not True or item.can_update_claim_trust is not False:
            valid = False
        if not item.source_refs or len(valid_refs) != len(item.source_refs):
            valid = False
        normalized = CloseoutBoundaryItem(
            text=text or str(item.text or ""),
            boundary_class=str(item.boundary_class or ""),
            source_refs=valid_refs,
            scope=str(item.scope or ""),
            conditions=[str(value) for value in item.conditions if str(value).strip()],
            requires_exact_expansion=True,
            can_update_claim_trust=False,
        )
        if valid:
            accepted.append(normalized)
        else:
            unverified.append(normalized)
            missing.append(f"unverified_{lane}[{index}]")
    return BoundaryClassification(
        accepted=tuple(accepted),
        unverified=tuple(unverified),
        missing_requirements=tuple(missing),
    )


def checked_families_for_refs(refs: Iterable[str]) -> tuple[str, ...]:
    families: set[str] = set()
    for ref in refs:
        try:
            _canonical, spec, _record_id = canonical_typed_ref(ref)
        except ValueError:
            continue
        if spec.family != "session_closeouts":
            families.add(spec.family)
    return tuple(sorted(families))


def retrieval_scope_token(
    *,
    checked_families: Iterable[str],
    family_state_tokens: dict[str, str],
    family_content_watermarks: dict[str, str],
) -> str:
    families = tuple(sorted(set(checked_families)))
    payload = {
        "checked_families": families,
        "family_content_watermarks": {
            family: family_content_watermarks.get(family, "") for family in families
        },
        "family_state_tokens": {
            family: family_state_tokens.get(family, "") for family in families
        },
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_closeout_record(record: SessionCloseoutRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if not record.closeout_id:
        errors.append("closeout_id must be non-empty")
    if not record.session_id or not record.topic_id or not record.milestone_id:
        errors.append("session_id, topic_id, and milestone_id must be non-empty")
    if not record.focus_set_ref:
        errors.append("focus_set_ref must be non-empty")
    if not record.checked_families:
        errors.append("checked_families must be non-empty")
    if set(record.family_state_tokens) != set(record.checked_families):
        errors.append("family_state_tokens must exactly cover checked_families")
    if set(record.family_content_watermarks) != set(record.checked_families):
        errors.append("family_content_watermarks must exactly cover checked_families")
    if not record.retrieval_scope_token:
        errors.append("retrieval_scope_token must be non-empty")
    if record.can_update_claim_trust is not False:
        errors.append("can_update_claim_trust must be false")
    for item in record.can_say:
        if item.boundary_class not in CAN_SAY_BOUNDARY_CLASSES or not item.source_refs:
            errors.append("can_say contains an unsupported model-facing boundary")
    return tuple(errors)
