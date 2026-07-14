"""Atomic runtime storage for trust-neutral recording candidates."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.record_path_safety import validate_record_id
from brain.v5.recording_batch_contracts import (
    RecordingBatchError,
    StagedCandidate,
    StagingDiagnostic,
    StagingInventory,
    deserialize_staged_candidate,
    serialize_staged_candidate,
)


def recording_staging_dir(ws: WorkspacePaths, session_id: str) -> Path:
    return ws.root / "runtime" / "recording_staging" / validate_record_id(session_id)


def recording_staging_history_dir(ws: WorkspacePaths, session_id: str) -> Path:
    return recording_staging_dir(ws, session_id) / "history"


def recording_staging_path(ws: WorkspacePaths, candidate: StagedCandidate) -> Path:
    validate_record_id(candidate.dedup_key)
    return recording_staging_dir(ws, candidate.session_id) / f"{candidate.dedup_key}.json"


def recording_batch_receipt_path(
    ws: WorkspacePaths,
    session_id: str,
    milestone_id: str,
) -> Path:
    validate_record_id(milestone_id)
    return recording_staging_dir(ws, session_id) / "receipts" / f"{milestone_id}.json"


def path_for_key(
    ws: WorkspacePaths,
    session_id: str,
    dedup_key: str,
) -> Path:
    validate_record_id(dedup_key)
    return recording_staging_dir(ws, session_id) / f"{dedup_key}.json"


def load_candidate_if_present(path: Path) -> StagedCandidate | None:
    if not path.exists():
        return None
    try:
        return deserialize_staged_candidate(path)
    except Exception as exc:  # noqa: BLE001 - never overwrite corrupt runtime state.
        raise RecordingBatchError(f"cannot read existing staging file {path}: {exc}") from exc


def load_required_candidate(path: Path) -> StagedCandidate:
    candidate = load_candidate_if_present(path)
    if candidate is None:
        raise RecordingBatchError(f"staged candidate does not exist: {path}")
    return candidate


def write_candidate(path: Path, candidate: StagedCandidate) -> None:
    write_text_atomic(path, serialize_staged_candidate(candidate))


def inspect_recording_staging(
    ws: WorkspacePaths,
    session_id: str,
) -> StagingInventory:
    """Read every current staging file and preserve corrupt-file diagnostics."""

    candidates: list[StagedCandidate] = []
    corrupt: list[StagingDiagnostic] = []
    directory = recording_staging_dir(ws, session_id)
    for path in sorted(directory.glob("*.json")) if directory.exists() else ():
        try:
            candidates.append(deserialize_staged_candidate(path))
        except Exception as exc:  # noqa: BLE001 - diagnostics must remain exhaustive.
            corrupt.append(
                StagingDiagnostic(
                    path=str(path),
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
    return StagingInventory(
        candidates=tuple(sorted(candidates, key=lambda item: item.dedup_key)),
        corrupt=tuple(corrupt),
    )


def write_recording_batch_receipt(
    ws: WorkspacePaths,
    session_id: str,
    milestone_id: str,
    *,
    status: str,
    batch_ref: str,
    included: list[str],
    rejected: list[str],
    expired: list[str],
    deferred: list[str],
    corrupt_files: list[str],
) -> None:
    payload = {
        "schema_version": "v1",
        "kind": "recording_batch_receipt",
        "session_id": session_id,
        "milestone_id": milestone_id,
        "status": status,
        "batch_ref": batch_ref,
        "included_staging_ids": sorted(set(included)),
        "rejected_staging_ids": sorted(set(rejected)),
        "expired_staging_ids": sorted(set(expired)),
        "deferred_staging_ids": sorted(set(deferred)),
        "corrupt_files": sorted(set(corrupt_files)),
        "trust_effect": "none",
        "can_update_claim_trust": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_text_atomic(
        recording_batch_receipt_path(ws, session_id, milestone_id),
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
