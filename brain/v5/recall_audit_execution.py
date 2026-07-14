"""Internal ordered retrieval and aggregation for canonical recall audits."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from brain.v5.lifecycle_models import RecallAuditRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_snapshot import load_effective_query_index, scoped_index_freshness
from brain.v5.recall_audit_contracts import deterministic_audit_id
from brain.v5.record_repository import RecordRepository
from brain.v5.research_retrieval import ResearchQuery, RetrievalResult, query_records
from brain.v5.research_scope import ScopeResolution
from brain.v5.research_scope_contracts import canonical_typed_ref
from brain.v5.session_lifecycle_contracts import retrieval_scope_token


def run_ordered_lanes(
    ws: WorkspacePaths,
    request: Any,
    scope: ScopeResolution,
    assignments: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    lane_specs = [
        (
            "primary",
            (scope.primary_topic_id,),
            (),
            assignments["primary"],
            False,
            tuple(scope.primary_refs),
        )
    ]
    if request.include_program_scope:
        lane_specs.append(
            (
                "program_shared",
                tuple(scope.supporting_topic_ids),
                (scope.program_id,) if scope.program_id else (),
                tuple(dict.fromkeys([*scope.supporting_refs, *assignments["program_shared"]])),
                False,
                tuple(scope.supporting_refs),
            )
        )
    if request.include_discovery:
        lane_specs.append(
            (
                "discovery",
                (),
                (),
                tuple(dict.fromkeys([*scope.discovery_refs, *assignments["discovery"]])),
                True,
                tuple(scope.discovery_refs),
            )
        )
    lanes: list[dict[str, Any]] = []
    for order, (name, topic_ids, program_ids, exact_refs, exact_only, scope_refs) in enumerate(
        lane_specs
    ):
        result = query_records(
            ws,
            ResearchQuery(
                text=request.query_text,
                exact_refs=exact_refs,
                topic_ids=topic_ids,
                program_ids=program_ids,
                families=tuple(sorted(set(request.required_families))),
                limit=request.top_k,
                verification_mode="strong",
                exact_only=exact_only,
            ),
        )
        lanes.append(
            _lane_payload(
                name=name,
                order=order,
                scope_refs=scope_refs,
                topic_ids=topic_ids,
                program_ids=program_ids,
                exact_refs=exact_refs,
                exact_only=exact_only,
                required_families=request.required_families,
                result=result,
            )
        )
    return lanes


def _lane_payload(
    *,
    name: str,
    order: int,
    scope_refs: tuple[str, ...],
    topic_ids: tuple[str, ...],
    program_ids: tuple[str, ...],
    exact_refs: tuple[str, ...],
    exact_only: bool,
    required_families: tuple[str, ...],
    result: RetrievalResult,
) -> dict[str, Any]:
    coverage = result.coverage
    self_blocked = "recall_audits" in coverage.checked_families
    read_errors = list(coverage.read_errors)
    stale = bool(
        result.index_status != "fresh"
        or not coverage.scope_state_fresh
        or not coverage.scope_content_verified
        or coverage.dirty_families
        or read_errors
    )
    content_verified = bool(coverage.scope_content_verified and not read_errors)
    exhaustive = bool(
        coverage.exhaustive
        and content_verified
        and not result.truncated
        and not result.excluded_candidates
        and not self_blocked
    )
    checked = list(coverage.checked_families)
    return {
        "lane": name,
        "order": order,
        "scope_refs": list(scope_refs),
        "topic_ids": list(topic_ids),
        "program_ids": list(program_ids),
        "requested_exact_refs": list(exact_refs),
        "exact_only": exact_only,
        "checked_families": checked,
        "unchecked_families": sorted(set(required_families) - set(checked)),
        "records_read": len(result.items),
        "total_count": result.total_count,
        "top_refs": [item.record_ref for item in result.items],
        "excluded_candidates": list(result.excluded_candidates),
        "dirty_families": list(coverage.dirty_families),
        "read_errors": read_errors,
        "results": [
            {
                "record_ref": item.record_ref,
                "family": item.family,
                "topic_id": item.topic_id,
                "exact_score": item.exact_score,
                "lexical_score": item.lexical_score,
                "total_score": item.total_score,
            }
            for item in result.items
        ],
        "index_status": result.index_status,
        "index_generation": result.index_generation,
        "malformed_count": coverage.malformed_count,
        "content_verified": content_verified,
        "exhaustive": exhaustive,
        "stale": stale,
        "truncated": bool(result.truncated),
        "self_certification_blocked": self_blocked,
    }


def build_audit_record(
    ws: WorkspacePaths,
    *,
    request: Any,
    scope: ScopeResolution,
    canonical_exact: tuple[str, ...],
    missing_exact: tuple[str, ...],
    lanes: list[dict[str, Any]],
) -> RecallAuditRecord:
    snapshot = load_effective_query_index(ws)
    checked = tuple(
        sorted(
            {
                family
                for lane in lanes
                for family in lane["checked_families"]
            }
        )
    )
    unchecked = tuple(sorted(set(request.required_families) - set(checked)))
    state_tokens = {family: snapshot.family_state_tokens.get(family, "") for family in checked}
    content_watermarks = {
        family: snapshot.family_content_watermarks.get(family, "") for family in checked
    }
    dirty = tuple(
        sorted(
            set(snapshot.dirty_families).intersection(checked).union(
                family for lane in lanes for family in lane["dirty_families"]
            )
        )
    )
    top_refs = tuple(
        list(
            dict.fromkeys(
                ref for lane in lanes for ref in lane["top_refs"]
            )
        )[: request.top_k]
    )
    lane_excluded = [
        ref for lane in lanes for ref in lane["excluded_candidates"]
    ]
    visible_discovery = set(scope.discovery_refs) if request.include_discovery else set()
    excluded = tuple(
        dict.fromkeys(
            [
                *(ref for ref in scope.excluded_refs if ref not in visible_discovery),
                *lane_excluded,
                *missing_exact,
            ]
        )
    )
    read_errors = tuple(
        dict.fromkeys([*scope.read_errors, *(error for lane in lanes for error in lane["read_errors"])])
    )
    stale = bool(scope.read_errors or dirty or any(lane["stale"] for lane in lanes))
    content_verified = bool(
        lanes
        and all(lane["content_verified"] for lane in lanes)
        and not read_errors
        and not dirty
    )
    truncated = bool(any(lane["truncated"] for lane in lanes))
    exhaustive = bool(
        content_verified
        and not stale
        and not truncated
        and not unchecked
        and not missing_exact
        and all(lane["exhaustive"] for lane in lanes)
    )
    scope_token = retrieval_scope_token(
        checked_families=checked,
        family_state_tokens=state_tokens,
        family_content_watermarks=content_watermarks,
    )
    generation = max(int(snapshot.manifest.generation), int(snapshot.delta_generation))
    audit_id = deterministic_audit_id(
        {
            "session_id": request.session_id,
            "query_text": request.query_text,
            "normalized_intent": request.normalized_intent,
            "focus_set_ref": scope.focus_set_ref,
            "required_families": sorted(set(request.required_families)),
            "required_exact_refs": canonical_exact,
            "include_program_scope": request.include_program_scope,
            "include_discovery": request.include_discovery,
            "top_k": request.top_k,
            "index_generation": generation,
            "retrieval_scope_token": scope_token,
            "top_refs": top_refs,
            "excluded_candidates": excluded,
        }
    )
    scope_refs = tuple(
        dict.fromkeys(
            [
                *scope.primary_refs,
                *(scope.supporting_refs if request.include_program_scope else ()),
                *(scope.discovery_refs if request.include_discovery else ()),
                *canonical_exact,
            ]
        )
    )
    return RecallAuditRecord(
        audit_id=audit_id,
        session_id=request.session_id,
        topic_id=scope.primary_topic_id,
        query_text=request.query_text,
        normalized_intent=request.normalized_intent,
        scope_refs=list(scope_refs),
        focus_set_ref=scope.focus_set_ref,
        program_id=scope.program_id,
        required_families=list(dict.fromkeys(request.required_families)),
        required_exact_refs=list(canonical_exact),
        missing_exact_refs=list(missing_exact),
        include_program_scope=request.include_program_scope,
        include_discovery=request.include_discovery,
        top_k=request.top_k,
        lanes=lanes,
        index_generation=generation,
        base_index_generation=int(snapshot.manifest.generation),
        delta_generation=int(snapshot.delta_generation),
        canonical_watermark=str(snapshot.manifest.canonical_watermark or ""),
        retrieval_scope_token=scope_token,
        family_state_tokens=state_tokens,
        family_content_watermarks=content_watermarks,
        dirty_families=list(dirty),
        checked_families=list(checked),
        unchecked_families=list(unchecked),
        records_read=sum(lane["records_read"] for lane in lanes),
        top_refs=list(top_refs),
        excluded_candidates=list(excluded),
        read_errors=list(read_errors),
        truncated=truncated,
        stale=stale,
        content_verified=content_verified,
        exhaustive=exhaustive,
        can_claim_no_result=bool(exhaustive and not top_refs),
        can_update_claim_trust=False,
    )


def resolve_requested_exact_refs(
    repository: RecordRepository,
    refs: Iterable[str],
) -> tuple[tuple[str, ...], dict[str, str], tuple[str, ...]]:
    canonical_refs: list[str] = []
    topics: dict[str, str] = {}
    unreadable: list[str] = []
    for ref in dict.fromkeys(refs):
        canonical, _spec, _record_id = canonical_typed_ref(ref)
        canonical_refs.append(canonical)
        result = repository.read(canonical)
        if result.status != "found" or result.record is None:
            unreadable.append(canonical)
            continue
        payload = asdict(result.record) if is_dataclass(result.record) else dict(result.record)
        topics[canonical] = str(payload.get("topic_id") or payload.get("topic") or "")
    return tuple(canonical_refs), topics, tuple(unreadable)


def assign_exact_refs(
    refs: tuple[str, ...],
    topics: dict[str, str],
    scope: ScopeResolution,
    *,
    include_program_scope: bool,
    include_discovery: bool,
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    assigned: dict[str, list[str]] = {
        "primary": [],
        "program_shared": [],
        "discovery": [],
    }
    rejected: list[str] = []
    for ref in refs:
        if ref not in topics:
            continue
        topic_id = topics[ref]
        if ref in scope.discovery_refs:
            if include_discovery:
                assigned["discovery"].append(ref)
            else:
                rejected.append(ref)
        elif ref in scope.supporting_refs or topic_id in scope.supporting_topic_ids:
            if include_program_scope:
                assigned["program_shared"].append(ref)
            else:
                rejected.append(ref)
        elif ref in scope.primary_refs or topic_id == scope.primary_topic_id:
            assigned["primary"].append(ref)
        else:
            rejected.append(ref)
    return (
        {key: tuple(dict.fromkeys(values)) for key, values in assigned.items()},
        tuple(dict.fromkeys(rejected)),
    )


def validate_after_write(ws: WorkspacePaths, record: RecallAuditRecord) -> None:
    checked = tuple(family for family in record.checked_families if family != "recall_audits")
    if not checked:
        return
    snapshot = load_effective_query_index(ws, allow_cached=False)
    if any(
        snapshot.family_state_tokens.get(family, "")
        != record.family_state_tokens.get(family, "")
        or snapshot.family_content_watermarks.get(family, "")
        != record.family_content_watermarks.get(family, "")
        for family in checked
    ):
        raise RuntimeError("checked-family index facts changed while persisting recall")
    if record.content_verified:
        freshness = scoped_index_freshness(ws, snapshot, checked)
        if (
            not freshness.scope_state_fresh
            or not freshness.scope_content_verified
            or set(freshness.dirty_families).intersection(checked)
            or freshness.diagnostics
        ):
            raise RuntimeError("persisted recall coverage failed post-write validation")
