"""Full MCP wrappers for the v5 research-session lifecycle."""

from __future__ import annotations

from typing import Any

from brain.v5.lifecycle_facade import (
    apply_session_closeout,
    coalesce_candidate_batch,
    persist_recall_audit,
    plan_session_closeout,
    stage_candidate,
    start_session,
)
from brain.v5.public_surfaces import require_valid_public_surface


def aitp_v5_session_start(base: str, *, session_id: str) -> dict[str, Any]:
    return require_valid_public_surface(
        "session_start_boundary",
        start_session(base, session_id),
    )


def aitp_v5_run_recall_audit(
    base: str,
    *,
    request: dict[str, Any],
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return require_valid_public_surface(
        "recall_audit_result",
        persist_recall_audit(base, request, actor=actor),
    )


def aitp_v5_stage_recording_candidate(
    base: str,
    *,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return require_valid_public_surface(
        "recording_candidate_staging",
        stage_candidate(base, candidate),
    )


def aitp_v5_coalesce_recording_batch(
    base: str,
    *,
    session_id: str,
    milestone_id: str,
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return require_valid_public_surface(
        "recording_batch_handoff",
        coalesce_candidate_batch(
            base,
            session_id,
            milestone_id,
            actor=actor,
        ),
    )


def aitp_v5_plan_session_closeout(
    base: str,
    *,
    request: dict[str, Any],
) -> dict[str, Any]:
    return require_valid_public_surface(
        "session_closeout_plan",
        plan_session_closeout(base, request),
    )


def aitp_v5_apply_session_closeout(
    base: str,
    *,
    plan: dict[str, Any],
    plan_id: str,
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return require_valid_public_surface(
        "session_closeout_apply",
        apply_session_closeout(base, plan, plan_id, actor=actor),
    )
