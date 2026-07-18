"""Finalize a selected host route against existing single-topic scope records."""

from __future__ import annotations

from brain.v5.host_route_contracts import (
    HostRouteCandidate,
    HostRouteCoverage,
    HostRouteDecision,
    HostRouteRequest,
)
from brain.v5.host_route_coverage import extend_route_coverage
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import (
    QuerySnapshotSession,
    ResearchQuery,
    query_records,
)
from brain.v5.research_scope import ScopeResolutionError, resolve_session_scope


_MAX_SCOPE_REFS = 64
_MAX_SUPPORTING_TOPICS = 3


def finalize_selected_route(
    ws: WorkspacePaths,
    request: HostRouteRequest,
    *,
    fingerprint: str,
    primary_candidates: tuple[HostRouteCandidate, ...],
    primary_coverage: HostRouteCoverage,
    selected: HostRouteCandidate,
    query_session: QuerySnapshotSession,
) -> HostRouteDecision:
    try:
        scope = resolve_session_scope(
            ws,
            selected.session_id,
            query_session=query_session,
        )
    except (ScopeResolutionError, OSError, TypeError, ValueError) as exc:
        coverage = extend_route_coverage(
            primary_coverage,
            query_session,
            extra_checked_families=("session_focus_sets",),
            extra_errors=(f"session scope resolution failed: {type(exc).__name__}: {exc}",),
        )
        return _scope_blocked(fingerprint, primary_candidates, coverage)

    checked_families = tuple(
        sorted(
            {
                "session_focus_sets",
                *(_family_for_ref(ref) for ref in scope.checked_refs),
            }
            - {""}
        )
    )
    scope_errors = tuple(
        [
            *scope.read_errors,
            *(f"unresolved scope ref: {ref}" for ref in scope.unresolved_refs),
        ]
    )
    supporting_ids = tuple(
        dict.fromkeys(
            topic_id
            for topic_id in scope.supporting_topic_ids
            if topic_id and topic_id != selected.topic_id
        )
    )
    if len(supporting_ids) > _MAX_SUPPORTING_TOPICS:
        scope_errors = (*scope_errors, "supporting topic scope exceeds route bound")
    supporting_ids = supporting_ids[:_MAX_SUPPORTING_TOPICS]
    if not supporting_ids:
        coverage = extend_route_coverage(
            primary_coverage,
            query_session,
            extra_checked_families=checked_families,
            extra_errors=scope_errors,
        )
        if not coverage.strong_selection_eligible:
            return _scope_blocked(fingerprint, primary_candidates, coverage)
        return _selected_decision(
            fingerprint,
            primary_candidates,
            coverage,
            selected,
            (),
        )

    sessions = query_records(
        ws,
        ResearchQuery(
            topic_ids=supporting_ids,
            families=("sessions",),
            limit=12,
            verification_mode="strong",
        ),
        query_session=query_session,
    )
    exact_refs = tuple(
        dict.fromkeys(
            [
                *scope.checked_refs,
                *(f"topic:{topic_id}" for topic_id in supporting_ids),
                *(item.record_ref for item in sessions.items),
            ]
        )
    )
    if len(exact_refs) > _MAX_SCOPE_REFS:
        scope_errors = (*scope_errors, "selected scope exact refs exceed route bound")
        exact_refs = exact_refs[:_MAX_SCOPE_REFS]
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
    scope_errors = (
        *scope_errors,
        *_verify_exact_refs(ws, request, exact_refs),
    )
    coverage = extend_route_coverage(
        primary_coverage,
        query_session,
        retrievals=(sessions, exact),
        extra_checked_families=checked_families,
        extra_errors=scope_errors,
    )
    supporting_candidates = _supporting_candidates(
        supporting_ids,
        sessions.items,
        scope.requires_revalidation_refs,
        selected.score,
    )
    candidates = (selected, *supporting_candidates[:2])
    if not coverage.strong_selection_eligible:
        return _scope_blocked(fingerprint, candidates, coverage)
    return _selected_decision(
        fingerprint,
        candidates,
        coverage,
        selected,
        supporting_ids,
    )


def _supporting_candidates(topic_ids, session_items, scope_refs, primary_score):
    sessions_by_topic: dict[str, list[str]] = {topic_id: [] for topic_id in topic_ids}
    for item in session_items:
        topic_id = str(item.topic_id or item.record.get("topic_id") or "").strip()
        session_id = str(item.record.get("record_id") or "").strip()
        if topic_id in sessions_by_topic and session_id:
            sessions_by_topic[topic_id].append(session_id)
    candidates = []
    for topic_id in topic_ids:
        session_ids = sorted(set(sessions_by_topic[topic_id]))
        if len(session_ids) != 1:
            continue
        session_id = session_ids[0]
        exact_refs = (
            f"session:{session_id}",
            f"topic:{topic_id}",
            *tuple(scope_refs)[:30],
        )
        candidates.append(
            HostRouteCandidate(
                topic_id=topic_id,
                session_id=session_id,
                score=max(0, primary_score - 1),
                evidence_tier="supporting_scope",
                component_scores={"reviewed_supporting_scope": 1},
                reason_codes=("reviewed_cross_topic_scope", "target_revalidation_required"),
                exact_refs=exact_refs,
                supporting_only=True,
                requires_target_revalidation=True,
            )
        )
    return tuple(candidates)


def _verify_exact_refs(ws, request, refs):
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="dynamic-host-route-scope-read",
            host=request.host or "aitp",
        ),
    )
    errors = []
    for ref in refs:
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            errors.append(f"exact scope ref {ref}: {result.status}")
    return tuple(errors)


def _family_for_ref(ref: str) -> str:
    kind = ref.partition(":")[0].replace("-", "_")
    for family, spec in record_family_specs().items():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if kind in aliases:
            return family
    return ""


def _selected_decision(
    fingerprint,
    candidates,
    coverage,
    selected,
    supporting_topic_ids,
):
    return HostRouteDecision(
        status="selected",
        request_fingerprint=fingerprint,
        candidates=tuple(candidates),
        coverage=coverage,
        selected_topic_id=selected.topic_id,
        selected_session_id=selected.session_id,
        supporting_topic_ids=tuple(supporting_topic_ids),
        requires_target_revalidation=bool(supporting_topic_ids),
        reason_codes=("unique_verified_route_with_resolved_scope",),
        recommended_next_operation="enter_selected_session",
    )


def _scope_blocked(fingerprint, candidates, coverage):
    return HostRouteDecision(
        status="coverage_blocked",
        request_fingerprint=fingerprint,
        candidates=tuple(candidates)[:3],
        coverage=coverage,
        reason_codes=("selected_session_scope_blocked",),
        recommended_next_operation="repair_route_scope",
    )
