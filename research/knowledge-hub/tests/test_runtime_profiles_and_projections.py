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

from tests_support import (  # noqa: E402
    copy_kernel_schema_files,
    copy_runtime_schema_files,
    make_temp_kernel,
    write_protocol_placeholders,
)
from knowledge_hub.aitp_service import AITPService  # noqa: E402
from knowledge_hub.mode_envelope_support import build_runtime_mode_contract, filter_escalation_triggers_for_mode  # noqa: E402
from knowledge_hub.runtime_projection_handler import (  # noqa: E402
    append_transition_history,
    build_knowledge_packets_from_candidates,
    load_transition_history,
    write_promotion_trace,
    write_topic_skill_projection,
    write_topic_synopsis,
)


class RuntimeProfileProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.package_root = Path(__file__).resolve().parents[1]
        self.fixture = make_temp_kernel("aitp-runtime-profiles-")
        self.kernel_root = self.fixture.kernel_root
        copy_kernel_schema_files(
            self.package_root,
            self.kernel_root,
            "topic-synopsis.schema.json",
            "knowledge-packet.schema.json",
            "promotion-trace.schema.json",
            "topic-skill-projection.schema.json",
        )
        copy_runtime_schema_files(
            self.package_root,
            self.kernel_root,
            "progressive-disclosure-runtime-bundle.schema.json",
        )
        write_protocol_placeholders(
            self.kernel_root,
            "RESEARCH_EXECUTION_GUARDRAILS.md",
            "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md",
            "SECTION_FORMALIZATION_PROTOCOL.md",
        )

        self.runtime_root = self.kernel_root / "runtime" / "topics" / "demo-topic"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
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
        self.fixture.cleanup()

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
        review_bundle_json = self._write_surface(
            "runtime/topics/demo-topic/validation_review_bundle.active.json",
            json.dumps({"bundle_kind": "validation_review_bundle", "status": "not_materialized"}, indent=2) + "\n",
        )
        review_bundle_note = self._write_surface(
            "runtime/topics/demo-topic/validation_review_bundle.active.md",
            "# Validation review bundle\n",
        )
        gap_note = self._write_surface("runtime/topics/demo-topic/gap_map.md", "# Gap map\n")
        topic_completion_json = self._write_surface(
            "runtime/topics/demo-topic/topic_completion.json",
            json.dumps({"status": "in_progress"}, indent=2) + "\n",
        )
        topic_completion_note = self._write_surface("runtime/topics/demo-topic/topic_completion.md", "# Topic completion\n")
        statement_compilation_json = self._write_surface(
            "runtime/topics/demo-topic/statement_compilation.active.json",
            json.dumps({"status": "idle"}, indent=2) + "\n",
        )
        statement_compilation_note = self._write_surface(
            "runtime/topics/demo-topic/statement_compilation.active.md",
            "# Statement compilation\n",
        )
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
            "validation_review_bundle_path": review_bundle_json,
            "validation_review_bundle_note_path": review_bundle_note,
            "gap_map_path": gap_note,
            "topic_completion_path": topic_completion_json,
            "topic_completion_note_path": topic_completion_note,
            "statement_compilation_path": statement_compilation_json,
            "statement_compilation_note_path": statement_compilation_note,
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
            "validation_review_bundle": {
                "bundle_kind": "validation_review_bundle",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "status": "not_materialized",
                "primary_review_kind": "validation_contract",
                "candidate_ids": [],
                "validation_mode": "numerical",
                "promotion_readiness_status": "not_ready",
                "topic_completion_status": "in_progress",
                "promotion_gate_status": "not_requested",
                "blockers": ["Benchmark not yet executed."],
                "entrypoints": {
                    "validation_contract_path": "runtime/topics/demo-topic/validation_contract.active.json",
                    "validation_contract_note_path": "runtime/topics/demo-topic/validation_contract.active.md",
                    "promotion_readiness_path": "runtime/topics/demo-topic/promotion_readiness.json",
                    "promotion_readiness_note_path": "runtime/topics/demo-topic/promotion_readiness.md",
                    "topic_completion_path": "runtime/topics/demo-topic/topic_completion.json",
                    "topic_completion_note_path": "runtime/topics/demo-topic/topic_completion.md",
                    "gap_map_path": "runtime/topics/demo-topic/gap_map.md",
                    "promotion_gate_path": None,
                },
                "specialist_artifacts": [],
                "summary": "Primary L4 review surface for topic `demo-topic` using `validation_contract` as the current review entry point. No specialist review artifacts are materialized for the active run yet.",
                "updated_at": "2026-03-28T00:00:00+00:00",
                "updated_by": "test",
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
            "statement_compilation": {
                "status": "idle",
                "summary": "No statement-compilation packet is active.",
                "packet_count": 0,
                "ready_packet_count": 0,
                "needs_repair_count": 0,
                "packets": [],
                "path": "runtime/topics/demo-topic/statement_compilation.active.md",
                "updated_at": "2026-03-28T00:00:00+00:00",
                "updated_by": "test",
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

    def _rewrite_action_queue(self, action_type: str, summary: str, *, handler_args: dict[str, object] | None = None) -> None:
        (self.runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:01",
                    "action_type": action_type,
                    "summary": summary,
                    "status": "pending",
                    "auto_runnable": True,
                    "queue_source": "declared_contract",
                    "handler_args": handler_args or {"run_id": "run-001"},
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

    def _rewrite_interaction_state(self, payload: dict[str, object]) -> None:
        (self.runtime_root / "interaction_state.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def _must_read_paths(self, bundle: dict[str, object]) -> list[str]:
        return [str(row["path"]) for row in bundle["must_read_now"]]

    def _deferred_paths(self, bundle: dict[str, object]) -> list[str]:
        return [str(row["path"]) for row in bundle["may_defer_until_trigger"]]

    def _write_loop_retry_events(
        self,
        *,
        candidate_id: str = "candidate:demo-theorem",
        attempts: int = 3,
    ) -> None:
        metrics_path = self.runtime_root / "theory_operations.jsonl"
        rows: list[dict[str, object]] = []
        for attempt_index in range(2, attempts + 1):
            rows.append(
                {
                    "schema_version": 1,
                    "event_id": f"event:loop-retry:{attempt_index}",
                    "topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "operation_kind": "derivation_retry",
                    "status": "active",
                    "candidate_id": candidate_id,
                    "candidate_type": "theorem_card",
                    "phase": "",
                    "summary": f"Repeated blocked theorem-facing attempt {attempt_index}.",
                    "blocker_tags": [
                        "prerequisite_closure_incomplete",
                        "formalization_blockers_present",
                        "retry_source:formal_theory_audit",
                    ],
                    "source_paths": [
                        "validation/topics/demo-topic/runs/run-001/theory-packets/candidate-demo-theorem/formal_theory_review.json"
                    ],
                    "metric_values": {
                        "attempt_index": attempt_index,
                        "source_operation_kind": "formal_theory_audit",
                    },
                    "recorded_at": f"2026-04-13T10:0{attempt_index}:00+08:00",
                    "recorded_by": "test",
                }
            )
        metrics_path.write_text(
            "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )

    def _write_theory_packet_artifacts(self, *, candidate_id: str = "candidate:demo-theorem") -> dict[str, str]:
        packet_root = (
            self.kernel_root
            / "topics"
            / "demo-topic"
            / "L4"
            / "runs"
            / "run-001"
            / "theory-packets"
            / "candidate-demo-theorem"
        )
        packet_root.mkdir(parents=True, exist_ok=True)
        notation_table = packet_root / "notation_table.json"
        notation_table.write_text(
            json.dumps(
                {
                    "candidate_id": candidate_id,
                    "status": "captured",
                    "bindings": [
                        {"symbol": "H", "meaning": "Hamiltonian"},
                        {"symbol": "Z", "meaning": "Center"},
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        prerequisite_review = packet_root / "prerequisite_closure_review.json"
        prerequisite_review.write_text(
            json.dumps(
                {
                    "candidate_id": candidate_id,
                    "status": "closed",
                    "lean_prerequisite_ids": ["lemma:demo-prereq"],
                    "blocking_reasons": [],
                    "notes": "Prerequisites are closed for the bounded theorem packet.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        formal_review = packet_root / "formal_theory_review.json"
        formal_review.write_text(
            json.dumps(
                {
                    "candidate_id": candidate_id,
                    "overall_status": "ready",
                    "prerequisite_closure_status": "closed",
                    "lean_prerequisite_ids": ["lemma:demo-prereq"],
                    "formalization_blockers": [],
                    "prerequisite_notes": "Bounded theorem packet is prerequisite-closed.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "notation_table": str(notation_table),
            "prerequisite_closure_review": str(prerequisite_review),
            "formal_theory_review": str(formal_review),
        }

    def test_new_projection_schemas_validate_and_are_mirrored(self) -> None:
        for name in ("topic-synopsis", "knowledge-packet", "promotion-trace", "topic-skill-projection"):
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
            "l1_source_intake": {
                "source_count": 1,
                "assumption_rows": [
                    {
                        "source_id": "paper:demo-source",
                        "source_title": "Demo Source",
                        "source_type": "paper",
                        "assumption": "Benchmark first.",
                        "reading_depth": "abstract_only",
                        "evidence_excerpt": "Benchmark first.",
                    }
                ],
                "regime_rows": [
                    {
                        "source_id": "paper:demo-source",
                        "source_title": "Demo Source",
                        "source_type": "paper",
                        "regime": "weak coupling",
                        "reading_depth": "abstract_only",
                        "evidence_excerpt": "weak coupling",
                    }
                ],
                "reading_depth_rows": [
                    {
                        "source_id": "paper:demo-source",
                        "source_title": "Demo Source",
                        "source_type": "paper",
                        "reading_depth": "abstract_only",
                        "basis": "metadata_link",
                    }
                ],
                "method_specificity_rows": [
                    {
                        "source_id": "paper:demo-source",
                        "source_title": "Demo Source",
                        "source_type": "paper",
                        "method_family": "numerical_benchmark",
                        "specificity_tier": "high",
                        "reading_depth": "abstract_only",
                        "evidence_excerpt": "Benchmark first.",
                    }
                ],
            },
            "runtime_focus": {
                "summary": "Stage `L3`; next `Run the smallest exact benchmark first.`; human need `none`; last evidence `none`.",
                "why_this_topic_is_here": "The topic is currently following the bounded benchmark route.",
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "next_action_id": "action:demo-topic:01",
                "next_action_type": "run_benchmark",
                "next_action_summary": "Run the smallest exact benchmark first.",
                "human_need_status": "none",
                "human_need_kind": "none",
                "human_need_summary": "No active human checkpoint is currently blocking the bounded loop.",
                "blocker_summary": [],
                "last_evidence_kind": "none",
                "last_evidence_summary": "No durable evidence-return artifact is currently recorded for this topic.",
                "dependency_status": "clear",
                "dependency_summary": "No active topic dependencies.",
                "promotion_status": "not_ready",
                "momentum_status": "queued",
                "stuckness_status": "none",
                "surprise_status": "none",
                "judgment_summary": "Momentum `queued`; stuckness `none`; surprise `none`.",
            },
            "truth_sources": {
                "topic_state_path": "runtime/topics/demo-topic/topic_state.json",
                "research_question_contract_path": "runtime/topics/demo-topic/research_question.contract.json",
                "next_action_surface_path": "runtime/topics/demo-topic/action_queue.jsonl",
                "human_need_surface_path": None,
                "dependency_registry_path": "runtime/active_topics.json",
                "promotion_readiness_path": "runtime/topics/demo-topic/promotion_readiness.json",
                "promotion_gate_path": None,
            },
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

        topic_skill_projection = {
            "id": "topic_skill_projection:demo-topic",
            "topic_slug": "demo-topic",
            "source_topic_slug": "demo-topic",
            "run_id": "run-001",
            "title": "Demo Topic Skill Projection",
            "summary": "Reusable execution projection for the bounded benchmark-first route.",
            "lane": "toy_numeric",
            "status": "available",
            "status_reason": "Ready because the benchmark lane is stable enough to reuse.",
            "candidate_id": "candidate:topic-skill-projection-demo-topic",
            "intended_l2_target": "topic_skill_projection:demo-topic",
            "entry_signals": ["lane=toy_numeric"],
            "required_first_reads": ["runtime/topics/demo-topic/research_question.contract.md"],
            "required_first_routes": ["Close the exact benchmark before broader inference."],
            "benchmark_first_rules": ["Reproduce the small exact benchmark before route reuse."],
            "operator_checkpoint_rules": ["Raise an operator checkpoint on benchmark mismatch."],
            "operation_trust_requirements": ["Trust audit must pass before reuse."],
            "strategy_guidance": ["Reuse the benchmark-first route."],
            "forbidden_proxies": ["Do not treat prose-only confidence as benchmark closure."],
            "derived_from_artifacts": ["validation/topics/demo-topic/runs/run-001/trust_audit.json"],
            "updated_at": "2026-03-28T00:00:00+00:00",
            "updated_by": "test",
        }
        projection_result = write_topic_skill_projection(
            "demo-topic",
            topic_skill_projection,
            kernel_root=self.kernel_root,
        )
        self.assertTrue(Path(projection_result["path"]).exists())

        transition_result = append_transition_history(
            "demo-topic",
            {
                "run_id": "run-001",
                "event_kind": "runtime_resume_state",
                "from_layer": "L4",
                "to_layer": "L3",
                "reason": "Validation returned the topic to L3 after a bounded contradiction.",
                "evidence_refs": ["runtime/topics/demo-topic/gap_map.md"],
                "recorded_at": "2026-03-28T00:00:00+00:00",
                "recorded_by": "test",
            },
            kernel_root=self.kernel_root,
        )
        self.assertTrue(Path(transition_result["log_path"]).exists())
        self.assertTrue(Path(transition_result["path"]).exists())
        self.assertTrue(Path(transition_result["note_path"]).exists())
        transition_payload = load_transition_history("demo-topic", kernel_root=self.kernel_root)
        self.assertEqual(transition_payload["transition_count"], 1)
        self.assertEqual(transition_payload["backtrack_count"], 1)
        self.assertEqual(transition_payload["latest_demotion"]["to_layer"], "L3")

    def test_topic_skill_projection_schema_accepts_formal_theory_payload(self) -> None:
        schema = json.loads(
            (self.kernel_root / "schemas" / "topic-skill-projection.schema.json").read_text(encoding="utf-8")
        )
        payload = {
            "id": "topic_skill_projection:formal-demo",
            "topic_slug": "formal-demo",
            "source_topic_slug": "formal-demo",
            "run_id": "run-formal-001",
            "title": "Formal Demo Topic Skill Projection",
            "summary": "Reusable execution projection for a bounded formal-theory seed.",
            "lane": "formal_theory",
            "status": "blocked",
            "status_reason": "Projection is blocked until a ready formal_theory_review.json and promotion-ready topic_completion state exist for the active run.",
            "candidate_id": None,
            "intended_l2_target": None,
            "entry_signals": ["lane=formal_theory", "formal_theory_review=missing"],
            "required_first_reads": [
                "validation/topics/formal-demo/runs/run-formal-001/theory-packets/candidate-demo/formal_theory_review.json"
            ],
            "required_first_routes": [
                "Read the reviewed theorem-facing packet before reusing the bounded formal-theory route."
            ],
            "benchmark_first_rules": [
                "Do not reuse the route until theorem-facing trust artifacts are ready."
            ],
            "operator_checkpoint_rules": [
                "Require explicit human approval before promoting a formal-theory topic-skill projection."
            ],
            "operation_trust_requirements": [
                "formal_theory_review.json must report overall_status=ready before route reuse."
            ],
            "strategy_guidance": [
                "Treat the projection as execution memory, not theorem certification."
            ],
            "forbidden_proxies": [
                "Do not treat the projection itself as a theorem certificate or proof-complete artifact."
            ],
            "derived_from_artifacts": [
                "runtime/topics/formal-demo/topic_completion.json",
                "feedback/topics/formal-demo/runs/run-formal-001/strategy_memory.jsonl"
            ],
            "updated_at": "2026-04-01T00:00:00+00:00",
            "updated_by": "test",
        }
        jsonschema.validate(payload, schema)

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
        self.assertEqual(bundle["runtime_mode"], "explore")
        self.assertIsNone(bundle["active_submode"])
        self.assertEqual(bundle["mode_envelope"]["mode"], "explore")
        self.assertEqual(bundle["mode_envelope"]["load_profile"], "light")
        self.assertIn("control_plane", bundle)
        self.assertEqual(bundle["control_plane"]["task_type"], "open_exploration")
        self.assertEqual(bundle["control_plane"]["lane"], bundle["topic_synopsis"]["lane"])
        self.assertEqual(bundle["control_plane"]["layer"], "L3")
        self.assertEqual(bundle["control_plane"]["mode"], bundle["runtime_mode"])
        self.assertEqual(
            bundle["control_plane"]["transition"]["transition_kind"],
            bundle["transition_posture"]["transition_kind"],
        )
        self.assertEqual(bundle["control_plane"]["h_plane"]["checkpoint_status"], "answered")
        self.assertEqual(bundle["mode_envelope"]["minimum_mandatory_context"][0]["path"], "runtime/topics/demo-topic/topic_dashboard.md")
        self.assertIn("L3 -> L0", bundle["mode_envelope"]["allowed_backedges"])
        self.assertEqual(bundle["transition_posture"]["transition_kind"], "boundary_hold")
        self.assertEqual(len(bundle["must_read_now"]), 3)
        self.assertEqual(bundle["must_read_now"][0]["path"], "runtime/topics/demo-topic/topic_dashboard.md")
        self.assertEqual(bundle["must_read_now"][1]["path"], "runtime/topics/demo-topic/research_question.contract.md")
        self.assertEqual(bundle["must_read_now"][2]["path"], "topics/demo-topic/runtime/graph_analysis.md")
        self.assertEqual(bundle["minimal_execution_brief"]["open_next"], "runtime/topics/demo-topic/topic_dashboard.md")
        self.assertNotIn("operator_console.md", json.dumps(bundle["must_read_now"]))
        self.assertTrue(
            any(
                row["path"] == "topics/demo-topic/runtime/control_note.md"
                and row["trigger"] == "decision_override_present"
                for row in bundle["may_defer_until_trigger"]
            )
        )
        self.assertTrue(
            any(
                row["path"] == "topics/demo-topic/runtime/topic_synopsis.json"
                and row["trigger"] == "runtime_truth_audit"
                for row in bundle["may_defer_until_trigger"]
            )
        )
        self.assertIn("topic_synopsis", bundle)
        self.assertIn("runtime_focus", bundle["topic_synopsis"])
        self.assertIn("truth_sources", bundle["topic_synopsis"])
        self.assertEqual(
            bundle["minimal_execution_brief"]["selected_action_summary"],
            bundle["topic_synopsis"]["runtime_focus"]["next_action_summary"],
        )
        self.assertEqual(
            bundle["topic_synopsis"]["truth_sources"]["next_action_surface_path"],
            "topics/demo-topic/runtime/action_queue.jsonl",
        )
        self.assertTrue(any(row["trigger"] == "runtime_truth_audit" for row in bundle["escalation_triggers"]))
        self.assertIn("pending_decisions", bundle)
        self.assertTrue((self.runtime_root / "topic_synopsis.json").exists())
        self.assertTrue((self.runtime_root / "pending_decisions.json").exists())
        self.assertTrue((self.runtime_root / "promotion_readiness.json").exists())
        self.assertTrue((self.runtime_root / "promotion_trace.latest.json").exists())
        self.assertTrue((self.runtime_root / "transition_history.json").exists())
        self.assertTrue((self.runtime_root / "transition_history.md").exists())
        self.assertTrue((self.runtime_root / "knowledge_packets").exists())
        note_text = Path(result["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Transition history", note_text)
        self.assertIn("transition_history.json", note_text)

        schema = json.loads(
            (self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.validate(bundle, schema)

    def test_runtime_bundle_projects_l1_source_intake_into_contract_and_synopsis(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["research_question_contract"]["l1_source_intake"] = {
            "source_count": 1,
            "assumption_rows": [
                {
                    "source_id": "paper:demo-source",
                    "source_title": "Demo Source",
                    "source_type": "paper",
                    "assumption": "Benchmark first.",
                    "reading_depth": "abstract_only",
                    "evidence_excerpt": "Benchmark first.",
                }
            ],
            "regime_rows": [
                {
                    "source_id": "paper:demo-source",
                    "source_title": "Demo Source",
                    "source_type": "paper",
                    "regime": "weak coupling",
                    "reading_depth": "abstract_only",
                    "evidence_excerpt": "weak coupling",
                }
            ],
            "reading_depth_rows": [
                {
                    "source_id": "paper:demo-source",
                    "source_title": "Demo Source",
                    "source_type": "paper",
                    "reading_depth": "abstract_only",
                    "basis": "metadata_link",
                }
            ],
            "method_specificity_rows": [
                {
                    "source_id": "paper:demo-source",
                    "source_title": "Demo Source",
                    "source_type": "paper",
                    "method_family": "numerical_benchmark",
                    "specificity_tier": "high",
                    "reading_depth": "abstract_only",
                    "evidence_excerpt": "Exact benchmark workflow.",
                }
            ],
        }
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue this topic and keep the benchmark lane bounded",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(
            bundle["active_research_contract"]["l1_source_intake"]["assumption_rows"][0]["assumption"],
            "Benchmark first.",
        )
        self.assertEqual(
            bundle["topic_synopsis"]["l1_source_intake"]["reading_depth_rows"][0]["reading_depth"],
            "abstract_only",
        )
        self.assertEqual(
            bundle["active_research_contract"]["l1_source_intake"]["method_specificity_rows"][0]["method_family"],
            "numerical_benchmark",
        )
        note_text = Path(result["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## L1 source intake", note_text)
        self.assertIn("## Source-backed regimes", note_text)
        self.assertIn("## Method specificity", note_text)

    def test_runtime_bundle_projects_source_intelligence_into_read_path(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["source_intelligence_path"] = self._write_surface(
            "runtime/topics/demo-topic/source_intelligence.json",
            json.dumps({"topic_slug": "demo-topic"}, indent=2) + "\n",
        )
        shell_surfaces["source_intelligence_note_path"] = self._write_surface(
            "runtime/topics/demo-topic/source_intelligence.md",
            "# Source intelligence\n",
        )
        shell_surfaces["source_intelligence"] = {
            "topic_slug": "demo-topic",
            "summary": "1 canonical source id, 1 citation edge, 1 neighbor signal, 1 cross-topic match.",
            "canonical_source_ids": ["source_identity:doi:10-1000-demo"],
            "cross_topic_match_count": 1,
            "fidelity_rows": [
                {
                    "source_id": "paper:demo-source",
                    "canonical_source_id": "source_identity:doi:10-1000-demo",
                    "source_type": "paper",
                    "fidelity_tier": "peer_reviewed",
                    "fidelity_basis": "canonical_doi_identity",
                }
            ],
            "fidelity_summary": {
                "source_count": 1,
                "counts_by_tier": {"peer_reviewed": 1},
                "strongest_tier": "peer_reviewed",
                "weakest_tier": "peer_reviewed",
            },
            "citation_edges": [
                {
                    "source_id": "paper:demo-source",
                    "target_ref": "doi:10-1000/shared",
                    "target_source_id": None,
                    "relation": "cites",
                }
            ],
            "source_neighbors": [
                {
                    "source_id": "paper:demo-source",
                    "neighbor_source_id": "paper:neighbor-source",
                    "neighbor_topic_slug": "neighbor-topic",
                    "neighbor_canonical_source_id": "source_identity:doi:10-1000-neighbor",
                    "relation_kind": "shared_reference",
                    "shared_reference_count": 1,
                    "shared_term_count": 2,
                    "cross_topic": True,
                }
            ],
            "neighbor_signal_count": 1,
            "path": "runtime/topics/demo-topic/source_intelligence.json",
            "note_path": "runtime/topics/demo-topic/source_intelligence.md",
        }
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue this topic and inspect the source intelligence",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["source_intelligence"]["canonical_source_ids"][0], "source_identity:doi:10-1000-demo")
        self.assertEqual(bundle["source_intelligence"]["cross_topic_match_count"], 1)
        self.assertEqual(bundle["source_intelligence"]["source_neighbors"][0]["relation_kind"], "shared_reference")
        self.assertEqual(bundle["source_intelligence"]["fidelity_summary"]["strongest_tier"], "peer_reviewed")
        note_text = Path(result["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Source intelligence", note_text)
        self.assertIn("## Source fidelity", note_text)
        self.assertIn("shared_reference", note_text)

    def test_runtime_bundle_projects_graph_analysis_into_read_path(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["graph_analysis_path"] = self._write_surface(
            "runtime/topics/demo-topic/graph_analysis.json",
            json.dumps({"topic_slug": "demo-topic"}, indent=2) + "\n",
        )
        shell_surfaces["graph_analysis_note_path"] = self._write_surface(
            "runtime/topics/demo-topic/graph_analysis.md",
            "# Graph analysis\n",
        )
        shell_surfaces["graph_analysis_history_path"] = self._write_surface(
            "runtime/topics/demo-topic/graph_analysis_history.jsonl",
            "",
        )
        shell_surfaces["graph_analysis"] = {
            "topic_slug": "demo-topic",
            "summary": {
                "connection_count": 1,
                "question_count": 1,
                "history_length": 2,
            },
            "connections": [
                {
                    "kind": "shared_foundation_bridge",
                    "bridge_label": "Anyon condensation",
                    "source_ids": ["paper:anyon-condensation", "note:operator-algebra"],
                    "source_titles": ["Anyon condensation paper", "Operator algebra note"],
                    "community_labels": ["Anyon condensation cluster"],
                    "detail": "Anyon condensation appears across the two sources.",
                }
            ],
            "questions": [
                {
                    "question_id": "graph-question:01",
                    "question_type": "bridge_question",
                    "bridge_label": "Anyon condensation",
                    "question": "How does Anyon condensation connect the two source routes inside the current topic?",
                }
            ],
            "diff": {
                "added": {"node_count": 1, "node_labels": ["Anyon condensation"], "edge_count": 0, "edge_relations": [], "god_node_count": 1, "god_node_labels": ["Anyon condensation"]},
                "removed": {"node_count": 1, "node_labels": ["Topological order"], "edge_count": 0, "edge_relations": [], "god_node_count": 1, "god_node_labels": ["Topological order"]},
            },
            "path": "runtime/topics/demo-topic/graph_analysis.json",
            "note_path": "runtime/topics/demo-topic/graph_analysis.md",
            "history_path": "runtime/topics/demo-topic/graph_analysis_history.jsonl",
        }
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue this topic and inspect graph analysis",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["graph_analysis"]["summary"]["connection_count"], 1)
        self.assertEqual(bundle["graph_analysis"]["diff"]["added"]["node_labels"][0], "Anyon condensation")
        self.assertIn(
            "runtime/topics/demo-topic/graph_analysis.md",
            json.dumps(bundle["must_read_now"]),
        )
        note_text = Path(result["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Graph analysis", note_text)
        self.assertIn("Anyon condensation", note_text)

    def test_runtime_bundle_exposes_theory_context_fragment_map_for_formal_theory_work(self) -> None:
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "resume_stage": "L4",
                    "last_materialized_stage": "L4",
                    "latest_run_id": "run-001",
                    "research_mode": "formal_derivation",
                    "pointers": {
                        "control_note_path": "runtime/topics/demo-topic/control_note.md"
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._rewrite_action_queue(
            "formal_theory_revision",
            "Revise the bounded theorem-facing packet and its supporting theory artifacts.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-theorem"},
        )
        packet_paths = self._write_theory_packet_artifacts()
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["research_question_contract"]["template_mode"] = "formal_theory"
        shell_surfaces["research_question_contract"]["research_mode"] = "formal_derivation"
        shell_surfaces["validation_contract"]["validation_mode"] = "formal"
        shell_surfaces["validation_review_bundle"] = {
            **dict(shell_surfaces["validation_review_bundle"]),
            "status": "ready",
            "primary_review_kind": "formal_theory_review",
            "candidate_ids": ["candidate:demo-theorem"],
            "specialist_artifacts": [
                {
                    "candidate_id": "candidate:demo-theorem",
                    "candidate_type": "theorem_card",
                    "artifact_kind": "formal_theory_review",
                    "path": "validation/topics/demo-topic/runs/run-001/theory-packets/candidate-demo-theorem/formal_theory_review.json",
                    "status": "ready",
                }
            ],
            "summary": "Formal theory review is the primary theorem-facing review entry point.",
        }
        shell_surfaces["statement_compilation"] = {
            **dict(shell_surfaces["statement_compilation"]),
            "status": "ready",
            "summary": "Statement compilation is active for the bounded theorem packet.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/statement_compilation.active.md",
        }
        shell_surfaces["lean_bridge"] = {
            **dict(shell_surfaces["lean_bridge"]),
            "status": "ready",
            "summary": "Lean bridge packet is ready for the bounded theorem packet.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/lean_bridge.active.md",
        }
        self._write_surface(
            "runtime/topics/demo-topic/topic_skill_projection.active.json",
            json.dumps(
                {
                    "id": "topic_skill_projection:demo-topic",
                    "topic_slug": "demo-topic",
                    "source_topic_slug": "demo-topic",
                    "run_id": "run-001",
                    "title": "Demo theorem projection",
                    "summary": "Reusable theorem-facing route memory for the bounded demo theorem.",
                    "lane": "formal_theory",
                    "status": "available",
                    "status_reason": "Projection is available.",
                    "candidate_id": "candidate:demo-theorem",
                    "intended_l2_target": "topic_skill_projection:demo-topic",
                    "entry_signals": ["lane=formal_theory"],
                    "required_first_reads": ["runtime/topics/demo-topic/research_question.contract.md"],
                    "required_first_routes": ["Read the theorem-facing review packet before changing the route."],
                    "benchmark_first_rules": [],
                    "operator_checkpoint_rules": [],
                    "operation_trust_requirements": [],
                    "strategy_guidance": [],
                    "forbidden_proxies": [],
                    "derived_from_artifacts": [packet_paths["formal_theory_review"]],
                    "updated_at": "2026-04-13T10:00:00+08:00",
                    "updated_by": "test",
                },
                indent=2,
            )
            + "\n",
        )
        self._write_surface(
            "runtime/topics/demo-topic/topic_skill_projection.active.md",
            "# Demo theorem projection\n",
        )
        shell_surfaces["topic_skill_projection"] = {
            "id": "topic_skill_projection:demo-topic",
            "topic_slug": "demo-topic",
            "source_topic_slug": "demo-topic",
            "run_id": "run-001",
            "title": "Demo theorem projection",
            "summary": "Reusable theorem-facing route memory for the bounded demo theorem.",
            "lane": "formal_theory",
            "status": "available",
            "status_reason": "Projection is available.",
            "candidate_id": "candidate:demo-theorem",
            "intended_l2_target": "topic_skill_projection:demo-topic",
            "entry_signals": ["lane=formal_theory"],
            "required_first_reads": ["runtime/topics/demo-topic/research_question.contract.md"],
            "required_first_routes": ["Read the theorem-facing review packet before changing the route."],
            "benchmark_first_rules": [],
            "operator_checkpoint_rules": [],
            "operation_trust_requirements": [],
            "strategy_guidance": [],
            "forbidden_proxies": [],
            "derived_from_artifacts": [
                "validation/topics/demo-topic/runs/run-001/theory-packets/candidate-demo-theorem/formal_theory_review.json"
            ],
            "path": "runtime/topics/demo-topic/topic_skill_projection.active.json",
            "note_path": "runtime/topics/demo-topic/topic_skill_projection.active.md",
            "updated_at": "2026-04-13T10:00:00+08:00",
            "updated_by": "test",
        }
        candidate_rows = [
            {
                "candidate_id": "candidate:demo-theorem",
                "candidate_type": "theorem_card",
                "title": "Demo theorem",
                "summary": "Bounded theorem packet.",
                "formal_theory_review_overall_status": "ready",
                "topic_completion_status": "promotion-ready",
            }
        ]

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=candidate_rows):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="Continue the bounded theorem-facing revision lane.",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        injection = bundle["theory_context_injection"]
        self.assertEqual(injection["status"], "active")
        self.assertEqual(injection["session_ttl_seconds"], 3600)
        self.assertIn("topics/demo-topic/runtime/statement_compilation.active.md", injection["active_target_paths"])
        self.assertIn("topics/demo-topic/runtime/topic_skill_projection.active.md", injection["active_target_paths"])
        fragment_kinds = {row["kind"] for row in injection["fragments"]}
        self.assertEqual(
            fragment_kinds,
            {"notation_bindings", "prerequisite_closure", "relevant_l2_units"},
        )
        notation_fragment = next(row for row in injection["fragments"] if row["kind"] == "notation_bindings")
        self.assertIn("H = Hamiltonian", notation_fragment["summary"])
        self.assertIn(
            "topics/demo-topic/L4/runs/run-001/theory-packets/candidate-demo-theorem/notation_table.json",
            notation_fragment["source_paths"],
        )
        self.assertTrue((self.kernel_root / notation_fragment["path"]).exists())

        schema = json.loads(
            (self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.validate(bundle, schema)

    def test_runtime_bundle_surfaces_active_loop_detection_after_repeated_theorem_retries(self) -> None:
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "resume_stage": "L4",
                    "last_materialized_stage": "L4",
                    "latest_run_id": "run-001",
                    "research_mode": "formal_derivation",
                    "pointers": {
                        "control_note_path": "runtime/topics/demo-topic/control_note.md"
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._rewrite_action_queue(
            "proof_review",
            "Continue the bounded theorem-facing proof review for the same candidate.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-theorem"},
        )
        self._write_loop_retry_events(attempts=3)
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["research_question_contract"]["template_mode"] = "formal_theory"
        shell_surfaces["research_question_contract"]["research_mode"] = "formal_derivation"
        shell_surfaces["validation_contract"]["validation_mode"] = "formal"

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="Continue the bounded theorem-facing proof review for the same candidate.",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        loop_detection = bundle["loop_detection"]
        self.assertEqual(loop_detection["status"], "active")
        self.assertEqual(loop_detection["retry_threshold"], 3)
        self.assertEqual(loop_detection["retry_count"], 3)
        self.assertEqual(loop_detection["candidate_id"], "candidate:demo-theorem")
        self.assertEqual(loop_detection["source_operation_kind"], "formal_theory_audit")
        self.assertEqual(loop_detection["suggestion_kind"], "prerequisite_closure")
        self.assertIn("decompose", loop_detection["strategy_change_suggestion"].lower())
        self.assertTrue(loop_detection["note_path"].endswith("loop_detection.md"))
        self.assertIn(loop_detection["note_path"], self._must_read_paths(bundle))
        self.assertTrue((self.kernel_root / loop_detection["note_path"]).exists())
        note_text = Path(result["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Loop detection", note_text)

    def test_runtime_bundle_surfaces_protocol_manifest_drift_for_verify_mode(self) -> None:
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "resume_stage": "L4",
                    "last_materialized_stage": "L4",
                    "latest_run_id": "run-001",
                    "research_mode": "formal_derivation",
                    "pointers": {
                        "control_note_path": "runtime/topics/demo-topic/control_note.md"
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._rewrite_action_queue(
            "proof_review",
            "Continue the bounded theorem-facing proof review for the current candidate.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-theorem"},
        )
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["research_question_contract"]["template_mode"] = "formal_theory"
        shell_surfaces["research_question_contract"]["research_mode"] = "formal_derivation"
        shell_surfaces["validation_contract"]["validation_mode"] = "formal"
        Path(str(shell_surfaces["validation_contract_note_path"])).unlink()

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="Continue the bounded theorem-facing proof review for the current candidate.",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        manifest = bundle["protocol_manifest"]
        self.assertEqual(manifest["overall_status"], "fail")
        self.assertEqual(manifest["declared_state"], "verifying")
        self.assertIn("runtime/topics/demo-topic/validation_contract.active.md", manifest["missing_paths"])
        self.assertTrue(manifest["note_path"].endswith("protocol_manifest.active.md"))
        self.assertIn(manifest["note_path"], self._must_read_paths(bundle))
        self.assertTrue((self.kernel_root / manifest["path"]).exists())
        self.assertTrue((self.kernel_root / manifest["note_path"]).exists())
        note_text = Path(self.kernel_root / manifest["note_path"]).read_text(encoding="utf-8")
        self.assertIn("validation_contract.active.md", note_text)
        self.assertIn("verifying", note_text)

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
        self.assertNotIn("validation_review_bundle.active.md", json.dumps(bundle["must_read_now"]))
        self.assertIn("validation_review_bundle.active.md", json.dumps(bundle["may_defer_until_trigger"]))
        self.assertNotIn("operator_console.md", json.dumps(bundle["must_read_now"]))
        self.assertNotIn("agent_brief.md", json.dumps(bundle["must_read_now"]))

    def test_full_discussion_mode_defers_validation_and_promotion_context(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["idea_packet"]["status"] = "needs_clarification"
        shell_surfaces["idea_packet"]["status_reason"] = "The novelty target is still underspecified."

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="clarify the research direction before deeper work",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)
        deferred_paths = self._deferred_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "discussion")
        self.assertIn("runtime/topics/demo-topic/idea_packet.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/topic_dashboard.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/research_question.contract.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/validation_review_bundle.active.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/validation_contract.active.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/promotion_readiness.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/validation_review_bundle.active.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/validation_contract.active.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/promotion_readiness.md", deferred_paths)

    def test_full_explore_mode_keeps_candidate_context_and_defers_validation_and_promotion(self) -> None:
        shell_surfaces = self._shell_surfaces()

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="keep exploring the next bounded candidate route",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)
        deferred_paths = self._deferred_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "explore")
        self.assertIn("runtime/topics/demo-topic/topic_dashboard.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/research_question.contract.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/control_note.md", must_read_paths)
        self.assertIn("topics/demo-topic/runtime/topic_synopsis.json", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/validation_review_bundle.active.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/validation_contract.active.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/promotion_readiness.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/topic_completion.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/validation_review_bundle.active.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/validation_contract.active.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/promotion_readiness.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/topic_completion.md", deferred_paths)

    def test_full_verify_mode_foregrounds_validation_route_and_defers_promotion(self) -> None:
        shell_surfaces = self._shell_surfaces()
        (self.runtime_root / "selected_validation_route.md").write_text("# Selected validation route\n", encoding="utf-8")
        (self.runtime_root / "execution_task.md").write_text("# Execution task\n", encoding="utf-8")
        self._rewrite_action_queue(
            "dispatch_execution_task",
            "Dispatch the selected execution task.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-benchmark"},
        )
        self._rewrite_interaction_state(
            {
                "human_request": "continue the validation route",
                "action_queue_surface": {},
                "decision_surface": {},
                "human_edit_surfaces": [],
                "closed_loop": {
                    "selected_route_path": "runtime/topics/demo-topic/selected_validation_route.md",
                    "execution_task_path": "runtime/topics/demo-topic/execution_task.md",
                },
            }
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue the current verification lane",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)
        deferred_paths = self._deferred_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "verify")
        self.assertIn("runtime/topics/demo-topic/validation_review_bundle.active.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/validation_contract.active.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/selected_validation_route.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/execution_task.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/promotion_readiness.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/control_note.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/promotion_readiness.md", deferred_paths)
        self.assertIn("runtime/topics/demo-topic/control_note.md", deferred_paths)
        active_triggers = {
            row["trigger"]
            for row in bundle["escalation_triggers"]
            if row.get("active")
        }
        self.assertIn("verification_route_selection", active_triggers)
        self.assertNotIn("promotion_intent", active_triggers)

    def test_full_verify_mode_foregrounds_post_promotion_formalization_surfaces(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["statement_compilation"] = {
            **dict(shell_surfaces["statement_compilation"]),
            "status": "needs_repair",
            "summary": "Statement compilation surfaced open proof-repair holes after the promoted writeback.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/statement_compilation.active.md",
        }
        shell_surfaces["lean_bridge"] = {
            **dict(shell_surfaces["lean_bridge"]),
            "status": "needs_refinement",
            "summary": "Lean bridge still carries proof obligations after the promoted writeback.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/lean_bridge.active.md",
        }
        self._rewrite_action_queue(
            "prepare_lean_bridge",
            "Refresh Lean bridge packets and proof-state sidecars for the promoted Layer 2 candidate.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-theorem"},
        )
        self._rewrite_interaction_state(
            {
                "human_request": "continue the post-promotion formalization follow-up",
                "action_queue_surface": {},
                "decision_surface": {},
                "human_edit_surfaces": [],
                "closed_loop": {},
            }
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue the post-promotion formalization follow-up",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "verify")
        self.assertIn("runtime/topics/demo-topic/statement_compilation.active.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/lean_bridge.active.md", must_read_paths)

    def test_full_verify_mode_foregrounds_proof_repair_review_surfaces(self) -> None:
        shell_surfaces = self._shell_surfaces()
        shell_surfaces["statement_compilation"] = {
            **dict(shell_surfaces["statement_compilation"]),
            "status": "needs_repair",
            "summary": "Statement compilation surfaced open proof-repair holes after Lean bridge refresh.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/statement_compilation.active.md",
            "packets": [
                {
                    "candidate_id": "candidate:demo-theorem",
                    "repair_plan_note_path": "validation/topics/demo-topic/runs/run-001/statement-compilation/candidate-demo-theorem/proof_repair_plan.md",
                }
            ],
        }
        shell_surfaces["lean_bridge"] = {
            **dict(shell_surfaces["lean_bridge"]),
            "status": "needs_refinement",
            "summary": "Lean bridge still carries proof obligations after refresh.",
            "packet_count": 1,
            "path": "runtime/topics/demo-topic/lean_bridge.active.md",
            "packets": [
                {
                    "candidate_id": "candidate:demo-theorem",
                    "packet_note_path": "validation/topics/demo-topic/runs/run-001/lean-bridge/candidate-demo-theorem/lean_ready_packet.md",
                }
            ],
        }
        self._rewrite_action_queue(
            "review_proof_repair_plan",
            "Review the proof-repair plan and Lean proof obligations for the promoted candidate before deeper formalization.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-theorem"},
        )
        self._rewrite_interaction_state(
            {
                "human_request": "review the proof-repair plan after lean-bridge refresh",
                "action_queue_surface": {},
                "decision_surface": {},
                "human_edit_surfaces": [],
                "closed_loop": {},
            }
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="review the proof-repair plan after lean-bridge refresh",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "verify")
        self.assertIn("runtime/topics/demo-topic/statement_compilation.active.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/lean_bridge.active.md", must_read_paths)
        self.assertIn(
            "validation/topics/demo-topic/runs/run-001/statement-compilation/candidate-demo-theorem/proof_repair_plan.md",
            must_read_paths,
        )

    def test_full_promote_mode_foregrounds_gate_surfaces_and_defers_history(self) -> None:
        shell_surfaces = self._shell_surfaces()
        (self.runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "requested",
                    "candidate_id": "candidate:demo-benchmark",
                    "candidate_type": "method",
                    "backend_id": "backend:demo",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")
        self._rewrite_action_queue(
            "promote_candidate",
            "Promote the current candidate into Layer 2 after selected route review.",
            handler_args={"run_id": "run-001", "candidate_id": "candidate:demo-benchmark"},
        )
        self._rewrite_interaction_state(
            {
                "human_request": "review promotion and writeback readiness",
                "action_queue_surface": {},
                "decision_surface": {},
                "human_edit_surfaces": [],
                "closed_loop": {
                    "selected_route_path": "runtime/topics/demo-topic/selected_validation_route.md",
                },
            }
        )
        (self.runtime_root / "selected_validation_route.md").write_text("# Selected validation route\n", encoding="utf-8")

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="review promotion and writeback readiness",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)
        deferred_paths = self._deferred_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "promote")
        self.assertIn("runtime/topics/demo-topic/promotion_readiness.md", must_read_paths)
        self.assertIn("topics/demo-topic/runtime/promotion_gate.md", must_read_paths)
        self.assertIn("runtime/topics/demo-topic/topic_completion.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/control_note.md", must_read_paths)
        self.assertNotIn("runtime/topics/demo-topic/topic_synopsis.json", must_read_paths)
        self.assertIn("topics/demo-topic/runtime/control_note.md", deferred_paths)
        self.assertIn("topics/demo-topic/runtime/topic_synopsis.json", deferred_paths)
        active_triggers = {
            row["trigger"]
            for row in bundle["escalation_triggers"]
            if row.get("active")
        }
        self.assertIn("promotion_intent", active_triggers)
        self.assertNotIn("verification_route_selection", active_triggers)

    def test_full_promote_mode_keeps_selected_candidate_route_choice_as_supporting_evidence(self) -> None:
        shell_surfaces = self._shell_surfaces()
        topic_state = json.loads((self.runtime_root / "topic_state.json").read_text(encoding="utf-8"))
        topic_state["pointers"] = {
            **(topic_state.get("pointers") or {}),
            "selected_candidate_route_choice_note_path": "runtime/topics/demo-topic/selected_candidate_route_choice.active.md",
            "selected_candidate_route_choice_path": "runtime/topics/demo-topic/selected_candidate_route_choice.active.json",
        }
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(topic_state, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "pending_human_approval",
                    "candidate_id": "staging:demo-topic-existing",
                    "candidate_type": "concept",
                    "backend_id": "backend:demo",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")
        (self.runtime_root / "selected_candidate_route_choice.active.json").write_text(
            json.dumps(
                {
                    "selected_candidate_id": "staging:demo-topic-existing",
                    "chosen_action_type": "l2_promotion_review",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "selected_candidate_route_choice.active.md").write_text(
            "# Selected candidate route choice\n",
            encoding="utf-8",
        )
        self._rewrite_action_queue(
            "approve_promotion",
            "Review the pending promotion gate for the selected staged candidate before any Layer 2 writeback.",
            handler_args={"run_id": "run-001", "candidate_id": "staging:demo-topic-existing"},
        )
        self._rewrite_interaction_state(
            {
                "human_request": "review the pending promotion gate",
                "action_queue_surface": {},
                "decision_surface": {},
                "human_edit_surfaces": [],
                "closed_loop": {},
            }
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="review the pending promotion gate",
                    load_profile="full",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        must_read_paths = self._must_read_paths(bundle)

        self.assertEqual(bundle["runtime_mode"], "promote")
        self.assertIn("topics/demo-topic/runtime/promotion_gate.md", must_read_paths)
        self.assertIn(
            "runtime/topics/demo-topic/selected_candidate_route_choice.active.md",
            must_read_paths,
        )

    def test_runtime_bundle_enriches_paired_backend_bridge_entries(self) -> None:
        shell_surfaces = self._shell_surfaces()
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L3",
                    "latest_run_id": "run-001",
                    "research_mode": "toy_model",
                    "backend_bridges": [
                        {
                            "backend_id": "backend:theoretical-physics-brain",
                            "title": "Theoretical Physics Brain",
                            "backend_type": "human_note_library",
                            "status": "active",
                            "card_status": "present",
                            "card_path": "canonical/backends/theoretical-physics-brain.json",
                            "backend_root": "/tmp/brain",
                            "artifact_kinds": ["formal_theory_note"],
                            "canonical_targets": ["concept"],
                            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
                            "source_count": 1,
                        },
                        {
                            "backend_id": "backend:theoretical-physics-knowledge-network",
                            "title": "Theoretical Physics Knowledge Network",
                            "backend_type": "mixed_local_library",
                            "status": "active",
                            "card_status": "present",
                            "card_path": "canonical/backends/theoretical-physics-knowledge-network.json",
                            "backend_root": "/tmp/tpkn",
                            "artifact_kinds": ["typed_unit"],
                            "canonical_targets": ["concept"],
                            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
                            "source_count": 1,
                        },
                    ],
                    "pointers": {"control_note_path": "runtime/topics/demo-topic/control_note.md"},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "theoretical-physics-brain.json").write_text(
            json.dumps({"backend_id": "backend:theoretical-physics-brain", "title": "Theoretical Physics Brain"}, indent=2) + "\n",
            encoding="utf-8",
        )
        (backends_root / "theoretical-physics-knowledge-network.json").write_text(
            json.dumps({"backend_id": "backend:theoretical-physics-knowledge-network", "title": "Theoretical Physics Knowledge Network"}, indent=2) + "\n",
            encoding="utf-8",
        )
        (backends_root / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md").write_text("# Pair contract\n", encoding="utf-8")
        (self.kernel_root / "canonical" / "L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md").write_text("# Maintenance\n", encoding="utf-8")

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="inspect paired backend alignment",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        pair_rows = {row["backend_id"]: row for row in bundle["backend_bridges"]}
        self.assertEqual(pair_rows["backend:theoretical-physics-brain"]["pairing_role"], "operator_primary")
        self.assertEqual(
            pair_rows["backend:theoretical-physics-brain"]["paired_backend_id"],
            "backend:theoretical-physics-knowledge-network",
        )
        self.assertEqual(pair_rows["backend:theoretical-physics-brain"]["pairing_status"], "paired_active")
        self.assertEqual(pair_rows["backend:theoretical-physics-brain"]["drift_status"], "audit_required")
        self.assertEqual(pair_rows["backend:theoretical-physics-brain"]["backend_debt_status"], "unassessed")
        self.assertTrue(pair_rows["backend:theoretical-physics-brain"]["semantic_separation"]["promotion"]["distinct_from_sync"])

    def test_runtime_bundle_exposes_unified_h_plane_surface(self) -> None:
        shell_surfaces = self._shell_surfaces()
        (self.runtime_root / "control_note.md").write_text(
            "---\n"
            "directive: human_redirect\n"
            "summary: Redirect toward theorem-facing route.\n"
            "---\n",
            encoding="utf-8",
        )
        (self.runtime_root / "innovation_direction.md").write_text("# Direction\n", encoding="utf-8")
        (self.runtime_root / "innovation_decisions.jsonl").write_text(
            json.dumps({"decision": "redirect", "summary": "Redirect toward theorem-facing route."}, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        (self.kernel_root / "runtime" / "active_topics.json").write_text(
            json.dumps(
                {
                    "registry_version": 1,
                    "focused_topic_slug": "demo-topic",
                    "updated_at": "2026-04-11T02:30:00+08:00",
                    "updated_by": "test",
                    "source": "test",
                    "topics": [
                        {
                            "topic_slug": "demo-topic",
                            "status": "active",
                            "operator_status": "paused",
                            "priority": 0,
                            "last_activity": "2026-04-11T02:30:00+08:00",
                            "runtime_root": str(self.runtime_root),
                            "lane": "toy_numeric",
                            "resume_stage": "L3",
                            "run_id": "run-001",
                            "projection_status": "missing",
                            "projection_note_path": None,
                            "blocked_by": [],
                            "blocked_by_details": [],
                            "focus_state": "focused",
                            "summary": "Paused for review.",
                            "human_request": "",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.runtime_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "approved",
                    "candidate_id": "candidate:demo",
                    "backend_id": "backend:theoretical-physics-knowledge-network",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="redirect and pause this topic",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertIn("h_plane", bundle)
        self.assertEqual(bundle["h_plane"]["steering"]["status"], "active_redirect")
        self.assertEqual(bundle["h_plane"]["checkpoint"]["status"], "answered")
        self.assertEqual(bundle["h_plane"]["approval"]["status"], "approved")
        self.assertEqual(bundle["h_plane"]["registry"]["operator_status"], "paused")
        self.assertEqual(bundle["h_plane"]["registry"]["focus_state"], "focused")

    def test_runtime_bundle_treats_continue_recorded_h_plane_as_steady(self) -> None:
        shell_surfaces = self._shell_surfaces()
        (self.runtime_root / "control_note.md").write_text(
            "---\n"
            "summary: Continue the active topic under the current operator steering.\n"
            "---\n",
            encoding="utf-8",
        )
        (self.runtime_root / "innovation_direction.md").write_text("# Direction\n", encoding="utf-8")
        (self.runtime_root / "innovation_decisions.jsonl").write_text(
            json.dumps({"decision": "continue", "summary": "Continue the active topic under the current operator steering."}, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                result = self.service._materialize_runtime_protocol_bundle(
                    topic_slug="demo-topic",
                    updated_by="test",
                    human_request="continue this topic",
                    load_profile="light",
                )

        bundle = json.loads(Path(result["runtime_protocol_path"]).read_text(encoding="utf-8"))
        self.assertEqual(bundle["h_plane"]["steering"]["status"], "continue_recorded")
        self.assertEqual(bundle["h_plane"]["overall_status"], "steady")

    def test_build_runtime_mode_contract_classifies_verify_and_promote_modes(self) -> None:
        verify_contract = build_runtime_mode_contract(
            resume_stage="L4",
            load_profile="full",
            idea_packet_status="approved_for_execution",
            operator_checkpoint_status="cancelled",
            selected_action_type="dispatch_execution_task",
            selected_action_summary="Dispatch the selected execution task.",
            must_read_now=[{"path": "runtime/topics/demo-topic/topic_dashboard.md", "reason": "dashboard"}],
            may_defer_until_trigger=[],
            escalation_triggers=[
                {
                    "trigger": "verification_route_selection",
                    "active": True,
                    "condition": "selected route is active",
                    "required_reads": ["runtime/topics/demo-topic/selected_validation_route.json"],
                }
            ],
        )
        self.assertEqual(verify_contract["runtime_mode"], "verify")
        self.assertEqual(verify_contract["active_submode"], "iterative_verify")
        self.assertEqual(verify_contract["transition_posture"]["transition_kind"], "boundary_hold")

        promote_contract = build_runtime_mode_contract(
            resume_stage="L4",
            load_profile="full",
            idea_packet_status="approved_for_execution",
            operator_checkpoint_status="cancelled",
            selected_action_type="promote_candidate",
            selected_action_summary="Promote the current candidate into Layer 2.",
            must_read_now=[{"path": "runtime/topics/demo-topic/promotion_gate.md", "reason": "gate"}],
            may_defer_until_trigger=[],
            escalation_triggers=[
                {
                    "trigger": "promotion_intent",
                    "active": True,
                    "condition": "writeback is active",
                    "required_reads": ["runtime/topics/demo-topic/promotion_gate.md"],
                }
            ],
        )
        self.assertEqual(promote_contract["runtime_mode"], "promote")
        self.assertIsNone(promote_contract["active_submode"])
        self.assertEqual(promote_contract["transition_posture"]["transition_kind"], "forward_transition")

    def test_filter_escalation_triggers_for_mode_suppresses_out_of_mode_active_triggers(self) -> None:
        rows = [
            {
                "trigger": "verification_route_selection",
                "active": True,
                "condition": "verification path is active",
                "required_reads": ["runtime/topics/demo-topic/selected_validation_route.md"],
            },
            {
                "trigger": "promotion_intent",
                "active": True,
                "condition": "promotion path is active",
                "required_reads": ["runtime/topics/demo-topic/promotion_gate.md"],
            },
        ]

        filtered = filter_escalation_triggers_for_mode(runtime_mode="promote", escalation_triggers=rows)
        filtered_by_name = {row["trigger"]: row for row in filtered}

        self.assertTrue(filtered_by_name["promotion_intent"]["active"])
        self.assertFalse(filtered_by_name["verification_route_selection"]["active"])

    def test_topic_status_exposes_primary_runtime_surface_roles(self) -> None:
        shell_surfaces = self._shell_surfaces()
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                status_payload = self.service.topic_status(topic_slug="demo-topic")

        roles = status_payload["primary_runtime_surfaces"]
        self.assertIn("control_plane", status_payload)
        self.assertIn("h_plane", status_payload)
        self.assertEqual(status_payload["control_plane"]["task_type"], "open_exploration")
        self.assertEqual(status_payload["control_plane"]["lane"], status_payload["topic_synopsis"]["lane"])
        self.assertEqual(status_payload["control_plane"]["layer"], status_payload["current_stage"])
        self.assertEqual(status_payload["control_plane"]["mode"], "explore")
        self.assertEqual(roles["primary"]["runtime_machine"], "topics/demo-topic/runtime/topic_synopsis.json")
        self.assertEqual(roles["primary"]["runtime_human"], "topics/demo-topic/runtime/topic_dashboard.md")
        self.assertEqual(
            roles["primary"]["review_human"],
            "topics/demo-topic/runtime/validation_review_bundle.active.md",
        )
        self.assertEqual(roles["compatibility"]["current_topic_machine"], "runtime/current_topic.json")
        self.assertEqual(roles["compatibility"]["operator_console"], "topics/demo-topic/runtime/operator_console.md")
        self.assertEqual(status_payload["must_read_now"][0]["path"], "runtime/topics/demo-topic/topic_dashboard.md")

    def test_topic_status_materializes_layer_graph_surface(self) -> None:
        (self.runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": "demo-topic",
                    "task_type": "open_exploration",
                    "resume_stage": "L3",
                    "last_materialized_stage": "L4",
                    "latest_run_id": "run-001",
                    "research_mode": "formal_derivation",
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
                    "human_request": "Continue the bounded proof review after the returned result.",
                    "action_queue_surface": {},
                    "decision_surface": {
                        "selected_action_id": "action:demo-topic:return",
                        "decision_source": "heuristic",
                    },
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
                    "action_id": "action:demo-topic:return",
                    "action_type": "proof_review",
                    "summary": "Inspect the returned result and continue the bounded proof review.",
                    "status": "pending",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                    "handler_args": {"run_id": "run-001"},
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        shell_surfaces = self._shell_surfaces()
        with patch.object(self.service, "ensure_topic_shell_surfaces", return_value=shell_surfaces):
            with patch.object(self.service, "_candidate_rows_for_run", return_value=[]):
                status_payload = self.service.topic_status(topic_slug="demo-topic")

        self.assertEqual(status_payload["layer_graph"]["current_node_id"], "L3-R")
        self.assertEqual(status_payload["layer_graph"]["return_law"]["required_return_node"], "L3-R")
        self.assertEqual(
            status_payload["primary_runtime_surfaces"]["derived"]["layer_graph_human"],
            "topics/demo-topic/runtime/layer_graph.generated.md",
        )
        truth_runtime_root = self.kernel_root / "topics" / "demo-topic" / "runtime"
        self.assertTrue((truth_runtime_root / "layer_graph.generated.json").exists())
        self.assertTrue((truth_runtime_root / "layer_graph.generated.md").exists())


if __name__ == "__main__":
    unittest.main()
