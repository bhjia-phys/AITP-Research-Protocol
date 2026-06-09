"""CLI dispatch for literature intake assistant surfaces."""

from __future__ import annotations

import argparse

from brain.v5.literature_comparison_draft import build_literature_comparison_draft
from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake
from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff
from brain.v5.public_surfaces import require_valid_public_surface


def add_literature_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("literature")
    sub = parser.add_subparsers(dest="literature_command", required=True)
    _add_intake_args(sub.add_parser("suggest-intake"))
    _add_intake_args(sub.add_parser("record-candidate"))
    _add_intake_args(sub.add_parser("source-review-handoff"))
    _add_comparison_draft_args(sub.add_parser("comparison-draft"))


def dispatch_literature_command(args: argparse.Namespace, ws) -> dict:
    if args.literature_command == "comparison-draft":
        return require_valid_public_surface(
            "literature_comparison_draft",
            build_literature_comparison_draft(
                ws,
                session_id=args.session_id,
                comparison_question=args.comparison_question,
                source_refs=args.source_refs,
                dimensions=args.dimensions,
                optional_claim_id=args.optional_claim_id,
                rationale=args.rationale,
            ),
        )
    kwargs = {
        "session_id": args.session_id,
        "uri": args.uri,
        "label": args.label,
        "external_id": args.external_id,
        "short_summary": args.short_summary,
        "detected_relevance": args.detected_relevance,
        "optional_claim_id": args.optional_claim_id,
        "scoped_output": args.scoped_output,
    }
    if args.literature_command == "suggest-intake":
        return require_valid_public_surface(
            "literature_intake_suggestion",
            suggest_literature_intake(ws, **kwargs),
        )
    if args.literature_command == "record-candidate":
        return require_valid_public_surface(
            "literature_intake_record_result",
            record_literature_candidate(ws, **kwargs),
        )
    if args.literature_command == "source-review-handoff":
        return require_valid_public_surface(
            "literature_source_review_handoff",
            build_literature_source_review_handoff(ws, **kwargs, reviewed_refs=args.reviewed_refs),
        )
    raise SystemExit(f"unsupported literature command: {args.literature_command}")


def _add_intake_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session", required=True, dest="session_id")
    parser.add_argument("--uri", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--external-id", default="")
    parser.add_argument("--summary", required=True, dest="short_summary")
    parser.add_argument("--detected-relevance", required=True)
    parser.add_argument("--claim", default="", dest="optional_claim_id")
    parser.add_argument("--scoped-output", default="")
    parser.add_argument("--reviewed-ref", action="append", default=[], dest="reviewed_refs")


def _add_comparison_draft_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session", required=True, dest="session_id")
    parser.add_argument("--question", required=True, dest="comparison_question")
    parser.add_argument("--source-ref", action="append", required=True, dest="source_refs")
    parser.add_argument("--dimension", action="append", default=[], dest="dimensions")
    parser.add_argument("--claim", default="", dest="optional_claim_id")
    parser.add_argument("--rationale", default="")
