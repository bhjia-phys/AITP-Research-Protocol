"""Full-surface MCP wrappers for generic Harness Feedback cases."""

from __future__ import annotations

import json
from typing import Any, Mapping

from brain.v5.harness_feedback_case_contracts import HarnessFeedbackCaseRequest
from brain.v5.harness_feedback_cases import (
    build_harness_feedback_review_view,
    harness_feedback_case_write_payload,
    record_harness_feedback_case,
)
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor


def aitp_v5_record_harness_feedback_case(
    base: str,
    *,
    request_json: str,
    update_mode: str = "create_or_idempotent",
    expected_hash: str = "",
    actor_type: str = "model",
    actor_id: str = "aitp-harness-feedback-mcp",
    host: str = "mcp",
) -> dict[str, Any]:
    """Record one review-only problem dossier from structured observed facts."""

    payload = json.loads(request_json)
    if not isinstance(payload, Mapping):
        raise ValueError("request_json must decode to an object")
    ws = WorkspacePaths(resolve_workspace_base(base))
    result = record_harness_feedback_case(
        ws,
        HarnessFeedbackCaseRequest(**dict(payload)),
        actor=RecordActor(actor_type=actor_type, actor_id=actor_id, host=host),
        update_mode=update_mode,
        expected_hash=expected_hash,
    )
    return harness_feedback_case_write_payload(result)


def aitp_v5_build_harness_feedback_review_view(base: str) -> dict[str, Any]:
    """Return recurring feedback groups without writing optimization artifacts."""

    ws = WorkspacePaths(resolve_workspace_base(base))
    return build_harness_feedback_review_view(ws)
