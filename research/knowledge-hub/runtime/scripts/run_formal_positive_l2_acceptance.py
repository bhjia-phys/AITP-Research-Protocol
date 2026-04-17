#!/usr/bin/env python
"""Fresh formal positive-L2 acceptance built on top of the Jones closure lane."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService, write_json  # noqa: E402


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def run_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--topic",
        default="Fresh Jones finite-dimensional factor closure",
    )
    parser.add_argument(
        "--question",
        default=(
            "Promote one bounded Jones finite-dimensional factor result into "
            "authoritative L2."
        ),
    )
    parser.add_argument(
        "--reference-topic-slug",
        default="jones-von-neumann-algebras",
    )
    parser.add_argument(
        "--bootstrap-run-id",
        default=f"{run_stamp()}-bootstrap",
    )
    parser.add_argument(
        "--closure-run-id",
        default=f"{run_stamp()}-jones-close",
    )
    parser.add_argument(
        "--updated-by",
        default="formal-positive-l2-acceptance",
    )
    parser.add_argument("--human-request")
    parser.add_argument("--tpkn-template-root")
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def rewrite_topic_relative_path(
    value: str,
    *,
    reference_topic_slug: str,
    target_topic_slug: str,
) -> str:
    return str(value).replace(
        f"topics/{reference_topic_slug}/L0/",
        f"topics/{target_topic_slug}/L0/",
    )


def clone_reference_sources(
    *,
    kernel_root: Path,
    reference_topic_slug: str,
    target_topic_slug: str,
) -> dict[str, Any]:
    reference_root = kernel_root / "topics" / reference_topic_slug / "L0"
    if not reference_root.exists():
        raise FileNotFoundError(f"Reference topic root is missing: {reference_root}")

    target_root = kernel_root / "topics" / target_topic_slug / "L0"
    target_root.mkdir(parents=True, exist_ok=True)

    reference_sources_root = reference_root / "sources"
    target_sources_root = target_root / "sources"
    if reference_sources_root.exists():
        shutil.copytree(
            reference_sources_root,
            target_sources_root,
            dirs_exist_ok=True,
        )

    cloned_rows: list[dict[str, Any]] = []
    for row in read_jsonl(reference_root / "source_index.jsonl"):
        cloned = dict(row)
        cloned["topic_slug"] = target_topic_slug
        locator = dict(cloned.get("locator") or {})
        for key in ("local_path", "snapshot_path"):
            if key in locator:
                locator[key] = rewrite_topic_relative_path(
                    str(locator[key]),
                    reference_topic_slug=reference_topic_slug,
                    target_topic_slug=target_topic_slug,
                )
        cloned["locator"] = locator
        cloned_rows.append(cloned)
    write_jsonl(target_root / "source_index.jsonl", cloned_rows)

    topic_payload = read_json(reference_root / "topic.json") or {}
    if topic_payload:
        topic_payload["topic_slug"] = target_topic_slug
        if "slug" in topic_payload:
            topic_payload["slug"] = target_topic_slug
        write_json(target_root / "topic.json", topic_payload)

    return {
        "reference_topic_slug": reference_topic_slug,
        "target_topic_slug": target_topic_slug,
        "target_root": str(target_root),
        "source_count": len(cloned_rows),
    }


def run_python_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {message}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expected JSON output from {' '.join(command)}") from exc


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else (repo_root.parent / "_formal_positive_l2" / uuid.uuid4().hex[:8]).resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    human_request = str(args.human_request or "").strip() or (
        "Open a fresh formal-theory topic from natural language, seed it with the "
        "explicit Jones source packet, and then drive one bounded positive "
        "formal result through the existing Jones Chapter 4 closure machinery."
    )

    bootstrap_payload = service.new_topic(
        topic=args.topic,
        question=args.question,
        mode="formal_theory",
        run_id=args.bootstrap_run_id,
        updated_by=args.updated_by,
        human_request=human_request,
    )
    topic_slug = str(bootstrap_payload.get("topic_slug") or "").strip()
    if not topic_slug:
        raise RuntimeError("new_topic did not return a topic_slug.")

    entry_audit = service.audit(
        topic_slug=topic_slug,
        phase="entry",
        updated_by=args.updated_by,
    )
    (kernel_root / "topics" / topic_slug / "runtime" / "context_fragments").mkdir(
        parents=True,
        exist_ok=True,
    )
    source_seed = clone_reference_sources(
        kernel_root=kernel_root,
        reference_topic_slug=args.reference_topic_slug,
        target_topic_slug=topic_slug,
    )

    jones_script = SCRIPT_PATH.with_name(
        "run_jones_chapter4_finite_product_formal_closure_acceptance.py"
    )
    jones_command = [
        sys.executable,
        str(jones_script),
        "--kernel-root",
        str(kernel_root),
        "--repo-root",
        str(repo_root),
        "--topic-slug",
        topic_slug,
        "--run-id",
        args.closure_run_id,
        "--updated-by",
        args.updated_by,
        "--work-root",
        str(work_root / "jones-closure"),
        "--json",
    ]
    if args.tpkn_template_root:
        jones_command.extend(["--tpkn-template-root", str(args.tpkn_template_root)])
    closure_payload = run_python_json(jones_command)
    compile_map_payload = service.compile_l2_workspace_map()
    compile_graph_payload = service.compile_l2_graph_report()
    compile_report_payload = service.compile_l2_knowledge_report()
    consult_payload = service.consult_l2(
        query_text="Jones finite product theorem packet",
        retrieval_profile="l3_candidate_formation",
        max_primary_hits=8,
    )
    consult_ids = sorted(
        {
            str(row.get("id") or "").strip()
            for row in [
                *(consult_payload.get("primary_hits") or []),
                *(consult_payload.get("expanded_hits") or []),
            ]
            if str(row.get("id") or "").strip()
        }
    )
    if "theorem:jones-ch4-finite-product" not in consult_ids:
        raise RuntimeError("Expected consult_l2 to surface the fresh Jones theorem mirror.")
    if not any(
        str(row.get("knowledge_id") or "").strip() == "theorem:jones-ch4-finite-product"
        for row in (compile_report_payload.get("payload") or {}).get("knowledge_rows", [])
    ):
        raise RuntimeError("Expected workspace knowledge report to include the fresh Jones theorem mirror.")

    payload = {
        "status": "success",
        "topic_slug": topic_slug,
        "bootstrap_run_id": args.bootstrap_run_id,
        "closure_run_id": args.closure_run_id,
        "bootstrap": {
            "topic": args.topic,
            "question": args.question,
            "topic_slug": topic_slug,
            "research_mode": str(
                (bootstrap_payload.get("topic_state") or {}).get("research_mode")
                or bootstrap_payload.get("research_mode")
                or ""
            ),
            "runtime_protocol": str(
                (bootstrap_payload.get("files") or {}).get("runtime_protocol") or ""
            ),
        },
        "entry_audit": entry_audit,
        "source_seed": source_seed,
        "closure": closure_payload,
        "repo_local_l2": {
            "workspace_memory_map": {
                "json_path": compile_map_payload["json_path"],
                "markdown_path": compile_map_payload["markdown_path"],
            },
            "workspace_graph_report": {
                "json_path": compile_graph_payload["json_path"],
                "markdown_path": compile_graph_payload["markdown_path"],
            },
            "workspace_knowledge_report": {
                "json_path": compile_report_payload["json_path"],
                "markdown_path": compile_report_payload["markdown_path"],
            },
            "consultation": {
                "query_text": "Jones finite product theorem packet",
                "retrieval_profile": "l3_candidate_formation",
                "ids": consult_ids,
            },
        },
        "artifacts": {
            "bootstrap_topic_state": str(
                (bootstrap_payload.get("files") or {}).get("topic_state") or ""
            ),
            "bootstrap_runtime_protocol": str(
                (bootstrap_payload.get("files") or {}).get("runtime_protocol") or ""
            ),
            "source_index": str(
                kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
            ),
            "workspace_memory_map": compile_map_payload["json_path"],
            "workspace_graph_report": compile_graph_payload["json_path"],
            "workspace_knowledge_report": compile_report_payload["json_path"],
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
