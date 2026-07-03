"""CLI handlers for vNext lane exemplars."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.lane_exemplars import (
    build_lane_exemplar_manifest,
    record_lane_exemplar,
    record_librpa_code_backed_algorithm_exemplar,
)
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
    rec.add_argument("--domain-pack-ref", action="append", default=[], dest="domain_pack_refs")
    rec.add_argument("--context-profile-ref", action="append", default=[], dest="context_profile_refs")
    rec.add_argument("--skill-ref", action="append", default=[], dest="skill_refs")
    rec.add_argument("--surface-ref", action="append", default=[], dest="surface_refs")
    rec.add_argument("--validation-surface-ref", action="append", default=[], dest="validation_surface_refs")
    rec.add_argument("--workflow-step", action="append", default=[], dest="workflow_steps")
    rec.add_argument("--failure-mode", action="append", default=[], dest="failure_modes")
    rec.add_argument("--forbidden-use", action="append", default=[], dest="forbidden_uses")
    rec.add_argument("--can-say", action="append", default=[], dest="can_say")
    rec.add_argument("--cannot-say", action="append", default=[], dest="cannot_say")
    rec.add_argument("--required-next-record", action="append", default=[], dest="required_next_records")
    rec.add_argument("--promotion-blocker", action="append", default=[], dest="promotion_blockers")
    rec.add_argument("--trust-boundary", default="")
    rec.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    rec.add_argument("--status", default="candidate")
    librpa = lanes.add_parser("record-librpa-code")
    librpa.add_argument("--topic", required=True, dest="topic_id")
    librpa.add_argument("--claim", default="", dest="claim_id")
    librpa.add_argument("--run", default="", dest="run_id")
    librpa.add_argument("--status", default="accepted")
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
            domain_pack_refs=args.domain_pack_refs,
            context_profile_refs=args.context_profile_refs,
            skill_refs=args.skill_refs,
            surface_refs=args.surface_refs,
            validation_surface_refs=args.validation_surface_refs,
            workflow_steps=_workflow_step_items(args.workflow_steps),
            failure_modes=_failure_mode_items(args.failure_modes),
            forbidden_uses=args.forbidden_uses,
            can_say=args.can_say,
            cannot_say=args.cannot_say,
            required_next_records=args.required_next_records,
            promotion_blockers=args.promotion_blockers,
            trust_boundary=args.trust_boundary,
            source_refs=args.source_refs,
            status=args.status,
        )
        return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})
    if args.exemplar_command == "lane" and args.lane_exemplar_command == "record-librpa-code":
        record = record_librpa_code_backed_algorithm_exemplar(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            run_id=args.run_id,
            status=args.status,
        )
        return require_valid_public_surface("lane_exemplar_record", {"ok": True, **asdict(record)})
    if args.exemplar_command == "lane" and args.lane_exemplar_command == "manifest":
        return require_valid_public_surface("lane_exemplar_manifest", build_lane_exemplar_manifest(ws))
    raise SystemExit(f"unsupported exemplar command: {args.exemplar_command}")


def _workflow_step_items(values: list[str]) -> list[dict[str, str]]:
    return [
        {
            "step_id": f"manual_step_{index}",
            "purpose": value,
        }
        for index, value in enumerate(values, start=1)
    ]


def _failure_mode_items(values: list[str]) -> list[dict[str, str]]:
    return [
        {
            "failure_id": value,
            "required_basis": "manual review basis required",
        }
        for value in values
    ]
