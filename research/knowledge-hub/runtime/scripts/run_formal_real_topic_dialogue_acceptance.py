#!/usr/bin/env python
"""Acceptance for a real natural-language dialogue into the formal-theory lane."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))


REFERENCE_TOPIC_SLUG = "jones-von-neumann-algebras"
FORMAL_THEOREM_ID = "theorem:jones-ch4-finite-product"
TOPIC_TITLE = "Fresh Jones finite-dimensional factor closure"
TOPIC_SLUG = "fresh-jones-finite-dimensional-factor-closure"
JONES_CANDIDATE_DIR = "candidate-jones-ch4-fin-50e7c38d"
QUESTION_TEXT = (
    "I want to study one bounded Jones / von Neumann algebra result and check "
    "whether the public AITP front door can carry that real natural-language "
    "request into a trusted formal-theory L2 landing without pretending to "
    "formalize the whole book."
)


def run_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
HUMAN_REQUEST = (
    "Help me work on a bounded von Neumann algebra / Jones finite-factor "
    "question through the public front door, and keep the route tied to one "
    "already-proved positive formal result instead of widening into whole-book "
    "formalization."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--updated-by", default="formal-real-topic-dialogue-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_python_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="frtd-")).resolve()
    )
    kernel_root = work_root / "knowledge-hub"

    for relative in ("canonical", "knowledge_hub", "schemas"):
        shutil.copytree(package_root / relative, kernel_root / relative, dirs_exist_ok=True)
    (kernel_root / "runtime").mkdir(parents=True, exist_ok=True)
    for path in (package_root / "runtime").iterdir():
        if path.is_file():
            shutil.copy2(path, kernel_root / "runtime" / path.name)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_schemas_root = package_root / "runtime" / "schemas"
    if runtime_schemas_root.exists():
        shutil.copytree(runtime_schemas_root, kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    reference_topic_root = package_root / "source-layer" / "topics" / REFERENCE_TOPIC_SLUG
    shutil.copytree(
        reference_topic_root,
        kernel_root / "source-layer" / "topics" / reference_topic_root.name,
        dirs_exist_ok=True,
    )
    adapter_scripts_root = repo_root / "research" / "adapters" / "openclaw" / "scripts"
    shutil.copytree(
        adapter_scripts_root,
        work_root / "adapters" / "openclaw" / "scripts",
        dirs_exist_ok=True,
    )
    bootstrap_run_id = f"{run_stamp()}-bootstrap"
    closure_run_id = f"{run_stamp()}-jones-close"
    (
        kernel_root
        / "validation"
        / "topics"
        / TOPIC_SLUG
        / "runs"
        / closure_run_id
        / "theory-packets"
        / JONES_CANDIDATE_DIR
    ).mkdir(parents=True, exist_ok=True)

    formal_script = package_root / "runtime" / "scripts" / "run_formal_positive_l2_acceptance.py"
    payload = run_python_json(
        [
            sys.executable,
            str(formal_script),
            "--kernel-root",
            str(kernel_root),
            "--repo-root",
            str(repo_root),
            "--work-root",
            str(work_root),
            "--topic",
            TOPIC_TITLE,
            "--bootstrap-run-id",
            bootstrap_run_id,
            "--closure-run-id",
            closure_run_id,
            "--question",
            QUESTION_TEXT,
            "--reference-topic-slug",
            REFERENCE_TOPIC_SLUG,
            "--updated-by",
            args.updated_by,
            "--human-request",
            HUMAN_REQUEST,
            "--json",
        ]
    )

    topic_slug = str(payload["topic_slug"])
    check(topic_slug == TOPIC_SLUG, "Expected the fresh formal topic slug to stay on the bounded fresh-Jones route.")
    check(
        str((payload.get("bootstrap") or {}).get("research_mode") or "") == "formal_derivation",
        "Expected the fresh real-topic dialogue run to stay in formal_derivation mode.",
    )

    bootstrap_topic_state_path = Path(payload["artifacts"]["bootstrap_topic_state"])
    runtime_root = bootstrap_topic_state_path.parent
    interaction_state_path = runtime_root / "interaction_state.json"
    research_question_contract_path = runtime_root / "research_question.contract.json"
    runtime_protocol_note_path = runtime_root / "runtime_protocol.generated.md"

    for path in (
        bootstrap_topic_state_path,
        interaction_state_path,
        research_question_contract_path,
        runtime_protocol_note_path,
    ):
        ensure_exists(path)

    interaction_state_text = interaction_state_path.read_text(encoding="utf-8")
    research_contract_text = research_question_contract_path.read_text(encoding="utf-8")
    runtime_protocol_note = runtime_protocol_note_path.read_text(encoding="utf-8")
    consultation_ids = list((((payload.get("repo_local_l2") or {}).get("consultation") or {}).get("ids") or []))

    check(
        "von Neumann" in interaction_state_text or "Jones" in interaction_state_text,
        "Expected interaction_state to preserve the real natural-language formal-theory request.",
    )
    check(
        "von Neumann" in research_contract_text or "Jones" in research_contract_text,
        "Expected the research-question contract to preserve the real natural-language formal-theory topic.",
    )
    check(
        "formal" in runtime_protocol_note.lower() or "theorem" in runtime_protocol_note.lower(),
        "Expected the runtime protocol note to reflect the bounded formal-theory route.",
    )
    check(
        FORMAL_THEOREM_ID in consultation_ids,
        "Expected consult_l2 parity to preserve the bounded formal theorem on the real dialogue route.",
    )

    result = {
        "status": "success",
        "topic_slug": topic_slug,
        "dialogue_inputs": {
            "topic": TOPIC_TITLE,
            "question": QUESTION_TEXT,
            "human_request": HUMAN_REQUEST,
        },
        "bootstrap": payload["bootstrap"],
        "entry_artifacts": {
            "bootstrap_topic_state": str(bootstrap_topic_state_path),
            "interaction_state": str(interaction_state_path),
            "research_question_contract": str(research_question_contract_path),
            "runtime_protocol_note": str(runtime_protocol_note_path),
        },
        "repo_local_l2": payload["repo_local_l2"],
        "artifacts": payload["artifacts"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
