"""CLI handlers for vNext lane exemplars."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.lane_exemplars import build_lane_exemplar_manifest, record_lane_exemplar
from brain.v5.public_surfaces import require_valid_public_surface


def add_exemplar_parser(sp) -> None:
    ex = sp.add_parser("exemplar"); exs = ex.add_subparsers(dest="exemplar_command", required=True)
    lane = exs.add_parser("lane"); lanes = lane.add_subparsers(dest="lane_exemplar_command", required=True)
    rec = lanes.add_parser("record")
    rec.add_argument("--topic", required=True, dest="topic_id")
    rec.add_argument("--lane", required=True)
    rec.add_argument("--title", required=True)
    rec.add_argument("--summary", required=True)
    rec.add_argument("--claim", default="", dest="claim_id")
    rec.add_argument("--run", default="", dest="run_id")
    rec.add_argument("--gate", action="append", default=[], dest="gates_demonstrated")
    rec.add_argument("--artifact-ref", action="append", default=[], dest="artifact_refs")
    rec.add_argument("--trust-boundary", default="")
    rec.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    rec.add_argument("--status", default="candidate")
    lanes.add_parser("manifest")


def dispatch_exemplar_command(args, ws) -> dict:
    if args.exemplar_command == "lane" and args.lane_exemplar_command == "record":
        record = record_lane_exemplar(
            ws,
            topic_id=args.topic_id,
            lane=args.lane,
            title=args.title,
            summary=args.summary,
            claim_id=args.claim_id,
            run_id=args.run_id,
            gates_demonstrated=args.gates_demonstrated,
            artifact_refs=args.artifact_refs,
            trust_boundary=args.trust_boundary,
            source_refs=args.source_refs,
            status=args.status,
        )
        return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})
    if args.exemplar_command == "lane" and args.lane_exemplar_command == "manifest":
        return require_valid_public_surface("lane_exemplar_manifest", build_lane_exemplar_manifest(ws))
    raise SystemExit(f"unsupported exemplar command: {args.exemplar_command}")
