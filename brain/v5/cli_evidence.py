"""Focused CLI parser and dispatcher for evidence writes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.evidence import record_evidence
from brain.v5.evidence_basis_inputs import load_pinned_record_refs_file
from brain.v5.public_surfaces import require_valid_public_surface


def add_evidence_parser(subparsers) -> None:
    evidence = subparsers.add_parser("evidence")
    commands = evidence.add_subparsers(dest="evidence_command", required=True)
    record = commands.add_parser("record")
    record.add_argument("--topic", required=True, dest="topic_id")
    record.add_argument("--claim", required=True, dest="claim_id")
    record.add_argument("--type", required=True, dest="evidence_type")
    record.add_argument("--status", required=True)
    record.add_argument("--summary", required=True)
    record.add_argument("--supports-output", action="append", default=[], dest="supports_outputs")
    record.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    record.add_argument("--tool-run-id", action="append", default=[], dest="tool_run_ids")
    record.add_argument(
        "--validation-result-id",
        action="append",
        default=[],
        dest="validation_result_ids",
    )
    record.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    record.add_argument("--support-basis-json-file", default="")
    record.add_argument("--trace-context-json-file", default="")
    record.add_argument("--body-file", default="")


def dispatch_evidence_command(args, ws) -> dict:
    if args.command != "evidence" or args.evidence_command != "record":
        raise ValueError("unsupported evidence command")
    evidence = record_evidence(
        ws,
        topic_id=args.topic_id,
        claim_id=args.claim_id,
        evidence_type=args.evidence_type,
        status=args.status,
        summary=args.summary,
        supports_outputs=args.supports_outputs,
        source_refs=args.source_refs,
        tool_run_ids=args.tool_run_ids,
        validation_result_ids=args.validation_result_ids,
        artifact_ids=args.artifact_ids,
        support_basis_refs=load_pinned_record_refs_file(
            args.support_basis_json_file, field_name="support_basis_refs"
        ),
        trace_context_refs=load_pinned_record_refs_file(
            args.trace_context_json_file, field_name="trace_context_refs"
        ),
        body=_read_body_file(args.body_file),
    )
    return {
        "ok": True,
        **require_valid_public_surface(
            "evidence_record", {"ok": True, **asdict(evidence)}
        ),
    }


def _read_body_file(path: str) -> str | None:
    if not str(path or "").strip():
        return None
    source = Path(path).expanduser()
    try:
        return source.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"could not read evidence body file {source}: {exc}") from exc
