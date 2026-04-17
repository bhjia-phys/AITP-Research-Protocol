#!/usr/bin/env python
"""Acceptance for positive/negative coexistence on repo-local L2 surfaces."""

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

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402
from knowledge_hub.l2_staging import stage_negative_result_entry  # noqa: E402


NEGATIVE_TITLE = "Jones finite product theorem classification failure"
NEGATIVE_SUMMARY = (
    "The Jones finite product theorem packet does not justify a full "
    "type-I classification claim."
)
COEXISTENCE_QUERY = "Jones finite product theorem classification failure"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--updated-by", default="positive-negative-l2-coexistence-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_python_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
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
        else Path(tempfile.mkdtemp(prefix="pnco-")).resolve()
    )
    kernel_root = work_root / "knowledge-hub"

    for relative in ("canonical", "knowledge_hub", "schemas"):
        shutil.copytree(package_root / relative, kernel_root / relative, dirs_exist_ok=True)
    (kernel_root / "runtime").mkdir(parents=True, exist_ok=True)
    for path in (package_root / "runtime").iterdir():
        if path.is_file():
            shutil.copy2(path, kernel_root / "runtime" / path.name)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_schemas_root = package_root / "runtime" / "schemas"
    if runtime_schemas_root.exists():
        shutil.copytree(runtime_schemas_root, kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    reference_topic_root = package_root / "topics" / "jones-von-neumann-algebras" / "L0"
    shutil.copytree(reference_topic_root, kernel_root / "topics" / "jones-von-neumann-algebras" / "L0", dirs_exist_ok=True)
    adapter_scripts_root = repo_root / "research" / "adapters" / "openclaw" / "scripts"
    shutil.copytree(adapter_scripts_root, work_root / "adapters" / "openclaw" / "scripts", dirs_exist_ok=True)

    shutil.rmtree(kernel_root / "canonical" / "staging" / "entries", ignore_errors=True)
    (kernel_root / "canonical" / "staging" / "entries").mkdir(parents=True, exist_ok=True)
    (kernel_root / "canonical" / "staging" / "staging_index.jsonl").unlink(missing_ok=True)

    positive_script = kernel_root / "runtime" / "scripts" / "run_formal_positive_l2_acceptance.py"
    positive_payload = run_python_json(
        [
            sys.executable,
            str(positive_script),
            "--kernel-root",
            str(kernel_root),
            "--repo-root",
            str(repo_root),
            "--work-root",
            str(work_root / "fp"),
            "--updated-by",
            args.updated_by,
            "--json",
        ]
    )

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    negative_payload = stage_negative_result_entry(
        kernel_root,
        title=NEGATIVE_TITLE,
        summary=NEGATIVE_SUMMARY,
        failure_kind="scope_overreach",
        staged_by=args.updated_by,
    )
    report_payload = service.compile_l2_knowledge_report()
    consult_payload = service.consult_l2(
        query_text=COEXISTENCE_QUERY,
        retrieval_profile="l4_adjudication",
        include_staging=True,
        max_primary_hits=8,
    )

    theorem_id = "theorem:jones-ch4-finite-product"
    negative_entry_id = str(negative_payload["entry"]["entry_id"])
    knowledge_rows = {
        str(row.get("knowledge_id") or ""): row
        for row in (report_payload.get("payload") or {}).get("knowledge_rows", [])
    }
    theorem_row = knowledge_rows.get(theorem_id) or {}
    negative_row = knowledge_rows.get(negative_entry_id) or {}
    canonical_ids = sorted(
        {
            str(row.get("id") or "").strip()
            for row in [
                *(consult_payload.get("primary_hits") or []),
                *(consult_payload.get("expanded_hits") or []),
            ]
            if str(row.get("id") or "").strip()
        }
    )
    staged_ids = sorted(
        {
            str(row.get("entry_id") or "").strip()
            for row in (consult_payload.get("staged_hits") or [])
            if str(row.get("entry_id") or "").strip()
        }
    )

    check(theorem_row.get("authority_level") == "authoritative_canonical", "Expected theorem row to stay authoritative.")
    check(theorem_row.get("knowledge_state") == "trusted", "Expected theorem row to stay trusted.")
    check(negative_row.get("authority_level") == "non_authoritative_staging", "Expected negative row to stay staging.")
    check(negative_row.get("knowledge_state") == "contradiction_watch", "Expected negative row to compile as contradiction_watch.")
    check(bool(theorem_row.get("provenance_refs") or []), "Expected theorem row provenance refs to remain populated.")
    check(bool(negative_row.get("provenance_refs") or []), "Expected negative row provenance refs to remain populated.")
    check(theorem_id in canonical_ids, "Expected consultation to surface the authoritative theorem row.")
    check(negative_entry_id in staged_ids, "Expected consultation staged hits to surface the negative row.")

    report_json_path = Path(report_payload["json_path"])
    report_markdown_path = Path(report_payload["markdown_path"])
    ensure_exists(report_json_path)
    ensure_exists(report_markdown_path)
    ensure_exists(Path(negative_payload["entry_json_path"]))
    ensure_exists(Path(positive_payload["repo_local_l2"]["workspace_knowledge_report"]["json_path"]))

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "positive_acceptance": {
            "topic_slug": positive_payload["topic_slug"],
            "bootstrap_run_id": positive_payload["bootstrap_run_id"],
            "closure_run_id": positive_payload["closure_run_id"],
            "theorem_id": theorem_id,
            "projection_id": "topic_skill_projection:fresh-jones-finite-dimensional-factor-closure",
            "workspace_knowledge_report": positive_payload["repo_local_l2"]["workspace_knowledge_report"]["json_path"],
        },
        "negative_result": {
            "entry_id": negative_entry_id,
            "title": NEGATIVE_TITLE,
            "summary": NEGATIVE_SUMMARY,
            "entry_json_path": negative_payload["entry_json_path"],
            "entry_markdown_path": negative_payload["entry_markdown_path"],
            "staging_manifest_json_path": negative_payload["manifest_json_path"],
        },
        "knowledge_report": {
            "json_path": str(report_json_path),
            "markdown_path": str(report_markdown_path),
            "theorem_row": theorem_row,
            "negative_row": negative_row,
        },
        "consultation": {
            "query_text": COEXISTENCE_QUERY,
            "retrieval_profile": "l4_adjudication",
            "canonical_ids": canonical_ids,
            "staged_ids": staged_ids,
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
