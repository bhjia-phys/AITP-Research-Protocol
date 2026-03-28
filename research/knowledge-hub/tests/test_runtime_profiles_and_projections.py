from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import AITPService  # noqa: E402
from knowledge_hub.runtime_projection_handler import (  # noqa: E402
    build_knowledge_packets_from_candidates,
    write_promotion_trace,
    write_topic_synopsis,
)


class RuntimeProfileProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.package_root = Path(__file__).resolve().parents[1]
        self.temp_root = Path(tempfile.mkdtemp(prefix="aitp-runtime-profiles-"))
        self.kernel_root = self.temp_root / "kernel"
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for name in (
            "topic-synopsis.schema.json",
            "knowledge-packet.schema.json",
            "promotion-trace.schema.json",
        ):
            source = self.package_root / "schemas" / name
            target = self.kernel_root / "schemas" / name
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        bundle_schema = self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        (self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").write_text(
            bundle_schema.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        for protocol_name in (
            "RESEARCH_EXECUTION_GUARDRAILS.md",
            "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md",
            "SECTION_FORMALIZATION_PROTOCOL.md",
        ):
            (self.kernel_root / protocol_name).write_text(f"# {protocol_name}\n", encoding="utf-8")

        self.runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L3",
                    "latest_run_id": "run-001",
                    "research_mode": "toy_model",
                    "pointers": {
                        "control_note_path": "runtime/topics/demo-topic/control_note.md"
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": "continue this topic",
                    "action_queue_surface": {},
                    "decision_surface": {},
                    "human_edit_surfaces": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "action_type": "benchmark",
                    "summary": "Run the smallest exact benchmark first.",
                    "status": "pending",
                    "auto_runnable": True,
                    "queue_source": "declared_contract",
                    "handler_args": {"run_id": "run-001"},
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "control_note.md").write_text("# Control note\n", encoding="utf-8")
        (self.runtime_root / "operator_console.md").write_text("# Operator Console\n", encoding="utf-8")

        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root)

    def _write_surface(self, relative_path: str, content: str) -> str:
        path = self.kernel_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _shell_surfaces(self) -> dict[str, object]:
        research_json = self._write_surface(
            "runtime/topics/demo-topic/research_question.contract.json",
            json.dumps({"question_id": "research_question:demo-topic"}, indent=2) + "\n",
        )
        research_note = self._write_surface(
            "runtime/topics/demo-topic/research_question.contract.md",
            "# Research question\n",
        )
        validation_json = self._write_surface(
            "runtime/topics/demo-topic/validation_contract.active.json",
            json.dumps({"validation_id": "validation:demo-topic:active"}, indent=2) + "\n",
        )
        validation_note = self._write_surface(
            "runtime/topics/demo-topic/validation_contract.active.md",
            "# Validation contract\n",
        )
        idea_json = self._write_surface(
            "runtime/topics/demo-topic/idea_packet.json",
            json.dumps({"topic_slug": "demo-topic"}, indent=2) + "\n",
        )
        idea_note = self._write_surface("runtime/topics/demo-topic/idea_packet.md", "# Idea packet\n")
        checkpoint_json = self._write_surface(
            "runtime/topics/demo-topic/operator_checkpoint.active.json",
            json.dumps({"checkpoint_id": "checkpoint:demo"}, indent=2) + "\n",
        )
        checkpoint_note = self._write_surface(
            "runtime/topics/demo-topic/operator_checkpoint.active.md",
            "# Operator checkpoint\n",
        )
        checkpoint_ledger = self._write_surface(
            "runtime/topics/demo-topic/operator_checkpoints.jsonl",
            "",
        )
        dashboard = self._write_surface("runtime/topics/demo-topic/topic_dashboard.md", "# Dashboard\n")
        readiness_note = self._write_surface("runtime/topics/demo-topic/promotion_readiness.md", "# Promotion readiness\n")
        gap_note = self._write_surface("runtime/topics/demo-topic/gap_map.md", "# Gap map\n")
        topic_completion_json = self._write_surface(
            "runtime/topics/demo-topic/topic_completion.json",
            json.dumps({"status": "in_progress"}, indent=2) + "\n",
        )
        topic_completion_note = self._write_surface("runtime/topics/demo-topic/topic_completion.md", "# Topic completion\n")
        lean_bridge_json = self._write_surface(
            "runtime/topics/demo-topic/lean_bridge.active.json",
            json.dumps({"status": "idle"}, indent=2) + "\n",
        )
        lean_bridge_note = self._write_surface("runtime/topics/demo-topic/lean_bridge.active.md", "# Lean bridge\n")
        followup_reintegration_jsonl = self._write_surface("runtime/topics/demo-topic/followup_reintegration.jsonl", "")
        followup_reintegration_note = self._write_surface("runtime/topics/demo-topic/followup_reintegration.md", "# Follow-up reintegration\n")
        followup_gap_writeback_jsonl = self._write_surface("runtime/topics/demo-topic/followup_gap_writeback.jsonl", "")
        followup_gap_writeback_note = self._write_surface("runtime/topics/demo-topic/followup_gap_writeback.md", "# Follow-up gap writeback\n")

        return {
            "research_question_contract_path": research_json,
            "research_question_contract_note_path": research_note,
            "validation_contract_path": validation_json,
            "validation_contract_note_path": validation_note,
            "idea_packet_path": idea_json,
            "idea_packet_note_path": idea_note,
            "operator_checkpoint_path": checkpoint_json,
            "operator_checkpoint_note_path": checkpoint_note,
            "operator_checkpoint_ledger_path": checkpoint_ledger,
            "topic_dashboard_path": dashboard,
            "promotion_readiness_path": readiness_note,
            "gap_map_path": gap_note,
            "topic_completion_path": topic_completion_json,
            "topic_completion_note_path": topic_completion_note,
            "lean_bridge_path": lean_bridge_json,
            "lean_bridge_note_path": lean_bridge_note,
            "followup_reintegration_path": followup_reintegration_jsonl,
            "followup_reintegration_note_path": followup_reintegration_note,
            "followup_gap_writeback_path": followup_gap_writeback_jsonl,
            "followup_gap_writeback_note_path": followup_gap_writeback_note,
            "research_question_contract": {
                "question_id": "research_question:demo-topic",
                "title": "Demo Topic",
                "status": "active",
                "template_mode": "toy_numeric",
                "research_mode": "toy_model",
                "target_layers": ["L1", "L3", "L4", "L2"],
                "question": "What is the first honest benchmark route?",
                "assumptions": ["Benchmark before target-model inference."],
            },
            "validation_contract": {
                "validation_mode": "numerical",
            },
            "idea_packet": {
                "topic_slug": "demo-topic",
                "status": "approved_for_execution",
                "status_reason": "The bounded question is specific enough to execute.",
                "initial_idea": "Study the first exact benchmark lane.",
                "novelty_target": "Clarify the first reusable benchmark surface.",
                "non_goals": [],
                "first_validation_route": "small-system exact benchmark",
                "initial_evidence_bar": "Match the exact benchmark before larger-system inference.",
                "missing_fields": [],
                "clarification_questions": [],
                "execution_context_signals": [],
                "note_path": "runtime/topics/demo-topic/idea_packet.md",
                "updated_at": "2026-03-28T00:00:00+00:00",
                "updated_by": "test",
            },
            "operator_checkpoint": {
                "checkpoint_id": "checkpoint:demo",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "checkpoint_kind": None,
                "status": "answered",
                "active": False,
                "trigger_fingerprint": "",
                "question": "none",
                "required_response": "none",
                "response_channels": [],
                "blocker_summary": [],
                "evidence_refs": [],
                "selected_action_id": "action:demo-topic:01",
                "selected_action_summary": "Run the smallest exact benchmark first.",
                "answer": None,
                "requested_at": None,
                "requested_by": None,
                "answered_at": None,
                "answered_by": None,
                "note_path": "runtime/topics/demo-topic/operator_checkpoint.active.md",
                "ledger_path": "runtime/topics/demo-topic/operator_checkpoints.jsonl",
                "updated_at": "2026-03-28T00:00:00+00:00",
                "updated_by": "test",
            },
            "topic_state_explainability": {},
            "promotion_readiness": {
                "status": "not_ready",
                "gate_status": "not_requested",
                "ready_candidate_ids": [],
                "blockers": ["Benchmark not yet executed."],
                "blocker_count": 1,
                "summary": "The topic is not ready for promotion yet.",
            },
            "open_gap_summary": {
                "status": "open",
                "gap_count": 1,
                "blockers": ["Benchmark route not yet executed."],
                "followup_gap_ids": [],
                "followup_gap_writeback_count": 0,
                "followup_gap_writeback_child_topics": [],
                "pending_action_summaries": ["Run the smallest exact benchmark first."],
                "requires_l0_return": False,
                "capability_gap_active": False,
                "summary": "The benchmark route is still pending.",
            },
            "topic_completion": {
                "regression_manifest": {
                    "status": "empty",
                    "candidate_ids": [],
                    "regression_question_ids": [],
                    "oracle_ids": [],
                    "regression_run_ids": [],
                    "candidate_count": 0,
                    "question_count": 0,
                    "oracle_count": 0,
                    "run_count": 0,
                },
                "completion_gate_checks": [],
                "status": "in_progress",
                "summary": "Topic completion is not ready yet.",
                "promotion_ready_candidate_ids": [],
                "path": "runtime/topics/demo-topic/topic_completion.md",
            },
            "lean_bridge": {
                "status": "idle",
                "summary": "No Lean bridge packet is active.",
                "packet_count": 0,
                "ready_packet_count": 0,
                "needs_refinement_count": 0,
                "packets": [],
                "path": "runtime/topics/demo-topic/lean_bridge.active.md",
                "updated_at": "2026-03-28T00:00:00+00:00",
                "updated_by": "test",
            },
        }

    def test_new_projection_schemas_validate_and_are_mirrored(self) -> None:
        for name in ("topic-synopsis", "knowledge-packet", "promotion-trace"):
            public_path = self.repo_root / "schemas" / f"{name}.schema.json"
            kernel_path = self.package_root / "schemas" / f"{name}.schema.json"
            public_payload = json.loads(public_path.read_text(encoding="utf-8"))
            kernel_payload = json.loads(kernel_path.read_text(encoding="utf-8"))
            jsonschema.Draft7Validator.check_schema(public_payload)
            self.assertEqual(public_payload, kernel_payload)

    def test_projection_helpers_write_valid_outputs(self) -> None:
        synopsis = {
            "id": "topic_synopsis:demo-topic",
            "topic_slug": "demo-topic",
            "title": "Demo Topic",
            "question": "What is the first honest benchmark route?",
            "lane": "toy_numeric",
            "load_profile": "light",
            "status": "active",
            "human_request": "continue this topic",
            "assumptions": ["Benchmark first."],
            "next_action_summary": "Run the smallest exact benchmark first.",
            "open_gap_summary": "The benchmark route is still pending.",
            "pending_decision_count": 0,
            "knowledge_packet_paths": [],
            "updated_at": "2026-03-28T00:00:00+00:00",
            "updated_by": "test",
        }
        topic_synopsis_result = write_topic_synopsis("demo-topic", synopsis, kernel_root=self.kernel_root)
        self.assertTrue(Path(topic_synopsis_result["path"]).exists())

        packet_rows = build_knowledge_packets_from_candidates(
            "demo-topic",
            [
                {
                    "candidate_id": "candidate:demo-benchmark-packet",
                    "candidate_type": "method",
                    "title": "Demo Benchmark Packet",
                    "summary": "Small exact benchmark route for the topic.",
                    "status": "ready_for_validation",
                    "origin_refs": [],
                    "intended_l2_targets": ["workflow:demo-benchmark"],
                }
            ],
            lane="toy_numeric",
            updated_at="2026-03-28T00:00:00+00:00",
            updated_by="test",
            kernel_root=self.kernel_root,
        )
        self.assertEqual(len(packet_rows), 1)
        self.assertTrue(Path(packet_rows[0]["path"]).exists())

        promotion_trace = {
            "id": "promotion_trace:demo-topic",
            "topic_slug": "demo-topic",
            "trace_scope": "topic_latest",
            "status": "not_ready",
            "gate_status": "not_requested",
            "human_gate_status": "not_requested",
            "summary": "Promotion is still blocked by the missing benchmark result.",
            "candidate_refs": ["candidate:demo-benchmark-packet"],
            "packet_refs": [packet_rows[0]["path"]],
            "decision_trace_refs": [],
            "audit_refs": ["runtime/topics/demo-topic/topic_completion.md"],
            "backend_target": {
                "backend_id": "",
                "target_backend_root": "",
                "canonical_layer": "L2",
            },
            "updated_at": "2026-03-28T00:00:00+00:00",
            "updated_by": "test",
        }
        promotion_trace_result = write_promotion_trace("demo-topic", promotion_trace, kernel_root=self.kernel_root)
        self.assertTrue(Path(promotion_trace_result["path"]).exists())

    def test_resolve_load_profile_uses_light_by_default_and_full_for_escalation_requests(self) -> None:
        light, light_reason = self.service._resolve_load_profile(
            explicit_load_profile=None,
            human_request="continue this topic and tighten the benchmark plan",
            topic_state={},
        )
        full, full_reason = self.service._resolve_load_profile(
            explicit_load_profile=None,
            human_request="benchmark mismatch, promotion review, and full audit",
            topic_state={},
        )
        self.assertEqual(light, "light")
        self.assertEqual(light_reason, "auto_light_for_ordinary_topic_work")
        self.assertEqual(full, "full")
        self.assertEqual(full_reason, "auto_escalation_from_request")

    def test_runtime_bundle_uses_light_profile_and_writes_projections(self) -> None:
        shell_surfaces = self._shell_surfaces()
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(
                self.service,
                "_candidate_rows_for_run",
                return_value=[
                    {
                        "candidate_id": "candidate:demo-benchmark-packet",
                        "candidate_type": "method",
                        "title": "Demo Benchmark Packet",
                        "summary": "Small exact benchmark route for the topic.",
                        "status": "ready_for_validation",
                        "origin_refs": [],
                        "intended_l2_targets": ["workflow:demo-benchmark"],
                    }
                ],
            ):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue this topic and keep the benchmark lane bounded",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["load_profile"], "light")
        self.assertEqual(len(bundle["must_read_now"]), 4)
        self.assertEqual(bundle["must_read_now"][0]["path"], "runtime/topics/demo-topic/topic_state.json")
        self.assertIn("topic_synopsis", bundle)
        self.assertIn("pending_decisions", bundle)
        self.assertTrue((self.runtime_root / "topic_synopsis.json").exists())
        self.assertTrue((self.runtime_root / "pending_decisions.json").exists())
        self.assertTrue((self.runtime_root / "promotion_readiness.json").exists())
        self.assertTrue((self.runtime_root / "promotion_trace.latest.json").exists())
        self.assertTrue((self.runtime_root / "knowledge_packets").exists())

        schema = json.loads(
            (self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.validate(bundle, schema)

    def test_runtime_bundle_auto_escalates_to_full_for_mismatch_requests(self) -> None:
        shell_surfaces = self._shell_surfaces()
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="benchmark mismatch and promotion audit",
                    load_profile=None,
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["load_profile"], "full")
        self.assertGreater(len(bundle["must_read_now"]), 4)
        self.assertIn("topic_dashboard.md", json.dumps(bundle["must_read_now"]))


if __name__ == "__main__":
    unittest.main()
