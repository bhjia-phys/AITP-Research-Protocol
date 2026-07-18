"""Small machine-readable hook runner payload and argv builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.hook_routing_mode import HookRoutingMode, hook_routing_cli_args, hook_routing_metadata


def build_pre_tool_event_runner(
    runtime: str,
    payload_path: str | Path,
    *,
    routing: HookRoutingMode,
    topics_root: str,
    project_root: str,
) -> dict[str, Any]:
    path = str(Path(payload_path))
    routing_metadata = hook_routing_metadata(
        routing,
        topics_root=topics_root,
        project_root=project_root,
    )
    argv = build_adapter_event_runner_argv(
        executable="python",
        runner_path="hooks/aitp_v5_adapter_event_runner.py",
        event="pre-tool",
        runtime=runtime,
        topics_root=topics_root,
        project_root=project_root,
        routing=routing,
        bridge_payload_path=path,
    )
    return {
        "kind": "pre_tool_event_runner",
        "runtime": runtime,
        "session_id": routing.pinned_session_id,
        **routing_metadata,
        "bridge_payload_source": "payload_path",
        "payload_path": path,
        "platform_event_placeholder": "<platform-event-json>",
        "argv": argv,
        "stdin_runner": {
            "kind": "stdin_pre_tool_event_runner",
            "script": "hooks/aitp_v5_adapter_event_runner.py",
            "stdin": "<platform-event-json>",
            "argv": list(argv),
            "truth_source": "typed_records",
            "summary_inputs_trusted": False,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        },
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def build_adapter_event_runner_argv(
    *,
    executable: str,
    runner_path: str,
    event: str,
    runtime: str,
    topics_root: str,
    project_root: str,
    routing: HookRoutingMode,
    bridge_payload_path: str = "",
) -> list[str]:
    if event not in {"pre-tool", "post-tool"}:
        raise ValueError("adapter event runner requires pre-tool or post-tool")
    argv = [
        executable,
        runner_path,
        event,
        "--base",
        topics_root,
        "--runtime",
        runtime,
    ]
    routing_args = hook_routing_cli_args(routing)
    argv.extend(routing_args[2:])
    if event == "pre-tool":
        if not bridge_payload_path:
            raise ValueError("pre-tool runner requires bridge payload path")
        argv.extend(["--bridge-path", bridge_payload_path])
    elif bridge_payload_path:
        raise ValueError("post-tool runner cannot carry bridge payload path")
    argv.extend(["--project-root", project_root, *routing_args[:2]])
    return argv


def build_native_lifecycle_hook_argv(
    *,
    executable: str,
    hook_path: str,
    command: str,
    topics_root: str,
    project_root: str,
    routing: HookRoutingMode,
) -> list[str]:
    if command not in {"session-start", "pre-tool", "post-tool"}:
        raise ValueError("unsupported native lifecycle hook command")
    routing_args = hook_routing_cli_args(routing)
    return [
        executable,
        hook_path,
        command,
        "--base",
        topics_root,
        *routing_args[2:],
        "--project-root",
        project_root,
        *routing_args[:2],
    ]


__all__ = [
    "build_adapter_event_runner_argv",
    "build_native_lifecycle_hook_argv",
    "build_pre_tool_event_runner",
]
