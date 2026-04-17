#!/usr/bin/env python
"""Acceptance for promoting the bounded HS-like positive target into L2."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


REFERENCE_TOPIC_SLUG = "haldane-shastry-chaos-transition"
REFERENCE_RUN_ID = "2026-03-27-030941-bootstrap"
REFERENCE_CANDIDATE_ID = "candidate:hs-chaos-window-finite-size-core"
TARGET_UNIT_ID = "claim:hs-like-chaos-window-finite-size-core"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


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


def create_minimal_tpkn_backend(target_root: Path) -> None:
    for relative in (
        "docs",
        "schema",
        "scripts",
        "sources",
        "units/concepts",
        "units/definitions",
        "units/notations",
        "units/assumptions",
        "units/regimes",
        "units/theorems",
        "units/claims",
        "units/proof-fragments",
        "units/derivation-steps",
        "units/derivations",
        "units/methods",
        "units/topic-skill-projections",
        "units/bridges",
        "units/examples",
        "units/caveats",
        "units/equivalences",
        "units/symbol-bindings",
        "units/equations",
        "units/quantities",
        "units/models",
        "units/source-maps",
        "units/warnings",
        "edges",
        "indexes",
        "portal",
        "human-mirror",
    ):
        (target_root / relative).mkdir(parents=True, exist_ok=True)
    for relative in (
        "docs/PROTOCOLS.md",
        "docs/L2_RETRIEVAL_PROTOCOL.md",
        "docs/OBJECT_MODEL.md",
        "docs/L2_BRIDGE_PROTOCOL.md",
    ):
        (target_root / relative).write_text("# Minimal TPKN backend seed\n", encoding="utf-8")
    (target_root / "edges" / "edges.jsonl").write_text("", encoding="utf-8")
    write_json(
        target_root / "schema" / "unit.schema.json",
        {"title": "minimal-unit-schema"},
    )
    write_json(
        target_root / "schema" / "source-manifest.schema.json",
        {"title": "minimal-source-schema"},
    )
    backend_card = {
        "backend_id": "backend:theoretical-physics-knowledge-network",
        "canonical_targets": ["claim_card"],
        "source_policy": {"allows_auto_canonical_promotion": False},
    }
    write_json(target_root / "portal" / "backend_card.json", backend_card)
    (target_root / "scripts" / "kb.py").write_text(
        """from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT_DIRS = {
    "claim": ROOT / "units" / "claims",
    "concept": ROOT / "units" / "concepts",
    "method": ROOT / "units" / "methods",
    "workflow": ROOT / "units" / "workflows",
    "warning": ROOT / "units" / "warnings",
    "bridge": ROOT / "units" / "bridges",
    "topic_skill_projection": ROOT / "units" / "topic-skill-projections",
}

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def build() -> None:
    rows = []
    for unit_dir in UNIT_DIRS.values():
        unit_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(unit_dir.glob("*.json")):
            payload = read_json(path)
            rows.append(
                {
                    "id": payload["id"],
                    "type": payload["type"],
                    "title": payload["title"],
                    "summary": payload["summary"],
                    "path": str(path.relative_to(ROOT)),
                }
            )
    unit_index = ROOT / "indexes" / "unit_index.jsonl"
    unit_index.parent.mkdir(parents=True, exist_ok=True)
    unit_index.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\\n" for row in rows),
        encoding="utf-8",
    )

def main() -> int:
    if len(sys.argv) < 2:
        return 1
    command = sys.argv[1]
    if command == "check":
        for unit_dir in UNIT_DIRS.values():
            unit_dir.mkdir(parents=True, exist_ok=True)
        return 0
    if command == "build":
        build()
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )


def load_reference_candidate(package_root: Path) -> dict[str, Any]:
    ledger_path = (
        package_root / "topics" / REFERENCE_TOPIC_SLUG / "L3"
        / "runs"
        / REFERENCE_RUN_ID
        / "candidate_ledger.jsonl"
    )
    for row in read_jsonl(ledger_path):
        if str(row.get("candidate_id") or "").strip() == REFERENCE_CANDIDATE_ID:
            return row
    raise FileNotFoundError(f"Reference candidate missing: {ledger_path}")


def clone_candidate_for_fresh_topic(
    reference_candidate: dict[str, Any],
    *,
    topic_slug: str,
    run_id: str,
    target_contract_path: Path,
    baseline_summary_path: Path,
    trust_audit_path: Path,
) -> dict[str, Any]:
    candidate = dict(reference_candidate)
    candidate["topic_slug"] = topic_slug
    candidate["run_id"] = run_id
    candidate["status"] = "ready_for_validation"
    candidate["topic_completion_status"] = "promotion-ready"
    candidate["promotion_blockers"] = []
    candidate["split_required"] = False
    candidate["cited_recovery_required"] = False
    candidate["followup_gap_ids"] = []
    candidate["origin_refs"] = [
        {
            **dict(ref),
            "path": str(ref.get("path") or "").replace(
                f"topics/{REFERENCE_TOPIC_SLUG}/L0/",
                f"topics/{topic_slug}/L0/",
            ),
        }
        for ref in (reference_candidate.get("origin_refs") or [])
    ]
    candidate["review_packet_refs"] = {
        "target_contract": str(target_contract_path),
        "baseline_summary": str(baseline_summary_path),
        "trust_audit": str(trust_audit_path),
    }
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic")
    parser.add_argument("--question")
    parser.add_argument("--human-request")
    parser.add_argument("--updated-by", default="hs-positive-l2-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="hsp-")).resolve()
    )
    kernel_root = work_root / "knowledge-hub"

    contract_script = package_root / "runtime" / "scripts" / "run_hs_toy_model_target_contract_acceptance.py"
    contract_command = [
        sys.executable,
        str(contract_script),
        "--package-root",
        str(package_root),
        "--repo-root",
        str(repo_root),
        "--work-root",
        str(work_root),
        "--updated-by",
        args.updated_by,
        "--json",
    ]
    if args.topic:
        contract_command.extend(["--topic", args.topic])
    if args.question:
        contract_command.extend(["--question", args.question])
    if args.human_request:
        contract_command.extend(["--human-request", args.human_request])
    contract_payload = run_python_json(contract_command)

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    topic_slug = str(contract_payload["topic_slug"])
    run_id = str(contract_payload["run_id"])
    runtime_root = kernel_root / "topics" / topic_slug / "runtime"
    tpkn_root = work_root / "tpkn-hs-positive"
    create_minimal_tpkn_backend(tpkn_root)

    reference_candidate = load_reference_candidate(package_root)
    target_contract_path = Path(contract_payload["target_contract"]["json_path"])
    target_contract_note_path = Path(contract_payload["target_contract"]["markdown_path"])
    baseline_summary_path = Path(contract_payload["trust_gate"]["baseline_summary"])
    trust_audit_path = Path(contract_payload["trust_gate"]["trust_audit_path"])

    candidate = clone_candidate_for_fresh_topic(
        reference_candidate,
        topic_slug=topic_slug,
        run_id=run_id,
        target_contract_path=target_contract_path,
        baseline_summary_path=baseline_summary_path,
        trust_audit_path=trust_audit_path,
    )
    candidate_ledger_path = (
        kernel_root / "topics" / topic_slug / "L3"
        / "runs"
        / run_id
        / "candidate_ledger.jsonl"
    )
    write_jsonl(candidate_ledger_path, [candidate])

    request_payload = service.request_promotion(
        topic_slug=topic_slug,
        candidate_id=REFERENCE_CANDIDATE_ID,
        run_id=run_id,
        backend_id="backend:theoretical-physics-knowledge-network",
        target_backend_root=str(tpkn_root),
        requested_by=args.updated_by,
        notes="Promote the bounded HS-like finite-size chaos-window core claim card into authoritative canonical L2.",
    )
    approve_payload = service.approve_promotion(
        topic_slug=topic_slug,
        candidate_id=REFERENCE_CANDIDATE_ID,
        run_id=run_id,
        approved_by=args.updated_by,
        notes="Human-reviewed promotion: bounded finite-size core only; exact HS negative comparator remains explicit.",
    )
    promote_payload = service.promote_candidate(
        topic_slug=topic_slug,
        candidate_id=REFERENCE_CANDIDATE_ID,
        run_id=run_id,
        promoted_by=args.updated_by,
        target_backend_root=str(tpkn_root),
        domain="toy-models",
        subdomain="hs-like-chaos-window",
        source_id=str((contract_payload["target_contract"]["payload"]["source_refs"] or [None])[0] or ""),
        source_section="bounded-finite-size-chaos-window-core",
        source_section_title="HS-like finite-size chaos-window core benchmark contract",
        notes="Promote only the bounded 0.4<=alpha<=1.0 finite-size core claim; keep exact HS alpha=2 as negative comparator.",
        review_artifact_paths={
            "target_contract_path": str(target_contract_path),
            "target_contract_note_path": str(target_contract_note_path),
            "baseline_summary_path": str(baseline_summary_path),
            "trust_audit_path": str(trust_audit_path),
        },
        coverage_summary={
            "status": "pass",
            "summary": "The bounded HS-like finite-size core has an explicit benchmark-backed target contract.",
        },
        consensus_summary={
            "status": "ready",
            "summary": "The fresh toy-model target contract and benchmark gate agree on the bounded positive claim.",
        },
    )

    compile_map_payload = service.compile_l2_workspace_map()
    compile_graph_payload = service.compile_l2_graph_report()
    compile_report_payload = service.compile_l2_knowledge_report()
    consult_payload = service.consult_l2(
        query_text="HS-like finite-size chaos window robust core",
        retrieval_profile="l4_adjudication",
        max_primary_hits=8,
    )
    consult_ids = sorted(
        {
            str(row.get("id") or "").strip()
            for row in [
                *(consult_payload.get("primary_hits") or []),
                *(consult_payload.get("expanded_hits") or []),
            ]
            if str(row.get("id") or "").strip()
        }
    )
    if TARGET_UNIT_ID not in consult_ids:
        raise RuntimeError("Expected consult_l2 to surface the promoted HS-like positive claim.")
    if not any(
        str(row.get("knowledge_id") or "").strip() == TARGET_UNIT_ID
        for row in (compile_report_payload.get("payload") or {}).get("knowledge_rows", [])
    ):
        raise RuntimeError("Expected workspace knowledge report to include the promoted HS-like positive claim.")

    canonical_mirror_path = Path(promote_payload["canonical_mirror_path"])
    promotion_gate_path = runtime_root / "promotion_gate.json"
    for path in (
        candidate_ledger_path,
        target_contract_path,
        baseline_summary_path,
        trust_audit_path,
        canonical_mirror_path,
        promotion_gate_path,
        Path(compile_report_payload["json_path"]),
    ):
        ensure_exists(path)

    payload = {
        "status": "success",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "target_contract": contract_payload["target_contract"],
        "promotion": {
            "request": request_payload,
            "approve": approve_payload,
            "promote": promote_payload,
            "canonical_mirror_path": str(canonical_mirror_path),
            "target_unit_id": TARGET_UNIT_ID,
        },
        "repo_local_l2": {
            "workspace_memory_map": {
                "json_path": compile_map_payload["json_path"],
                "markdown_path": compile_map_payload["markdown_path"],
            },
            "workspace_graph_report": {
                "json_path": compile_graph_payload["json_path"],
                "markdown_path": compile_graph_payload["markdown_path"],
            },
            "workspace_knowledge_report": {
                "json_path": compile_report_payload["json_path"],
                "markdown_path": compile_report_payload["markdown_path"],
            },
            "consultation": {
                "query_text": "HS-like finite-size chaos window robust core",
                "retrieval_profile": "l4_adjudication",
                "ids": consult_ids,
            },
        },
        "artifacts": {
            "candidate_ledger": str(candidate_ledger_path),
            "promotion_gate": str(promotion_gate_path),
            "canonical_mirror": str(canonical_mirror_path),
            "workspace_knowledge_report": compile_report_payload["json_path"],
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
