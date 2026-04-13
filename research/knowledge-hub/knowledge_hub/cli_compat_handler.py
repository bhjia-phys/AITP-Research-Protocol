from __future__ import annotations

import argparse
import json
from typing import Any

from .l2_staging import stage_negative_result_entry

_CORE_HELP_COMMANDS = [
    "session-start",
    "status",
    "next",
    "work",
    "consult-l2",
]

_HELP_GROUPS: list[tuple[str, list[str]]] = [
    ("Core commands", _CORE_HELP_COMMANDS),
    (
        "Front door and install",
        [
            "hello",
            "explore",
            "promote-exploration",
            "install-agent",
            "migrate-local-install",
            "doctor",
        ],
    ),
    (
        "Topic lifecycle",
        [
            "bootstrap",
            "new-topic",
            "resume",
            "loop",
            "steer-topic",
            "layer-graph",
            "verify",
            "complete-topic",
            "reintegrate-followup",
            "update-followup-return",
            "topics",
            "current-topic",
            "state",
        ],
    ),
    (
        "Knowledge reuse and source work",
        [
            "seed-l2-direction",
            "stage-l2-provisional",
            "compile-l2-map",
            "compile-l2-graph-report",
            "compile-l2-knowledge-report",
            "compile-source-catalog",
            "compile-source-family",
            "trace-source-citations",
            "export-source-bibtex",
            "import-bibtex-sources",
            "sync-l1-graph-export-to-theoretical-physics-brain",
            "stage-negative-result",
        ],
    ),
    (
        "Validation and promotion",
        [
            "audit",
            "ci-check",
            "baseline",
            "atomize",
            "operation-init",
            "operation-update",
            "trust-audit",
            "capability-audit",
            "paired-backend-audit",
            "h-plane-audit",
            "coverage-audit",
            "formal-theory-audit",
            "analytical-review",
            "lean-bridge",
            "statement-compilation",
            "request-promotion",
            "approve-promotion",
            "reject-promotion",
            "promote",
            "auto-promote",
            "audit-l2-hygiene",
            "prune-compat-surfaces",
        ],
    ),
    (
        "Memory and scratchpad",
        [
            "collaborator-memory",
            "show-collaborator-memory",
            "record-collaborator-memory",
            "scratch-log",
            "record-scratch-note",
            "record-negative-result",
            "taste-profile",
            "record-taste",
            "replay-topic",
        ],
    ),
    (
        "Active topic registry",
        [
            "focus-topic",
            "pause-topic",
            "resume-topic",
            "block-topic",
            "unblock-topic",
            "clear-topic-dependencies",
        ],
    ),
    (
        "Decisions and chronicle",
        [
            "emit-decision",
            "resolve-decision",
            "list-decisions",
            "trace-decision",
            "chronicle",
        ],
    ),
]


def _command_help_map(parser: argparse.ArgumentParser) -> dict[str, str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return {
                str(choice_action.dest): str(choice_action.help or "").strip()
                for choice_action in action._choices_actions
            }
    return {}


def _render_help_rows(command_names: list[str], help_map: dict[str, str]) -> list[str]:
    lines: list[str] = []
    if not command_names:
        return lines
    width = max(len(name) for name in command_names)
    for command_name in command_names:
        description = help_map.get(command_name) or "Registered AITP command."
        lines.append(f"  {command_name.ljust(width)}  {description}")
    return lines


def render_cli_help(parser: argparse.ArgumentParser, *, show_all: bool = False) -> str:
    help_map = _command_help_map(parser)
    lines = [
        "AITP Help",
        "",
    ]

    if not show_all:
        lines.append("Core commands")
        lines.extend(_render_help_rows(list(_CORE_HELP_COMMANDS), help_map))
        lines.extend(
            [
                "",
                "See everything: aitp help --all",
                "Argparse reference: aitp -h",
            ]
        )
        return "\n".join(lines).rstrip()

    lines.append(f"All registered commands: {len(help_map)}")
    assigned: set[str] = set()
    for heading, command_names in _HELP_GROUPS:
        visible_names = [name for name in command_names if name in help_map and name not in assigned]
        if not visible_names:
            continue
        if len(lines) > 3:
            lines.append("")
        lines.append(heading)
        lines.extend(_render_help_rows(visible_names, help_map))
        assigned.update(visible_names)

    remaining = sorted(name for name in help_map if name not in assigned)
    if remaining:
        lines.append("")
        lines.append("Other commands")
        lines.extend(_render_help_rows(remaining, help_map))

    lines.extend(
        [
            "",
            "Argparse reference: aitp -h",
        ]
    )
    return "\n".join(lines).rstrip()


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


def _looks_like_doctor_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and "overall_status" in payload and "runtime_support_matrix" in payload and "package" in payload


def _topic_status_word(payload: dict[str, Any]) -> str:
    completion_status = str(((payload.get("topic_completion") or {}).get("status")) or "").strip().lower()
    gap_status = str(((payload.get("open_gap_summary") or {}).get("status")) or "").strip().lower()
    stage = str(payload.get("current_stage") or "").strip().lower()
    if completion_status in {"promoted", "complete", "completed"} or stage in {"l5", "complete", "completed"}:
        return "complete"
    if gap_status and gap_status not in {"clear", "unknown", "none", "not_applicable"}:
        return "blocked"
    return "active"


def render_topic_status_payload(payload: dict[str, Any], *, tier: str = "summary") -> str:
    topic = str(payload.get("title") or payload.get("topic_slug") or "(missing)")
    stage = str(payload.get("current_stage") or "(missing)")
    mode = str(payload.get("research_mode") or "(missing)")
    current = str(payload.get("selected_action_summary") or payload.get("next_action_hint") or "(no selected action)")
    next_action_hint = str(payload.get("next_action_hint") or "").strip()
    must_read_now = list(payload.get("must_read_now") or [])
    read_now = str((must_read_now[0] or {}).get("path") or "(none)") if must_read_now else "(none)"
    gap_status = str(((payload.get("open_gap_summary") or {}).get("status")) or "").strip() or "unknown"
    blocked = "none" if gap_status in {"clear", "unknown"} else gap_status.replace("_", " ")
    topic_slug = str(payload.get("topic_slug") or "").strip() or "<topic_slug>"
    status_word = _topic_status_word(payload)
    lines = [
        "AITP Status",
        "",
        f"Topic: {topic}",
        f"Topic slug: {topic_slug}",
        f"Stage: {stage}",
        f"Status: {status_word}",
        f"Next: {current}",
        f"Machine view: aitp status --topic-slug {topic_slug} --json",
    ]
    if tier == "verbose":
        lines.extend(
            [
                "",
                "Key sections",
                "",
                f"Mode: {mode}",
                f"Read now: {read_now}",
                f"Blocked: {blocked}",
                f"Hint: {next_action_hint or '(none)'}",
                f"Promotion readiness: {str(((payload.get('promotion_readiness') or {}).get('status')) or '(missing)')}",
                f"Topic completion: {str(((payload.get('topic_completion') or {}).get('status')) or '(missing)')}",
                f"Statement compilation: {str(((payload.get('statement_compilation') or {}).get('status')) or '(missing)')}",
                f"Lean bridge: {str(((payload.get('lean_bridge') or {}).get('status')) or '(missing)')}",
            ]
        )
    return "\n".join(lines).rstrip()


def render_topic_next_payload(payload: dict[str, Any]) -> str:
    topic_slug = str(payload.get("topic_slug") or "").strip() or "<topic_slug>"
    current = str(payload.get("selected_action_summary") or "(no selected action)")
    must_read_now = list(payload.get("must_read_now") or [])
    read_now = str((must_read_now[0] or {}).get("path") or payload.get("open_next") or "(none)") if must_read_now else str(payload.get("open_next") or "(none)")
    gap_status = str(((payload.get("open_gap_summary") or {}).get("status")) or "").strip() or "unknown"
    blocked = "none" if gap_status in {"clear", "unknown"} else gap_status.replace("_", " ")
    lines = [
        "AITP Next",
        "",
        f"Topic: {topic_slug}",
        f"Do: {current}",
        f"Read now: {read_now}",
        f"Blocked: {blocked}",
        f"Machine view: aitp next --topic-slug {topic_slug} --json",
    ]
    return "\n".join(lines).rstrip()


def render_hello_payload(payload: dict[str, Any]) -> str:
    mode = str(payload.get("mode") or "welcome")
    topic_slug = str(payload.get("topic_slug") or "").strip() or "<topic_slug>"
    install_status = str(((payload.get("install") or {}).get("overall_status")) or "unknown")
    status = payload.get("status") or {}
    title = str(payload.get("topic_title") or topic_slug).replace("-", " ").strip().title() or topic_slug
    next_step = str(status.get("selected_action_summary") or payload.get("suggested_command") or "(missing)")
    if mode == "current_topic":
        lines = [
            "AITP Hello",
            "",
            f"Install check: {install_status}",
            f"Topic: {title}",
            f"Topic slug: {topic_slug}",
            f"Next step: {next_step}",
            f"Docs: {str(payload.get('docs_hint') or 'research/knowledge-hub/README.md')}",
            "Machine view: aitp hello --json",
        ]
        return "\n".join(lines).rstrip()
    lines = [
        "AITP Hello",
        "",
        f"Install check: {install_status}",
        "Status: no active topic",
        "AITP helps turn one bounded research topic into an auditable runtime loop.",
        f"First step: {next_step}",
        f"Docs: {str(payload.get('docs_hint') or 'research/knowledge-hub/README.md')}",
        "Machine view: aitp hello --json",
    ]
    return "\n".join(lines).rstrip()


def _doctor_runtime_lines(runtime_key: str, row: dict[str, Any], *, indent: int = 2) -> list[str]:
    prefix = " " * indent
    detail_prefix = " " * (indent + 2)
    maturity_label = str(row.get("maturity_class") or "").replace("_", " ").strip() or "runtime"
    display_name = str(row.get("display_name") or runtime_key)
    status = str(row.get("status") or "unknown")
    lines = [f"{prefix}- {display_name}: {status} [{maturity_label}]"]
    entry = str(row.get("preferred_entry") or "").strip()
    if entry:
        lines.append(f"{detail_prefix}Entry: {entry}")
    issues = list(row.get("issues") or [])
    if issues:
        lines.append(f"{detail_prefix}Issues: {', '.join(str(issue) for issue in issues)}")
    remediation = row.get("remediation") or {}
    remediation_status = str(remediation.get("status") or "")
    if remediation_status and remediation_status != "none_required":
        lines.append(f"{detail_prefix}Repair status: {remediation_status}")
        command = str(remediation.get("command") or "").strip()
        if command:
            lines.append(f"{detail_prefix}Repair: {command}")
        doc_path = str(remediation.get("doc_path") or "").strip()
        if doc_path:
            lines.append(f"{detail_prefix}Docs: {doc_path}")
        seen_hints: set[str] = set()
        for hint_row in remediation.get("issue_hints") or []:
            hint = str((hint_row or {}).get("hint") or "").strip()
            if hint and hint not in seen_hints:
                seen_hints.add(hint)
                lines.append(f"{detail_prefix}Hint: {hint}")
    return lines


def _doctor_deep_execution_lines(runtime_key: str, row: dict[str, Any], *, indent: int = 2) -> list[str]:
    prefix = " " * indent
    detail_prefix = " " * (indent + 2)
    relationship = str(row.get("baseline_relationship") or row.get("maturity_class") or "runtime").replace("_", " ").strip()
    display_name = str(row.get("display_name") or runtime_key)
    status = str(row.get("status") or "unknown")
    lines = [f"{prefix}- {display_name}: {status} [{relationship}]"]
    acceptance_command = str(row.get("acceptance_command") or "").strip()
    if acceptance_command:
        lines.append(f"{detail_prefix}Acceptance: {acceptance_command}")
    front_door_status = str(row.get("front_door_status") or "").strip()
    if front_door_status and front_door_status != "ready":
        lines.append(f"{detail_prefix}Front door: {front_door_status}")
    blockers = list(row.get("blockers") or [])
    if blockers:
        lines.append(f"{detail_prefix}Blockers: {', '.join(str(blocker) for blocker in blockers)}")
    repair_command = str(row.get("repair_command") or "").strip()
    if repair_command:
        lines.append(f"{detail_prefix}Repair: {repair_command}")
    return lines


def _render_doctor_payload(payload: dict[str, Any]) -> list[str]:
    lines = ["AITP Doctor", ""]
    lines.append(f"Overall: {payload.get('overall_status', 'unknown')}")

    package = payload.get("package") or {}
    package_status = str(package.get("status") or "unknown")
    package_version = str(package.get("version") or "unknown")
    package_name = str(package.get("name") or "aitp")
    lines.append(f"Package: {package_status} ({package_name} {package_version})")

    layer_roots = payload.get("layer_roots") or {}
    missing_roots = [name for name, row in layer_roots.items() if str((row or {}).get("status") or "") != "present"]
    protocol_contracts = payload.get("protocol_contracts") or {}
    missing_contracts = [name for name, row in protocol_contracts.items() if str((row or {}).get("status") or "") != "present"]
    if not missing_roots and not missing_contracts:
        lines.append("Protocol roots: ready")
    else:
        missing_rows = missing_roots + missing_contracts
        lines.append(f"Protocol roots: missing {', '.join(str(item) for item in missing_rows)}")

    runtime_convergence = payload.get("runtime_convergence") or {}
    front_door_ready = list(runtime_convergence.get("front_door_ready_runtimes") or [])
    front_door_non_ready = list(runtime_convergence.get("front_door_non_ready_runtimes") or [])
    front_door_converged = bool(runtime_convergence.get("front_door_runtimes_converged"))
    if front_door_converged:
        lines.append("Front-door convergence: yes")
    else:
        lines.append(
            "Front-door convergence: no"
            + (
                f" (ready: {', '.join(front_door_ready)}; repair: {', '.join(front_door_non_ready)})"
                if front_door_ready or front_door_non_ready
                else ""
            )
        )

    full_repair = payload.get("full_convergence_repair") or {}
    if str(full_repair.get("status") or "") != "none_required":
        command = str(full_repair.get("command") or "").strip()
        if command:
            lines.append(f"Full repair: {command}")

    matrix = payload.get("runtime_support_matrix") or {}
    runtime_rows = matrix.get("runtimes") or {}
    front_door_runtimes = list(runtime_convergence.get("front_door_runtimes") or [])
    if front_door_runtimes:
        lines.append("")
        lines.append("Front-door runtimes:")
        for runtime_key in front_door_runtimes:
            row = runtime_rows.get(runtime_key) or {}
            lines.extend(_doctor_runtime_lines(runtime_key, row))

    specialized_lanes = list(matrix.get("specialized_lanes") or [])
    if specialized_lanes:
        lines.append("")
        lines.append("Specialized lanes:")
        for runtime_key in specialized_lanes:
            row = runtime_rows.get(runtime_key) or {}
            lines.extend(_doctor_runtime_lines(runtime_key, row))

    deep_execution_summary = payload.get("deep_execution_parity") or {}
    deep_execution_matrix = (payload.get("runtime_support_matrix") or {}).get("deep_execution_parity") or {}
    if deep_execution_summary:
        baseline_runtime = str(deep_execution_summary.get("baseline_runtime") or "")
        baseline_status = str(deep_execution_summary.get("baseline_status") or "unknown")
        pending_targets = list(deep_execution_summary.get("pending_targets") or [])
        blocked_targets = list(deep_execution_summary.get("blocked_targets") or [])
        summary_line = "Deep-execution parity: "
        summary_line += "yes" if deep_execution_summary.get("parity_targets_converged") else "no"
        detail_parts: list[str] = []
        if baseline_runtime:
            detail_parts.append(f"baseline: {baseline_runtime}={baseline_status}")
        if pending_targets:
            detail_parts.append(f"pending: {', '.join(str(item) for item in pending_targets)}")
        if blocked_targets:
            detail_parts.append(f"blocked: {', '.join(str(item) for item in blocked_targets)}")
        if detail_parts:
            summary_line += f" ({'; '.join(detail_parts)})"
        lines.append(summary_line)

        scoped_runtimes = list(
            deep_execution_matrix.get("scoped_runtimes")
            or [baseline_runtime, *list(deep_execution_summary.get("parity_targets") or [])]
        )
        deep_rows = deep_execution_matrix.get("runtimes") or {}
        if scoped_runtimes:
            lines.append("")
            lines.append("Deep-execution runtimes:")
            for runtime_key in scoped_runtimes:
                row = deep_rows.get(runtime_key) or {}
                lines.extend(_doctor_deep_execution_lines(runtime_key, row))
        deferred_lanes = list(deep_execution_matrix.get("deferred_lanes") or [])
        if deferred_lanes:
            lines.append("")
            lines.append("Deep-execution deferred lanes:")
            for runtime_key in deferred_lanes:
                row = deep_rows.get(runtime_key) or {}
                lines.extend(_doctor_deep_execution_lines(runtime_key, row))

    lines.append("")
    lines.append("Machine view: aitp doctor --json")
    return lines


def emit_payload(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if _looks_like_doctor_payload(payload):
        lines = _render_doctor_payload(payload)
    else:
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

    scratch_log = subparsers.add_parser(
        "scratch-log",
        help="Read topic-scoped scratch and negative-result runtime memory",
    )
    scratch_log.add_argument("--topic-slug", required=True)
    scratch_log.add_argument("--updated-by", default="aitp-cli")
    scratch_log.add_argument("--json", action="store_true")

    record_scratch_note = subparsers.add_parser(
        "record-scratch-note",
        help="Append one topic-scoped scratch or route-comparison note",
    )
    record_scratch_note.add_argument("--topic-slug", required=True)
    record_scratch_note.add_argument(
        "--kind",
        required=True,
        choices=["scratch_note", "route_comparison", "open_question", "failed_attempt"],
    )
    record_scratch_note.add_argument("--summary", required=True)
    record_scratch_note.add_argument("--details")
    record_scratch_note.add_argument("--run-id")
    record_scratch_note.add_argument("--candidate-id")
    record_scratch_note.add_argument("--related-artifact", action="append", default=[])
    record_scratch_note.add_argument("--updated-by", default="aitp-cli")
    record_scratch_note.add_argument("--json", action="store_true")

    record_negative_result_runtime = subparsers.add_parser(
        "record-negative-result",
        help="Append one topic-scoped negative-result note into the runtime scratchpad",
    )
    record_negative_result_runtime.add_argument("--topic-slug", required=True)
    record_negative_result_runtime.add_argument("--summary", required=True)
    record_negative_result_runtime.add_argument("--failure-kind", required=True)
    record_negative_result_runtime.add_argument("--details")
    record_negative_result_runtime.add_argument("--run-id")
    record_negative_result_runtime.add_argument("--candidate-id")
    record_negative_result_runtime.add_argument("--related-artifact", action="append", default=[])
    record_negative_result_runtime.add_argument("--updated-by", default="aitp-cli")
    record_negative_result_runtime.add_argument("--json", action="store_true")

    taste_profile = subparsers.add_parser(
        "taste-profile",
        help="Read the runtime-side research taste and physical-intuition surface for one topic",
    )
    taste_profile.add_argument("--topic-slug", required=True)
    taste_profile.add_argument("--updated-by", default="aitp-cli")
    taste_profile.add_argument("--json", action="store_true")

    record_taste = subparsers.add_parser(
        "record-taste",
        help="Append one structured runtime-side research taste or physical-intuition entry",
    )
    record_taste.add_argument("--topic-slug", required=True)
    record_taste.add_argument(
        "--kind",
        required=True,
        choices=["route_taste", "elegance", "formalism", "intuition", "surprise_handling"],
    )
    record_taste.add_argument("--summary", required=True)
    record_taste.add_argument("--details")
    record_taste.add_argument("--run-id")
    record_taste.add_argument("--formalism", action="append", default=[])
    record_taste.add_argument("--tag", action="append", default=[])
    record_taste.add_argument("--related-artifact", action="append", default=[])
    record_taste.add_argument("--updated-by", default="aitp-cli")
    record_taste.add_argument("--json", action="store_true")

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

    if args.command == "scratch-log":
        return service.topic_scratchpad(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )

    if args.command == "record-scratch-note":
        return service.record_scratch_note(
            topic_slug=args.topic_slug,
            entry_kind=args.kind,
            summary=args.summary,
            details=args.details,
            run_id=args.run_id,
            candidate_id=args.candidate_id,
            related_artifacts=args.related_artifact,
            updated_by=args.updated_by,
        )

    if args.command == "record-negative-result":
        return service.record_negative_result(
            topic_slug=args.topic_slug,
            summary=args.summary,
            failure_kind=args.failure_kind,
            details=args.details,
            run_id=args.run_id,
            candidate_id=args.candidate_id,
            related_artifacts=args.related_artifact,
            updated_by=args.updated_by,
        )

    if args.command == "taste-profile":
        return service.topic_research_taste(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )

    if args.command == "record-taste":
        return service.record_research_taste(
            topic_slug=args.topic_slug,
            taste_kind=args.kind,
            summary=args.summary,
            details=args.details,
            run_id=args.run_id,
            formalisms=args.formalism,
            tags=args.tag,
            related_artifacts=args.related_artifact,
            updated_by=args.updated_by,
        )

    if args.command == "stage-negative-result":
        return stage_negative_result_entry(
            service.kernel_root,
            title=args.title,
            summary=args.summary,
            failure_kind=args.failure_kind,
            staged_by=args.updated_by,
        )

    return None
