"""Evidence and artifact records for AITP v5."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.evidence_basis_policy import audit_evidence_basis
from brain.v5.evidence_support_policy import pinned_record_ids
from brain.v5.models import ArtifactRecord, EvidenceRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, pin_current_record
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
    support_basis_refs: list[PinnedRecordRef] | None = None,
    trace_context_refs: list[PinnedRecordRef] | None = None,
    body: str | None = None,
) -> EvidenceRecord:
    """Record claim-local evidence that may satisfy action-budget outputs."""

    if support_basis_refs is None:
        inferred_refs = [
            *[
                ref for ref in source_refs or []
                if ref.startswith(("source_asset:", "reference_location:"))
            ],
            *[f"tool_run:{run_id}" for run_id in tool_run_ids or []],
            *[
                f"validation_result:{result_id}"
                for result_id in validation_result_ids or []
            ],
            *[f"artifact:{artifact_id}" for artifact_id in artifact_ids or []],
        ]
        if inferred_refs:
            support_basis_refs = [pin_current_record(ws, ref) for ref in inferred_refs]
            trace_context_refs = trace_context_refs or []
    support_pins = support_basis_refs or []
    pinned_sources = [
        pin.record_ref
        for pin in support_pins
        if pin.record_ref.startswith(("source_asset:", "reference_location:"))
    ]
    source_refs = _merge_unique(source_refs or [], pinned_sources)
    tool_run_ids = _merge_unique(
        tool_run_ids or [], pinned_record_ids(support_pins, "tool_run")
    )
    validation_result_ids = _merge_unique(
        validation_result_ids or [], pinned_record_ids(support_pins, "validation_result")
    )
    artifact_ids = _merge_unique(
        artifact_ids or [], pinned_record_ids(support_pins, "artifact")
    )
    policy_payload = {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "evidence_type": evidence_type,
        "status": status,
        "summary": summary,
        "supports_outputs": supports_outputs or [],
        "source_refs": source_refs,
        "tool_run_ids": tool_run_ids,
        "validation_result_ids": validation_result_ids,
        "artifact_ids": artifact_ids,
    }
    basis_audit = None
    if support_basis_refs is not None or trace_context_refs is not None:
        basis_audit = audit_evidence_basis(
            ws,
            topic_id=topic_id,
            support_basis_refs=tuple(support_basis_refs or ()),
            trace_context_refs=tuple(trace_context_refs or ()),
            evidence_payload=policy_payload,
        )
        if not basis_audit.admissible:
            raise ValueError("inadmissible evidence basis: " + ", ".join(basis_audit.errors))
    identity_payload = {
        **policy_payload,
        "support_basis_refs": [asdict(pin) for pin in support_basis_refs or ()],
        "trace_context_refs": [asdict(pin) for pin in trace_context_refs or ()],
        "basis_payload_hash": basis_audit.payload_hash if basis_audit else "",
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
        source_refs=source_refs,
        tool_run_ids=tool_run_ids,
        validation_result_ids=validation_result_ids,
        artifact_ids=artifact_ids,
        support_basis_refs=[asdict(pin) for pin in support_basis_refs or ()],
        trace_context_refs=[asdict(pin) for pin in trace_context_refs or ()],
        basis_audit=asdict(basis_audit) if basis_audit else {},
        basis_policy_status="admissible" if basis_audit else "legacy_unchecked",
        basis_payload_hash=basis_audit.payload_hash if basis_audit else "",
        basis_policy_version=basis_audit.policy_version if basis_audit else "",
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


def _merge_unique(first: list[str], second: list[str]) -> list[str]:
    return list(dict.fromkeys([*first, *second]))


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
