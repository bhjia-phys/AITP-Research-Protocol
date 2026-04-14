#!/usr/bin/env python
"""Isolated acceptance for advancing beyond selected consultation candidate summary."""

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
            tempfile.mkdtemp(prefix="aitp-selected-candidate-route-choice-acceptance-")
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
    pre_route_choice_next = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    route_choice_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue and choose the first honest deeper route for the selected staged candidate.",
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

    route_choice_path = (
        kernel_root
        / "runtime"
        / "topics"
        / args.topic_slug
        / "selected_candidate_route_choice.active.json"
    )
    route_choice_payload = json.loads(route_choice_path.read_text(encoding="utf-8"))
    check(
        str(pre_route_choice_next.get("selected_action_type") or "")
        == "selected_consultation_candidate_followup",
        "Expected selected-candidate summary before the fifth continue step.",
    )
    check(
        str(next_payload.get("selected_action_type") or "") == "l2_promotion_review",
        "Expected `next` to advance from selected-candidate summary into the first deeper route choice.",
    )
    check(
        str(status_payload.get("selected_action_type") or "") == "l2_promotion_review",
        "Expected `status` to advance from selected-candidate summary into the first deeper route choice.",
    )
    check(
        "Review Layer 2 promotion" in str(next_payload.get("selected_action_summary") or ""),
        "Expected `next` summary to expose Layer 2 promotion review for the selected staged candidate.",
    )
    check(
        "Review Layer 2 promotion" in str(status_payload.get("selected_action_summary") or ""),
        "Expected `status` summary to expose Layer 2 promotion review for the selected staged candidate.",
    )
    check(route_choice_path.exists(), "Expected selected_candidate_route_choice.active.json to be materialized.")
    check(
        str(route_choice_payload.get("chosen_action_type") or "") == "l2_promotion_review",
        "Expected the chosen deeper route to be Layer 2 promotion review on the isolated baseline.",
    )
    check(
        str(route_choice_payload.get("selected_candidate_id") or "").strip(),
        "Expected the route-choice artifact to retain the selected candidate id.",
    )
    auto_actions = (route_choice_loop.get("auto_actions") or {}).get("executed") or []
    check(not auto_actions, "Expected the fifth continue step to derive route choice without additional auto-action execution.")

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "bootstrap": bootstrap_payload,
        "initial_loop": initial_loop,
        "registration": registration_payload,
        "followthrough_loop": followthrough_loop,
        "reentry_loop": reentry_loop,
        "selection_loop": selection_loop,
        "route_choice_loop": route_choice_loop,
        "pre_route_choice_next": pre_route_choice_next,
        "next": next_payload,
        "status": status_payload,
        "route_choice": route_choice_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "selected candidate route choice acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"chosen_action_type: {route_choice_payload.get('chosen_action_type') or '(missing)'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
