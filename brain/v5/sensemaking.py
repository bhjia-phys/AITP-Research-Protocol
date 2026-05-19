"""Local sense-making report records for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import SensemakingReportRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


def record_sensemaking_report(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    title: str,
    summary: str,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    open_questions: list[str] | None = None,
    next_actions: list[str] | None = None,
    validation_status: str = "not_validation",
) -> SensemakingReportRecord:
    report_id = prefixed_id("sensemaking-report", f"{topic_id}:{claim_id}:{title}", max_slug=64)
    record = SensemakingReportRecord(
        report_id=report_id,
        topic_id=topic_id,
        claim_id=claim_id,
        title=title,
        summary=summary,
        object_ids=object_ids or [],
        relation_ids=relation_ids or [],
        evidence_refs=evidence_refs or [],
        open_questions=open_questions or [],
        next_actions=next_actions or [],
        validation_status=validation_status,
    )
    write_record(
        ws.registry_dir("sensemaking_reports") / f"{report_id}.md",
        record,
        body=f"# Sense-Making Report: {title}\n\n{summary}\n",
    )
    return record
