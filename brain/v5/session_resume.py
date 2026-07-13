"""Derived startup resume cards compiled from canonical closeouts and current scope."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from brain.v5.context_compiler import ContextRequest, compile_research_context
from brain.v5.lifecycle_models import SessionCloseoutRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_snapshot import load_effective_query_index, scoped_index_freshness
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import ResearchQuery, query_records
from brain.v5.session_resume_rendering import (
    bounded_closeout_lanes,
    canonical_resume_boundary_json,
    closeout_exact_refs,
    compact_context_from_resume,
    compact_resume_boundary,
    finalize_resume_card,
    render_resume_boundary_section,
)


class SessionResumeError(RuntimeError):
    """Raised when the latest canonical closeout cannot be selected safely."""


def build_session_resume_card(
    ws: WorkspacePaths,
    session_id: str,
    *,
    max_tokens: int = 800,
) -> dict[str, Any]:
    """Compile one bounded startup-orientation card without persisting it."""

    if not str(session_id or "").strip():
        raise ValueError("session_id must be non-empty")
    if not 128 <= max_tokens <= 800:
        raise ValueError("max_tokens must be between 128 and 800")
    context = compile_research_context(
        ws,
        ContextRequest(
            session_id=session_id,
            disclosure_level="startup_orientation",
            max_tokens=max_tokens,
            max_bytes=4000,
            candidate_limit=6,
            record_limit=40,
        ),
    )
    closeout, closeout_ref, lookup = _latest_closeout(ws, session_id)
    if closeout is None:
        card = _fallback_card(context, lookup)
    else:
        card = _closeout_card(ws, context, closeout, closeout_ref, lookup)
    return finalize_resume_card(card, max_tokens=max_tokens)


def _latest_closeout(
    ws: WorkspacePaths,
    session_id: str,
) -> tuple[SessionCloseoutRecord | None, str, dict[str, Any]]:
    result = query_records(
        ws,
        ResearchQuery(
            families=("session_closeouts",),
            session_ids=(session_id,),
            limit=200,
            allow_family_fallback=True,
            fallback_max_records=500,
            verification_mode="strong",
        ),
    )
    lookup = {
        "exhaustive": bool(result.coverage.exhaustive and not result.truncated),
        "index_status": result.index_status,
        "index_generation": result.index_generation,
        "read_errors": list(result.coverage.read_errors),
        "malformed_count": result.coverage.malformed_count,
        "truncated": result.truncated,
    }
    if result.truncated:
        raise SessionResumeError("closeout lookup is truncated; exact selection is required")
    repository = _read_repository(ws)
    candidates: list[tuple[float, str, SessionCloseoutRecord]] = []
    for item in result.items:
        exact = repository.read(item.record_ref)
        if exact.status != "found" or not isinstance(exact.record, SessionCloseoutRecord):
            detail = exact.issue.message if exact.issue else exact.status
            raise SessionResumeError(
                f"indexed closeout cannot be read exactly: {item.record_ref}: {detail}"
            )
        if exact.record.session_id != session_id:
            raise SessionResumeError("indexed closeout belongs to another session")
        candidates.append((_timestamp(exact.record), item.record_ref, exact.record))
    if not candidates:
        return None, "", lookup
    candidates.sort(key=lambda value: (value[0], value[1]), reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise SessionResumeError("latest session closeout is ambiguous")
    _timestamp_value, record_ref, closeout = candidates[0]
    return closeout, record_ref, lookup


def _closeout_card(
    ws: WorkspacePaths,
    context: Any,
    closeout: SessionCloseoutRecord,
    closeout_ref: str,
    lookup: dict[str, Any],
) -> dict[str, Any]:
    coverage = _compare_coverage(ws, closeout, lookup)
    lanes, omitted = bounded_closeout_lanes(closeout)
    exact_refs = closeout_exact_refs(closeout, closeout_ref)
    return {
        "kind": "session_resume_card",
        "disclosure_level": "startup_orientation",
        "session_id": closeout.session_id,
        "topic_id": closeout.topic_id,
        "closeout_ref": closeout_ref,
        "closeout_id": closeout.closeout_id,
        "milestone_id": closeout.milestone_id,
        "focus_set_ref": context.focus_set_ref or closeout.focus_set_ref,
        "current_objective": dict(context.current_objective),
        "current_boundary": dict(context.current_boundary),
        "scope": dict(context.scope),
        **lanes,
        "unverified_note_count": len(closeout.unverified_notes),
        "pending_candidate_batch_refs": list(closeout.pending_candidate_batch_refs[:20]),
        "reusable_workflow_candidate_refs": list(
            closeout.reusable_workflow_candidate_refs[:20]
        ),
        "coverage": coverage,
        "exact_expansion_refs": list(exact_refs[:20]),
        "exact_expansion_ref_count": len(exact_refs),
        "exact_expansion_refs_truncated": len(exact_refs) > 20,
        "fallback_used": False,
        "not_shown_counts": omitted,
        "source_index_generation": max(
            int(context.source_index_generation),
            int(closeout.index_generation),
        ),
        "partial": bool(coverage["relevant_stale"] or context.partial or omitted),
        "truncated": bool(omitted or len(exact_refs) > 20),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _fallback_card(context: Any, lookup: dict[str, Any]) -> dict[str, Any]:
    coverage = {
        "checked_families": list(context.coverage.get("checked_families") or []),
        "changed_state_families": [],
        "changed_content_families": [],
        "dirty_families": list(context.coverage.get("dirty_families") or []),
        "read_errors": list(
            dict.fromkeys([*lookup.get("read_errors", []), *context.read_errors])
        ),
        "content_verified": bool(context.coverage.get("scope_content_verified")),
        "scope_state_fresh": bool(context.coverage.get("scope_state_fresh")),
        "scope_content_verified": bool(
            context.coverage.get("scope_content_verified")
        ),
        "can_claim_no_result": False,
        "exhaustive": bool(lookup.get("exhaustive") and context.coverage.get("exhaustive")),
        "relevant_stale": bool(
            not lookup.get("exhaustive")
            or context.index_status != "fresh"
            or context.read_errors
        ),
        "closeout_lookup_exhaustive": bool(lookup.get("exhaustive")),
    }
    return {
        "kind": "session_resume_card",
        "disclosure_level": "startup_orientation",
        "session_id": context.session_id,
        "topic_id": context.topic_id,
        "closeout_ref": "",
        "closeout_id": "",
        "milestone_id": "",
        "focus_set_ref": context.focus_set_ref,
        "current_objective": dict(context.current_objective),
        "current_boundary": dict(context.current_boundary),
        "scope": dict(context.scope),
        "completed_work": [],
        "can_say": [],
        "cannot_say": [],
        "open_gaps": [],
        "failed_routes": [],
        "next_actions": [],
        "unverified_note_count": 0,
        "pending_candidate_batch_refs": [],
        "reusable_workflow_candidate_refs": [],
        "coverage": coverage,
        "exact_expansion_refs": list(context.record_refs[:20]),
        "exact_expansion_ref_count": len(context.record_refs),
        "exact_expansion_refs_truncated": len(context.record_refs) > 20,
        "fallback_used": True,
        "not_shown_counts": {},
        "source_index_generation": int(context.source_index_generation),
        "partial": True,
        "truncated": bool(context.truncated or len(context.record_refs) > 20),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _compare_coverage(
    ws: WorkspacePaths,
    closeout: SessionCloseoutRecord,
    lookup: dict[str, Any],
) -> dict[str, Any]:
    checked = tuple(closeout.checked_families)
    read_errors: list[str] = list(lookup.get("read_errors") or [])
    try:
        snapshot = load_effective_query_index(ws)
        freshness = scoped_index_freshness(ws, snapshot, checked)
    except Exception as exc:  # noqa: BLE001 - resume must report derived-read failures.
        return {
            "checked_families": list(checked),
            "changed_state_families": list(checked),
            "changed_content_families": list(checked),
            "dirty_families": list(checked),
            "read_errors": [*read_errors, f"{type(exc).__name__}: {exc}"],
            "content_verified": False,
            "scope_state_fresh": False,
            "scope_content_verified": False,
            "can_claim_no_result": False,
            "exhaustive": False,
            "relevant_stale": True,
            "closeout_lookup_exhaustive": bool(lookup.get("exhaustive")),
        }
    changed_state = [
        family
        for family in checked
        if snapshot.family_state_tokens.get(family, "")
        != closeout.family_state_tokens.get(family, "")
    ]
    changed_content = [
        family
        for family in checked
        if snapshot.family_content_watermarks.get(family, "")
        != closeout.family_content_watermarks.get(family, "")
    ]
    dirty = sorted(set(freshness.dirty_families) & set(checked))
    malformed = [
        family for family in checked if snapshot.malformed_family_counts.get(family, 0)
    ]
    read_errors.extend(freshness.diagnostics)
    read_errors.extend(
        f"malformed records in checked family: {family}" for family in malformed
    )
    read_errors = list(dict.fromkeys(read_errors))
    verified = bool(
        freshness.scope_state_fresh
        and freshness.scope_content_verified
        and not dirty
        and not malformed
        and not read_errors
    )
    relevant_stale = bool(
        changed_state
        or changed_content
        or dirty
        or not verified
        or not lookup.get("exhaustive")
    )
    return {
        "checked_families": list(checked),
        "changed_state_families": changed_state,
        "changed_content_families": changed_content,
        "dirty_families": dirty,
        "read_errors": read_errors,
        "content_verified": verified,
        "scope_state_fresh": bool(freshness.scope_state_fresh),
        "scope_content_verified": bool(freshness.scope_content_verified),
        "can_claim_no_result": False,
        "exhaustive": bool(verified and lookup.get("exhaustive")),
        "relevant_stale": relevant_stale,
        "closeout_lookup_exhaustive": bool(lookup.get("exhaustive")),
        "base_index_generation": int(snapshot.manifest.generation),
        "delta_generation": int(snapshot.delta_generation),
    }


def _timestamp(record: SessionCloseoutRecord) -> float:
    try:
        return datetime.fromisoformat(record.created_at.replace("Z", "+00:00")).timestamp()
    except ValueError as exc:
        raise SessionResumeError(
            f"closeout has invalid created_at: {record.closeout_id}"
        ) from exc


def _read_repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="session-resume-read",
            host="session-resume",
        ),
    )
