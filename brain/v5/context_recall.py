"""Explicit persisted-recall facts for bounded model-facing context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.lifecycle_models import RecallAuditRecord
from brain.v5.record_repository import RecordRepository


class RecallContextError(RuntimeError):
    """Raised when an explicitly requested recall audit is not relevant or readable."""


@dataclass(frozen=True)
class RecallContextFacts:
    audit_ref: str = ""
    coverage: dict[str, Any] = field(default_factory=dict)
    record_refs: tuple[str, ...] = ()
    expansion_refs: tuple[str, ...] = ()
    process_refs: tuple[str, ...] = ()
    lines: tuple[str, ...] = ()
    can_claim_no_result: bool = False
    partial: bool = False


def build_recall_context_facts(
    repository: RecordRepository,
    *,
    audit_ref: str,
    session_id: str,
    topic_id: str,
    disclosure_level: str,
) -> RecallContextFacts:
    normalized_ref = str(audit_ref or "").strip()
    if not normalized_ref:
        return RecallContextFacts()
    if disclosure_level not in {"startup_orientation", "normal_research"}:
        raise RecallContextError(
            "recall_audit_ref is allowed only for startup_orientation or normal_research"
        )
    result = repository.read(normalized_ref)
    if result.status != "found" or not isinstance(result.record, RecallAuditRecord):
        detail = result.issue.message if result.issue else result.status
        raise RecallContextError(f"recall audit is not exactly readable: {detail}")
    audit = result.record
    canonical_ref = f"recall_audit:{audit.audit_id}"
    if canonical_ref != normalized_ref:
        raise RecallContextError("recall audit ref is not canonical")
    if audit.session_id != session_id or audit.topic_id != topic_id:
        raise RecallContextError("recall audit belongs to another session or topic")
    can_claim = bool(
        disclosure_level == "normal_research"
        and audit.can_claim_no_result
        and audit.exhaustive
        and audit.content_verified
        and not audit.stale
        and not audit.truncated
        and not audit.top_refs
        and not audit.read_errors
        and not audit.missing_exact_refs
    )
    partial = bool(
        audit.stale
        or not audit.content_verified
        or not audit.exhaustive
        or audit.truncated
        or audit.read_errors
        or audit.missing_exact_refs
    )
    coverage = {
        "recall_audit_ref": canonical_ref,
        "recall_query_text": audit.query_text,
        "recall_normalized_intent": audit.normalized_intent,
        "recall_required_families": list(audit.required_families),
        "recall_checked_families": list(audit.checked_families),
        "recall_unchecked_families": list(audit.unchecked_families),
        "recall_missing_exact_refs": list(audit.missing_exact_refs),
        "recall_read_errors": list(audit.read_errors),
        "recall_content_verified": bool(audit.content_verified),
        "recall_exhaustive": bool(audit.exhaustive),
        "recall_stale": bool(audit.stale),
        "recall_truncated": bool(audit.truncated),
        "recall_can_claim_no_result": can_claim,
    }
    expansion_refs = tuple(dict.fromkeys([canonical_ref, *audit.top_refs]))
    lines = (
        f"Recall audit: {canonical_ref}",
        f"Recall query boundary: {audit.normalized_intent} | {audit.query_text}",
        (
            "Recall coverage: "
            f"content_verified={str(bool(audit.content_verified)).lower()}; "
            f"exhaustive={str(bool(audit.exhaustive)).lower()}; "
            f"can_claim_no_result={str(can_claim).lower()}."
        ),
        "Recall results remain exact-expansion handles and are not evidence.",
    )
    return RecallContextFacts(
        audit_ref=canonical_ref,
        coverage=coverage,
        record_refs=(canonical_ref,),
        expansion_refs=expansion_refs,
        process_refs=(canonical_ref,),
        lines=lines,
        can_claim_no_result=can_claim,
        partial=partial,
    )
