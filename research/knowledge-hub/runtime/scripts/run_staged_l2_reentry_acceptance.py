#!/usr/bin/env python
"""Isolated acceptance for staged-L2 review reentry under benign continue steering."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from run_first_run_topic_acceptance import (
    KERNEL_ROOT,
    REPO_ROOT,
    TOPIC_SLUG,
    assert_topic_is_fresh,
    check,
    ensure_exists,
    prepare_first_run_kernel,
    run_cli_json,
    run_registration_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic-slug", default=TOPIC_SLUG)
    parser.add_argument("--register-arxiv-id", required=True)
    parser.add_argument("--registration-metadata-json")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-staged-l2-reentry-acceptance-")).resolve()
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
            "Jones Chapter 4 finite-dimensional backbone",
            "--topic-slug",
            args.topic_slug,
            "--statement",
            "Start from the finite-dimensional backbone and record the first honest closure target.",
            "--json",
        ],
    )
    initial_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue with the first bounded route.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
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

    followthrough_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    auto_actions = followthrough_loop.get("auto_actions") or {}
    executed = auto_actions.get("executed") or []
    check(executed, "Expected one bounded literature-intake follow-through action to execute.")
    check(
        executed[0]["action_type"] == "literature_intake_stage" and executed[0]["status"] == "completed",
        "Expected literature_intake_stage to complete before staged-L2 reentry.",
    )
    staging = (executed[0].get("result") or {}).get("staging") or {}
    ensure_exists(Path(staging["manifest_json_path"]))
    check(int(staging.get("entry_count") or 0) >= 1, "Expected at least one staged entry before reentry.")

    next_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "next",
            "--topic-slug",
            args.topic_slug,
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

    expected_summary = "Inspect the current L2 staging manifest before continuing."
    check(
        str(next_payload.get("selected_action_summary") or "") == expected_summary,
        "Expected `next` to stay focused on staged-L2 review under benign continue steering.",
    )
    check(
        str(status_payload.get("selected_action_summary") or "") == expected_summary,
        "Expected `status` to stay focused on staged-L2 review under benign continue steering.",
    )
    check(
        str(((next_payload.get("h_plane") or {}).get("overall_status")) or "") == "steady",
        "Expected `next` h_plane to remain steady under benign continue steering.",
    )
    check(
        str(((status_payload.get("h_plane") or {}).get("overall_status")) or "") == "steady",
        "Expected `status` h_plane to remain steady under benign continue steering.",
    )
    check(
        str(next_payload.get("open_next") or "").replace("\\", "/").endswith("topic_dashboard.md"),
        "Expected primary reentry surface to remain on the topic dashboard.",
    )

    consult_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "consult-l2",
            "--query-text",
            "topological order anyon condensation",
            "--retrieval-profile",
            "l1_provisional_understanding",
            "--include-staging",
            "--topic-slug",
            args.topic_slug,
            "--stage",
            "L1",
            "--run-id",
            str(followthrough_loop.get("run_id") or ""),
            "--json",
        ],
    )
    staged_hits = consult_payload.get("staged_hits") or []
    check(staged_hits, "Expected public consult-l2 to return staged hits during reentry.")
    check(
        any(str(row.get("topic_slug") or "").strip() == args.topic_slug for row in staged_hits),
        "Expected at least one topic-local staged hit during reentry.",
    )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "bootstrap": bootstrap_payload,
        "initial_loop": initial_loop,
        "registration": registration_payload,
        "followthrough_loop": followthrough_loop,
        "next": next_payload,
        "status": status_payload,
        "consult": {
            "primary_hit_count": len(consult_payload.get("primary_hits") or []),
            "staged_hit_count": len(staged_hits),
            "topic_local_staged_hit_count": sum(
                1 for row in staged_hits if str(row.get("topic_slug") or "").strip() == args.topic_slug
            ),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "staged-l2 reentry acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"reentry_summary: {expected_summary}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
