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

from knowledge_hub.l3_derivation_support import record_l3_derivation_entry
from knowledge_hub.aitp_service import AITPService
from knowledge_hub.topic_shell_support import compute_topic_completion_payload


def test_record_l3_derivation_entry_writes_run_surface_and_notebook_event() -> None:
    with tempfile.TemporaryDirectory() as td:
        topic_root = Path(td) / "topics" / "demo-topic"
        l3_root = topic_root / "L3"
        run_root = l3_root / "runs" / "run-001"
        run_root.mkdir(parents=True, exist_ok=True)

        result = record_l3_derivation_entry(
            run_root=run_root,
            topic_slug="demo-topic",
            run_id="run-001",
            title="Response reconstruction",
            body="Recover the main source-side derivation.\n\n$$k = \\frac{1}{2\\pi} \\int F$$",
            derivation_kind="source_reconstruction",
            status="in_progress",
            source_refs=["paper-a §2 eq.(4)"],
            assumptions=["Weak-coupling regime"],
            provenance_note="Reconstructed in L3 from the cited source.",
            updated_by="test",
        )

        ledger_path = run_root / "derivation_records.jsonl"
        note_path = run_root / "derivation_records.md"
        notebook_entries = l3_root / "research_notebook_entries.jsonl"

        assert result["derivation_id"].startswith("derivation:")
        assert ledger_path.exists()
        assert note_path.exists()
        assert notebook_entries.exists()

        rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) == 1
        assert rows[0]["title"] == "Response reconstruction"
        assert rows[0]["derivation_kind"] == "source_reconstruction"
        assert rows[0]["source_refs"] == ["paper-a §2 eq.(4)"]

        note_text = note_path.read_text(encoding="utf-8")
        assert "# L3 Derivation Records" in note_text
        assert "Response reconstruction" in note_text
        assert "paper-a §2 eq.(4)" in note_text

        notebook_rows = [json.loads(line) for line in notebook_entries.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(notebook_rows) == 1
        assert notebook_rows[0]["kind"] == "derivation_note"
        assert notebook_rows[0]["title"] == "Response reconstruction"


def test_derivation_candidate_update_auto_mirrors_into_derivation_records() -> None:
    with tempfile.TemporaryDirectory() as td:
        kernel_root = Path(td)
        service = AITPService(kernel_root=kernel_root, repo_root=Path.cwd().resolve())

        topic_slug = "demo-topic"
        run_id = "run-001"
        run_root = kernel_root / "topics" / topic_slug / "L3" / "runs" / run_id
        run_root.mkdir(parents=True, exist_ok=True)

        service._replace_candidate_row(
            topic_slug,
            run_id,
            "candidate:demo-derivation",
            {
                "candidate_id": "candidate:demo-derivation",
                "candidate_type": "derivation_object",
                "title": "Demo derivation candidate",
                "summary": "A bounded source-grounded derivation candidate.",
                "question": "Does the reconstructed derivation close without changing conventions?",
                "assumptions": ["Weak-coupling regime"],
                "status": "ready_for_validation",
                "origin_refs": [
                    {
                        "id": "paper:demo-source",
                        "layer": "L0",
                        "path": "source-layer/topics/demo-topic/source_index.jsonl",
                        "title": "Demo source",
                    }
                ],
            },
        )

        ledger_path = run_root / "derivation_records.jsonl"
        assert ledger_path.exists()

        rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) == 1
        assert rows[0]["title"] == "Demo derivation candidate"
        assert rows[0]["derivation_kind"] == "candidate_derivation"
        assert "source-layer/topics/demo-topic/source_index.jsonl" in rows[0]["source_refs"][0]


def _promotion_ready_derivation_candidate() -> dict[str, object]:
    return {
        "candidate_id": "candidate:demo-derivation",
        "candidate_type": "derivation_object",
        "title": "Demo derivation candidate",
        "summary": "A bounded source-grounded derivation candidate.",
        "question": "Does the reconstructed derivation close without changing conventions?",
        "assumptions": ["Weak-coupling regime"],
        "status": "ready_for_validation",
        "topic_completion_status": "promotion-ready",
        "supporting_regression_question_ids": ["rq:1"],
        "supporting_oracle_ids": ["oracle:1"],
        "supporting_regression_run_ids": ["run:1"],
        "origin_refs": [
            {
                "id": "paper:demo-source",
                "layer": "L0",
                "path": "source-layer/topics/demo-topic/source_index.jsonl",
                "title": "Demo source",
            }
        ],
    }


def test_derivation_candidate_without_detailed_body_blocks_promotion_readiness_and_completion() -> None:
    with tempfile.TemporaryDirectory() as td:
        kernel_root = Path(td)
        service = AITPService(kernel_root=kernel_root, repo_root=Path.cwd().resolve())
        candidate = _promotion_ready_derivation_candidate()

        readiness = service._derive_promotion_readiness(
            topic_slug="demo-topic",
            latest_run_id="run-001",
            promotion_gate={},
            candidate_rows=[candidate],
        )
        completion = compute_topic_completion_payload(
            service,
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_rows=[candidate],
            updated_by="test",
        )

        assert readiness["status"] == "blocked"
        assert any("missing detailed L3 derivation record" in item for item in readiness["blockers"])
        assert completion["status"] == "promotion-blocked"
        assert any("missing detailed L3 derivation record" in item for item in completion["blockers"])


def test_detailed_derivation_and_l2_comparison_unblock_promotion_readiness_and_completion() -> None:
    with tempfile.TemporaryDirectory() as td:
        kernel_root = Path(td)
        service = AITPService(kernel_root=kernel_root, repo_root=Path.cwd().resolve())
        candidate = _promotion_ready_derivation_candidate()

        service.record_l3_derivation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="Demo derivation candidate",
            body="We reconstruct the source-side argument step by step and keep the regime assumptions explicit.\n\n$$k = \\frac{1}{2\\pi} \\int F$$\n\nThe remaining benchmark comparison checks whether the external normalization introduces any hidden factor.",
            derivation_kind="source_reconstruction",
            epistemic_status="ai_provisional_reasoning",
            status="in_progress",
            source_refs=["source-layer/topics/demo-topic/source_index.jsonl"],
            assumptions=["Weak-coupling regime"],
            provenance_note="This is an AI-authored provisional derivation record, not truth by itself.",
            derivation_id="candidate:demo-derivation",
        )
        service.record_l2_derivation_comparison(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_id="candidate:demo-derivation",
            title="Benchmark comparison",
            comparison_summary="Compared the reconstructed derivation against a nearby L2 benchmark-facing derivation packet and tracked the remaining normalization caveat explicitly.",
            compared_unit_ids=["derivation:nearby-benchmark-demo"],
            comparison_scope="bounded benchmark route",
            outcome="partial_match",
            limitations=["A convention-dependent normalization caveat remains explicit."],
        )

        readiness = service._derive_promotion_readiness(
            topic_slug="demo-topic",
            latest_run_id="run-001",
            promotion_gate={},
            candidate_rows=[candidate],
        )
        completion = compute_topic_completion_payload(
            service,
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_rows=[candidate],
            updated_by="test",
        )

        assert readiness["status"] == "ready"
        assert not any("derivation" in item.lower() for item in readiness["blockers"])
        assert completion["status"] == "promotion-ready"


def test_detailed_derivation_still_blocked_without_l2_comparison_receipt() -> None:
    with tempfile.TemporaryDirectory() as td:
        kernel_root = Path(td)
        service = AITPService(kernel_root=kernel_root, repo_root=Path.cwd().resolve())
        candidate = _promotion_ready_derivation_candidate()

        service.record_l3_derivation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="Demo derivation candidate",
            body="We reconstruct the source-side argument step by step and keep the regime assumptions explicit.\n\n$$k = \\frac{1}{2\\pi} \\int F$$\n\nThe remaining benchmark comparison checks whether the external normalization introduces any hidden factor.",
            derivation_kind="source_reconstruction",
            epistemic_status="ai_provisional_reasoning",
            status="in_progress",
            source_refs=["source-layer/topics/demo-topic/source_index.jsonl"],
            assumptions=["Weak-coupling regime"],
            provenance_note="This is an AI-authored provisional derivation record, not truth by itself.",
            derivation_id="candidate:demo-derivation",
        )

        readiness = service._derive_promotion_readiness(
            topic_slug="demo-topic",
            latest_run_id="run-001",
            promotion_gate={},
            candidate_rows=[candidate],
        )
        completion = compute_topic_completion_payload(
            service,
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_rows=[candidate],
            updated_by="test",
        )

        assert readiness["status"] == "blocked"
        assert any("comparison receipt" in item.lower() for item in readiness["blockers"])
        assert completion["status"] == "promotion-blocked"
        assert any("comparison receipt" in item.lower() for item in completion["blockers"])


def test_theorem_candidate_requires_theory_packet_surfaces_for_readiness() -> None:
    with tempfile.TemporaryDirectory() as td:
        kernel_root = Path(td)
        service = AITPService(kernel_root=kernel_root, repo_root=Path.cwd().resolve())
        candidate = {
            "candidate_id": "candidate:demo-theorem",
            "candidate_type": "theorem_card",
            "title": "Demo theorem candidate",
            "summary": "A bounded theorem-facing candidate.",
            "question": "Does the theorem packet really close?",
            "assumptions": ["Bounded theorem scope"],
            "status": "ready_for_validation",
            "topic_completion_status": "promotion-ready",
            "supporting_regression_question_ids": ["rq:1"],
            "supporting_oracle_ids": ["oracle:1"],
            "supporting_regression_run_ids": ["run:1"],
            "origin_refs": [
                {
                    "id": "paper:demo-source",
                    "layer": "L0",
                    "path": "source-layer/topics/demo-topic/source_index.jsonl",
                    "title": "Demo source",
                }
            ],
            "formal_theory_role": "trusted_target",
            "statement_graph_role": "target_statement",
        }

        service.record_l3_derivation(
            topic_slug="demo-topic",
            run_id="run-001",
            title="Demo theorem candidate",
            body="We reconstruct the theorem-facing derivation spine in detail.\n\n$$A \\Rightarrow B$$\n\nA separate theory packet must still capture the proof spine before the theorem is called promotion-ready.",
            derivation_kind="candidate_derivation",
            epistemic_status="ai_provisional_reasoning",
            status="in_progress",
            source_refs=["source-layer/topics/demo-topic/source_index.jsonl"],
            assumptions=["Bounded theorem scope"],
            provenance_note="This is an AI-authored provisional derivation record, not truth by itself.",
            derivation_id="candidate:demo-theorem",
        )
        service.record_l2_derivation_comparison(
            topic_slug="demo-topic",
            run_id="run-001",
            candidate_id="candidate:demo-theorem",
            title="Theorem comparison",
            comparison_summary="Compared the theorem-facing route against one nearby L2 theorem packet.",
            compared_unit_ids=["theorem:nearby-demo"],
            comparison_scope="bounded theorem packet",
            outcome="partial_match",
            limitations=["The proof spine is not yet fully captured."],
        )

        readiness = service._derive_promotion_readiness(
            topic_slug="demo-topic",
            latest_run_id="run-001",
            promotion_gate={},
            candidate_rows=[candidate],
        )

        assert readiness["status"] == "blocked"
        assert any("theory-packet derivation graph" in item.lower() for item in readiness["blockers"])
