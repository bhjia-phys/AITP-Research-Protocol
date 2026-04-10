from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module(module_name: str, relative_path: str):
    kernel_root = Path(__file__).resolve().parents[1]
    target_path = kernel_root / relative_path
    if str(target_path.parent) not in sys.path:
        sys.path.insert(0, str(target_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {target_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.knowledge_root = Path(self._tmpdir.name)
        (self.knowledge_root / "runtime").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "feedback").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "validation").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "source-layer").mkdir(parents=True, exist_ok=True)
        self.orchestrate_topic = _load_module(
            "aitp_orchestrate_topic_test",
            "runtime/scripts/orchestrate_topic.py",
        )
        self.decide_next_action = _load_module(
            "aitp_decide_next_action_test",
            "runtime/scripts/decide_next_action.py",
        )
        self.closed_loop_v1 = _load_module(
            "aitp_closed_loop_v1_test",
            "runtime/scripts/closed_loop_v1.py",
        )
        self.sync_topic_state = _load_module(
            "aitp_sync_topic_state_test",
            "runtime/scripts/sync_topic_state.py",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_json(self, relative_path: str, payload: dict) -> None:
        path = self.knowledge_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    def _write_jsonl(self, relative_path: str, rows: list[dict]) -> None:
        path = self.knowledge_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_infer_resume_state_handles_accepted_and_needs_revision(self) -> None:
        accepted = self.sync_topic_state.infer_resume_state(
            intake_status=None,
            feedback_status=None,
            latest_decision={"verdict": "accepted", "fallback_targets": []},
            closed_loop_decision=None,
        )
        needs_revision = self.sync_topic_state.infer_resume_state(
            intake_status=None,
            feedback_status=None,
            latest_decision={
                "verdict": "needs_revision",
                "fallback_targets": ["feedback/topics/demo-topic/runs/2026-03-13-demo"],
            },
            closed_loop_decision=None,
        )

        self.assertEqual(accepted[0], "L2")
        self.assertEqual(needs_revision[0], "L3")

    def test_pending_split_contract_action_detects_unapplied_contract(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "candidate_split_policy": {
                    "enabled": True,
                    "auto_apply_contracts": True,
                    "contract_filename": "candidate_split.contract.json",
                    "receipt_filename": "candidate_split_receipts.jsonl",
                }
            },
        )
        self._write_json(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_split.contract.json",
            {
                "contract_version": 1,
                "splits": [
                    {
                        "source_candidate_id": "candidate:demo",
                        "reason": "Split one wide candidate into smaller units.",
                        "child_candidates": [],
                        "deferred_fragments": [],
                    }
                ],
            },
        )

        actions = self.orchestrate_topic.pending_split_contract_action(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "apply_candidate_split_contract")

    def test_auto_promotion_actions_detect_ready_candidate(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "auto_promotion_policy": {
                    "enabled": True,
                    "default_backend_id": "backend:theoretical-physics-knowledge-network",
                    "trigger_candidate_statuses": ["ready_for_validation"],
                    "theory_formal_candidate_types": ["definition_card"],
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "title": "Demo Definition",
                    "summary": "A bounded definition.",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "origin_refs": [],
                    "question": "Can the definition be promoted?",
                    "assumptions": [],
                    "proposed_validation_route": "bounded-smoke",
                    "intended_l2_targets": ["definition:demo-definition"],
                    "status": "ready_for_validation",
                }
            ],
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/coverage_ledger.json",
            {"status": "pass"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/agent_consensus.json",
            {"status": "ready"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/regression_gate.json",
            {"status": "pass", "split_clearance_status": "clear", "promotion_blockers": []},
        )

        actions = self.orchestrate_topic.auto_promotion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "auto_promote_candidate")
        self.assertEqual(actions[0]["handler_args"]["candidate_id"], "candidate:demo-definition")

    def test_auto_promotion_actions_block_split_and_blockers(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "auto_promotion_policy": {
                    "enabled": True,
                    "default_backend_id": "backend:theoretical-physics-knowledge-network",
                    "trigger_candidate_statuses": ["ready_for_validation"],
                    "theory_formal_candidate_types": ["definition_card"],
                    "require_regression_gate_pass": True,
                    "block_when_split_required": True,
                    "block_when_promotion_blockers_present": True,
                    "block_when_cited_recovery_required": True,
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "title": "Demo Definition",
                    "summary": "A bounded definition.",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "origin_refs": [],
                    "question": "Can the definition be promoted?",
                    "assumptions": [],
                    "proposed_validation_route": "bounded-smoke",
                    "intended_l2_targets": ["definition:demo-definition"],
                    "status": "ready_for_validation",
                    "split_required": True,
                    "promotion_blockers": ["Still too wide."],
                }
            ],
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/coverage_ledger.json",
            {"status": "pass"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/agent_consensus.json",
            {"status": "ready"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/regression_gate.json",
            {
                "status": "pass",
                "split_required": True,
                "split_clearance_status": "blocked",
                "promotion_blockers": ["Still too wide."],
                "cited_recovery_required": True,
            },
        )

        actions = self.orchestrate_topic.auto_promotion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(actions, [])

    def test_followup_reintegration_actions_detect_returned_child_topic(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "followup_subtopic_policy": {
                    "enabled": True,
                    "unresolved_return_statuses": [
                        "pending_reentry",
                        "returned_with_gap",
                        "returned_unresolved"
                    ]
                }
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/followup_subtopics.jsonl",
            [
                {
                    "child_topic_slug": "demo-topic--followup--x",
                    "parent_topic_slug": "demo-topic",
                    "status": "spawned",
                    "return_packet_path": str(
                        self.knowledge_root / "runtime" / "topics" / "demo-topic--followup--x" / "followup_return_packet.json"
                    ),
                }
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic--followup--x/followup_return_packet.json",
            {
                "return_packet_version": 1,
                "child_topic_slug": "demo-topic--followup--x",
                "parent_topic_slug": "demo-topic",
                "parent_run_id": "2026-03-13-demo",
                "receipt_id": "receipt:demo",
                "query": "recover missing definition",
                "parent_gap_ids": ["open_gap:demo-gap"],
                "parent_followup_task_ids": ["followup_source_task:demo-gap"],
                "reentry_targets": ["definition:demo"],
                "supporting_regression_question_ids": ["regression_question:demo"],
                "source_id": "paper:demo",
                "arxiv_id": "1510.07698v1",
                "expected_return_route": "L0->L1->L3->L4->L2",
                "acceptable_return_shapes": ["recovered_units", "resolved_gap_update", "still_unresolved_packet"],
                "required_output_artifacts": ["candidate_ledger_or_recovered_units"],
                "unresolved_return_statuses": ["pending_reentry", "returned_with_gap", "returned_unresolved"],
                "return_status": "recovered_units",
                "accepted_return_shape": "recovered_units",
                "return_summary": "Recovered the missing definition.",
                "return_artifact_paths": ["feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl"],
                "reintegration_requirements": {
                    "must_write_back_parent_gaps": True,
                    "must_update_reentry_targets": True,
                    "must_not_patch_parent_directly": True,
                    "requires_child_topic_summary": True
                },
                "updated_at": "2026-03-13T00:00:00+08:00",
                "updated_by": "test"
            },
        )

        actions = self.orchestrate_topic.followup_reintegration_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "reintegrate_followup_subtopic")
        self.assertEqual(actions[0]["handler_args"]["child_topic_slug"], "demo-topic--followup--x")

    def test_topic_completion_actions_detect_missing_completion_surface(self) -> None:
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "ready_for_validation",
                }
            ],
        )

        actions = self.orchestrate_topic.topic_completion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "assess_topic_completion")

    def test_topic_completion_actions_refresh_when_gate_promoted_but_completion_is_stale(self) -> None:
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "auto_promoted",
                }
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic/promotion_gate.json",
            {
                "status": "promoted",
                "candidate_id": "candidate:demo-definition",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/topic_completion.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "promotion-ready",
                "candidate_count": 1,
                "followup_subtopic_count": 0,
            },
        )

        actions = self.orchestrate_topic.topic_completion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "assess_topic_completion")

    def test_materialize_action_queue_prunes_stale_promotion_review_after_gate_promoted(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/promotion_gate.json",
            {
                "status": "promoted",
                "candidate_id": "candidate:demo-definition",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/topic_completion.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "promoted",
                "candidate_count": 1,
                "followup_subtopic_count": 0,
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L2",
                "pending_actions": [
                    "Review Layer 2 promotion for `candidate:demo-definition` now that coverage, formal-theory review, topic completion, and Lean bridge are all ready.",
                    "Keep the abstract/concrete equivalence route as a separate follow-up lane instead of widening the current concrete bicommutant bridge candidate.",
                    "Keep the multiplication-operator / masa example as its own follow-up lane after the concrete theorem-level package stabilizes.",
                ],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        summaries = [str(row.get("summary") or "") for row in queue]
        self.assertFalse(any(summary.startswith("Review Layer 2 promotion") for summary in summaries))
        self.assertTrue(
            any(summary.startswith("Keep the abstract/concrete equivalence route") for summary in summaries)
        )

    def test_materialize_action_queue_prefers_skill_discovery_for_capability_gap_contract(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "explore",
                "transition_posture": {
                    "transition_kind": "backedge_transition",
                    "triggered_by": ["capability_gap_blocker"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L3",
                "pending_actions": [
                    "Continue a manual follow-up on the current lane.",
                    "Review whether a new backend or workflow capability is needed.",
                ],
            },
            ["bounded capability gap"],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "skill_discovery")

    def test_materialize_action_queue_prefers_promotion_review_in_promote_mode(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "promote",
                "transition_posture": {
                    "transition_kind": "forward_transition",
                    "triggered_by": ["promotion_intent"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L4",
                "pending_actions": [
                    "Keep a manual follow-up lane open for later.",
                    "Review Layer 2 promotion for the bounded candidate.",
                ],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "l2_promotion_review")

    def test_materialize_action_queue_skips_runtime_execution_append_for_consultation_backedge(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "explore",
                "transition_posture": {
                    "transition_kind": "backedge_transition",
                    "triggered_by": ["non_trivial_consultation"],
                },
            },
        )

        with patch.object(
            self.orchestrate_topic,
            "compute_closed_loop_status",
            return_value={
                "next_transition": "select_route",
                "awaiting_external_result": False,
                "execution_task": None,
                "literature_followups": [],
                "paths": {},
            },
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pending_actions": [
                        "Consult memory before reshaping the candidate.",
                    ],
                },
                [],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        self.assertFalse(any(row["action_type"] == "select_validation_route" for row in queue))

    def test_materialize_action_queue_skips_skill_append_in_promote_mode(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "promote",
                "transition_posture": {
                    "transition_kind": "forward_transition",
                    "triggered_by": ["promotion_intent"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L4",
                "pending_actions": [
                    "Resolve backend parity before doing anything else.",
                    "Review Layer 2 promotion for the bounded candidate.",
                ],
            },
            ["backend parity"],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertFalse(any(row["action_type"] == "skill_discovery" for row in queue))

    def test_materialize_action_queue_skips_runtime_appends_when_human_checkpoint_required(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "verify",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": ["verification_route_selection"],
                    "requires_human_checkpoint": True,
                },
            },
        )

        with patch.object(
            self.orchestrate_topic,
            "compute_closed_loop_status",
            return_value={
                "next_transition": "select_route",
                "awaiting_external_result": False,
                "execution_task": None,
                "literature_followups": [
                    {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                ],
                "paths": {},
            },
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                ["backend parity"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        self.assertFalse(any(row["action_type"] == "skill_discovery" for row in queue))
        self.assertFalse(any(row["action_type"] == "select_validation_route" for row in queue))
        self.assertFalse(any(row["action_type"] == "literature_followup_search" for row in queue))

    def test_materialize_action_queue_skips_helper_runtime_appends_when_human_checkpoint_required(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "verify",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": ["verification_route_selection"],
                    "requires_human_checkpoint": True,
                },
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": None,
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
            patch.object(
                self.orchestrate_topic,
                "topic_completion_actions",
                return_value=[helper_action("action:demo-topic:completion", "assess_topic_completion")],
            ),
            patch.object(
                self.orchestrate_topic,
                "auto_promotion_actions",
                return_value=[helper_action("action:demo-topic:auto-promote", "auto_promote_candidate")],
            ),
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                [],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertNotIn("assess_topic_completion", action_types)
        self.assertNotIn("auto_promote_candidate", action_types)

    def test_materialize_action_queue_skips_runtime_and_helper_appends_when_operator_checkpoint_is_requested(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/operator_checkpoint.active.json",
            {
                "checkpoint_id": "checkpoint:demo-topic:execution-lane-confirmation",
                "topic_slug": "demo-topic",
                "checkpoint_kind": "execution_lane_confirmation",
                "status": "requested",
                "active": True,
                "question": "Confirm the execution lane before deeper runtime expansion.",
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": None,
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "compute_closed_loop_status",
                return_value={
                    "next_transition": "select_route",
                    "awaiting_external_result": False,
                    "execution_task": None,
                    "literature_followups": [
                        {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                    ],
                    "paths": {},
                },
            ),
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
        ):
            queue, queue_meta = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                ["bounded capability gap"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertNotIn("skill_discovery", action_types)
        self.assertNotIn("select_validation_route", action_types)
        self.assertNotIn("literature_followup_search", action_types)
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertEqual(
            queue_meta["operator_checkpoint_path"],
            "runtime/topics/demo-topic/operator_checkpoint.active.json",
        )
        self.assertIn("operator checkpoint", str(queue_meta["append_policy_reason"]).lower())

    def test_materialize_action_queue_declared_contract_can_disable_runtime_appends_but_keep_skill_append(self) -> None:
        self._write_json(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.contract.json",
            {
                "contract_version": 1,
                "policy_note": "Keep only the declared queue plus capability-gap help.",
                "append_runtime_actions": False,
                "append_skill_action_if_needed": True,
                "actions": [
                    {
                        "action_id": "action:demo-topic:declared-01",
                        "summary": "Continue a bounded manual derivation follow-up.",
                        "action_type": "manual_followup",
                        "resume_stage": "L3",
                        "auto_runnable": False,
                    }
                ],
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.contract.json",
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "compute_closed_loop_status",
                return_value={
                    "next_transition": "select_route",
                    "awaiting_external_result": False,
                    "execution_task": None,
                    "literature_followups": [
                        {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                    ],
                    "paths": {},
                },
            ),
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
            patch.object(
                self.orchestrate_topic,
                "followup_subtopic_actions",
                return_value=[helper_action("action:demo-topic:subtopic", "spawn_followup_subtopics")],
            ),
            patch.object(
                self.orchestrate_topic,
                "topic_completion_actions",
                return_value=[helper_action("action:demo-topic:completion", "assess_topic_completion")],
            ),
            patch.object(
                self.orchestrate_topic,
                "auto_promotion_actions",
                return_value=[helper_action("action:demo-topic:auto-promote", "auto_promote_candidate")],
            ),
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                    "pointers": {
                        "next_actions_path": "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.md",
                    },
                },
                ["backend parity"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertIn("manual_followup", action_types)
        self.assertIn("skill_discovery", action_types)
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertNotIn("select_validation_route", action_types)
        self.assertNotIn("literature_followup_search", action_types)
        self.assertNotIn("spawn_followup_subtopics", action_types)
        self.assertNotIn("assess_topic_completion", action_types)
        self.assertNotIn("auto_promote_candidate", action_types)

    def test_decide_next_action_prefers_skill_discovery_for_capability_gap_backedge(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "runtime_protocol.generated.json").write_text(
            json.dumps(
                {
                    "runtime_mode": "explore",
                    "transition_posture": {
                        "transition_kind": "backedge_transition",
                        "triggered_by": ["capability_gap_blocker"],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        topic_state = {
            "topic_slug": "demo-topic",
            "updated_by": "test",
            "resume_stage": "L3",
            "pointers": {},
        }
        queue_rows = [
            {
                "action_id": "action:demo:1",
                "action_type": "manual_followup",
                "summary": "Keep probing the current manual lane.",
                "status": "pending",
                "auto_runnable": False,
            },
            {
                "action_id": "action:demo:2",
                "action_type": "skill_discovery",
                "summary": "Search for the bounded missing capability.",
                "status": "pending",
                "auto_runnable": True,
            },
        ]
        control_note = {"directive": None}
        runtime_contract = self.decide_next_action.load_runtime_contract(topic_runtime_root)

        unfinished = self.decide_next_action.build_unfinished_work(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )
        decision = self.decide_next_action.build_next_action_decision(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )

        self.assertEqual(unfinished["queue_head_action_id"], "action:demo:2")
        self.assertEqual(decision["selected_action"]["action_id"], "action:demo:2")
        self.assertEqual(decision["decision_basis"], "runtime_contract_preferred:skill_discovery")

    def test_decide_next_action_prefers_promotion_review_in_promote_mode(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "runtime_protocol.generated.json").write_text(
            json.dumps(
                {
                    "runtime_mode": "promote",
                    "transition_posture": {
                        "transition_kind": "forward_transition",
                        "triggered_by": ["promotion_intent"],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        topic_state = {
            "topic_slug": "demo-topic",
            "updated_by": "test",
            "resume_stage": "L4",
            "pointers": {},
        }
        queue_rows = [
            {
                "action_id": "action:demo:1",
                "action_type": "manual_followup",
                "summary": "Continue a non-promotion manual lane.",
                "status": "pending",
                "auto_runnable": False,
            },
            {
                "action_id": "action:demo:2",
                "action_type": "l2_promotion_review",
                "summary": "Review Layer 2 promotion for the bounded candidate.",
                "status": "pending",
                "auto_runnable": False,
            },
        ]
        control_note = {"directive": None}
        runtime_contract = self.decide_next_action.load_runtime_contract(topic_runtime_root)

        unfinished = self.decide_next_action.build_unfinished_work(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )
        decision = self.decide_next_action.build_next_action_decision(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )

        self.assertEqual(unfinished["queue_head_action_id"], "action:demo:2")
        self.assertEqual(decision["selected_action"]["action_id"], "action:demo:2")
        self.assertEqual(decision["decision_basis"], "runtime_contract_preferred:l2_promotion_review")

    def test_lean_bridge_actions_detect_missing_candidate_packet(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "lean_bridge_policy": {
                    "enabled": True,
                    "trigger_candidate_types": ["definition_card"]
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "ready_for_validation",
                }
            ],
        )

        actions = self.orchestrate_topic.lean_bridge_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "prepare_lean_bridge")

    def test_deferred_reactivation_actions_detect_ready_entry(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "deferred_buffer_policy": {
                    "enabled": True,
                    "auto_reactivate": True,
                }
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/deferred_candidates.json",
            {
                "buffer_version": 1,
                "topic_slug": "demo-topic",
                "updated_at": "2026-03-17T00:00:00+08:00",
                "updated_by": "aitp-cli",
                "entries": [
                    {
                        "entry_id": "deferred:demo",
                        "source_candidate_id": "candidate:demo",
                        "title": "Deferred Demo",
                        "summary": "Deferred until a follow-up source appears.",
                        "reason": "Missing source.",
                        "status": "buffered",
                        "reactivation_conditions": {
                            "source_ids_any": ["paper:followup-source"]
                        },
                        "reactivation_candidate": {
                            "candidate_id": "candidate:demo-reactivated"
                        },
                    }
                ],
            },
        )
        self._write_jsonl(
            "source-layer/topics/demo-topic/source_index.jsonl",
            [
                {
                    "source_id": "paper:followup-source",
                    "title": "Follow-up Source",
                    "summary": "Contains the missing resolution.",
                }
            ],
        )

        actions = self.orchestrate_topic.deferred_reactivation_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "reactivate_deferred_candidate")
        self.assertEqual(actions[0]["handler_args"]["entry_id"], "deferred:demo")

    def test_build_operator_console_starts_with_immediate_execution_contract(self) -> None:
        topic_state = {
            "topic_slug": "demo-topic",
            "promotion_gate": {"status": "approved"},
            "status_explainability": {
                "why_this_topic_is_here": "AITP is waiting on a bounded capability-gap step.",
                "current_route_choice": {
                    "next_action_summary": "Find the missing bounded workflow.",
                },
                "last_evidence_return": {
                    "summary": "No durable evidence-return artifact is currently recorded for this topic.",
                },
                "active_human_need": {
                    "summary": "No active human checkpoint is currently blocking the bounded loop.",
                },
            },
            "pointers": {
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
            },
        }
        interaction_state = {
            "topic_slug": "demo-topic",
            "human_request": "Continue bounded validation",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "human_edit_surfaces": [
                {
                    "surface": "runtime_queue_contract",
                    "path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                    "role": "editable queue contract snapshot",
                }
            ],
            "action_queue_surface": {
                "queue_source": "heuristic",
                "generated_contract_path": "runtime/topics/demo-topic/action_queue_contract.generated.json",
                "generated_contract_note_path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
            },
            "decision_surface": {
                "decision_mode": "continue_unfinished",
                "decision_source": "heuristic",
                "decision_basis": "fallback queue selection",
                "selected_action_id": "action:demo:1",
                "selected_action_type": "skill_discovery",
                "selected_action_auto_runnable": True,
                "pending_count": 1,
                "manual_pending_count": 0,
                "auto_pending_count": 1,
                "reason": "Bounded capability gap remains.",
                "control_note_status": "missing",
                "decision_contract_status": "missing",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "unfinished_work_note_path": "runtime/topics/demo-topic/unfinished_work.md",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
                "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
            },
            "capability_adaptation": {
                "protocol_path": "research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md",
                "discovery_script": "research/adapters/openclaw/scripts/discover_external_skills.py",
                "auto_install_allowed": False,
                "discovery_artifacts": [],
            },
            "delivery_contract": {
                "rule": "Outputs must cite exact artifact paths and justify the chosen layer."
            },
        }
        queue = [
            {
                "action_id": "action:demo:1",
                "action_type": "skill_discovery",
                "summary": "Find the missing bounded workflow.",
                "auto_runnable": True,
                "handler": "discover_external_skills",
            }
        ]

        rendered = self.orchestrate_topic.build_operator_console(topic_state, interaction_state, queue)

        self.assertIn("## Immediate execution contract", rendered)
        self.assertIn("### Do now", rendered)
        self.assertIn("### Escalate when", rendered)
        self.assertIn("## Topic explainability", rendered)
        self.assertIn("AITP is waiting on a bounded capability-gap step.", rendered)
        self.assertIn("`promotion_intent` status=`active`", rendered)
        self.assertIn("## Deferred surfaces and human edit areas", rendered)

    def test_build_resume_markdown_renders_status_explainability(self) -> None:
        state = {
            "topic_slug": "demo-topic",
            "updated_at": "2026-03-28T10:00:00+08:00",
            "updated_by": "codex",
            "last_materialized_stage": "L4",
            "resume_stage": "L3",
            "latest_run_id": "2026-03-20-demo",
            "research_mode": "formal_derivation",
            "active_executor_kind": "codex",
            "active_reasoning_profile": "bounded",
            "resume_reason": "Latest closed-loop decision is revise; resume exploratory work in Layer 3.",
            "source_count": 2,
            "pending_actions": ["Inspect the returned result and continue the bounded proof review."],
            "deferred_candidate_count": 0,
            "reactivable_deferred_count": 0,
            "followup_subtopic_count": 0,
            "research_mode_profile": {
                "profile_path": "runtime/research_modes/formal_derivation.json",
                "label": "Formal derivation",
                "description": "Formal derivation profile.",
                "reproducibility_expectations": ["Keep derivation anchors explicit."],
                "note_expectations": ["Write a human-readable derivation note."],
            },
            "backend_bridges": [],
            "promotion_gate": {"status": "not_requested"},
            "layer_status": {
                "L0": {"status": "present"},
                "L1": {"status": "present"},
                "L3": {"status": "active"},
                "L4": {"status": "revise"},
            },
            "closed_loop": {
                "status": "revise",
                "selected_route_id": "route:demo",
                "task_id": "task:demo",
                "result_id": "result:demo",
                "latest_decision": "revise",
                "literature_followup_count": 0,
                "followup_gap_count": 0,
            },
            "status_explainability": {
                "why_this_topic_is_here": "The topic is currently following `Inspect the returned result and continue the bounded proof review.` at stage `L3`.",
                "current_route_choice": {
                    "selected_route_id": "route:demo",
                    "execution_task_id": "task:demo",
                    "next_action_summary": "Inspect the returned result and continue the bounded proof review.",
                    "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
                    "selected_validation_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                },
                "last_evidence_return": {
                    "status": "present",
                    "kind": "result_manifest",
                    "record_id": "result:demo",
                    "recorded_at": "2026-03-28T09:00:00+08:00",
                    "path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                    "summary": "Closed-loop result manifest is `partial`.",
                },
                "active_human_need": {
                    "status": "none",
                    "kind": "none",
                    "path": "",
                    "summary": "No active human checkpoint is currently blocking the bounded loop.",
                },
                "blocker_summary": [],
            },
            "pointers": {
                "l0_source_index_path": "source-layer/topics/demo-topic/source_index.jsonl",
                "intake_status_path": "intake/topics/demo-topic/status.json",
                "feedback_status_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/status.json",
                "next_actions_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.md",
                "next_actions_contract_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.contract.json",
                "promotion_decision_path": "validation/topics/demo-topic/runs/2026-03-20-demo/promotion_decisions.jsonl",
                "consultation_index_path": "consultation/topics/demo-topic/consultation_index.jsonl",
                "control_note_path": "",
                "innovation_direction_path": "",
                "innovation_decisions_path": "",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "unfinished_work_note_path": "runtime/topics/demo-topic/unfinished_work.md",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
                "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
                "next_action_decision_contract_path": "runtime/topics/demo-topic/next_action_decision.contract.json",
                "next_action_decision_contract_note_path": "runtime/topics/demo-topic/next_action_decision.contract.md",
                "action_queue_contract_generated_path": "runtime/topics/demo-topic/action_queue_contract.generated.json",
                "action_queue_contract_generated_note_path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                "selected_validation_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                "execution_task_path": "runtime/topics/demo-topic/execution_task.json",
                "execution_notes_path": "validation/topics/demo-topic/runs/2026-03-20-demo/execution_notes",
                "returned_execution_result_path": "validation/topics/demo-topic/runs/2026-03-20-demo/returned_execution_result.json",
                "result_manifest_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                "trajectory_log_path": "validation/topics/demo-topic/runs/2026-03-20-demo/trajectory_log.jsonl",
                "trajectory_note_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_summary.md",
                "failure_classification_path": "validation/topics/demo-topic/runs/2026-03-20-demo/failure_classification.json",
                "failure_classification_note_path": "validation/topics/demo-topic/runs/2026-03-20-demo/failure_classification.md",
                "decision_ledger_path": "validation/topics/demo-topic/runs/2026-03-20-demo/decision_ledger.jsonl",
                "literature_followup_queries_path": "",
                "literature_followup_receipts_path": "",
                "followup_gap_writeback_path": "",
                "followup_gap_writeback_note_path": "",
                "deferred_buffer_path": "",
                "deferred_buffer_note_path": "",
                "followup_subtopics_path": "",
                "followup_subtopics_note_path": "",
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
            },
        }

        rendered = self.sync_topic_state.build_resume_markdown(state)

        self.assertIn("## Why this topic is here", rendered)
        self.assertIn("## Current route choice", rendered)
        self.assertIn("## Last evidence return", rendered)
        self.assertIn("## Active human need", rendered)
        self.assertIn("result:demo", rendered)

    def test_derive_status_explainability_prioritizes_operator_checkpoint(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "operator_checkpoint.active.json").write_text(
            json.dumps(
                {
                    "status": "requested",
                    "checkpoint_kind": "promotion_approval",
                    "question": "Should the current candidate be promoted?",
                    "blocker_summary": ["Promotion is waiting for an explicit human decision."],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        explainability = self.sync_topic_state.derive_status_explainability(
            topic_slug="demo-topic",
            resume_stage="L3",
            resume_reason="Latest closed-loop decision is revise; resume exploratory work in Layer 3.",
            pending_actions=["Inspect the returned result and continue the bounded proof review."],
            topic_runtime_root=topic_runtime_root,
            feedback_status=None,
            closed_loop={
                "result_manifest": {
                    "result_id": "result:demo",
                    "status": "partial",
                },
                "paths": {
                    "result_manifest_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                },
                "selected_route": {
                    "route_id": "route:demo",
                },
                "execution_task": {
                    "task_id": "task:demo",
                },
                "latest_decision": {
                    "reason": "The returned result still needs bounded manual review.",
                },
            },
            next_action_decision_note_path=topic_runtime_root / "next_action_decision.md",
        )

        self.assertEqual(explainability["active_human_need"]["kind"], "promotion_approval")
        self.assertEqual(explainability["last_evidence_return"]["kind"], "result_manifest")
        self.assertEqual(explainability["last_evidence_return"]["record_id"], "result:demo")
        self.assertIn("Promotion is waiting for an explicit human decision.", explainability["why_this_topic_is_here"])

    def test_build_agent_brief_starts_with_immediate_execution_contract(self) -> None:
        topic_state = {
            "topic_slug": "demo-topic",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "source_count": 2,
            "latest_run_id": "2026-03-20-demo",
            "research_mode": "formal_derivation",
            "active_executor_kind": "codex",
            "active_reasoning_profile": "bounded",
            "research_mode_profile": {
                "profile_path": "runtime/research_modes/formal_derivation.json",
                "label": "Formal derivation",
                "reproducibility_expectations": ["Keep derivation anchors explicit."],
                "note_expectations": ["Write a human-readable derivation note."],
            },
            "backend_bridges": [],
            "promotion_gate": {"status": "not_requested", "promoted_units": []},
            "pointers": {
                "l0_source_index_path": "source-layer/topics/demo-topic/source_index.jsonl",
                "intake_status_path": "source-layer/topics/demo-topic/intake_status.json",
                "feedback_status_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/feedback_status.json",
                "promotion_decision_path": "validation/topics/demo-topic/runs/2026-03-20-demo/promotion_decision.json",
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
                "consultation_index_path": "runtime/topics/demo-topic/consultation_index.json",
            },
        }
        interaction_state = {
            "decision_surface": {
                "decision_source": "heuristic",
                "decision_mode": "continue_unfinished",
                "selected_action_id": "action:demo:2",
                "control_note_status": "present",
                "decision_contract_status": "missing",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
            },
            "action_queue_surface": {
                "queue_source": "declared_contract",
                "declared_contract_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.contract.json",
            },
            "closed_loop": {
                "selected_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                "execution_task_path": "runtime/topics/demo-topic/execution_task.json",
                "returned_result_path": "validation/topics/demo-topic/runs/2026-03-20-demo/returned_execution_result.json",
                "trajectory_log_path": "runtime/topics/demo-topic/loop_history.jsonl",
                "failure_classification_path": "runtime/topics/demo-topic/failure_classification.json",
            },
        }
        queue = [
            {
                "action_id": "action:demo:2",
                "action_type": "consultation_followup",
                "summary": "Consult memory before reshaping the candidate.",
                "auto_runnable": False,
            }
        ]

        rendered = self.orchestrate_topic.build_agent_brief(topic_state, queue, interaction_state)

        self.assertIn("## Immediate execution contract", rendered)
        self.assertIn("### Do now", rendered)
        self.assertIn("### Escalate when", rendered)
        self.assertIn("`decision_override_present` status=`active`", rendered)
        self.assertIn("`non_trivial_consultation` status=`active`", rendered)
        self.assertIn("## Deferred surfaces and exact pointers", rendered)

    def test_materialize_execution_task_defaults_to_human_confirmation_for_inferred_route(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/selected_validation_route.json",
            {
                "route_id": "route:demo-topic:benchmark",
                "objective": "Run the bounded benchmark lane in the current execution environment.",
                "input_artifacts": ["feedback/topics/demo-topic/runs/run-001/result_summary.md"],
                "expected_outputs": ["validation/topics/demo-topic/runs/run-001/results/benchmark.json"],
                "success_criterion": ["Benchmark output is materialized."],
                "failure_signals": ["Benchmark run does not produce the declared artifact."],
                "run_id": "run-001",
                "surface": "numerical",
            },
        )

        payload = self.closed_loop_v1.materialize_execution_task(
            self.knowledge_root,
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "research_mode": "first_principles",
                "updated_by": "test",
            },
            updated_by="test",
        )

        self.assertTrue(payload["needs_human_confirm"])
        self.assertFalse(payload["auto_dispatch_allowed"])
        task_note = (
            self.knowledge_root / "runtime" / "topics" / "demo-topic" / "execution_task.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Human confirmation is required before dispatch", task_note)


if __name__ == "__main__":
    unittest.main()
