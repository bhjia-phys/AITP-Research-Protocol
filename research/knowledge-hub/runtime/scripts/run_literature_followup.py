#!/usr/bin/env python3
"""Run one bounded literature follow-up search and register arXiv sources."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "literature-followup"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        stripped = str(value).strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            deduped.append(stripped)
    return deduped


def receipt_matches_existing(row: dict, args: argparse.Namespace) -> bool:
    if row.get("query") != args.query or row.get("target_source_type") != args.target_source_type:
        return False
    if dedupe_strings(list(row.get("parent_gap_ids") or [])) != dedupe_strings(args.parent_gap_id):
        return False
    existing_parent_followups = dedupe_strings(
        list(row.get("parent_followup_task_ids") or [])
        + ([str(row.get("parent_followup_task_id") or "").strip()] if str(row.get("parent_followup_task_id") or "").strip() else [])
    )
    if existing_parent_followups != dedupe_strings(args.parent_followup_task_id):
        return False
    if dedupe_strings(list(row.get("reentry_targets") or [])) != dedupe_strings(args.reentry_target):
        return False
    if dedupe_strings(list(row.get("supporting_regression_question_ids") or [])) != dedupe_strings(
        args.supporting_regression_question_id
    ):
        return False
    return row.get("status") == "completed"


def fetch_url(url: str, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def python_command() -> list[str]:
    executable = str(getattr(sys, "executable", "") or "").strip()
    if executable:
        return [executable]

    for candidate in ("python3", "python"):
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved]

    launcher = shutil.which("py")
    if launcher:
        return [launcher, "-3"]

    return ["python"]


def search_arxiv(query: str, max_results: int) -> list[dict]:
    encoded = urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": max(max_results, 1)}
    )
    url = f"https://export.arxiv.org/api/query?{encoded}"
    payload = fetch_url(url).decode("utf-8")
    root = ET.fromstring(payload)
    results: list[dict] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        identifier = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
        versioned_id = identifier.rsplit("/", 1)[-1] if identifier else ""
        title = entry.findtext("atom:title", default="", namespaces=ATOM_NS).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS).strip()
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
        results.append(
            {
                "arxiv_id": versioned_id,
                "title": title,
                "published": published,
                "summary": " ".join(summary.split())[:500],
            }
        )
    return [result for result in results if result.get("arxiv_id")]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--priority", default="medium")
    parser.add_argument("--target-source-type", default="paper")
    parser.add_argument("--max-results", type=int, default=2)
    parser.add_argument("--parent-gap-id", action="append", default=[])
    parser.add_argument("--parent-followup-task-id", action="append", default=[])
    parser.add_argument("--reentry-target", action="append", default=[])
    parser.add_argument("--supporting-regression-question-id", action="append", default=[])
    parser.add_argument("--updated-by", default="openclaw")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = Path(__file__).resolve().parents[2]
    validation_run_root = knowledge_root / "topics" / args.topic_slug / "L4" / "runs" / args.run_id
    receipts_path = validation_run_root / "literature_followup_receipts.jsonl"

    for row in read_jsonl(receipts_path):
        if receipt_matches_existing(row, args):
            print(json.dumps(row, ensure_ascii=True))
            return 0

    matches = search_arxiv(args.query, args.max_results)
    register_script = knowledge_root / "source-layer" / "scripts" / "register_arxiv_source.py"
    registered_arxiv_ids: list[str] = []
    py = python_command()
    for match in matches:
        arxiv_id = str(match["arxiv_id"])
        completed = subprocess.run(
            [
                *py,
                str(register_script),
                "--topic-slug",
                args.topic_slug,
                "--arxiv-id",
                arxiv_id,
                "--registered-by",
                args.updated_by,
            ],
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
        if completed.returncode == 0:
            registered_arxiv_ids.append(arxiv_id)

    receipt = {
        "receipt_id": f"literature-followup:{args.topic_slug}:{slugify(args.query)}:{now_iso()}",
        "topic_slug": args.topic_slug,
        "run_id": args.run_id,
        "query": args.query,
        "priority": args.priority,
        "target_source_type": args.target_source_type,
        "parent_gap_ids": dedupe_strings(args.parent_gap_id),
        "parent_followup_task_ids": dedupe_strings(args.parent_followup_task_id),
        "reentry_targets": dedupe_strings(args.reentry_target),
        "supporting_regression_question_ids": dedupe_strings(args.supporting_regression_question_id),
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "status": "completed" if matches else "no_matches",
        "matches": matches,
        "registered_arxiv_ids": registered_arxiv_ids,
    }
    append_jsonl(receipts_path, receipt)
    print(json.dumps(receipt, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
