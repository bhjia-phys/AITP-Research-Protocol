"""Coverage aggregation for one coherent dynamic-route query snapshot."""

from __future__ import annotations

from brain.v5.host_route_contracts import HostRouteCoverage
from brain.v5.record_family_registry import record_family_specs
from brain.v5.research_retrieval import QuerySnapshotSession, RetrievalResult


def route_coverage(
    retrieval: RetrievalResult,
    query_session: QuerySnapshotSession,
) -> HostRouteCoverage:
    return combined_route_coverage((retrieval,), query_session)


def combined_route_coverage(
    retrievals: tuple[RetrievalResult, ...],
    query_session: QuerySnapshotSession,
    *,
    extra_errors: tuple[str, ...] = (),
    extra_checked_families: tuple[str, ...] = (),
) -> HostRouteCoverage:
    snapshot = query_session.snapshot
    watermark = snapshot.manifest.canonical_watermark if snapshot is not None else ""
    checked = tuple(
        sorted(
            {
                *extra_checked_families,
                *(
                    family
                    for retrieval in retrievals
                    for family in retrieval.coverage.checked_families
                ),
            }
        )
    )
    all_families = tuple(sorted(record_family_specs()))
    malformed = (
        sum(snapshot.malformed_family_counts.get(family, 0) for family in checked)
        if snapshot is not None
        else sum(retrieval.coverage.malformed_count for retrieval in retrievals)
    )
    errors = tuple(
        dict.fromkeys(
            [
                *(
                    error
                    for retrieval in retrievals
                    for error in retrieval.coverage.read_errors
                ),
                *(
                    f"excluded exact ref: {ref}"
                    for retrieval in retrievals
                    for ref in retrieval.excluded_candidates
                ),
                *extra_errors,
            ]
        )
    )
    fresh = bool(retrievals) and all(
        retrieval.index_status == "fresh" for retrieval in retrievals
    )
    scope_fresh = fresh and all(
        retrieval.coverage.scope_fresh
        and retrieval.coverage.scope_content_verified
        for retrieval in retrievals
    )
    truncated = any(retrieval.truncated for retrieval in retrievals)
    strong = bool(
        fresh and scope_fresh and malformed == 0 and not errors and not truncated and watermark
    )
    return HostRouteCoverage(
        checked_families=checked,
        not_shown_families=(),
        not_checked_families=tuple(
            family for family in all_families if family not in checked
        ),
        malformed_count=malformed,
        read_errors=errors,
        truncated=truncated,
        index_status="fresh" if fresh else "stale",
        index_generation=(snapshot.manifest.generation if snapshot is not None else 0),
        canonical_watermark=watermark,
        scope_fresh=scope_fresh,
        strong_selection_eligible=strong,
    )


def extend_route_coverage(
    base: HostRouteCoverage,
    query_session: QuerySnapshotSession,
    *,
    retrievals: tuple[RetrievalResult, ...] = (),
    extra_errors: tuple[str, ...] = (),
    extra_checked_families: tuple[str, ...] = (),
) -> HostRouteCoverage:
    snapshot = query_session.snapshot
    checked = tuple(sorted({*base.checked_families, *extra_checked_families}))
    all_families = tuple(sorted(record_family_specs()))
    errors = tuple(
        dict.fromkeys(
            [
                *base.read_errors,
                *(
                    error
                    for retrieval in retrievals
                    for error in retrieval.coverage.read_errors
                ),
                *(
                    f"excluded exact ref: {ref}"
                    for retrieval in retrievals
                    for ref in retrieval.excluded_candidates
                ),
                *extra_errors,
            ]
        )
    )
    malformed = (
        sum(snapshot.malformed_family_counts.get(family, 0) for family in checked)
        if snapshot is not None
        else base.malformed_count
    )
    fresh = base.index_status == "fresh" and all(
        retrieval.index_status == "fresh" for retrieval in retrievals
    )
    scope_fresh = base.scope_fresh and all(
        retrieval.coverage.scope_fresh
        and retrieval.coverage.scope_content_verified
        for retrieval in retrievals
    )
    truncated = base.truncated or any(retrieval.truncated for retrieval in retrievals)
    watermark = base.canonical_watermark
    strong = bool(
        fresh and scope_fresh and malformed == 0 and not errors and not truncated and watermark
    )
    return HostRouteCoverage(
        checked_families=checked,
        not_shown_families=(),
        not_checked_families=tuple(
            family for family in all_families if family not in checked
        ),
        malformed_count=malformed,
        read_errors=errors,
        truncated=truncated,
        index_status="fresh" if fresh else "stale",
        index_generation=base.index_generation,
        canonical_watermark=watermark,
        scope_fresh=scope_fresh,
        strong_selection_eligible=strong,
    )
