"""CLI handlers for topic status surfaces."""

from __future__ import annotations

from brain.v5.context_pack import build_aitp_context_pack
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.hpc_cockpit import build_hpc_cockpit
from brain.v5.lane_contracts import lane_contract_payload, record_lane_contract
from brain.v5.note_outline import compile_note_outline
from brain.v5.objective_graph import build_compact_brief, build_objective_graph
from brain.v5.qsgw_cockpit import (
    DEFAULT_QSGW_TOPIC_ID,
    compact_qsgw_cockpit_bundle,
    write_qsgw_cockpit_surfaces,
)
from brain.v5.research_cockpit import compact_research_cockpit_bundle, write_research_cockpit_surfaces
from brain.v5.research_distillation import build_research_distillation_candidates
from brain.v5.topic_status import compact_topic_status_bundle, write_topic_status_surfaces
from brain.v5.vnext_readiness import build_vnext_readiness_manifest, compact_vnext_readiness_manifest


def add_status_parser(sp) -> None:
    status = sp.add_parser("status"); ss = status.add_subparsers(dest="status_command", required=True)
    topic = ss.add_parser("topic")
    topic.add_argument("session_id")
    topic.add_argument("--compact", "--progress", action="store_true", dest="compact")
    objective = ss.add_parser("objective-graph")
    objective.add_argument("session_id")
    compact_brief = ss.add_parser("compact-brief")
    compact_brief.add_argument("session_id")
    compact_brief.add_argument("--max-lines", type=int, default=40)
    context_pack = ss.add_parser("context-pack")
    context_pack.add_argument("session_id")
    context_pack.add_argument("--max-lines", type=int, default=60)
    context_pack.add_argument("--candidate-limit", type=int, default=3)
    context_pack.add_argument("--task-profile", default="")
    distillation = ss.add_parser("distillation-candidates")
    distillation.add_argument("session_id")
    distillation.add_argument("--limit", type=int, default=8)
    note = ss.add_parser("note-outline")
    note.add_argument("session_id")
    note.add_argument("--style", default="jhep")
    note.add_argument("--candidate-limit", type=int, default=8)
    cockpit = ss.add_parser("qsgw-cockpit")
    cockpit.add_argument("--topic", default=DEFAULT_QSGW_TOPIC_ID, dest="topic_id")
    cockpit.add_argument("--reports-dir", default="")
    cockpit.add_argument("--scripts-dir", default="")
    cockpit.add_argument("--compact", "--progress", action="store_true", dest="compact")
    research = ss.add_parser("research-cockpit")
    research.add_argument("--compact", "--progress", action="store_true", dest="compact")
    vnext = ss.add_parser("vnext-readiness")
    vnext.add_argument("--compact", "--progress", action="store_true", dest="compact")
    hpc = ss.add_parser("hpc-cockpit")
    hpc.add_argument("--topic", default="", dest="topic_id")
    lane = ss.add_parser("lane-contract")
    lane.add_argument("--topic", default="", dest="topic_id")
    lane.add_argument("--campaign", default="")
    lane.add_argument("--forbidden-root", action="append", default=[], dest="forbidden_roots")
    lane.add_argument("--preferred-root", action="append", default=[], dest="preferred_clean_roots")
    lane.add_argument("--final-rule", action="append", default=[], dest="final_rules")
    lane.add_argument("--trust-update-forbidden", action="store_true", dest="trust_update_forbidden")


def dispatch_status_command(args, ws) -> dict:
    if args.status_command == "topic":
        bundle = require_valid_public_surface(
            "topic_status_bundle",
            write_topic_status_surfaces(ws, session_id=args.session_id),
        )
        if getattr(args, "compact", False):
            return compact_topic_status_bundle(bundle)
        return bundle
    if args.status_command == "objective-graph":
        return require_valid_public_surface("objective_graph", build_objective_graph(ws, args.session_id))
    if args.status_command == "compact-brief":
        return require_valid_public_surface(
            "compact_execution_brief",
            build_compact_brief(ws, args.session_id, max_lines=args.max_lines),
        )
    if args.status_command == "context-pack":
        return require_valid_public_surface(
            "aitp_context_pack",
            build_aitp_context_pack(
                ws,
                args.session_id,
                max_lines=args.max_lines,
                candidate_limit=args.candidate_limit,
                task_profile=args.task_profile,
            ),
        )
    if args.status_command == "distillation-candidates":
        return require_valid_public_surface(
            "research_distillation_candidates",
            build_research_distillation_candidates(ws, args.session_id, limit=args.limit),
        )
    if args.status_command == "note-outline":
        return require_valid_public_surface(
            "note_outline",
            compile_note_outline(ws, args.session_id, style=args.style, candidate_limit=args.candidate_limit),
        )
    if args.status_command == "vnext-readiness":
        manifest = require_valid_public_surface("vnext_readiness_manifest", build_vnext_readiness_manifest(ws))
        if getattr(args, "compact", False):
            return compact_vnext_readiness_manifest(manifest)
        return manifest
    if args.status_command == "qsgw-cockpit":
        bundle = require_valid_public_surface(
            "qsgw_cockpit_bundle",
            write_qsgw_cockpit_surfaces(
                ws,
                topic_id=args.topic_id,
                reports_dir=args.reports_dir or None,
                scripts_dir=args.scripts_dir or None,
            ),
        )
        if getattr(args, "compact", False):
            return compact_qsgw_cockpit_bundle(bundle)
        return bundle
    if args.status_command == "research-cockpit":
        bundle = require_valid_public_surface(
            "research_cockpit_bundle",
            write_research_cockpit_surfaces(ws),
        )
        if getattr(args, "compact", False):
            return compact_research_cockpit_bundle(bundle)
        return bundle
    if args.status_command == "hpc-cockpit":
        return require_valid_public_surface("hpc_cockpit", build_hpc_cockpit(ws, args.topic_id))
    if args.status_command == "lane-contract":
        record = record_lane_contract(
            ws,
            topic_id=args.topic_id,
            campaign=args.campaign,
            forbidden_roots=args.forbidden_roots,
            preferred_clean_roots=args.preferred_clean_roots,
            final_rules=args.final_rules,
            trust_update_forbidden=args.trust_update_forbidden,
        )
        return require_valid_public_surface("lane_contract_record", lane_contract_payload(record))
    raise SystemExit(f"unsupported status command: {args.status_command}")
