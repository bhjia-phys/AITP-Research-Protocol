"""CLI parser and dispatch for M0 capability and context operations."""

from __future__ import annotations

from brain.v5.mcp_context import (
    aitp_v5_compile_research_context,
    aitp_v5_get_capability_registry,
    aitp_v5_get_runtime_capability_audit,
)


def add_context_parser(subparsers) -> None:
    context = subparsers.add_parser("context")
    commands = context.add_subparsers(dest="context_command", required=True)
    commands.add_parser("capability-audit")
    runtime = commands.add_parser("runtime-audit")
    runtime.add_argument("--repo-root", default="")
    compile_parser = commands.add_parser("compile")
    compile_parser.add_argument("session_id")
    compile_parser.add_argument("--objective", default="", dest="objective_text")
    compile_parser.add_argument("--user-goal", default="")
    compile_parser.add_argument("--topic", default="", dest="topic_id")
    compile_parser.add_argument("--ref", action="append", default=[], dest="exact_refs")
    compile_parser.add_argument("--max-tokens", type=int, default=1200)
    compile_parser.add_argument("--max-bytes", type=int, default=6000)
    compile_parser.add_argument("--record-limit", type=int, default=80)
    compile_parser.add_argument("--candidate-limit", type=int, default=12)


def dispatch_context_command(args) -> dict:
    if args.context_command == "capability-audit":
        return aitp_v5_get_capability_registry()
    if args.context_command == "runtime-audit":
        return aitp_v5_get_runtime_capability_audit(
            args.base,
            repo_root=args.repo_root,
        )
    if args.context_command == "compile":
        return aitp_v5_compile_research_context(
            args.base,
            session_id=args.session_id,
            objective_text=args.objective_text,
            user_goal=args.user_goal,
            topic_id=args.topic_id,
            exact_refs=args.exact_refs,
            max_tokens=args.max_tokens,
            max_bytes=args.max_bytes,
            record_limit=args.record_limit,
            candidate_limit=args.candidate_limit,
        )
    raise SystemExit(f"unsupported context command: {args.context_command}")
