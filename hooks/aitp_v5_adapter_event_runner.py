"""Host-facing runner for sidecar-backed AITP v5 adapter events."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.hook_adapters import hook_trace_event_payload
from brain.v5.host_lifecycle_facade import (
    dispatch_host_lifecycle_event,
    host_lifecycle_capability,
    normalize_host_lifecycle_event,
)
from brain.v5.hook_research_moment_bridge import process_explicit_hook_research_moment
from brain.v5.hooks import post_tool_use_trace_event
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.trace import persist_hook_trace_event
from brain.v5.workspace import get_session_binding, init_workspace


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _validate_routing_args(parser, args)
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
    pre_tool.add_argument("--session-id", default="")
    pre_tool.add_argument(
        "--routing-mode",
        choices=("dynamic", "pinned", "pinned_compat"),
        default="pinned_compat",
    )
    pre_tool.add_argument("--bridge-path", default="")
    post_tool = subparsers.add_parser("post-tool")
    post_tool.add_argument("--base", required=True)
    post_tool.add_argument("--runtime", required=True)
    post_tool.add_argument("--session-id", default="")
    post_tool.add_argument(
        "--routing-mode",
        choices=("dynamic", "pinned", "pinned_compat"),
        default="pinned_compat",
    )
    return parser


def _dispatch(args: argparse.Namespace, platform_event: dict[str, Any]) -> dict[str, Any]:
    if args.routing_mode == "dynamic":
        return _dispatch_dynamic(args, platform_event)
    if args.command == "post-tool":
        return _dispatch_post_tool(args, platform_event)
    if args.command != "pre-tool":
        raise SystemExit(f"unsupported adapter event command: {args.command}")
    bridge = _read_bridge(args.bridge_path)
    _validate_runner(bridge, runtime=args.runtime, session_id=args.session_id, bridge_path=args.bridge_path)
    event = _with_pre_tool_defaults(platform_event, runtime=args.runtime, session_id=args.session_id)
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_platform_pre_tool_event(init_workspace(args.base), bridge, event),
    )


def _dispatch_dynamic(
    args: argparse.Namespace,
    platform_event: dict[str, Any],
) -> dict[str, Any]:
    ws = init_workspace(args.base)
    route = _dynamic_lifecycle_dispatch(ws, args, platform_event)
    if route.route_status != "selected":
        return _route_dispatch_payload(route)
    if args.command == "post-tool":
        return _dispatch_post_tool(
            args,
            platform_event,
            selected_session_id=route.session_id,
            selected_topic_id=route.topic_id,
        )
    if not args.bridge_path:
        raise SystemExit(
            "dynamic pre-tool routing requires --bridge-path after route selection"
        )
    bridge = _read_bridge(args.bridge_path)
    _validate_runner(
        bridge,
        runtime=args.runtime,
        session_id=route.session_id,
        bridge_path=args.bridge_path,
    )
    event = _with_pre_tool_defaults(
        platform_event,
        runtime=args.runtime,
        session_id=route.session_id,
    )
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_platform_pre_tool_event(ws, bridge, event),
    )


def _dispatch_post_tool(
    args: argparse.Namespace,
    platform_event: dict[str, Any],
    *,
    selected_session_id: str = "",
    selected_topic_id: str = "",
) -> dict[str, Any]:
    ws = init_workspace(args.base)
    session_id = selected_session_id or args.session_id
    event = _with_post_tool_defaults(
        platform_event,
        ws,
        runtime=args.runtime,
        session_id=session_id,
        selected_topic_id=selected_topic_id,
    )
    trace_event = post_tool_use_trace_event(
        session_id=event["session_id"],
        topic_id=event["topic_id"],
        risk_level=event["risk_level"],
        claim_id=event["claim_id"],
        tool_name=event["tool_name"],
        evidence_status=event["evidence_status"],
    )
    hook_payload = hook_trace_event_payload(trace_event, hook_name="post_tool")
    record = persist_hook_trace_event(ws, hook_payload)
    moment = process_explicit_hook_research_moment(
        ws,
        platform_event,
        host=args.runtime,
        session_id=session_id,
        routing_mode=args.routing_mode,
    )
    if moment is not None:
        record = {**record, "research_moment": moment}
    return require_valid_public_surface("hook_trace_event_record", record)


def _dynamic_lifecycle_dispatch(ws, args, platform_event):
    logical_event = "pre_tool" if args.command == "pre-tool" else "post_tool"
    capability = host_lifecycle_capability(args.runtime)
    native_event = next(
        (
            event.native_event
            for event in capability.automatic_events
            if event.logical_event == logical_event
        ),
        "",
    )
    if not native_event:
        raise SystemExit(
            f"runtime {args.runtime!r} has no automatic {logical_event} lifecycle event"
        )
    payload = {
        "event_id": _required_top_level_string(platform_event, "event_id"),
        "host_session_id": _required_top_level_string(
            platform_event, "host_session_id"
        ),
        "topic_id": _string_value(platform_event.get("topic_id")),
        "tool_name": _tool_name(platform_event),
        "status": _evidence_status(platform_event),
        **_top_level_route_fields(platform_event),
    }
    event = normalize_host_lifecycle_event(
        args.runtime,
        native_event,
        payload,
        routing_mode="dynamic",
    )
    return dispatch_host_lifecycle_event(ws, event)


def _route_dispatch_payload(dispatch) -> dict[str, Any]:
    return {
        "kind": "host_route_dispatch",
        "ok": True,
        **asdict(dispatch),
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "exit_code": 0,
    }


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


def _with_post_tool_defaults(
    event: dict[str, Any],
    ws,
    *,
    runtime: str,
    session_id: str,
    selected_topic_id: str = "",
) -> dict[str, str]:
    binding = get_session_binding(ws, session_id)
    return {
        "runtime": runtime,
        "session_id": session_id,
        "topic_id": selected_topic_id
        or _string_value(event.get("topic_id"))
        or binding.topic_id,
        "claim_id": (
            binding.active_claim
            if selected_topic_id
            else _string_value(event.get("claim_id")) or binding.active_claim
        ),
        "risk_level": _string_value(event.get("risk_level")) or "guided",
        "tool_name": _tool_name(event),
        "evidence_status": _evidence_status(event),
    }


def _validate_routing_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.routing_mode == "dynamic" and args.session_id:
        parser.error("dynamic routing does not accept --session-id")
    if args.routing_mode in {"pinned", "pinned_compat"} and not args.session_id:
        parser.error(f"{args.routing_mode} routing requires --session-id")
    if (
        args.command == "pre-tool"
        and args.routing_mode != "dynamic"
        and not args.bridge_path
    ):
        parser.error("pinned pre-tool routing requires --bridge-path")


def _required_top_level_string(event: dict[str, Any], field: str) -> str:
    value = _string_value(event.get(field)).strip()
    if not value:
        raise SystemExit(f"dynamic routing requires top-level {field}")
    return value


def _top_level_route_fields(event: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in ("project_root", "current_path", "repo_id", "branch"):
        value = _string_value(event.get(field)).strip()
        if value:
            result[field] = value
    return result


def _tool_name(event: dict[str, Any]) -> str:
    return (
        _string_value(event.get("tool_name"))
        or _string_value(_nested(event, "tool", "name"))
        or _string_value(event.get("name"))
        or "unknown_tool"
    )


def _evidence_status(event: dict[str, Any]) -> str:
    return (
        _string_value(event.get("evidence_status"))
        or _string_value(event.get("status"))
        or _string_value(_nested(event, "result", "status"))
        or "unknown"
    )


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _string_value(value: Any) -> str:
    return value if isinstance(value, str) and value else ""


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
