"""Derived claim/evidence relation map for recovery briefs.

This surface is deliberately read-only.  It compiles existing typed records into
an explicit conclusion-boundary view, but it is never a source of claim trust.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from brain.v5.evidence import list_evidence_for_claim
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
from brain.v5.store import list_valid_records
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
# Lifecycle status sets: records carrying these are excluded from the active conclusion.
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
    "executable path",
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
)


def build_claim_relation_map(ws, session_id: str, *, registry_index: dict[str, dict[str, list[Any]]] | None = None) -> dict[str, Any]:
    """Build a read-only relation map for the session's active claim."""

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

    for run in tool_runs:
        if getattr(run, "lifecycle_status", "active") in _INACTIVE_LIFECYCLE_STATUSES | _HISTORICAL_LIFECYCLE_STATUSES:
            continue
        entry = _tool_run_entry(run)
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


def build_claim_relation_registry_index(ws) -> dict[str, dict[str, list[Any]]]:
    """Preload registry records by claim for workspace-scale recovery audits."""

    return {
        "evidence": _group_by_claim(list_valid_records(ws.registry_dir("evidence"), EvidenceRecord)),
        "tool_runs": _group_by_claim(list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)),
        "claim_statuses": _group_by_claim(list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)),
        "proof_obligations": _group_by_claim(list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord)),
        "object_relations": _group_by_claim(list_valid_records(ws.registry_dir("object_relations"), ObjectRelationRecord)),
        "claims_by_topic": _group_claims_by_topic(list_valid_records(ws.registry_dir("claims"), ClaimRecord)),
        "legacy_semantic_reviews": _group_by_topic(
            list_valid_records(ws.registry_dir("legacy_semantic_reviews"), LegacySemanticReviewResultRecord)
        ),
        "legacy_migration_topics": _legacy_migration_topics_by_topic(ws),
    }


def empty_claim_relation_map(
    *,
    topic_id: str,
    session_id: str,
    reason: str,
    requested_session_id: str = "",
    recovery_selection_source: str = "",
) -> dict[str, Any]:
    return {
        "kind": "claim_relation_map",
        "topic_id": topic_id or "unbound-session",
        "session_id": session_id or "unbound-session",
        "requested_session_id": requested_session_id or session_id or "unbound-session",
        "recovery_selection_source": recovery_selection_source or "session_binding",
        "claim_id": "",
        "claim_statement": "",
        "confidence_state": "",
        "evidence_profile": "",
        "key_object_relation_count": 0,
        "key_object_relations": [],
        "latest_claim_status": {},
        "supported_by": [],
        "limited_by": [],
        "contradicted_by": [],
        "not_tested_by": [],
        "historical": [],
        "misrouted": [],
        "cross_topic_references": [],
        "object_relations": [],
        "topic_claim_boundaries": _empty_topic_claim_boundaries(),
        "current_conclusion": {
            "can_say": [reason],
            "cannot_say": ["cannot infer claim support, failure, or trust state without an active claim"],
        },
        "current_blockers": [reason],
        "next_valid_actions": ["bind a session to a topic and active claim before restoring research state"],
        "source_records": {
            "claims": [],
            "evidence": [],
            "tool_runs": [],
            "claim_statuses": [],
            "proof_obligations": [],
            "object_relations": [],
            "sibling_claims": [],
            "legacy_semantic_reviews": [],
            "legacy_migration_topics": [],
        },
        "derived_from": [],
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }


def _session_binding_failure_reason(error: Exception) -> str:
    text = str(error)
    if isinstance(error, FileNotFoundError):
        return "session binding is missing"
    if "SessionBinding.__init__()" in text:
        return "session binding is missing or malformed"
    return "session binding is malformed"


def compact_claim_relation_map(payload: dict[str, Any]) -> dict[str, Any]:
    conclusion = payload.get("current_conclusion") or {}
    legacy = payload.get("legacy_semantic_review") if isinstance(payload.get("legacy_semantic_review"), dict) else {}
    return {
        "kind": "claim_relation_map_progress",
        "claim_id": str(payload.get("claim_id") or ""),
        "claim_statement_excerpt": _excerpt(payload.get("claim_statement") or ""),
        "confidence_state": str(payload.get("confidence_state") or ""),
        "supported_count": len(payload.get("supported_by") or []),
        "limited_count": len(payload.get("limited_by") or []),
        "contradicted_count": len(payload.get("contradicted_by") or []),
        "not_tested_count": len(payload.get("not_tested_by") or []),
        "object_relation_count": len(payload.get("object_relations") or []),
        "key_object_relations": list(payload.get("key_object_relations") or [])[:5],
        "sibling_claim_count": int((payload.get("topic_claim_boundaries") or {}).get("sibling_claim_count") or 0),
        "sibling_claims": list((payload.get("topic_claim_boundaries") or {}).get("sibling_claims") or [])[:5],
        "legacy_semantic_review_status": str(legacy.get("status") or ""),
        "legacy_active_claim_divergence": bool(legacy.get("active_claim_divergence") is True),
        "can_say": list(conclusion.get("can_say") or [])[:5],
        "cannot_say": list(conclusion.get("cannot_say") or [])[:5],
        "current_blockers": list(payload.get("current_blockers") or [])[:5],
        "next_valid_actions": list(payload.get("next_valid_actions") or [])[:5],
        "orientation_only": True,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
    }


def render_claim_relation_map_markdown(payload: dict[str, Any]) -> str:
    conclusion = payload.get("current_conclusion") or {}
    lines = [
        "# Current Relation Map\n\n",
        f"Claim: `{payload.get('claim_id', '')}`\n\n",
        f"{payload.get('claim_statement', '')}\n\n",
        "## Supported By\n\n",
        _entry_bullets(payload.get("supported_by") or []),
        "\n## Limited By\n\n",
        _entry_bullets(payload.get("limited_by") or []),
        "\n## Not Tested By\n\n",
        _entry_bullets(payload.get("not_tested_by") or []),
        "\n## Contradicted By\n\n",
        _entry_bullets(payload.get("contradicted_by") or []),
        "\n## Key Object Relations\n\n",
        _bullets(payload.get("key_object_relations") or []),
        "\n## Topic Claim Boundaries\n\n",
        _topic_claim_boundaries_markdown(payload.get("topic_claim_boundaries") or {}),
        "\n## Legacy Semantic Review\n\n",
        _legacy_semantic_review_markdown(payload.get("legacy_semantic_review") or {}),
        "\n## Can Say\n\n",
        _bullets(conclusion.get("can_say") or []),
        "\n## Cannot Say\n\n",
        _bullets(conclusion.get("cannot_say") or []),
        "\n## Current Blockers\n\n",
        _bullets(payload.get("current_blockers") or []),
        "\n## Next Valid Actions\n\n",
        _bullets(payload.get("next_valid_actions") or []),
        "\nThis surface is orientation-only and cannot update claim trust.\n",
    ]
    return "".join(lines)


def _tool_runs_for_claim(ws, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]


def _claim_statuses_for_claim(ws, claim_id: str) -> list[ClaimStatusRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
        if record.claim_id == claim_id
    ]


def _claims_for_topic(ws, topic_id: str) -> list[ClaimRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("claims"), ClaimRecord)
        if record.topic_id == topic_id
    ]


def _legacy_semantic_reviews_for_topic(ws, topic_id: str) -> list[LegacySemanticReviewResultRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("legacy_semantic_reviews"), LegacySemanticReviewResultRecord)
        if record.topic == topic_id
    ]


def _legacy_migration_topics_for_topic(ws, topic_id: str) -> list[dict[str, Any]]:
    return _legacy_migration_topics_by_topic(ws).get(topic_id, [])


def _legacy_migration_topics_by_topic(ws) -> dict[str, list[dict[str, Any]]]:
    try:
        coverage = audit_legacy_migration_coverage(ws)
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    run_id = str(coverage.get("run_id") or "")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in coverage.get("topics", []):
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic") or "")
        if not topic:
            continue
        payload = dict(item)
        payload["migration_run_id"] = run_id
        grouped.setdefault(topic, []).append(payload)
    return grouped


def _legacy_migration_topic_ref(record: dict[str, Any]) -> str:
    run_id = str(record.get("migration_run_id") or "")
    topic = str(record.get("topic") or "")
    if run_id and topic:
        return f"{run_id}:{topic}"
    return topic


def _indexed_claim_records(
    registry_index: dict[str, dict[str, list[Any]]] | None,
    bucket: str,
    claim_id: str,
) -> list[Any] | None:
    if registry_index is None:
        return None
    return list(registry_index.get(bucket, {}).get(claim_id, []))


def _indexed_topic_records(
    registry_index: dict[str, dict[str, list[Any]]] | None,
    bucket: str,
    topic_id: str,
) -> list[Any] | None:
    if registry_index is None:
        return None
    return list(registry_index.get(bucket, {}).get(topic_id, []))


def _group_by_claim(records: list[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {}
    for record in records:
        claim_id = str(getattr(record, "claim_id", "") or "")
        if not claim_id:
            continue
        grouped.setdefault(claim_id, []).append(record)
    return grouped


def _group_by_topic(records: list[Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {}
    for record in records:
        topic = str(getattr(record, "topic", "") or getattr(record, "topic_id", "") or "")
        if not topic:
            continue
        grouped.setdefault(topic, []).append(record)
    for values in grouped.values():
        values.sort(key=_legacy_semantic_review_sort_key)
    return grouped


def _group_claims_by_topic(records: list[ClaimRecord]) -> dict[str, list[ClaimRecord]]:
    grouped: dict[str, list[ClaimRecord]] = {}
    for record in records:
        if record.topic_id:
            grouped.setdefault(record.topic_id, []).append(record)
    for values in grouped.values():
        values.sort(key=lambda item: item.claim_id)
    return grouped


def _latest_claim_status(records: list[ClaimStatusRecord]) -> ClaimStatusRecord | None:
    return records[-1] if records else None


def _latest_legacy_semantic_review(records: list[LegacySemanticReviewResultRecord]) -> LegacySemanticReviewResultRecord | None:
    if not records:
        return None
    return sorted(records, key=_legacy_semantic_review_sort_key)[-1]


def _select_legacy_semantic_review(
    records: list[LegacySemanticReviewResultRecord],
    claim_id: str,
) -> LegacySemanticReviewResultRecord | None:
    if not records:
        return None
    matching = [
        record
        for record in records
        if record.active_claim_id and record.active_claim_id == claim_id
    ]
    if matching:
        return _latest_legacy_semantic_review(matching)
    return _latest_legacy_semantic_review(records)


def _legacy_semantic_review_sort_key(record: LegacySemanticReviewResultRecord) -> tuple[str, str]:
    return (record.created_at or "", record.review_id)


def _claim_status_payload(record: ClaimStatusRecord) -> dict[str, Any]:
    return {
        "status_id": record.status_id,
        "maturity_level": record.maturity_level,
        "claim_status": record.claim_status,
        "scope": record.scope,
        "risk": record.risk,
        "next_action": record.next_action,
        "open_gaps": list(record.open_gaps),
        "evidence_refs": list(record.evidence_refs),
        "human_gate_required": bool(record.human_gate_required),
        "can_update_claim_trust": bool(record.can_update_claim_trust),
    }


def _legacy_semantic_review_context(
    record: LegacySemanticReviewResultRecord | None,
    *,
    relation_claim_id: str,
    topic_id: str,
    migration_active_claim_id: str = "",
    migration_run_id: str = "",
) -> dict[str, Any]:
    if record is None:
        migration_divergence = bool(
            migration_active_claim_id and relation_claim_id and migration_active_claim_id != relation_claim_id
        )
        return {
            "kind": "legacy_semantic_review_context",
            "present": bool(migration_active_claim_id),
            "has_review_record": False,
            "status": "pending" if migration_active_claim_id else "",
            "review_id": "",
            "migration_run_id": migration_run_id,
            "topic_id": topic_id,
            "active_claim_id": "",
            "migration_active_claim_id": migration_active_claim_id,
            "relation_claim_id": relation_claim_id,
            "review_active_claim_divergence": False,
            "migration_active_claim_divergence": migration_divergence,
            "active_claim_divergence": migration_divergence,
            "remaining_actions": [],
            "summary_excerpt": "",
            "truth_source": "legacy_semantic_review_records",
            "orientation_only": True,
            "summary_inputs_trusted": False,
            "can_update_claim_trust": False,
        }
    active_claim_id = str(record.active_claim_id or "")
    review_divergence = bool(active_claim_id and relation_claim_id and active_claim_id != relation_claim_id)
    migration_divergence = bool(
        migration_active_claim_id and relation_claim_id and migration_active_claim_id != relation_claim_id
    )
    return {
        "kind": "legacy_semantic_review_context",
        "present": True,
        "has_review_record": True,
        "status": record.status,
        "review_id": record.review_id,
        "migration_run_id": record.migration_run_id,
        "topic_id": topic_id,
        "active_claim_id": active_claim_id,
        "migration_active_claim_id": migration_active_claim_id,
        "relation_claim_id": relation_claim_id,
        "review_active_claim_divergence": review_divergence,
        "migration_active_claim_divergence": migration_divergence,
        "active_claim_divergence": review_divergence or migration_divergence,
        "remaining_actions": list(record.remaining_actions),
        "summary_excerpt": _excerpt(record.summary, limit=360),
        "truth_source": "legacy_semantic_review_records",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _legacy_semantic_review_entry(context: dict[str, Any]) -> dict[str, Any] | None:
    if not context.get("present"):
        return None
    status = str(context.get("status") or "")
    divergence = bool(context.get("active_claim_divergence") is True)
    if status == "passed" and not divergence:
        return None
    return {
        "record_kind": "legacy_semantic_review",
        "record_id": str(context.get("review_id") or _legacy_semantic_review_context_ref(context)),
        "relation_to_claim": "limits_migration_recovery_trust",
        "status": status or "pending",
        "summary": _legacy_semantic_review_limit_summary(context),
        "reason": "legacy semantic review is a migration recovery boundary, not claim-trust evidence",
        "source_refs": _legacy_semantic_review_source_refs(context),
        "evidence_refs": [],
        "tool_run_ids": [],
        "artifact_ids": [],
    }


def _legacy_semantic_review_limit_summary(context: dict[str, Any]) -> str:
    status = str(context.get("status") or "pending")
    summary = f"Latest legacy semantic review status is {status}."
    if context.get("active_claim_divergence"):
        summary += (
            " Its reviewed or migration active claim differs from the relation-map claim, so recovery must not "
            "treat the migration as semantically settled."
        )
    if not context.get("has_review_record") and context.get("migration_active_claim_id"):
        summary += " No legacy semantic review result has been recorded for the latest migration coverage item."
    if context.get("summary_excerpt"):
        summary += f" Summary: {context['summary_excerpt']}"
    return summary


def _legacy_semantic_review_blockers(context: dict[str, Any]) -> list[str]:
    if not context.get("present"):
        return []
    blockers: list[str] = []
    if context.get("active_claim_divergence"):
        blockers.append("active_claim_divergence_requires_semantic_review")
    status = str(context.get("status") or "")
    if status == "pending":
        blockers.append("legacy_semantic_review_pending")
    if status in {"needs_revision", "inconclusive"}:
        blockers.append(f"legacy_semantic_review_{status}")
    for action in context.get("remaining_actions") or []:
        lower = str(action).lower()
        if "source_reconstruction" in lower or "source reconstruction" in lower:
            blockers.append("source_reconstruction_incomplete_for_semantic_lossless_migration")
        if "active_claim_divergence" in lower or "active claim divergence" in lower:
            blockers.append("active_claim_divergence_requires_semantic_review")
    return blockers


def _legacy_semantic_review_next_actions(context: dict[str, Any]) -> list[str]:
    if not context.get("present"):
        return []
    actions: list[str] = []
    if context.get("active_claim_divergence"):
        actions.append("resolve active-claim divergence before using legacy review for session recovery trust")
    for action in context.get("remaining_actions") or []:
        actions.append(str(action))
    status = str(context.get("status") or "")
    if status == "pending":
        actions.append("record legacy semantic review result before treating migration as semantically lossless")
    if status in {"needs_revision", "inconclusive"}:
        actions.append("complete legacy semantic review before treating migration as semantically lossless")
    return actions


def _legacy_semantic_review_can_say(context: dict[str, Any]) -> list[str]:
    if not context.get("present"):
        return []
    status = str(context.get("status") or "pending")
    statements = [f"latest legacy semantic review status is {status}"]
    if context.get("active_claim_divergence"):
        statements.append("legacy semantic review or migration active claim diverges from the recovered relation-map claim")
    return statements


def _legacy_semantic_review_cannot_say(context: dict[str, Any]) -> list[str]:
    if not context.get("present"):
        return []
    statements: list[str] = []
    status = str(context.get("status") or "")
    if status != "passed":
        statements.append("cannot treat the legacy migration as semantically lossless until the legacy semantic review passes")
    if context.get("active_claim_divergence"):
        statements.append("cannot use divergent legacy semantic review or migration active-claim state as session-recovery trust for this claim")
    return statements


def _legacy_semantic_review_markdown(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict) or not payload.get("present"):
        return "- None\n"
    lines = [
        f"- Review: `{payload.get('review_id', '') or '(pending)'}` status={payload.get('status', '')}\n",
        f"- Active claim divergence: `{bool(payload.get('active_claim_divergence') is True)}`\n",
    ]
    if payload.get("summary_excerpt"):
        lines.append(f"- Summary: {payload.get('summary_excerpt')}\n")
    if payload.get("remaining_actions"):
        lines.append("- Remaining actions:\n")
        for action in payload.get("remaining_actions") or []:
            lines.append(f"  - {action}\n")
    return "".join(lines)


def _topic_claim_boundaries(records: list[ClaimRecord], *, active_claim_id: str) -> dict[str, Any]:
    siblings = [
        {
            "claim_id": record.claim_id,
            "confidence_state": record.confidence_state,
            "evidence_profile": record.evidence_profile,
            "statement_excerpt": _excerpt(record.statement, limit=180),
        }
        for record in sorted(records, key=lambda item: item.claim_id)
        if record.claim_id != active_claim_id
    ]
    has_siblings = bool(siblings)
    return {
        "kind": "topic_claim_boundaries",
        "active_claim_id": active_claim_id,
        "sibling_claim_count": len(siblings),
        "sibling_claims": siblings,
        "boundary_rule": (
            "Sibling claims are same-topic research lines for orientation only; their records cannot support, "
            "limit, or refute the active claim unless explicitly linked to this active claim."
        ),
        "current_conclusion": {
            "can_say": (
                ["same-topic sibling claims exist and may explain topic history"]
                if has_siblings
                else ["no same-topic sibling claims were found"]
            ),
            "cannot_say": (
                ["cannot use sibling-claim evidence or legacy reviews as active-claim support without an explicit claim link"]
                if has_siblings
                else []
            ),
        },
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _empty_topic_claim_boundaries() -> dict[str, Any]:
    return _topic_claim_boundaries([], active_claim_id="")


def _topic_claim_boundaries_markdown(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "- None\n"
    siblings = payload.get("sibling_claims") or []
    lines = [
        f"- Active claim: `{payload.get('active_claim_id', '')}`\n",
        f"- Sibling claim count: `{payload.get('sibling_claim_count', 0)}`\n",
        f"- Boundary rule: {payload.get('boundary_rule', '')}\n",
    ]
    for item in siblings[:8]:
        lines.append(
            f"- Sibling `{item.get('claim_id', '')}` "
            f"({item.get('confidence_state', '')}, {item.get('evidence_profile', '')}): "
            f"{item.get('statement_excerpt', '')}\n"
        )
    return "".join(lines)


def _legacy_semantic_review_context_ref(context: dict[str, Any]) -> str:
    run_id = str(context.get("migration_run_id") or "")
    topic = str(context.get("topic_id") or "")
    if run_id and topic:
        return f"legacy-migration-coverage:{run_id}:{topic}"
    return f"legacy-semantic-review:{topic or 'pending'}"


def _legacy_semantic_review_source_refs(context: dict[str, Any]) -> list[str]:
    if context.get("review_id"):
        return [f"legacy_semantic_review:{context.get('review_id')}"]
    ref = _legacy_semantic_review_context_ref(context)
    return [ref] if ref else []


def _key_object_relation_summaries(object_relations: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for relation in object_relations:
        relation_type = str(relation.get("relation_type") or "").strip()
        statement = str(relation.get("statement") or "").strip()
        subject_id = str(relation.get("subject_id") or "").strip()
        object_id = str(relation.get("object_id") or "").strip()
        status = str(relation.get("status") or "").strip()
        failure_modes = [
            str(item).strip()
            for item in relation.get("failure_modes", [])
            if str(item).strip()
        ]
        if statement:
            summary = f"{relation_type}: {statement}" if relation_type else statement
        else:
            summary = f"{subject_id} --{relation_type or 'relates_to'}-> {object_id}"
        if status:
            summary = f"{summary} (status={status})"
        if failure_modes:
            summary = f"{summary}; failure modes: {', '.join(failure_modes[:3])}"
        summaries.append(summary)
    return _dedupe_clean(summaries)


def _bucket_for_status(status: str, *, text: str) -> str:
    normalized = status.strip().lower().replace(" ", "_")
    lower = text.lower()
    if normalized in _SUPPORT_STATUSES:
        return "supported_by"
    if normalized in _LIMIT_STATUSES:
        return "limited_by"
    if _is_pre_domain_failure_text(lower) and (
        normalized in _RUNTIME_FAILURE_STATUSES or _has_explicit_pre_domain_failure_context(lower)
    ):
        return "not_tested_by"
    if normalized in _CONTRADICT_STATUSES:
        return "contradicted_by"
    return "limited_by"


def _is_pre_domain_failure_text(lower_text: str) -> bool:
    if not any(marker in lower_text for marker in _PRE_DOMAIN_FAILURE_MARKERS):
        return False
    return _has_explicit_pre_domain_failure_context(lower_text)


def _has_explicit_pre_domain_failure_context(lower_text: str) -> bool:
    return any(marker in lower_text for marker in _EXPLICIT_PRE_DOMAIN_FAILURE_CONTEXT_MARKERS)


def _evidence_entry(record) -> dict[str, Any]:
    text = _evidence_text(record)
    return {
        "record_kind": "evidence",
        "record_id": record.evidence_id,
        "relation_to_claim": _relation_label(record.status, text=text),
        "status": record.status,
        "summary": record.summary,
        "reason": _relation_reason(record.status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [record.evidence_id],
        "tool_run_ids": list(record.tool_run_ids),
        "artifact_ids": list(record.artifact_ids),
    }


def _tool_run_entry(record: ToolRunRecord) -> dict[str, Any]:
    text = _tool_run_text(record)
    return {
        "record_kind": "tool_run",
        "record_id": record.run_id,
        "relation_to_claim": _relation_label(record.evidence_status, text=text),
        "status": record.evidence_status,
        "summary": _excerpt(text, limit=360),
        "reason": _relation_reason(record.evidence_status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [],
        "tool_run_ids": [record.run_id],
        "artifact_ids": list(record.artifact_ids),
    }


def _claim_status_gap_entry(record: ClaimStatusRecord, gap: str) -> dict[str, Any]:
    return {
        "record_kind": "claim_status",
        "record_id": record.status_id,
        "relation_to_claim": "limits_claim_scope",
        "status": record.claim_status,
        "summary": gap,
        "reason": f"recorded open gap under scope: {record.scope}",
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }


def _proof_obligation_entry(record: ProofObligationRecord) -> dict[str, Any]:
    return {
        "record_kind": "proof_obligation",
        "record_id": record.obligation_id,
        "relation_to_claim": "open_proof_or_validation_gap",
        "status": record.status,
        "summary": record.statement,
        "reason": record.next_action,
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }


def _relation_label(status: str, *, text: str) -> str:
    bucket = _bucket_for_status(status, text=text)
    if bucket == "not_tested_by":
        return "does_not_test_core_claim"
    if bucket == "supported_by":
        return "supports_claim_within_scope"
    if bucket == "contradicted_by":
        return "challenges_or_refutes_claim"
    return "limits_or_does_not_close_claim"


def _relation_reason(status: str, *, text: str) -> str:
    if _bucket_for_status(status, text=text) == "not_tested_by":
        return "classified as application/runtime/pre-domain failure, so it cannot support or refute the core claim"
    if status.strip().lower() in _SUPPORT_STATUSES:
        return "record status is supporting"
    if status.strip().lower() in _CONTRADICT_STATUSES:
        return "record status is challenging and no pre-domain failure marker was found"
    return "record is mixed, inconclusive, diagnostic, or scope-limiting"


def _evidence_text(record) -> str:
    return " ".join(
        [
            str(record.evidence_type),
            str(record.status),
            str(record.summary),
            " ".join(record.supports_outputs),
            " ".join(record.source_refs),
            " ".join(record.tool_run_ids),
            " ".join(record.artifact_ids),
        ]
    )


def _tool_run_text(record: ToolRunRecord) -> str:
    return " ".join(
        [
            str(record.tool_family),
            str(record.tool_name),
            str(record.evidence_status),
            _json_text(record.inputs),
            _json_text(record.outputs),
            _json_text(record.environment),
            " ".join(record.source_refs),
        ]
    )


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return str(value)


def _blocker_hints(text: str) -> list[str]:
    lower = text.lower()
    hints: list[str] = []
    if "scalapack" in lower:
        hints.append("ScaLAPACK/runtime dependency failure")
    if "executable" in lower or "path" in lower:
        hints.append("executable path or executable selection blocker")
    if "slurm" in lower:
        hints.append("Slurm/runtime job failure")
    if "before analytic continuation" in lower or "pre_ac" in lower or "pre-ac" in lower or "before ac" in lower:
        hints.append("failure occurred before analytic continuation")
    if not hints and any(marker in lower for marker in _PRE_DOMAIN_FAILURE_MARKERS):
        hints.append("application/runtime failure before the core claim was tested")
    return hints


def _can_say(claim, supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    statements: list[str] = [f"active claim remains {claim.confidence_state}"]
    if supported_by:
        statements.append("recorded support exists for the claim within the explicit recorded scope")
    if limited_by:
        statements.append("recorded limitations or open gaps bound how far the claim can be used")
    if not_tested_by:
        statements.append("some failed attempts are application/runtime failures and do not test the core claim")
    if blockers:
        statements.append(f"current blocker: {blockers[0]}")
    return _dedupe_clean(statements)


def _cannot_say(supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], contradicted_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]]) -> list[str]:
    statements = ["cannot update or promote claim trust from this relation map alone"]
    if not supported_by:
        statements.append("cannot say the claim is supported until supporting evidence records exist")
    if limited_by:
        statements.append("cannot ignore scope limits, gap audits, or open proof obligations")
    if not_tested_by:
        statements.append("cannot say runtime/application failures prove the core algorithm works or fails")
    if contradicted_by:
        statements.append("cannot treat the claim as settled while challenging evidence remains unresolved")
    return _dedupe_clean(statements)


def _fallback_next_actions(not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    if not_tested_by and blockers:
        text = " ".join(str(entry.get("summary") or "") for entry in not_tested_by).lower()
        if "thiele" in text and "ridge" in text:
            return [
                "resolve the runtime/application blocker, then rerun the same-executable Thiele baseline before interpreting ridge evidence"
            ]
        return [
            "resolve the runtime/application blocker, then rerun the same-executable baseline/control before interpreting algorithm evidence"
        ]
    if blockers:
        return ["resolve the recorded blocker before trust-changing interpretation"]
    return ["record explicit evidence, claim status, or proof obligation before drawing conclusions"]


def _prioritized_next_actions(
    recorded_actions: list[str],
    not_tested_by: list[dict[str, Any]],
    blockers: list[str],
) -> list[str]:
    fallback = _fallback_next_actions(not_tested_by, blockers)
    if not not_tested_by or not blockers:
        return recorded_actions or fallback
    if any(_is_specific_runtime_resolution_action(action) for action in recorded_actions):
        return recorded_actions
    return _dedupe_clean(fallback + recorded_actions)


def _is_specific_runtime_resolution_action(action: str) -> bool:
    lower = action.lower()
    if "baseline" in lower and ("same executable" in lower or "same-executable" in lower):
        return True
    if "thiele" in lower and "ridge" in lower and ("rerun" in lower or "reproduce" in lower or "run" in lower):
        return True
    if "control" in lower and ("runtime" in lower or "application" in lower):
        return True
    return False


def _entry_bullets(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "- None\n"
    lines = []
    for entry in entries:
        lines.append(
            f"- `{entry.get('record_id', '')}` ({entry.get('relation_to_claim', '')}, "
            f"status={entry.get('status', '')}): {entry.get('summary', '')}\n"
        )
    return "".join(lines)


def _bullets(values: list[str]) -> str:
    return "".join(f"- {value}\n" for value in values) if values else "- None\n"


def _dedupe_clean(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in out:
            out.append(clean)
    return out


def _excerpt(value: Any, *, limit: int = 260) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
