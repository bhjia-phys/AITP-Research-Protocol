"""Retrieval planning and result merging for scoped context compilation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Callable

from brain.v5.context_compiler_support import unique_refs
from brain.v5.context_disclosure import startup_support_refs
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, pin_current_record
from brain.v5.research_retrieval import (
    ResearchQuery,
    RetrievalResult,
    exact_expand,
)
from brain.v5.research_scope import ScopeResolution


QueryFunction = Callable[[WorkspacePaths, ResearchQuery], RetrievalResult]

_GLOBAL_OPERATIONAL_FAMILIES = frozenset(
    {
        "code_states",
        "contexts",
        "execution_environments",
        "research_programs",
        "tool_recipes",
    }
)


@dataclass(frozen=True)
class ScopedRetrievalOutcome:
    result: RetrievalResult
    blocked_explicit_refs: tuple[str, ...] = ()


def scoped_retrieval_result(
    ws: WorkspacePaths,
    request: Any,
    scope: ScopeResolution,
    *,
    query_fn: QueryFunction,
) -> ScopedRetrievalOutcome:
    explicit_refs, blocked_explicit_refs = _partition_explicit_refs(
        ws,
        request.exact_refs,
        scope,
    )
    primary_exact = unique_refs(
        [
            *scope.primary_refs,
            *explicit_refs,
        ]
    )
    query_text = " ".join(
        part.strip() for part in (request.objective_text, request.user_goal) if part.strip()
    )
    support_refs = (
        startup_support_refs(scope)
        if request.disclosure_level == "startup_orientation"
        else scope.supporting_refs
    )
    support_limit = _support_page_size(request.record_limit, len(support_refs))
    primary_limit = max(1, request.record_limit - support_limit)
    primary = query_fn(
        ws,
        ResearchQuery(
            text=query_text,
            exact_refs=primary_exact,
            topic_ids=(scope.primary_topic_id,),
            families=tuple(dict.fromkeys(request.families)),
            include_unscoped_families=tuple(
                sorted(_GLOBAL_OPERATIONAL_FAMILIES.intersection(request.families))
            ),
            limit=primary_limit,
            verification_mode="orientation",
        ),
    )
    if not support_refs or support_limit == 0:
        return ScopedRetrievalOutcome(primary, blocked_explicit_refs)
    supporting = exact_expand(ws, support_refs, limit=support_limit)
    if support_limit < len(support_refs):
        supporting = replace(
            supporting,
            total_count=len(support_refs),
            truncated=True,
            next_offset=support_limit,
            coverage=replace(
                supporting.coverage,
                exhaustive=False,
                can_claim_no_result=False,
                reason="reviewed supporting scope is paginated in the normal context slice",
            ),
        )
    return ScopedRetrievalOutcome(
        merge_retrieval_results(primary, supporting, limit=request.record_limit),
        blocked_explicit_refs,
    )


def _partition_explicit_refs(
    ws: WorkspacePaths,
    refs: tuple[str, ...],
    scope: ScopeResolution,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    requested = unique_refs(list(refs))
    if not requested:
        return (), ()
    bounded = requested[:50]
    result = exact_expand(ws, bounded, limit=max(1, len(bounded)))
    items = {item.record_ref: item for item in result.items}
    primary = set(scope.primary_refs)
    supporting = set(scope.supporting_refs)
    blocked_scope = set(scope.excluded_refs) | set(scope.unresolved_refs)
    allowed: list[str] = []
    blocked: list[str] = list(requested[50:])
    for ref in bounded:
        if ref in blocked_scope:
            blocked.append(ref)
            continue
        if ref in supporting:
            continue
        if ref in primary:
            allowed.append(ref)
            continue
        item = items.get(ref)
        if item is None:
            allowed.append(ref)
            continue
        if item.topic_id and item.topic_id != scope.primary_topic_id:
            blocked.append(ref)
            continue
        item_program_id = str(item.record.get("program_id") or "")
        if item_program_id and item_program_id != scope.program_id:
            blocked.append(ref)
            continue
        if not item.topic_id and item.family not in _GLOBAL_OPERATIONAL_FAMILIES:
            blocked.append(ref)
            continue
        allowed.append(ref)
    return tuple(allowed), tuple(dict.fromkeys(blocked))


def _support_page_size(record_limit: int, support_count: int) -> int:
    if support_count <= 0 or record_limit <= 1:
        return 0
    reserved = max(1, record_limit // 4)
    return min(support_count, reserved, 20, record_limit - 1)


def exact_disclosure_result(
    ws: WorkspacePaths,
    request: Any,
) -> tuple[RetrievalResult, dict[str, Any]]:
    requested = unique_refs(list(request.exact_refs))
    exact_pins = tuple(getattr(request, "exact_pins", ()))
    if exact_pins:
        if any(not isinstance(pin, PinnedRecordRef) for pin in exact_pins):
            raise ValueError("exact expansion pins must be PinnedRecordRef values")
        if tuple(pin.record_ref for pin in exact_pins) != tuple(request.exact_refs):
            raise ValueError("exact expansion pins must match requested refs")
        for pin in exact_pins:
            if pin_current_record(ws, pin.record_ref) != pin:
                raise ValueError(f"exact expansion pin is stale: {pin.record_ref}")
    bounded = requested[:50]
    page_size = min(request.record_limit, 20)
    page = bounded[request.record_offset : request.record_offset + page_size]
    result = exact_expand(ws, page, limit=max(1, len(page)))
    next_offset = (
        request.record_offset + len(page)
        if request.record_offset + len(page) < len(bounded)
        else None
    )
    input_truncated = len(requested) > len(bounded)
    unchecked_refs = tuple(ref for ref in bounded if ref not in set(page))
    incomplete = bool(unchecked_refs or input_truncated)
    result = replace(
        result,
        total_count=len(requested),
        offset=request.record_offset,
        limit=page_size,
        truncated=incomplete,
        next_offset=next_offset,
        coverage=replace(
            result.coverage,
            exhaustive=result.coverage.exhaustive and not incomplete,
            can_claim_no_result=result.coverage.can_claim_no_result and not incomplete,
            reason=(
                "canonical exact reads cover the requested page; other requested refs remain unchecked"
                if incomplete
                else result.coverage.reason
            ),
        ),
    )
    expansion = {
        "surface": "record_refs",
        "refs": [item.record_ref for item in result.items],
        "requested_refs": list(bounded),
        "requested_pins": [asdict(pin) for pin in exact_pins],
        "requested_ref_count": len(requested),
        "bounded_ref_count": len(bounded),
        "input_truncated": input_truncated,
        "page_size": len(page),
        "next_offset": next_offset,
        "items": [asdict(item) for item in result.items],
        "checked_requested_refs": list(page),
        "unchecked_requested_refs": list(unchecked_refs),
        "unresolved_requested_refs": list(result.excluded_candidates),
        "canonical_record_payloads_in_expansion": True,
        "anchored_source_passages": [],
        "requires_explicit_call": True,
        "full_record_bodies_in_default_context": False,
    }
    return result, expansion


def merge_retrieval_results(
    primary: RetrievalResult,
    supporting: RetrievalResult,
    *,
    limit: int,
) -> RetrievalResult:
    items = list(primary.items)
    seen = {item.record_ref for item in items}
    supporting_duplicates = sum(
        1 for item in supporting.items if item.record_ref in seen
    )
    items.extend(item for item in supporting.items if item.record_ref not in seen)
    merged_count = primary.total_count + max(
        0,
        supporting.total_count - supporting_duplicates,
    )
    page_truncated = len(items) > limit
    checked = tuple(
        sorted(
            set(primary.coverage.checked_families)
            | set(supporting.coverage.checked_families)
        )
    )
    unchecked = tuple(
        sorted(
            set(primary.coverage.unchecked_families)
            & set(supporting.coverage.unchecked_families)
        )
    )
    coverage = replace(
        primary.coverage,
        exhaustive=primary.coverage.exhaustive and supporting.coverage.exhaustive,
        can_claim_no_result=False,
        checked_families=checked,
        unchecked_families=unchecked,
        malformed_count=(
            primary.coverage.malformed_count + supporting.coverage.malformed_count
        ),
        read_errors=tuple(
            dict.fromkeys(
                [*primary.coverage.read_errors, *supporting.coverage.read_errors]
            )
        ),
        reason="primary-topic query plus exact reviewed supporting scope",
    )
    return RetrievalResult(
        items=tuple(items[:limit]),
        total_count=merged_count,
        offset=primary.offset,
        limit=limit,
        truncated=bool(primary.truncated or supporting.truncated or page_truncated),
        next_offset=(
            primary.next_offset
            if primary.next_offset is not None
            else limit if page_truncated else None
        ),
        index_status=(
            "fresh"
            if primary.index_status == supporting.index_status == "fresh"
            else "stale"
        ),
        index_generation=max(primary.index_generation, supporting.index_generation),
        coverage=coverage,
        excluded_candidates=tuple(
            dict.fromkeys(
                [*primary.excluded_candidates, *supporting.excluded_candidates]
            )
        ),
    )


def record_expansion(result: RetrievalResult) -> dict[str, Any]:
    refs = [item.record_ref for item in result.items]
    return {
        "surface": "record_refs",
        "refs": refs,
        "page_size": min(20, max(1, len(refs))),
        "next_offset": result.next_offset,
        "requires_explicit_call": True,
        "full_record_bodies_in_default_context": False,
    }
