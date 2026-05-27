"""CLI handlers for topic-local operator checkpoints."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.operator_checkpoint import answer_operator_checkpoint, request_operator_checkpoint
from brain.v5.public_surfaces import require_valid_public_surface


def add_operator_parser(sp) -> None:
    op = sp.add_parser("operator"); ops = op.add_subparsers(dest="operator_command", required=True)
    cp = ops.add_parser("checkpoint"); cps = cp.add_subparsers(dest="operator_checkpoint_command", required=True)

    req = cps.add_parser("request")
    req.add_argument("--topic", required=True, dest="topic_id")
    req.add_argument("--kind", required=True, dest="checkpoint_kind")
    req.add_argument("--question", required=True)
    req.add_argument("--option", action="append", required=True, dest="options")
    req.add_argument("--requested-by", required=True)
    req.add_argument("--claim", default="", dest="claim_id")
    req.add_argument("--human-checkpoint", default="", dest="human_checkpoint_id")
    req.add_argument("--source-ref", action="append", default=[], dest="source_refs")

    ans = cps.add_parser("answer")
    ans.add_argument("checkpoint_id")
    ans.add_argument("--topic", required=True, dest="topic_id")
    ans.add_argument("--selected-option", default="")
    ans.add_argument("--rationale", required=True)
    ans.add_argument("--answered-by", required=True)
    ans.add_argument("--status", default="answered")


def dispatch_operator_command(args, ws) -> dict:
    if args.operator_command == "checkpoint" and args.operator_checkpoint_command == "request":
        checkpoint = request_operator_checkpoint(
            ws,
            topic_id=args.topic_id,
            checkpoint_kind=args.checkpoint_kind,
            question=args.question,
            options=args.options,
            requested_by=args.requested_by,
            claim_id=args.claim_id,
            human_checkpoint_id=args.human_checkpoint_id,
            source_refs=args.source_refs,
        )
        return require_valid_public_surface("operator_checkpoint_record", {"ok": True, **asdict(checkpoint)})
    if args.operator_command == "checkpoint" and args.operator_checkpoint_command == "answer":
        checkpoint = answer_operator_checkpoint(
            ws,
            topic_id=args.topic_id,
            checkpoint_id=args.checkpoint_id,
            selected_option=args.selected_option,
            rationale=args.rationale,
            answered_by=args.answered_by,
            status=args.status,
        )
        return require_valid_public_surface("operator_checkpoint_record", {"ok": True, **asdict(checkpoint)})
    raise SystemExit(f"unsupported operator command: {args.operator_command}")
