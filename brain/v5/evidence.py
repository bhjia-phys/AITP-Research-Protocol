"""Evidence and artifact records for AITP v5."""

from __future__ import annotations

from dataclasses import dataclass

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import ArtifactRecord, EvidenceRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record, write_record


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
    size_bytes: int = 0,
    metadata: dict | None = None,
) -> ArtifactRecord:
    """Record a large artifact by reference, not by copying raw content."""

    suffix = short_hash(f"{topic_id}:{claim_id}:{artifact_type}:{uri}", 10)
    artifact_id = f"artifact-{artifact_type}-{suffix}"
    record = ArtifactRecord(
        artifact_id=artifact_id,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=uri,
        summary=summary,
        size_bytes=size_bytes,
        metadata=metadata or {},
    )
    write_record(
        ws.registry_dir("artifacts") / f"{artifact_id}.md",
        record,
        body=f"# Artifact\n\n{summary}\n\nURI: `{uri}`\n",
    )
    return record


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

    evidence_id = prefixed_id("evidence", f"{topic_id}:{claim_id}:{evidence_type}:{summary}", max_slug=64)
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
    write_record(
        ws.registry_dir("evidence") / f"{evidence_id}.md",
        record,
        body=body if body is not None else f"# Evidence\n\n{summary}\n",
    )
    return record


def list_evidence_for_claim(ws: WorkspacePaths, claim_id: str) -> list[EvidenceRecord]:
    """Return evidence records linked to a claim."""

    root = ws.registry_dir("evidence")
    if not root.exists():
        return []
    records: list[tuple[int, str, EvidenceRecord]] = []
    for path in root.glob("*.md"):
        try:
            evidence = read_record(path, EvidenceRecord)
        except (TypeError, ValueError):
            continue
        if evidence.claim_id == claim_id:
            records.append((path.stat().st_mtime_ns, path.name, evidence))
    return [evidence for _, _, evidence in sorted(records)]


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
