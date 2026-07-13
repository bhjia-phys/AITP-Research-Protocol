# Compatibility shard 1 for claim_relation_map.
from __future__ import annotations

import json

from dataclasses import asdict

from typing import Any

from brain.v5.active_claim_focus import (
    active_claim_focus_families,
    detect_active_claim_focus_drift,
    empty_active_claim_focus_reconciliation,
)

from brain.v5.evidence import list_evidence_for_claim

from brain.v5.context_compiler import load_indexed_topic_snapshot

from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage

from brain.v5.models import (
    ClaimRecord,
    ClaimStatusRecord,
    EvidenceRecord,
    LegacySemanticReviewResultRecord,
    ObjectRelationRecord,
    ProofObligationRecord,
    ToolRunRecord,
)

from brain.v5.physics_objects import list_object_relations_for_claim, object_relation_brief_payload

from brain.v5.research_state import list_proof_obligations_for_claim

from brain.v5.recovery_session import recover_session_binding_for_read

from brain.v5.store import list_records

from brain.v5.workspace import get_claim

_SUPPORT_STATUSES = {"supports", "support", "supported", "passed", "pass", "valid", "positive", "supports_scoped_claim"}

_LIMIT_STATUSES = {
    "mixed",
    "inconclusive",
    "partial",
    "limited",
    "unreviewed",
    "diagnostic",
    "supports_with_limitations",
    "supports_reconstruction_boundary",
}

_CONTRADICT_STATUSES = {"contradicts", "contradict", "refutes", "refute", "failed", "fail", "invalid", "negative"}

_INACTIVE_LIFECYCLE_STATUSES = {"misrouted", "voided"}

_HISTORICAL_LIFECYCLE_STATUSES = {"superseded", "duplicate"}

_RUNTIME_FAILURE_STATUSES = {
    "application_failure",
    "diagnostic",
    "failed",
    "fail",
    "falsifies_application",
    "negative",
    "runtime_failure",
}

_OPEN_STATUSES = {"open", "pending", "blocked", "incomplete", "inconclusive", "needs_revision", "partial"}

_PRE_DOMAIN_FAILURE_MARKERS = (
    "application",
    "runtime",
    "setup",
    "pre_ac",
    "pre-ac",
    "before analytic continuation",
    "before ac",
    "did not enter ac",
    "does not test algorithm",
    "does_not_test_algorithm",
    "falsifies_application",
    "scalapack",
    "executable",
    "slurm",
    "scheduler",
    "executable path",
    "path error",
    "modulenotfounderror",
    "module not found",
    "no module named",
    "importerror",
    "import error",
    "missing file",
    "no such file",
    "file not found",
    "out of memory",
    "oom",
    "exceeded memory",
    "memory limit",
    "dependency never satisfied",
    "dependency unresolved",
    "dependency not met",
    "cancelled before start",
)

_EXPLICIT_PRE_DOMAIN_FAILURE_CONTEXT_MARKERS = (
    "all failed",
    "blocked",
    "blocker",
    "crash",
    "did not enter",
    "does not test",
    "does_not_test",
    "failed before",
    "failure before",
    "falsifies_application",
    "map::at",
    "out_of_range",
    "pre_ac",
    "pre-ac",
    "before analytic continuation",
    "before ac",
    "runtime failed",
    "runtime failure",
    "runtime/environment blocker",
    "application failed",
    "application failure",
    "application/runtime blocker",
    "setup failure",
    "setup failed",
    "setup_failure",
    "failed_setup",
    "failed_runtime",
    "modulenotfounderror",
    "no module named",
    "importerror",
    "import error",
    "no such file",
    "no such file or directory",
    "file not found",
    "missing file",
    "out of memory",
    "oom",
    "exceeded memory",
    "exceeded memory limit",
    "dependency never satisfied",
    "dependency unresolved",
    "dependency not met",
    "cancelled before start",
    "cancelled_before_start",
    "path error",
    "path not found",
)

def build_claim_relation_map(
    ws,
    session_id: str,
    *,
    registry_index: dict[str, dict[str, list[Any]]] | None = None,
    objective_text: str = "",
    user_goal: str = "",
    indexed_snapshot: Any | None = None,
) -> dict[str, Any]:
    """Build a read-only relation map for the session's active claim."""

    snapshot = indexed_snapshot
    try:
        recovered = recover_session_binding_for_read(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError) as error:
        return empty_claim_relation_map(
            topic_id="unbound-session",
            session_id=session_id,
            reason=_session_binding_failure_reason(error),
        )
    session = recovered.session
    requested_session_id = recovered.requested_session_id
    recovery_selection_source = recovered.recovery_selection_source
    if registry_index is None:
        if snapshot is None:
            snapshot = load_indexed_topic_snapshot(
                ws,
                session.session_id,
                families=tuple(
                    dict.fromkeys(
                        (
                            "claim_statuses",
                            "claims",
                            "evidence",
                            "legacy_semantic_reviews",
                            "object_relations",
                            "proof_obligations",
                            "tool_runs",
                            *active_claim_focus_families(),
                        )
                    )
                ),
            )
        registry_index = _registry_index_from_snapshot(ws, snapshot)
    if not session.active_claim:
        return empty_claim_relation_map(
            topic_id=session.topic_id,
            session_id=requested_session_id,
            reason="session has no active claim",
            requested_session_id=requested_session_id,
            recovery_selection_source=recovery_selection_source,
        )

    try:
        claim = get_claim(ws, session.active_claim)
    except (FileNotFoundError, TypeError, ValueError):
        return empty_claim_relation_map(
            topic_id=session.topic_id,
            session_id=session.session_id,
            reason=f"active claim is missing or malformed: {session.active_claim}",
            requested_session_id=requested_session_id,
            recovery_selection_source=recovery_selection_source,
        )
    evidence_records = _indexed_claim_records(registry_index, "evidence", claim.claim_id)
    if evidence_records is None:
        evidence_records = list_evidence_for_claim(ws, claim.claim_id)
    tool_runs = _indexed_claim_records(registry_index, "tool_runs", claim.claim_id)
    if tool_runs is None:
        tool_runs = _tool_runs_for_claim(ws, claim.claim_id)
    claim_statuses = _indexed_claim_records(registry_index, "claim_statuses", claim.claim_id)
    if claim_statuses is None:
        claim_statuses = _claim_statuses_for_claim(ws, claim.claim_id)
    proof_obligations = _indexed_claim_records(registry_index, "proof_obligations", claim.claim_id)
    if proof_obligations is None:
        proof_obligations = list_proof_obligations_for_claim(ws, claim.claim_id)
    raw_object_relations = _indexed_claim_records(registry_index, "object_relations", claim.claim_id)
    if raw_object_relations is None:
        raw_object_relations = list_object_relations_for_claim(ws, claim.claim_id)
    object_relations = [
        object_relation_brief_payload(relation)
        for relation in raw_object_relations
    ]
    key_object_relations = _key_object_relation_summaries(object_relations)
    legacy_reviews = _indexed_topic_records(registry_index, "legacy_semantic_reviews", session.topic_id)
    if legacy_reviews is None:
        legacy_reviews = _legacy_semantic_reviews_for_topic(ws, session.topic_id)
    legacy_review = _select_legacy_semantic_review(legacy_reviews, claim.claim_id)
    legacy_migration_topics = _indexed_topic_records(registry_index, "legacy_migration_topics", session.topic_id)
    if legacy_migration_topics is None:
        legacy_migration_topics = _legacy_migration_topics_for_topic(ws, session.topic_id)
    legacy_migration_topic = legacy_migration_topics[-1] if legacy_migration_topics else {}
    topic_claims = _indexed_topic_records(registry_index, "claims_by_topic", session.topic_id)
    if topic_claims is None:
        topic_claims = _claims_for_topic(ws, session.topic_id)
    topic_claim_boundaries = _topic_claim_boundaries(topic_claims, active_claim_id=claim.claim_id)
    legacy_context = _legacy_semantic_review_context(
        legacy_review,
        relation_claim_id=claim.claim_id,
        topic_id=session.topic_id,
        migration_active_claim_id=str(legacy_migration_topic.get("active_claim_id") or ""),
        migration_run_id=str(legacy_migration_topic.get("migration_run_id") or ""),
    )
    if snapshot is None:
        focus_reconciliation = empty_active_claim_focus_reconciliation(
            session_id=session.session_id,
            topic_id=session.topic_id,
            reason="active-claim focus drift was not evaluated from an external registry index",
        )
    else:
        focus_reconciliation = detect_active_claim_focus_drift(
            ws,
            session_id,
            objective_text=objective_text or claim.statement,
            user_goal=user_goal,
            indexed_snapshot=snapshot,
        )
    drift_detected = bool(focus_reconciliation.get("not_authoritative_for_current_goal_if_rebind_needed"))

    supported_by: list[dict[str, Any]] = []
    limited_by: list[dict[str, Any]] = []
    contradicted_by: list[dict[str, Any]] = []
    not_tested_by: list[dict[str, Any]] = []
    historical: list[dict[str, Any]] = []
    misrouted_zone: list[dict[str, Any]] = []
    blockers: list[str] = []
    next_actions: list[str] = []

    for evidence in evidence_records:
        entry = _evidence_entry(evidence)
        if getattr(evidence, "lifecycle_status", "active") in _INACTIVE_LIFECYCLE_STATUSES:
            misrouted_zone.append(entry)
            continue
        if getattr(evidence, "lifecycle_status", "active") in _HISTORICAL_LIFECYCLE_STATUSES:
            historical.append(entry)
            continue
        bucket = _bucket_for_status(evidence.status, text=_evidence_text(evidence))
        if bucket == "not_tested_by":
            not_tested_by.append(entry)
            blockers.extend(_blocker_hints(_evidence_text(evidence)))
        elif bucket == "supported_by":
            supported_by.append(entry)
        elif bucket == "contradicted_by":
            contradicted_by.append(entry)
        else:
            limited_by.append(entry)

    superseded_tool_run_ids = {
        getattr(run, "supersedes_run_id", "")
        for run in tool_runs
        if getattr(run, "supersedes_run_id", "")
    }
    for run in tool_runs:
        if getattr(run, "lifecycle_status", "active") in _INACTIVE_LIFECYCLE_STATUSES | _HISTORICAL_LIFECYCLE_STATUSES:
            continue
        entry = _tool_run_entry(run)
        if run.run_id in superseded_tool_run_ids or getattr(run, "superseded_by", ""):
            historical.append(entry)
            continue
        bucket = _bucket_for_status(run.evidence_status, text=_tool_run_text(run))
        if bucket == "not_tested_by":
            not_tested_by.append(entry)
            blockers.extend(_blocker_hints(_tool_run_text(run)))
        elif bucket == "supported_by":
            supported_by.append(entry)
        elif bucket == "contradicted_by":
            contradicted_by.append(entry)
        elif run.evidence_status:
            limited_by.append(entry)

    for status in claim_statuses:
        for gap in status.open_gaps:
            limited_by.append(_claim_status_gap_entry(status, gap))
            blockers.append(gap)
        if status.next_action:
            next_actions.append(status.next_action)

    for obligation in proof_obligations:
        if obligation.status.strip().lower() in _OPEN_STATUSES:
            limited_by.append(_proof_obligation_entry(obligation))
            blockers.append(obligation.statement)
            if obligation.next_action:
                next_actions.append(obligation.next_action)

    for relation in object_relations:
        if relation.get("failure_modes"):
            blockers.extend(str(item) for item in relation.get("failure_modes", []))

    legacy_entry = _legacy_semantic_review_entry(legacy_context)
    if legacy_entry:
        limited_by.append(legacy_entry)
    blockers = _dedupe_clean(_legacy_semantic_review_blockers(legacy_context) + blockers)
    next_actions = _dedupe_clean(_legacy_semantic_review_next_actions(legacy_context) + next_actions)

    cross_topic_references: list[dict[str, Any]] = []
    try:
        from brain.v5.lifecycle_events import list_cross_topic_pointers
        for ptr in list_cross_topic_pointers(ws, session.topic_id):
            cross_topic_references.append({
                "source_record_id": ptr.get("source_record_id"),
                "source_topic": ptr.get("source_topic"),
                "target_topic": ptr.get("target_topic"),
            })
    except (ImportError, OSError, ValueError, TypeError):
        # lifecycle_events missing on this host, or a malformed pointer file — degrade
        # gracefully to an empty zone rather than poisoning the whole relation-map.
        # Programming errors (AttributeError/KeyError) are deliberately NOT swallowed.
        cross_topic_references = []

    next_actions = _prioritized_next_actions(next_actions, not_tested_by, blockers)
    latest_status = _latest_claim_status(claim_statuses)
    can_say = _dedupe_clean(
        _legacy_semantic_review_can_say(legacy_context)
        + _can_say(claim, supported_by, limited_by, not_tested_by, blockers)
    )
    cannot_say = _dedupe_clean(
        _legacy_semantic_review_cannot_say(legacy_context)
        + _cannot_say(supported_by, limited_by, contradicted_by, not_tested_by)
    )

    payload = {
        "kind": "claim_relation_map",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "requested_session_id": requested_session_id,
        "recovery_selection_source": recovery_selection_source,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "relation_map_scope": "active_claim_only",
        "not_authoritative_for_current_goal_if_rebind_needed": drift_detected,
        "warnings": ["active_claim_focus_drift_detected"] if drift_detected else [],
        "active_claim_focus_reconciliation": focus_reconciliation,
        "confidence_state": claim.confidence_state,
        "evidence_profile": claim.evidence_profile,
        "key_object_relation_count": len(key_object_relations),
        "key_object_relations": key_object_relations,
        "latest_claim_status": _claim_status_payload(latest_status) if latest_status else {},
        "supported_by": supported_by,
        "limited_by": limited_by,
        "contradicted_by": contradicted_by,
        "not_tested_by": not_tested_by,
        "historical": historical,
        "misrouted": misrouted_zone,
        "cross_topic_references": cross_topic_references,
        "object_relations": object_relations,
        "topic_claim_boundaries": topic_claim_boundaries,
        "legacy_semantic_review": legacy_context,
        "current_conclusion": {
            "can_say": can_say,
            "cannot_say": cannot_say,
        },
        "current_blockers": blockers,
        "next_valid_actions": next_actions,
        "source_records": {
            "claims": [claim.claim_id],
            "evidence": [record.evidence_id for record in evidence_records],
            "tool_runs": [record.run_id for record in tool_runs],
            "claim_statuses": [record.status_id for record in claim_statuses],
            "proof_obligations": [record.obligation_id for record in proof_obligations],
            "object_relations": [str(record.get("relation_id") or "") for record in object_relations if record.get("relation_id")],
            "sibling_claims": [item["claim_id"] for item in topic_claim_boundaries.get("sibling_claims", [])],
            "legacy_semantic_reviews": [record.review_id for record in legacy_reviews],
            "legacy_migration_topics": [
                _legacy_migration_topic_ref(record)
                for record in legacy_migration_topics
                if _legacy_migration_topic_ref(record)
            ],
        },
        "retrieval_coverage": snapshot.coverage if snapshot else {},
        "index_status": snapshot.index_status if snapshot else "external_registry_index",
        "source_index_generation": snapshot.index_generation if snapshot else 0,
        "retrieval_truncated": snapshot.truncated if snapshot else False,
        "read_errors": list(snapshot.read_errors) if snapshot else [],
        "derived_from": [
            "claim_status_records",
            "evidence_records",
            "tool_run_records",
            "object_relation_records",
            "proof_obligation_records",
            "topic_claim_boundary_records",
            "legacy_semantic_review_records",
            "legacy_migration_coverage_audit",
        ],
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }
    return payload

def _registry_index_from_snapshot(ws, snapshot) -> dict[str, dict[str, list[Any]]]:
    records = snapshot.records_by_family
    return {
        "evidence": _group_by_claim(list(records.get("evidence", ()))),
        "tool_runs": _group_by_claim(list(records.get("tool_runs", ()))),
        "claim_statuses": _group_by_claim(list(records.get("claim_statuses", ()))),
        "proof_obligations": _group_by_claim(list(records.get("proof_obligations", ()))),
        "object_relations": _group_by_claim(list(records.get("object_relations", ()))),
        "claims_by_topic": _group_claims_by_topic(list(records.get("claims", ()))),
        "legacy_semantic_reviews": _group_by_topic(
            list(records.get("legacy_semantic_reviews", ()))
        ),
        "legacy_migration_topics": _legacy_migration_topics_by_topic(ws),
    }

def build_claim_relation_registry_index(ws) -> dict[str, dict[str, list[Any]]]:
    """Preload registry records by claim for workspace-scale recovery audits."""

    return {
        "evidence": _group_by_claim(list_records(ws.registry_dir("evidence"), EvidenceRecord)),
        "tool_runs": _group_by_claim(list_records(ws.registry_dir("tool_runs"), ToolRunRecord)),
        "claim_statuses": _group_by_claim(list_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)),
        "proof_obligations": _group_by_claim(list_records(ws.registry_dir("proof_obligations"), ProofObligationRecord)),
        "object_relations": _group_by_claim(list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)),
        "claims_by_topic": _group_claims_by_topic(list_records(ws.registry_dir("claims"), ClaimRecord)),
        "legacy_semantic_reviews": _group_by_topic(
            list_records(ws.registry_dir("legacy_semantic_reviews"), LegacySemanticReviewResultRecord)
        ),
        "legacy_migration_topics": _legacy_migration_topics_by_topic(ws),
    }
