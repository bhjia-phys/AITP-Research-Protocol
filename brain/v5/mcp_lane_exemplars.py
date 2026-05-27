"""MCP wrappers for vNext lane exemplars."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.lane_exemplars import build_lane_exemplar_manifest, record_lane_exemplar
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_record_lane_exemplar(
    base: str, *, topic_id: str, lane: str, title: str, summary: str,
    claim_id: str = "", run_id: str = "", gates_demonstrated: list[str] | None = None,
    artifact_refs: list[str] | None = None, trust_boundary: str = "",
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
        trust_boundary=trust_boundary,
        source_refs=source_refs,
        status=status,
    )
    return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})


def aitp_v5_build_lane_exemplar_manifest(base: str) -> dict:
    return require_valid_public_surface("lane_exemplar_manifest", build_lane_exemplar_manifest(_ws(base)))
