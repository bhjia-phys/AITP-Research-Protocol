from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from tests_support import copy_kernel_schema_files, copy_runtime_schema_files, make_temp_kernel  # noqa: E402
from knowledge_hub.aitp_service import AITPService  # noqa: E402
from knowledge_hub.runtime_projection_handler import (  # noqa: E402
    write_pending_decisions_projection,
    write_topic_synopsis,
)


class TopicTruthRootLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.package_root = Path(__file__).resolve().parents[1]
        self.fixture = make_temp_kernel("aitp-topic-truth-root-")
        self.kernel_root = self.fixture.kernel_root
        copy_kernel_schema_files(
            self.package_root,
            self.kernel_root,
            "topic-synopsis.schema.json",
        )
        copy_runtime_schema_files(
            self.package_root,
            self.kernel_root,
            "progressive-disclosure-runtime-bundle.schema.json",
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_service_uses_single_topic_truth_root_for_runtime_and_layer_paths(self) -> None:
        self.assertEqual(
            self.service._relativize(self.service._topic_root("demo-topic")),
            "topics/demo-topic",
        )
        self.assertEqual(
            self.service._relativize(self.service._runtime_root("demo-topic")),
            "topics/demo-topic/runtime",
        )
        self.assertEqual(
            self.service._relativize(self.service._l0_root("demo-topic")),
            "topics/demo-topic/L0",
        )
        self.assertEqual(
            self.service._relativize(self.service._feedback_run_root("demo-topic", "run-001")),
            "topics/demo-topic/L3/runs/run-001",
        )
        self.assertEqual(
            self.service._relativize(self.service._validation_run_root("demo-topic", "run-001")),
            "topics/demo-topic/L4/runs/run-001",
        )
        self.assertEqual(
            self.service._relativize(self.service._consultation_root("demo-topic")),
            "topics/demo-topic/consultation",
        )

    def test_ensure_runtime_root_creates_topic_manifest_and_layer_scaffold(self) -> None:
        runtime_root = self.service._ensure_runtime_root("demo-topic")
        topic_root = self.service._topic_root("demo-topic")

        self.assertEqual(runtime_root, topic_root / "runtime")
        self.assertTrue((topic_root / "topic_manifest.md").exists())
        self.assertTrue((topic_root / "L0").exists())
        self.assertTrue((topic_root / "L1").exists())
        self.assertTrue((topic_root / "L2").exists())
        self.assertTrue((topic_root / "L3" / "runs").exists())
        self.assertTrue((topic_root / "L4" / "runs").exists())
        self.assertTrue((topic_root / "consultation").exists())
        self.assertTrue((topic_root / "logs").exists())

    def test_runtime_projection_writers_emit_markdown_companions_inside_topic_runtime_root(self) -> None:
        topic_runtime_root = self.kernel_root / "topics" / "demo-topic" / "runtime"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)

        synopsis_payload = {
            "id": "topic_synopsis:demo-topic",
            "topic_slug": "demo-topic",
            "title": "Demo Topic",
            "question": "Which bounded route should remain active?",
            "lane": "formal_theory",
            "load_profile": "light",
            "status": "active",
            "human_request": "Continue this topic.",
            "assumptions": [],
            "l1_source_intake": {
                "source_count": 0,
                "assumption_rows": [],
                "regime_rows": [],
                "reading_depth_rows": [],
                "method_specificity_rows": [],
            },
            "runtime_focus": {
                "summary": "Keep the bounded theorem-facing route explicit.",
                "why_this_topic_is_here": "The theorem-facing route is still active.",
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "next_action_id": "action:demo-topic:01",
                "next_action_type": "proof_review",
                "next_action_summary": "Keep the bounded theorem-facing route explicit.",
                "human_need_status": "none",
                "human_need_kind": "none",
                "human_need_summary": "No active human checkpoint is blocking progress.",
                "blocker_summary": [],
                "last_evidence_kind": "none",
                "last_evidence_summary": "No evidence has returned yet.",
                "dependency_status": "clear",
                "dependency_summary": "No explicit dependency blocker is active.",
                "promotion_status": "not_requested",
                "momentum_status": "steady",
                "stuckness_status": "not_stuck",
                "surprise_status": "none",
                "judgment_summary": "Proceed with the current bounded route.",
            },
            "truth_sources": {
                "topic_state_path": "topics/demo-topic/runtime/topic_state.json",
                "research_question_contract_path": "topics/demo-topic/runtime/research_question.contract.json",
                "next_action_surface_path": "topics/demo-topic/runtime/action_queue.jsonl",
                "human_need_surface_path": "topics/demo-topic/runtime/operator_checkpoint.active.json",
                "dependency_registry_path": "topics/demo-topic/runtime/topic_state.json",
                "promotion_readiness_path": "topics/demo-topic/runtime/promotion_readiness.md",
                "promotion_gate_path": None,
            },
            "next_action_summary": "Keep the bounded theorem-facing route explicit.",
            "open_gap_summary": "No explicit gap is open.",
            "pending_decision_count": 1,
            "knowledge_packet_paths": [],
            "updated_at": "2026-04-14T12:00:00+08:00",
            "updated_by": "test",
        }
        pending_payload = {
            "topic_slug": "demo-topic",
            "decision_count": 1,
            "pending_decisions": [
                {
                    "id": "dp:demo-route-choice",
                    "question": "Which bounded route should run next?",
                }
            ],
        }

        synopsis_result = write_topic_synopsis(
            "demo-topic",
            synopsis_payload,
            kernel_root=self.kernel_root,
        )
        pending_result = write_pending_decisions_projection(
            "demo-topic",
            pending_payload,
            kernel_root=self.kernel_root,
        )

        self.assertEqual(
            Path(synopsis_result["path"]),
            topic_runtime_root / "topic_synopsis.json",
        )
        self.assertEqual(
            Path(pending_result["path"]),
            topic_runtime_root / "pending_decisions.json",
        )
        self.assertTrue((topic_runtime_root / "topic_synopsis.md").exists())
        self.assertTrue((topic_runtime_root / "pending_decisions.md").exists())

        synopsis_note = (topic_runtime_root / "topic_synopsis.md").read_text(encoding="utf-8")
        pending_note = (topic_runtime_root / "pending_decisions.md").read_text(encoding="utf-8")
        self.assertIn("artifact_kind: topic_synopsis", synopsis_note)
        self.assertIn("Keep the bounded theorem-facing route explicit.", synopsis_note)
        self.assertIn("artifact_kind: pending_decisions", pending_note)
        self.assertIn("Which bounded route should run next?", pending_note)

    def test_request_promotion_reads_legacy_runtime_and_feedback_layout(self) -> None:
        legacy_runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        legacy_feedback_run_root = (
            self.kernel_root / "feedback" / "topics" / "demo-topic" / "runs" / "run-001"
        )
        legacy_runtime_root.mkdir(parents=True, exist_ok=True)
        legacy_feedback_run_root.mkdir(parents=True, exist_ok=True)
        (legacy_runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "run-001",
                    "resume_stage": "L4",
                    "last_materialized_stage": "L4",
                    "research_mode": "formal_derivation",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (legacy_feedback_run_root / "candidate_ledger.jsonl").write_text(
            json.dumps(
                {
                    "candidate_id": "candidate:demo-candidate",
                    "candidate_type": "theorem_card",
                    "title": "Demo theorem candidate",
                    "summary": "A bounded theorem candidate ready for human L2 approval.",
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "origin_refs": [],
                    "question": "Can the bounded theorem be approved for L2?",
                    "assumptions": ["The submitted candidate still needs a narrower regime statement."],
                    "proposed_validation_route": "analytical",
                    "intended_l2_targets": ["theorem:demo-approved-result"],
                    "status": "ready_for_validation",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.request_promotion(
            topic_slug="demo-topic",
            candidate_id="candidate:demo-candidate",
            requested_by="test",
        )

        new_gate_path = self.kernel_root / "topics" / "demo-topic" / "runtime" / "promotion_gate.json"
        legacy_gate_path = self.kernel_root / "runtime" / "topics" / "demo-topic" / "promotion_gate.json"
        self.assertEqual(payload["status"], "pending_human_approval")
        self.assertTrue(new_gate_path.exists())
        self.assertTrue(legacy_gate_path.exists())

    def test_runtime_projection_writers_emit_legacy_runtime_compatibility_copies(self) -> None:
        topic_runtime_root = self.kernel_root / "topics" / "demo-topic" / "runtime"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)

        synopsis_payload = {
            "id": "topic_synopsis:demo-topic",
            "topic_slug": "demo-topic",
            "title": "Demo Topic",
            "question": "Which bounded route should remain active?",
            "lane": "formal_theory",
            "load_profile": "light",
            "status": "active",
            "human_request": "Continue this topic.",
            "assumptions": [],
            "l1_source_intake": {
                "source_count": 0,
                "assumption_rows": [],
                "regime_rows": [],
                "reading_depth_rows": [],
                "method_specificity_rows": [],
            },
            "runtime_focus": {
                "summary": "Keep the bounded theorem-facing route explicit.",
                "why_this_topic_is_here": "The theorem-facing route is still active.",
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "next_action_id": "action:demo-topic:01",
                "next_action_type": "proof_review",
                "next_action_summary": "Keep the bounded theorem-facing route explicit.",
                "human_need_status": "none",
                "human_need_kind": "none",
                "human_need_summary": "No active human checkpoint is blocking progress.",
                "blocker_summary": [],
                "last_evidence_kind": "none",
                "last_evidence_summary": "No evidence has returned yet.",
                "dependency_status": "clear",
                "dependency_summary": "No explicit dependency blocker is active.",
                "promotion_status": "not_requested",
                "momentum_status": "steady",
                "stuckness_status": "not_stuck",
                "surprise_status": "none",
                "judgment_summary": "Proceed with the current bounded route.",
            },
            "truth_sources": {
                "topic_state_path": "topics/demo-topic/runtime/topic_state.json",
                "research_question_contract_path": "topics/demo-topic/runtime/research_question.contract.json",
                "next_action_surface_path": "topics/demo-topic/runtime/action_queue.jsonl",
                "human_need_surface_path": "topics/demo-topic/runtime/operator_checkpoint.active.json",
                "dependency_registry_path": "topics/demo-topic/runtime/topic_state.json",
                "promotion_readiness_path": "topics/demo-topic/runtime/promotion_readiness.md",
                "promotion_gate_path": None,
            },
            "next_action_summary": "Keep the bounded theorem-facing route explicit.",
            "open_gap_summary": "No explicit gap is open.",
            "pending_decision_count": 1,
            "knowledge_packet_paths": [],
            "updated_at": "2026-04-14T12:00:00+08:00",
            "updated_by": "test",
        }
        pending_payload = {
            "topic_slug": "demo-topic",
            "decision_count": 1,
            "pending_decisions": [
                {
                    "id": "dp:demo-route-choice",
                    "question": "Which bounded route should run next?",
                }
            ],
        }

        write_topic_synopsis("demo-topic", synopsis_payload, kernel_root=self.kernel_root)
        write_pending_decisions_projection("demo-topic", pending_payload, kernel_root=self.kernel_root)

        legacy_runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        self.assertTrue((legacy_runtime_root / "topic_synopsis.json").exists())
        self.assertTrue((legacy_runtime_root / "topic_synopsis.md").exists())
        self.assertTrue((legacy_runtime_root / "pending_decisions.json").exists())
        self.assertTrue((legacy_runtime_root / "pending_decisions.md").exists())


if __name__ == "__main__":
    unittest.main()
