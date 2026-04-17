#!/usr/bin/env python
"""Acceptance for one replayable real-topic Lean bridge export report."""

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--updated-by", default="real-lean-bridge-export-acceptance")
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
        else Path(tempfile.mkdtemp(prefix="real-lean-export-")).resolve()
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
    shutil.copytree(
        reference_topic_root,
        kernel_root / "topics" / "jones-von-neumann-algebras" / "L0",
        dirs_exist_ok=True,
    )

    reference_topic_root = package_root / "topics" / "jones-von-neumann-algebras" / "L0"
    shutil.copytree(
        reference_topic_root,
        kernel_root / "topics" / "jones-von-neumann-algebras" / "L0",
        dirs_exist_ok=True,
    )
    adapter_scripts_root = repo_root / "research" / "adapters" / "openclaw" / "scripts"
    shutil.copytree(
        adapter_scripts_root,
        work_root / "adapters" / "openclaw" / "scripts",
        dirs_exist_ok=True,
    )

    jones_script = package_root / "runtime" / "scripts" / "run_jones_chapter4_finite_product_formal_closure_acceptance.py"
    jones_payload = run_python_json(
        [
            sys.executable,
            str(jones_script),
            "--kernel-root",
            str(kernel_root),
            "--repo-root",
            str(repo_root),
            "--work-root",
            str(work_root / "jones-closure"),
            "--updated-by",
            args.updated_by,
            "--json",
        ]
    )

    topic_slug = str(jones_payload.get("topic_slug") or "").strip()
    run_id = str(jones_payload.get("run_id") or "").strip()
    check(topic_slug, "Expected Jones closure acceptance to return a topic_slug.")
    check(run_id, "Expected Jones closure acceptance to return a run_id.")

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    export_target = service.select_lean_bridge_export_target(
        topic_slug=topic_slug,
        run_id=run_id,
        updated_by=args.updated_by,
        refresh_runtime_bundle=False,
    )
    check(
        str(export_target.get("status") or "") == "selected",
        "Expected a selected real-topic Lean bridge export target.",
    )

    lean_bin = shutil.which("lean")
    if lean_bin:
        checker_command = [lean_bin]
        checker_mode = "system_lean"
    else:
        fallback_checker = work_root / "fake_lean_unavailable.py"
        fallback_checker.write_text(
            "import sys\nprint('lean executable unavailable', file=sys.stderr)\nraise SystemExit(1)\n",
            encoding="utf-8",
        )
        checker_command = [sys.executable, str(fallback_checker)]
        checker_mode = "fallback_mismatch"

    export_check = service.run_lean_bridge_export_check(
        topic_slug=topic_slug,
        run_id=run_id,
        checker_command=checker_command,
        updated_by=args.updated_by,
        refresh_runtime_bundle=False,
    )

    export_report_path = Path(str(export_check.get("export_report_path") or ""))
    export_module_path = Path(str(export_check.get("export_module_path") or ""))
    active_target_path = kernel_root / "topics" / topic_slug / "runtime" / "lean_bridge_export_target.active.json"
    active_check_path = kernel_root / "topics" / topic_slug / "runtime" / "lean_bridge_export_check.active.json"
    for path in (
        export_report_path,
        export_module_path,
        active_target_path,
        active_check_path,
    ):
        ensure_exists(path)

    status = str(export_check.get("status") or "").strip()
    check(
        status in {"typecheck_passed", "mismatch_reported"},
        "Expected Lean bridge export check to end in typecheck_passed or mismatch_reported.",
    )

    payload = {
        "status": "success",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "checker_mode": checker_mode,
        "jones_closure": jones_payload,
        "export_target": export_target,
        "export_check": export_check,
        "artifacts": {
            "lean_bridge_export_target": str(active_target_path),
            "lean_bridge_export_check": str(active_check_path),
            "export_report": str(export_report_path),
            "export_module": str(export_module_path),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
