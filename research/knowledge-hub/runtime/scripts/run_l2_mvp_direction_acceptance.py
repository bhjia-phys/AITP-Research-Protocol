#!/usr/bin/env python
"""Isolated acceptance for the bounded L2 MVP direction."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


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


def run_cli_json(*, package_root: Path, kernel_root: Path, repo_root: Path, args: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "knowledge_hub.aitp_cli",
        "--kernel-root",
        str(kernel_root),
        "--repo-root",
        str(repo_root),
        *args,
    ]
    completed = subprocess.run(
        command,
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l2-mvp-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    (kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
    bundle_schema = package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
    (kernel_root / "runtime" / "schemas" / bundle_schema.name).write_text(
        bundle_schema.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    seed_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["seed-l2-direction", "--direction", "tfim-benchmark-first", "--json"],
    )
    consult_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "consult-l2",
            "--query-text",
            "TFIM exact diagonalization benchmark workflow",
            "--retrieval-profile",
            "l3_candidate_formation",
            "--max-primary-hits",
            "2",
            "--json",
        ],
    )
    compile_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["compile-l2-map", "--json"],
    )
    graph_report_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["compile-l2-graph-report", "--json"],
    )
    hygiene_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["audit-l2-hygiene", "--json"],
    )

    compile_json = Path(compile_payload["json_path"])
    compile_md = Path(compile_payload["markdown_path"])
    graph_report_json = Path(graph_report_payload["json_path"])
    graph_report_md = Path(graph_report_payload["markdown_path"])
    navigation_index = Path(graph_report_payload["navigation_index_path"])
    navigation_root = Path(graph_report_payload["navigation_root"])
    hygiene_json = Path(hygiene_payload["json_path"])
    hygiene_md = Path(hygiene_payload["markdown_path"])
    for path in (compile_json, compile_md, graph_report_json, graph_report_md, navigation_index, hygiene_json, hygiene_md):
        ensure_exists(path)

    primary_ids = {row["id"] for row in consult_payload["primary_hits"]}
    expanded_ids = {row["id"] for row in consult_payload["expanded_hits"]}
    compiled_map = json.loads(compile_json.read_text(encoding="utf-8"))
    graph_report = json.loads(graph_report_json.read_text(encoding="utf-8"))
    hygiene_report = json.loads(hygiene_json.read_text(encoding="utf-8"))
    workflow_navigation_page = navigation_root / "workflow--tfim-benchmark-workflow.md"
    ensure_exists(workflow_navigation_page)

    check(seed_payload["direction"] == "tfim-benchmark-first", "Expected the TFIM MVP direction to seed.")
    check(
        "physical_picture:tfim-weak-coupling-benchmark-intuition" in (primary_ids | expanded_ids),
        "Expected consult-l2 to return the seeded physical_picture.",
    )
    check(
        "physical_picture" in set(compiled_map["summary"]["unit_types_present"]),
        "Expected the compiled L2 map to include physical_picture.",
    )
    check(
        compiled_map["summary"]["total_units"] >= 9,
        "Expected the compiled L2 map to include the seeded direction units.",
    )
    check(
        graph_report["summary"]["total_units"] >= 9,
        "Expected the compiled graph report to include the seeded direction units.",
    )
    check(
        graph_report_json.name == "workspace_graph_report.json",
        "Expected the graph report JSON artifact to be named workspace_graph_report.json.",
    )
    check(
        graph_report_md.name == "workspace_graph_report.md",
        "Expected the graph report markdown artifact to be named workspace_graph_report.md.",
    )
    check(
        navigation_index.name == "index.md",
        "Expected the derived navigation index artifact to be named index.md.",
    )
    check(
        graph_report["hub_units"][0]["unit_id"] == "workflow:tfim-benchmark-workflow",
        "Expected the workflow node to surface as the primary graph hub.",
    )
    check(
        graph_report_payload["navigation_page_count"] >= 9,
        "Expected derived navigation to include one page per seeded unit.",
    )
    check(
        hygiene_report["summary"]["total_units"] >= 9,
        "Expected the hygiene report to cover the seeded direction units.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "seed_direction": seed_payload["direction"],
            "consult_profile": consult_payload["retrieval_profile"],
            "compiled_total_units": compiled_map["summary"]["total_units"],
            "compiled_unit_types": compiled_map["summary"]["unit_types_present"],
            "graph_report_total_units": graph_report["summary"]["total_units"],
            "graph_report_primary_hub": graph_report["hub_units"][0]["unit_id"],
            "navigation_page_count": graph_report_payload["navigation_page_count"],
            "hygiene_total_units": hygiene_report["summary"]["total_units"],
            "hygiene_status": hygiene_report["summary"]["status"],
        },
        "artifacts": {
            "compile_json": str(compile_json),
            "compile_markdown": str(compile_md),
            "graph_report_json": str(graph_report_json),
            "graph_report_markdown": str(graph_report_md),
            "navigation_index_path": str(navigation_index),
            "workflow_navigation_page": str(workflow_navigation_page),
            "hygiene_json": str(hygiene_json),
            "hygiene_markdown": str(hygiene_md),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
