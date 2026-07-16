"""MCP-facing evidence wrappers for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.evidence import record_evidence
from brain.v5.evidence_basis_inputs import coerce_pinned_record_refs
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_record_evidence(
    base: str, *, topic_id: str, claim_id: str, evidence_type: str, status: str,
    summary: str, supports_outputs: list[str] | None = None, source_refs: list[str] | None = None,
    tool_run_ids: list[str] | None = None, validation_result_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    support_basis_refs: list[dict] | None = None,
    trace_context_refs: list[dict] | None = None,
    body: str | None = None,
) -> dict:
    evidence = record_evidence(init_workspace(Path(base)), topic_id=topic_id, claim_id=claim_id,
        evidence_type=evidence_type, status=status, summary=summary,
        supports_outputs=supports_outputs, source_refs=source_refs,
        tool_run_ids=tool_run_ids, validation_result_ids=validation_result_ids,
        artifact_ids=artifact_ids,
        support_basis_refs=coerce_pinned_record_refs(
            support_basis_refs, field_name="support_basis_refs"
        ),
        trace_context_refs=coerce_pinned_record_refs(
            trace_context_refs, field_name="trace_context_refs"
        ),
        body=body)
    return require_valid_public_surface("evidence_record", {"ok": True, **asdict(evidence)})
