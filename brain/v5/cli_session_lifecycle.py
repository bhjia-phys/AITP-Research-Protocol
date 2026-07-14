"""File-backed CLI adapter for the v5 research-session lifecycle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from brain.v5.mcp_session_lifecycle import (
    aitp_v5_apply_session_closeout,
    aitp_v5_coalesce_recording_batch,
    aitp_v5_plan_session_closeout,
    aitp_v5_run_recall_audit,
    aitp_v5_session_start,
    aitp_v5_stage_recording_candidate,
)


_COMMANDS = frozenset(
    {
        "start",
        "recall-audit",
        "recording-stage",
        "recording-batch",
        "closeout-plan",
        "closeout-apply",
    }
)


def add_session_lifecycle_parsers(sp: argparse._SubParsersAction) -> None:
    session_parser = sp.choices.get("session")
    if session_parser is None:
        raise RuntimeError("session parser must exist before lifecycle extensions")
    session_subparsers = next(
        action
        for action in session_parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    session_subparsers.add_parser("start").add_argument("session_id")

    recall = session_subparsers.add_parser("recall-audit")
    recall.add_argument("--request-json", required=True)
    recall.add_argument("--actor-json", default="")

    stage = session_subparsers.add_parser("recording-stage")
    stage.add_argument("--candidate-json", required=True)

    batch = session_subparsers.add_parser("recording-batch")
    batch.add_argument("session_id")
    batch.add_argument("milestone_id")
    batch.add_argument("--actor-json", default="")

    plan = session_subparsers.add_parser("closeout-plan")
    plan.add_argument("--request-json", required=True)

    apply = session_subparsers.add_parser("closeout-apply")
    apply.add_argument("--plan-json", required=True)
    apply.add_argument("--plan-id", required=True)
    apply.add_argument("--actor-json", default="")


def is_session_lifecycle_command(args: argparse.Namespace) -> bool:
    return args.command == "session" and args.session_command in _COMMANDS


def dispatch_session_lifecycle(args: argparse.Namespace) -> dict[str, Any]:
    base = str(args.base)
    command = args.session_command
    if command == "start":
        return aitp_v5_session_start(base, session_id=args.session_id)
    if command == "recall-audit":
        return aitp_v5_run_recall_audit(
            base,
            request=_read_json_object(args.request_json),
            actor=_optional_json_object(args.actor_json),
        )
    if command == "recording-stage":
        return aitp_v5_stage_recording_candidate(
            base,
            candidate=_read_json_object(args.candidate_json),
        )
    if command == "recording-batch":
        return aitp_v5_coalesce_recording_batch(
            base,
            session_id=args.session_id,
            milestone_id=args.milestone_id,
            actor=_optional_json_object(args.actor_json),
        )
    if command == "closeout-plan":
        return aitp_v5_plan_session_closeout(
            base,
            request=_read_json_object(args.request_json),
        )
    if command == "closeout-apply":
        return aitp_v5_apply_session_closeout(
            base,
            plan=_read_json_object(args.plan_json),
            plan_id=args.plan_id,
            actor=_optional_json_object(args.actor_json),
        )
    raise SystemExit(f"unsupported session lifecycle command: {command}")


def _optional_json_object(path: str) -> dict[str, Any] | None:
    return _read_json_object(path) if str(path or "").strip() else None


def _read_json_object(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON payload must be an object: {path}")
    return value
