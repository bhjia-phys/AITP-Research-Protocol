#!/usr/bin/env python
"""Shared bounded acceptance harness for deep-execution runtime parity."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from run_first_run_topic_acceptance import (
    KERNEL_ROOT,
    LOOP_REQUEST,
    REPO_ROOT,
    TOPIC_SLUG,
    TOPIC_STATEMENT,
    TOPIC_TITLE,
    check,
    ensure_exists,
    prepare_first_run_kernel,
    run_cli_json,
)


ENTRY_SURFACES = {
    "codex": "native `using-aitp` skill discovery",
    "claude_code": "Claude SessionStart bootstrap",
    "opencode": "OpenCode plugin bootstrap",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=sorted(ENTRY_SURFACES), required=True)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def acceptance_command(runtime: str) -> str:
    return f"python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime {runtime} --json"


def expected_artifacts(topic_slug: str) -> list[str]:
    return [
        f"runtime/topics/{topic_slug}/topic_state.json",
        f"runtime/topics/{topic_slug}/loop_state.json",
        f"runtime/topics/{topic_slug}/runtime_protocol.generated.json",
        f"runtime/topics/{topic_slug}/runtime_protocol.generated.md",
        f"status --topic-slug {topic_slug} --json -> selected_action_id",
    ]


def pending_probe_payload(runtime: str) -> dict[str, Any]:
    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": runtime,
        "baseline_runtime": "codex",
        "status": "probe_pending",
        "entry_surface": ENTRY_SURFACES[runtime],
        "acceptance_command": acceptance_command(runtime),
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": [],
        "blockers": ["runtime_specific_probe_not_implemented"],
        "notes": [
            "The shared parity harness exists now, but this runtime-specific deep-execution probe has not landed yet.",
            "Use the Codex baseline report as the current artifact bar until the dedicated probe is implemented.",
        ],
    }


def codex_baseline_payload(*, package_root: Path, repo_root: Path, work_root: Path) -> dict[str, Any]:
    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)

    bootstrap_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "bootstrap",
            "--topic",
            TOPIC_TITLE,
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
            TOPIC_SLUG,
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
            TOPIC_SLUG,
            "--json",
        ],
    )

    check(bootstrap_payload["topic_slug"] == TOPIC_SLUG, "bootstrap should create the expected topic slug")
    check(loop_payload["topic_slug"] == TOPIC_SLUG, "loop should stay on the same topic")
    check(status_payload["topic_slug"] == TOPIC_SLUG, "status should read the same topic")
    check(loop_payload["load_profile"] == "light", "Codex baseline should stay in the light runtime profile")
    check(bool(status_payload.get("selected_action_id")), "status should expose the next bounded action")

    checked_artifacts = [
        {"label": "topic_state", "path": str(Path(bootstrap_payload["files"]["topic_state"])), "status": "present"},
        {"label": "bootstrap_runtime_protocol", "path": str(Path(bootstrap_payload["files"]["runtime_protocol"])), "status": "present"},
        {"label": "loop_state", "path": str(Path(loop_payload["loop_state_path"])), "status": "present"},
        {"label": "loop_runtime_protocol", "path": str(Path(loop_payload["runtime_protocol"]["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol", "path": str(Path(status_payload["runtime_protocol_path"])), "status": "present"},
        {"label": "status_runtime_protocol_note", "path": str(Path(status_payload["runtime_protocol_note_path"])), "status": "present"},
    ]
    for row in checked_artifacts:
        ensure_exists(Path(row["path"]))

    return {
        "report_kind": "runtime_deep_execution_parity",
        "runtime": "codex",
        "baseline_runtime": "codex",
        "status": "baseline_ready",
        "entry_surface": ENTRY_SURFACES["codex"],
        "acceptance_command": acceptance_command("codex"),
        "topic_slug": TOPIC_SLUG,
        "load_profile": loop_payload["load_profile"],
        "expected_artifacts": expected_artifacts(TOPIC_SLUG),
        "checked_artifacts": checked_artifacts,
        "blockers": [],
        "notes": [
            "This is the current deep-execution baseline for v1.67.",
            "Future Claude Code and OpenCode probes should be compared against this artifact footprint and bounded-route behavior.",
        ],
        "work_root": str(work_root),
        "bootstrap": bootstrap_payload,
        "loop": loop_payload,
        "status_payload": status_payload,
    }


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if args.runtime == "codex":
        work_root = (
            Path(args.work_root).expanduser().resolve()
            if args.work_root
            else Path(tempfile.mkdtemp(prefix="aitp-runtime-parity-codex-")).resolve()
        )
        payload = codex_baseline_payload(package_root=package_root, repo_root=repo_root, work_root=work_root)
    else:
        payload = pending_probe_payload(args.runtime)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "runtime parity acceptance\n"
            f"runtime: {payload['runtime']}\n"
            f"status: {payload['status']}\n"
            f"acceptance: {payload['acceptance_command']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
