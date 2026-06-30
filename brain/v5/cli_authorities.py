"""CLI wiring for research authority records."""

from __future__ import annotations

import json
from dataclasses import asdict

from brain.v5.authorities import authority_registry_payload, record_authority
from brain.v5.public_surfaces import require_valid_public_surface


def add_authority_parser(sp) -> None:
    parser = sp.add_parser("authority")
    sub = parser.add_subparsers(dest="authority_command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--topic", required=True, dest="topic_id")
    record.add_argument("--type", required=True, dest="authority_type")
    record.add_argument("--statement", required=True, dest="authority_statement")
    record.add_argument("--work-package", default="")
    record.add_argument("--claim", default="", dest="claim_id")
    record.add_argument("--scope-json", default="{}")
    record.add_argument("--generator-set", default="")
    record.add_argument("--closure-envelope", default="")
    record.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    record.add_argument("--source-ref", action="append", default=[], dest="source_refs")
    record.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    record.add_argument("--linked-records-json", default="{}")
    record.add_argument("--limitation", action="append", default=[], dest="limitations")
    record.add_argument("--status", default="research_authority_not_trust_promotion")

    listing = sub.add_parser("list")
    listing.add_argument("--topic", required=True, dest="topic_id")
    listing.add_argument("--type", default="", dest="authority_type")
    listing.add_argument("--work-package", default="")
    listing.add_argument("--include-inactive", action="store_true")


def dispatch_authority_command(args, ws) -> dict:
    if args.authority_command == "record":
        record = record_authority(
            ws,
            topic_id=args.topic_id,
            authority_type=args.authority_type,
            authority_statement=args.authority_statement,
            work_package=args.work_package,
            claim_id=args.claim_id,
            scope=_j(args.scope_json),
            generator_set=args.generator_set,
            closure_envelope=args.closure_envelope,
            evidence_refs=args.evidence_refs,
            source_refs=args.source_refs,
            artifact_ids=args.artifact_ids,
            linked_records=_j(args.linked_records_json),
            limitations=args.limitations,
            status=args.status,
        )
        return require_valid_public_surface("authority_record", {"ok": True, **asdict(record)})
    if args.authority_command == "list":
        return require_valid_public_surface(
            "authority_registry",
            authority_registry_payload(
                ws,
                topic_id=args.topic_id,
                authority_type=args.authority_type,
                work_package=args.work_package,
                include_inactive=args.include_inactive,
            ),
        )
    raise SystemExit(f"unsupported authority command: {args.authority_command}")


def _j(value: str) -> dict:
    parsed = json.loads(value or "{}")
    if not isinstance(parsed, dict):
        raise ValueError("expected a JSON object")
    return parsed
