"""MCP-facing L2 memory audit wrappers for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.failure_mode_audit import audit_failure_mode_coverage
from brain.v5.failure_mode_review import build_failure_mode_review_packet, record_failure_mode_review_result, request_failure_mode_review_checkpoint
from brain.v5.memory_audit import audit_l2_memory_context
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_audit_l2_memory_context(base: str, *, claim_id: str) -> dict:
    payload = audit_l2_memory_context(init_workspace(Path(base)), claim_id=claim_id)
    return require_valid_public_surface("l2_memory_audit", payload)


def aitp_v5_audit_failure_mode_coverage(base: str, *, claim_id: str) -> dict:
    payload = audit_failure_mode_coverage(init_workspace(Path(base)), claim_id=claim_id)
    return require_valid_public_surface("failure_mode_audit", payload)


def aitp_v5_build_failure_mode_review_packet(base: str, *, claim_id: str) -> dict:
    payload = build_failure_mode_review_packet(init_workspace(Path(base)), claim_id=claim_id)
    return require_valid_public_surface("failure_mode_review_packet", payload)


def aitp_v5_request_failure_mode_review_checkpoint(base: str, *, claim_id: str) -> dict:
    checkpoint = request_failure_mode_review_checkpoint(init_workspace(Path(base)), claim_id=claim_id)
    return require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(checkpoint)})


def aitp_v5_record_failure_mode_review_result(
    base: str,
    *,
    claim_id: str,
    checkpoint_id: str,
    status: str,
    reviewed_failure_modes: list[str] | None = None,
    basis_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    tool_run_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    reviewer_role: str = "adversarial_reviewer",
    summary: str = "",
) -> dict:
    result = record_failure_mode_review_result(
        init_workspace(Path(base)),
        claim_id=claim_id,
        checkpoint_id=checkpoint_id,
        status=status,
        reviewed_failure_modes=reviewed_failure_modes,
        basis_refs=basis_refs,
        evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids,
        tool_run_ids=tool_run_ids,
        reference_location_ids=reference_location_ids,
        artifact_ids=artifact_ids,
        reviewer_role=reviewer_role,
        summary=summary,
    )
    return require_valid_public_surface("failure_mode_review_result_record", {"ok": True, **asdict(result)})
