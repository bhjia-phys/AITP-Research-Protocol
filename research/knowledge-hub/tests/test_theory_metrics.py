from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import AITPService


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


class TheoryMetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.kernel_root.mkdir(parents=True)
        self.repo_root.mkdir(parents=True)
        (self.kernel_root / "canonical").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, self.kernel_root / "schemas" / schema_path.name)
        runtime_bundle_schema = self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        shutil.copyfile(
            runtime_bundle_schema,
            self.kernel_root / "runtime" / "schemas" / runtime_bundle_schema.name,
        )
        shutil.copytree(
            self.package_root / "runtime" / "scripts",
            self.kernel_root / "runtime" / "scripts",
            dirs_exist_ok=True,
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_runtime_state(self, topic_slug: str = "demo-topic", run_id: str = "2026-03-13-demo") -> Path:
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": run_id,
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return runtime_root

    def _write_candidate(
        self,
        *,
        topic_slug: str = "demo-topic",
        run_id: str = "2026-03-13-demo",
        candidate_type: str = "theorem_card",
        candidate_id: str = "candidate:demo-candidate",
    ) -> None:
        feedback_root = self.kernel_root / "feedback" / "topics" / topic_slug / "runs" / run_id
        feedback_root.mkdir(parents=True, exist_ok=True)
        ledger_path = feedback_root / "candidate_ledger.jsonl"
        row = {
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "title": "Demo theorem",
            "summary": "A bounded theorem packet for theory-metrics tests.",
            "topic_slug": topic_slug,
            "run_id": run_id,
            "origin_refs": [
                {
                    "id": "paper:demo-source",
                    "layer": "L0",
                    "object_type": "source",
                    "path": f"source-layer/topics/{topic_slug}/source_index.jsonl",
                    "title": "Demo Source",
                    "summary": "Demo source summary.",
                }
            ],
            "question": "Can this theorem-facing candidate clear the trust boundary?",
            "assumptions": ["Bounded example."],
            "proposed_validation_route": "bounded-formal-smoke",
            "intended_l2_targets": ["theorem:demo-theorem"],
            "status": "ready_for_validation",
        }
        ledger_path.write_text(json.dumps(row, ensure_ascii=True) + "\n", encoding="utf-8")

        source_root = self.kernel_root / "source-layer" / "topics" / topic_slug
        source_root.mkdir(parents=True, exist_ok=True)
        (source_root / "source_index.jsonl").write_text(
            json.dumps(
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Demo Source",
                    "topic_slug": topic_slug,
                    "summary": "Demo source summary.",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_conformance_shell_artifacts(self, *, topic_slug: str = "demo-topic", run_id: str = "2026-03-13-demo") -> None:
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": run_id,
                    "resume_stage": "L3",
                    "research_mode": "formal_theory",
                    "active_executor_kind": "codex",
                    "pointers": {
                        "research_question_contract_path": f"runtime/topics/{topic_slug}/research_question.contract.json",
                        "validation_contract_path": f"runtime/topics/{topic_slug}/validation_contract.active.json",
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "resume.md").write_text("# Resume\n", encoding="utf-8")
        (runtime_root / "agent_brief.md").write_text("# Agent brief\n", encoding="utf-8")
        (runtime_root / "operator_console.md").write_text("# Operator console\n", encoding="utf-8")
        (runtime_root / "unfinished_work.json").write_text(
            json.dumps({"status": "active", "items": []}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "unfinished_work.md").write_text("# Unfinished work\n", encoding="utf-8")
        (runtime_root / "next_action_decision.json").write_text(
            json.dumps(
                {
                    "policy": {"default_mode": "continue_unfinished"},
                    "decision_mode": "continue_unfinished",
                    "selected_action": {"action_id": f"action:{topic_slug}:inspect"},
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "next_action_decision.md").write_text("# Next action\n", encoding="utf-8")
        (runtime_root / "action_queue_contract.generated.json").write_text(
            json.dumps(
                {
                    "actions": [
                        {
                            "action_id": f"action:{topic_slug}:inspect",
                            "status": "pending",
                            "action_type": "inspect_runtime",
                            "summary": "Inspect the runtime state before the next bounded step.",
                            "auto_runnable": False,
                        }
                    ]
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue_contract.generated.md").write_text("# Action queue contract\n", encoding="utf-8")
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": f"action:{topic_slug}:inspect",
                    "status": "pending",
                    "action_type": "inspect_runtime",
                    "summary": "Inspect the runtime state before the next bounded step.",
                    "auto_runnable": False,
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "Continue the active topic carefully.",
                    "human_edit_surfaces": [f"runtime/topics/{topic_slug}/operator_console.md"],
                    "delivery_contract": {"rule": "return_updated_runtime_state"},
                    "capability_adaptation": {"protocol_path": f"runtime/topics/{topic_slug}/capability_protocol.md"},
                    "decision_surface": {"next_action_decision_path": f"runtime/topics/{topic_slug}/next_action_decision.json"},
                    "action_queue_surface": {
                        "generated_contract_path": f"runtime/topics/{topic_slug}/action_queue_contract.generated.json"
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def test_theory_metrics_append_production_events(self) -> None:
        self._write_conformance_shell_artifacts()
        self._write_candidate()

        self.service.scaffold_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            title="Small-system validation backend",
            kind="numerical",
        )
        self.service.update_operation(
            topic_slug="demo-topic",
            run_id="2026-03-13-demo",
            operation="Small-system validation backend",
            baseline_status="passed",
        )
        self.service.audit(topic_slug="demo-topic", phase="exit")
        self.service.audit_theory_coverage(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            source_sections=["sec:intro"],
            covered_sections=["sec:intro"],
            missing_anchor_count=1,
            skeptic_major_gap_count=0,
            critical_unit_recall=0.8,
        )
        self.service.audit_formal_theory(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            formal_theory_role="trusted_target",
            statement_graph_role="target_statement",
            faithfulness_status="reviewed",
            comparator_audit_status="passed",
            prerequisite_closure_status="pending",
            formalization_blockers=["Missing prerequisite proof."],
        )
        self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            backend_id="backend:theoretical-physics-knowledge-network",
        )
        self.service.reject_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            notes="The bounded theorem packet is not ready.",
        )
        self.service.assess_topic_completion(topic_slug="demo-topic", run_id="2026-03-13-demo", refresh_runtime_bundle=False)

        metrics_root = self.kernel_root / "runtime" / "theory_metrics"
        global_rows = _read_jsonl(metrics_root / "theory_operations.jsonl")
        topic_rows = _read_jsonl(self.kernel_root / "runtime" / "topics" / "demo-topic" / "theory_operations.jsonl")

        operation_kinds = [row["operation_kind"] for row in global_rows]
        self.assertIn("conformance_audit", operation_kinds)
        self.assertIn("theory_coverage_audit", operation_kinds)
        self.assertIn("formal_theory_audit", operation_kinds)
        self.assertIn("promotion_request", operation_kinds)
        self.assertIn("promotion_reject", operation_kinds)
        self.assertIn("topic_completion_assessment", operation_kinds)
        self.assertEqual(len(global_rows), len(topic_rows))
        self.assertTrue(any("missing_source_anchors" in row.get("blocker_tags", []) for row in global_rows))
        self.assertTrue(any("prerequisite_closure_incomplete" in row.get("blocker_tags", []) for row in global_rows))
        self.assertTrue(any(row["status"] == "rejected" for row in global_rows if row["operation_kind"] == "promotion_reject"))

    def test_theory_metrics_analyzer_surfaces_actionable_proposals_with_confidence_scores(self) -> None:
        self._write_runtime_state()
        self._write_candidate()

        for _ in range(2):
            self.service.audit_theory_coverage(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                source_sections=["sec:intro"],
                covered_sections=["sec:intro"],
                missing_anchor_count=2,
                skeptic_major_gap_count=0,
                critical_unit_recall=0.7,
            )
            self.service.audit_formal_theory(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                formal_theory_role="trusted_target",
                statement_graph_role="target_statement",
                faithfulness_status="reviewed",
                comparator_audit_status="passed",
                prerequisite_closure_status="pending",
                formalization_blockers=["Missing prerequisite proof."],
            )
            self.service.request_promotion(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                backend_id="backend:theoretical-physics-knowledge-network",
            )
            self.service.reject_promotion(
                topic_slug="demo-topic",
                candidate_id="candidate:demo-candidate",
                notes="Still blocked by prerequisite debt.",
            )

        analysis = self.service.analyze_theory_metrics(topic_slug="demo-topic", updated_by="aitp-cli")

        proposal_kinds = {row["proposal_kind"] for row in analysis["proposals"]}
        self.assertIn("recover_source_anchors_before_coverage", proposal_kinds)
        self.assertIn("strengthen_prerequisite_closure_guidance", proposal_kinds)
        self.assertIn("surface_promotion_blockers_earlier", proposal_kinds)
        self.assertTrue(all(0.0 < float(row["confidence_score"]) <= 1.0 for row in analysis["proposals"]))
        self.assertTrue(any(row["evidence_count"] >= 2 for row in analysis["proposals"]))
        self.assertTrue(Path(analysis["analysis_json_path"]).exists())
        self.assertTrue(Path(analysis["analysis_note_path"]).exists())
        note_text = Path(analysis["analysis_note_path"]).read_text(encoding="utf-8")
        self.assertIn("confidence", note_text.lower())

        global_rows = _read_jsonl(self.kernel_root / "runtime" / "theory_metrics" / "theory_operations.jsonl")
        self.assertTrue(any(row["operation_kind"] == "derivation_retry" for row in global_rows))


if __name__ == "__main__":
    unittest.main()
