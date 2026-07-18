"""File-backed CLI ingress for explicit Research Moment events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.record_envelope import RecordActor
from brain.v5.research_moment_facade import process_research_moment_request


def add_research_moment_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("research-moment")
    sub = parser.add_subparsers(dest="research_moment_command", required=True)
    process = sub.add_parser("process")
    process.add_argument("--request-json-file", required=True)
    process.add_argument(
        "--actor-type",
        choices=("human", "model", "tool", "migration"),
        default="model",
    )
    process.add_argument("--actor-id", default="aitp-research-moment-cli")
    process.add_argument("--host", default="cli")


def is_research_moment_command(args: argparse.Namespace) -> bool:
    return getattr(args, "command", None) == "research-moment"


def dispatch_research_moment_command(args: argparse.Namespace, ws) -> dict[str, Any]:
    if args.research_moment_command != "process":
        raise SystemExit(
            f"unsupported research-moment command: {args.research_moment_command}"
        )
    request = _load_request(args.request_json_file)
    payload = process_research_moment_request(
        ws,
        request,
        actor=RecordActor(
            actor_type=args.actor_type,
            actor_id=args.actor_id,
            host=args.host,
        ),
    )
    return require_valid_public_surface("research_moment_process_result", payload)


def _load_request(path: str) -> dict[str, Any]:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read Research Moment request {source}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Research Moment request JSON must be an object")
    return dict(payload)


__all__ = [
    "add_research_moment_parser",
    "dispatch_research_moment_command",
    "is_research_moment_command",
]
