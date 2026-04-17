#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route transition-authority surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import run_hypothesis_route_transition_commitment_acceptance as commitment_acceptance


build_parser = commitment_acceptance.build_parser
ensure_exists = commitment_acceptance.ensure_exists
check = commitment_acceptance.check
run_cli_json = commitment_acceptance.run_cli_json
read_jsonl = commitment_acceptance.read_jsonl


def seed_demo_runtime(kernel_root: Path, *, topic_slug: str, route_mode: str) -> None:
    if route_mode != "current_target_missing_route_ref":
        commitment_acceptance.seed_demo_runtime(kernel_root, topic_slug=topic_slug, route_mode=route_mode)
        return

    commitment_acceptance.seed_demo_runtime(kernel_root, topic_slug=topic_slug, route_mode="current_target")
    contract_path = kernel_root / "topics" / topic_slug / "runtime" / "research_question.contract.json"
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["question"] = "Has the committed route become the authoritative bounded truth surface yet?"
    payload["scope"] = [
        "Keep route transition authority bounded to explicit commitment and current topic truth surfaces."
    ]
    payload["non_goals"] = [
        "Do not auto-assert route authority or mutate runtime state in this slice."
    ]
    payload["observables"] = [
        "Route transition authority should stay explicit on the active topic surface."
    ]
    payload["deliverables"] = [
        "Keep route transition authority durable on the active topic surface."
    ]
    payload["acceptance_tests"] = [
        "Runtime status and replay expose route transition authority directly."
    ]
    payload["forbidden_proxies"] = [
        "Do not infer route transition authority from prose-only notes."
    ]
    payload["uncertainty_markers"] = [
        "The committed route may still lack aligned current-topic truth surfaces."
    ]
    payload["competing_hypotheses"][0]["summary"] = (
        "The symmetry-breaking route is active, but its durable route ref still points at transition history instead of a current-topic truth surface."
    )
    payload["competing_hypotheses"][0]["route_target_ref"] = (
        f"topics/{topic_slug}/runtime/transition_history.md"
    )
    contract_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else commitment_acceptance.Path(
            commitment_acceptance.tempfile.mkdtemp(
                prefix="aitp-hypothesis-route-transition-authority-acceptance-"
            )
        ).resolve()
    )
    kernel_root = work_root / "kernel"
    commitment_acceptance.shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    commitment_acceptance.shutil.copytree(
        package_root / "runtime" / "schemas",
        kernel_root / "runtime" / "schemas",
        dirs_exist_ok=True,
    )
    commitment_acceptance.shutil.copytree(
        package_root / "runtime" / "scripts",
        kernel_root / "runtime" / "scripts",
        dirs_exist_ok=True,
    )

    topics = [
        ("demo-topic-no-authority", "current_weak", "none"),
        ("demo-topic-authority-waiting", "deferred_target", "waiting_commitment"),
        ("demo-topic-authority-pending", "current_target_missing_route_ref", "pending_authority"),
        ("demo-topic-authority-authoritative", "current_target", "authoritative"),
    ]
    artifacts: dict[str, dict[str, str]] = {}
    checks: dict[str, dict[str, Any]] = {}
    for topic_slug, route_mode, expected_status in topics:
        seed_demo_runtime(kernel_root, topic_slug=topic_slug, route_mode=route_mode)
        status_payload = run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=["status", "--topic-slug", topic_slug, "--json"],
        )
        replay_payload = run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=["replay-topic", "--topic-slug", topic_slug, "--json"],
        )

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
        replay_json = Path(replay_payload["json_path"])
        replay_md = Path(replay_payload["markdown_path"])
        transition_history_note = kernel_root / "topics" / topic_slug / "runtime" / "transition_history.md"
        for path in (runtime_protocol_note, replay_json, replay_md):
            ensure_exists(path)
        if route_mode != "current_weak":
            ensure_exists(transition_history_note)

        authority = status_payload["active_research_contract"]["route_transition_authority"]
        replay_bundle = replay_payload["payload"]
        runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
        replay_text = replay_md.read_text(encoding="utf-8")

        check(authority["authority_status"] == expected_status, f"Expected {topic_slug} to expose `{expected_status}`.")
        check(
            replay_bundle["route_transition_authority"]["authority_status"] == expected_status,
            f"Expected replay to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["current_position"]["route_transition_authority_status"] == expected_status,
            f"Expected replay current position to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["conclusions"]["route_transition_authority_status"] == expected_status,
            f"Expected replay conclusions to expose `{expected_status}` for {topic_slug}.",
        )
        check("## Route transition authority" in runtime_protocol_text, f"Expected runtime protocol to include route transition authority for {topic_slug}.")
        check("## Route Transition Authority" in replay_text, f"Expected replay markdown to include route transition authority for {topic_slug}.")

        if expected_status == "none":
            check(authority["authority_kind"] == "none", "Expected the no-authority topic to keep kind none.")
        elif expected_status == "waiting_commitment":
            check(authority["authority_kind"] == "commitment_not_ready", "Expected the waiting topic to expose commitment_not_ready.")
        elif expected_status == "pending_authority":
            check(authority["authority_kind"] == "authority_ref_not_current_topic", "Expected the pending topic to expose authority_ref_not_current_topic.")
            check(authority["route_kind"] == "current_topic", "Expected the pending topic to keep current_topic route kind.")
            check("transition_history.md" in (authority.get("route_target_ref") or ""), "Expected the pending topic to keep a non-current-topic route target ref visible.")
        else:
            check(authority["authority_kind"] == "current_topic_authoritative", "Expected the authoritative topic to expose current_topic_authoritative.")
            check(authority["route_kind"] == "current_topic", "Expected the authoritative topic to keep current_topic route kind.")
            check(
                f"topics/{topic_slug}/runtime/" in (authority.get("authority_ref") or ""),
                f"Expected the authoritative topic to keep a current-topic authority ref visible for {topic_slug}.",
            )

        candidate_ledger = kernel_root / "topics" / topic_slug / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl"
        reactivated_rows = [
            row
            for row in read_jsonl(candidate_ledger)
            if str(row.get("candidate_id") or "").strip() == "candidate:demo-symmetry-reactivated"
            or str(row.get("reactivated_from") or "").strip()
        ]
        check(
            not reactivated_rows,
            f"Expected the bounded transition-authority slice not to materialize a reactivated deferred candidate for {topic_slug}.",
        )

        artifacts[topic_slug] = {
            "runtime_protocol_note": str(runtime_protocol_note),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
            "transition_history_note": str(transition_history_note),
            "candidate_ledger": str(candidate_ledger),
        }
        checks[topic_slug] = {
            "authority_status": authority["authority_status"],
            "authority_kind": authority["authority_kind"],
            "route_kind": authority["route_kind"],
            "authority_ref": authority["authority_ref"],
        }

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": checks,
        "artifacts": artifacts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
