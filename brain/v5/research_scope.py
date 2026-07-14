"""Canonical writers and isolated resolution for M1 research-session scope."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from brain.v5.lifecycle_models import (
    CrossTopicRelationRecord,
    ResearchProgramRecord,
    SessionFocusSetRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult
from brain.v5.research_retrieval import QuerySnapshotSession, ResearchQuery, query_records
from brain.v5.research_scope_contracts import (
    SCOPED_PROGRAM_REVIEW_STATUSES,
    SUPPORTING_BRIDGE_STATUSES,
    canonical_typed_ref,
    inspect_existing_ref,
    record_payload,
    validate_cross_topic_relation,
    validate_research_program,
    validate_session_focus_set,
)


class ScopeResolutionError(RuntimeError):
    """Raised when a session cannot be resolved to one unambiguous primary scope."""


@dataclass(frozen=True)
class ScopeResolution:
    session_id: str
    primary_topic_id: str
    focus_set_ref: str
    program_id: str
    primary_refs: tuple[str, ...]
    supporting_topic_ids: tuple[str, ...]
    supporting_refs: tuple[str, ...]
    excluded_refs: tuple[str, ...]
    unresolved_refs: tuple[str, ...]
    discovery_refs: tuple[str, ...]
    requires_revalidation_refs: tuple[str, ...]
    checked_refs: tuple[str, ...] = ()
    unchecked_refs: tuple[str, ...] = ()
    read_errors: tuple[str, ...] = ()
    claim_trust_transfer: str = "forbidden"


def record_research_program(
    ws: WorkspacePaths,
    record: ResearchProgramRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    repository = RecordRepository(ws, actor=actor)
    validate_research_program(repository, record)
    return repository.write(
        "research_programs",
        record,
        body=f"# Research Program: {record.title}\n",
        policy=WritePolicy(mode="create_or_idempotent"),
    )


def record_session_focus_set(
    ws: WorkspacePaths,
    record: SessionFocusSetRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    repository = RecordRepository(ws, actor=actor)
    validate_session_focus_set(repository, record)
    return repository.write(
        "session_focus_sets",
        record,
        body=(
            f"# Session Focus Set: {record.focus_set_id}\n\n"
            f"Primary topic: `{record.primary_topic_id}`\n"
        ),
        policy=WritePolicy(mode="create_or_idempotent"),
    )


def record_cross_topic_relation(
    ws: WorkspacePaths,
    record: CrossTopicRelationRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    repository = RecordRepository(ws, actor=actor)
    validate_cross_topic_relation(repository, record)
    return repository.write(
        "cross_topic_relations",
        record,
        body=(
            f"# Cross-Topic Relation: {record.relation_id}\n\n"
            f"Boundary: {record.applicability_boundary}\n"
        ),
        policy=WritePolicy(mode="create_or_idempotent"),
    )


def resolve_session_scope(
    ws: WorkspacePaths,
    session_id: str,
    *,
    include_discovery: bool = False,
    focus_set_ref: str = "",
    program_id: str = "",
    query_session: QuerySnapshotSession | None = None,
) -> ScopeResolution:
    """Resolve one session without rebinding its runtime claim or topic."""

    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="research-scope-read",
            host="research-scope",
        ),
    )
    _session_ref, _session_spec, session_result = inspect_existing_ref(
        repository, f"session:{session_id}"
    )
    session = record_payload(session_result)
    primary_topic_id = str(session.get("topic_id") or "")
    if not primary_topic_id:
        raise ScopeResolutionError("session binding has no primary topic")
    inspect_existing_ref(repository, f"topic:{primary_topic_id}")

    focus = _select_focus_set(
        ws,
        repository,
        session_id=session_id,
        requested_ref=focus_set_ref,
        query_session=query_session,
    )
    if focus is not None and focus.primary_topic_id != primary_topic_id:
        raise ScopeResolutionError("focus primary topic conflicts with the session topic")

    state = _ScopeState()
    state.check(f"session:{session_id}")
    state.add_primary(f"session:{session_id}")
    state.check(f"topic:{primary_topic_id}")
    state.add_primary(f"topic:{primary_topic_id}")
    _add_session_anchors(repository, session, state)

    selected_program_id = program_id.strip()
    selected_focus_ref = ""
    if focus is not None:
        selected_focus_ref = f"session_focus_set:{focus.focus_set_id}"
        selected_program_id = selected_program_id or focus.program_id
        state.check(selected_focus_ref)
        state.add_primary(selected_focus_ref)
        _add_exact_primary(repository, focus.focus_ref, state)
        for ref in focus.objective_refs:
            _add_exact_primary(repository, ref, state)
        for ref in focus.excluded_refs:
            _add_excluded(repository, ref, state)
        for ref in focus.supporting_refs:
            _add_supporting_ref(
                repository,
                ref,
                primary_topic_id=primary_topic_id,
                include_discovery=include_discovery,
                state=state,
            )

    supporting_topic_ids: list[str] = []
    if selected_program_id:
        _add_program_scope(
            repository,
            selected_program_id,
            primary_topic_id=primary_topic_id,
            state=state,
            supporting_topic_ids=supporting_topic_ids,
        )
    supporting_topic_ids.extend(state.supporting_topic_ids)
    state.remove_excluded_and_unresolved()
    return ScopeResolution(
        session_id=session_id,
        primary_topic_id=primary_topic_id,
        focus_set_ref=selected_focus_ref,
        program_id=selected_program_id,
        primary_refs=_unique(state.primary_refs),
        supporting_topic_ids=_unique(supporting_topic_ids),
        supporting_refs=_unique(state.supporting_refs),
        excluded_refs=_unique(state.excluded_refs),
        unresolved_refs=_unique(state.unresolved_refs),
        discovery_refs=_unique(state.discovery_refs),
        requires_revalidation_refs=_unique(state.requires_revalidation_refs),
        checked_refs=_unique(state.checked_refs),
        unchecked_refs=_unique(state.unresolved_refs),
        read_errors=_unique(state.read_errors),
    )


@dataclass
class _ScopeState:
    primary_refs: list[str] = field(default_factory=list)
    supporting_refs: list[str] = field(default_factory=list)
    excluded_refs: list[str] = field(default_factory=list)
    unresolved_refs: list[str] = field(default_factory=list)
    discovery_refs: list[str] = field(default_factory=list)
    requires_revalidation_refs: list[str] = field(default_factory=list)
    checked_refs: list[str] = field(default_factory=list)
    read_errors: list[str] = field(default_factory=list)
    supporting_topic_ids: list[str] = field(default_factory=list)

    def check(self, ref: str) -> None:
        self.checked_refs.append(ref)

    def add_primary(self, ref: str) -> None:
        self.primary_refs.append(ref)

    def remove_excluded_and_unresolved(self) -> None:
        blocked = set(self.excluded_refs) | set(self.unresolved_refs)
        self.primary_refs = [ref for ref in self.primary_refs if ref not in blocked]
        self.supporting_refs = [ref for ref in self.supporting_refs if ref not in blocked]


def _select_focus_set(
    ws: WorkspacePaths,
    repository: RecordRepository,
    *,
    session_id: str,
    requested_ref: str,
    query_session: QuerySnapshotSession | None,
) -> SessionFocusSetRecord | None:
    if requested_ref:
        canonical, spec, result = inspect_existing_ref(repository, requested_ref)
        if spec.family != "session_focus_sets":
            raise ScopeResolutionError(f"requested focus ref is not a focus set: {canonical}")
        focus = result.record
        if not isinstance(focus, SessionFocusSetRecord) or focus.session_id != session_id:
            raise ScopeResolutionError("requested focus set belongs to another session")
        if focus.scope_status != "active":
            raise ScopeResolutionError(
                f"requested focus set is not active: {focus.scope_status}"
            )
        return focus
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    # Focus is routing metadata: verify the cached state token, then exact-read
    # every selected record. A stale state falls back to the bounded family scan.
    result = query_records(
        ws,
        ResearchQuery(
            families=("session_focus_sets",),
            session_ids=(session_id,),
            limit=200,
            allow_family_fallback=True,
            fallback_max_records=500,
            verification_mode="orientation",
        ),
        query_session=query_session,
    )
    if result.truncated:
        raise ScopeResolutionError("focus-set lookup is incomplete; exact selection is required")
    if (
        result.index_status != "fresh"
        or not result.coverage.scope_state_fresh
        or result.coverage.malformed_count
        or result.coverage.read_errors
    ):
        raise ScopeResolutionError(
            "focus-set lookup is stale or malformed; repair the derived index or records"
        )
    active: list[SessionFocusSetRecord] = []
    for item in result.items:
        exact = repository.read(item.record_ref)
        if exact.status != "found" or not isinstance(exact.record, SessionFocusSetRecord):
            detail = exact.issue.message if exact.issue else exact.status
            raise ScopeResolutionError(
                f"indexed focus set cannot be read exactly: {item.record_ref}: {detail}"
            )
        if exact.record.session_id == session_id and exact.record.scope_status == "active":
            active.append(exact.record)
    if not active:
        return None
    active.sort(key=lambda row: (_focus_timestamp(row), row.focus_set_id), reverse=True)
    if len(active) > 1 and _focus_timestamp(active[0]) == _focus_timestamp(active[1]):
        raise ScopeResolutionError("ambiguous active focus sets have the same creation time")
    return active[0]


def _add_session_anchors(
    repository: RecordRepository,
    session: Mapping[str, Any],
    state: _ScopeState,
) -> None:
    for kind, field in (("claim", "active_claim"), ("research_route", "active_route")):
        record_id = str(session.get(field) or "").strip()
        if record_id:
            _add_exact_primary(repository, f"{kind}:{record_id}", state)


def _add_exact_primary(
    repository: RecordRepository,
    ref: str,
    state: _ScopeState,
) -> None:
    canonical, _spec, result = _inspect_for_resolution(repository, ref, state)
    if result is not None:
        state.add_primary(canonical)


def _add_excluded(
    repository: RecordRepository,
    ref: str,
    state: _ScopeState,
) -> None:
    canonical, _spec, _result = _inspect_for_resolution(repository, ref, state)
    state.excluded_refs.append(canonical)


def _add_supporting_ref(
    repository: RecordRepository,
    ref: str,
    *,
    primary_topic_id: str,
    include_discovery: bool,
    state: _ScopeState,
) -> None:
    canonical, spec, result = _inspect_for_resolution(repository, ref, state)
    if result is None:
        return
    payload = record_payload(result)
    if spec.family == "cross_topic_relations":
        _add_bridge(
            repository,
            canonical,
            payload,
            primary_topic_id=primary_topic_id,
            include_discovery=include_discovery,
            state=state,
        )
        return
    topic_id = str(payload.get("topic_id") or "")
    if topic_id and topic_id != primary_topic_id:
        state.excluded_refs.append(canonical)
        if include_discovery:
            state.discovery_refs.append(canonical)
        return
    state.supporting_refs.append(canonical)


def _add_bridge(
    repository: RecordRepository,
    bridge_ref: str,
    bridge: Mapping[str, Any],
    *,
    primary_topic_id: str,
    include_discovery: bool,
    state: _ScopeState,
) -> None:
    status = str(bridge.get("status") or "")
    target_topic_id = str(bridge.get("target_topic_id") or "")
    source_ref = str(bridge.get("source_ref") or "")
    target_ref = str(bridge.get("target_ref") or "")
    if status not in SUPPORTING_BRIDGE_STATUSES or target_topic_id != primary_topic_id:
        state.excluded_refs.append(bridge_ref)
        if include_discovery:
            state.discovery_refs.append(bridge_ref)
        if status == "pending_target" and target_ref:
            _inspect_for_resolution(repository, target_ref, state)
        return
    source_canonical, _source_spec, source_result = _inspect_for_resolution(
        repository, source_ref, state
    )
    target_canonical, _target_spec, target_result = _inspect_for_resolution(
        repository, target_ref, state
    )
    if source_result is None or target_result is None:
        state.excluded_refs.append(bridge_ref)
        return
    state.supporting_refs.extend([bridge_ref, source_canonical])
    state.requires_revalidation_refs.extend([bridge_ref, source_canonical])
    source_topic_id = str(bridge.get("source_topic_id") or "")
    if source_topic_id:
        state.supporting_topic_ids.append(source_topic_id)
    if target_canonical not in state.primary_refs:
        state.primary_refs.append(target_canonical)


def _add_program_scope(
    repository: RecordRepository,
    program_id: str,
    *,
    primary_topic_id: str,
    state: _ScopeState,
    supporting_topic_ids: list[str],
) -> None:
    program_ref = f"research_program:{program_id}"
    canonical, spec, result = _inspect_for_resolution(repository, program_ref, state)
    if result is None or spec.family != "research_programs":
        raise ScopeResolutionError(f"program is unavailable: {program_ref}")
    program = record_payload(result)
    if program.get("review_status") not in SCOPED_PROGRAM_REVIEW_STATUSES:
        raise ScopeResolutionError("program is not reviewed or approved for session scope")
    if primary_topic_id not in program.get("primary_topic_ids", []):
        raise ScopeResolutionError("session primary topic is outside the selected program")
    state.primary_refs.append(canonical)
    for topic_id in program.get("supporting_topic_ids", []):
        topic_ref = f"topic:{topic_id}"
        topic_canonical, _topic_spec, topic_result = _inspect_for_resolution(
            repository, topic_ref, state
        )
        if topic_result is not None:
            supporting_topic_ids.append(str(topic_id))
            state.supporting_refs.append(topic_canonical)


def _inspect_for_resolution(
    repository: RecordRepository,
    ref: str,
    state: _ScopeState,
) -> tuple[str, Any, Any | None]:
    try:
        canonical, spec, _record_id = canonical_typed_ref(ref)
    except ValueError as exc:
        state.read_errors.append(str(exc))
        return str(ref), None, None
    state.check(canonical)
    result = repository.read(canonical)
    if result.status == "found" and result.record is not None:
        return canonical, spec, result
    state.unresolved_refs.append(canonical)
    if result.status not in {"not_found"}:
        detail = result.issue.message if result.issue else result.status
        state.read_errors.append(f"{canonical}: {detail}")
    return canonical, spec, None


def _unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _focus_timestamp(record: SessionFocusSetRecord) -> float:
    try:
        return datetime.fromisoformat(
            record.created_at.replace("Z", "+00:00")
        ).timestamp()
    except ValueError as exc:
        raise ScopeResolutionError(
            f"focus set has invalid created_at: {record.focus_set_id}"
        ) from exc
