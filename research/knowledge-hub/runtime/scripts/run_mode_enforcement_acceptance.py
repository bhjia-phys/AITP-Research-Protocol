#!/usr/bin/env python
"""Isolated acceptance for mode-aware runtime enforcement and literature fast path."""

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
PACKAGE_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(PACKAGE_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def copy_kernel_contracts(package_root: Path, kernel_root: Path) -> None:
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
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
    (kernel_root / "intake").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package_root / "intake" / "L1_VAULT_PROTOCOL.md", kernel_root / "intake" / "L1_VAULT_PROTOCOL.md")
    (kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md").write_text("# Guardrails\n", encoding="utf-8")
    (kernel_root / "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md").write_text("# Upstream\n", encoding="utf-8")
    (kernel_root / "SECTION_FORMALIZATION_PROTOCOL.md").write_text("# Section formalization\n", encoding="utf-8")
    exploration_window = package_root / "exploration_window.json"
    if exploration_window.exists():
        shutil.copy2(exploration_window, kernel_root / "exploration_window.json")


def seed_runtime_topic(
    kernel_root: Path,
    *,
    topic_slug: str,
    human_request: str,
    action_rows: list[dict[str, Any]],
    resume_stage: str,
    last_materialized_stage: str | None = None,
    latest_run_id: str | None = "run-001",
    research_mode: str = "formal_derivation",
    interaction_updates: dict[str, Any] | None = None,
) -> Path:
    runtime_root = kernel_root / "runtime" / "topics" / topic_slug
    runtime_root.mkdir(parents=True, exist_ok=True)
    topic_state = {
        "topic_slug": topic_slug,
        "task_type": "open_exploration",
        "resume_stage": resume_stage,
        "last_materialized_stage": last_materialized_stage or resume_stage,
        "research_mode": research_mode,
        "pointers": {
            "control_note_path": f"topics/{topic_slug}/runtime/control_note.md",
        },
    }
    if latest_run_id is not None:
        topic_state["latest_run_id"] = latest_run_id
    write_json(runtime_root / "topic_state.json", topic_state)
    interaction_state = {
        "human_request": human_request,
        "action_queue_surface": {},
        "decision_surface": {},
        "human_edit_surfaces": [],
    }
    if interaction_updates:
        interaction_state.update(interaction_updates)
    write_json(runtime_root / "interaction_state.json", interaction_state)
    if action_rows:
        write_jsonl(runtime_root / "action_queue.jsonl", action_rows)
    else:
        (runtime_root / "action_queue.jsonl").write_text("", encoding="utf-8")
    (runtime_root / "control_note.md").write_text("# Control note\n", encoding="utf-8")
    (runtime_root / "operator_console.md").write_text("# Operator console\n", encoding="utf-8")
    return runtime_root


def seed_discussion_topic(kernel_root: Path) -> None:
    seed_runtime_topic(
        kernel_root,
        topic_slug="demo-discussion",
        human_request="clarify the research direction before deeper work",
        action_rows=[],
        resume_stage="L1",
        latest_run_id=None,
    )


def seed_explore_topic(kernel_root: Path) -> None:
    seed_runtime_topic(
        kernel_root,
        topic_slug="demo-explore",
        human_request="continue this topic and keep the candidate route bounded",
        action_rows=[
            {
                "action_id": "action:demo-explore:01",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the current runtime state.",
                "status": "pending",
                "auto_runnable": False,
                "queue_source": "declared_contract",
                "handler_args": {"run_id": "run-001"},
            }
        ],
        resume_stage="L3",
    )


def seed_verify_topic(kernel_root: Path) -> None:
    runtime_root = seed_runtime_topic(
        kernel_root,
        topic_slug="demo-verify",
        human_request="continue the current verification lane",
        action_rows=[
            {
                "action_id": "action:demo-verify:01",
                "action_type": "dispatch_execution_task",
                "summary": "Dispatch the selected execution task.",
                "status": "pending",
                "auto_runnable": True,
                "queue_source": "declared_contract",
                "handler_args": {"run_id": "run-001", "candidate_id": "candidate:demo"},
            }
        ],
        resume_stage="L3",
        interaction_updates={
            "closed_loop": {
                "selected_route_path": "topics/demo-verify/runtime/selected_validation_route.md",
                "execution_task_path": "topics/demo-verify/runtime/execution_task.md",
            }
        },
    )
    (runtime_root / "selected_validation_route.md").write_text("# Selected validation route\n", encoding="utf-8")
    (runtime_root / "execution_task.md").write_text("# Execution task\n", encoding="utf-8")


def seed_promote_topic(kernel_root: Path) -> None:
    runtime_root = seed_runtime_topic(
        kernel_root,
        topic_slug="demo-promote",
        human_request="review promotion and writeback readiness",
        action_rows=[
            {
                "action_id": "action:demo-promote:01",
                "action_type": "promote_candidate",
                "summary": "Promote the current candidate into Layer 2.",
                "status": "pending",
                "auto_runnable": False,
                "queue_source": "declared_contract",
                "handler_args": {"run_id": "run-001", "candidate_id": "candidate:demo"},
            }
        ],
        resume_stage="L4",
        last_materialized_stage="L4",
    )
    write_json(
        runtime_root / "promotion_gate.json",
        {
            "status": "approved",
            "candidate_id": "candidate:demo",
            "candidate_type": "method",
            "backend_id": "backend:demo",
        },
    )
    (runtime_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")


def register_demo_arxiv_source(package_root: Path, kernel_root: Path, work_root: Path) -> dict[str, Any]:
    metadata_path = work_root / "demo-arxiv-metadata.json"
    write_json(
        metadata_path,
        {
            "arxiv_id": "2401.01234v1",
            "title": "Weak-coupling benchmark note",
            "summary": (
                "Assume weak coupling and benchmark the exact diagonalization method before broader interpretation. "
                "The notation uses H for the effective Hamiltonian."
            ),
            "published": "2024-01-03T00:00:00Z",
            "updated": "2024-01-04T00:00:00Z",
            "authors": ["Demo Author"],
        },
    )
    command = [
        sys.executable,
        str(package_root / "source-layer" / "scripts" / "register_arxiv_source.py"),
        "--knowledge-root",
        str(kernel_root),
        "--topic-slug",
        "demo-literature",
        "--arxiv-id",
        "2401.01234v1",
        "--metadata-json",
        str(metadata_path),
        "--json",
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


def seed_literature_topic(package_root: Path, kernel_root: Path, work_root: Path) -> dict[str, Any]:
    seed_runtime_topic(
        kernel_root,
        topic_slug="demo-literature",
        human_request="Read and extract reusable knowledge from this paper",
        action_rows=[
            {
                "action_id": "action:demo-literature:01",
                "action_type": "inspect_source_intake",
                "summary": "Read and extract reusable knowledge from this paper.",
                "status": "pending",
                "auto_runnable": False,
                "queue_source": "declared_contract",
                "handler_args": {"run_id": "run-001"},
            }
        ],
        resume_stage="L1",
    )
    return register_demo_arxiv_source(package_root, kernel_root, work_root)


def runtime_bundle(service: AITPService, topic_slug: str) -> dict[str, Any]:
    payload = service.topic_status(topic_slug=topic_slug, updated_by="mode-enforcement-acceptance")
    bundle_path = Path(payload["runtime_protocol_path"])
    ensure_exists(bundle_path)
    return json.loads(bundle_path.read_text(encoding="utf-8"))


def active_trigger_names(bundle: dict[str, Any]) -> set[str]:
    return {
        str(row.get("trigger") or "").strip()
        for row in bundle.get("escalation_triggers") or []
        if row.get("active")
    }


def path_list(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("path") or "").strip() for row in rows]


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-mode-enforcement-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"

    copy_kernel_contracts(package_root, kernel_root)
    seed_discussion_topic(kernel_root)
    seed_explore_topic(kernel_root)
    seed_verify_topic(kernel_root)
    seed_promote_topic(kernel_root)
    register_payload = seed_literature_topic(package_root, kernel_root, work_root)

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)

    discussion_bundle = runtime_bundle(service, "demo-discussion")
    discussion_must_read = path_list(discussion_bundle["must_read_now"])
    discussion_deferred = path_list(discussion_bundle["may_defer_until_trigger"])
    check(discussion_bundle["runtime_mode"] == "discussion", "Expected demo-discussion to materialize discussion mode.")
    check("topics/demo-discussion/runtime/operator_checkpoint.active.md" in discussion_must_read, "Expected discussion mode to foreground the active operator checkpoint.")
    check("topics/demo-discussion/runtime/idea_packet.md" in discussion_must_read, "Expected discussion mode to foreground the idea packet.")
    check("topics/demo-discussion/runtime/validation_review_bundle.active.md" not in discussion_must_read, "Discussion mode must defer validation review.")
    check("topics/demo-discussion/runtime/validation_review_bundle.active.md" in discussion_deferred, "Discussion mode must defer validation review into the deferred set.")
    check("topics/demo-discussion/runtime/promotion_readiness.md" in discussion_deferred, "Discussion mode must defer promotion readiness.")

    explore_bundle = runtime_bundle(service, "demo-explore")
    explore_must_read = path_list(explore_bundle["must_read_now"])
    explore_deferred = path_list(explore_bundle["may_defer_until_trigger"])
    check(explore_bundle["runtime_mode"] == "explore", "Expected demo-explore to materialize explore mode.")
    check(explore_bundle.get("active_submode") is None, "Expected demo-explore to stay in the base explore mode.")
    check("topics/demo-explore/runtime/topic_dashboard.md" in explore_must_read, "Explore mode must foreground the topic dashboard.")
    check("topics/demo-explore/runtime/research_question.contract.md" in explore_must_read, "Explore mode must foreground the research contract.")
    check("topics/demo-explore/runtime/validation_review_bundle.active.md" not in explore_must_read, "Explore mode must defer validation review.")
    check("topics/demo-explore/runtime/validation_review_bundle.active.md" in explore_deferred, "Explore mode must defer validation review.")

    verify_bundle = runtime_bundle(service, "demo-verify")
    verify_must_read = path_list(verify_bundle["must_read_now"])
    verify_deferred = path_list(verify_bundle["may_defer_until_trigger"])
    verify_active_triggers = active_trigger_names(verify_bundle)
    check(verify_bundle["runtime_mode"] == "verify", "Expected demo-verify to materialize verify mode.")
    check("topics/demo-verify/runtime/validation_review_bundle.active.md" in verify_must_read, "Verify mode must foreground validation review.")
    check("topics/demo-verify/runtime/validation_contract.active.md" in verify_must_read, "Verify mode must foreground validation contract.")
    check("topics/demo-verify/runtime/selected_validation_route.md" in verify_must_read, "Verify mode must foreground the selected validation route.")
    check("topics/demo-verify/runtime/execution_task.md" in verify_must_read, "Verify mode must foreground the execution task surface.")
    check("topics/demo-verify/runtime/promotion_readiness.md" in verify_deferred, "Verify mode must defer promotion readiness.")
    check("verification_route_selection" in verify_active_triggers, "Verify mode must keep verification_route_selection active.")
    check("formal_theory_upstream_scan" not in verify_active_triggers, "Verify mode must suppress unrelated formal_theory_upstream_scan triggers.")

    promote_bundle = runtime_bundle(service, "demo-promote")
    promote_must_read = path_list(promote_bundle["must_read_now"])
    promote_deferred = path_list(promote_bundle["may_defer_until_trigger"])
    promote_active_triggers = active_trigger_names(promote_bundle)
    check(promote_bundle["runtime_mode"] == "promote", "Expected demo-promote to materialize promote mode.")
    check("topics/demo-promote/runtime/promotion_readiness.md" in promote_must_read, "Promote mode must foreground promotion readiness.")
    check("topics/demo-promote/runtime/promotion_gate.md" in promote_must_read, "Promote mode must foreground the promotion gate.")
    check("topics/demo-promote/runtime/control_note.md" not in promote_must_read, "Promote mode must defer unrelated control-note history.")
    check("topics/demo-promote/runtime/control_note.md" in promote_deferred, "Promote mode must defer unrelated control-note history.")
    check("promotion_intent" in promote_active_triggers, "Promote mode must keep promotion_intent active.")
    check("verification_route_selection" not in promote_active_triggers, "Promote mode must suppress verification-route triggers.")
    check("formal_theory_upstream_scan" not in promote_active_triggers, "Promote mode must suppress unrelated formal_theory_upstream_scan triggers.")

    literature_bundle = runtime_bundle(service, "demo-literature")
    literature_must_read = path_list(literature_bundle["must_read_now"])
    literature_deferred = path_list(literature_bundle["may_defer_until_trigger"])
    check(literature_bundle["runtime_mode"] == "explore", "Expected demo-literature to remain inside explore mode.")
    check(literature_bundle.get("active_submode") == "literature", "Expected demo-literature to activate the literature submode.")
    check("topics/demo-literature/L1/vault/wiki/source-intake.md" in literature_must_read, "Literature submode must foreground the L1 source-intake wiki page.")
    check("canonical/staging/workspace_staging_manifest.json" in literature_must_read, "Literature submode must foreground the workspace staging manifest.")
    check("canonical/index.jsonl" in literature_must_read, "Literature submode must foreground the canonical index.")
    check("topics/demo-literature/runtime/validation_review_bundle.active.md" not in literature_must_read, "Literature submode must defer validation review.")
    check("topics/demo-literature/runtime/validation_review_bundle.active.md" in literature_deferred, "Literature submode must defer validation review into the deferred set.")

    literature_execution = service._execute_auto_actions(
        topic_slug="demo-literature",
        updated_by="mode-enforcement-acceptance",
        max_auto_steps=1,
        default_skill_queries=None,
    )
    check(literature_execution["executed"], "Expected one bounded literature auto action to execute.")
    check(
        literature_execution["executed"][0]["action_type"] == "literature_intake_stage"
        and literature_execution["executed"][0]["status"] == "completed",
        "Expected literature_intake_stage to complete successfully.",
    )
    staging_payload = literature_execution["executed"][0]["result"]["staging"]
    manifest_path = Path(staging_payload["manifest_json_path"])
    ensure_exists(manifest_path)
    check(staging_payload["entry_count"] > 0, "Expected the literature fast path to stage at least one L2 entry.")
    check(
        all(bool((entry.get("provenance") or {}).get("literature_intake_fast_path")) for entry in staging_payload["entries"]),
        "Expected all staged literature entries to carry literature_intake_fast_path provenance.",
    )
    canonical_index_text = (kernel_root / "canonical" / "index.jsonl").read_text(encoding="utf-8")
    staged_entry_ids = {str(entry["entry_id"]) for entry in staging_payload["entries"]}
    check(
        all(entry_id not in canonical_index_text for entry_id in staged_entry_ids),
        "Expected staged literature entries to remain out of canonical/index.jsonl.",
    )
    consult_payload = service.consult_l2(
        query_text="weak coupling benchmark",
        retrieval_profile="l1_provisional_understanding",
        include_staging=True,
        topic_slug="demo-literature",
        stage="L1",
        run_id="run-001",
        updated_by="mode-enforcement-acceptance",
        record_consultation=False,
    )
    check(consult_payload["staged_hits"], "Expected consult_l2(include_staging=True) to return staged literature hits.")
    check(
        all(str(row.get("trust_surface") or "") == "staging" for row in consult_payload["staged_hits"]),
        "Expected consult_l2 staged hits to be marked with trust_surface=staging.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "discussion_mode": discussion_bundle["runtime_mode"],
            "explore_mode": explore_bundle["runtime_mode"],
            "verify_mode": verify_bundle["runtime_mode"],
            "promote_mode": promote_bundle["runtime_mode"],
            "literature_submode": literature_bundle["active_submode"],
            "literature_entry_count": staging_payload["entry_count"],
            "consult_staged_hit_count": len(consult_payload["staged_hits"]),
            "registered_arxiv_source_id": register_payload["source_id"],
        },
        "artifacts": {
            "discussion_runtime_protocol": str(kernel_root / "topics" / "demo-discussion" / "runtime" / "runtime_protocol.generated.json"),
            "explore_runtime_protocol": str(kernel_root / "topics" / "demo-explore" / "runtime" / "runtime_protocol.generated.json"),
            "verify_runtime_protocol": str(kernel_root / "topics" / "demo-verify" / "runtime" / "runtime_protocol.generated.json"),
            "promote_runtime_protocol": str(kernel_root / "topics" / "demo-promote" / "runtime" / "runtime_protocol.generated.json"),
            "literature_runtime_protocol": str(kernel_root / "topics" / "demo-literature" / "runtime" / "runtime_protocol.generated.json"),
            "workspace_staging_manifest": str(manifest_path),
            "canonical_index": str(kernel_root / "canonical" / "index.jsonl"),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
