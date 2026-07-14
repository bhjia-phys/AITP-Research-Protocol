"""M1 session-lifecycle runtime entrypoints."""

from __future__ import annotations


RUNTIME_ENTRYPOINTS_03 = {
    "session_start": {
        "mcp": "aitp_v5_session_start",
        "cli": "aitp-v5 session start <session-id>",
        "surface": "session_start_boundary",
    },
    "recall_audit": {
        "mcp": "aitp_v5_run_recall_audit",
        "cli": "aitp-v5 session recall-audit --request-json <args>",
        "surface": "recall_audit_result",
    },
    "recording_stage": {
        "mcp": "aitp_v5_stage_recording_candidate",
        "cli": "aitp-v5 session recording-stage --candidate-json <args>",
        "surface": "recording_candidate_staging",
    },
    "recording_batch": {
        "mcp": "aitp_v5_coalesce_recording_batch",
        "cli": "aitp-v5 session recording-batch <session-id> <args>",
        "surface": "recording_batch_handoff",
    },
    "session_closeout_plan": {
        "mcp": "aitp_v5_plan_session_closeout",
        "cli": "aitp-v5 session closeout-plan --request-json <args>",
        "surface": "session_closeout_plan",
    },
    "session_closeout_apply": {
        "mcp": "aitp_v5_apply_session_closeout",
        "cli": "aitp-v5 session closeout-apply --plan-json <args>",
        "surface": "session_closeout_apply",
    },
}
