#!/usr/bin/env python
"""Isolated acceptance for fresh-topic first-source follow-through into L2 staging."""

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


def _service(package_root: Path, kernel_root: Path, repo_root: Path):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from knowledge_hub.aitp_service import AITPService

    return AITPService(kernel_root=kernel_root, repo_root=repo_root)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-first-source-followthrough-acceptance-")).resolve()
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
    loop_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "loop",
            "--topic-slug",
            args.topic_slug,
            "--human-request",
            "Continue with the first bounded route and stop before expensive execution.",
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
    selected_action_summary = str(status_payload.get("selected_action_summary") or "")
    check(
        "discover_and_register.py" in selected_action_summary
        and "register_arxiv_source.py" in selected_action_summary,
        "status should expose the concrete L0 source handoff before registration.",
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
    post_registration_summary = str(status_after_registration.get("selected_action_summary") or "")
    check(
        post_registration_summary == "Stage bounded literature-intake units from the current L1 vault into L2 staging.",
        "status after registration should expose the literature-intake follow-through step.",
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
    auto_actions = followthrough_loop.get("auto_actions") or {}
    executed = auto_actions.get("executed") or []
    check(executed, "Expected one bounded follow-through auto action to execute.")
    check(
        executed[0]["action_type"] == "literature_intake_stage" and executed[0]["status"] == "completed",
        "Expected literature_intake_stage to complete during the first post-registration follow-through.",
    )
    staging = (executed[0].get("result") or {}).get("staging") or {}
    manifest_path = Path(staging["manifest_json_path"])
    ensure_exists(manifest_path)
    check(int(staging.get("entry_count") or 0) >= 1, "Expected at least one staged L2 entry from the first follow-through.")

    status_after_followthrough = run_cli_json(
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
    followthrough_summary = str(status_after_followthrough.get("selected_action_summary") or "")
    check(
        followthrough_summary == "Inspect the current L2 staging manifest before continuing.",
        "status after follow-through should advance to staging review instead of repeating literature_intake_stage.",
    )
    must_read_paths = {
        str(item.get("path") or "").replace("\\", "/")
        for item in (status_after_followthrough.get("must_read_now") or [])
        if isinstance(item, dict)
    }
    check(
        "canonical/staging/workspace_staging_manifest.json" in must_read_paths,
        "status after follow-through should foreground the workspace staging manifest.",
    )

    service = _service(package_root, kernel_root, repo_root)
    consult_payload = service.consult_l2(
        query_text="topological order anyon condensation",
        retrieval_profile="l1_provisional_understanding",
        include_staging=True,
        topic_slug=args.topic_slug,
        stage="L1",
        run_id=str(followthrough_loop.get("run_id") or ""),
        updated_by="first-source-followthrough-acceptance",
        record_consultation=False,
    )
    staged_hits = consult_payload.get("staged_hits") or []
    check(staged_hits, "Expected consult_l2(include_staging=True) to surface the freshly staged follow-through entries.")
    check(
        any(str(row.get("topic_slug") or "").strip() == args.topic_slug for row in staged_hits),
        "Expected at least one staged hit from the current fresh topic.",
    )

    payload = {
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "bootstrap": bootstrap_payload,
        "initial_loop": loop_payload,
        "status": status_payload,
        "registration": registration_payload,
        "status_after_registration": status_after_registration,
        "followthrough_loop": followthrough_loop,
        "status_after_followthrough": status_after_followthrough,
        "consult_after_followthrough": {
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
            "first-source follow-through acceptance passed\n"
            f"topic_slug: {args.topic_slug}\n"
            f"staging_manifest: {manifest_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
