"""CLI commands for generic, review-only Harness Feedback cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from brain.v5.harness_feedback_case_contracts import HarnessFeedbackCaseRequest
from brain.v5.harness_feedback_cases import (
    build_harness_feedback_review_view,
    harness_feedback_case_write_payload,
    record_harness_feedback_case,
)
from brain.v5.record_envelope import RecordActor


def add_harness_feedback_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("harness-feedback")
    sub = parser.add_subparsers(dest="harness_feedback_command", required=True)
    record = sub.add_parser("record")
    record.add_argument("--request-json-file", required=True)
    record.add_argument(
        "--update-mode",
        choices=("create_or_idempotent", "revision", "related"),
        default="create_or_idempotent",
    )
    record.add_argument("--expected-hash", default="")
    record.add_argument(
        "--actor-type",
        choices=("human", "model", "tool", "migration"),
        default="model",
    )
    record.add_argument("--actor-id", default="aitp-harness-feedback-cli")
    record.add_argument("--host", default="cli")
    sub.add_parser("review-view")


def dispatch_harness_feedback_command(args: argparse.Namespace, ws) -> dict[str, Any]:
    if args.harness_feedback_command == "record":
        request = HarnessFeedbackCaseRequest(**_load_request(args.request_json_file))
        result = record_harness_feedback_case(
            ws,
            request,
            actor=RecordActor(
                actor_type=args.actor_type,
                actor_id=args.actor_id,
                host=args.host,
            ),
            update_mode=args.update_mode,
            expected_hash=args.expected_hash,
        )
        return harness_feedback_case_write_payload(result)
    if args.harness_feedback_command == "review-view":
        return build_harness_feedback_review_view(ws)
    raise SystemExit(f"unsupported harness-feedback command: {args.harness_feedback_command}")


def _load_request(path: str) -> dict[str, Any]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read Harness Feedback request {source}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Harness Feedback request JSON must be an object")
    return dict(payload)
