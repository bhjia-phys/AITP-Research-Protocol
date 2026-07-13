"""Canonical session closeout planning and trust-neutral persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from brain.v5.lifecycle_models import CloseoutBoundaryItem, SessionCloseoutRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.query_index_snapshot import load_effective_query_index, scoped_index_freshness
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult
from brain.v5.research_scope import ScopeResolutionError, resolve_session_scope
from brain.v5.research_scope_contracts import canonical_typed_ref, record_payload
from brain.v5.session_lifecycle_contracts import (
    checked_families_for_refs,
    classify_boundary_items,
    deterministic_closeout_id,
    retrieval_scope_token,
    validate_closeout_record,
    validate_closeout_request_shape,
)


class SessionLifecycleError(RuntimeError):
    """Raised when a closeout cannot cross the canonical write boundary."""


@dataclass(frozen=True)
class SessionCloseoutRequest:
    session_id: str
    milestone_id: str
    completed_work: tuple[str, ...]
    can_say: tuple[CloseoutBoundaryItem, ...]
    cannot_say: tuple[CloseoutBoundaryItem, ...]
    open_gaps: tuple[CloseoutBoundaryItem, ...]
    failed_routes: tuple[CloseoutBoundaryItem, ...]
    next_actions: tuple[str, ...]
    source_record_refs: tuple[str, ...]
    pending_candidate_batch_refs: tuple[str, ...] = ()
    reusable_workflow_candidate_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_closeout_request_shape(self)


@dataclass(frozen=True)
class SessionCloseoutPlan:
    record: SessionCloseoutRecord
    missing_requirements: tuple[str, ...]
    unresolved_refs: tuple[str, ...]
    allowed: bool
    can_update_claim_trust: bool = False


def build_session_closeout_plan(
    ws: WorkspacePaths,
    request: SessionCloseoutRequest,
) -> SessionCloseoutPlan:
    """Build one deterministic closeout without mutating canonical records."""

    repository = _read_repository(ws)
    try:
        scope = resolve_session_scope(ws, request.session_id)
    except (ScopeResolutionError, TypeError, ValueError) as exc:
        raise SessionLifecycleError(f"cannot resolve closeout scope: {exc}") from exc
    session_result = repository.read(f"session:{request.session_id}")
    if session_result.status != "found" or session_result.record is None:
        raise SessionLifecycleError(f"session is not readable: {request.session_id}")
    session = record_payload(session_result)
    focus_objective_refs = _focus_objective_refs(repository, scope.focus_set_ref)

    all_requested_refs = _all_request_refs(request, scope)
    resolved_refs, unresolved_refs = _resolve_exact_refs(repository, all_requested_refs)
    unresolved_refs = list(
        dict.fromkeys([*unresolved_refs, *getattr(scope, "unresolved_refs", ())])
    )
    classifications = {
        lane: classify_boundary_items(
            getattr(request, lane),
            lane=lane,
            resolved_refs=resolved_refs,
        )
        for lane in ("can_say", "cannot_say", "open_gaps", "failed_routes")
    }
    missing: list[str] = []
    if not request.completed_work:
        missing.append("completed_work")
    if not request.next_actions:
        missing.append("next_actions")
    if not scope.focus_set_ref:
        missing.append("active_focus_set")
    for classification in classifications.values():
        missing.extend(classification.missing_requirements)

    checked_families = checked_families_for_refs(
        resolved_refs.get(ref, "") for ref in all_requested_refs
    )
    coverage = _capture_coverage(ws, checked_families)
    if not coverage["content_verified"]:
        missing.append("coverage_content_verification")
    if not checked_families:
        missing.append("checked_families")
    blocking_missing = {
        item for item in missing if not item.startswith("unverified_")
    }

    normalized_source_refs = _resolved_sequence(request.source_record_refs, resolved_refs)
    normalized_batches = _resolved_sequence(
        request.pending_candidate_batch_refs, resolved_refs
    )
    normalized_workflows = _resolved_sequence(
        request.reusable_workflow_candidate_refs, resolved_refs
    )
    unverified = tuple(
        item
        for classification in classifications.values()
        for item in classification.unverified
    )
    record = SessionCloseoutRecord(
        closeout_id=deterministic_closeout_id(request.session_id, request.milestone_id),
        session_id=request.session_id,
        topic_id=scope.primary_topic_id,
        milestone_id=request.milestone_id,
        focus_set_ref=scope.focus_set_ref,
        objective_refs=list(focus_objective_refs),
        completed_work=list(request.completed_work),
        can_say=list(classifications["can_say"].accepted),
        cannot_say=list(classifications["cannot_say"].accepted),
        open_gaps=list(classifications["open_gaps"].accepted),
        failed_routes=list(classifications["failed_routes"].accepted),
        unverified_notes=list(unverified),
        next_actions=list(request.next_actions),
        source_record_refs=list(normalized_source_refs),
        pending_candidate_batch_refs=list(normalized_batches),
        reusable_workflow_candidate_refs=list(normalized_workflows),
        index_generation=max(coverage["base_generation"], coverage["delta_generation"]),
        base_index_generation=coverage["base_generation"],
        delta_generation=coverage["delta_generation"],
        canonical_watermark=coverage["canonical_watermark"],
        retrieval_scope_token=coverage["retrieval_scope_token"],
        family_state_tokens=coverage["family_state_tokens"],
        family_content_watermarks=coverage["family_content_watermarks"],
        dirty_families=list(coverage["dirty_families"]),
        checked_families=list(checked_families),
        read_errors=list(coverage["read_errors"]),
        coverage_content_verified=coverage["content_verified"],
        coverage_exhaustive=coverage["exhaustive"] and not unresolved_refs,
        operator=str(session.get("runtime") or "session_lifecycle"),
        can_update_claim_trust=False,
    )
    record_errors = validate_closeout_record(record)
    if record_errors:
        blocking_missing.update(record_errors)
        missing.extend(error for error in record_errors if error not in missing)
    return SessionCloseoutPlan(
        record=record,
        missing_requirements=tuple(dict.fromkeys(missing)),
        unresolved_refs=tuple(unresolved_refs),
        allowed=not blocking_missing and not unresolved_refs,
        can_update_claim_trust=False,
    )


def record_session_closeout(
    ws: WorkspacePaths,
    plan: SessionCloseoutPlan,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Persist an allowed closeout without touching evidence, memory, or trust."""

    if not isinstance(plan, SessionCloseoutPlan):
        raise TypeError("plan must be a SessionCloseoutPlan")
    if not plan.allowed:
        raise SessionLifecycleError(
            "closeout plan is not allowed: "
            + ", ".join([*plan.missing_requirements, *plan.unresolved_refs])
        )
    errors = validate_closeout_record(plan.record)
    if errors:
        raise SessionLifecycleError("invalid closeout record: " + "; ".join(errors))
    _require_current_coverage(ws, plan.record)
    repository = RecordRepository(ws, actor=actor)
    return repository.write(
        "session_closeouts",
        plan.record,
        body=_closeout_body(plan.record),
        policy=WritePolicy(mode="create_or_idempotent"),
    )


def _capture_coverage(
    ws: WorkspacePaths,
    checked_families: tuple[str, ...],
) -> dict[str, object]:
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    try:
        snapshot = load_effective_query_index(ws)
        freshness = scoped_index_freshness(ws, snapshot, checked_families)
    except Exception as exc:  # noqa: BLE001 - coverage failures must fail closed.
        return {
            "base_generation": 0,
            "delta_generation": 0,
            "canonical_watermark": "",
            "retrieval_scope_token": "",
            "family_state_tokens": {family: "" for family in checked_families},
            "family_content_watermarks": {family: "" for family in checked_families},
            "dirty_families": (),
            "read_errors": (f"{type(exc).__name__}: {exc}",),
            "content_verified": False,
            "exhaustive": False,
        }
    state_tokens = {
        family: snapshot.family_state_tokens.get(family, "")
        for family in checked_families
    }
    content_watermarks = {
        family: snapshot.family_content_watermarks.get(family, "")
        for family in checked_families
    }
    dirty = tuple(sorted(set(freshness.dirty_families) & set(checked_families)))
    malformed = tuple(
        family
        for family in checked_families
        if snapshot.malformed_family_counts.get(family, 0)
    )
    read_errors = tuple(
        dict.fromkeys(
            [
                *freshness.diagnostics,
                *(f"malformed records in checked family: {family}" for family in malformed),
            ]
        )
    )
    verified = bool(
        freshness.scope_state_fresh
        and freshness.scope_content_verified
        and not dirty
        and not malformed
        and not read_errors
    )
    return {
        "base_generation": int(snapshot.manifest.generation),
        "delta_generation": int(snapshot.delta_generation),
        "canonical_watermark": str(snapshot.manifest.canonical_watermark or ""),
        "retrieval_scope_token": retrieval_scope_token(
            checked_families=checked_families,
            family_state_tokens=state_tokens,
            family_content_watermarks=content_watermarks,
        ),
        "family_state_tokens": state_tokens,
        "family_content_watermarks": content_watermarks,
        "dirty_families": dirty,
        "read_errors": read_errors,
        "content_verified": verified,
        "exhaustive": verified,
    }


def _require_current_coverage(ws: WorkspacePaths, record: SessionCloseoutRecord) -> None:
    current = _capture_coverage(ws, tuple(record.checked_families))
    if not current["content_verified"]:
        raise SessionLifecycleError("closeout coverage is no longer content verified")
    if current["retrieval_scope_token"] != record.retrieval_scope_token:
        raise SessionLifecycleError("closeout coverage changed after planning")


def _resolve_exact_refs(
    repository: RecordRepository,
    refs: Iterable[str],
) -> tuple[dict[str, str], list[str]]:
    resolved: dict[str, str] = {}
    unresolved: list[str] = []
    for ref in dict.fromkeys(refs):
        try:
            canonical, _spec, _record_id = canonical_typed_ref(ref)
        except ValueError:
            unresolved.append(str(ref))
            continue
        result = repository.read(canonical)
        if result.status == "found" and result.record is not None:
            resolved[str(ref)] = canonical
        else:
            unresolved.append(canonical)
    return resolved, list(dict.fromkeys(unresolved))


def _all_request_refs(request: SessionCloseoutRequest, scope: object) -> tuple[str, ...]:
    boundary_refs = [
        ref
        for lane in (request.can_say, request.cannot_say, request.open_gaps, request.failed_routes)
        for item in lane
        for ref in item.source_refs
    ]
    return tuple(
        dict.fromkeys(
            [
                *getattr(scope, "primary_refs", ()),
                *getattr(scope, "supporting_refs", ()),
                *boundary_refs,
                *request.source_record_refs,
                *request.pending_candidate_batch_refs,
                *request.reusable_workflow_candidate_refs,
            ]
        )
    )


def _focus_objective_refs(
    repository: RecordRepository,
    focus_set_ref: str,
) -> tuple[str, ...]:
    if not focus_set_ref:
        return ()
    result = repository.read(focus_set_ref)
    payload = record_payload(result)
    refs: list[str] = []
    for ref in payload.get("objective_refs", []):
        try:
            canonical, _spec, _record_id = canonical_typed_ref(ref)
        except ValueError:
            continue
        refs.append(canonical)
    return tuple(dict.fromkeys(refs))


def _resolved_sequence(
    refs: Iterable[str],
    resolved_refs: dict[str, str],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(resolved_refs[ref] for ref in refs if ref in resolved_refs)
    )


def _read_repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="session-lifecycle-read",
            host="session-lifecycle",
        ),
    )


def _closeout_body(record: SessionCloseoutRecord) -> str:
    lines = [
        f"# Session Closeout: {record.milestone_id}",
        "",
        f"Session: `{record.session_id}`",
        f"Topic: `{record.topic_id}`",
        f"Focus: `{record.focus_set_ref}`",
        "",
        "This process record is trust-neutral and requires exact expansion.",
    ]
    return "\n".join(lines) + "\n"
