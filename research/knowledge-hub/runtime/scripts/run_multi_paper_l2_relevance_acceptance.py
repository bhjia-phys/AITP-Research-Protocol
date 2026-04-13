#!/usr/bin/env python
"""Isolated acceptance for multi-paper real-topic L2 relevance hardening."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]


TOPIC_SLUG = "fresh-measurement-induced-observer-algebra-relevance-proof"
QUERY_TEXT = "measurement induced observer algebra bridge"
PRIMARY_TITLE = "Measurement-induced observer algebra bridge note"
UNRELATED_CANONICAL_ID = "concept:observer-algebra-carryover"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def seed_unrelated_canonical_carryover(kernel_root: Path) -> None:
    path = kernel_root / "canonical" / "concepts" / "concept--observer-algebra-carryover.json"
    write_json(
        path,
        {
            "id": UNRELATED_CANONICAL_ID,
            "unit_type": "concept",
            "title": "Observer algebra carryover concept",
            "summary": "Older canonical material about observer algebra bridge structure from an unrelated topic.",
            "maturity": "human_promoted",
            "created_at": "2026-04-14T00:00:00+00:00",
            "updated_at": "2026-04-14T00:00:00+00:00",
            "topic_completion_status": "regression-stable",
            "tags": ["observer-algebra", "bridge", "carryover"],
            "assumptions": [],
            "regime": {
                "domain": "unrelated canonical topic",
                "approximations": [],
                "scale": "bounded",
                "boundary_conditions": [],
                "exclusions": [],
            },
            "scope": {
                "applies_to": ["unrelated canonical carryover"],
                "out_of_scope": ["fresh local topic routing"],
            },
            "provenance": {
                "source_ids": ["source:older-topic"],
                "l1_artifacts": [],
                "l3_runs": [],
                "l4_checks": [],
                "citations": [],
            },
            "promotion": {
                "route": "L3->L4->L2",
                "review_mode": "human",
                "canonical_layer": "L2",
                "promoted_by": "test-suite",
                "promoted_at": "2026-04-14T00:00:00+00:00",
                "review_status": "accepted",
                "rationale": "Seed unrelated canonical carryover for local-relevance ordering proof.",
            },
            "dependencies": [],
            "related_units": [],
            "payload": {},
        },
    )


def seed_source_artifacts(kernel_root: Path) -> list[dict[str, str]]:
    topic_root = kernel_root / "source-layer" / "topics" / TOPIC_SLUG / "sources"
    sources = [
        {
            "source_id": "source:measurement-induced-bridge-paper",
            "source_slug": "paper-measurement-induced-bridge",
            "source_title": "Measurement-induced observer algebra bridge paper",
        },
        {
            "source_id": "source:factor-type-warning-paper",
            "source_slug": "paper-factor-type-warning",
            "source_title": "Factor-type warning paper",
        },
    ]
    for row in sources:
        source_root = topic_root / row["source_slug"]
        source_root.mkdir(parents=True, exist_ok=True)
        write_json(
            source_root / "source.json",
            {
                "source_id": row["source_id"],
                "title": row["source_title"],
                "summary": f"Seed source for {TOPIC_SLUG}.",
            },
        )
    return sources


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-multi-paper-l2-relevance-")).resolve()
    )
    kernel_root = work_root / "kernel"

    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)

    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    from knowledge_hub.aitp_service import AITPService
    from knowledge_hub.l2_compiler import materialize_workspace_knowledge_report
    from knowledge_hub.l2_graph import materialize_canonical_index
    from knowledge_hub.literature_intake_support import stage_literature_units

    seed_unrelated_canonical_carryover(kernel_root)
    sources = seed_source_artifacts(kernel_root)
    materialize_canonical_index(kernel_root)

    source_by_id = {row["source_id"]: row for row in sources}
    staging_payload = stage_literature_units(
        kernel_root,
        topic_slug=TOPIC_SLUG,
        source_slug="multi-paper-batch",
        candidate_units=[
            {
                "candidate_unit_type": "concept",
                "title": PRIMARY_TITLE,
                "summary": "Fresh local staged note connecting measurement-induced transitions and observer algebras.",
                "tags": ["measurement-induced", "observer-algebra", "bridge"],
                "source_refs": [sources[0]["source_id"]],
                "provenance": {
                    "source_id": sources[0]["source_id"],
                    "source_slug": sources[0]["source_slug"],
                    "source_title": sources[0]["source_title"],
                },
            },
            {
                "candidate_unit_type": "warning_note",
                "title": "Do not equate measurement-induced transition with factor-type phase",
                "summary": "The local paper set does not justify a direct von Neumann factor-type identification for monitored phases.",
                "tags": ["measurement-induced", "warning", "observer-algebra"],
                "source_refs": [sources[1]["source_id"]],
                "provenance": {
                    "source_id": sources[1]["source_id"],
                    "source_slug": sources[1]["source_slug"],
                    "source_title": sources[1]["source_title"],
                },
            },
        ],
        created_by="multi-paper-l2-relevance-acceptance",
    )
    knowledge_report = materialize_workspace_knowledge_report(kernel_root)
    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    consult_payload = service.consult_l2(
        query_text=QUERY_TEXT,
        retrieval_profile="l1_provisional_understanding",
        max_primary_hits=3,
        include_staging=True,
        topic_slug=TOPIC_SLUG,
        updated_by="multi-paper-l2-relevance-acceptance",
        record_consultation=False,
    )

    entries_by_title = {entry["title"]: entry for entry in staging_payload["entries"]}
    primary_entry = entries_by_title[PRIMARY_TITLE]

    ensure_exists(Path(staging_payload["manifest_json_path"]))
    ensure_exists(Path(knowledge_report["json_path"]))
    check(
        consult_payload["primary_hits"][0]["id"] == primary_entry["entry_id"],
        "Expected the topic-local staged bridge note to win the primary consultation surface.",
    )
    check(
        consult_payload["primary_hits"][0]["trust_surface"] == "staging",
        "Expected the primary consultation winner to remain explicitly non-authoritative staging.",
    )
    staged_source_ids = {
        str((entry.get("provenance") or {}).get("source_id") or "")
        for entry in staging_payload["entries"]
    }
    check(
        staged_source_ids == set(source_by_id),
        "Expected staged entries to preserve distinct per-paper source provenance.",
    )
    check(
        any(hit["id"] == UNRELATED_CANONICAL_ID for hit in consult_payload["primary_hits"][1:] + consult_payload["expanded_hits"]),
        "Expected the unrelated canonical carryover to remain visible but not outrank the local staged hit.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "topic_slug": TOPIC_SLUG,
        "query_text": QUERY_TEXT,
        "checks": {
            "staged_entry_count": staging_payload["entry_count"],
            "staged_source_ids": sorted(staged_source_ids),
            "primary_hit_id": consult_payload["primary_hits"][0]["id"],
            "primary_hit_trust_surface": consult_payload["primary_hits"][0]["trust_surface"],
            "unrelated_canonical_id": UNRELATED_CANONICAL_ID,
        },
        "artifacts": {
            "workspace_staging_manifest": staging_payload["manifest_json_path"],
            "workspace_staging_note": staging_payload["manifest_markdown_path"],
            "workspace_knowledge_report": knowledge_report["json_path"],
            "workspace_knowledge_report_note": knowledge_report["markdown_path"],
        },
        "consultation": consult_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
