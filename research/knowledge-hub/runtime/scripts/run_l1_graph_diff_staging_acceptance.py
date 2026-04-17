#!/usr/bin/env python
"""Isolated acceptance for graph-diff-aware literature-intake staging."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
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


def seed_runtime(runtime_root: Path) -> None:
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
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Inspect graph drift and stage bounded downstream units.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:graph-diff",
                    "decision_source": "heuristic",
                },
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "action_queue.jsonl").write_text(
        json.dumps(
            {
                "action_id": "action:demo-topic:manual:01",
                "status": "pending",
                "auto_runnable": False,
                "action_type": "manual_followup",
                "summary": "Wait for bounded manual follow-up after graph diff staging.",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def write_concept_graph(path: Path, *, source_id: str, source_json_path: str, label: str, node_id: str, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "source_concept_graph",
                "graph_version": 1,
                "topic_slug": "demo-topic",
                "source_id": source_id,
                "source_json_path": source_json_path,
                "generated_at": generated_at,
                "generated_by": "acceptance-test",
                "provider": "override_json",
                "nodes": [
                    {
                        "node_id": node_id,
                        "label": label,
                        "node_type": "concept",
                        "confidence_tier": "EXTRACTED",
                        "confidence_score": 0.95,
                        "evidence_refs": [],
                        "notes": "",
                    }
                ],
                "edges": [],
                "hyperedges": [],
                "communities": [],
                "god_nodes": [node_id],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_source_index(source_root: Path, *, paper_graph_path: str, note_graph_path: str | None) -> None:
    rows = [
        json.dumps(
            {
                "source_id": "paper:anyon-condensation-2401-00005",
                "source_type": "paper",
                "title": "Anyon condensation paper",
                "summary": "Anyon condensation summary.",
                "locator": {
                    "concept_graph_path": paper_graph_path,
                },
                "provenance": {
                    "abs_url": "https://example.org/anyon-condensation",
                },
            },
            ensure_ascii=True,
        ),
        json.dumps(
            {
                "source_id": "note:operator-algebra",
                "source_type": "local_note",
                "title": "Operator algebra note",
                "summary": "Operator algebra note summary.",
                "locator": (
                    {"concept_graph_path": note_graph_path}
                    if note_graph_path
                    else {}
                ),
                "provenance": {
                    "deepxiv_tldr": "Operator algebra route summary.",
                },
            },
            ensure_ascii=True,
        ),
    ]
    (source_root / "source_index.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-diff-staging-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki").mkdir(parents=True, exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "home.md").write_text(
        "# Demo Home\n\nGraph diff staging acceptance.\n",
        encoding="utf-8",
    )
    (kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md").write_text(
        "# Source Intake\n\nGraph diff staging acceptance.\n",
        encoding="utf-8",
    )

    import sys

    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from knowledge_hub.aitp_service import AITPService

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    seed_runtime(runtime_root)

    source_root = kernel_root / "topics" / "demo-topic" / "L0"
    paper_source_slug = "paper-anyon-condensation-2401-00005"
    note_source_slug = "note-operator-algebra"
    paper_graph_path = source_root / "sources" / paper_source_slug / "concept_graph.json"
    note_graph_path = source_root / "sources" / note_source_slug / "concept_graph.json"

    write_concept_graph(
        paper_graph_path,
        source_id="paper:anyon-condensation-2401-00005",
        source_json_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/source.json",
        label="Topological order",
        node_id="concept:topological-order",
        generated_at="2026-04-13T00:00:00+08:00",
    )
    write_source_index(
        source_root,
        paper_graph_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/concept_graph.json",
        note_graph_path=None,
    )
    service.topic_status(topic_slug="demo-topic")

    write_concept_graph(
        paper_graph_path,
        source_id="paper:anyon-condensation-2401-00005",
        source_json_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/source.json",
        label="Anyon condensation",
        node_id="concept:anyon-condensation",
        generated_at="2026-04-14T00:00:00+08:00",
    )
    write_concept_graph(
        note_graph_path,
        source_id="note:operator-algebra",
        source_json_path=f"topics/demo-topic/L0/sources/{note_source_slug}/source.json",
        label="Anyon condensation",
        node_id="concept:anyon-condensation-operator",
        generated_at="2026-04-14T00:00:00+08:00",
    )
    write_source_index(
        source_root,
        paper_graph_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/concept_graph.json",
        note_graph_path=f"topics/demo-topic/L0/sources/{note_source_slug}/concept_graph.json",
    )
    second_status = service.topic_status(topic_slug="demo-topic")
    runtime_protocol_json = runtime_root / "runtime_protocol.generated.json"
    runtime_protocol_note = runtime_root / "runtime_protocol.generated.md"
    runtime_bundle = json.loads(runtime_protocol_json.read_text(encoding="utf-8"))
    runtime_bundle["runtime_mode"] = "explore"
    runtime_bundle["active_submode"] = "literature"
    runtime_bundle["graph_analysis"] = second_status["graph_analysis"]
    runtime_protocol_json.write_text(json.dumps(runtime_bundle, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    runtime_protocol_note.write_text("# Runtime protocol\n", encoding="utf-8")

    with patch.object(
        service,
        "_materialize_runtime_protocol_bundle",
        return_value={
            "runtime_protocol_path": str(runtime_protocol_json),
            "runtime_protocol_note_path": str(runtime_protocol_note),
        },
    ):
        payload = service._execute_auto_actions(
            topic_slug="demo-topic",
            updated_by="graph-diff-staging-acceptance",
            max_auto_steps=1,
            default_skill_queries=None,
        )

    check(payload["executed"], "Expected one bounded literature auto action to execute.")
    execution = payload["executed"][0]
    check(
        execution["action_type"] == "literature_intake_stage" and execution["status"] == "completed",
        "Expected literature_intake_stage to complete successfully from graph diff.",
    )
    staging = execution["result"]["staging"]
    manifest_path = Path(staging["manifest_json_path"])
    graph_analysis_json = kernel_root / "topics" / "demo-topic" / "runtime" / "graph_analysis.json"
    graph_analysis_history = kernel_root / "topics" / "demo-topic" / "runtime" / "graph_analysis_history.jsonl"
    for path in (manifest_path, graph_analysis_json, graph_analysis_history):
        ensure_exists(path)

    staged_entries = staging["entries"]
    check(len(staged_entries) >= 2, "Expected graph diff staging to materialize at least two downstream units.")
    graph_diff_kinds = {entry["provenance"].get("graph_analysis_kind") for entry in staged_entries}
    check(
        {"graph_diff_added", "graph_diff_removed"}.issubset(graph_diff_kinds),
        "Expected staged entries to include both graph_diff_added and graph_diff_removed provenance kinds.",
    )
    diff_entries = [
        entry
        for entry in staged_entries
        if entry["provenance"].get("graph_analysis_kind") in {"graph_diff_added", "graph_diff_removed"}
    ]
    check(
        {entry["candidate_unit_type"] for entry in diff_entries} == {"claim_card", "warning_note"},
        "Expected graph-diff-specific staging to materialize claim_card + warning_note.",
    )

    result = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "entry_count": len(staged_entries),
            "candidate_unit_types": sorted({entry["candidate_unit_type"] for entry in staged_entries}),
            "graph_analysis_kinds": sorted(str(item) for item in graph_diff_kinds if item),
        },
        "artifacts": {
            "manifest_json_path": str(manifest_path),
            "graph_analysis_json": str(graph_analysis_json),
            "graph_analysis_history": str(graph_analysis_history),
        },
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
