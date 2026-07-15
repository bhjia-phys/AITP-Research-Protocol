"""Hash-bound, human-gated review decisions for knowledge and insight candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.ids import prefixed_id
from brain.v5.knowledge_candidates import KnowledgeCandidate, diagnose_knowledge_candidate
from brain.v5.models import HumanCheckpointRecord, KnowledgeReviewDecisionRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def knowledge_candidate_hash(candidate: KnowledgeCandidate) -> str:
    encoded = json.dumps(
        asdict(candidate),
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
    diagnostics = diagnose_knowledge_candidate(ws, candidate)
    if diagnostics.lane not in {"grounded_knowledge", "speculative_insight"}:
        raise ValueError("knowledge review requires a knowledge or insight lane")
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
        f"{candidate.candidate_id}:{candidate_hash}:{decision}:{checkpoint_ref.content_hash}",
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
        source_refs=[asdict(pin) for pin in candidate.grounding_pins],
    )
    return RecordRepository(ws, actor=actor).write(
        "knowledge_review_decisions",
        record,
        body=f"# Knowledge Review: {decision}\n\n{checkpoint.rationale}\n",
    )
