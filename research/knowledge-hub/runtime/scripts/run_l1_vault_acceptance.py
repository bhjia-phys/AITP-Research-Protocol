#!/usr/bin/env python
"""Isolated acceptance for the bounded L1 raw/wiki/output vault surface."""

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
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_cli_json(*, package_root: Path, kernel_root: Path, repo_root: Path, args: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "knowledge_hub.aitp_cli",
        "--kernel-root",
        str(kernel_root),
        "--repo-root",
        str(repo_root),
        *args,
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def seed_demo_runtime(kernel_root: Path) -> None:
    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "topic_state.json").write_text(
        json.dumps(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "resume_stage": "L1",
                "research_mode": "formal_derivation",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Compile the bounded intake state into the wiki-style vault before deeper proof work.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:vault",
                    "decision_source": "heuristic",
                },
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "action_queue.jsonl").write_text(
        json.dumps(
            {
                "action_id": "action:demo-topic:vault",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the compiled L1 vault before continuing.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "control_note.md").write_text(
        "# Control note\n\n"
        "directive: continue\n"
        "summary: Keep the intake compilation aligned with the bounded theorem route.\n",
        encoding="utf-8",
    )
    (runtime_root / "operator_console.md").write_text(
        "# Operator console\n\n"
        "- Next: inspect the L1 vault and compare it with the runtime contract.\n",
        encoding="utf-8",
    )


def seed_demo_source_layer(kernel_root: Path) -> None:
    topic_root = kernel_root / "topics" / "demo-topic" / "L0"
    topic_root.mkdir(parents=True, exist_ok=True)
    source_rows = [
        {
            "source_id": "thesis:bounded-closure",
            "source_type": "thesis",
            "title": "Bounded closure derivation",
            "summary": (
                "We assume fractional occupations remain bounded in the weak coupling limit and derive the first theorem-facing closure target."
            ),
            "provenance": {
                "absolute_path": str(kernel_root / "inputs" / "bounded-closure.tex"),
            },
        },
        {
            "source_id": "note:followup-comparison",
            "source_type": "local_note",
            "title": "Follow-up comparison note",
            "summary": (
                "Compare the bounded closure route against the finite benchmark and keep the notation alignment explicit."
            ),
            "provenance": {
                "abs_url": "https://example.org/followup-comparison",
            },
        },
    ]
    write_jsonl(topic_root / "source_index.jsonl", source_rows)
    snapshot_root = topic_root / "sources" / "thesis-bounded-closure"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "snapshot.md").write_text(
        "# Snapshot\n\n"
        "## Preview\n"
        "We assume fractional occupations remain bounded in the weak coupling limit and derive the first theorem-facing closure target.\n",
        encoding="utf-8",
    )


def rel_to_abs(kernel_root: Path, relative_path: str) -> Path:
    return kernel_root / Path(relative_path)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-vault-acceptance-")).resolve()
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

    l1_vault = ((status_payload.get("active_research_contract") or {}).get("l1_vault") or {})
    research_contract_note = kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    manifest_path = rel_to_abs(kernel_root, str(l1_vault.get("root_path") or "")) / "vault_manifest.json"
    raw_manifest_path = rel_to_abs(kernel_root, str(((l1_vault.get("raw") or {}).get("manifest_path")) or ""))
    wiki_home_path = rel_to_abs(kernel_root, str(((l1_vault.get("wiki") or {}).get("home_page_path")) or ""))
    wiki_schema_path = rel_to_abs(kernel_root, str(((l1_vault.get("wiki") or {}).get("schema_path")) or ""))
    output_digest_note_path = rel_to_abs(kernel_root, str(((l1_vault.get("output") or {}).get("digest_note_path")) or ""))
    flowback_log_path = rel_to_abs(kernel_root, str(((l1_vault.get("output") or {}).get("flowback_log_path")) or ""))
    runtime_bridge_path = rel_to_abs(kernel_root, "topics/demo-topic/L1/vault/wiki/runtime-bridge.md")

    ensure_exists(research_contract_note)
    ensure_exists(runtime_protocol_note)
    ensure_exists(manifest_path)
    ensure_exists(raw_manifest_path)
    ensure_exists(wiki_home_path)
    ensure_exists(wiki_schema_path)
    ensure_exists(output_digest_note_path)
    ensure_exists(flowback_log_path)
    ensure_exists(runtime_bridge_path)

    home_text = wiki_home_path.read_text(encoding="utf-8")
    schema_text = wiki_schema_path.read_text(encoding="utf-8")
    bridge_text = runtime_bridge_path.read_text(encoding="utf-8")
    contract_note_text = research_contract_note.read_text(encoding="utf-8")
    runtime_note_text = runtime_protocol_note.read_text(encoding="utf-8")
    flowback_rows = [
        json.loads(line)
        for line in flowback_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    check(l1_vault.get("status") == "materialized", "Expected l1_vault status to be materialized.")
    check(((l1_vault.get("raw") or {}).get("source_count") or 0) == 2, "Expected two raw-layer sources.")
    check("page_type: topic_home" in home_text, "Expected topic-home frontmatter in wiki home page.")
    check("[[source-intake|Source Intake]]" in home_text, "Expected wiki home page to link to source-intake.")
    check("output/flowback.jsonl" in schema_text, "Expected wiki schema page to document the flowback log.")
    check("research_question.contract.md" in bridge_text, "Expected runtime bridge page to link the research question contract.")
    check("control_note.md" in bridge_text, "Expected runtime bridge page to link the control note.")
    check("operator_console.md" in bridge_text, "Expected runtime bridge page to link the operator console.")
    check(len(flowback_rows) >= 4, "Expected at least four flowback rows.")
    check(all(row.get("status") == "applied" for row in flowback_rows), "Expected applied flowback rows.")
    check("## L1 vault" in contract_note_text, "Expected research_question.contract.md to include an L1 vault section.")
    check("## L1 vault" in runtime_note_text, "Expected runtime protocol note to include an L1 vault section.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "raw_source_count": (l1_vault.get("raw") or {}).get("source_count"),
            "wiki_page_count": (l1_vault.get("wiki") or {}).get("page_count"),
            "flowback_entry_count": len(flowback_rows),
        },
        "artifacts": {
            "vault_manifest": str(manifest_path),
            "raw_manifest": str(raw_manifest_path),
            "wiki_home": str(wiki_home_path),
            "runtime_bridge": str(runtime_bridge_path),
            "output_digest_note": str(output_digest_note_path),
            "flowback_log": str(flowback_log_path),
            "research_question_contract_note": str(research_contract_note),
            "runtime_protocol_note": str(runtime_protocol_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
