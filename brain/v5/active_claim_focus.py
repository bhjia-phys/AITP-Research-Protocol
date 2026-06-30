"""Active-claim focus reconciliation for AITP v5 sessions.

This module is intentionally conservative.  It can detect and explain that a
session's active claim may no longer match the current durable record focus, but
it never changes the binding unless a caller uses the explicit confirmation
operation.  Detection is an orientation-only surface; confirmation writes an
audit record and then updates only the session binding.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import re
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import (
    ActiveClaimRebindAuditRecord,
    ArtifactRecord,
    AuthorityRecord,
    ClaimRecord,
    ClaimStatusRecord,
    EvidenceRecord,
    ExploratoryRecord,
    ObjectRelationRecord,
    ProofObligationRecord,
    QuietCheckpointBatchRecord,
    ReferenceLocationRecord,
    ResearchRouteRecord,
    ResearchRunEventRecord,
    ResearchRunRecord,
    SensemakingReportRecord,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.store import list_valid_records, read_record, write_record
from brain.v5.workspace import bind_session, get_claim

_WARNING_CODE = "active_claim_focus_drift_detected"
_RELATION_MAP_SCOPE = "active_claim_only"
_RECENT_WINDOW_SIZE = 40
_DEFAULT_CANDIDATE_LIMIT = 5
_FOCUS_TERMS = {
    "a2",
    "alpha",
    "casimir",
    "charge",
    "commutant",
    "hidden",
    "irreducible",
    "level",
    "matrix",
    "motif",
    "partition",
    "pr",
    "ratio",
    "schur",
    "sector",
    "spacing",
    "spectral",
    "statistics",
    "symm",
    "symmetry",
    "yangian",
}


_RECORD_SPECS: tuple[tuple[str, type, str, tuple[str, ...], bool], ...] = (
    ("source_assets", SourceAssetRecord, "asset_id", ("title", "label", "summary", "uri"), True),
    ("tool_runs", ToolRunRecord, "run_id", ("tool_name", "tool_family", "evidence_status", "inputs", "outputs"), False),
    ("evidence", EvidenceRecord, "evidence_id", ("evidence_type", "status", "summary", "supports_outputs"), False),
    (
        "authorities",
        AuthorityRecord,
        "authority_id",
        ("authority_type", "authority_statement", "generator_set", "closure_envelope", "limitations"),
        True,
    ),
    ("sensemaking_reports", SensemakingReportRecord, "report_id", ("title", "summary", "open_questions", "next_actions"), True),
    ("artifacts", ArtifactRecord, "artifact_id", ("artifact_type", "uri", "summary"), False),
    ("reference_locations", ReferenceLocationRecord, "location_id", ("label", "uri", "summary"), True),
    ("object_relations", ObjectRelationRecord, "relation_id", ("relation_type", "statement", "failure_modes"), False),
    ("claim_statuses", ClaimStatusRecord, "status_id", ("claim_status", "scope", "risk", "next_action", "open_gaps"), False),
    ("proof_obligations", ProofObligationRecord, "obligation_id", ("statement", "obligation_type", "status", "next_action"), False),
    ("routes", ResearchRouteRecord, "route_id", ("title", "route_type", "current_question", "next_action"), True),
    ("research_runs", ResearchRunRecord, "run_id", ("title", "objective", "research_question", "phase", "status"), True),
    ("research_run_events", ResearchRunEventRecord, "event_id", ("event_type", "summary", "phase", "status"), True),
    ("validation_contracts", ValidationContractRecord, "contract_id", ("required_checks", "failure_modes", "status"), False),
    ("validation_results", ValidationResultRecord, "result_id", ("status", "summary", "failure_modes_observed"), False),
    ("quiet_checkpoints", QuietCheckpointBatchRecord, "checkpoint_id", ("summary", "durable_observations", "next_blockers"), True),
    ("exploratory_records", ExploratoryRecord, "record_id", ("title", "focal_question", "summary", "next_actions"), True),
)


def detect_active_claim_focus_drift(
    ws: WorkspacePaths,
    session_id: str,
    *,
    objective_text: str = "",
    user_goal: str = "",
    candidate_limit: int = _DEFAULT_CANDIDATE_LIMIT,
    recent_window_size: int = _RECENT_WINDOW_SIZE,
) -> dict[str, Any]:
    """Detect whether recent typed records point away from the active claim."""

    try:
        recovered = recover_session_binding_for_read(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError) as error:
        return _empty_reconciliation(
            session_id=session_id,
            status="session_binding_missing_or_malformed",
            reason=_session_failure_reason(error),
        )

    session = recovered.session
    claims = _topic_claims(ws, session.topic_id)
    claims_by_id = {claim.claim_id: claim for claim in claims}
    active_claim = claims_by_id.get(session.active_claim)
    observations = _record_observations(ws, session.topic_id)
    recent_observations = sorted(
        observations,
        key=lambda item: (float(item.get("mtime") or 0.0), str(item.get("record_id") or "")),
        reverse=True,
    )[: max(1, min(int(recent_window_size), 100))]
    stats_by_claim = _claim_stats(ws, claims, observations, recent_observations)
    active_stats = stats_by_claim.get(session.active_claim, _blank_stats(session.active_claim))
    goal_text = " ".join(
        item
        for item in [
            objective_text,
            user_goal,
            session.interaction_steering,
            active_claim.statement if active_claim else "",
        ]
        if item
    )
    goal_tokens = _tokens(goal_text)
    active_match_count = _goal_match_count(goal_tokens, active_claim, active_stats)

    candidates: list[dict[str, Any]] = []
    for claim in claims:
        if claim.claim_id == session.active_claim:
            continue
        stats = stats_by_claim.get(claim.claim_id, _blank_stats(claim.claim_id))
        candidate = _candidate_payload(
            claim=claim,
            stats=stats,
            active_stats=active_stats,
            goal_tokens=goal_tokens,
            active_goal_match_count=active_match_count,
        )
        if _candidate_has_signal(candidate):
            candidates.append(candidate)
    candidates.sort(key=lambda item: (int(item.get("_score") or 0), str(item.get("latest_update") or "")), reverse=True)
    candidates = [_strip_private_keys(candidate) for candidate in candidates[: max(1, min(int(candidate_limit), 12))]]

    drift_detected = _is_drift_detected(active_stats, candidates)
    warnings = [_WARNING_CODE] if drift_detected else []
    status = _WARNING_CODE if drift_detected else "no_active_claim_focus_drift"
    payload = {
        "kind": "active_claim_focus_reconciliation",
        "status": status,
        "warning_code": _WARNING_CODE if drift_detected else "",
        "warnings": warnings,
        "session_id": session.session_id,
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "topic_id": session.topic_id,
        "active_claim": _active_claim_payload(active_claim, active_stats),
        "candidate_sibling_claims": candidates,
        "record_distribution": {
            "recent_window_size": len(recent_observations),
            "active_claim_recent_record_count": int(active_stats.get("recent_record_count") or 0),
            "active_claim_latest_update": str(active_stats.get("latest_update") or ""),
            "by_claim": _record_distribution_rows(claims, stats_by_claim),
        },
        "available_options": _available_options(),
        "recommended_next_action": (
            "choose keep, explicit rebind, claim split, or stale read-only mode before treating the active-claim relation map as current-goal context"
            if drift_detected
            else "continue with current active claim binding"
        ),
        "relation_map_scope": _RELATION_MAP_SCOPE,
        "not_authoritative_for_current_goal_if_rebind_needed": drift_detected,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
        "can_rebind_without_confirmation": False,
    }
    return payload


def propose_active_claim_rebind(
    ws: WorkspacePaths,
    session_id: str,
    *,
    candidate_claim_id: str = "",
    reason: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    """Return a read-only rebind proposal that still requires confirmation."""

    reconciliation = detect_active_claim_focus_drift(
        ws,
        session_id,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    candidates = list(reconciliation.get("candidate_sibling_claims") or [])
    if candidate_claim_id:
        selected = next((candidate for candidate in candidates if candidate.get("claim_id") == candidate_claim_id), None)
        if selected is None:
            selected = _claim_candidate_from_store(ws, reconciliation.get("topic_id", ""), candidate_claim_id)
    else:
        selected = candidates[0] if candidates else {}
    old_claim_id = str((reconciliation.get("active_claim") or {}).get("claim_id") or "")
    new_claim_id = str(selected.get("claim_id") or "")
    proposal_reason = reason or "; ".join(selected.get("matching_reasons") or []) or "user-selected active claim focus repair"
    return {
        "kind": "active_claim_rebind_proposal",
        "status": "requires_user_confirmation" if new_claim_id else "no_candidate_selected",
        "session_id": str(reconciliation.get("session_id") or session_id),
        "requested_session_id": str(reconciliation.get("requested_session_id") or session_id),
        "topic_id": str(reconciliation.get("topic_id") or ""),
        "old_claim_id": old_claim_id,
        "candidate_claim_id": new_claim_id,
        "candidate_claim": selected,
        "reason": proposal_reason,
        "required_confirmation": "human/user confirmation text must be supplied to aitp_v5_confirm_active_claim_rebind",
        "proposed_operation": {
            "operation": "active_claim_rebind",
            "old_claim_id": old_claim_id,
            "new_claim_id": new_claim_id,
            "will_update_session_binding": bool(new_claim_id and new_claim_id != old_claim_id),
            "will_update_claim_trust": False,
            "will_update_evidence_trust": False,
            "will_update_l2_memory": False,
            "will_write_audit_record": True,
        },
        "active_claim_focus_reconciliation": reconciliation,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
        "can_apply_without_confirmation": False,
    }


def confirm_active_claim_rebind(
    ws: WorkspacePaths,
    session_id: str,
    *,
    new_claim_id: str,
    reason: str,
    user_confirmation: str,
    operator: str = "human",
) -> dict[str, Any]:
    """Apply an explicit active-claim rebind and write an audit record."""

    confirmation = str(user_confirmation or "").strip()
    if not confirmation:
        raise ValueError("user_confirmation is required for active claim rebind")
    if not str(new_claim_id or "").strip():
        raise ValueError("new_claim_id is required for active claim rebind")

    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    old_claim_id = session.active_claim
    new_claim = get_claim(ws, new_claim_id)
    if new_claim.topic_id != session.topic_id:
        raise ValueError("new active claim must belong to the session topic")
    if old_claim_id == new_claim_id:
        raise ValueError("new active claim is already bound")

    proposal = propose_active_claim_rebind(
        ws,
        session_id,
        candidate_claim_id=new_claim_id,
        reason=reason,
    )
    timestamp = _utc_timestamp()
    audit_id = prefixed_id("active-claim-rebind", f"{session.session_id}:{old_claim_id}:{new_claim_id}:{timestamp}")
    audit = ActiveClaimRebindAuditRecord(
        audit_id=audit_id,
        session_id=session.session_id,
        topic_id=session.topic_id,
        old_claim_id=old_claim_id,
        new_claim_id=new_claim_id,
        reason=reason,
        user_confirmation=confirmation,
        timestamp=timestamp,
        operator=operator or "human",
        status="confirmed_pending_apply",
        candidate_snapshot=proposal.get("candidate_claim") or {},
        source_records={
            "session_binding": [session.session_id],
            "old_claim": [old_claim_id] if old_claim_id else [],
            "new_claim": [new_claim_id],
            "reconciliation": ["active_claim_focus_reconciliation"],
        },
    )
    _write_rebind_audit(ws, audit)
    updated = bind_session(
        ws,
        session.session_id,
        topic_id=session.topic_id,
        context_id=session.context_id,
        runtime=session.runtime,
        interaction_profile=session.interaction_profile,
        interaction_steering=session.interaction_steering,
        active_cycle=session.active_cycle,
        active_claim=new_claim_id,
        active_route=session.active_route,
        write_scope=session.write_scope,
        lock_level=session.lock_level,
    )
    audit.status = "applied"
    _write_rebind_audit(ws, audit)
    after = detect_active_claim_focus_drift(ws, session.session_id)
    return {
        "kind": "active_claim_rebind_confirmation",
        "status": "applied",
        "session_id": updated.session_id,
        "requested_session_id": recovered.requested_session_id,
        "topic_id": updated.topic_id,
        "old_claim_id": old_claim_id,
        "new_claim_id": new_claim_id,
        "audit_id": audit.audit_id,
        "audit_record": asdict(audit),
        "session_binding": asdict(updated),
        "active_claim_focus_reconciliation": after,
        "truth_source": "session_binding_and_active_claim_rebind_audit",
        "orientation_only": False,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
        "evidence_trust_update_allowed": False,
        "l2_memory_update_allowed": False,
    }


def empty_active_claim_focus_reconciliation(*, session_id: str, topic_id: str = "", reason: str = "") -> dict[str, Any]:
    return _empty_reconciliation(session_id=session_id, topic_id=topic_id, status="not_evaluated", reason=reason)


def _record_observations(ws: WorkspacePaths, topic_id: str) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for family, cls, id_attr, text_attrs, default_orientation_only in _RECORD_SPECS:
        root = ws.registry_dir(family)
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            try:
                record = read_record(path, cls)
            except (TypeError, ValueError, OSError):
                continue
            if str(getattr(record, "topic_id", "") or "") != topic_id:
                continue
            claim_id = str(getattr(record, "claim_id", "") or "").strip()
            if not claim_id:
                continue
            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0.0
            orientation_only = bool(getattr(record, "orientation_only", default_orientation_only))
            observations.append(
                {
                    "record_kind": family,
                    "record_id": str(getattr(record, id_attr, "") or path.stem),
                    "claim_id": claim_id,
                    "mtime": mtime,
                    "latest_update": _iso_from_mtime(mtime),
                    "text": _record_text(record, text_attrs),
                    "orientation_only": orientation_only,
                    "can_update_claim_trust": bool(getattr(record, "can_update_claim_trust", False)),
                }
            )
    return observations


def _claim_stats(
    ws: WorkspacePaths,
    claims: list[ClaimRecord],
    observations: list[dict[str, Any]],
    recent_observations: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    observations_by_claim: dict[str, list[dict[str, Any]]] = {}
    recent_by_claim: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        observations_by_claim.setdefault(str(observation.get("claim_id") or ""), []).append(observation)
    for observation in recent_observations:
        recent_by_claim.setdefault(str(observation.get("claim_id") or ""), []).append(observation)
    stats: dict[str, dict[str, Any]] = {}
    for claim in claims:
        all_records = sorted(
            observations_by_claim.get(claim.claim_id, []),
            key=lambda item: (float(item.get("mtime") or 0.0), str(item.get("record_id") or "")),
            reverse=True,
        )
        recent_records = recent_by_claim.get(claim.claim_id, [])
        claim_mtime = _claim_mtime(ws, claim.claim_id)
        latest_mtime = max([claim_mtime] + [float(item.get("mtime") or 0.0) for item in all_records])
        stats[claim.claim_id] = {
            "claim_id": claim.claim_id,
            "total_record_count": len(all_records),
            "recent_record_count": len(recent_records),
            "orientation_only_record_count": sum(1 for item in all_records if item.get("orientation_only") is True),
            "claim_trust_capable_record_count": sum(1 for item in all_records if item.get("can_update_claim_trust") is True),
            "latest_mtime": latest_mtime,
            "latest_update": _iso_from_mtime(latest_mtime),
            "record_kind_counts": _kind_counts(all_records),
            "recent_record_kind_counts": _kind_counts(recent_records),
            "sample_record_refs": _sample_refs(all_records),
            "record_text": " ".join(str(item.get("text") or "") for item in all_records[:12]),
        }
    return stats


def _candidate_payload(
    *,
    claim: ClaimRecord,
    stats: dict[str, Any],
    active_stats: dict[str, Any],
    goal_tokens: set[str],
    active_goal_match_count: int,
) -> dict[str, Any]:
    goal_matches = sorted(goal_tokens & _tokens(f"{claim.statement} {stats.get('record_text', '')}"))
    focus_hits = sorted(_tokens(f"{claim.statement} {stats.get('record_text', '')}") & _FOCUS_TERMS)
    reasons: list[str] = []
    if int(stats.get("recent_record_count") or 0) > int(active_stats.get("recent_record_count") or 0):
        reasons.append(f"recent_records_concentrated:{stats.get('recent_record_count')}")
    if int(active_stats.get("recent_record_count") or 0) == 0 and int(stats.get("recent_record_count") or 0) > 0:
        reasons.append("active_claim_has_no_recent_records_in_window")
    if float(stats.get("latest_mtime") or 0.0) > float(active_stats.get("latest_mtime") or 0.0) + 1.0:
        reasons.append("latest_update_newer_than_active_claim")
    if len(goal_matches) > active_goal_match_count:
        reasons.append("goal_keyword_match:" + ",".join(goal_matches[:8]))
    if focus_hits:
        reasons.append("record_keyword_match:" + ",".join(focus_hits[:8]))
    score = (
        int(stats.get("recent_record_count") or 0) * 6
        + int(stats.get("total_record_count") or 0)
        + len(goal_matches) * 3
        + len(focus_hits)
        + (4 if "latest_update_newer_than_active_claim" in reasons else 0)
    )
    return {
        "claim_id": claim.claim_id,
        "statement_summary": _excerpt(claim.statement, limit=180),
        "statement_excerpt": _excerpt(claim.statement, limit=180),
        "recent_record_count": int(stats.get("recent_record_count") or 0),
        "total_record_count": int(stats.get("total_record_count") or 0),
        "orientation_only_record_count": int(stats.get("orientation_only_record_count") or 0),
        "claim_trust_capable_record_count": int(stats.get("claim_trust_capable_record_count") or 0),
        "latest_update": str(stats.get("latest_update") or ""),
        "record_kind_counts": dict(stats.get("record_kind_counts") or {}),
        "recent_record_kind_counts": dict(stats.get("recent_record_kind_counts") or {}),
        "sample_record_refs": list(stats.get("sample_record_refs") or []),
        "matching_reasons": reasons,
        "trust_promotion_allowed": False,
        "_score": score,
    }


def _candidate_has_signal(candidate: dict[str, Any]) -> bool:
    return bool(
        int(candidate.get("recent_record_count") or 0) > 0
        or int(candidate.get("total_record_count") or 0) > 0
        or candidate.get("matching_reasons")
    )


def _is_drift_detected(active_stats: dict[str, Any], candidates: list[dict[str, Any]]) -> bool:
    if not candidates:
        return False
    top = candidates[0]
    top_recent = int(top.get("recent_record_count") or 0)
    active_recent = int(active_stats.get("recent_record_count") or 0)
    top_total = int(top.get("total_record_count") or 0)
    active_total = int(active_stats.get("total_record_count") or 0)
    if active_recent == 0 and top_recent > 0:
        return True
    if top_recent >= active_recent + 2:
        return True
    if top_recent > active_recent and top_total >= active_total:
        return True
    if any(str(reason).startswith("goal_keyword_match:") for reason in top.get("matching_reasons") or []):
        return top_recent > 0 or top_total > active_total
    return False


def _active_claim_payload(claim: ClaimRecord | None, stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id if claim else str(stats.get("claim_id") or ""),
        "statement_summary": _excerpt(claim.statement if claim else "", limit=180),
        "statement_excerpt": _excerpt(claim.statement if claim else "", limit=180),
        "recent_record_count": int(stats.get("recent_record_count") or 0),
        "total_record_count": int(stats.get("total_record_count") or 0),
        "orientation_only_record_count": int(stats.get("orientation_only_record_count") or 0),
        "latest_update": str(stats.get("latest_update") or ""),
        "record_kind_counts": dict(stats.get("record_kind_counts") or {}),
        "recent_record_kind_counts": dict(stats.get("recent_record_kind_counts") or {}),
        "sample_record_refs": list(stats.get("sample_record_refs") or []),
    }


def _available_options() -> list[dict[str, Any]]:
    return [
        {
            "option": "keep_current_active_claim",
            "effect": "leave SessionBinding unchanged and keep relation maps scoped to the current active claim",
            "requires_confirmation": False,
        },
        {
            "option": "rebind_session_active_claim_to_candidate",
            "effect": "use aitp_v5_confirm_active_claim_rebind with explicit user confirmation; writes an audit record",
            "requires_confirmation": True,
        },
        {
            "option": "create_new_work_package_or_claim_split",
            "effect": "do not rebind yet; create or select a typed work package/claim split before future records",
            "requires_confirmation": True,
        },
        {
            "option": "continue_read_only_with_old_binding",
            "effect": "keep old binding and mark active-claim-only relation maps stale for the current goal",
            "requires_confirmation": False,
        },
    ]


def _record_distribution_rows(claims: list[ClaimRecord], stats_by_claim: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim in claims:
        stats = stats_by_claim.get(claim.claim_id, _blank_stats(claim.claim_id))
        rows.append(
            {
                "claim_id": claim.claim_id,
                "statement_excerpt": _excerpt(claim.statement, limit=120),
                "recent_record_count": int(stats.get("recent_record_count") or 0),
                "total_record_count": int(stats.get("total_record_count") or 0),
                "latest_update": str(stats.get("latest_update") or ""),
                "record_kind_counts": dict(stats.get("record_kind_counts") or {}),
            }
        )
    rows.sort(key=lambda item: (int(item.get("recent_record_count") or 0), str(item.get("latest_update") or "")), reverse=True)
    return rows


def _claim_candidate_from_store(ws: WorkspacePaths, topic_id: str, claim_id: str) -> dict[str, Any]:
    try:
        claim = get_claim(ws, claim_id)
    except (FileNotFoundError, TypeError, ValueError):
        return {}
    if topic_id and claim.topic_id != topic_id:
        return {}
    return {
        "claim_id": claim.claim_id,
        "statement_summary": _excerpt(claim.statement, limit=180),
        "statement_excerpt": _excerpt(claim.statement, limit=180),
        "recent_record_count": 0,
        "total_record_count": 0,
        "orientation_only_record_count": 0,
        "claim_trust_capable_record_count": 0,
        "latest_update": _iso_from_mtime(_claim_mtime(ws, claim.claim_id)),
        "record_kind_counts": {},
        "recent_record_kind_counts": {},
        "sample_record_refs": [],
        "matching_reasons": ["user_selected_candidate_claim"],
        "trust_promotion_allowed": False,
    }


def _topic_claims(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    claims = [
        claim
        for claim in list_valid_records(ws.registry_dir("claims"), ClaimRecord)
        if claim.topic_id == topic_id and getattr(claim, "lifecycle_status", "active") == "active"
    ]
    claims.sort(key=lambda claim: claim.claim_id)
    return claims


def _goal_match_count(goal_tokens: set[str], claim: ClaimRecord | None, stats: dict[str, Any]) -> int:
    if not goal_tokens or claim is None:
        return 0
    return len(goal_tokens & _tokens(f"{claim.statement} {stats.get('record_text', '')}"))


def _tokens(text: str) -> set[str]:
    value = str(text or "").lower()
    tokens = {token for token in re.findall(r"[a-z0-9_+\-.]{2,}", value) if len(token.strip("._-")) >= 2}
    for phrase in ("hidden symmetry", "level statistics", "active claim", "schur tail", "irreducible sector"):
        if phrase in value:
            tokens.update(phrase.split())
    return tokens


def _record_text(record: Any, attrs: tuple[str, ...]) -> str:
    parts: list[str] = []
    for attr in attrs:
        value = getattr(record, attr, "")
        parts.append(_flatten_text(value))
    return " ".join(part for part in parts if part)


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value or "")


def _blank_stats(claim_id: str) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "total_record_count": 0,
        "recent_record_count": 0,
        "orientation_only_record_count": 0,
        "claim_trust_capable_record_count": 0,
        "latest_mtime": 0.0,
        "latest_update": "",
        "record_kind_counts": {},
        "recent_record_kind_counts": {},
        "sample_record_refs": [],
        "record_text": "",
    }


def _kind_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get("record_kind") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _sample_refs(records: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    refs: list[str] = []
    for record in records[:limit]:
        ref = f"{record.get('record_kind')}:{record.get('record_id')}"
        if ref not in refs:
            refs.append(ref)
    return refs


def _claim_mtime(ws: WorkspacePaths, claim_id: str) -> float:
    if not claim_id:
        return 0.0
    path = ws.registry_dir("claims") / f"{claim_id}.md"
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _write_rebind_audit(ws: WorkspacePaths, audit: ActiveClaimRebindAuditRecord) -> None:
    body = (
        f"# Active Claim Rebind Audit\n\n"
        f"- Session: `{audit.session_id}`\n"
        f"- Old claim: `{audit.old_claim_id}`\n"
        f"- New claim: `{audit.new_claim_id}`\n"
        f"- Reason: {audit.reason}\n"
        f"- Confirmation: {audit.user_confirmation}\n"
    )
    write_record(ws.registry_dir("active_claim_rebind_audits") / f"{audit.audit_id}.md", audit, body=body)


def _empty_reconciliation(
    *,
    session_id: str,
    topic_id: str = "",
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "kind": "active_claim_focus_reconciliation",
        "status": status,
        "warning_code": "",
        "warnings": [],
        "session_id": session_id,
        "requested_session_id": session_id,
        "recovery_selection_source": "session_binding",
        "topic_id": topic_id,
        "active_claim": {},
        "candidate_sibling_claims": [],
        "record_distribution": {"recent_window_size": 0, "active_claim_recent_record_count": 0, "by_claim": []},
        "available_options": _available_options(),
        "recommended_next_action": reason,
        "relation_map_scope": _RELATION_MAP_SCOPE,
        "not_authoritative_for_current_goal_if_rebind_needed": False,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "trust_update_allowed": False,
        "can_rebind_without_confirmation": False,
    }


def _session_failure_reason(error: Exception) -> str:
    if isinstance(error, FileNotFoundError):
        return "session binding is missing"
    text = str(error)
    if "SessionBinding.__init__()" in text:
        return "session binding is missing or malformed"
    return "session binding is malformed"


def _strip_private_keys(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if not key.startswith("_")}


def _iso_from_mtime(mtime: float) -> str:
    if not mtime:
        return ""
    return datetime.fromtimestamp(float(mtime), tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
