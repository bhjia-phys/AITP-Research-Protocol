"""Transparent filtered and lexical retrieval over the derived AITP index."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    canonical_state_token,
    lexical_terms,
    load_query_index,
    load_query_manifest,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.record_family_registry import record_family_specs


@dataclass(frozen=True)
class ResearchQuery:
    text: str = ""
    exact_refs: tuple[str, ...] = ()
    topic_ids: tuple[str, ...] = ()
    families: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    offset: int = 0
    limit: int = 20


@dataclass(frozen=True)
class RetrievalCoverage:
    exhaustive: bool
    can_claim_no_result: bool
    checked_families: tuple[str, ...]
    unchecked_families: tuple[str, ...]
    malformed_count: int
    reason: str


@dataclass(frozen=True)
class RetrievalItem:
    record_ref: str
    family: str
    topic_id: str
    exact_score: int
    lexical_score: int
    total_score: int
    record: dict[str, Any]


@dataclass(frozen=True)
class RetrievalResult:
    items: tuple[RetrievalItem, ...]
    total_count: int
    offset: int
    limit: int
    truncated: bool
    next_offset: int | None
    index_status: str
    index_generation: int
    coverage: RetrievalCoverage
    excluded_candidates: tuple[str, ...] = ()
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def query_records(ws: WorkspacePaths, query: ResearchQuery) -> RetrievalResult:
    """Query derived metadata while preserving stale and malformed boundaries."""

    if query.offset < 0 or query.limit < 1:
        raise ValueError("offset must be non-negative and limit must be positive")
    index = load_query_index(ws)
    fresh = canonical_state_token(ws) == index.manifest.canonical_state_token
    index_status = "fresh" if fresh else "stale"
    selected_families = tuple(sorted(set(query.families)))
    all_families = tuple(sorted(record_family_specs()))
    checked_set = set(selected_families)
    checked_set.update(
        family for family in (_family_for_ref(ref) for ref in query.exact_refs) if family
    )
    checked_families = tuple(sorted(checked_set)) or all_families
    unchecked = tuple(family for family in all_families if family not in checked_families)
    malformed_count = sum(
        index.manifest.malformed_family_counts.get(family, 0) for family in checked_families
    )
    exhaustive = fresh and malformed_count == 0
    if not fresh:
        reason = "stale coverage forbids absolute no-result language"
    elif malformed_count:
        reason = "read errors in the requested scope forbid absolute no-result language"
    elif unchecked:
        reason = "fresh index exhaustively covers the requested family scope only"
    else:
        reason = "fresh index exhaustively covers all canonical families"
    coverage = RetrievalCoverage(
        exhaustive=exhaustive,
        can_claim_no_result=exhaustive,
        checked_families=checked_families,
        unchecked_families=unchecked,
        malformed_count=malformed_count,
        reason=reason,
    )

    items_by_ref: dict[str, RetrievalItem] = {}
    excluded: list[str] = []
    indexed_by_ref = {row["record_ref"]: row for row in index.documents}
    for ref in query.exact_refs:
        exact = _exact_item(ws, ref, indexed_by_ref)
        if exact is None:
            excluded.append(ref)
        else:
            items_by_ref[ref] = exact

    terms = lexical_terms(query.text)
    for row in index.documents:
        if row["record_ref"] in items_by_ref:
            continue
        if selected_families and row["family"] not in selected_families:
            continue
        if query.topic_ids and row["topic_id"] not in query.topic_ids:
            continue
        row_statuses = {row.get("status", ""), row.get("lifecycle_status", "")}
        if query.statuses and not row_statuses.intersection(query.statuses):
            continue
        lexical_score = sum(
            1 for term in terms if row["doc_id"] in index.lexical_terms.get(term, ())
        )
        if terms and lexical_score == 0:
            continue
        items_by_ref[row["record_ref"]] = RetrievalItem(
            record_ref=row["record_ref"],
            family=row["family"],
            topic_id=row["topic_id"],
            exact_score=0,
            lexical_score=lexical_score,
            total_score=lexical_score,
            record=dict(row),
        )

    ranked = sorted(
        items_by_ref.values(),
        key=lambda item: (-item.total_score, item.record_ref),
    )
    page = tuple(ranked[query.offset : query.offset + query.limit])
    next_offset = query.offset + query.limit if query.offset + query.limit < len(ranked) else None
    return RetrievalResult(
        items=page,
        total_count=len(ranked),
        offset=query.offset,
        limit=query.limit,
        truncated=next_offset is not None,
        next_offset=next_offset,
        index_status=index_status,
        index_generation=index.manifest.generation,
        coverage=coverage,
        excluded_candidates=tuple(excluded),
    )


def exact_expand(
    ws: WorkspacePaths,
    refs: tuple[str, ...] | list[str],
    *,
    limit: int = 50,
) -> RetrievalResult:
    if limit < 1:
        raise ValueError("limit must be positive")
    requested = tuple(dict.fromkeys(str(ref).strip() for ref in refs if str(ref).strip()))
    page_refs = requested[:limit]
    manifest = load_query_manifest(ws)
    fresh = canonical_state_token(ws) == manifest.canonical_state_token
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="migration", actor_id="retrieval-read", host="retrieval"),
    )
    items: list[RetrievalItem] = []
    excluded: list[str] = []
    for ref in page_refs:
        item = _exact_item_from_repository(repository, ref)
        if item is None:
            excluded.append(ref)
        else:
            items.append(item)
    checked = tuple(
        sorted(
            {
                family
                for family in (_family_for_ref(ref) for ref in page_refs)
                if family
            }
        )
    )
    all_families = tuple(sorted(record_family_specs()))
    unchecked = tuple(family for family in all_families if family not in checked)
    malformed_count = sum(manifest.malformed_family_counts.get(family, 0) for family in checked)
    exhaustive = fresh and malformed_count == 0 and not excluded
    if not fresh:
        reason = "stale coverage forbids absolute no-result language"
    elif malformed_count or excluded:
        reason = "read errors in the requested exact refs forbid absolute no-result language"
    else:
        reason = "fresh canonical exact reads cover every requested ref"
    coverage = RetrievalCoverage(
        exhaustive=exhaustive,
        can_claim_no_result=exhaustive,
        checked_families=checked,
        unchecked_families=unchecked,
        malformed_count=malformed_count,
        reason=reason,
    )
    next_offset = limit if len(requested) > limit else None
    return RetrievalResult(
        items=tuple(items),
        total_count=len(items),
        offset=0,
        limit=limit,
        truncated=next_offset is not None,
        next_offset=next_offset,
        index_status="fresh" if fresh else "stale",
        index_generation=manifest.generation,
        coverage=coverage,
        excluded_candidates=tuple(excluded),
    )


def _exact_item(
    ws: WorkspacePaths,
    ref: str,
    indexed_by_ref: dict[str, dict[str, Any]],
) -> RetrievalItem | None:
    repo = RecordRepository(
        ws,
        actor=RecordActor(actor_type="migration", actor_id="retrieval-read", host="retrieval"),
    )
    result = repo.read(ref)
    if result.status == "found":
        record = asdict(result.record) if is_dataclass(result.record) else dict(result.record)
    else:
        indexed = indexed_by_ref.get(ref)
        if indexed is None:
            return None
        record = dict(indexed)
    family = _family_for_ref(ref)
    return RetrievalItem(
        record_ref=ref,
        family=family,
        topic_id=str(record.get("topic_id") or record.get("topic") or ""),
        exact_score=100,
        lexical_score=0,
        total_score=100,
        record=record,
    )


def _exact_item_from_repository(
    repository: RecordRepository,
    ref: str,
) -> RetrievalItem | None:
    result = repository.read(ref)
    if result.status == "found":
        record = asdict(result.record) if is_dataclass(result.record) else dict(result.record)
    elif (
        result.issue is not None
        and result.issue.error_type in {"TypeError", "ValueError"}
        and result.frontmatter is not None
    ):
        record = dict(result.frontmatter)
        if result.body:
            record["body"] = result.body
    else:
        return None
    family = _family_for_ref(ref)
    return RetrievalItem(
        record_ref=ref,
        family=family,
        topic_id=str(record.get("topic_id") or record.get("topic") or ""),
        exact_score=100,
        lexical_score=0,
        total_score=100,
        record=record,
    )


def _family_for_ref(ref: str) -> str:
    kind = ref.partition(":")[0].replace("-", "_")
    for family, spec in record_family_specs().items():
        if kind in {alias.replace("-", "_") for alias in spec.exact_ref_aliases}:
            return family
    return ""
