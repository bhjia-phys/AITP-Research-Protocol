"""Review-gated promotion of knowledge and insight candidates."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from brain.v5.ids import prefixed_id
from brain.v5.knowledge_candidates import KnowledgeCandidate, diagnose_knowledge_candidate
from brain.v5.knowledge_review import (
    knowledge_candidate_hash,
    knowledge_candidate_payload_hash,
)
from brain.v5.models import (
    InsightRecord,
    KnowledgeReviewDecisionRecord,
    PhysicsAssertionRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.physics_assertions import record_physics_assertion
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def promote_knowledge_candidate(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
    *,
    decision_ref: PinnedRecordRef,
    actor: RecordActor,
) -> WriteResult:
    """Promote one exact approved candidate without changing claim trust."""

    diagnostics = diagnose_knowledge_candidate(ws, candidate)
    if diagnostics.lane not in {"grounded_knowledge", "speculative_insight"}:
        raise ValueError("promotion requires a knowledge or insight lane")
    if len(candidate.content_kinds) != 1:
        raise ValueError("promotion requires exactly one candidate content kind")
    if diagnostics.lane == "grounded_knowledge" and not diagnostics.eligible_for_grounded_review:
        detail = [*diagnostics.missing_requirements, *diagnostics.errors]
        raise ValueError("grounded candidate is not promotion-ready: " + ", ".join(detail))

    decision = _approved_active_decision(ws, candidate, diagnostics.lane, decision_ref)
    exact_decision = asdict(decision_ref)
    identity = f"{candidate.candidate_id}:{decision.candidate_hash}:{decision_ref.content_hash}"
    if diagnostics.lane == "grounded_knowledge":
        if not candidate.subject_ref.startswith("physics_object:"):
            raise ValueError("grounded promotion requires a physics_object subject_ref")
        repository = RecordRepository(ws, actor=actor)
        if repository.read(candidate.subject_ref).status != "found":
            raise ValueError("grounded promotion subject_ref does not resolve")
        asset_refs = [
            pin.record_ref for pin in candidate.grounding_pins
            if pin.record_ref.startswith("source_asset:")
        ]
        location_refs = [
            pin.record_ref for pin in candidate.grounding_pins
            if pin.record_ref.startswith("reference_location:")
        ]
        assertion = PhysicsAssertionRecord(
            assertion_id=prefixed_id("assertion", identity, max_slug=72),
            object_ref=candidate.subject_ref,
            topic_id=candidate.topic_id,
            predicate=candidate.content_kinds[0],
            value=candidate.statement,
            framework=candidate.framework,
            regime=candidate.regime,
            conventions=list(candidate.conventions),
            source_asset_refs=asset_refs,
            source_location_refs=location_refs,
            review_decision_ref=exact_decision,
            review_status="reviewed",
        )
        return record_physics_assertion(ws, assertion, actor=actor)

    insight = InsightRecord(
        insight_id=prefixed_id("insight", identity, max_slug=72),
        insight_kind=candidate.content_kinds[0],
        statement=candidate.statement,
        topic_id=candidate.topic_id,
        grounding_refs=[pin.record_ref for pin in candidate.grounding_pins],
        framework=candidate.framework,
        regime=candidate.regime,
        review_status="reviewed",
        checkpoint_id=_checkpoint_id(decision.checkpoint_ref),
        review_decision_ref=exact_decision,
        source_refs=[pin.record_ref for pin in candidate.grounding_pins],
    )
    return RecordRepository(ws, actor=actor).write(
        "insights",
        insight,
        body=f"# Reviewed Insight: {insight.insight_kind}\n\n{insight.statement}\n",
    )


def _approved_active_decision(
    ws: WorkspacePaths,
    candidate: KnowledgeCandidate,
    lane: str,
    decision_ref: PinnedRecordRef,
) -> KnowledgeReviewDecisionRecord:
    if pin_current_record(ws, decision_ref.record_ref) != decision_ref:
        raise ValueError("knowledge review decision pin is stale")
    decision = get_record_version(ws, decision_ref).record
    if not isinstance(decision, KnowledgeReviewDecisionRecord):
        raise ValueError("decision_ref must pin a knowledge review decision")
    candidate_hash = knowledge_candidate_hash(candidate)
    if decision.candidate_hash != candidate_hash:
        raise ValueError("knowledge review decision candidate hash does not match")
    if knowledge_candidate_payload_hash(decision.candidate_payload) != candidate_hash:
        raise ValueError("knowledge review decision candidate payload hash does not match")
    if (
        decision.candidate_id != candidate.candidate_id
        or decision.topic_id != candidate.topic_id
        or decision.candidate_lane != lane
    ):
        raise ValueError("knowledge review decision scope does not match candidate")
    if decision.decision != "approve":
        raise ValueError("knowledge candidate is not approved for promotion")
    if decision.lifecycle_status != "active":
        raise ValueError("knowledge review decision is not active")
    report = RecordRepository(ws, actor=_audit_actor()).list("knowledge_review_decisions")
    if report.malformed:
        raise ValueError("knowledge review registry contains malformed records")
    _require_unique_active_decision(ws, report.records, decision, decision_ref)
    return decision


def _require_unique_active_decision(
    ws: WorkspacePaths,
    records: tuple[Any, ...],
    selected: KnowledgeReviewDecisionRecord,
    selected_pin: PinnedRecordRef,
) -> None:
    relevant = [
        record
        for record in records
        if isinstance(record, KnowledgeReviewDecisionRecord)
        and record.topic_id == selected.topic_id
        and record.candidate_id == selected.candidate_id
    ]
    pins = {
        pin_current_record(ws, f"knowledge_review_decision:{record.decision_id}"): record
        for record in relevant
    }
    successors: dict[PinnedRecordRef, list[PinnedRecordRef]] = {}
    for successor_pin, record in pins.items():
        prior = _coerce_optional_pin(record.supersedes_decision_ref)
        if prior is None:
            continue
        if prior not in pins:
            raise ValueError("knowledge review history has invalid supersedes scope")
        successors.setdefault(prior, []).append(successor_pin)
    if any(len(items) > 1 for items in successors.values()):
        raise ValueError("knowledge review history has multiple active branches")
    leaves = set(pins).difference(successors)
    if len(leaves) != 1:
        raise ValueError("knowledge review history has multiple active branches")
    if selected_pin not in leaves:
        raise ValueError("knowledge review decision has been superseded")


def _coerce_optional_pin(value: Any) -> PinnedRecordRef | None:
    if not value:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("knowledge review supersedes ref must be an exact pin")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=int(value.get("revision") or 0),
    )


def _checkpoint_id(value: Mapping[str, Any]) -> str:
    record_ref = str(value.get("record_ref") or "")
    return record_ref.split(":", 1)[1] if record_ref.startswith("checkpoint:") else ""


def _audit_actor() -> RecordActor:
    return RecordActor(actor_type="system", actor_id="knowledge-promotion-audit", host="aitp-v5")
