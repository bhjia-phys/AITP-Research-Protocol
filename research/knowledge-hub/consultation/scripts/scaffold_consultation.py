#!/usr/bin/env python3
"""Scaffold a first-class L2 consultation bundle."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


VALID_STAGES = {"L1", "L3", "L4"}
VALID_CONTEXT_LAYERS = {"L0", "L1", "L2", "L3", "L4"}
VALID_UNIT_TYPES = {
    "atomic_note",
    "concept",
    "claim_card",
    "derivation_object",
    "method",
    "workflow",
    "bridge",
    "validation_pattern",
    "warning_note",
}
VALID_OUTCOMES = {
    "terminology_normalized",
    "candidate_narrowed",
    "validation_route_selected",
    "warning_attached",
    "contradiction_flagged",
    "needs_more_sources",
    "no_change",
}


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_csv(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("Expected at least one comma-separated value.")
    return items


def validate_membership(items: list[str], allowed: set[str], label: str) -> None:
    invalid = [item for item in items if item not in allowed]
    if invalid:
        joined = ", ".join(sorted(invalid))
        raise SystemExit(f"Invalid {label}: {joined}")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def dump_json(path: Path, payload: dict, dry_run: bool) -> None:
    text = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    if dry_run:
        print(f"=== {path} ===")
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict], dry_run: bool) -> None:
    text = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)
    if dry_run:
        print(f"=== {path} ===")
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scaffold request/result/application JSON for a first-class L2 consultation."
    )
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--stage", required=True, choices=sorted(VALID_STAGES))
    parser.add_argument(
        "--consultation-slug",
        required=True,
        help="Slug without the typed prefix; e.g. l3-my-candidate-shaping",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--context-id", required=True)
    parser.add_argument("--context-layer", required=True, choices=sorted(VALID_CONTEXT_LAYERS))
    parser.add_argument("--context-object-type", required=True)
    parser.add_argument("--context-path", required=True)
    parser.add_argument("--context-title", required=True)
    parser.add_argument("--context-summary", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--query-text", required=True)
    parser.add_argument(
        "--requested-unit-types",
        required=True,
        type=parse_csv,
        help="Comma-separated list of requested Layer 2 unit types.",
    )
    parser.add_argument("--requested-by", default="codex")
    parser.add_argument("--produced-by")
    parser.add_argument("--written-by")
    parser.add_argument("--retrieval-profile")
    parser.add_argument("--result-summary")
    parser.add_argument("--effect-on-work")
    parser.add_argument("--index-summary")
    parser.add_argument("--outcome", default="no_change", choices=sorted(VALID_OUTCOMES))
    parser.add_argument("--projection-path", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def with_optional(base: dict, key: str, value: str | None) -> dict:
    if value:
        base[key] = value
    return base


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    validate_membership(args.requested_unit_types, VALID_UNIT_TYPES, "requested unit type(s)")

    knowledge_hub_root = Path(__file__).resolve().parents[2]
    consultation_root = knowledge_hub_root / "consultation"
    topic_root = consultation_root / "topics" / args.topic_slug
    call_dir = topic_root / "calls" / f"consult-{args.consultation_slug}"
    request_path = call_dir / "request.json"
    result_path = call_dir / "result.json"
    application_path = call_dir / "application.json"
    index_path = topic_root / "consultation_index.jsonl"

    consultation_id = f"consult:{args.consultation_slug}"
    produced_by = args.produced_by or args.requested_by
    written_by = args.written_by or args.requested_by
    retrieval_profile = args.retrieval_profile or f"{args.stage}-default"
    timestamp = iso_now()

    context_ref = {
        "id": args.context_id,
        "layer": args.context_layer,
        "object_type": args.context_object_type,
        "path": args.context_path,
        "title": args.context_title,
        "summary": args.context_summary,
    }

    request = with_optional(
        {
            "consultation_id": consultation_id,
            "topic_slug": args.topic_slug,
            "stage": args.stage,
            "context_ref": context_ref,
            "purpose": args.purpose,
            "query_text": args.query_text,
            "requested_unit_types": args.requested_unit_types,
            "requested_by": args.requested_by,
            "requested_at": timestamp,
            "notes": "Scaffolded consultation request. Fill in any stage-specific details if needed.",
        },
        "run_id",
        args.run_id,
    )

    result = with_optional(
        {
            "consultation_id": consultation_id,
            "topic_slug": args.topic_slug,
            "stage": args.stage,
            "retrieval_profile": retrieval_profile,
            "query_text": args.query_text,
            "retrieved_refs": [],
            "expanded_edge_types": [],
            "result_summary": args.result_summary
            or f"Pending retrieval result for {consultation_id}.",
            "produced_by": produced_by,
            "produced_at": timestamp,
            "notes": "Scaffolded result. Replace placeholders with actual retrieved refs.",
        },
        "run_id",
        args.run_id,
    )

    application = with_optional(
        {
            "consultation_id": consultation_id,
            "topic_slug": args.topic_slug,
            "stage": args.stage,
            "context_ref": context_ref,
            "applied_refs": [],
            "deferred_refs": [],
            "effect_on_work": args.effect_on_work
            or "Pending application summary for this consultation.",
            "outcome": args.outcome,
            "projection_paths": args.projection_path,
            "written_by": written_by,
            "written_at": timestamp,
            "notes": "Scaffolded application. Update after the stage artifact is revised.",
        },
        "run_id",
        args.run_id,
    )

    request_rel = request_path.relative_to(knowledge_hub_root).as_posix()
    result_rel = result_path.relative_to(knowledge_hub_root).as_posix()
    application_rel = application_path.relative_to(knowledge_hub_root).as_posix()

    index_entry = with_optional(
        {
            "consultation_id": consultation_id,
            "topic_slug": args.topic_slug,
            "stage": args.stage,
            "status": "requested",
            "context_ref": context_ref,
            "request_path": request_rel,
            "result_path": result_rel,
            "application_path": application_rel,
            "summary": args.index_summary
            or f"Pending completion for {consultation_id}.",
        },
        "run_id",
        args.run_id,
    )

    existing_rows = load_jsonl(index_path)
    existing_ids = {row["consultation_id"] for row in existing_rows}
    if consultation_id in existing_ids and not args.force:
        raise SystemExit(
            f"{consultation_id} already exists in {index_path}. Use --force to replace it."
        )

    existing_files = [path for path in (request_path, result_path, application_path) if path.exists()]
    if existing_files and not args.force and not args.dry_run:
        joined = ", ".join(str(path) for path in existing_files)
        raise SystemExit(f"Refusing to overwrite existing files without --force: {joined}")

    updated_rows = [row for row in existing_rows if row["consultation_id"] != consultation_id]
    updated_rows.append(index_entry)

    dump_json(request_path, request, args.dry_run)
    dump_json(result_path, result, args.dry_run)
    dump_json(application_path, application, args.dry_run)
    dump_jsonl(index_path, updated_rows, args.dry_run)

    if args.dry_run:
        return 0

    print(f"Scaffolded consultation bundle for {consultation_id}")
    print(f"- request: {request_path}")
    print(f"- result: {result_path}")
    print(f"- application: {application_path}")
    print(f"- index: {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
