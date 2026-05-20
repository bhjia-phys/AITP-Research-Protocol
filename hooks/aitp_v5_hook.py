"""Small shell-facing adapter for AITP v5 hook decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain.v5.hook_adapters import hook_decision_payload
from brain.v5.hooks import decide_pre_commit


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    payload = _dispatch(args)
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return int(payload["exit_code"])


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp-v5-hook")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pre_commit = subparsers.add_parser("pre-commit")
    pre_commit.add_argument("--changed-file", action="append", default=[], dest="changed_files")
    pre_commit.add_argument("--test-ref", action="append", default=[], dest="test_refs")
    pre_commit.add_argument("--evolution-note", default="")

    return parser


def _dispatch(args: argparse.Namespace) -> dict:
    if args.command == "pre-commit":
        decision = decide_pre_commit(
            changed_files=args.changed_files,
            test_refs=args.test_refs,
            evolution_note=args.evolution_note,
        )
        return hook_decision_payload(decision, hook_name="pre_commit")
    raise SystemExit(f"unsupported hook command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
