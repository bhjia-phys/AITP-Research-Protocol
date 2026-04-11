from __future__ import annotations

import argparse
from typing import Any

from .l2_staging import stage_provisional_l2_entry


L2_GRAPH_COMMANDS = {
    "stage-l2-provisional",
    "seed-l2-direction",
    "consult-l2",
}


def register_l2_graph_commands(subparsers: argparse._SubParsersAction[Any]) -> None:
    stage_l2 = subparsers.add_parser("stage-l2-provisional", help="Write provisional L2-adjacent output into canonical staging")
    stage_l2.add_argument("--topic-slug", required=True)
    stage_l2.add_argument("--entry-kind", required=True)
    stage_l2.add_argument("--title", required=True)
    stage_l2.add_argument("--summary", required=True)
    stage_l2.add_argument("--source-artifact-path", action="append", default=[])
    stage_l2.add_argument("--notes")
    stage_l2.add_argument("--updated-by", default="aitp-cli")
    stage_l2.add_argument("--json", action="store_true")

    seed_l2_direction = subparsers.add_parser(
        "seed-l2-direction",
        help="Seed one bounded MVP L2 direction into canonical graph storage",
    )
    seed_l2_direction.add_argument("--direction", required=True)
    seed_l2_direction.add_argument("--updated-by", default="aitp-cli")
    seed_l2_direction.add_argument("--json", action="store_true")

    consult_l2 = subparsers.add_parser(
        "consult-l2",
        help="Consult bounded canonical L2 memory through the MVP retrieval path",
    )
    consult_l2.add_argument("--query-text", required=True)
    consult_l2.add_argument(
        "--retrieval-profile",
        required=True,
        choices=["l1_provisional_understanding", "l3_candidate_formation", "l4_adjudication"],
    )
    consult_l2.add_argument("--max-primary-hits", type=int)
    consult_l2.add_argument("--include-staging", action="store_true")
    consult_l2.add_argument("--topic-slug")
    consult_l2.add_argument("--stage", choices=["L1", "L3", "L4"], default="L3")
    consult_l2.add_argument("--run-id")
    consult_l2.add_argument("--updated-by", default="aitp-cli")
    consult_l2.add_argument("--record-consultation", action="store_true")
    consult_l2.add_argument("--json", action="store_true")


def dispatch_l2_graph_command(args: argparse.Namespace, service: Any) -> dict[str, Any] | None:
    if args.command == "stage-l2-provisional":
        return stage_provisional_l2_entry(
            service.kernel_root,
            topic_slug=args.topic_slug,
            entry_kind=args.entry_kind,
            title=args.title,
            summary=args.summary,
            source_artifact_paths=args.source_artifact_path,
            notes=args.notes,
            staged_by=args.updated_by,
        )

    if args.command == "seed-l2-direction":
        return service.seed_l2_direction(
            direction=args.direction,
            updated_by=args.updated_by,
        )

    if args.command == "consult-l2":
        return service.consult_l2(
            query_text=args.query_text,
            retrieval_profile=args.retrieval_profile,
            max_primary_hits=args.max_primary_hits,
            include_staging=args.include_staging,
            topic_slug=args.topic_slug,
            stage=args.stage,
            run_id=args.run_id,
            updated_by=args.updated_by,
            record_consultation=args.record_consultation,
        )

    return None
