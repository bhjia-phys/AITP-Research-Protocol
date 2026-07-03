"""MCP wrappers for vNext lane exemplars."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.lane_exemplars import (
    build_lane_exemplar_manifest,
    record_lane_exemplar,
    record_librpa_code_backed_algorithm_exemplar,
    record_qft_qg_source_reconstruction_exemplar,
    record_toy_numeric_finite_size_exemplar,
)
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_record_lane_exemplar(
    base: str, *, topic_id: str, lane: str, title: str, summary: str,
    claim_id: str = "", run_id: str = "", gates_demonstrated: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    domain_pack_refs: list[str] | None = None,
    context_profile_refs: list[str] | None = None,
    skill_refs: list[str] | None = None,
    surface_refs: list[str] | None = None,
    validation_surface_refs: list[str] | None = None,
    workflow_steps: list[dict] | None = None,
    failure_modes: list[dict] | None = None,
    forbidden_uses: list[str] | None = None,
    can_say: list[str] | None = None,
    cannot_say: list[str] | None = None,
    required_next_records: list[str] | None = None,
    promotion_blockers: list[str] | None = None,
    trust_boundary: str = "",
    source_refs: list[str] | None = None, status: str = "candidate",
) -> dict:
    record = record_lane_exemplar(
        _ws(base),
        topic_id=topic_id,
        lane=lane,
        title=title,
        summary=summary,
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=gates_demonstrated,
        artifact_refs=artifact_refs,
        domain_pack_refs=domain_pack_refs,
        context_profile_refs=context_profile_refs,
        skill_refs=skill_refs,
        surface_refs=surface_refs,
        validation_surface_refs=validation_surface_refs,
        workflow_steps=workflow_steps,
        failure_modes=failure_modes,
        forbidden_uses=forbidden_uses,
        can_say=can_say,
        cannot_say=cannot_say,
        required_next_records=required_next_records,
        promotion_blockers=promotion_blockers,
        trust_boundary=trust_boundary,
        source_refs=source_refs,
        status=status,
    )
    return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})


def aitp_v5_record_librpa_code_backed_algorithm_exemplar(
    base: str,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> dict:
    record = record_librpa_code_backed_algorithm_exemplar(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        run_id=run_id,
        status=status,
    )
    return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})


def aitp_v5_record_qft_qg_source_reconstruction_exemplar(
    base: str,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> dict:
    record = record_qft_qg_source_reconstruction_exemplar(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        run_id=run_id,
        status=status,
    )
    return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})


def aitp_v5_record_toy_numeric_finite_size_exemplar(
    base: str,
    *,
    topic_id: str,
    claim_id: str = "",
    run_id: str = "",
    status: str = "accepted",
) -> dict:
    record = record_toy_numeric_finite_size_exemplar(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        run_id=run_id,
        status=status,
    )
    return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})


def aitp_v5_build_lane_exemplar_manifest(base: str) -> dict:
    return require_valid_public_surface("lane_exemplar_manifest", build_lane_exemplar_manifest(_ws(base)))
