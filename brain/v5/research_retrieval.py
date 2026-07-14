"""Transparent filtered and lexical retrieval over the derived AITP index."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import (
    IndexIntegrityError,
    IndexManifest,
    lexical_terms,
    load_query_index,
    load_query_manifest,
    query_index_is_fresh,
)
from brain.v5.query_index_delta import (
    load_effective_query_index,
    scoped_index_freshness,
    scoped_index_orientation,
)
from brain.v5.query_index_delta_contracts import EffectiveIndexSnapshot
from brain.v5.query_index_fallback import strict_family_fallback
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.record_family_registry import record_family_specs


@dataclass(frozen=True)
class ResearchQuery:
    text: str = ""
    exact_refs: tuple[str, ...] = ()
    topic_ids: tuple[str, ...] = ()
    program_ids: tuple[str, ...] = ()
    session_ids: tuple[str, ...] = ()
    families: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    offset: int = 0
    limit: int = 20
    allow_family_fallback: bool = False
    fallback_max_records: int = 500
    verification_mode: str = "strong"
    exact_only: bool = False


@dataclass(frozen=True)
class RetrievalCoverage:
    exhaustive: bool
    can_claim_no_result: bool
    checked_families: tuple[str, ...]
    unchecked_families: tuple[str, ...]
    malformed_count: int
    reason: str
    scope_state_fresh: bool = False
    scope_content_verified: bool = False
    scope_fresh: bool = False
    global_fresh: bool = False
    dirty_families: tuple[str, ...] = ()
    checked_paths: tuple[str, ...] = ()
    fallback_used: bool = False
    read_errors: tuple[str, ...] = ()


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
    if query.allow_family_fallback and query.fallback_max_records < 1:
        raise ValueError("fallback_max_records must be positive")
    if query.verification_mode not in {"strong", "orientation"}:
        raise ValueError("verification_mode must be strong or orientation")
    if not isinstance(query.exact_only, bool):
        raise ValueError("exact_only must be a boolean")
    selected_families = tuple(sorted(set(query.families)))
    all_families = tuple(sorted(record_family_specs()))
    checked_set = set(selected_families)
    checked_set.update(
        family for family in (_family_for_ref(ref) for ref in query.exact_refs) if family
    )
    checked_families = tuple(sorted(checked_set)) or all_families
    unchecked = tuple(family for family in all_families if family not in checked_families)
    try:
        index = load_effective_query_index(
            ws,
            allow_cached=query.verification_mode == "orientation",
        )
    except (IndexIntegrityError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        index = _fail_closed_index_snapshot(ws, all_families, exc)
    freshness = (
        scoped_index_freshness(ws, index, checked_families)
        if query.verification_mode == "strong"
        else scoped_index_orientation(ws, index, checked_families)
    )
    fresh = freshness.scope_fresh
    fallback_used = False
    scope_state_fresh = freshness.scope_state_fresh
    scope_content_verified = freshness.scope_content_verified
    scope_fresh = freshness.scope_fresh
    checked_paths = freshness.checked_paths
    read_errors = freshness.diagnostics
    if not fresh and query.allow_family_fallback and len(checked_families) == 1:
        fallback = strict_family_fallback(
            ws,
            index,
            checked_families[0],
            max_records=query.fallback_max_records,
        )
        if fallback.used and fallback.snapshot is not None:
            index = fallback.snapshot
            fallback_used = True
            fresh = fallback.content_verified
            scope_state_fresh = fallback.content_verified
            scope_content_verified = fallback.content_verified
            scope_fresh = fallback.content_verified
            checked_paths = fallback.checked_paths
            read_errors = fallback.diagnostics
        else:
            read_errors = tuple(dict.fromkeys([*read_errors, *fallback.diagnostics]))
    index_status = "fresh" if fresh else "stale"
    malformed_count = sum(
        index.malformed_family_counts.get(family, 0) for family in checked_families
    )
    exhaustive = (
        fresh
        and scope_content_verified
        and malformed_count == 0
        and not read_errors
    )
    if fallback_used and exhaustive:
        reason = "bounded canonical single-family fallback exhaustively covers the requested scope"
    elif fallback_used:
        reason = "bounded canonical single-family fallback has malformed or read-error coverage"
    elif not fresh:
        reason = "stale coverage forbids absolute no-result language"
    elif query.verification_mode == "orientation":
        reason = "orientation state is current but strong canonical content was not checked"
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
        scope_state_fresh=scope_state_fresh,
        scope_content_verified=scope_content_verified,
        scope_fresh=scope_fresh,
        global_fresh=freshness.global_fresh,
        dirty_families=freshness.dirty_families,
        checked_paths=checked_paths,
        fallback_used=fallback_used,
        read_errors=read_errors,
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
        if query.exact_only:
            continue
        if selected_families and row["family"] not in selected_families:
            continue
        if query.topic_ids or query.program_ids:
            topic_match = bool(query.topic_ids and row["topic_id"] in query.topic_ids)
            program_match = bool(
                query.program_ids and row.get("program_id", "") in query.program_ids
            )
            if not topic_match and not program_match:
                continue
        if query.session_ids and row.get("session_id", "") not in query.session_ids:
            continue
        row_statuses = {row.get("status", ""), row.get("lifecycle_status", "")}
        if query.statuses and not row_statuses.intersection(query.statuses):
            continue
        matching_terms = [
            term for term in terms if row["doc_id"] in index.lexical_terms.get(term, ())
        ]
        lexical_score = len(matching_terms)
        if terms and lexical_score == 0:
            continue
        weighted_score = sum(
            1
            + int(
                math.log2(
                    (len(index.documents) + 1)
                    / (len(index.lexical_terms.get(term, ())) + 1)
                )
                * 4
            )
            for term in matching_terms
        )
        items_by_ref[row["record_ref"]] = RetrievalItem(
            record_ref=row["record_ref"],
            family=row["family"],
            topic_id=row["topic_id"],
            exact_score=0,
            lexical_score=lexical_score,
            total_score=weighted_score,
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
    fresh = len(items) == len(page_refs)
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
        scope_state_fresh=fresh,
        scope_content_verified=fresh,
        scope_fresh=fresh,
        global_fresh=fresh,
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
        total_score=10_000,
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
        total_score=10_000,
        record=record,
    )


def _family_for_ref(ref: str) -> str:
    kind = ref.partition(":")[0].replace("-", "_")
    for family, spec in record_family_specs().items():
        if kind in {alias.replace("-", "_") for alias in spec.exact_ref_aliases}:
            return family
    return ""


def _fail_closed_index_snapshot(
    ws: WorkspacePaths,
    all_families: tuple[str, ...],
    error: Exception,
) -> EffectiveIndexSnapshot:
    diagnostic = f"{type(error).__name__}: {error}"
    try:
        base = load_query_index(ws)
        return EffectiveIndexSnapshot(
            manifest=base.manifest,
            documents=base.documents,
            lexical_terms=base.lexical_terms,
            record_refs=base.record_refs,
            family_state_tokens=dict(base.manifest.family_state_tokens),
            family_content_watermarks=dict(base.manifest.family_content_watermarks),
            family_content_accumulators=dict(base.manifest.family_content_accumulators),
            malformed_family_counts=dict(base.manifest.malformed_family_counts),
            dirty_families=all_families,
            read_errors=(diagnostic,),
        )
    except (IndexIntegrityError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        try:
            manifest = load_query_manifest(ws)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            manifest = IndexManifest(
                generation=0,
                canonical_watermark="",
                canonical_state_token="",
                content_hash="",
                record_count=0,
                family_counts={},
                malformed_count=0,
                malformed_family_counts={},
                built_at="",
                document_hash="",
                lexical_hash="",
                issues_hash="",
            )
        return EffectiveIndexSnapshot(
            manifest=manifest,
            documents=(),
            lexical_terms={},
            record_refs=(),
            family_state_tokens=dict(manifest.family_state_tokens),
            family_content_watermarks=dict(manifest.family_content_watermarks),
            family_content_accumulators=dict(manifest.family_content_accumulators),
            malformed_family_counts=dict(manifest.malformed_family_counts),
            dirty_families=all_families,
            read_errors=(diagnostic,),
        )
