"""Compatibility monitor helpers and generic Harness Feedback exports."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.harness_feedback_case_contracts import HarnessFeedbackCaseRequest
from brain.v5.harness_feedback_cases import (
    HarnessFeedbackCaseConflict,
    build_harness_feedback_review_view,
    harness_feedback_case_write_payload,
    record_harness_feedback_case,
    render_harness_feedback_case,
)
from brain.v5.models import MonitorSnapshotRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


def record_monitor_snapshot(ws: WorkspacePaths, **kwargs: Any) -> MonitorSnapshotRecord:
    """Compatibility writer for the pre-v2 monitor snapshot surface."""

    record = MonitorSnapshotRecord(**kwargs)
    record.claim_trust_mutation = "none"
    record.summary_inputs_trusted = False
    record.orientation_only = True
    record.can_update_claim_trust = False
    write_record(
        ws.registry_dir("monitor_snapshots") / f"{record.snapshot_id}.md",
        record,
        body=f"# Monitor Snapshot\n\n{record.interpretation_boundary}\n",
    )
    return record


def monitor_snapshot_payload(record: MonitorSnapshotRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


__all__ = [
    "HarnessFeedbackCaseConflict",
    "HarnessFeedbackCaseRequest",
    "build_harness_feedback_review_view",
    "harness_feedback_case_write_payload",
    "monitor_snapshot_payload",
    "record_harness_feedback_case",
    "record_monitor_snapshot",
    "render_harness_feedback_case",
]
