#!/usr/bin/env python
"""Bounded formal-closure acceptance for the Jones Chapter 4 finite-product lane."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
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
from knowledge_hub.topic_truth_root_support import compatibility_projection_path  # noqa: E402


TOPIC_SLUG = "jones-von-neumann-algebras"
CANDIDATE_ID = "candidate:jones-ch4-finite-product"
CANDIDATE_SLUG = bounded_slugify(CANDIDATE_ID)
TARGET_UNIT_ID = "theorem:finite-dimensional-block-centralizer-is-linear-product-of-block-fiber-type-i-factors"
PRIMARY_SOURCE_ID = "local_note:jones-von-neumann-algebras-definition-packet"
PRIMARY_SOURCE_SECTION = "chapter-4/multiplicity-and-finite-dimensional-von-neumann-algebras"
PRIMARY_SOURCE_SECTION_TITLE = "Multiplicity And Finite-Dimensional Von Neumann Algebras"
ORIGIN_SOURCE_IDS = (
    "local_note:jones-von-neumann-algebras-definition-packet",
    "local_note:theorem-level-package-roadmap",
    "local_note:readme",
)


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def run_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--topic-slug", default=TOPIC_SLUG)
    parser.add_argument("--run-id", default=f"{run_stamp()}-jones-ch4-fp")
    parser.add_argument("--updated-by", default="jones-ch4-finite-product-acceptance")
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
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".lake", "portal", "indexes"),
    )


def ensure_kb_entrypoint(target_root: Path) -> None:
    scripts_root = target_root / "scripts"
    scripts_root.mkdir(parents=True, exist_ok=True)
    kb_path = scripts_root / "kb.py"
    if kb_path.exists():
        return
    kb_path.write_text(
        textwrap.dedent(
            """\
            from __future__ import annotations

            import subprocess
            import sys
            from pathlib import Path

            ROOT = Path(__file__).resolve().parents[1]

            def main() -> int:
                if len(sys.argv) < 2:
                    return 1
                command = sys.argv[1]
                if command == "check":
                    return subprocess.call([sys.executable, str(ROOT / "scripts" / "check_protocol.py")], cwd=ROOT)
                if command == "build":
                    return subprocess.call([sys.executable, str(ROOT / "scripts" / "build.py")], cwd=ROOT)
                return 1

            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ),
        encoding="utf-8",
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
        "units/regression-questions",
        "units/question-oracles",
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
                "regression_question": ROOT / "units" / "regression-questions",
                "question_oracle": ROOT / "units" / "question-oracles",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_python_json(command: list[str], env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {message}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expected JSON output from {' '.join(command)}") from exc


def source_index_rows(kernel_root: Path, topic_slug: str) -> list[dict[str, Any]]:
    source_index_path = kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
    ensure_exists(source_index_path)
    return read_jsonl(source_index_path)


def origin_refs_for_candidate(kernel_root: Path, topic_slug: str) -> list[dict[str, Any]]:
    rows = source_index_rows(kernel_root, topic_slug)
    index = {
        str(row.get("source_id") or "").strip(): row
        for row in rows
        if str(row.get("source_id") or "").strip()
    }
    refs: list[dict[str, Any]] = []
    for source_id in ORIGIN_SOURCE_IDS:
        row = index.get(source_id)
        if row is None:
            raise FileNotFoundError(f"Required Jones source row is missing: {source_id}")
        refs.append(
            {
                "id": source_id,
                "layer": "L0",
                "object_type": "source",
                "path": f"source-layer/topics/{topic_slug}/source_index.jsonl",
                "title": str(row.get("title") or source_id),
                "summary": str(row.get("summary") or ""),
            }
        )
    return refs


def upsert_candidate_row(ledger_path: Path, row: dict[str, Any]) -> None:
    existing = [
        candidate
        for candidate in read_jsonl(ledger_path)
        if str(candidate.get("candidate_id") or "").strip() != str(row.get("candidate_id") or "").strip()
    ]
    existing.append(row)
    write_jsonl(ledger_path, existing)


def candidate_row(kernel_root: Path, topic_slug: str, run_id: str) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_type": "theorem_card",
        "title": "Jones Chapter 4 Finite-Product Block-Centralizer Type-I Packet",
        "summary": (
            "Bounded theorem-card candidate for the current Jones Chapter 4 finite-dimensional/type-I "
            "backbone: package the compile-checked block-centralizer finite-product theorem packet as "
            "the current honest finite-dimensional anchor, exposing the ambient centralizer as a linear "
            "product of block-fiber full-operator/type-I pieces together with the centralizer "
            "subalgebra identification, diagonal block-compression formula, and finrank audit, "
            "without claiming the stronger subalgebra-level AlgEquiv product theorem or the full "
            "Chapter 4 classification route."
        ),
        "topic_slug": topic_slug,
        "run_id": run_id,
        "origin_refs": origin_refs_for_candidate(kernel_root, topic_slug),
        "question": (
            "Can the bounded Jones Chapter 4 finite-product block-centralizer theorem packet travel "
            "through coverage audit, formal-theory review, topic-completion surfacing, Lean-bridge "
            "materialization, and L2_auto writeback without hiding the still-open stronger algebra-level "
            "product theorem, full type-I classification, or later Lane A/B/C follow-up routes?"
        ),
        "assumptions": [
            "This candidate is finite-dimensional and Chapter-4-local; it does not claim the full type-I classification theorem.",
            "The formal target is the current bounded theorem-facing packet `jonesFiniteDimensionalBlockCentralizerFiniteProductTypeITheoremPacket`, not the deferred subalgebra-level AlgEquiv product theorem.",
            "Lane A closure-bridge work, Lane B abstract/concrete equivalence, and Lane C multiplication-operator/masa work remain separate follow-up lanes.",
        ],
        "proposed_validation_route": "jones-ch4-finite-product-block-centralizer",
        "intended_l2_targets": [TARGET_UNIT_ID],
        "supporting_regression_question_ids": [
            "regression_question:state-jones-chapter-4-finite-dimensional-backbone",
            "regression_question:state-jones-whole-book-formalization-surface",
            "regression_question:state-jones-section-formalization-surface",
        ],
        "supporting_oracle_ids": [
            "question_oracle:state-jones-chapter-4-finite-dimensional-backbone",
            "question_oracle:state-jones-whole-book-formalization-surface",
            "question_oracle:state-jones-section-formalization-surface",
        ],
        "supporting_regression_run_ids": [
            "regression_run:jones-section-formalization-2026-03-24",
        ],
        "promotion_blockers": [],
        "split_required": False,
        "cited_recovery_required": False,
        "followup_gap_ids": [],
        "status": "ready_for_validation",
    }


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    env = runtime_env(kernel_root, repo_root)
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else (repo_root.parent / "_jones_accept" / uuid.uuid4().hex[:8]).resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)
    tpkn_work_root = work_root / "theoretical-physics-knowledge-network"
    if args.tpkn_template_root:
        tpkn_template_root = discover_tpkn_template_root(repo_root, args.tpkn_template_root)
        copy_tpkn_tree(tpkn_template_root, tpkn_work_root)
        ensure_kb_entrypoint(tpkn_work_root)
        tpkn_template_root_value = str(tpkn_template_root)
    else:
        create_minimal_tpkn_backend(tpkn_work_root)
        tpkn_template_root_value = "(generated-minimal)"

    human_request = (
        "Continue the active Jones topic by turning the already compile-checked Chapter 4 finite-product "
        "block-centralizer theorem packet into a governed formal-theory acceptance lane. Keep the result "
        "strictly finite-dimensional and honest about the still-open stronger algebra-level product theorem "
        "and the later Lane A/B/C routes."
    )
    statement = (
        "Materialize bounded formal-theory closure artifacts for the current Jones Chapter 4 finite-product "
        "block-centralizer theorem packet."
    )

    orchestrated = service.orchestrate(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        statement=statement,
        updated_by=args.updated_by,
        human_request=human_request,
        research_mode="formal_derivation",
    )
    service.audit(topic_slug=args.topic_slug, phase="entry", updated_by=args.updated_by)

    feedback_root = kernel_root / "feedback" / "topics" / args.topic_slug / "runs" / args.run_id
    feedback_root.mkdir(parents=True, exist_ok=True)
    candidate_ledger_path = feedback_root / "candidate_ledger.jsonl"
    service._replace_candidate_row(
        args.topic_slug,
        args.run_id,
        CANDIDATE_ID,
        candidate_row(kernel_root, args.topic_slug, args.run_id),
    )
    validation_run_root = kernel_root / "validation" / "topics" / args.topic_slug / "runs" / args.run_id
    (validation_run_root / "theory-packets" / CANDIDATE_SLUG).mkdir(
        parents=True,
        exist_ok=True,
    )
    (validation_run_root / "lean-bridge" / CANDIDATE_SLUG).mkdir(
        parents=True,
        exist_ok=True,
    )

    coverage = service.audit_theory_coverage(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        candidate_id=CANDIDATE_ID,
        updated_by=args.updated_by,
        source_sections=[
            "chapter-4/definition-of-type-i-factor",
            "chapter-4/classification-of-all-type-i-factors",
            "chapter-4/multiplicity-and-finite-dimensional-von-neumann-algebras",
        ],
        covered_sections=[
            "chapter-4/definition-of-type-i-factor",
            "chapter-4/classification-of-all-type-i-factors",
            "chapter-4/multiplicity-and-finite-dimensional-von-neumann-algebras",
        ],
        notation_bindings=[
            {"symbol": "block", "meaning": "finite partition map on the ambient coordinate index set"},
            {"symbol": "B(ℂ^{ι_k})", "meaning": "full operator model on the block fiber indexed by k"},
            {"symbol": "centralizer", "meaning": "bounded operators commuting with all block projections"},
        ],
        derivation_nodes=[
            "theorem:finite-dimensional-full-operator-von-neumann-algebra-has-scalar-commutant",
            "theorem:finite-dimensional-full-operator-algebra-admits-block-decomposition",
            "theorem:finite-dimensional-block-projection-centralizer-has-off-block-vanishing-characterization",
            "proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition",
            "proof_fragment:finite-dimensional-block-centralizer-is-supremum-of-single-block-matrix-unit-spans",
            "proof_fragment:finite-dimensional-block-centralizer-block-fiber-factor-shadow",
            "proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares",
        ],
        derivation_edges=[
            {
                "source": "theorem:finite-dimensional-full-operator-algebra-admits-block-decomposition",
                "target": "theorem:finite-dimensional-block-projection-centralizer-has-off-block-vanishing-characterization",
                "relation": "supports",
            },
            {
                "source": "theorem:finite-dimensional-block-projection-centralizer-has-off-block-vanishing-characterization",
                "target": "proof_fragment:finite-dimensional-block-centralizer-is-supremum-of-single-block-matrix-unit-spans",
                "relation": "refines_to",
            },
            {
                "source": "proof_fragment:finite-dimensional-block-centralizer-block-fiber-factor-shadow",
                "target": "proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition",
                "relation": "assembles",
            },
            {
                "source": "proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition",
                "target": "proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares",
                "relation": "audits",
            },
        ],
        agent_votes=[
            {
                "role": "structure",
                "verdict": "covered",
                "notes": "The bounded Chapter 4 finite-dimensional theorem packet is source-mapped and structurally explicit.",
            },
            {
                "role": "skeptic",
                "verdict": "no_major_gap",
                "notes": "The candidate stays honest about missing stronger algebra-level and whole-chapter routes.",
            },
            {
                "role": "adjudicator",
                "verdict": "unanimous",
                "notes": "Safe to exercise the formal-theory acceptance lane on this bounded Chapter 4 target.",
            },
        ],
        consensus_status="unanimous",
        critical_unit_recall=1.0,
        missing_anchor_count=0,
        skeptic_major_gap_count=0,
        supporting_regression_question_ids=[
            "regression_question:state-jones-chapter-4-finite-dimensional-backbone",
            "regression_question:state-jones-whole-book-formalization-surface",
            "regression_question:state-jones-section-formalization-surface",
        ],
        supporting_oracle_ids=[
            "question_oracle:state-jones-chapter-4-finite-dimensional-backbone",
            "question_oracle:state-jones-whole-book-formalization-surface",
            "question_oracle:state-jones-section-formalization-surface",
        ],
        supporting_regression_run_ids=[
            "regression_run:jones-section-formalization-2026-03-24",
        ],
        promotion_blockers=[],
        split_required=False,
        cited_recovery_required=False,
        followup_gap_ids=[],
        topic_completion_status="promotion-ready",
        notes="Bounded Jones Chapter 4 acceptance for the finite-dimensional finite-product block-centralizer theorem packet.",
    )

    formal_review = service.audit_formal_theory(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        candidate_id=CANDIDATE_ID,
        updated_by=args.updated_by,
        formal_theory_role="trusted_target",
        statement_graph_role="target_statement",
        target_statement_id=TARGET_UNIT_ID,
        statement_graph_parents=[
            "definition:finite-dimensional-type-i-factor",
            "theorem:finite-dimensional-full-operator-von-neumann-algebra-has-scalar-commutant",
            "theorem:finite-dimensional-block-projection-centralizer-has-off-block-vanishing-characterization",
        ],
        statement_graph_children=[
            "proof_fragment:finite-dimensional-block-centralizer-diagonal-block-compression-decomposition",
            "proof_fragment:finite-dimensional-block-centralizer-finrank-sum-of-block-fiber-squares",
        ],
        informal_statement=(
            "For a finite block decomposition, the Jones Chapter 4 bounded theorem packet identifies the "
            "block-projection centralizer with a linear product of block-fiber full-operator/type-I pieces, "
            "together with the within-block subalgebra equality, diagonal block-compression decomposition, "
            "and the finite-dimensional finrank sum formula."
        ),
        formal_target="AITP.Jones2015.jonesFiniteDimensionalBlockCentralizerFiniteProductTypeITheoremPacket",
        faithfulness_status="reviewed",
        faithfulness_strategy="bounded Chapter 4 source-map plus compile-checked theorem-packet comparison",
        comparator_audit_status="passed",
        comparator_risks=[
            "The current formal target is a theorem-facing linear finite-product packet and does not yet prove the stronger subalgebra-level AlgEquiv product theorem.",
            "The current packet remains finite-dimensional and does not close the full Chapter 4 type-I classification, tensor-product, or infinite-multiplicity routes.",
        ],
        provenance_kind="adapted_existing_formalization",
        attribution_requirements=[
            "Preserve the Jones Chapter 4 finite-dimensional/type-I source anchors and keep the bounded theorem-packet boundary explicit.",
        ],
        provenance_sources=[
            "research/open-physics-kb/examples/jones-2015-von-neumann-algebras/lean/JonesVonNeumannDefinitions/Jones2015/Section4FiniteDimensionalBlockProjectionCentralizer.lean::AITP.Jones2015.jonesFiniteDimensionalBlockCentralizerFiberPiTypeIPacket",
            "research/open-physics-kb/examples/jones-2015-von-neumann-algebras/lean/JonesVonNeumannDefinitions/Jones2015/Section4FiniteDimensionalBlockProjectionCentralizer.lean::AITP.Jones2015.finrank_jonesBlockProjectionCentralizerSubalgebra",
            "research/open-physics-kb/examples/jones-2015-von-neumann-algebras/lean/JonesVonNeumannDefinitions/Jones2015/Chapter4FiniteDimensionalVonNeumannAlgebrasAndTypeIFactors.lean::AITP.Jones2015.jonesFiniteDimensionalBlockCentralizerFiniteProductTypeITheoremPacket",
        ],
        prerequisite_closure_status="closed",
        lean_prerequisite_ids=[
            "AITP.Jones2015.jonesFiniteDimensionalTypeIClassificationTheoremPacket",
            "AITP.Jones2015.jonesFiniteDimensionalBlockCentralizerFiberPiTypeIPacket",
            "AITP.Jones2015.finrank_jonesBlockProjectionCentralizerSubalgebra",
        ],
        supporting_obligation_ids=[
            "proof_obligation:jones-ch4-block-centralizer-isup-decomposition",
            "proof_obligation:jones-ch4-block-centralizer-linear-product-transport",
            "proof_obligation:jones-ch4-block-centralizer-finrank-audit",
        ],
        prerequisite_notes="The current Chapter 4 target is intentionally limited to the finite-dimensional theorem packet already validated against the Lean benchmark.",
    )
    formal_review_path = (
        kernel_root
        / "validation"
        / "topics"
        / args.topic_slug
        / "runs"
        / args.run_id
        / "theory-packets"
        / CANDIDATE_SLUG
        / "formal_theory_review.json"
    )
    coverage_ledger_path = (
        kernel_root
        / "validation"
        / "topics"
        / args.topic_slug
        / "runs"
        / args.run_id
        / "theory-packets"
        / CANDIDATE_SLUG
        / "coverage_ledger.json"
    )
    strategy_memory = service.record_strategy_memory(
        topic_slug=args.topic_slug,
        run_id=args.run_id,
        strategy_type="verification_guardrail",
        summary=(
            "Read the ready formal-theory review packet before reusing the bounded Jones Chapter 4 theorem-facing route."
        ),
        outcome="helpful",
        lane="formal_theory",
        confidence=0.84,
        evidence_refs=[str(formal_review_path), str(coverage_ledger_path)],
        reuse_conditions=[
            "bounded Jones Chapter 4 finite-dimensional theorem packet",
            "formal_theory review overall_status=ready",
            "topic completion promotion-ready or promoted",
        ],
        do_not_apply_when=[
            "the route still lacks a ready formal_theory_review.json",
            "the task is claiming the stronger algebra-level product theorem rather than the bounded theorem packet",
        ],
        human_note="Use the projection only as theorem-facing execution memory, not as theorem certification.",
        updated_by=args.updated_by,
    )

    verification = service.prepare_verification(
        topic_slug=args.topic_slug,
        mode="topic-completion",
        updated_by=args.updated_by,
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
    projection_payload = service.project_topic_skill(
        topic_slug=args.topic_slug,
        updated_by=args.updated_by,
    )
    projection = projection_payload["topic_skill_projection"]
    projection_candidate = projection_payload["topic_skill_projection_candidate"]
    check(
        str(projection.get("status") or "") == "available",
        "Expected the Jones formal-theory topic-skill projection to be available.",
    )
    check(
        projection_candidate is not None,
        "Expected the Jones formal-theory topic-skill projection to materialize an L3 candidate.",
    )
    projection_request = service.request_promotion(
        topic_slug=args.topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        backend_id="backend:theoretical-physics-knowledge-network",
        target_backend_root=str(tpkn_work_root),
        requested_by=args.updated_by,
    )
    projection_approve = service.approve_promotion(
        topic_slug=args.topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        approved_by=args.updated_by,
    )
    projection_promote = service.promote_candidate(
        topic_slug=args.topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        promoted_by=args.updated_by,
        target_backend_root=str(tpkn_work_root),
        domain="operator-algebras",
        subdomain="finite-dimensional-von-neumann-algebras",
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
            "operator-algebras",
            "--subdomain",
            "finite-dimensional-von-neumann-algebras",
            "--source-id",
            PRIMARY_SOURCE_ID,
            "--source-section",
            PRIMARY_SOURCE_SECTION,
            "--source-section-title",
            PRIMARY_SOURCE_SECTION_TITLE,
            "--notes",
            "Bounded Jones Chapter 4 formal-closure acceptance for the finite-dimensional finite-product block-centralizer theorem packet.",
            "--updated-by",
            args.updated_by,
            "--json",
        ],
        env,
    )
    final_completion = run_python_json(
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

    exit_audit = service.audit(topic_slug=args.topic_slug, phase="exit", updated_by=args.updated_by)
    status_payload = service.topic_status(topic_slug=args.topic_slug, updated_by=args.updated_by)

    topic_completion_path = kernel_root / "runtime" / "topics" / args.topic_slug / "topic_completion.json"
    lean_bridge_path = kernel_root / "runtime" / "topics" / args.topic_slug / "lean_bridge.active.json"
    validation_contract_path = kernel_root / "runtime" / "topics" / args.topic_slug / "validation_contract.active.json"
    promotion_gate_path = kernel_root / "runtime" / "topics" / args.topic_slug / "promotion_gate.json"
    projection_path = kernel_root / "runtime" / "topics" / args.topic_slug / "topic_skill_projection.active.json"
    projection_note_path = kernel_root / "runtime" / "topics" / args.topic_slug / "topic_skill_projection.active.md"
    theory_packet_root = (
        kernel_root
        / "validation"
        / "topics"
        / args.topic_slug
        / "runs"
        / args.run_id
        / "theory-packets"
        / CANDIDATE_SLUG
    )
    lean_packet_root = (
        kernel_root
        / "validation"
        / "topics"
        / args.topic_slug
        / "runs"
        / args.run_id
        / "lean-bridge"
        / CANDIDATE_SLUG
    )
    check(
        str(auto_promotion.get("source_manifest_path") or "").strip(),
        "Expected auto promotion to return a source_manifest_path.",
    )
    source_manifest_path = Path(str(auto_promotion.get("source_manifest_path") or ""))
    theorem_promotion_gate_payload = json.loads(promotion_gate_path.read_text(encoding="utf-8"))
    theorem_promoted_unit_ids = theorem_promotion_gate_payload.get("promoted_units") or []
    check(theorem_promoted_unit_ids, "Expected at least one promoted theorem unit id in promotion_gate.json.")
    theorem_promoted_unit_slug = str(theorem_promoted_unit_ids[0]).split(":", 1)[-1]
    theorem_promoted_unit_path = tpkn_work_root / "units" / "theorems" / f"{theorem_promoted_unit_slug}.json"
    ensure_exists(theorem_promoted_unit_path)
    theorem_promoted_unit_payload = json.loads(theorem_promoted_unit_path.read_text(encoding="utf-8"))
    projection_promoted_unit_path = Path(str(projection_promote["target_unit_path"]))
    ensure_exists(projection_promoted_unit_path)
    projection_promoted_unit_payload = json.loads(projection_promoted_unit_path.read_text(encoding="utf-8"))

    for path in (
        candidate_ledger_path,
        Path(strategy_memory["strategy_memory_path"]),
        topic_completion_path,
        lean_bridge_path,
        validation_contract_path,
        promotion_gate_path,
        projection_path,
        projection_note_path,
        theory_packet_root / "coverage_ledger.json",
        theory_packet_root / "formal_theory_review.json",
        lean_packet_root / "lean_ready_packet.json",
        lean_packet_root / "proof_obligations.json",
        lean_packet_root / "proof_state.json",
        theory_packet_root / "auto_promotion_report.json",
        source_manifest_path,
        projection_promoted_unit_path,
        theorem_promoted_unit_path,
    ):
        ensure_exists(path)

    candidate_rows = read_jsonl(candidate_ledger_path)
    candidate_payload = next(
        row for row in candidate_rows if str(row.get("candidate_id") or "").strip() == CANDIDATE_ID
    )
    projection_candidate_payload = next(
        row
        for row in candidate_rows
        if str(row.get("candidate_id") or "").strip() == str(projection_candidate["candidate_id"] or "").strip()
    )
    topic_completion_payload = json.loads(topic_completion_path.read_text(encoding="utf-8"))
    lean_bridge_payload = json.loads(lean_bridge_path.read_text(encoding="utf-8"))
    validation_contract_payload = json.loads(validation_contract_path.read_text(encoding="utf-8"))
    promotion_gate_payload = json.loads(promotion_gate_path.read_text(encoding="utf-8"))
    candidate_lean_packet = next(
        packet
        for packet in lean_bridge_payload.get("packets") or []
        if str(packet.get("candidate_id") or "").strip() == CANDIDATE_ID
    )
    check(str(coverage.get("coverage_status") or "") == "pass", "Expected Jones Chapter 4 coverage audit to pass.")
    check(str(formal_review.get("overall_status") or "") == "ready", "Expected Jones Chapter 4 formal theory review to be ready.")
    check(
        str(validation_contract_payload.get("validation_mode") or "") == "hybrid",
        "Expected the Jones validation contract to move to topic-completion mode.",
    )
    check(
        str(candidate_lean_packet.get("status") or "") == "ready",
        "Expected the Jones Chapter 4 Lean bridge packet to be ready.",
    )
    check(
        str(theorem_promotion_gate_payload.get("status") or "") == "promoted",
        "Expected the Jones Chapter 4 theorem promotion gate to finish in promoted status.",
    )
    check(
        str(candidate_payload.get("status") or "") == "auto_promoted",
        "Expected the Jones Chapter 4 candidate ledger row to end in auto_promoted status.",
    )
    check(
        str(theorem_promoted_unit_payload.get("canonical_layer") or "") == "L2_auto",
        "Expected the promoted Jones Chapter 4 unit to land in canonical_layer L2_auto.",
    )
    check(
        str(theorem_promoted_unit_payload.get("review_mode") or "") == "ai_auto",
        "Expected the promoted Jones Chapter 4 unit to preserve ai_auto review mode.",
    )
    check(
        str(topic_completion_payload.get("status") or "") in {"promotion-ready", "promoted"},
        "Expected Jones topic-completion status to remain promotion-ready or promoted.",
    )
    check(
        str(projection_candidate_payload.get("candidate_type") or "") == "topic_skill_projection",
        "Expected the Jones projection candidate ledger row to be topic_skill_projection.",
    )
    check(
        str(projection_candidate_payload.get("promotion_mode") or "") == "human",
        "Expected the Jones projection candidate to stay on the human-reviewed route.",
    )
    check(
        "/units/topic-skill-projections/" in str(projection_promote.get("target_unit_path") or "").replace("\\", "/"),
        "Expected the Jones projection promotion to land in units/topic-skill-projections/.",
    )
    check(
        str(projection_promoted_unit_payload.get("type") or "") == "topic_skill_projection",
        "Expected the promoted Jones projection unit type to be topic_skill_projection.",
    )
    check(
        str(status_payload["topic_skill_projection"]["status"]) == "available",
        "Expected topic status to surface the available Jones formal-theory projection.",
    )
    projection_note_row = next(
        row
        for row in status_payload["must_read_now"]
        if str(row.get("path") or "").endswith("topic_skill_projection.active.md")
    )
    check(
        "theorem-facing route" in str(projection_note_row.get("reason") or ""),
        "Expected runtime read-path reason to mention the theorem-facing route for the Jones projection.",
    )

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
        "lean_bridge_status": candidate_lean_packet.get("status"),
        "auto_promotion_status": theorem_promotion_gate_payload.get("status"),
        "topic_skill_projection_status": status_payload["topic_skill_projection"]["status"],
        "artifacts": {
            "topic_state": orchestrated["files"]["topic_state"],
            "runtime_protocol": orchestrated["files"]["runtime_protocol"],
            "candidate_ledger": str(candidate_ledger_path),
            "validation_contract": str(validation_contract_path),
            "topic_completion": str(topic_completion_path),
            "lean_bridge": str(lean_bridge_path),
            "topic_skill_projection": str(projection_path),
            "topic_skill_projection_note": str(projection_note_path),
            "strategy_memory": str(strategy_memory["strategy_memory_path"]),
            "lean_ready_packet": str(lean_packet_root / "lean_ready_packet.json"),
            "proof_obligations": str(lean_packet_root / "proof_obligations.json"),
            "proof_state": str(lean_packet_root / "proof_state.json"),
            "coverage_ledger": str(theory_packet_root / "coverage_ledger.json"),
            "formal_theory_review": str(theory_packet_root / "formal_theory_review.json"),
            "auto_promotion_report": str(theory_packet_root / "auto_promotion_report.json"),
            "promotion_gate": str(promotion_gate_path),
            "promoted_theorem_unit": str(theorem_promoted_unit_path),
            "promoted_projection_unit": str(projection_promoted_unit_path),
            "source_manifest": str(source_manifest_path),
            "conformance_report": exit_audit["conformance_report_path"],
        },
        "dispatch_payloads": {
            "topic_completion_before_promotion": completion,
            "lean_bridge": lean_bridge,
            "auto_promotion": auto_promotion,
            "topic_completion_after_promotion": final_completion,
        },
        "projection_payload": {
            "strategy_memory": strategy_memory,
            "project_topic_skill": projection_payload,
            "request_promotion": projection_request,
            "approve_promotion": projection_approve,
            "promote": projection_promote,
            "topic_status": {
                "topic_skill_projection": status_payload["topic_skill_projection"],
                "must_read_now": status_payload["must_read_now"],
            },
        },
        "verification_payload": verification,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
