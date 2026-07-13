# Compatibility shard 2 for claim_relation_map.
from __future__ import annotations

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
        "relation_map_scope": "active_claim_only",
        "not_authoritative_for_current_goal_if_rebind_needed": False,
        "warnings": [],
        "active_claim_focus_reconciliation": empty_active_claim_focus_reconciliation(
            session_id=requested_session_id or session_id or "unbound-session",
            topic_id=topic_id or "unbound-session",
            reason=reason,
        ),
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
        "relation_map_scope": str(payload.get("relation_map_scope") or "active_claim_only"),
        "not_authoritative_for_current_goal_if_rebind_needed": bool(
            payload.get("not_authoritative_for_current_goal_if_rebind_needed")
        ),
        "warnings": list(payload.get("warnings") or []),
        "active_claim_focus_candidates": list(
            ((payload.get("active_claim_focus_reconciliation") or {}).get("candidate_sibling_claims") or [])
        )[:5],
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
        _focus_drift_markdown(payload),
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

def _focus_drift_markdown(payload: dict[str, Any]) -> str:
    if not payload.get("not_authoritative_for_current_goal_if_rebind_needed"):
        return ""
    reconciliation = payload.get("active_claim_focus_reconciliation") or {}
    candidates = list(reconciliation.get("candidate_sibling_claims") or [])[:5]
    lines = [
        "## Active Claim Focus Warning\n\n",
        "- Warning: `active_claim_focus_drift_detected`.\n",
        "- Relation map scope: `active_claim_only`.\n",
        "- This map is not authoritative for the current goal until the active-claim focus is confirmed or rebound.\n",
        "- Candidate sibling claims:\n",
    ]
    if candidates:
        for candidate in candidates:
            lines.append(
                f"  - `{candidate.get('claim_id', '')}`: "
                f"{candidate.get('statement_excerpt', '')} "
                f"(recent records: {candidate.get('recent_record_count', 0)})\n"
            )
    else:
        lines.append("  - none\n")
    lines.append("\n")
    return "".join(lines)

def _tool_runs_for_claim(ws, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]

def _claim_statuses_for_claim(ws, claim_id: str) -> list[ClaimStatusRecord]:
    return [
        record
        for record in list_records(ws.registry_dir("claim_statuses"), ClaimStatusRecord)
        if record.claim_id == claim_id
    ]

def _claims_for_topic(ws, topic_id: str) -> list[ClaimRecord]:
    return [
        record
        for record in list_records(ws.registry_dir("claims"), ClaimRecord)
        if record.topic_id == topic_id
    ]

def _legacy_semantic_reviews_for_topic(ws, topic_id: str) -> list[LegacySemanticReviewResultRecord]:
    return [
        record
        for record in list_records(ws.registry_dir("legacy_semantic_reviews"), LegacySemanticReviewResultRecord)
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
