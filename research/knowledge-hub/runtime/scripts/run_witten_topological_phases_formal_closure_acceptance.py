#!/usr/bin/env python
"""Cross-platform real-topic acceptance for the Witten topological-phases closure lane."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService, bounded_slugify, write_json  # noqa: E402


WITTEN_SOURCE_ID = "paper:witten-topological-phases-1510.07698v2"
CANDIDATE_ID = "candidate:witten-l2-hall-response-equivalence"
TARGET_UNIT_ID = "theorem:integer-quantum-hall-response-equals-band-and-many-body-chern-number"


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--topic", default="Witten topological phases formal closure acceptance")
    parser.add_argument("--topic-slug", default=f"witten-tp-formal-close-{now_stamp()}")
    parser.add_argument("--run-id", default=f"{now_stamp()}-witten-tp-close")
    parser.add_argument("--updated-by", default="witten-formal-closure-acceptance")
    parser.add_argument("--tpkn-template-root")
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def runtime_env(kernel_root: Path, repo_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["AITP_KERNEL_ROOT"] = str(kernel_root)
    env["AITP_REPO_ROOT"] = str(repo_root)
    pythonpath_parts = [str(kernel_root)]
    existing = env.get("PYTHONPATH", "")
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


def discover_tpkn_template_root(repo_root: Path, override: str | None) -> Path:
    if not override:
        raise FileNotFoundError("No explicit TPKN template root was provided.")
    candidate = Path(override).expanduser().resolve()
    if (candidate / "scripts" / "check_protocol.py").exists():
        return candidate
    raise FileNotFoundError(f"Invalid TPKN template root: {candidate}")


def copy_tpkn_tree(source_root: Path, target_root: Path) -> None:
    shutil.copytree(
        source_root,
        target_root,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "portal", "indexes"),
    )


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
    write_json(target_root / "schema" / "unit.schema.json", {"title": "minimal-unit-schema"})
    write_json(target_root / "schema" / "source-manifest.schema.json", {"title": "minimal-source-schema"})
    (target_root / "scripts" / "kb.py").write_text(
        textwrap.dedent(
            """\
            from __future__ import annotations

            import json
            import sys
            from pathlib import Path

            ROOT = Path(__file__).resolve().parents[1]
            UNIT_DIRS = {
                "concept": ROOT / "units" / "concepts",
                "definition": ROOT / "units" / "definitions",
                "notation": ROOT / "units" / "notations",
                "assumption": ROOT / "units" / "assumptions",
                "regime": ROOT / "units" / "regimes",
                "theorem": ROOT / "units" / "theorems",
                "claim": ROOT / "units" / "claims",
                "proof_fragment": ROOT / "units" / "proof-fragments",
                "derivation_step": ROOT / "units" / "derivation-steps",
                "derivation": ROOT / "units" / "derivations",
                "method": ROOT / "units" / "methods",
                "bridge": ROOT / "units" / "bridges",
                "example": ROOT / "units" / "examples",
                "caveat": ROOT / "units" / "caveats",
                "equivalence": ROOT / "units" / "equivalences",
                "symbol_binding": ROOT / "units" / "symbol-bindings",
                "equation": ROOT / "units" / "equations",
                "quantity": ROOT / "units" / "quantities",
                "model": ROOT / "units" / "models",
                "source_map": ROOT / "units" / "source-maps",
                "warning": ROOT / "units" / "warnings",
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
                        for path in sorted(unit_dir.glob("*.json")):
                            payload = read_json(path)
                            for field in ("id", "type", "title", "summary"):
                                if field not in payload:
                                    raise SystemExit(
                                        f"ERROR: {path.relative_to(ROOT)}: missing required field '{field}'"
                                    )
                    return 0
                if command == "build":
                    build()
                    return 0
                return 1

            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ),
        encoding="utf-8",
    )


def write_source_index_row(kernel_root: Path, topic_slug: str) -> Path:
    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    source_index_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "source_id": WITTEN_SOURCE_ID,
        "source_type": "paper",
        "title": "Three Lectures On Topological Phases Of Matter",
        "topic_slug": topic_slug,
        "provenance": {
            "authors": ["Edward Witten"],
            "published": "2015-10-26T00:00:00+00:00",
            "updated": "2015-11-17T00:00:00+00:00",
            "abs_url": "https://arxiv.org/abs/1510.07698v2",
            "pdf_url": "https://arxiv.org/pdf/1510.07698v2",
            "source_url": "https://arxiv.org/e-print/1510.07698v2",
            "doi": "https://doi.org/10.48550/arXiv.1510.07698",
            "journal_url": "https://doi.org/10.1393/ncr/i2016-10125-3",
        },
        "acquired_at": "2026-03-23T00:00:00+08:00",
        "summary": (
            "Primary source row for the bounded Witten Lecture Two hall-response / Chern-number "
            "formal-closure acceptance."
        ),
    }
    source_index_path.write_text(json.dumps(row, ensure_ascii=True) + "\n", encoding="utf-8")
    return source_index_path


def write_real_topic_candidate(kernel_root: Path, topic_slug: str, run_id: str) -> Path:
    feedback_root = kernel_root / "topics" / topic_slug / "L3" / "runs" / run_id
    feedback_root.mkdir(parents=True, exist_ok=True)
    ledger_path = feedback_root / "candidate_ledger.jsonl"
    row = {
        "candidate_id": CANDIDATE_ID,
        "candidate_type": "theorem_card",
        "title": "Witten Lecture Two Hall-Response / Chern-Number Equivalence",
        "summary": (
            "Bounded theorem-card candidate for the real Witten Lecture Two equality "
            "k = k' = \\widehat{k}' used to validate the formal-theory closure lane."
        ),
        "topic_slug": topic_slug,
        "run_id": run_id,
        "origin_refs": [
            {
                "id": WITTEN_SOURCE_ID,
                "layer": "L0",
                "object_type": "source",
                "path": f"topics/{topic_slug}/L0/source_index.jsonl",
                "title": "Three Lectures On Topological Phases Of Matter",
                "summary": "Witten Lecture Two source anchor for the formal-closure acceptance theorem.",
            }
        ],
        "question": (
            "Can the Witten Lecture Two Hall-response / Chern-number theorem travel through "
            "coverage audit, formal-theory review, topic completion, Lean bridge, and L2_auto writeback?"
        ),
        "assumptions": [
            "This acceptance lane validates the bounded Witten-side theorem statement, not the entire external-source fusion backlog."
        ],
        "proposed_validation_route": "real-topic-formal-closure-acceptance",
        "intended_l2_targets": [TARGET_UNIT_ID],
        "supporting_regression_question_ids": [
            "regression_question:reconstruct-hall-response-chern-number-equivalence"
        ],
        "supporting_oracle_ids": [
            "question_oracle:reconstruct-hall-response-chern-number-equivalence"
        ],
        "supporting_regression_run_ids": [
            "regression_run:topological-phases-core-2026-03-20"
        ],
        "promotion_blockers": [],
        "split_required": False,
        "cited_recovery_required": False,
        "followup_gap_ids": [],
        "status": "ready_for_validation",
    }
    ledger_path.write_text(json.dumps(row, ensure_ascii=True) + "\n", encoding="utf-8")
    return ledger_path


def run_python_json(command: list[str], env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {message}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expected JSON output from {' '.join(command)}") from exc


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    env = runtime_env(kernel_root, repo_root)
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else (repo_root.parent / "_wtp_accept" / uuid.uuid4().hex[:8]).resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)
    tpkn_work_root = work_root / "theoretical-physics-knowledge-network"
    if args.tpkn_template_root:
        tpkn_template_root = discover_tpkn_template_root(repo_root, args.tpkn_template_root)
        copy_tpkn_tree(tpkn_template_root, tpkn_work_root)
        tpkn_template_root_value = str(tpkn_template_root)
    else:
        create_minimal_tpkn_backend(tpkn_work_root)
        tpkn_template_root_value = "(generated-minimal)"

    orchestrate_command = [
        sys.executable,
        str(kernel_root / "runtime" / "scripts" / "orchestrate_topic.py"),
        "--topic",
        args.topic,
        "--topic-slug",
        args.topic_slug,
        "--statement",
        "Materialize bounded formal-theory closure artifacts for the Witten Lecture Two hall-response theorem.",
        "--run-id",
        args.run_id,
        "--research-mode",
        "formal_derivation",
        "--human-request",
        "Run the real-topic formal-closure acceptance for Witten Lecture Two on a bounded theorem candidate.",
        "--updated-by",
        args.updated_by,
    ]
    subprocess.run(orchestrate_command, check=True, env=env, capture_output=True, text=True)

    _witten_runtime_root = kernel_root / "topics" / args.topic_slug / "runtime"
    (_witten_runtime_root / "session_start.contract.json").write_text(
        json.dumps({"updated_at": "test-seed"}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

    source_index_path = write_source_index_row(kernel_root, args.topic_slug)
    candidate_ledger_path = write_real_topic_candidate(kernel_root, args.topic_slug, args.run_id)

    coverage = service.audit_theory_coverage(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        candidate_id=CANDIDATE_ID,
        updated_by=args.updated_by,
        source_sections=[
            "lecture-two/quantization-of-the-hall-conductivity",
            "lecture-two/relation-to-band-topology",
            "lecture-two/proof-of-the-equivalence",
        ],
        covered_sections=[
            "lecture-two/quantization-of-the-hall-conductivity",
            "lecture-two/relation-to-band-topology",
            "lecture-two/proof-of-the-equivalence",
        ],
        equation_labels=["murr", "plizz"],
        notation_bindings=[
            {"symbol": "k", "meaning": "integer Hall-response level"},
            {"symbol": "k'", "meaning": "filled-band TKNN invariant"},
            {"symbol": "\\widehat{k}'", "meaning": "many-body twist-angle Chern number"},
        ],
        derivation_nodes=[
            "proof_fragment:large-gauge-invariance-quantizes-chern-simons-level",
            "derivation_step:chern-simons-action-induces-hall-current",
            "definition:tknn-invariant-as-first-chern-class-of-filled-band-bundle",
            "proof_fragment:twisted-boundary-berry-curvature-reproduces-hall-level",
        ],
        derivation_edges=[
            {
                "source": "proof_fragment:large-gauge-invariance-quantizes-chern-simons-level",
                "target": "derivation_step:chern-simons-action-induces-hall-current",
                "relation": "enables",
            },
            {
                "source": "definition:tknn-invariant-as-first-chern-class-of-filled-band-bundle",
                "target": "proof_fragment:twisted-boundary-berry-curvature-reproduces-hall-level",
                "relation": "matches",
            },
        ],
        agent_votes=[
            {"role": "structure", "verdict": "covered", "notes": "All bounded Witten sections are represented."},
            {"role": "skeptic", "verdict": "no_major_gap", "notes": "No hidden blocker inside the bounded theorem statement."},
            {"role": "adjudicator", "verdict": "unanimous", "notes": "Safe to test closure artifacts."},
        ],
        consensus_status="unanimous",
        critical_unit_recall=1.0,
        missing_anchor_count=0,
        skeptic_major_gap_count=0,
        supporting_regression_question_ids=["regression_question:reconstruct-hall-response-chern-number-equivalence"],
        supporting_oracle_ids=["question_oracle:reconstruct-hall-response-chern-number-equivalence"],
        supporting_regression_run_ids=["regression_run:topological-phases-core-2026-03-20"],
        promotion_blockers=[],
        split_required=False,
        cited_recovery_required=False,
        followup_gap_ids=[],
        topic_completion_status="promotion-ready",
        notes="Bounded real-topic acceptance for the Witten Lecture Two theorem statement.",
    )
    formal_review = service.audit_formal_theory(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        candidate_id=CANDIDATE_ID,
        updated_by=args.updated_by,
        formal_theory_role="trusted_target",
        statement_graph_role="target_statement",
        target_statement_id=TARGET_UNIT_ID,
        informal_statement=(
            "In the gapped integer quantum Hall system, the Hall-response level agrees with both the TKNN invariant "
            "and the many-body twist-angle Chern number."
        ),
        formal_target=TARGET_UNIT_ID,
        faithfulness_status="reviewed",
        faithfulness_strategy="bounded Witten Lecture Two statement-to-target alignment",
        comparator_audit_status="passed",
        attribution_requirements=["Preserve the Witten Lecture Two source anchor in the promoted theorem card."],
        prerequisite_closure_status="closed",
        supporting_obligation_ids=[
            "proof_obligation:large-gauge-holonomy-shift-quantizes-chern-simons-level",
            "proof_obligation:hall-response-band-and-many-body-chern-numbers-coincide",
        ],
        prerequisite_notes="The acceptance candidate is intentionally bounded to the local Witten-side theorem statement.",
    )

    dispatch_script = kernel_root.parent / "adapters" / "openclaw" / "scripts" / "dispatch_runtime_controller_action.py"
    completion = run_python_json(
        [
            sys.executable,
            str(dispatch_script),
            "--topic-slug",
            args.topic_slug,
            "--action-type",
            "assess_topic_completion",
            "--run-id",
            args.run_id,
            "--updated-by",
            args.updated_by,
            "--json",
        ],
        env,
    )
    lean_bridge = run_python_json(
        [
            sys.executable,
            str(dispatch_script),
            "--topic-slug",
            args.topic_slug,
            "--action-type",
            "prepare_lean_bridge",
            "--run-id",
            args.run_id,
            "--candidate-id",
            CANDIDATE_ID,
            "--updated-by",
            args.updated_by,
            "--json",
        ],
        env,
    )
    auto_promotion = run_python_json(
        [
            sys.executable,
            str(dispatch_script),
            "--topic-slug",
            args.topic_slug,
            "--action-type",
            "auto_promote_candidate",
            "--run-id",
            args.run_id,
            "--candidate-id",
            CANDIDATE_ID,
            "--target-backend-root",
            str(tpkn_work_root),
            "--domain",
            "topological-phases-of-matter",
            "--subdomain",
            "integer-quantum-hall-effect",
            "--source-id",
            WITTEN_SOURCE_ID,
            "--source-section",
            "lecture-two/proof-of-the-equivalence",
            "--source-section-title",
            "Proof Of The Equivalence",
            "--notes",
            "Real-topic formal-closure acceptance for the bounded Witten Lecture Two theorem candidate.",
            "--updated-by",
            args.updated_by,
            "--json",
        ],
        env,
    )

    topic_completion_path = kernel_root / "topics" / args.topic_slug / "runtime" / "topic_completion.json"
    lean_bridge_path = kernel_root / "topics" / args.topic_slug / "runtime" / "lean_bridge.active.json"
    lean_packet_path = (
        kernel_root / "topics" / args.topic_slug / "L4"
        / "runs"
        / args.run_id
        / "lean-bridge"
        / bounded_slugify("candidate:witten-l2-hall-response-equivalence")
        / "lean_ready_packet.json"
    )
    promotion_gate_path = kernel_root / "topics" / args.topic_slug / "runtime" / "promotion_gate.json"
    source_manifest_path = tpkn_work_root / "sources" / "witten-topological-phases-1510.07698v2" / "manifest.json"

    for path in (
        source_index_path,
        candidate_ledger_path,
        topic_completion_path,
        lean_bridge_path,
        lean_packet_path,
        promotion_gate_path,
        source_manifest_path,
    ):
        ensure_exists(path)

    topic_completion_payload = json.loads(topic_completion_path.read_text(encoding="utf-8"))
    lean_bridge_payload = json.loads(lean_bridge_path.read_text(encoding="utf-8"))
    promotion_gate_payload = json.loads(promotion_gate_path.read_text(encoding="utf-8"))
    promoted_unit_ids = promotion_gate_payload.get("promoted_units") or []
    if not promoted_unit_ids:
        raise RuntimeError("Expected at least one promoted unit id in promotion_gate.json.")
    promoted_unit_slug = str(promoted_unit_ids[0]).split(":", 1)[-1]
    expected_unit_path = tpkn_work_root / "units" / "theorems" / f"{promoted_unit_slug}.json"
    ensure_exists(expected_unit_path)
    promoted_unit = json.loads(expected_unit_path.read_text(encoding="utf-8"))

    if str(promoted_unit.get("canonical_layer") or "") != "L2_auto":
        raise RuntimeError("Expected the promoted real-topic unit to land in canonical_layer L2_auto.")
    if str(promoted_unit.get("review_mode") or "") != "ai_auto":
        raise RuntimeError("Expected the promoted real-topic unit to preserve ai_auto review mode.")
    if str(lean_bridge_payload.get("status") or "") != "ready":
        raise RuntimeError("Expected the Lean bridge acceptance packet to be ready.")
    if str(promotion_gate_payload.get("status") or "") != "promoted":
        raise RuntimeError("Expected the promotion gate to finish in promoted status.")

    payload = {
        "status": "success",
        "topic_slug": args.topic_slug,
        "run_id": args.run_id,
        "work_root": str(work_root),
        "tpkn_template_root": tpkn_template_root_value,
        "tpkn_work_root": str(tpkn_work_root),
        "coverage_status": coverage["coverage_status"],
        "formal_theory_review_status": formal_review["overall_status"],
        "topic_completion_status": topic_completion_payload.get("status"),
        "lean_bridge_status": lean_bridge_payload.get("status"),
        "auto_promotion_status": promotion_gate_payload.get("status"),
        "artifacts": {
            "source_index": str(source_index_path),
            "candidate_ledger": str(candidate_ledger_path),
            "topic_completion": str(topic_completion_path),
            "lean_bridge": str(lean_bridge_path),
            "lean_packet": str(lean_packet_path),
            "promotion_gate": str(promotion_gate_path),
            "promoted_unit": str(expected_unit_path),
            "source_manifest": str(source_manifest_path),
        },
        "dispatch_payloads": {
            "topic_completion": completion,
            "lean_bridge": lean_bridge,
            "auto_promotion": auto_promotion,
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
