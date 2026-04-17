#!/usr/bin/env python
"""Isolated acceptance for concept-graph analysis feeding L1 -> L2 staging."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]


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


def seed_runtime(runtime_root: Path) -> dict[str, Path]:
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "topic_state.json").write_text(
        json.dumps(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "resume_stage": "L1",
                "research_mode": "formal_derivation",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    queue_path = runtime_root / "action_queue.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "action_id": "action:demo-topic:manual:01",
                "status": "pending",
                "auto_runnable": False,
                "action_type": "manual_followup",
                "summary": "Wait for bounded manual follow-up after graph staging.",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    protocol_json = runtime_root / "runtime_protocol.generated.json"
    protocol_note = runtime_root / "runtime_protocol.generated.md"
    protocol_json.write_text(
        json.dumps(
            {
                "runtime_mode": "explore",
                "active_submode": "literature",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": [],
                },
                "active_research_contract": {
                    "l1_source_intake": {
                        "source_count": 2,
                        "assumption_rows": [],
                        "regime_rows": [],
                        "reading_depth_rows": [],
                        "method_specificity_rows": [],
                        "notation_rows": [],
                        "contradiction_candidates": [],
                        "notation_tension_candidates": [],
                        "concept_graph": {
                            "nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "source_title": "Anyon condensation paper",
                                    "source_type": "paper",
                                    "node_id": "concept:topological-order",
                                    "label": "Topological order",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.95,
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "source_title": "Operator algebra note",
                                    "source_type": "local_note",
                                    "node_id": "concept:topological-order-operator",
                                    "label": "Topological order",
                                    "node_type": "concept",
                                    "confidence_tier": "EXTRACTED",
                                    "confidence_score": 0.91,
                                },
                            ],
                            "edges": [],
                            "hyperedges": [],
                            "communities": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "community_id": "community-topological-order",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:topological-order"],
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "community_id": "community-topological-order-operator",
                                    "label": "Topological order cluster",
                                    "node_ids": ["concept:topological-order-operator"],
                                },
                            ],
                            "god_nodes": [
                                {
                                    "source_id": "paper:anyon-condensation",
                                    "node_id": "concept:topological-order",
                                    "label": "Topological order",
                                },
                                {
                                    "source_id": "note:operator-algebra",
                                    "node_id": "concept:topological-order-operator",
                                    "label": "Topological order",
                                },
                            ],
                        },
                    },
                    "l1_vault": {
                        "topic_slug": "demo-topic",
                        "wiki": {
                            "page_paths": [
                                "topics/demo-topic/L1/vault/wiki/home.md",
                                "topics/demo-topic/L1/vault/wiki/source-intake.md",
                            ]
                        },
                    },
                },
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    protocol_note.write_text("# Runtime protocol\n", encoding="utf-8")
    return {
        "queue_path": queue_path,
        "protocol_json": protocol_json,
        "protocol_note": protocol_note,
    }


def seed_intake(kernel_root: Path) -> None:
    wiki_root = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki"
    wiki_root.mkdir(parents=True, exist_ok=True)
    (wiki_root / "home.md").write_text(
        "# Demo Home\n\nTopological order bridge draft.\n",
        encoding="utf-8",
    )
    (wiki_root / "source-intake.md").write_text(
        "# Source Intake\n\nGraph-derived cross-source staging should appear here.\n",
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-analysis-staging-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_paths = seed_runtime(kernel_root / "topics" / "demo-topic" / "runtime")
    seed_intake(kernel_root)

    import sys

    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from knowledge_hub.aitp_service import AITPService

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    with patch.object(
        service,
        "_materialize_runtime_protocol_bundle",
        return_value={
            "runtime_protocol_path": str(runtime_paths["protocol_json"]),
            "runtime_protocol_note_path": str(runtime_paths["protocol_note"]),
        },
    ):
        payload = service._execute_auto_actions(
            topic_slug="demo-topic",
            updated_by="graph-analysis-acceptance",
            max_auto_steps=1,
            default_skill_queries=None,
        )

    check(payload["executed"], "Expected one bounded literature auto action to execute.")
    execution = payload["executed"][0]
    check(
        execution["action_type"] == "literature_intake_stage" and execution["status"] == "completed",
        "Expected literature_intake_stage to complete successfully from concept-graph analysis.",
    )
    staging = execution["result"]["staging"]
    manifest_path = Path(staging["manifest_json_path"])
    ensure_exists(manifest_path)
    check(staging["entry_count"] == 2, "Expected graph analysis to stage one bridge picture and one question-seed workflow.")
    check(
        {entry["candidate_unit_type"] for entry in staging["entries"]} == {"physical_picture", "workflow"},
        "Expected staged graph-analysis entries to materialize as physical_picture + workflow.",
    )
    check(
        all(bool((entry.get("provenance") or {}).get("graph_analysis_kind")) for entry in staging["entries"]),
        "Expected staged graph-analysis entries to persist graph_analysis_kind provenance.",
    )
    queue_rows = [
        json.loads(line)
        for line in runtime_paths["queue_path"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    check(
        any(row["action_type"] == "literature_intake_stage" and row["status"] == "completed" for row in queue_rows),
        "Expected action_queue.jsonl to record the completed literature_intake_stage row.",
    )

    consult_payload = service.consult_l2(
        query_text="topological order bridge",
        retrieval_profile="l1_provisional_understanding",
        include_staging=True,
        topic_slug="demo-topic",
        stage="L1",
        run_id="run-001",
        updated_by="graph-analysis-acceptance",
        record_consultation=False,
    )
    check(consult_payload["staged_hits"], "Expected consult_l2(include_staging=True) to return staged graph-analysis hits.")

    result = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "entry_count": staging["entry_count"],
            "candidate_unit_types": sorted({entry["candidate_unit_type"] for entry in staging["entries"]}),
            "staged_hit_count": len(consult_payload["staged_hits"]),
        },
        "artifacts": {
            "manifest_json_path": str(manifest_path),
            "runtime_protocol_note": str(runtime_paths["protocol_note"]),
            "wiki_source_intake_note": str(kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md"),
        },
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
