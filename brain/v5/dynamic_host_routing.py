"""Read-only dynamic routing from bounded host intent to existing research sessions."""

from __future__ import annotations

from brain.v5.host_route_contracts import (
    HostRouteCandidate,
    HostRouteCoverage,
    HostRouteDecision,
    HostRouteRequest,
    host_route_request_fingerprint,
    normalize_host_route_request,
)
from brain.v5.host_route_coverage import combined_route_coverage, route_coverage
from brain.v5.host_route_discovery import (
    DISCOVERY_FAMILIES,
    DISCOVERY_LIMIT,
    SESSION_LIMIT,
    candidate_from_plan,
    candidate_plans,
    discovery_text,
    rank_topic_matches,
)
from brain.v5.host_route_scope import finalize_selected_route
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import (
    QuerySnapshotSession,
    ResearchQuery,
    query_records,
)


def resolve_host_research_route(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    *,
    query_session: QuerySnapshotSession | None = None,
) -> HostRouteDecision:
    """Return one bounded route decision without writing canonical or runtime state."""

    if not isinstance(ws, WorkspacePaths):
        raise TypeError("ws must be WorkspacePaths")
    normalized = normalize_host_route_request(request)
    fingerprint = host_route_request_fingerprint(normalized)
    if not _aitp_required(normalized):
        return _unscoped_decision(
            "outside_aitp",
            fingerprint,
            reason_codes=("request_does_not_require_research_memory",),
            next_operation="none",
        )

    explicit_session, conflict = _explicit_session(normalized)
    if conflict:
        return _unscoped_decision(
            "conflict",
            fingerprint,
            reason_codes=(conflict,),
            next_operation="resolve_explicit_route_conflict",
        )
    explicit_topics = _explicit_topics(normalized)
    if len(explicit_topics) > 1:
        return _unscoped_decision(
            "conflict",
            fingerprint,
            reason_codes=("multiple_explicit_topics_require_choice",),
            next_operation="resolve_explicit_route_conflict",
        )
    coherent_query = query_session or QuerySnapshotSession()
    if explicit_session:
        return _resolve_explicit_session(
            ws,
            normalized,
            explicit_session,
            fingerprint=fingerprint,
            query_session=coherent_query,
        )
    return _resolve_indexed_candidates(
        ws,
        normalized,
        fingerprint=fingerprint,
        query_session=coherent_query,
    )


def _aitp_required(request: HostRouteRequest) -> bool:
    if (
        request.explicit_session_ids
        or request.explicit_topic_ids
        or request.exact_refs
        or request.pinned_session_id
    ):
        return True
    from brain.v5.codex_facade import codex_route_intent

    payload = codex_route_intent(
        None,
        request_summary=request.request_summary,
        session_id=(
            request.explicit_session_ids[0]
            if len(request.explicit_session_ids) == 1
            else request.pinned_session_id
        ),
        topics=list(request.explicit_topic_ids),
        visible_files=list(request.visible_files),
        semantic_assessment=dict(request.semantic_assessment),
    )
    return bool(payload.get("aitp_required_before_answer"))


def _explicit_session(request: HostRouteRequest) -> tuple[str, str]:
    sessions = tuple(
        sorted(
            {
                *request.explicit_session_ids,
                *(
                    ref.partition(":")[2]
                    for ref in request.exact_refs
                    if ref.startswith("session:")
                ),
            }
        )
    )
    pin = request.pinned_session_id
    if len(sessions) > 1:
        return "", "multiple_explicit_sessions_require_choice"
    explicit = sessions[0] if sessions else ""
    if pin and explicit and pin != explicit:
        return "", "pinned_session_conflicts_with_explicit_session"
    return pin or explicit, ""


def _explicit_topics(request: HostRouteRequest) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                *request.explicit_topic_ids,
                *(
                    ref.partition(":")[2]
                    for ref in request.exact_refs
                    if ref.startswith("topic:")
                ),
            }
        )
    )


def _resolve_indexed_candidates(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    *,
    fingerprint: str,
    query_session: QuerySnapshotSession,
) -> HostRouteDecision:
    discovery_exact_refs = tuple(
        dict.fromkeys(
            (
                *request.exact_refs,
                *(f"topic:{topic_id}" for topic_id in request.explicit_topic_ids),
            )
        )
    )
    discovery = query_records(
        ws,
        ResearchQuery(
            text=discovery_text(request),
            exact_refs=discovery_exact_refs,
            families=DISCOVERY_FAMILIES,
            limit=DISCOVERY_LIMIT,
            verification_mode="strong",
        ),
        query_session=query_session,
    )
    coverage = combined_route_coverage((discovery,), query_session)
    if not coverage.strong_selection_eligible:
        return _coverage_blocked(fingerprint, (), coverage, "discovery_coverage_blocked")

    ranked_topics = rank_topic_matches(request, discovery)
    if not ranked_topics:
        return _workspace_recovery(fingerprint, coverage, "no_indexed_topic_candidate")
    topic_matches = {item[0]: item for item in ranked_topics[:3]}
    sessions = query_records(
        ws,
        ResearchQuery(
            topic_ids=tuple(topic_matches),
            families=("sessions",),
            limit=SESSION_LIMIT,
            verification_mode="strong",
        ),
        query_session=query_session,
    )
    plans = candidate_plans(topic_matches, sessions)
    if not plans:
        coverage = combined_route_coverage((discovery, sessions), query_session)
        if not coverage.strong_selection_eligible:
            return _coverage_blocked(
                fingerprint, (), coverage, "session_discovery_coverage_blocked"
            )
        return _workspace_recovery(fingerprint, coverage, "matched_topic_has_no_session")

    plans = plans[:3]
    exact_refs = tuple(
        dict.fromkeys(ref for plan in plans for ref in plan[4])
    )
    exact = query_records(
        ws,
        ResearchQuery(
            exact_refs=exact_refs,
            limit=max(1, len(exact_refs)),
            verification_mode="strong",
            exact_only=True,
        ),
        query_session=query_session,
    )
    read_errors = _verify_exact_refs(ws, request, exact_refs)
    coverage = combined_route_coverage(
        (discovery, sessions, exact),
        query_session,
        extra_errors=read_errors,
    )
    candidates = tuple(candidate_from_plan(plan) for plan in plans)
    if not coverage.strong_selection_eligible:
        return _coverage_blocked(
            fingerprint, candidates, coverage, "candidate_verification_blocked"
        )
    if len(candidates) > 1 and candidates[0].score == candidates[1].score:
        return HostRouteDecision(
            status="ambiguous",
            request_fingerprint=fingerprint,
            candidates=candidates,
            coverage=coverage,
            reason_codes=("indexed_candidates_tied",),
            recommended_next_operation="choose_research_session",
        )
    selected = candidates[0]
    return finalize_selected_route(
        ws,
        request,
        fingerprint=fingerprint,
        primary_candidates=candidates,
        primary_coverage=coverage,
        selected=selected,
        query_session=query_session,
    )


def _verify_exact_refs(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    refs: tuple[str, ...],
) -> tuple[str, ...]:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="dynamic-host-route-read",
            host=request.host or "aitp",
        ),
    )
    errors = []
    for ref in refs:
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            errors.append(f"exact route anchor {ref}: {result.status}")
    return tuple(errors)


def _resolve_explicit_session(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    session_id: str,
    *,
    fingerprint: str,
    query_session: QuerySnapshotSession,
) -> HostRouteDecision:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="dynamic-host-route-read",
            host=request.host or "aitp",
        ),
    )
    session_result = repository.read(f"session:{session_id}")
    if session_result.status != "found" or session_result.record is None:
        return _exact_read_blocked(
            fingerprint,
            reason=f"explicit_session_{session_result.status}",
        )
    topic_id = str(getattr(session_result.record, "topic_id", "") or "").strip()
    if not topic_id:
        return _exact_read_blocked(
            fingerprint,
            reason="explicit_session_missing_topic_id",
        )
    explicit_topics = _explicit_topics(request)
    if len(explicit_topics) > 1:
        return _unscoped_decision(
            "conflict",
            fingerprint,
            reason_codes=("multiple_explicit_topics_require_choice",),
            next_operation="resolve_explicit_route_conflict",
        )
    if explicit_topics and topic_id not in explicit_topics:
        return _unscoped_decision(
            "conflict",
            fingerprint,
            reason_codes=("explicit_topic_conflicts_with_session_binding",),
            next_operation="resolve_explicit_route_conflict",
        )
    topic_result = repository.read(f"topic:{topic_id}")
    if topic_result.status != "found" or topic_result.record is None:
        return _exact_read_blocked(
            fingerprint,
            reason=f"bound_topic_{topic_result.status}",
        )

    exact_refs = (f"session:{session_id}", f"topic:{topic_id}")
    retrieval = query_records(
        ws,
        ResearchQuery(
            exact_refs=exact_refs,
            families=("sessions", "topics"),
            limit=3,
            verification_mode="strong",
            exact_only=True,
        ),
        query_session=query_session,
    )
    coverage = route_coverage(retrieval, query_session)
    candidate = HostRouteCandidate(
        topic_id=topic_id,
        session_id=session_id,
        score=1_000_000,
        evidence_tier=(
            "pinned" if request.pinned_session_id else "explicit"
        ),
        component_scores={
            "pinned_session" if request.pinned_session_id else "explicit_session": 1_000_000
        },
        reason_codes=(
            "pinned_session" if request.pinned_session_id else "explicit_session",
            "exact_session_topic_verified",
        ),
        exact_refs=exact_refs,
    )
    if not coverage.strong_selection_eligible:
        return HostRouteDecision(
            status="coverage_blocked",
            request_fingerprint=fingerprint,
            candidates=(candidate,),
            coverage=coverage,
            reason_codes=("explicit_route_coverage_blocked",),
            recommended_next_operation="repair_route_coverage",
        )
    return finalize_selected_route(
        ws,
        request,
        fingerprint=fingerprint,
        primary_candidates=(candidate,),
        primary_coverage=coverage,
        selected=candidate,
        query_session=query_session,
    )


def _workspace_recovery(
    fingerprint: str,
    coverage: HostRouteCoverage,
    reason: str,
) -> HostRouteDecision:
    return HostRouteDecision(
        status="workspace_recovery",
        request_fingerprint=fingerprint,
        candidates=(),
        coverage=coverage,
        reason_codes=(reason,),
        recommended_next_operation="recover_workspace_candidates",
    )


def _coverage_blocked(
    fingerprint: str,
    candidates: tuple[HostRouteCandidate, ...],
    coverage: HostRouteCoverage,
    reason: str,
) -> HostRouteDecision:
    return HostRouteDecision(
        status="coverage_blocked",
        request_fingerprint=fingerprint,
        candidates=candidates,
        coverage=coverage,
        reason_codes=(reason,),
        recommended_next_operation="repair_route_coverage",
    )


def _unscoped_decision(
    status: str,
    fingerprint: str,
    *,
    reason_codes: tuple[str, ...],
    next_operation: str,
) -> HostRouteDecision:
    return HostRouteDecision(
        status=status,
        request_fingerprint=fingerprint,
        candidates=(),
        coverage=_empty_coverage(),
        reason_codes=reason_codes,
        recommended_next_operation=next_operation,
    )


def _exact_read_blocked(fingerprint: str, *, reason: str) -> HostRouteDecision:
    return HostRouteDecision(
        status="coverage_blocked",
        request_fingerprint=fingerprint,
        candidates=(),
        coverage=HostRouteCoverage(
            checked_families=("sessions", "topics"),
            not_shown_families=(),
            not_checked_families=(),
            malformed_count=1 if reason.endswith("malformed") else 0,
            read_errors=(reason,),
            truncated=False,
            index_status="invalid",
            index_generation=0,
            canonical_watermark="",
            scope_fresh=False,
            strong_selection_eligible=False,
        ),
        reason_codes=(reason,),
        recommended_next_operation="repair_or_choose_route",
    )


def _empty_coverage() -> HostRouteCoverage:
    return HostRouteCoverage(
        checked_families=(),
        not_shown_families=(),
        not_checked_families=(),
        malformed_count=0,
        read_errors=(),
        truncated=False,
        index_status="missing",
        index_generation=0,
        canonical_watermark="",
        scope_fresh=False,
        strong_selection_eligible=False,
    )
