from __future__ import annotations

import argparse
import json
from typing import Any

from .aitp_service import AITPService


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AITP kernel CLI")
    parser.add_argument("--kernel-root")
    parser.add_argument("--repo-root")

    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Bootstrap or update an AITP topic")
    bootstrap.add_argument("--topic")
    bootstrap.add_argument("--topic-slug")
    bootstrap.add_argument("--statement")
    bootstrap.add_argument("--run-id")
    bootstrap.add_argument("--control-note")
    bootstrap.add_argument("--updated-by", default="aitp-cli")
    bootstrap.add_argument("--arxiv-id", action="append", default=[])
    bootstrap.add_argument("--local-note-path", action="append", default=[])
    bootstrap.add_argument("--skill-query", action="append", default=[])
    bootstrap.add_argument("--human-request")
    bootstrap.add_argument("--json", action="store_true")

    resume = subparsers.add_parser("resume", help="Resume an existing AITP topic")
    resume.add_argument("--topic-slug", required=True)
    resume.add_argument("--run-id")
    resume.add_argument("--control-note")
    resume.add_argument("--updated-by", default="aitp-cli")
    resume.add_argument("--arxiv-id", action="append", default=[])
    resume.add_argument("--local-note-path", action="append", default=[])
    resume.add_argument("--skill-query", action="append", default=[])
    resume.add_argument("--human-request")
    resume.add_argument("--json", action="store_true")

    audit = subparsers.add_parser("audit", help="Run the AITP conformance audit")
    audit.add_argument("--topic-slug", required=True)
    audit.add_argument("--phase", choices=["entry", "exit"], default="entry")
    audit.add_argument("--updated-by", default="aitp-cli")
    audit.add_argument("--json", action="store_true")

    ci_check = subparsers.add_parser("ci-check", help="CI-friendly alias for the AITP conformance audit")
    ci_check.add_argument("--topic-slug", required=True)
    ci_check.add_argument("--phase", choices=["entry", "exit"], default="exit")
    ci_check.add_argument("--updated-by", default="aitp-cli")
    ci_check.add_argument("--json", action="store_true")

    baseline = subparsers.add_parser("baseline", help="Scaffold baseline-reproduction artifacts")
    baseline.add_argument("--topic-slug", required=True)
    baseline.add_argument("--run-id", required=True)
    baseline.add_argument("--title", required=True)
    baseline.add_argument("--reference", required=True)
    baseline.add_argument("--agreement-criterion", required=True)
    baseline.add_argument("--baseline-kind", default="public_example")
    baseline.add_argument("--updated-by", default="aitp-cli")
    baseline.add_argument("--notes")
    baseline.add_argument("--json", action="store_true")

    atomize = subparsers.add_parser("atomize", help="Scaffold atomic-understanding artifacts")
    atomize.add_argument("--topic-slug", required=True)
    atomize.add_argument("--run-id", required=True)
    atomize.add_argument("--method-title", required=True)
    atomize.add_argument("--updated-by", default="aitp-cli")
    atomize.add_argument("--scope-note")
    atomize.add_argument("--json", action="store_true")

    operation_init = subparsers.add_parser("operation-init", help="Register a reusable operation for trust tracking")
    operation_init.add_argument("--topic-slug", required=True)
    operation_init.add_argument("--run-id")
    operation_init.add_argument("--title", required=True)
    operation_init.add_argument("--kind", required=True)
    operation_init.add_argument("--updated-by", default="aitp-cli")
    operation_init.add_argument("--summary")
    operation_init.add_argument("--notes")
    operation_init.add_argument("--reference", action="append", default=[])
    operation_init.add_argument("--source-path", action="append", default=[])
    operation_init.add_argument("--baseline-required", action="store_true")
    operation_init.add_argument("--no-baseline-required", action="store_true")
    operation_init.add_argument("--atomic-required", action="store_true")
    operation_init.add_argument("--no-atomic-required", action="store_true")
    operation_init.add_argument("--json", action="store_true")

    operation_update = subparsers.add_parser("operation-update", help="Update operation trust status or artifacts")
    operation_update.add_argument("--topic-slug", required=True)
    operation_update.add_argument("--run-id")
    operation_update.add_argument("--operation", required=True)
    operation_update.add_argument("--updated-by", default="aitp-cli")
    operation_update.add_argument("--summary")
    operation_update.add_argument("--notes")
    operation_update.add_argument("--baseline-status")
    operation_update.add_argument("--atomic-status")
    operation_update.add_argument("--reference", action="append", default=[])
    operation_update.add_argument("--source-path", action="append", default=[])
    operation_update.add_argument("--artifact-path", action="append", default=[])
    operation_update.add_argument("--json", action="store_true")

    trust_audit = subparsers.add_parser("trust-audit", help="Audit operation trust for a validation run")
    trust_audit.add_argument("--topic-slug", required=True)
    trust_audit.add_argument("--run-id")
    trust_audit.add_argument("--updated-by", default="aitp-cli")
    trust_audit.add_argument("--json", action="store_true")

    capability_audit = subparsers.add_parser("capability-audit", help="Audit runtime/operator capability state")
    capability_audit.add_argument("--topic-slug", required=True)
    capability_audit.add_argument("--updated-by", default="aitp-cli")
    capability_audit.add_argument("--json", action="store_true")

    loop = subparsers.add_parser("loop", help="Run the safe AITP auto-continue loop")
    loop.add_argument("--topic")
    loop.add_argument("--topic-slug")
    loop.add_argument("--statement")
    loop.add_argument("--run-id")
    loop.add_argument("--control-note")
    loop.add_argument("--updated-by", default="aitp-cli")
    loop.add_argument("--skill-query", action="append", default=[])
    loop.add_argument("--human-request")
    loop.add_argument("--max-auto-steps", type=int, default=4)
    loop.add_argument("--json", action="store_true")

    state = subparsers.add_parser("state", help="Read topic runtime state")
    state.add_argument("--topic-slug", required=True)
    state.add_argument("--json", action="store_true")

    install = subparsers.add_parser("install-agent", help="Install AITP wrappers for supported agents")
    install.add_argument("--agent", choices=["codex", "openclaw", "opencode", "all"], required=True)
    install.add_argument("--scope", choices=["user", "project"], default="user")
    install.add_argument("--target-root")
    install.add_argument("--no-force", action="store_true")
    install.add_argument("--no-mcp", action="store_true")
    install.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="Show AITP CLI install status")
    doctor.add_argument("--json", action="store_true")

    return parser


def _service_from_args(args: argparse.Namespace) -> AITPService:
    kwargs: dict[str, Any] = {}
    if args.kernel_root:
        kwargs["kernel_root"] = args.kernel_root
    if args.repo_root:
        kwargs["repo_root"] = args.repo_root
    return AITPService(**kwargs)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    service = _service_from_args(args)

    if args.command == "bootstrap":
        payload = service.orchestrate(
            topic_slug=args.topic_slug,
            topic=args.topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
            skill_queries=args.skill_query,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "resume":
        payload = service.orchestrate(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            arxiv_ids=args.arxiv_id,
            local_note_paths=args.local_note_path,
            skill_queries=args.skill_query,
            human_request=args.human_request,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "audit":
        payload = service.audit(topic_slug=args.topic_slug, phase=args.phase, updated_by=args.updated_by)
        _emit(payload, args.json)
        state = payload.get("conformance_state") or {}
        return 0 if state.get("overall_status") == "pass" else 1

    if args.command == "ci-check":
        payload = service.audit(topic_slug=args.topic_slug, phase=args.phase, updated_by=args.updated_by)
        _emit(payload, args.json)
        state = payload.get("conformance_state") or {}
        return 0 if state.get("overall_status") == "pass" else 1

    if args.command == "baseline":
        payload = service.scaffold_baseline(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            title=args.title,
            reference=args.reference,
            agreement_criterion=args.agreement_criterion,
            baseline_kind=args.baseline_kind,
            updated_by=args.updated_by,
            notes=args.notes,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "atomize":
        payload = service.scaffold_atomic_understanding(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            method_title=args.method_title,
            updated_by=args.updated_by,
            scope_note=args.scope_note,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "operation-init":
        baseline_required = None
        if args.baseline_required:
            baseline_required = True
        if args.no_baseline_required:
            baseline_required = False

        atomic_required = None
        if args.atomic_required:
            atomic_required = True
        if args.no_atomic_required:
            atomic_required = False

        payload = service.scaffold_operation(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            title=args.title,
            kind=args.kind,
            updated_by=args.updated_by,
            summary=args.summary,
            notes=args.notes,
            baseline_required=baseline_required,
            atomic_understanding_required=atomic_required,
            references=args.reference,
            source_paths=args.source_path,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "operation-update":
        payload = service.update_operation(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            operation=args.operation,
            updated_by=args.updated_by,
            summary=args.summary,
            notes=args.notes,
            baseline_status=args.baseline_status,
            atomic_understanding_status=args.atomic_status,
            references=args.reference,
            source_paths=args.source_path,
            artifact_paths=args.artifact_path,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "trust-audit":
        payload = service.audit_operation_trust(
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0 if payload.get("overall_status") == "pass" else 1

    if args.command == "capability-audit":
        payload = service.capability_audit(
            topic_slug=args.topic_slug,
            updated_by=args.updated_by,
        )
        _emit(payload, args.json)
        return 0 if payload.get("overall_status") == "ready" else 1

    if args.command == "loop":
        payload = service.run_topic_loop(
            topic_slug=args.topic_slug,
            topic=args.topic,
            statement=args.statement,
            run_id=args.run_id,
            control_note=args.control_note,
            updated_by=args.updated_by,
            human_request=args.human_request,
            skill_queries=args.skill_query,
            max_auto_steps=args.max_auto_steps,
        )
        _emit(payload, args.json)
        exit_state = (payload.get("exit_audit") or {}).get("conformance_state") or {}
        return 0 if exit_state.get("overall_status") == "pass" else 1

    if args.command == "state":
        payload = {"topic_state": service.get_runtime_state(args.topic_slug)}
        _emit(payload, args.json)
        return 0

    if args.command == "install-agent":
        payload = service.install_agent(
            agent=args.agent,
            scope=args.scope,
            target_root=args.target_root,
            force=not args.no_force,
            install_mcp=not args.no_mcp,
        )
        _emit(payload, args.json)
        return 0

    if args.command == "doctor":
        payload = service.ensure_cli_installed()
        _emit(payload, args.json)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
