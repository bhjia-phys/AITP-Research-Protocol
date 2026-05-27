"""MCP wrappers for topic-local operator checkpoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.operator_checkpoint import answer_operator_checkpoint, request_operator_checkpoint
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_request_operator_checkpoint(
    base: str, *, topic_id: str, checkpoint_kind: str, question: str,
    options: list[str], requested_by: str, claim_id: str = "",
    human_checkpoint_id: str = "", source_refs: list[str] | None = None,
) -> dict:
    checkpoint = request_operator_checkpoint(
        _ws(base),
        topic_id=topic_id,
        checkpoint_kind=checkpoint_kind,
        question=question,
        options=options,
        requested_by=requested_by,
        claim_id=claim_id,
        human_checkpoint_id=human_checkpoint_id,
        source_refs=source_refs,
    )
    return require_valid_public_surface("operator_checkpoint_record", {"ok": True, **asdict(checkpoint)})


def aitp_v5_answer_operator_checkpoint(
    base: str, *, topic_id: str, checkpoint_id: str, selected_option: str = "",
    rationale: str, answered_by: str, status: str = "answered",
) -> dict:
    checkpoint = answer_operator_checkpoint(
        _ws(base),
        topic_id=topic_id,
        checkpoint_id=checkpoint_id,
        selected_option=selected_option,
        rationale=rationale,
        answered_by=answered_by,
        status=status,
    )
    return require_valid_public_surface("operator_checkpoint_record", {"ok": True, **asdict(checkpoint)})
