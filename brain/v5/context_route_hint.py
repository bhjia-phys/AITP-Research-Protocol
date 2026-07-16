"""Pure route-hint field assembly for the bounded context compiler."""

from __future__ import annotations

from typing import Any

from brain.v5.context_compiler_support import (
    bounded_markdown,
    empty_boundary,
    estimate_context_tokens,
)
from brain.v5.context_disclosure import (
    next_level_handles,
    route_hint_coverage,
    route_hint_markdown,
    route_hint_refs,
    scope_payload,
)
from brain.v5.knowledge_context_integration import knowledge_coverage
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import load_query_manifest
from brain.v5.research_scope import ScopeResolution
from brain.v5.skill_context_integration import skill_context_coverage


def route_hint_bundle_fields(
    ws: WorkspacePaths,
    request: Any,
    scope: ScopeResolution,
) -> dict[str, Any]:
    refs = route_hint_refs(scope)
    coverage = route_hint_coverage()
    coverage.update(knowledge_coverage({}))
    coverage.update(skill_context_coverage({}))
    raw_markdown = route_hint_markdown(scope, refs)
    markdown, budget_truncated = bounded_markdown(
        raw_markdown.rstrip().splitlines(),
        max_bytes=request.max_bytes,
        max_tokens=request.max_tokens,
    )
    generation = load_query_manifest(ws).generation
    return {
        "session_id": request.session_id,
        "topic_id": scope.primary_topic_id,
        "disclosure_level": request.disclosure_level,
        "focus_set_ref": scope.focus_set_ref,
        "program_id": scope.program_id,
        "scope": scope_payload(scope),
        "next_level_handles": next_level_handles(scope, request.disclosure_level),
        "current_objective": {
            "objective_id": f"route-{scope.primary_topic_id}",
            "title": scope.primary_topic_id,
            "requested_focus": "",
            "source_ref": f"topic:{scope.primary_topic_id}",
            "orientation_only": True,
        },
        "current_boundary": empty_boundary(),
        "recent_process_refs": (),
        "candidate_summaries": (),
        "record_refs": refs,
        "expansion": {
            "surface": "record_refs",
            "refs": list(refs),
            "page_size": min(20, max(1, len(refs))),
            "next_offset": None,
            "requires_explicit_call": True,
            "full_record_bodies_in_default_context": False,
        },
        "knowledge_context": {},
        "applicable_skills": (),
        "coverage": coverage,
        "read_errors": scope.read_errors,
        "not_found_refs": (),
        "not_checked_families": tuple(coverage["unchecked_families"]),
        "index_status": "fresh",
        "source_index_generation": generation,
        "total_candidates": len(refs),
        "not_shown_count": 0,
        "not_shown_reason": (),
        "partial": True,
        "retrieval_truncated": False,
        "render_truncated": budget_truncated,
        "truncated": budget_truncated,
        "can_claim_no_prior_result": False,
        "requires_exact_expansion_before_trust_conclusions": True,
        "markdown": markdown,
        "byte_count": len(markdown.encode("utf-8")),
        "estimated_tokens": estimate_context_tokens(markdown),
        "max_bytes": request.max_bytes,
        "max_tokens": request.max_tokens,
    }


__all__ = ["route_hint_bundle_fields"]
