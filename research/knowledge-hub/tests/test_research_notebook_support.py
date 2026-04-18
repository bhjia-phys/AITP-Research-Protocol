from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub import research_notebook_support as notebook


def test_preamble_includes_notebook_layout_and_box_styling() -> None:
    assert r"\usepackage[most]{tcolorbox}" in notebook._PREAMBLE
    assert r"\usepackage{tabularx}" in notebook._PREAMBLE
    assert r"\begin{titlepage}" in notebook._PREAMBLE
    assert "TOPIC_SLUG_PLACEHOLDER" in notebook._PREAMBLE
    assert "DATE_PLACEHOLDER" in notebook._PREAMBLE


def test_render_entry_uses_kind_box_metadata_badges_and_detail_table() -> None:
    rendered = notebook._render_entry(
        {
            "kind": "candidate_update",
            "timestamp": "2026-04-18T10:20:30+08:00",
            "run_id": "run-42",
            "title": "Gap Closure Benchmark",
            "body": "Observed $E=mc^2$ agreement.\n\n$$a^2+b^2=c^2$$",
            "status": "approved",
            "details": {
                "acceptance_metric": "0.5%",
                "artifacts": ["plot.pdf", "table.csv"],
            },
        }
    )

    assert r"\section{Candidate Update: Gap Closure Benchmark}" in rendered
    assert r"\begin{tcolorbox}[" in rendered
    assert "candidateframe" in rendered
    assert r"\kindpill{candidateframe}{Candidate Update}" in rendered
    assert r"\entrytag{candidate\_update}" in rendered
    assert r"\metaitem{Time}{2026-04-18T10:20:30+08:00}" in rendered
    assert r"\metaitem{Run}{run-42}" in rendered
    assert r"\statusgood{approved}" in rendered
    assert r"\begin{tabularx}{\linewidth}" in rendered
    assert "acceptance\\_metric" in rendered
    assert "$E=mc^2$" in rendered
    assert "$$a^2+b^2=c^2$$" in rendered


def test_topic_notebook_compiles_runtime_l1_and_l3_surfaces_into_archive_sections() -> None:
    with tempfile.TemporaryDirectory() as td:
        topic_root = Path(td) / "topics" / "demo-topic"
        l3_root = topic_root / "L3"
        runtime_root = topic_root / "runtime"
        run_root = l3_root / "runs" / "run-001"
        l3_root.mkdir(parents=True, exist_ok=True)
        runtime_root.mkdir(parents=True, exist_ok=True)
        run_root.mkdir(parents=True, exist_ok=True)

        (runtime_root / "research_question.contract.json").write_text(
            json.dumps(
                {
                    "title": "Demo Topic",
                    "question": "Recover the bounded derivation and benchmark route.",
                    "scope": [
                        "Stay within the currently registered source set.",
                        "Track notation and validation obligations explicitly.",
                    ],
                    "assumptions": [
                        "Only persisted evidence counts.",
                    ],
                    "open_ambiguities": [
                        "The sign convention for the response coefficient remains unresolved.",
                    ],
                    "formalism_and_notation": [
                        "Use Euclidean-signature notation unless a source explicitly says otherwise.",
                    ],
                    "deliverables": [
                        "Produce a bounded candidate and one explicit validation route.",
                    ],
                    "l1_source_intake": {
                        "source_count": 2,
                        "reading_depth_rows": [
                            {
                                "source_title": "Lecture Notes A",
                                "reading_depth": "full_read",
                            },
                            {
                                "source_title": "Benchmark Paper B",
                                "reading_depth": "skim",
                            },
                        ],
                        "method_specificity_rows": [
                            {
                                "source_title": "Lecture Notes A",
                                "method_family": "derivation",
                                "specificity_tier": "high",
                            }
                        ],
                        "notation_tension_candidates": [
                            {
                                "summary": "Paper A uses k while Paper B uses sigma_xy for the same response coefficient."
                            }
                        ],
                        "contradiction_candidates": [
                            {
                                "summary": "Benchmark ranges disagree outside the weak-coupling regime."
                            }
                        ],
                    },
                    "l1_vault": {
                        "wiki": {
                            "page_paths": [
                                "topics/demo-topic/L1/vault/wiki/home.md",
                                "topics/demo-topic/L1/vault/wiki/source-bridge.md",
                            ]
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (runtime_root / "idea_packet.json").write_text(
            json.dumps(
                {
                    "status": "approved_for_execution",
                    "initial_idea": "Understand the literature derivation and turn it into a bounded executable question.",
                    "novelty_target": "Clarify the derivation path and benchmark boundary.",
                    "first_validation_route": "Bounded benchmark comparison",
                    "initial_evidence_bar": "Persisted derivation notes plus one explicit validation artifact.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (runtime_root / "unfinished_work.json").write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "summary": "Recover the missing intermediate derivation step from the cited source.",
                            "status": "pending",
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        (run_root / "derivation_records.jsonl").write_text(
            json.dumps(
                {
                    "derivation_id": "derivation:demo-reconstruction",
                    "title": "Response-coefficient reconstruction from source A",
                    "derivation_kind": "source_reconstruction",
                    "status": "in_progress",
                    "body": "Starting from the source statement, we recover\n\n$$k = \\frac{1}{2\\pi} \\int F$$",
                    "source_refs": [
                        "paper-a §2 eq.(4)",
                        "paper-b §3 benchmark discussion",
                    ],
                    "assumptions": ["Weak-coupling regime", "Translation invariance"],
                    "provenance_note": "This derivation is reconstructed in L3 from the cited source, not copied as an authoritative result.",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / "l2_comparison_receipts.jsonl").write_text(
            json.dumps(
                {
                    "comparison_id": "comparison:demo-benchmark-check",
                    "candidate_ref_id": "candidate:demo-bound",
                    "title": "Benchmark-facing derivation comparison",
                    "comparison_summary": "The reconstructed route matches the nearby L2 derivation up to one normalization convention that remains explicit.",
                    "compared_unit_ids": [
                        "derivation:chern-benchmark-demo",
                    ],
                    "comparison_scope": "bounded benchmark route",
                    "outcome": "partial_match",
                    "limitations": [
                        "Normalization differs by a convention-dependent factor pending explicit closure.",
                    ],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / "candidate_ledger.jsonl").write_text(
            json.dumps(
                {
                    "candidate_id": "candidate:demo-bound",
                    "candidate_type": "derivation_object",
                    "title": "Bounded response derivation",
                    "summary": "A source-grounded derivation candidate for the response coefficient.",
                    "status": "ready_for_validation",
                    "question": "Does the reconstructed derivation agree with the benchmark regime?",
                    "assumptions": ["Weak-coupling regime", "Translation invariance"],
                    "proposed_validation_route": "benchmark_review",
                    "intended_l2_targets": ["derivation:demo-bound"],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / "strategy_memory.jsonl").write_text(
            json.dumps(
                {
                    "summary": "Check notation alignment before comparing benchmark formulas.",
                    "strategy_type": "verification_guardrail",
                    "outcome": "helpful",
                    "confidence": 0.81,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (run_root / "iteration_journal.json").write_text(
            json.dumps(
                {
                    "run_id": "run-001",
                    "status": "iterating",
                    "current_iteration_id": "iteration-002",
                    "iteration_ids": ["iteration-001", "iteration-002"],
                    "latest_conclusion_status": "continue_iteration",
                    "latest_staging_decision": "defer",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        notebook.append_notebook_entry(
            l3_root,
            kind="candidate_update",
            title="Bounded response derivation",
            body="A first candidate has been recorded.",
            status="ready_for_validation",
            run_id="run-001",
            details={"candidate_id": "candidate:demo-bound"},
        )

        tex = (l3_root / "research_notebook.tex").read_text(encoding="utf-8")

        assert r"\section{Research Framing}" in tex
        assert "Recover the bounded derivation and benchmark route." in tex
        assert r"\section{Source Provenance Map}" in tex
        assert "Lecture Notes A" in tex
        assert "Paper A uses k while Paper B uses sigma\\_xy" in tex
        assert r"\section{Derivation Notebook}" in tex
        assert "Response-coefficient reconstruction from source A" in tex
        assert "paper-a" in tex
        assert "This derivation is reconstructed in L3 from the cited source" in tex
        assert r"\section{L2 Comparison Receipts}" in tex
        assert "Benchmark-facing derivation comparison" in tex
        assert "Normalization differs by a convention-dependent factor" in tex
        assert r"\section{Run And Iteration Record}" in tex
        assert "run-001" in tex
        assert "iteration-002" in tex
        assert r"\section{Candidate Catalog}" in tex
        assert "candidate:demo-bound" in tex
        assert r"\section{Strategy And Failure Memory}" in tex
        assert "Check notation alignment before comparing benchmark formulas." in tex
        assert r"\section{Open Problems And Deferred Fragments}" in tex
        assert "Recover the missing intermediate derivation step" in tex
        assert r"\section{Chronological Entry Log}" in tex
