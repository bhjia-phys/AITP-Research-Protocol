"""Persisted, lane-aware deep recall and trust-neutral prerequisite gates."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.lifecycle_models import RecallAuditRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.query_index_locking import acquire_canonical_mutation_lease
from brain.v5.recall_audit_contracts import (
    validate_recall_audit,
    validate_recall_request_shape,
)
from brain.v5.recall_audit_execution import (
    assign_exact_refs,
    build_audit_record,
    resolve_requested_exact_refs,
    run_ordered_lanes,
    validate_after_write,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy
from brain.v5.research_scope import ScopeResolutionError, resolve_session_scope


class RecallAuditError(RuntimeError):
    """Raised when deep recall cannot produce a valid canonical audit."""


@dataclass(frozen=True)
class RecallRequest:
    session_id: str
    query_text: str
    normalized_intent: str
    required_families: tuple[str, ...]
    exact_refs: tuple[str, ...] = ()
    focus_set_ref: str = ""
    include_program_scope: bool = True
    include_discovery: bool = False
    top_k: int = 20

    def __post_init__(self) -> None:
        validate_recall_request_shape(self)


@dataclass(frozen=True)
class RecallGateDecision:
    action: str
    allowed: bool
    reason_code: str
    required_actions: tuple[str, ...]
    audit_ref: str
    can_update_claim_trust: bool = False


def run_recall_audit(
    ws: WorkspacePaths,
    request: RecallRequest,
    *,
    actor: RecordActor,
) -> RecallAuditRecord:
    """Run ordered deep recall and persist only coverage, refs, and scores."""

    if not isinstance(request, RecallRequest):
        raise TypeError("request must be a RecallRequest")
    if not isinstance(actor, RecordActor):
        raise TypeError("actor must be a RecordActor")
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    with acquire_canonical_mutation_lease(ws, timeout_seconds=10.0):
        repository = RecordRepository(ws, actor=actor)
        try:
            scope = resolve_session_scope(
                ws,
                request.session_id,
                include_discovery=request.include_discovery,
                focus_set_ref=request.focus_set_ref,
            )
        except (ScopeResolutionError, TypeError, ValueError) as exc:
            raise RecallAuditError(f"cannot resolve recall scope: {exc}") from exc
        canonical_exact, exact_topics, unreadable_exact = resolve_requested_exact_refs(
            repository,
            request.exact_refs,
        )
        assignments, out_of_scope = assign_exact_refs(
            canonical_exact,
            exact_topics,
            scope,
            include_program_scope=request.include_program_scope,
            include_discovery=request.include_discovery,
        )
        lanes = run_ordered_lanes(ws, request, scope, assignments)
        missing_exact = tuple(dict.fromkeys([*unreadable_exact, *out_of_scope]))
        record = build_audit_record(
            ws,
            request=request,
            scope=scope,
            canonical_exact=canonical_exact,
            missing_exact=missing_exact,
            lanes=lanes,
        )
        errors = validate_recall_audit(record)
        if errors:
            raise RecallAuditError("invalid recall audit: " + "; ".join(errors))
        result = repository.write(
            "recall_audits",
            record,
            body=_audit_body(record),
            policy=WritePolicy(mode="create_or_idempotent"),
        )
        try:
            validate_after_write(ws, record)
        except RuntimeError as exc:
            raise RecallAuditError(str(exc)) from exc
        persisted = repository.read(result.record_ref)
        if persisted.status != "found" or not isinstance(persisted.record, RecallAuditRecord):
            raise RecallAuditError("persisted recall audit is not exactly readable")
        return persisted.record


def evaluate_recall_prerequisite(
    audit: RecallAuditRecord,
    action: str,
) -> RecallGateDecision:
    """Evaluate one high-cost action without granting any trust authority."""

    if not isinstance(audit, RecallAuditRecord):
        raise TypeError("audit must be a RecallAuditRecord")
    normalized_action = str(action or "").strip()
    if not normalized_action:
        raise ValueError("action must be non-empty")
    audit_ref = f"recall_audit:{audit.audit_id}"
    if audit.unchecked_families:
        return _blocked_gate(
            normalized_action,
            "required_family_unchecked",
            ("run_recall_audit", "repair_or_expand_required_family_scope"),
            audit_ref,
        )
    if audit.missing_exact_refs:
        return _blocked_gate(
            normalized_action,
            "required_exact_ref_missing",
            ("resolve_required_exact_refs", "run_recall_audit"),
            audit_ref,
        )
    if audit.read_errors:
        return _blocked_gate(
            normalized_action,
            "recall_read_error",
            ("repair_recall_read_errors", "run_recall_audit"),
            audit_ref,
        )
    if audit.truncated:
        return _blocked_gate(
            normalized_action,
            "recall_truncated",
            ("increase_or_page_recall_scope", "run_recall_audit"),
            audit_ref,
        )
    if audit.stale or not audit.content_verified or not audit.exhaustive:
        return _blocked_gate(
            normalized_action,
            "required_recall_not_exhaustive",
            ("repair_recall_index", "run_recall_audit"),
            audit_ref,
        )
    return RecallGateDecision(
        action=normalized_action,
        allowed=True,
        reason_code="recall_prerequisite_satisfied",
        required_actions=(),
        audit_ref=audit_ref,
        can_update_claim_trust=False,
    )


def _blocked_gate(
    action: str,
    reason_code: str,
    required_actions: tuple[str, ...],
    audit_ref: str,
) -> RecallGateDecision:
    return RecallGateDecision(
        action=action,
        allowed=False,
        reason_code=reason_code,
        required_actions=required_actions,
        audit_ref=audit_ref,
        can_update_claim_trust=False,
    )


def _audit_body(record: RecallAuditRecord) -> str:
    return (
        f"# Recall Audit: {record.normalized_intent}\n\n"
        f"Session: `{record.session_id}`\n"
        f"Topic: `{record.topic_id}`\n"
        f"Query: {record.query_text}\n\n"
        "Coverage facts and exact refs only; retrieved summaries are not evidence.\n"
    )
