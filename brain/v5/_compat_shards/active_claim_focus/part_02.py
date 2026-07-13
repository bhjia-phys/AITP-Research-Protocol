# Compatibility shard 2 for active_claim_focus.
from __future__ import annotations

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
        for claim in list_records(ws.registry_dir("claims"), ClaimRecord)
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
