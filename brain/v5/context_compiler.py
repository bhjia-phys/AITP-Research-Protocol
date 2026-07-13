"""Bounded research context compiled through an isolated session scope."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from brain.v5.indexed_topic_snapshot import (
    load_indexed_topic_snapshot,
)
from brain.v5.context_selection import candidate_not_shown, select_candidate_summaries
from brain.v5.context_compiler_support import (
    boundary as _boundary,
    bounded_markdown as _bounded_markdown,
    candidate_summary as _candidate_summary,
    context_lines as _context_lines,
    empty_boundary as _empty_boundary,
    estimate_context_tokens,
    index_generation as _index_generation,
    objective as _objective,
    read_errors as _read_errors,
    record_mapping as _record_mapping,
    typed_ref as _typed_ref,
)
from brain.v5.context_compiler_retrieval import (
    QueryFunction,
    exact_disclosure_result as _exact_disclosure_result,
    record_expansion as _record_expansion,
    scoped_retrieval_result as _scoped_retrieval_result,
)
from brain.v5.context_disclosure import (
    next_level_handles,
    route_hint_coverage,
    route_hint_markdown,
    route_hint_refs,
    scope_payload,
    validate_disclosure_level,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index, load_query_manifest
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import RetrievalResult, query_records
from brain.v5.research_scope import ScopeResolution, resolve_session_scope


_DEFAULT_CONTEXT_FAMILIES = (
    "artifacts",
    "checkpoints",
    "claim_statuses",
    "claims",
    "code_states",
    "evidence",
    "exploratory_records",
    "object_relations",
    "physics_objects",
    "proof_obligations",
    "quiet_checkpoints",
    "reference_locations",
    "research_run_events",
    "research_runs",
    "routes",
    "sensemaking_reports",
    "source_assets",
    "tool_recipes",
    "tool_runs",
    "validation_contracts",
    "validation_results",
)
class ContextCompilationError(RuntimeError):
    """Raised when the requested session cannot anchor a bounded context."""


@dataclass(frozen=True)
class ContextRequest:
    session_id: str
    objective_text: str = ""
    user_goal: str = ""
    topic_id: str = ""
    disclosure_level: str = "normal_research"
    focus_set_ref: str = ""
    program_id: str = ""
    include_cross_topic_discovery: bool = False
    exact_refs: tuple[str, ...] = ()
    families: tuple[str, ...] = _DEFAULT_CONTEXT_FAMILIES
    max_tokens: int = 1200
    max_bytes: int = 6000
    record_limit: int = 160
    candidate_limit: int = 12
    record_offset: int = 0

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must be non-empty")
        validate_disclosure_level(self.disclosure_level)
        if self.disclosure_level == "exact_expansion" and not self.exact_refs:
            raise ValueError("exact_expansion requires at least one exact ref")
        if not isinstance(self.include_cross_topic_discovery, bool):
            raise ValueError("include_cross_topic_discovery must be a boolean")
        if self.max_tokens < 64:
            raise ValueError("max_tokens must be at least 64")
        if self.max_bytes < 384:
            raise ValueError("max_bytes must be at least 384")
        if not 1 <= self.record_limit <= 200:
            raise ValueError("record_limit must be between 1 and 200")
        if not 1 <= self.candidate_limit <= 40:
            raise ValueError("candidate_limit must be between 1 and 40")
        if self.record_offset < 0:
            raise ValueError("record_offset must be non-negative")


@dataclass(frozen=True)
class ContextBundle:
    session_id: str
    topic_id: str
    disclosure_level: str
    focus_set_ref: str
    program_id: str
    scope: dict[str, Any]
    next_level_handles: dict[str, Any]
    current_objective: dict[str, Any]
    current_boundary: dict[str, Any]
    recent_process_refs: tuple[str, ...]
    candidate_summaries: tuple[dict[str, Any], ...]
    record_refs: tuple[str, ...]
    expansion: dict[str, Any]
    coverage: dict[str, Any]
    read_errors: tuple[str, ...]
    not_found_refs: tuple[str, ...]
    not_checked_families: tuple[str, ...]
    index_status: str
    source_index_generation: int
    total_candidates: int
    not_shown_count: int
    not_shown_reason: tuple[str, ...]
    partial: bool
    retrieval_truncated: bool
    render_truncated: bool
    truncated: bool
    can_claim_no_prior_result: bool
    requires_exact_expansion_before_trust_conclusions: bool
    markdown: str
    byte_count: int
    estimated_tokens: int
    max_bytes: int
    max_tokens: int
    orientation_only: bool = True
    summary_inputs_trusted: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def compile_research_context(
    ws: WorkspacePaths,
    request: ContextRequest,
    *,
    query_fn: QueryFunction = query_records,
    repository: RecordRepository | None = None,
) -> ContextBundle:
    """Compile one trust-neutral context through the fixed disclosure ladder."""

    repo = repository or RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="context-compiler-read",
            host="context-compiler",
        ),
    )
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    try:
        scope = resolve_session_scope(
            ws,
            request.session_id,
            include_discovery=request.include_cross_topic_discovery,
            focus_set_ref=request.focus_set_ref,
            program_id=request.program_id,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise ContextCompilationError(
            f"cannot resolve scope for session {request.session_id!r}: {exc}"
        ) from exc
    session_result = repo.read(f"session:{request.session_id}")
    if session_result.status != "found" or session_result.record is None:
        detail = session_result.issue.message if session_result.issue else session_result.status
        raise ContextCompilationError(
            f"cannot compile context for session {request.session_id!r}: {detail}"
        )
    session = _record_mapping(session_result.record)
    topic_id = scope.primary_topic_id
    if not topic_id:
        raise ContextCompilationError("session does not identify a topic")
    if request.topic_id.strip() and request.topic_id.strip() != topic_id:
        raise ContextCompilationError("requested topic conflicts with the resolved session scope")
    if request.disclosure_level == "route_hint":
        return _compile_route_hint(ws, request, scope)

    if request.disclosure_level == "exact_expansion":
        result, expansion = _exact_disclosure_result(ws, request)
    else:
        result = _scoped_retrieval_result(
            ws,
            request,
            scope,
            query_fn=query_fn,
        )
        blocked_explicit_refs = result.blocked_explicit_refs
        result = result.result
        expansion = _record_expansion(result)
    if request.disclosure_level == "exact_expansion":
        blocked_explicit_refs = ()
    return _bundle_from_result(
        request=request,
        scope=scope,
        session=session,
        result=result,
        expansion=expansion,
        blocked_explicit_refs=blocked_explicit_refs,
    )


def _compile_route_hint(
    ws: WorkspacePaths,
    request: ContextRequest,
    scope: ScopeResolution,
) -> ContextBundle:
    refs = route_hint_refs(scope)
    coverage = route_hint_coverage()
    raw_markdown = route_hint_markdown(scope, refs)
    markdown, budget_truncated = _bounded_markdown(
        raw_markdown.rstrip().splitlines(),
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )
    generation = load_query_manifest(ws).generation
    return ContextBundle(
        session_id=request.session_id,
        topic_id=scope.primary_topic_id,
        disclosure_level=request.disclosure_level,
        focus_set_ref=scope.focus_set_ref,
        program_id=scope.program_id,
        scope=scope_payload(scope),
        next_level_handles=next_level_handles(scope, request.disclosure_level),
        current_objective={
            "objective_id": f"route-{scope.primary_topic_id}",
            "title": scope.primary_topic_id,
            "requested_focus": "",
            "source_ref": f"topic:{scope.primary_topic_id}",
            "orientation_only": True,
        },
        current_boundary=_empty_boundary(),
        recent_process_refs=(),
        candidate_summaries=(),
        record_refs=refs,
        expansion={
            "surface": "record_refs",
            "refs": list(refs),
            "page_size": min(20, max(1, len(refs))),
            "next_offset": None,
            "requires_explicit_call": True,
            "full_record_bodies_in_default_context": False,
        },
        coverage=coverage,
        read_errors=scope.read_errors,
        not_found_refs=(),
        not_checked_families=tuple(coverage["unchecked_families"]),
        index_status="fresh",
        source_index_generation=generation,
        total_candidates=len(refs),
        not_shown_count=0,
        not_shown_reason=(),
        partial=True,
        retrieval_truncated=False,
        render_truncated=budget_truncated,
        truncated=budget_truncated,
        can_claim_no_prior_result=False,
        requires_exact_expansion_before_trust_conclusions=True,
        markdown=markdown,
        byte_count=len(markdown.encode("utf-8")),
        estimated_tokens=estimate_context_tokens(markdown),
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )


def _bundle_from_result(
    *,
    request: ContextRequest,
    scope: ScopeResolution,
    session: dict[str, Any],
    result: RetrievalResult,
    expansion: dict[str, Any],
    blocked_explicit_refs: tuple[str, ...],
) -> ContextBundle:
    topic_id = scope.primary_topic_id
    item_by_ref = {item.record_ref: item for item in result.items}
    topic_item = item_by_ref.get(f"topic:{topic_id}")
    active_claim_ref = _typed_ref("claim", session.get("active_claim"))
    claim_item = item_by_ref.get(active_claim_ref) if active_claim_ref else None
    current_objective = _objective(topic_id, topic_item, request)
    current_boundary = _boundary(claim_item)
    record_refs = tuple(item.record_ref for item in result.items)
    omitted_supporting_refs = tuple(
        ref for ref in scope.supporting_refs if ref not in set(record_refs)
    )
    supporting = set(scope.supporting_refs)
    revalidation = set(scope.requires_revalidation_refs)
    anchor_refs = (
        set()
        if request.disclosure_level == "exact_expansion"
        else {f"session:{request.session_id}", f"topic:{topic_id}"}
    )
    all_candidate_summaries = [
        _candidate_summary(
            item,
            retrieval_rank=rank,
            scope_lane="supporting" if item.record_ref in supporting else "primary",
            requires_target_revalidation=item.record_ref in revalidation,
        )
        for rank, item in enumerate(result.items)
        if item.record_ref not in anchor_refs
    ]
    candidate_summaries = select_candidate_summaries(
        all_candidate_summaries,
        limit=request.candidate_limit,
    )
    matched_anchor_count = len(anchor_refs.difference(result.excluded_candidates))
    not_shown_count, not_shown_reason = candidate_not_shown(
        total_count=result.total_count,
        shown_anchor_count=matched_anchor_count,
        page_candidate_count=len(all_candidate_summaries),
        selected_count=len(candidate_summaries),
        retrieval_truncated=result.truncated,
    )
    read_errors = tuple(dict.fromkeys([*_read_errors(result), *scope.read_errors]))
    not_found_refs = tuple(result.excluded_candidates)
    not_checked_families = tuple(result.coverage.unchecked_families)
    coverage = asdict(result.coverage)
    scope_data = scope_payload(scope)
    scope_data["blocked_explicit_refs"] = list(blocked_explicit_refs)
    scope_data["not_shown_refs"] = list(
        dict.fromkeys(
            [
                *scope_data["not_shown_refs"],
                *blocked_explicit_refs,
                *omitted_supporting_refs,
            ]
        )
    )
    lines = _context_lines(
        request=request,
        topic_id=topic_id,
        current_objective=current_objective,
        current_boundary=current_boundary,
        candidate_summaries=candidate_summaries,
        coverage=coverage,
        index_status=result.index_status,
        read_errors=read_errors,
        not_found_refs=not_found_refs,
        not_checked_families=not_checked_families,
        not_shown_count=not_shown_count,
        not_shown_reason=not_shown_reason,
        record_refs=record_refs,
        scope=scope_data,
    )
    markdown, budget_truncated = _bounded_markdown(
        lines,
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )
    truncated = bool(result.truncated or budget_truncated)
    partial = bool(
        result.index_status != "fresh"
        or not result.coverage.exhaustive
        or not_found_refs
        or not_checked_families
        or read_errors
        or truncated
        or not_shown_count
        or scope.unresolved_refs
        or scope.excluded_refs
        or blocked_explicit_refs
    )
    can_claim_no_prior_result = bool(
        request.disclosure_level == "normal_research"
        and result.total_count == 0
        and result.coverage.can_claim_no_result
        and not truncated
        and not read_errors
        and not not_found_refs
    )
    process_refs = tuple(
        row["record_ref"]
        for row in all_candidate_summaries
        if row["process_family"]
    )[:12]
    handles = next_level_handles(scope, request.disclosure_level)
    recoverable_refs = (
        ()
        if request.disclosure_level == "exact_expansion"
        else tuple(dict.fromkeys([*blocked_explicit_refs, *omitted_supporting_refs]))
    )
    handles["exact_expansion_refs"] = list(recoverable_refs[:20])
    handles["exact_expansion_ref_count"] = len(recoverable_refs)
    handles["exact_expansion_refs_truncated"] = len(recoverable_refs) > 20
    handles["blocked_refs_require_exact_expansion"] = bool(blocked_explicit_refs)
    return ContextBundle(
        session_id=request.session_id,
        topic_id=topic_id,
        disclosure_level=request.disclosure_level,
        focus_set_ref=scope.focus_set_ref,
        program_id=scope.program_id,
        scope=scope_data,
        next_level_handles=handles,
        current_objective=current_objective,
        current_boundary=current_boundary,
        recent_process_refs=process_refs,
        candidate_summaries=candidate_summaries,
        record_refs=record_refs,
        expansion=expansion,
        coverage=coverage,
        read_errors=read_errors,
        not_found_refs=not_found_refs,
        not_checked_families=not_checked_families,
        index_status=result.index_status,
        source_index_generation=_index_generation(result),
        total_candidates=result.total_count,
        not_shown_count=not_shown_count,
        not_shown_reason=not_shown_reason,
        partial=partial,
        retrieval_truncated=bool(result.truncated),
        render_truncated=budget_truncated,
        truncated=truncated,
        can_claim_no_prior_result=can_claim_no_prior_result,
        requires_exact_expansion_before_trust_conclusions=True,
        markdown=markdown,
        byte_count=len(markdown.encode("utf-8")),
        estimated_tokens=estimate_context_tokens(markdown),
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )


def context_bundle_payload(bundle: ContextBundle) -> dict[str, Any]:
    """Return the stable JSON-compatible representation used by host surfaces."""

    return asdict(bundle)
