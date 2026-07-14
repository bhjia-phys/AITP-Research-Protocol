"""Runtime staging and one-review-batch persistence for research moments."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Any, Mapping

from brain.v5.lifecycle_models import RecordingCandidateBatchRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_locking import acquire_canonical_mutation_lease
from brain.v5.record_envelope import RecordActor
from brain.v5.record_path_safety import validate_record_id
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult
from brain.v5.recording_batch_contracts import (
    RecordingBatchError,
    StagedCandidate,
    StagingDiagnostic,
    StagingInventory,
    deterministic_batch_id,
    is_expired,
    normalize_staged_candidate,
    normalize_timestamp,
)
from brain.v5.recording_batch_storage import (
    inspect_recording_staging,
    load_candidate_if_present as _load_if_present,
    load_required_candidate as _load_required,
    path_for_key as _path_for_key,
    recording_batch_receipt_path,
    recording_staging_dir,
    recording_staging_history_dir,
    recording_staging_path,
    write_candidate as _write_candidate,
    write_recording_batch_receipt as _write_receipt,
)
from brain.v5.research_scope_contracts import record_payload


def stage_recording_candidate(
    ws: WorkspacePaths,
    candidate: StagedCandidate,
) -> StagedCandidate:
    """Normalize and atomically stage one trust-neutral candidate."""

    with acquire_canonical_mutation_lease(ws, timeout_seconds=10.0):
        repository = _repository(ws)
        _validate_session_topic(repository, candidate.session_id, candidate.topic_id)
        normalized = normalize_staged_candidate(candidate)
        _require_readable_sources(repository, normalized.source_refs)
        path = recording_staging_path(ws, normalized)
        existing = _load_if_present(path)
        if existing is not None:
            normalized = normalize_staged_candidate(candidate, existing=existing)
            if normalized.staging_id == existing.staging_id:
                return existing
            archived = replace(existing, status="superseded", rejection_reason="")
            history_path = (
                recording_staging_history_dir(ws, existing.session_id)
                / f"{existing.staging_id}.json"
            )
            _write_candidate(history_path, archived)
            normalized = replace(
                normalized,
                supersedes=tuple(dict.fromkeys((*normalized.supersedes, existing.staging_id))),
                status="staged",
                rejection_reason="",
            )
        _write_candidate(path, normalized)
        return normalized


def reject_recording_candidate(
    ws: WorkspacePaths,
    session_id: str,
    dedup_key: str,
    *,
    reason: str,
) -> StagedCandidate:
    """Reject one current runtime candidate without creating canonical memory."""

    reason = " ".join(str(reason or "").split())
    if not reason:
        raise ValueError("rejection reason must be non-empty")
    with acquire_canonical_mutation_lease(ws, timeout_seconds=10.0):
        path = _path_for_key(ws, session_id, dedup_key)
        candidate = _load_required(path)
        if candidate.status in {"included", "superseded"}:
            raise RecordingBatchError(f"cannot reject candidate in status {candidate.status}")
        updated = replace(candidate, status="rejected", rejection_reason=reason)
        _write_candidate(path, updated)
        return updated


def resume_recording_candidate(
    ws: WorkspacePaths,
    session_id: str,
    dedup_key: str,
    *,
    expires_at: str,
) -> StagedCandidate:
    """Return a rejected or expired candidate to the pending runtime queue."""

    normalized_expiry = normalize_timestamp(expires_at, "expires_at")
    if datetime.fromisoformat(normalized_expiry) <= datetime.now(timezone.utc):
        raise ValueError("resumed candidate expires_at must be in the future")
    with acquire_canonical_mutation_lease(ws, timeout_seconds=10.0):
        path = _path_for_key(ws, session_id, dedup_key)
        candidate = _load_required(path)
        if candidate.status not in {"rejected", "expired"}:
            raise RecordingBatchError(
                f"only rejected or expired candidates can resume, got {candidate.status}"
            )
        updated = replace(
            candidate,
            status="staged",
            expires_at=normalized_expiry,
            rejection_reason="",
        )
        _write_candidate(path, updated)
        return updated


def coalesce_recording_batch(
    ws: WorkspacePaths,
    session_id: str,
    milestone_id: str,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Persist at most one canonical, human-reviewable batch per milestone."""

    validate_record_id(session_id)
    validate_record_id(milestone_id)
    with acquire_canonical_mutation_lease(ws, timeout_seconds=10.0):
        repository = RecordRepository(ws, actor=actor)
        topic_id = _session_topic(repository, session_id)
        inventory = inspect_recording_staging(ws, session_id)
        batch_id = deterministic_batch_id(session_id, milestone_id)
        existing = repository.read(f"recording_candidate_batch:{batch_id}")
        if existing.status not in {"found", "not_found"}:
            raise RecordingBatchError(
                f"cannot inspect deterministic recording batch: {existing.status}"
            )

        corrupt_files = [item.path for item in inventory.corrupt]

        if existing.status == "found":
            if existing.record is None:
                raise RecordingBatchError("deterministic recording batch is unreadable")
            record = existing.record
            if (
                record.session_id != session_id
                or record.topic_id != topic_id
                or record.milestone_id != milestone_id
            ):
                raise RecordingBatchError("deterministic recording batch scope mismatch")
            included_ids = _batch_staging_ids(record)
            reconciled = _reconcile_existing_inclusions(
                ws,
                inventory.candidates,
                included_ids,
            )
            eligible, rejected, expired, deferred = _classify_candidates(
                repository,
                reconciled,
            )
            _persist_expired(ws, expired)
            deferred_ids = sorted(
                {item.staging_id for item in (*eligible, *deferred)}
            )
            result = repository.write(
                "recording_candidate_batches",
                record,
                body=existing.body,
                policy=WritePolicy(mode="create_or_idempotent"),
            )
            _write_receipt(
                ws,
                session_id,
                milestone_id,
                status="batch_exists",
                batch_ref=result.record_ref,
                included=included_ids,
                rejected=[item.staging_id for item in rejected],
                expired=[item.staging_id for item in expired],
                deferred=deferred_ids,
                corrupt_files=corrupt_files,
            )
            return result

        eligible, rejected, expired, deferred = _classify_candidates(
            repository,
            inventory.candidates,
        )
        _persist_expired(ws, expired)
        if not eligible:
            _write_receipt(
                ws,
                session_id,
                milestone_id,
                status="no_eligible_candidates",
                batch_ref="",
                included=[],
                rejected=[item.staging_id for item in rejected],
                expired=[item.staging_id for item in expired],
                deferred=[item.staging_id for item in deferred],
                corrupt_files=corrupt_files,
            )
            raise RecordingBatchError("no eligible staged candidates for recording batch")

        ordered = sorted(
            eligible,
            key=lambda item: (item.semantic_key, item.source_refs, item.staging_id),
        )
        now = datetime.now(timezone.utc).isoformat()
        record = RecordingCandidateBatchRecord(
            batch_id=batch_id,
            session_id=session_id,
            topic_id=topic_id,
            milestone_id=milestone_id,
            candidates=[asdict(item) for item in ordered],
            dedup_keys=[item.dedup_key for item in ordered],
            source_event_refs=sorted(
                {ref for item in ordered for ref in item.source_event_refs}
            ),
            missing_prerequisites=sorted(
                {value for item in ordered for value in item.missing_prerequisites}
            ),
            status="pending_review",
            expires_at=min(item.expires_at for item in ordered),
            created_at=now,
            can_update_claim_trust=False,
        )
        result = repository.write(
            "recording_candidate_batches",
            record,
            body=_batch_body(record),
            policy=WritePolicy(mode="create_or_idempotent"),
        )
        for candidate in ordered:
            _mark_included(ws, candidate)
        _write_receipt(
            ws,
            session_id,
            milestone_id,
            status="batch_created",
            batch_ref=result.record_ref,
            included=[item.staging_id for item in ordered],
            rejected=[item.staging_id for item in rejected],
            expired=[item.staging_id for item in expired],
            deferred=[item.staging_id for item in deferred],
            corrupt_files=corrupt_files,
        )
        return result


def stage_moment_recording_candidate(
    ws: WorkspacePaths,
    *,
    decision: Mapping[str, Any],
    candidate: StagedCandidate,
) -> dict[str, Any]:
    """Quietly stage only decisions that represent durable recording moments."""

    decision_type = str(decision.get("decision_type") or "").strip()
    action_kind = str(decision.get("action_kind") or "").strip()
    stageable = decision_type in {"recording", "navigate", "checkpoint"} or (
        action_kind.startswith("record") or action_kind in {"navigate", "checkpoint"}
    )
    if not stageable:
        return {
            "kind": "recording_candidate_staging",
            "status": "skipped",
            "reason": "moment_not_recordable",
            "trust_effect": "none",
            "can_update_claim_trust": False,
        }
    staged = stage_recording_candidate(ws, candidate)
    return {
        "kind": "recording_candidate_staging",
        "status": "staged",
        "staging_id": staged.staging_id,
        "dedup_key": staged.dedup_key,
        "trust_effect": "none",
        "can_update_claim_trust": False,
    }


def coalesce_closeout_recording_batch(
    ws: WorkspacePaths,
    session_id: str,
    milestone_id: str,
    *,
    actor: RecordActor,
) -> WriteResult:
    return coalesce_recording_batch(
        ws,
        session_id,
        milestone_id,
        actor=actor,
    )


def recording_batch_handoff(result: WriteResult) -> dict[str, Any]:
    return {
        "kind": "recording_batch_handoff",
        "status": result.status,
        "batch_ref": result.record_ref,
        "review_status": "pending_review",
        "human_review_required": True,
        "can_update_claim_trust": False,
    }


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="recording-staging-read",
            host="recording-batches",
        ),
    )


def _validate_session_topic(
    repository: RecordRepository,
    session_id: str,
    topic_id: str,
) -> None:
    actual = _session_topic(repository, validate_record_id(session_id))
    validate_record_id(topic_id)
    if actual != topic_id:
        raise RecordingBatchError("candidate topic does not match session topic")


def _session_topic(repository: RecordRepository, session_id: str) -> str:
    result = repository.read(f"session:{session_id}")
    if result.status != "found" or result.record is None:
        raise RecordingBatchError(f"session is not readable: {session_id}")
    topic_id = str(record_payload(result).get("topic_id") or "").strip()
    if not topic_id:
        raise RecordingBatchError("session binding has no topic_id")
    topic = repository.read(f"topic:{topic_id}")
    if topic.status != "found" or topic.record is None:
        raise RecordingBatchError(f"session topic is not readable: {topic_id}")
    return topic_id


def _require_readable_sources(
    repository: RecordRepository,
    source_refs: tuple[str, ...],
) -> None:
    for ref in source_refs:
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            raise RecordingBatchError(f"source ref is not readable: {ref} ({result.status})")


def _classify_candidates(
    repository: RecordRepository,
    candidates: tuple[StagedCandidate, ...],
) -> tuple[
    list[StagedCandidate],
    list[StagedCandidate],
    list[StagedCandidate],
    list[StagedCandidate],
]:
    eligible: list[StagedCandidate] = []
    rejected: list[StagedCandidate] = []
    expired: list[StagedCandidate] = []
    deferred: list[StagedCandidate] = []
    for candidate in candidates:
        if candidate.status == "rejected":
            rejected.append(candidate)
        elif candidate.status == "expired" or (
            candidate.status == "staged" and is_expired(candidate)
        ):
            expired.append(candidate)
        elif candidate.status in {"included", "superseded"}:
            continue
        elif candidate.status != "staged":
            deferred.append(candidate)
        else:
            try:
                _require_readable_sources(repository, candidate.source_refs)
            except RecordingBatchError:
                deferred.append(candidate)
            else:
                eligible.append(candidate)
    return eligible, rejected, expired, deferred


def _persist_expired(ws: WorkspacePaths, candidates: list[StagedCandidate]) -> None:
    for candidate in candidates:
        if candidate.status == "staged":
            _write_candidate(
                recording_staging_path(ws, candidate),
                replace(candidate, status="expired"),
            )


def _mark_included(ws: WorkspacePaths, candidate: StagedCandidate) -> None:
    path = recording_staging_path(ws, candidate)
    current = _load_required(path)
    if current.staging_id != candidate.staging_id or current.status != "staged":
        raise RecordingBatchError("staged candidate changed during batch coalescing")
    _write_candidate(path, replace(current, status="included"))


def _reconcile_existing_inclusions(
    ws: WorkspacePaths,
    candidates: tuple[StagedCandidate, ...],
    included_ids: list[str],
) -> tuple[StagedCandidate, ...]:
    included = set(included_ids)
    reconciled: list[StagedCandidate] = []
    for candidate in candidates:
        if candidate.staging_id in included and candidate.status != "included":
            candidate = replace(
                candidate,
                status="included",
                rejection_reason="",
            )
            _write_candidate(recording_staging_path(ws, candidate), candidate)
        reconciled.append(candidate)
    return tuple(reconciled)


def _batch_staging_ids(record: RecordingCandidateBatchRecord) -> list[str]:
    return sorted(
        {
            str(item.get("staging_id") or "")
            for item in record.candidates
            if isinstance(item, Mapping) and str(item.get("staging_id") or "")
        }
    )


def _batch_body(record: RecordingCandidateBatchRecord) -> str:
    lines = [f"# Recording Candidate Batch: {record.batch_id}", ""]
    lines.extend(
        f"- `{item.get('candidate_kind')}`: {item.get('summary')}"
        for item in record.candidates
    )
    return "\n".join(lines) + "\n"


__all__ = [
    "RecordingBatchError",
    "StagedCandidate",
    "StagingDiagnostic",
    "StagingInventory",
    "coalesce_closeout_recording_batch",
    "coalesce_recording_batch",
    "inspect_recording_staging",
    "recording_batch_handoff",
    "recording_batch_receipt_path",
    "recording_staging_dir",
    "recording_staging_history_dir",
    "recording_staging_path",
    "reject_recording_candidate",
    "resume_recording_candidate",
    "stage_moment_recording_candidate",
    "stage_recording_candidate",
]
