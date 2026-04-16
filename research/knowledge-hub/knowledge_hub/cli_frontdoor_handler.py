from __future__ import annotations

import argparse
from typing import Any


FRONTDOOR_COMMANDS = {
    "explore",
    "promote-exploration",
    "session-start",
    "install-agent",
    "migrate-local-install",
    "doctor",
}


def register_frontdoor_commands(subparsers: argparse._SubParsersAction[Any]) -> None:
    explore = subparsers.add_parser(
        "explore",
        help="Materialize a lightweight quick-exploration session without full topic bootstrap",
    )
    explore.add_argument("--updated-by", default="aitp-explore")
    explore.add_argument("--json", action="store_true")
    explore.add_argument("task", help="Natural-language speculative exploration request")

    promote_exploration = subparsers.add_parser(
        "promote-exploration",
        help="Promote a lightweight exploration session into the normal topic session-start path",
    )
    promote_exploration.add_argument("--exploration-id", required=True)
    promote_exploration.add_argument("--current-topic", action="store_true")
    promote_exploration.add_argument("--topic-slug")
    promote_exploration.add_argument("--topic")
    promote_exploration.add_argument("--updated-by", default="aitp-explore")
    promote_exploration.add_argument("--json", action="store_true")

    session_start = subparsers.add_parser(
        "session-start",
        help="Materialize AITP routing and runtime state from a natural-language session-start request",
    )
    session_topic_group = session_start.add_mutually_exclusive_group(required=False)
    session_topic_group.add_argument("--topic-slug")
    session_topic_group.add_argument("--topic")
    session_topic_group.add_argument("--current-topic", action="store_true")
    session_topic_group.add_argument("--latest-topic", action="store_true")
    session_start.add_argument("--statement")
    session_start.add_argument("--run-id")
    session_start.add_argument("--control-note")
    session_start.add_argument("--updated-by", default="aitp-session-start")
    session_start.add_argument("--skill-query", action="append", default=[])
    session_start.add_argument("--max-auto-steps", type=int, default=4)
    session_start.add_argument("--research-mode")
    session_start.add_argument("--load-profile", choices=["auto", "light", "full"], default="auto")
    session_start.add_argument("--json", action="store_true")
    session_start.add_argument("task", help="Natural-language research request to route into AITP")

    install = subparsers.add_parser("install-agent", help="Install AITP skills and bootstrap assets for supported agents")
    install.add_argument("--agent", choices=["codex", "openclaw", "opencode", "claude-code", "all"], required=True)
    install.add_argument("--scope", choices=["user", "project"], default="user")
    install.add_argument("--target-root")
    install.add_argument("--mcp-profile", choices=["full", "review", "skeptic"], default="full")
    install.add_argument("--no-force", action="store_true")
    install.add_argument("--no-mcp", action="store_true")
    install.add_argument("--json", action="store_true")

    migrate = subparsers.add_parser("migrate-local-install", help="Converge a mixed local AITP install to the canonical repo-backed install")
    migrate.add_argument("--workspace-root", required=True)
    migrate.add_argument("--backup-root")
    migrate.add_argument("--agent", action="append", choices=["codex", "claude-code", "opencode"])
    migrate.add_argument("--with-mcp", action="store_true")
    migrate.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Show AITP CLI install status")
    doctor.add_argument("--workspace-root")
    doctor.add_argument("--strict-l0l1", action="store_true")
    doctor.add_argument("--json", action="store_true")


def dispatch_frontdoor_command(args: argparse.Namespace, service: Any) -> dict[str, Any] | None:
    if args.command == "explore":
        return service.explore(
            task=args.task,
            updated_by=args.updated_by,
        )

    if args.command == "promote-exploration":
        return service.promote_exploration(
            exploration_id=args.exploration_id,
            explicit_current_topic=args.current_topic,
            explicit_topic_slug=args.topic_slug,
            explicit_topic=args.topic,
            updated_by=args.updated_by,
        )

    if args.command == "session-start":
        return service.start_chat_session(
            task=args.task,
            explicit_topic_slug=args.topic_slug,
            explicit_topic=args.topic,
            explicit_current_topic=args.current_topic,
            explicit_latest_topic=args.latest_topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            skill_queries=args.skill_query,
            max_auto_steps=args.max_auto_steps,
            research_mode=args.research_mode,
            load_profile=None if args.load_profile == "auto" else args.load_profile,
        )

    if args.command == "install-agent":
        return service.install_agent(
            agent=args.agent,
            scope=args.scope,
            target_root=args.target_root,
            force=not args.no_force,
            install_mcp=not args.no_mcp,
            mcp_profile=args.mcp_profile,
        )

    if args.command == "migrate-local-install":
        return service.migrate_local_install(
            workspace_root=args.workspace_root,
            backup_root=args.backup_root,
            agents=args.agent or None,
            with_mcp=args.with_mcp,
        )

    if args.command == "doctor":
        return service.ensure_cli_installed(workspace_root=args.workspace_root)

    return None
