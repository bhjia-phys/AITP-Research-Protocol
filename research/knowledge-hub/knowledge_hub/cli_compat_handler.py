from __future__ import annotations

import argparse
import json
from typing import Any

from .l2_staging import stage_negative_result_entry


def _humanize_key(key: str) -> str:
    return str(key or "").replace("_", " ").strip() or "value"


def _render_human_lines(payload: Any, *, indent: int = 0, key: str | None = None) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(payload, dict):
        if key is not None:
            lines.append(f"{prefix}{_humanize_key(key)}:")
            indent += 2
        for child_key, child_value in payload.items():
            lines.extend(_render_human_lines(child_value, indent=indent, key=str(child_key)))
        return lines
    if isinstance(payload, list):
        if key is not None:
            if not payload:
                return [f"{prefix}{_humanize_key(key)}: (none)"]
            if all(not isinstance(item, (dict, list)) for item in payload):
                return [f"{prefix}{_humanize_key(key)}: {', '.join(str(item) for item in payload)}"]
            lines.append(f"{prefix}{_humanize_key(key)}:")
            for item in payload:
                lines.extend(_render_human_lines(item, indent=indent + 2))
            return lines
        for item in payload:
            lines.extend(_render_human_lines(item, indent=indent))
        return lines
    if key is None:
        return [f"{prefix}{payload}"]
    return [f"{prefix}{_humanize_key(key)}: {payload}"]


def emit_payload(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    lines = ["Result", ""]
    lines.extend(_render_human_lines(payload))
    print("\n".join(lines).rstrip())


def register_compat_commands(subparsers: argparse._SubParsersAction[Any]) -> None:
    show_collaborator_memory = subparsers.add_parser(
        "show-collaborator-memory",
        help="Backward-compatible alias for collaborator-memory with a compact wrapper payload",
    )
    show_collaborator_memory.add_argument("--topic-slug")
    show_collaborator_memory.add_argument("--limit", type=int, default=10)
    show_collaborator_memory.add_argument("--json", action="store_true")

    record_collaborator_memory = subparsers.add_parser(
        "record-collaborator-memory",
        help="Append one runtime-side collaborator-memory row",
    )
    record_collaborator_memory.add_argument(
        "--memory-kind",
        choices=["preference", "trajectory", "working_style", "stuckness", "surprise", "coordination"],
    )
    record_collaborator_memory.add_argument("--summary")
    record_collaborator_memory.add_argument(
        "--preference",
        action="append",
        default=[],
        help="Backward-compatible shorthand for --memory-kind preference --summary <text>",
    )
    record_collaborator_memory.add_argument("--details")
    record_collaborator_memory.add_argument("--topic-slug")
    record_collaborator_memory.add_argument("--run-id")
    record_collaborator_memory.add_argument("--tag", action="append", default=[])
    record_collaborator_memory.add_argument("--related-topic-slug", action="append", default=[])
    record_collaborator_memory.add_argument("--updated-by", default="aitp-cli")
    record_collaborator_memory.add_argument("--json", action="store_true")

    stage_negative_result = subparsers.add_parser(
        "stage-negative-result",
        help="Stage one negative-result note into canonical staging using the legacy CLI entrypoint",
    )
    stage_negative_result.add_argument("--title", required=True)
    stage_negative_result.add_argument("--summary", required=True)
    stage_negative_result.add_argument("--failure-kind", required=True)
    stage_negative_result.add_argument("--updated-by", default="aitp-cli")
    stage_negative_result.add_argument("--json", action="store_true")


def _show_collaborator_memory_payload(raw_payload: dict[str, Any]) -> dict[str, Any]:
    entries = list(raw_payload.get("entries") or [])
    preferences = [
        str(row.get("summary") or "").strip()
        for row in entries
        if str(row.get("memory_kind") or "").strip() == "preference" and str(row.get("summary") or "").strip()
    ]
    return {
        "collaborator_memory": {
            "memory_kind": "collaborator_memory",
            "preferences": preferences,
            "entries": entries,
            "row_count": raw_payload.get("row_count", 0),
            "status": raw_payload.get("status", "absent"),
        }
    }


def dispatch_compat_command(args: argparse.Namespace, service: Any, parser: argparse.ArgumentParser) -> dict[str, Any] | None:
    if args.command == "show-collaborator-memory":
        raw_payload = service.get_collaborator_memory(
            topic_slug=args.topic_slug,
            limit=args.limit,
        )
        return _show_collaborator_memory_payload(raw_payload)

    if args.command == "record-collaborator-memory":
        memory_kind = args.memory_kind or ("preference" if args.preference else "")
        summary = args.summary or (args.preference[0] if args.preference else "")
        if not memory_kind or not summary:
            parser.error("record-collaborator-memory requires --memory-kind/--summary or --preference")
        raw_payload = service.record_collaborator_memory(
            memory_kind=memory_kind,
            summary=summary,
            details=args.details,
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            tags=args.tag,
            related_topic_slugs=args.related_topic_slug,
            updated_by=args.updated_by,
        )
        entry = raw_payload.get("collaborator_memory_entry") or {}
        return {
            "memory_kind": "collaborator_memory",
            "preference": entry.get("summary", ""),
            **raw_payload,
        }

    if args.command == "stage-negative-result":
        return stage_negative_result_entry(
            service.kernel_root,
            title=args.title,
            summary=args.summary,
            failure_kind=args.failure_kind,
            staged_by=args.updated_by,
        )

    return None
