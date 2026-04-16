#!/usr/bin/env python3
"""Compatibility wrapper for the single-entry OpenClaw AITP loop."""

from __future__ import annotations

import argparse
import subprocess

from _aitp_runtime_common import (
    ADAPTER_ROOT,
    python_command,
    quote_command,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug")
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--human-request")
    parser.add_argument("--updated-by", default="openclaw")
    parser.add_argument("--skill-query", action="append", default=[])
    parser.add_argument("--dispatch-auto", action="store_true")
    parser.add_argument("--max-auto-actions", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    max_steps = max(args.max_auto_actions, 0) if args.dispatch_auto else 0
    loop_command = [
        *python_command(),
        str(ADAPTER_ROOT / "scripts" / "aitp_loop.py"),
        "--updated-by",
        args.updated_by,
        "--max-steps",
        str(max_steps),
    ]
    if args.topic_slug:
        loop_command.extend(["--topic-slug", args.topic_slug])
    if args.run_id:
        loop_command.extend(["--run-id", args.run_id])
    if args.control_note:
        loop_command.extend(["--control-note", args.control_note])
    if args.human_request:
        loop_command.extend(["--human-request", args.human_request])
    for query in args.skill_query:
        loop_command.extend(["--skill-query", query])

    if args.dry_run:
        print(f"loop_command={quote_command(loop_command)}")
        return 0

    return subprocess.run(loop_command, check=False, stdin=subprocess.DEVNULL).returncode


if __name__ == "__main__":
    raise SystemExit(main())
