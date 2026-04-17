#!/usr/bin/env python
"""Isolated acceptance for the richer L1 contradiction runtime surface."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from run_l1_assumption_depth_acceptance import (
    KERNEL_ROOT,
    REPO_ROOT,
    check,
    ensure_exists,
    run_cli_json,
    seed_demo_runtime,
    seed_demo_source_layer,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-contradiction-surface-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    (kernel_root / "intake").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package_root / "intake" / "L1_VAULT_PROTOCOL.md", kernel_root / "intake" / "L1_VAULT_PROTOCOL.md")
    seed_demo_runtime(kernel_root)
    seed_demo_source_layer(kernel_root)

    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    l1_source_intake = ((status_payload.get("active_research_contract") or {}).get("l1_source_intake") or {})
    contradiction_candidates = l1_source_intake.get("contradiction_candidates", [])
    check(contradiction_candidates, "Expected at least one contradiction candidate.")
    contradiction = contradiction_candidates[0]
    check(str(contradiction.get("comparison_basis") or "") == "regime_rows", "Expected contradiction basis to stay visible.")
    check("strong coupling" in str(contradiction.get("source_basis_summary") or ""), "Expected source-side basis summary.")
    check("weak coupling" in str(contradiction.get("against_basis_summary") or ""), "Expected compared-side basis summary.")

    research_contract_note = kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
    topic_dashboard_note = kernel_root / "topics" / "demo-topic" / "runtime" / "topic_dashboard.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    wiki_source_intake_note = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md"
    for path in (
        research_contract_note,
        topic_dashboard_note,
        runtime_protocol_note,
        wiki_source_intake_note,
    ):
        ensure_exists(path)

    research_text = research_contract_note.read_text(encoding="utf-8")
    dashboard_text = topic_dashboard_note.read_text(encoding="utf-8")
    runtime_text = runtime_protocol_note.read_text(encoding="utf-8")
    wiki_text = wiki_source_intake_note.read_text(encoding="utf-8")

    for text in (research_text, dashboard_text, runtime_text):
        check("basis=`regime_rows`" in text, "Expected runtime/read-path contradiction notes to expose comparison basis.")
        check("strong coupling" in text, "Expected runtime/read-path contradiction notes to expose source-side basis summary.")
        check("weak coupling" in text, "Expected runtime/read-path contradiction notes to expose compared-side basis summary.")
    check("## Contradictions" in wiki_text, "Expected contradiction section in the L1 vault source-intake page.")
    check("basis=`regime_rows`" in wiki_text, "Expected vault contradiction section to expose comparison basis.")
    check("strong coupling" in wiki_text, "Expected vault contradiction section to expose source-side basis summary.")
    check("weak coupling" in wiki_text, "Expected vault contradiction section to expose compared-side basis summary.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "contradiction_candidate_count": len(contradiction_candidates),
            "comparison_basis": contradiction.get("comparison_basis"),
            "source_basis_summary": contradiction.get("source_basis_summary"),
            "against_basis_summary": contradiction.get("against_basis_summary"),
        },
        "artifacts": {
            "research_question_contract_note": str(research_contract_note),
            "topic_dashboard_note": str(topic_dashboard_note),
            "runtime_protocol_note": str(runtime_protocol_note),
            "wiki_source_intake_note": str(wiki_source_intake_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
