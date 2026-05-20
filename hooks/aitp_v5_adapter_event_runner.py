"""Host-facing runner for sidecar-backed AITP v5 adapter events."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    payload = _dispatch(args, _read_stdin_payload())
    json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return int(payload.get("exit_code", 0))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp-v5-adapter-event-runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pre_tool = subparsers.add_parser("pre-tool")
    pre_tool.add_argument("--base", required=True)
    pre_tool.add_argument("--runtime", required=True)
    pre_tool.add_argument("--session-id", required=True)
    pre_tool.add_argument("--bridge-path", required=True)
    return parser


def _dispatch(args: argparse.Namespace, platform_event: dict[str, Any]) -> dict[str, Any]:
    if args.command != "pre-tool":
        raise SystemExit(f"unsupported adapter event command: {args.command}")
    bridge = _read_bridge(args.bridge_path)
    _validate_runner(bridge, runtime=args.runtime, session_id=args.session_id, bridge_path=args.bridge_path)
    event = _with_pre_tool_defaults(platform_event, runtime=args.runtime, session_id=args.session_id)
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_platform_pre_tool_event(init_workspace(args.base), bridge, event),
    )


def _read_stdin_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise SystemExit("adapter event runner stdin must be a JSON object")
    return payload


def _read_bridge(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("bridge sidecar must be a JSON object")
    return payload


def _with_pre_tool_defaults(event: dict[str, Any], *, runtime: str, session_id: str) -> dict[str, Any]:
    payload = dict(event)
    payload.setdefault("runtime", runtime)
    payload.setdefault("session_id", session_id)
    payload.setdefault("hook_name", "pre_tool")
    payload.setdefault("lifecycle_event", "pre_tool")
    return payload


def _validate_runner(bridge: dict[str, Any], *, runtime: str, session_id: str, bridge_path: str) -> None:
    runner = _runner_payload(bridge)
    if runner.get("runtime") != runtime:
        raise SystemExit("bridge runner runtime does not match requested runtime")
    if runner.get("session_id") != session_id:
        raise SystemExit("bridge runner session_id does not match requested session")
    argv = runner.get("argv")
    if not isinstance(argv, list):
        raise SystemExit("bridge runner argv must be a list")
    try:
        path_arg = argv[argv.index("--bridge-path") + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit("bridge runner argv must include --bridge-path") from exc
    if Path(str(path_arg)).resolve() != Path(bridge_path).resolve():
        raise SystemExit("bridge runner argv bridge path does not match requested sidecar")


def _runner_payload(bridge: dict[str, Any]) -> dict[str, Any]:
    if bridge.get("kind") == "codex_hook_bridge":
        runner = bridge.get("pre_tool_event_runner")
    elif bridge.get("kind") == "opencode_plugin_bridge":
        runner = bridge.get("plugin_bridge", {}).get("pre_tool_event_runner")
    else:
        raise SystemExit("unsupported bridge sidecar kind")
    if not isinstance(runner, dict):
        raise SystemExit("bridge sidecar is missing pre_tool_event_runner")
    return runner


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
