"""CLI handlers for run-local iteration continuity."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.run_iterations import record_run_iteration


def add_run_parser(sp) -> None:
    run = sp.add_parser("run"); runs = run.add_subparsers(dest="run_command", required=True)
    iteration = runs.add_parser("iteration")
    its = iteration.add_subparsers(dest="run_iteration_command", required=True)
    rec = its.add_parser("record")
    rec.add_argument("--topic", required=True, dest="topic_id")
    rec.add_argument("--run", required=True, dest="run_id")
    rec.add_argument("--iteration", required=True, dest="iteration_id")
    rec.add_argument("--plan-summary", required=True)
    rec.add_argument("--deliverable", action="append", default=[], dest="deliverables")
    rec.add_argument("--check", action="append", default=[], dest="checks")
    rec.add_argument("--stop-rule", action="append", default=[], dest="stop_rules")
    rec.add_argument("--l4-return-summary", default="")
    rec.add_argument("--l4-artifact-ref", action="append", default=[], dest="l4_artifact_refs")
    rec.add_argument("--l3-synthesis-summary", default="")
    rec.add_argument("--decision", default="")
    rec.add_argument("--status", default="planned")
    rec.add_argument("--claim", default="", dest="claim_id")
    rec.add_argument("--source-ref", action="append", default=[], dest="source_refs")


def dispatch_run_command(args, ws) -> dict:
    if args.run_command == "iteration" and args.run_iteration_command == "record":
        record = record_run_iteration(
            ws,
            topic_id=args.topic_id,
            run_id=args.run_id,
            iteration_id=args.iteration_id,
            plan_summary=args.plan_summary,
            deliverables=args.deliverables,
            checks=args.checks,
            stop_rules=args.stop_rules,
            l4_return_summary=args.l4_return_summary,
            l4_artifact_refs=args.l4_artifact_refs,
            l3_synthesis_summary=args.l3_synthesis_summary,
            decision=args.decision,
            status=args.status,
            claim_id=args.claim_id,
            source_refs=args.source_refs,
        )
        return require_valid_public_surface("run_iteration_record", {"ok": True, **asdict(record)})
    raise SystemExit(f"unsupported run command: {args.run_command}")
