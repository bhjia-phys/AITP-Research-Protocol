"""Hash-bound, human-gated review decisions for knowledge and insight candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Mapping

from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.ids import prefixed_id
from brain.v5.knowledge_candidates import KnowledgeCandidate, diagnose_knowledge_candidate
from brain.v5.models import HumanCheckpointRecord, KnowledgeReviewDecisionRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def knowledge_candidate_hash(candidate: KnowledgeCandidate) -> str:
    return knowledge_candidate_payload_hash(asdict(candidate))


def knowledge_candidate_payload_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def record_knowledge_review_decision(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
    *,
    checkpoint_ref: PinnedRecordRef,
    decision: str,
    actor: RecordActor,
) -> WriteResult:
    existing = _candidate_decisions(ws, candidate.topic_id, candidate.candidate_id)
    if existing:
        candidate_hash = knowledge_candidate_hash(candidate)
        checkpoint_payload = asdict(checkpoint_ref)
        idempotent_retry = bool(
            len(existing) == 1
            and existing[0].candidate_hash == candidate_hash
            and existing[0].decision == decision
            and existing[0].checkpoint_ref == checkpoint_payload
            and not existing[0].supersedes_decision_ref
        )
        if not idempotent_retry:
            raise ValueError("knowledge review history exists; use supersede")
    return _record_knowledge_review_decision(
        ws,
        candidate,
        checkpoint_ref=checkpoint_ref,
        decision=decision,
        supersedes_decision_ref=None,
        actor=actor,
    )


def supersede_knowledge_review_decision(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
    *,
    prior_decision_ref: PinnedRecordRef,
    checkpoint_ref: PinnedRecordRef,
    decision: str,
    actor: RecordActor,
) -> WriteResult:
    """Append one exact replacement and reject branched review history."""

    if pin_current_record(ws, prior_decision_ref.record_ref) != prior_decision_ref:
        raise ValueError("prior knowledge review decision pin is stale")
    prior = get_record_version(ws, prior_decision_ref).record
    if not isinstance(prior, KnowledgeReviewDecisionRecord):
        raise ValueError("prior_decision_ref must pin a knowledge review decision")
    if prior.candidate_id != candidate.candidate_id or prior.topic_id != candidate.topic_id:
        raise ValueError("replacement review must preserve candidate identity and topic")
    if _decision_successors(ws, prior_decision_ref):
        raise ValueError("prior knowledge review decision already has a successor")
    return _record_knowledge_review_decision(
        ws,
        candidate,
        checkpoint_ref=checkpoint_ref,
        decision=decision,
        supersedes_decision_ref=prior_decision_ref,
        actor=actor,
    )


def _record_knowledge_review_decision(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
    *,
    checkpoint_ref: PinnedRecordRef,
    decision: str,
    supersedes_decision_ref: PinnedRecordRef | None,
    actor: RecordActor,
) -> WriteResult:
    diagnostics = diagnose_knowledge_candidate(ws, candidate)
    if diagnostics.lane not in {"grounded_knowledge", "speculative_insight"}:
        raise ValueError("knowledge review requires a knowledge or insight lane")
    if len(candidate.content_kinds) != 1:
        raise ValueError("knowledge review requires exactly one content kind")
    if diagnostics.lane == "grounded_knowledge" and not diagnostics.eligible_for_grounded_review:
        detail = [*diagnostics.missing_requirements, *diagnostics.errors]
        raise ValueError("grounded candidate is not review-ready: " + ", ".join(detail))
    if pin_current_record(ws, checkpoint_ref.record_ref) != checkpoint_ref:
        raise ValueError("knowledge review checkpoint pin is stale")
    checkpoint = get_record_version(ws, checkpoint_ref).record
    candidate_hash = knowledge_candidate_hash(candidate)
    if not isinstance(checkpoint, HumanCheckpointRecord) or not checkpoint_can_authorize_trust(checkpoint):
        raise ValueError("knowledge review requires a host-attested checkpoint")
    if checkpoint.topic_id != candidate.topic_id or checkpoint.action != "review_knowledge_candidate":
        raise ValueError("knowledge review checkpoint scope or action does not match")
    if checkpoint.request_hash != candidate_hash:
        raise ValueError("knowledge review checkpoint candidate hash does not match")
    expected_subject = {"candidate_id": candidate.candidate_id, "candidate_hash": candidate_hash}
    if expected_subject not in checkpoint.subject_refs:
        raise ValueError("knowledge review checkpoint subject does not bind the candidate hash")
    if checkpoint.decision != decision:
        raise ValueError("knowledge review decision does not match the checkpoint")
    decision_id = prefixed_id(
        "knowledge-review",
        (
            f"{candidate.candidate_id}:{candidate_hash}:{decision}:"
            f"{checkpoint_ref.content_hash}:"
            f"{supersedes_decision_ref.content_hash if supersedes_decision_ref else ''}"
        ),
        max_slug=72,
    )
    record = KnowledgeReviewDecisionRecord(
        decision_id=decision_id,
        candidate_id=candidate.candidate_id,
        candidate_hash=candidate_hash,
        candidate_lane=diagnostics.lane,
        topic_id=candidate.topic_id,
        decision=decision,
        rationale=checkpoint.rationale,
        reviewer=checkpoint.decided_by,
        checkpoint_ref=asdict(checkpoint_ref),
        candidate_payload=asdict(candidate),
        source_refs=[asdict(pin) for pin in candidate.grounding_pins],
        supersedes_decision_ref=(
            asdict(supersedes_decision_ref) if supersedes_decision_ref else {}
        ),
    )
    return RecordRepository(ws, actor=actor).write(
        "knowledge_review_decisions",
        record,
        body=f"# Knowledge Review: {decision}\n\n{checkpoint.rationale}\n",
    )


def _decision_successors(
    ws: WorkspacePaths,
    prior: PinnedRecordRef,
) -> tuple[KnowledgeReviewDecisionRecord, ...]:
    report = RecordRepository(ws, actor=_review_audit_actor()).list(
        "knowledge_review_decisions"
    )
    if report.malformed:
        raise ValueError("knowledge review registry contains malformed records")
    return tuple(
        record
        for record in report.records
        if isinstance(record, KnowledgeReviewDecisionRecord)
        and _coerce_optional_pin(record.supersedes_decision_ref) == prior
    )


def _candidate_decisions(
    ws: WorkspacePaths,
    topic_id: str,
    candidate_id: str,
) -> tuple[KnowledgeReviewDecisionRecord, ...]:
    report = RecordRepository(ws, actor=_review_audit_actor()).list(
        "knowledge_review_decisions"
    )
    if report.malformed:
        raise ValueError("knowledge review registry contains malformed records")
    return tuple(
        record
        for record in report.records
        if isinstance(record, KnowledgeReviewDecisionRecord)
        and record.topic_id == topic_id
        and record.candidate_id == candidate_id
    )


def _coerce_optional_pin(value: object) -> PinnedRecordRef | None:
    if not value:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("knowledge review supersedes ref must be an exact pin")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=int(value.get("revision") or 0),
    )


def _review_audit_actor() -> RecordActor:
    return RecordActor(actor_type="system", actor_id="knowledge-review-audit", host="aitp-v5")
