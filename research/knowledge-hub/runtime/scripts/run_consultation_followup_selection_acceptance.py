#!/usr/bin/env python
"""Isolated acceptance for closing consultation_followup into a selected staged candidate."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from run_first_run_topic_acceptance import KERNEL_ROOT, REPO_ROOT, TOPIC_SLUG
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
        else Path(
            tempfile.mkdtemp(prefix="aitp-consultation-followup-selection-acceptance-")
        ).resolve()
    )
    kernel_root = work_root / "kernel"
    prepare_first_run_kernel(package_root, kernel_root)
    assert_topic_is_fresh(kernel_root, args.topic_slug)

    metadata_json = (
        Path(args.registration_metadata_json).expanduser().resolve()
        if args.registration_metadata_json
        else None
    )

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
    pre_selection_next = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    pre_selection_status = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )

    consultation_summary = (
        "Consult the topic-local staged L2 memory and choose one bounded candidate before deeper execution."
    )
    check(
        str(pre_selection_next.get("selected_action_summary") or "") == consultation_summary,
        "Expected `next` to surface consultation_followup before the final continue step.",
    )
    check(
        str(pre_selection_status.get("selected_action_summary") or "") == consultation_summary,
        "Expected `status` to surface consultation_followup before the final continue step.",
    )

    selection_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue by choosing one bounded staged candidate.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    post_selection_next = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    post_selection_status = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )

    selection_path = (
        kernel_root / "topics" / args.topic_slug / "runtime"
        / "consultation_followup_selection.active.json"
    )
    selection_payload = json.loads(selection_path.read_text(encoding="utf-8"))
    check(
        str(post_selection_next.get("selected_action_type") or "")
        == "selected_consultation_candidate_followup",
        "Expected `next` to advance from consultation_followup to the selected candidate summary.",
    )
    check(
        str(post_selection_status.get("selected_action_type") or "")
        == "selected_consultation_candidate_followup",
        "Expected `status` to advance from consultation_followup to the selected candidate summary.",
    )
    check(
        "Review the selected staged candidate"
        in str(post_selection_next.get("selected_action_summary") or ""),
        "Expected `next` summary to name the selected staged candidate.",
    )
    check(
        "Review the selected staged candidate"
        in str(post_selection_status.get("selected_action_summary") or ""),
        "Expected `status` summary to name the selected staged candidate.",
    )
    check(selection_path.exists(), "Expected consultation_followup_selection.active.json to be materialized.")
    check(
        str(selection_payload.get("status") or "") == "selected",
        "Expected consultation-followup selection status to be `selected`.",
    )
    check(
        str(selection_payload.get("selected_candidate_topic_slug") or "") == args.topic_slug,
        "Expected the selected consultation candidate to remain topic-local.",
    )
    auto_actions = (selection_loop.get("auto_actions") or {}).get("executed") or []
    check(auto_actions, "Expected the final continue step to execute one consultation_followup auto action.")
    check(
        auto_actions[0]["action_type"] == "consultation_followup"
        and auto_actions[0]["status"] == "completed",
        "Expected consultation_followup to complete during the final continue step.",
    )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "bootstrap": bootstrap_payload,
        "initial_loop": initial_loop,
        "registration": registration_payload,
        "followthrough_loop": followthrough_loop,
        "reentry_loop": reentry_loop,
        "selection_loop": selection_loop,
        "pre_selection_next": pre_selection_next,
        "pre_selection_status": pre_selection_status,
        "next": post_selection_next,
        "status": post_selection_status,
        "selection": selection_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "consultation followup selection acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"selected_candidate: {selection_payload.get('selected_candidate_id') or '(none)'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
