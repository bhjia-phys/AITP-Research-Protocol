#!/usr/bin/env python
"""Isolated acceptance for advancing beyond staged-L2 review on the same fresh topic."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from run_first_run_topic_acceptance import KERNEL_ROOT, REPO_ROOT, TOPIC_SLUG
from run_staged_l2_reentry_acceptance import main as _unused  # noqa: F401
from run_first_run_topic_acceptance import (
    assert_topic_is_fresh,
    check,
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
        else Path(tempfile.mkdtemp(prefix="aitp-staged-l2-advancement-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)
    assert_topic_is_fresh(kernel_root, args.topic_slug)

    metadata_json = (
        Path(args.registration_metadata_json).expanduser().resolve()
        if args.registration_metadata_json
        else None
    )

    run_cli_json(
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
    first_loop = run_cli_json(
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
    registration_payload = run_registration_json(
        package_root=package_root,
        kernel_root=kernel_root,
        topic_slug=args.topic_slug,
        arxiv_id=args.register_arxiv_id,
        metadata_json=metadata_json,
    )
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
    reentry_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue from the staged L2 review and keep the next step bounded.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    next_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )

    advanced_summary = "Consult the topic-local staged L2 memory and choose one bounded candidate before deeper execution."
    check(
        str(next_payload.get("selected_action_summary") or "") == advanced_summary,
        "Expected `next` to advance beyond staged-L2 review after the third bounded continue step.",
    )
    check(
        str(status_payload.get("selected_action_summary") or "") == advanced_summary,
        "Expected `status` to advance beyond staged-L2 review after the third bounded continue step.",
    )
    check(
        str(((next_payload.get("h_plane") or {}).get("overall_status")) or "") == "steady",
        "Expected `next` h_plane to remain steady during staged-L2 advancement.",
    )
    check(
        str(((status_payload.get("h_plane") or {}).get("overall_status")) or "") == "steady",
        "Expected `status` h_plane to remain steady during staged-L2 advancement.",
    )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "initial_loop": first_loop,
        "registration": registration_payload,
        "followthrough_loop": followthrough_loop,
        "reentry_loop": reentry_loop,
        "next": next_payload,
        "status": status_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "staged-l2 advancement acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"advanced_summary: {advanced_summary}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
