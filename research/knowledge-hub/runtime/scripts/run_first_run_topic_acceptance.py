#!/usr/bin/env python
"""Isolated acceptance for the first-run bootstrap -> loop -> status path."""

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

TOPIC_TITLE = "Jones Chapter 4 finite-dimensional backbone"
TOPIC_STATEMENT = "Start from the finite-dimensional backbone and record the first honest closure target."
LOOP_REQUEST = "Continue with the first bounded route and stop before expensive execution."
TOPIC_SLUG = "jones-chapter-4-finite-dimensional-backbone"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic-slug", default=TOPIC_SLUG)
    parser.add_argument("--register-arxiv-id")
    parser.add_argument("--registration-metadata-json")
    parser.add_argument("--use-package-root-as-kernel", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


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


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_script_json(*, command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def prepare_first_run_kernel(package_root: Path, kernel_root: Path) -> None:
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)

    for dirname in ("source-layer", "intake", "feedback", "consultation", "validation"):
        (kernel_root / dirname).mkdir(parents=True, exist_ok=True)

    for name in (
        "closed_loop_policies.json",
        "research_mode_profiles.json",
        "CONTROL_NOTE_CONTRACT.md",
        "DECLARATIVE_RUNTIME_CONTRACTS.md",
        "DEFERRED_RUNTIME_CONTRACTS.md",
        "INNOVATION_DIRECTION_TEMPLATE.md",
        "PROGRESSIVE_DISCLOSURE_PROTOCOL.md",
    ):
        target = kernel_root / "runtime" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_root / "runtime" / name, target)

    for path in package_root.iterdir():
        if path.is_file() and path.suffix == ".md":
            shutil.copy2(path, kernel_root / path.name)

    exploration_window = package_root / "exploration_window.json"
    if exploration_window.exists():
        shutil.copy2(exploration_window, kernel_root / "exploration_window.json")


def assert_topic_is_fresh(kernel_root: Path, topic_slug: str) -> None:
    paths = [
        kernel_root / "runtime" / "topics" / topic_slug,
        kernel_root / "feedback" / "topics" / topic_slug,
        kernel_root / "source-layer" / "topics" / topic_slug,
        kernel_root / "intake" / "topics" / topic_slug,
    ]
    for path in paths:
        check(not path.exists(), f"expected a fresh topic slug, but found existing path: {path}")


def run_registration_json(
    *,
    package_root: Path,
    kernel_root: Path,
    topic_slug: str,
    arxiv_id: str,
    metadata_json: Path | None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(package_root / "source-layer" / "scripts" / "register_arxiv_source.py"),
        "--knowledge-root",
        str(kernel_root),
        "--topic-slug",
        topic_slug,
        "--arxiv-id",
        arxiv_id,
        "--registered-by",
        "acceptance-script",
        "--skip-enrichment",
        "--skip-graph-build",
        "--json",
    ]
    if metadata_json is not None:
        command.extend(["--metadata-json", str(metadata_json)])
    return run_script_json(command=command, cwd=package_root)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.use_package_root_as_kernel and args.work_root:
        raise RuntimeError("--work-root cannot be combined with --use-package-root-as-kernel.")

    if args.use_package_root_as_kernel:
        work_root = package_root
        kernel_root = package_root
    else:
        work_root = (
            Path(args.work_root).expanduser().resolve()
            if args.work_root
            else Path(tempfile.mkdtemp(prefix="aitp-first-run-acceptance-")).resolve()
        )
        kernel_root = work_root / "kernel"
        prepare_first_run_kernel(package_root, kernel_root)

    assert_topic_is_fresh(kernel_root, args.topic_slug)

    bootstrap_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "bootstrap",
            "--topic",
            TOPIC_TITLE,
            "--topic-slug",
            args.topic_slug,
            "--statement",
            TOPIC_STATEMENT,
            "--json",
        ],
    )
    loop_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            LOOP_REQUEST,
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "status",
            "--topic-slug",
            args.topic_slug,
            "--json",
        ],
    )

    check(bootstrap_payload["topic_slug"] == args.topic_slug, "bootstrap should create the expected topic slug")
    check(loop_payload["topic_slug"] == args.topic_slug, "loop should stay on the same topic")
    check(status_payload["topic_slug"] == args.topic_slug, "status should read the same topic")
    check(loop_payload["load_profile"] == "light", "first-run loop should stay in the light runtime profile")
    check(bool(status_payload.get("selected_action_id")), "status should expose the next bounded action")
    selected_action_summary = str(status_payload.get("selected_action_summary") or "")
    check(
        "discover_and_register.py" in selected_action_summary
        and "register_arxiv_source.py" in selected_action_summary,
        "status should expose the concrete L0 source handoff before registration.",
    )

    ensure_exists(Path(bootstrap_payload["files"]["topic_state"]))
    ensure_exists(Path(bootstrap_payload["files"]["runtime_protocol"]))
    ensure_exists(Path(loop_payload["loop_state_path"]))
    ensure_exists(Path(loop_payload["runtime_protocol"]["runtime_protocol_path"]))
    ensure_exists(Path(status_payload["runtime_protocol_path"]))
    ensure_exists(Path(status_payload["runtime_protocol_note_path"]))

    registration_payload = None
    status_after_registration = None
    if args.register_arxiv_id:
        metadata_json = (
            Path(args.registration_metadata_json).expanduser().resolve()
            if args.registration_metadata_json
            else None
        )
        registration_payload = run_registration_json(
            package_root=package_root,
            kernel_root=kernel_root,
            topic_slug=args.topic_slug,
            arxiv_id=args.register_arxiv_id,
            metadata_json=metadata_json,
        )
        ensure_exists(Path(registration_payload["layer0_source_json"]))
        ensure_exists(Path(registration_payload["layer0_snapshot"]))
        check(
            str((registration_payload.get("runtime_status_sync") or {}).get("status") or "") == "refreshed",
            "registration should refresh runtime status surfaces when the topic runtime already exists.",
        )
        status_after_registration = run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=[
                "status",
                "--topic-slug",
                args.topic_slug,
                "--json",
            ],
        )
        check(
            int(
                (
                    ((status_after_registration.get("active_research_contract") or {}).get("l1_source_intake") or {}).get(
                        "source_count"
                    )
                    or 0
                )
            )
            >= 1,
            "status after registration should expose at least one registered source immediately.",
        )
        post_registration_summary = str(status_after_registration.get("selected_action_summary") or "")
        check(
            "discover_and_register.py" not in post_registration_summary
            and "register_arxiv_source.py" not in post_registration_summary,
            "status after registration should move off the stale L0 source handoff wording.",
        )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "bootstrap": bootstrap_payload,
        "loop": loop_payload,
        "status": status_payload,
    }
    if registration_payload is not None:
        payload["registration"] = registration_payload
    if status_after_registration is not None:
        payload["status_after_registration"] = status_after_registration
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "first-run topic acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"loop_state: {loop_payload['loop_state_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
