#!/usr/bin/env python
"""Isolated acceptance for approved staged-candidate writeback into L2."""

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
            tempfile.mkdtemp(prefix="aitp-scpw-")
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
    run_cli_json(
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
    run_registration_json(
        package_root=package_root,
        kernel_root=kernel_root,
        topic_slug=args.topic_slug,
        arxiv_id=args.register_arxiv_id,
        metadata_json=metadata_json,
    )
    for loop_args in (
        [
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--max-auto-steps",
            "1",
            "--json",
        ],
        [
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue from the staged L2 review and keep the next step bounded.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
        [
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue by choosing one bounded staged candidate.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
        [
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue and choose the first honest deeper route for the selected staged candidate.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
        [
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue from the promotion-review summary and materialize the first explicit gate.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    ):
        run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=loop_args,
        )

    gate_path = kernel_root / "runtime" / "topics" / args.topic_slug / "promotion_gate.json"
    gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))
    candidate_id = str(gate_payload.get("candidate_id") or "").strip()
    check(candidate_id, "Expected the explicit promotion gate to retain the staged candidate id.")

    approve_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "approve-promotion",
            "--topic-slug",
            args.topic_slug,
            "--candidate-id",
            candidate_id,
            "--json",
        ],
    )
    check(
        str(approve_payload.get("status") or "") == "approved",
        "Expected approval to mark the explicit promotion gate as approved.",
    )

    loop_after_approve = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue after explicit approval and keep the next writeback step bounded.",
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
    check(
        str(next_payload.get("selected_action_type") or "") == "promote_candidate",
        "Expected front-door routing to advance into promote_candidate after approval.",
    )

    promote_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "promote",
            "--topic-slug",
            args.topic_slug,
            "--candidate-id",
            candidate_id,
            "--json",
        ],
    )
    final_gate_payload = json.loads(gate_path.read_text(encoding="utf-8"))
    next_after_promote = run_cli_json(
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

    check(
        str(final_gate_payload.get("status") or "") == "promoted",
        "Expected promote to complete and mark the gate as promoted.",
    )
    target_unit_path = Path(str(promote_payload.get("target_unit_path") or ""))
    check(target_unit_path.exists(), "Expected promote to write the target L2 backend unit.")
    check(
        str(next_after_promote.get("selected_action_type") or "") != "promote_candidate",
        "Expected `next` to move past promote_candidate after writeback succeeds.",
    )
    check(
        str(status_payload.get("selected_action_type") or "") != "promote_candidate",
        "Expected `status` to move past promote_candidate after writeback succeeds.",
    )
    post_completion_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue after promoted writeback and keep the next step bounded.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    next_after_completion = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    status_after_completion = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )
    check(
        str(next_after_completion.get("selected_action_type") or "") != "assess_topic_completion",
        "Expected `next` to move beyond repeated topic-completion refresh once that refresh is current.",
    )
    check(
        str(status_after_completion.get("selected_action_type") or "") != "assess_topic_completion",
        "Expected `status` to move beyond repeated topic-completion refresh once that refresh is current.",
    )
    post_inspect_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue after promoted inspection and keep the next step bounded.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    next_after_post_inspect = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    status_after_post_inspect = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )
    check(
        str(next_after_post_inspect.get("selected_action_type") or "") == "review_topic_completion_blockers",
        "Expected `next` to advance from generic post-promotion inspect into explicit topic-completion blocker review.",
    )
    check(
        str(status_after_post_inspect.get("selected_action_type") or "") == "review_topic_completion_blockers",
        "Expected `status` to advance from generic post-promotion inspect into explicit topic-completion blocker review.",
    )
    post_blocker_loop = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue after reviewing topic-completion blockers.",
            "--max-auto-steps",
            "1",
            "--json",
        ],
    )
    next_after_blocker_review = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["next", "--topic-slug", args.topic_slug, "--json"],
    )
    status_after_blocker_review = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", args.topic_slug, "--json"],
    )
    check(
        str(next_after_blocker_review.get("selected_action_type") or "") == "review_statement_compilation",
        "Expected `next` to advance from topic-completion blocker review into explicit statement-compilation review.",
    )
    check(
        str(status_after_blocker_review.get("selected_action_type") or "") == "review_statement_compilation",
        "Expected `status` to advance from topic-completion blocker review into explicit statement-compilation review.",
    )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "candidate_id": candidate_id,
        "approve": approve_payload,
        "loop_after_approve": loop_after_approve,
        "next_after_approve": next_payload,
        "promote": promote_payload,
        "promotion_gate": final_gate_payload,
        "next_after_promote": next_after_promote,
        "status_after_promote": status_payload,
        "post_completion_loop": post_completion_loop,
        "next_after_completion": next_after_completion,
        "status_after_completion": status_after_completion,
        "post_inspect_loop": post_inspect_loop,
        "next_after_post_inspect": next_after_post_inspect,
        "status_after_post_inspect": status_after_post_inspect,
        "post_blocker_loop": post_blocker_loop,
        "next_after_blocker_review": next_after_blocker_review,
        "status_after_blocker_review": status_after_blocker_review,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "selected candidate promotion writeback acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"candidate_id: {candidate_id}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
