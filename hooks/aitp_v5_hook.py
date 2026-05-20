"""Small shell-facing adapter for AITP v5 hook decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain.v5.hook_adapters import hook_decision_payload, policy_decision_from_payload
from brain.v5.hooks import decide_pre_commit, decide_pre_tool_use


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

    pre_tool = subparsers.add_parser("pre-tool")
    pre_tool.add_argument("--action", required=True)
    pre_tool.add_argument("--risk-level", default="fluid")
    pre_tool.add_argument("--policy-json", required=True)

    return parser


def _dispatch(args: argparse.Namespace) -> dict:
    if args.command == "pre-commit":
        decision = decide_pre_commit(
            changed_files=args.changed_files,
            test_refs=args.test_refs,
            evolution_note=args.evolution_note,
        )
        return hook_decision_payload(decision, hook_name="pre_commit")
    if args.command == "pre-tool":
        policy_payload = json.loads(_read_json_arg(args.policy_json))
        decision = decide_pre_tool_use(
            action=args.action,
            risk_level=args.risk_level,
            policy_decision=policy_decision_from_payload(
                policy_payload,
                fallback_action=args.action,
            ),
        )
        return hook_decision_payload(decision, hook_name="pre_tool")
    raise SystemExit(f"unsupported hook command: {args.command}")


def _read_json_arg(value: str) -> str:
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
