"""Evidence and artifact records for AITP v5."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import ArtifactRecord, EvidenceRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordCollisionError, RecordRepository
from brain.v5.store import read_record


@dataclass
class OutputCoverage:
    satisfied_outputs: list[str]
    missing_outputs: list[str]
    evidence_ids_by_output: dict


def record_artifact_ref(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    artifact_type: str,
    uri: str,
    summary: str,
    size_bytes: int | str | None = 0,
    metadata: dict | None = None,
) -> ArtifactRecord:
    """Record a large artifact by reference, not by copying raw content."""

    normalized_size = _normalize_size_bytes(size_bytes)
    suffix = short_hash(f"{topic_id}:{claim_id}:{artifact_type}:{uri}", 10)
    artifact_id = f"artifact-{artifact_type}-{suffix}"
    normalized_metadata = metadata or {}
    record = ArtifactRecord(
        artifact_id=artifact_id,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=uri,
        summary=summary,
        size_bytes=normalized_size,
        metadata=normalized_metadata,
    )
    repository = _repository(ws, actor_id="record_artifact_ref")
    current = repository.read(f"artifact:{artifact_id}")
    if current.status == "found" and isinstance(current.record, ArtifactRecord):
        _require_compatible_artifact_observation(current.record, record)
        return current.record
    try:
        repository.write(
            "artifacts",
            record,
            body=f"# Artifact\n\n{summary}\n\nURI: `{uri}`\n",
        )
    except RecordCollisionError:
        raced = repository.read(f"artifact:{artifact_id}")
        if raced.status != "found" or not isinstance(raced.record, ArtifactRecord):
            raise
        _require_compatible_artifact_observation(raced.record, record)
        return raced.record
    return record


def _require_compatible_artifact_observation(
    existing: ArtifactRecord,
    incoming: ArtifactRecord,
) -> None:
    existing_size = _normalize_size_bytes(existing.size_bytes)
    incoming_size = _normalize_size_bytes(incoming.size_bytes)
    existing_hash = str(existing.metadata.get("sha256") or "").strip().lower()
    incoming_hash = str(incoming.metadata.get("sha256") or "").strip().lower()
    if existing_hash and incoming_hash and existing_hash != incoming_hash:
        raise ValueError(
            f"artifact identity {existing.artifact_id} has conflicting sha256 observations"
        )
    if existing_size > 0 and incoming_size > 0 and existing_size != incoming_size:
        raise ValueError(
            f"artifact identity {existing.artifact_id} has conflicting size_bytes observations"
        )


def _normalize_size_bytes(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"size_bytes must be a non-negative integer, got {value!r}") from exc
    if size < 0:
        raise ValueError(f"size_bytes must be non-negative, got {size}")
    return size


def record_evidence(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    evidence_type: str,
    status: str,
    summary: str,
    supports_outputs: list[str] | None = None,
    source_refs: list[str] | None = None,
    tool_run_ids: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    body: str | None = None,
) -> EvidenceRecord:
    """Record claim-local evidence that may satisfy action-budget outputs."""

    identity_payload = {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "evidence_type": evidence_type,
        "status": status,
        "summary": summary,
        "supports_outputs": supports_outputs or [],
        "source_refs": source_refs or [],
        "tool_run_ids": tool_run_ids or [],
        "validation_result_ids": validation_result_ids or [],
        "artifact_ids": artifact_ids or [],
        "body": body or "",
    }
    identity_hash = hashlib.sha256(
        json.dumps(
            identity_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:12]
    evidence_id = prefixed_id(
        "evidence",
        f"{topic_id}:{claim_id}:{evidence_type}:{summary}:{identity_hash}",
        max_slug=64,
    )
    record = EvidenceRecord(
        evidence_id=evidence_id,
        topic_id=topic_id,
        claim_id=claim_id,
        evidence_type=evidence_type,
        status=status,
        summary=summary,
        supports_outputs=supports_outputs or [],
        source_refs=source_refs or [],
        tool_run_ids=tool_run_ids or [],
        validation_result_ids=validation_result_ids or [],
        artifact_ids=artifact_ids or [],
    )
    _repository(ws, actor_id="record_evidence").write(
        "evidence",
        record,
        body=body if body is not None else f"# Evidence\n\n{summary}\n",
    )
    return record


def list_evidence_for_claim(ws: WorkspacePaths, claim_id: str) -> list[EvidenceRecord]:
    """Return claim evidence, failing visibly on malformed canonical records."""

    root = ws.registry_dir("evidence")
    if not root.exists():
        return []
    records: list[tuple[int, str, EvidenceRecord]] = []
    for path in root.glob("*.md"):
        evidence = read_record(path, EvidenceRecord)
        if evidence.claim_id == claim_id:
            records.append((path.stat().st_mtime_ns, path.name, evidence))
    return [evidence for _, _, evidence in sorted(records)]


def _repository(ws: WorkspacePaths, *, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp"),
    )


def required_output_coverage(
    evidence_records: list[EvidenceRecord],
    *,
    required_outputs: list[str],
) -> OutputCoverage:
    """Map evidence records onto required and observed evidence outputs."""

    evidence_ids_by_output: dict[str, list[str]] = {output: [] for output in required_outputs}
    for evidence in evidence_records:
        if evidence.status in {"failed", "refutes", "invalid"}:
            continue
        for output in evidence.supports_outputs:
            evidence_ids_by_output.setdefault(output, []).append(evidence.evidence_id)

    satisfied = [output for output, evidence_ids in evidence_ids_by_output.items() if evidence_ids]
    missing = [output for output in required_outputs if not evidence_ids_by_output[output]]
    return OutputCoverage(
        satisfied_outputs=satisfied,
        missing_outputs=missing,
        evidence_ids_by_output=evidence_ids_by_output,
    )
