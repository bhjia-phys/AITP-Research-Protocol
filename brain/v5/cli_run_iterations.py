"""CLI handlers for run-local iteration continuity."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_runs import (
    record_research_run_event,
    research_run_event_payload,
    research_run_payload,
    start_research_run,
    update_research_run,
)
from brain.v5.run_iterations import record_run_iteration


def add_run_parser(sp) -> None:
    run = sp.add_parser("run"); runs = run.add_subparsers(dest="run_command", required=True)
    research = runs.add_parser("research")
    research_sub = research.add_subparsers(dest="research_run_command", required=True)
    start = research_sub.add_parser("start")
    start.add_argument("--topic", required=True, dest="topic_id")
    start.add_argument("--objective", required=True)
    start.add_argument("--question", required=True, dest="research_question")
    start.add_argument("--operator", required=True)
    start.add_argument("--title", default="")
    start.add_argument("--claim", default="", dest="claim_id")
    start.add_argument("--session", default="", dest="session_id")
    start.add_argument("--hypothesis", default="")
    start.add_argument("--phase", default="planning")
    start.add_argument("--metadata-json", default="{}")

    update = research_sub.add_parser("update")
    update.add_argument("--run", required=True, dest="run_id")
    update.add_argument("--topic", required=True, dest="topic_id")
    update.add_argument("--operator", required=True)
    update.add_argument("--status", default="")
    update.add_argument("--phase", default="")
    update.add_argument("--terminal-answer-state", default="")
    update.add_argument("--stop-reason", default="")
    update.add_argument("--aitp-slice-ref", action="append", default=[], dest="aitp_slice_refs")
    update.add_argument("--action-ref", action="append", default=[], dest="action_refs")
    update.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    update.add_argument("--validation-ref", action="append", default=[], dest="validation_refs")
    update.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    update.add_argument("--answer-packet-ref", default="")
    update.add_argument("--event-type", default="status_changed")
    update.add_argument("--event-summary", default="")
    update.add_argument("--payload-json", default="{}")

    event = runs.add_parser("event")
    events = event.add_subparsers(dest="research_run_event_command", required=True)
    rec_event = events.add_parser("record")
    rec_event.add_argument("--run", required=True, dest="run_id")
    rec_event.add_argument("--topic", required=True, dest="topic_id")
    rec_event.add_argument("--operator", required=True)
    rec_event.add_argument("--type", required=True, dest="event_type")
    rec_event.add_argument("--summary", required=True)
    rec_event.add_argument("--status", default="recorded")
    rec_event.add_argument("--phase", default="")
    rec_event.add_argument("--claim", default="", dest="claim_id")
    rec_event.add_argument("--session", default="", dest="session_id")
    rec_event.add_argument("--action-id", default="")
    rec_event.add_argument("--action-ref", default="")
    rec_event.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    rec_event.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    rec_event.add_argument("--validation-ref", action="append", default=[], dest="validation_refs")
    rec_event.add_argument("--artifact-ref", action="append", default=[], dest="artifact_refs")
    rec_event.add_argument("--payload-json", default="{}")

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
    if args.run_command == "research" and args.research_run_command == "start":
        record = start_research_run(
            ws,
            topic_id=args.topic_id,
            objective=args.objective,
            research_question=args.research_question,
            operator=args.operator,
            title=args.title,
            claim_id=args.claim_id,
            session_id=args.session_id,
            hypothesis=args.hypothesis,
            phase=args.phase,
            metadata=_j(args.metadata_json),
        )
        return require_valid_public_surface("research_run_record", research_run_payload(record))
    if args.run_command == "research" and args.research_run_command == "update":
        record = update_research_run(
            ws,
            run_id=args.run_id,
            topic_id=args.topic_id,
            operator=args.operator,
            status=args.status or None,
            phase=args.phase or None,
            terminal_answer_state=args.terminal_answer_state or None,
            stop_reason=args.stop_reason,
            aitp_slice_refs=args.aitp_slice_refs or None,
            action_refs=args.action_refs or None,
            evidence_refs=args.evidence_refs or None,
            validation_refs=args.validation_refs or None,
            source_refs=args.source_refs or None,
            answer_packet_ref=args.answer_packet_ref if args.answer_packet_ref else None,
            event_type=args.event_type,
            event_summary=args.event_summary,
            payload=_j(args.payload_json),
        )
        return require_valid_public_surface("research_run_record", research_run_payload(record))
    if args.run_command == "event" and args.research_run_event_command == "record":
        record = record_research_run_event(
            ws,
            run_id=args.run_id,
            topic_id=args.topic_id,
            operator=args.operator,
            event_type=args.event_type,
            summary=args.summary,
            status=args.status,
            phase=args.phase,
            claim_id=args.claim_id,
            session_id=args.session_id,
            action_id=args.action_id,
            action_ref=args.action_ref,
            source_refs=args.source_refs,
            evidence_refs=args.evidence_refs,
            validation_refs=args.validation_refs,
            artifact_refs=args.artifact_refs,
            payload=_j(args.payload_json),
        )
        return require_valid_public_surface("research_run_event_record", research_run_event_payload(record))
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


def _j(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("expected a JSON object")
    return payload
