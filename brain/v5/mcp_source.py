"""MCP wrappers for source reconstruction surfaces."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.source_stack_coverage import build_source_stack_coverage_manifest
from brain.v5.source_reconstruction_obsidian import write_source_reconstruction_obsidian_view
from brain.v5.source_reconstruction import (
    audit_source_reconstruction,
    build_source_reconstruction_manifest,
    build_source_reconstruction_review_packet,
)
from brain.v5.source_reconstruction_review import (
    build_source_reconstruction_review_manifest,
    record_source_reconstruction_review_result,
)
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(resolve_workspace_base(base))


def aitp_v5_audit_source_reconstruction(base: str, *, claim_id: str) -> dict:
    result = audit_source_reconstruction(_ws(base), claim_id=claim_id)
    return require_valid_public_surface("source_reconstruction_audit", result)


def aitp_v5_build_source_reconstruction_manifest(base: str) -> dict:
    result = build_source_reconstruction_manifest(_ws(base))
    return {"ok": True, **require_valid_public_surface("source_reconstruction_manifest", result)}


def aitp_v5_build_source_stack_coverage_manifest(base: str) -> dict:
    result = build_source_stack_coverage_manifest(_ws(base))
    return {"ok": True, **require_valid_public_surface("source_stack_coverage_manifest", result)}


def aitp_v5_build_source_reconstruction_review_manifest(base: str) -> dict:
    result = build_source_reconstruction_review_manifest(_ws(base))
    return require_valid_public_surface("source_reconstruction_review_manifest", result)


def aitp_v5_write_source_reconstruction_obsidian_view(base: str, *, output_dir: str = "") -> dict:
    result = write_source_reconstruction_obsidian_view(_ws(base), output_dir=output_dir)
    return require_valid_public_surface("source_reconstruction_obsidian_view_bundle", result)


def aitp_v5_build_source_reconstruction_review_packet(base: str, *, claim_id: str) -> dict:
    result = build_source_reconstruction_review_packet(_ws(base), claim_id=claim_id)
    return require_valid_public_surface("source_reconstruction_review_packet", result)


def aitp_v5_record_source_reconstruction_review_result(
    base: str,
    *,
    claim_id: str,
    status: str,
    reviewed_components: list[str] | None = None,
    basis_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    remaining_actions: list[str] | None = None,
    reviewer_role: str = "human_or_adversarial_reviewer",
    summary: str = "",
) -> dict:
    result = record_source_reconstruction_review_result(
        _ws(base),
        claim_id=claim_id,
        status=status,
        reviewed_components=reviewed_components,
        basis_refs=basis_refs,
        evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids,
        reference_location_ids=reference_location_ids,
        object_ids=object_ids,
        relation_ids=relation_ids,
        remaining_actions=remaining_actions,
        reviewer_role=reviewer_role,
        summary=summary,
    )
    return require_valid_public_surface("source_reconstruction_review_result_record", {"ok": True, **asdict(result)})
