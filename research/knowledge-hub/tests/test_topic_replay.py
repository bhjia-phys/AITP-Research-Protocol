from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.topic_replay import materialize_topic_replay_bundle


class TopicReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self.tempdir.name)
        self.topic_slug = "demo-topic"
        self.topic_root = self.kernel_root / "runtime" / "topics" / self.topic_slug
        self.topic_root.mkdir(parents=True, exist_ok=True)

        (self.topic_root / "topic_synopsis.json").write_text(
            json.dumps(
                {
                    "topic_slug": self.topic_slug,
                    "title": "Demo Topic",
                    "question": "What does the demo topic establish?",
                    "lane": "formal_theory",
                    "human_request": "Keep it bounded.",
                    "next_action_summary": "Review the promoted result.",
                    "open_gap_summary": "No explicit gap packet is currently open.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": self.topic_slug,
                    "resume_stage": "L2",
                    "last_materialized_stage": "L4",
                    "latest_run_id": "run-001",
                    "summary": "Resume at L2 after a promoted result.",
                    "promotion_gate": {"promoted_units": ["theorem:demo-result"]},
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "research_question.contract.json").write_text(
            json.dumps(
                {
                    "title": "Demo Topic",
                    "question": "What does the demo topic establish?",
                    "competing_hypotheses": [
                        {
                            "hypothesis_id": "hypothesis:demo-leading",
                            "label": "Demo leading route",
                            "status": "leading",
                            "summary": "The leading bounded route stays visible on the active topic.",
                            "route_kind": "current_topic",
                            "route_target_summary": "Keep the leading route on the current topic branch.",
                            "route_target_ref": "runtime/topics/demo-topic/research_question.contract.md",
                            "evidence_refs": ["note:demo-leading"],
                            "exclusion_notes": [],
                        },
                        {
                            "hypothesis_id": "hypothesis:demo-followup",
                            "label": "Demo follow-up route",
                            "status": "watch",
                            "summary": "A neighboring route should stay live on a separate follow-up branch.",
                            "route_kind": "followup_subtopic",
                            "route_target_summary": "Open a bounded follow-up subtopic for the neighboring route.",
                            "route_target_ref": "runtime/topics/demo-topic/followup_subtopics.jsonl",
                            "evidence_refs": ["note:demo-followup"],
                            "exclusion_notes": [],
                        },
                        {
                            "hypothesis_id": "hypothesis:demo-excluded",
                            "label": "Demo excluded route",
                            "status": "excluded",
                            "summary": "A stronger alternative is currently ruled out.",
                            "route_kind": "excluded",
                            "route_target_summary": "Keep the stronger alternative excluded with no active branch route.",
                            "route_target_ref": "",
                            "evidence_refs": [],
                            "exclusion_notes": ["Contradicted by the bounded review."],
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "research_question.contract.md").write_text("# Research question\n", encoding="utf-8")
        (self.topic_root / "followup_subtopics.jsonl").write_text(
            json.dumps(
                {
                    "child_topic_slug": "demo-topic--followup--route",
                    "parent_topic_slug": self.topic_slug,
                    "status": "spawned",
                    "query": "Recover the neighboring route before reintegration.",
                    "return_packet_path": str(
                        self.kernel_root
                        / "runtime"
                        / "topics"
                        / "demo-topic--followup--route"
                        / "followup_return_packet.json"
                    ),
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (
            self.kernel_root
            / "runtime"
            / "topics"
            / "demo-topic--followup--route"
            / "followup_return_packet.json"
        ).parent.mkdir(parents=True, exist_ok=True)
        (
            self.kernel_root
            / "runtime"
            / "topics"
            / "demo-topic--followup--route"
            / "followup_return_packet.json"
        ).write_text(
            json.dumps(
                {
                    "return_packet_version": 1,
                    "child_topic_slug": "demo-topic--followup--route",
                    "parent_topic_slug": self.topic_slug,
                    "parent_run_id": "run-001",
                    "receipt_id": "receipt:demo-followup",
                    "query": "Recover the neighboring route before reintegration.",
                    "parent_gap_ids": ["open_gap:demo-followup"],
                    "parent_followup_task_ids": ["followup_source_task:demo-followup"],
                    "reentry_targets": ["definition:demo-followup"],
                    "supporting_regression_question_ids": ["regression_question:demo-followup"],
                    "source_id": "paper:demo-followup",
                    "arxiv_id": "9876.54321",
                    "expected_return_route": "L0->L1->L3->L4->L2",
                    "acceptable_return_shapes": ["recovered_units", "resolved_gap_update", "still_unresolved_packet"],
                    "required_output_artifacts": ["candidate_ledger_or_recovered_units"],
                    "unresolved_return_statuses": ["pending_reentry", "returned_with_gap", "returned_unresolved"],
                    "return_status": "pending_reentry",
                    "reintegration_requirements": {
                        "must_write_back_parent_gaps": True,
                        "must_update_reentry_targets": True,
                        "must_not_patch_parent_directly": True,
                        "requires_child_topic_summary": True,
                    },
                    "updated_at": "2026-04-12T00:00:00+00:00",
                    "updated_by": "test",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "topic_dashboard.md").write_text("# Topic dashboard\n", encoding="utf-8")
        (self.topic_root / "runtime_protocol.generated.md").write_text("# Runtime protocol\n", encoding="utf-8")
        (self.topic_root / "resume.md").write_text("# Resume\n", encoding="utf-8")
        (self.topic_root / "validation_review_bundle.active.json").write_text(
            json.dumps(
                {
                    "status": "ready",
                    "summary": "Validation is ready and no blockers remain.",
                    "candidate_ids": ["candidate:demo"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "validation_review_bundle.active.md").write_text("# Review bundle\n", encoding="utf-8")
        (self.topic_root / "topic_completion.json").write_text(
            json.dumps(
                {
                    "status": "promoted",
                    "summary": "At least one candidate has been promoted.",
                    "promotion_ready_candidate_ids": ["candidate:demo"],
                    "blocked_candidate_ids": [],
                    "open_gap_ids": [],
                    "blockers": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "topic_completion.md").write_text("# Topic completion\n", encoding="utf-8")
        (self.topic_root / "topic_skill_projection.active.json").write_text(
            json.dumps(
                {
                    "status": "available",
                    "summary": "Reusable projection is available.",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "topic_skill_projection.active.md").write_text("# Projection\n", encoding="utf-8")
        (self.topic_root / "transition_history.json").write_text(
            json.dumps(
                {
                    "topic_slug": self.topic_slug,
                    "status": "recorded",
                    "transition_count": 2,
                    "forward_count": 1,
                    "backtrack_count": 1,
                    "hold_count": 0,
                    "demotion_count": 1,
                    "latest_transition": {
                        "event_kind": "promotion_rejected",
                        "from_layer": "L4",
                        "to_layer": "L3",
                        "reason": "Validation contradiction returned the topic to L3.",
                    },
                    "latest_demotion": {
                        "event_kind": "promotion_rejected",
                        "from_layer": "L4",
                        "to_layer": "L3",
                        "reason": "Validation contradiction returned the topic to L3.",
                    },
                    "rows": [
                        {
                            "event_kind": "promoted",
                            "from_layer": "L4",
                            "to_layer": "L2",
                            "reason": "Promotion completed.",
                        },
                        {
                            "event_kind": "promotion_rejected",
                            "from_layer": "L4",
                            "to_layer": "L3",
                            "reason": "Validation contradiction returned the topic to L3.",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "transition_history.md").write_text("# Transition history\n", encoding="utf-8")
        (self.topic_root / "promotion_gate.json").write_text(
            json.dumps(
                {
                    "status": "approved",
                    "candidate_id": "candidate:demo",
                    "approval_change_kind": "approved_with_modifications",
                    "human_modifications": [
                        {
                            "field": "statement",
                            "change": "Narrowed to weak coupling only.",
                            "reason": "The original submission overstated the regime.",
                            "recorded_at": "2026-03-28T00:00:00+00:00",
                            "recorded_by": "test",
                        }
                    ],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "promotion_gate.md").write_text("# Promotion gate\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_materialize_topic_replay_bundle_writes_outputs(self) -> None:
        result = materialize_topic_replay_bundle(self.kernel_root, self.topic_slug)
        payload = result["payload"]

        self.assertEqual(payload["kind"], "topic_replay_bundle")
        self.assertEqual(payload["overview"]["title"], "Demo Topic")
        self.assertEqual(payload["current_position"]["resume_stage"], "L2")
        self.assertEqual(payload["current_position"]["latest_demotion_reason"], "Validation contradiction returned the topic to L3.")
        self.assertEqual(payload["current_position"]["approval_change_kind"], "approved_with_modifications")
        self.assertEqual(payload["current_position"]["leading_competing_hypothesis_id"], "hypothesis:demo-leading")
        self.assertEqual(payload["current_position"]["active_branch_hypothesis_id"], "hypothesis:demo-leading")
        self.assertEqual(payload["current_position"]["active_local_action_summary"], "Keep the leading route on the current topic branch.")
        self.assertEqual(payload["current_position"]["route_transition_gate_status"], "blocked")
        self.assertEqual(payload["current_position"]["route_transition_intent_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_receipt_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_resolution_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_discrepancy_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_repair_status"], "none_required")
        self.assertEqual(payload["current_position"]["route_transition_escalation_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_clearance_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_followthrough_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_resumption_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_commitment_status"], "none")
        self.assertEqual(payload["current_position"]["route_transition_authority_status"], "none")
        self.assertEqual(payload["conclusions"]["topic_completion_status"], "promoted")
        self.assertEqual(payload["conclusions"]["promoted_units"], ["theorem:demo-result"])
        self.assertEqual(payload["conclusions"]["demotion_count"], 1)
        self.assertEqual(payload["conclusions"]["human_modification_count"], 1)
        self.assertEqual(payload["conclusions"]["competing_hypothesis_count"], 3)
        self.assertEqual(payload["conclusions"]["excluded_competing_hypothesis_count"], 1)
        self.assertEqual(payload["conclusions"]["followup_branch_hypothesis_count"], 1)
        self.assertEqual(payload["conclusions"]["parked_route_count"], 1)
        self.assertEqual(payload["conclusions"]["reentry_ready_count"], 0)
        self.assertEqual(payload["conclusions"]["route_transition_gate_status"], "blocked")
        self.assertEqual(payload["conclusions"]["route_transition_intent_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_receipt_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_resolution_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_discrepancy_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_repair_status"], "none_required")
        self.assertEqual(payload["conclusions"]["route_transition_escalation_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_clearance_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_followthrough_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_resumption_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_commitment_status"], "none")
        self.assertEqual(payload["conclusions"]["route_transition_authority_status"], "none")
        self.assertEqual(payload["route_activation"]["active_local_hypothesis_id"], "hypothesis:demo-leading")
        self.assertEqual(payload["route_activation"]["parked_route_count"], 1)
        self.assertEqual(len(payload["route_activation"]["followup_obligations"]), 1)
        self.assertEqual(payload["route_reentry"]["reentry_ready_count"], 0)
        self.assertEqual(len(payload["route_reentry"]["followup_routes"]), 1)
        self.assertEqual(payload["route_reentry"]["followup_routes"][0]["reentry_status"], "waiting")
        self.assertEqual(payload["route_transition_gate"]["transition_status"], "blocked")
        self.assertEqual(payload["route_transition_gate"]["gate_kind"], "no_handoff_candidate")
        self.assertEqual(payload["route_transition_intent"]["intent_status"], "none")
        self.assertEqual(payload["route_transition_receipt"]["receipt_status"], "none")
        self.assertEqual(payload["route_transition_resolution"]["resolution_status"], "none")
        self.assertEqual(payload["route_transition_discrepancy"]["discrepancy_status"], "none")
        self.assertEqual(payload["route_transition_repair"]["repair_status"], "none_required")
        self.assertEqual(payload["route_transition_escalation"]["escalation_status"], "none")
        self.assertEqual(payload["route_transition_clearance"]["clearance_status"], "none")
        self.assertEqual(payload["route_transition_followthrough"]["followthrough_status"], "none")
        self.assertEqual(payload["route_transition_resumption"]["resumption_status"], "none")
        self.assertEqual(payload["route_transition_commitment"]["commitment_status"], "none")
        self.assertEqual(payload["route_transition_authority"]["authority_status"], "none")
        self.assertTrue(any(step["label"] == "Current dashboard" for step in payload["reading_path"]))
        self.assertTrue(any(step["label"] == "Follow-up subtopics" for step in payload["reading_path"]))
        self.assertTrue(any(step["label"] == "Promotion gate" for step in payload["reading_path"]))
        self.assertTrue(any(step["label"] == "Transition history" for step in payload["reading_path"]))
        self.assertIn("topic_dashboard_path", payload["authoritative_artifacts"])
        self.assertIn("followup_subtopics_path", payload["authoritative_artifacts"])
        self.assertIn("promotion_gate_path", payload["authoritative_artifacts"])
        self.assertIn("transition_history_path", payload["authoritative_artifacts"])
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())

        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("# Topic Replay Bundle", markdown)
        self.assertIn("## Reading Path", markdown)
        self.assertIn("theorem:demo-result", markdown)
        self.assertIn("Validation contradiction returned the topic to L3.", markdown)
        self.assertIn("approved_with_modifications", markdown)
        self.assertIn("## Competing Hypotheses", markdown)
        self.assertIn("Demo leading route", markdown)
        self.assertIn("route=`followup_subtopic`", markdown)
        self.assertIn("## Route Activation", markdown)
        self.assertIn("Follow-up obligations", markdown)
        self.assertIn("## Route Re-entry", markdown)
        self.assertIn("## Route Transition Gate", markdown)
        self.assertIn("## Route Transition Intent", markdown)
        self.assertIn("## Route Transition Receipt", markdown)
        self.assertIn("## Route Transition Resolution", markdown)
        self.assertIn("## Route Transition Discrepancy", markdown)
        self.assertIn("## Route Transition Repair", markdown)
        self.assertIn("## Route Transition Escalation", markdown)
        self.assertIn("## Route Transition Clearance", markdown)
        self.assertIn("## Route Transition Followthrough", markdown)
        self.assertIn("## Route Transition Resumption", markdown)
        self.assertIn("## Route Transition Commitment", markdown)
        self.assertIn("## Route Transition Authority", markdown)
        self.assertIn("expected return route", markdown)

    def test_materialize_topic_replay_bundle_reports_missing_artifacts_honestly(self) -> None:
        (self.topic_root / "validation_review_bundle.active.md").unlink()
        (self.topic_root / "topic_skill_projection.active.md").unlink()
        (self.topic_root / "transition_history.md").unlink()
        (self.topic_root / "promotion_gate.md").unlink()

        result = materialize_topic_replay_bundle(self.kernel_root, self.topic_slug)
        missing = set(result["payload"]["missing_artifacts"])
        self.assertIn("validation_review_bundle_path", missing)
        self.assertIn("topic_skill_projection_path", missing)
        self.assertIn("transition_history_path", missing)
        self.assertIn("promotion_gate_path", missing)

    def test_materialize_topic_replay_bundle_surfaces_l0_source_handoff(self) -> None:
        (self.topic_root / "topic_synopsis.json").write_text(
            json.dumps(
                {
                    "topic_slug": self.topic_slug,
                    "title": "Demo Topic",
                    "question": "What should the operator do next?",
                    "lane": "formal_theory",
                    "human_request": "Recover sources first.",
                    "next_action_summary": "Return to L0 source expansion.",
                    "open_gap_summary": "Source recovery remains active.",
                    "runtime_focus": {
                        "l0_source_handoff": {
                            "status": "needs_sources",
                            "summary": "Start with discovery, then fall back to direct arXiv registration when an id is known.",
                            "primary_path": "source-layer/scripts/discover_and_register.py",
                            "primary_when": "Use when you have a topic query rather than a fixed arXiv id.",
                            "alternate_entries": [
                                {
                                    "path": "source-layer/scripts/register_arxiv_source.py",
                                    "when": "Use when the arXiv id is already known."
                                },
                                {
                                    "path": "intake/ARXIV_FIRST_SOURCE_INTAKE.md",
                                    "when": "Use for the exact command forms and intake workflow."
                                }
                            ]
                        }
                    }
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        result = materialize_topic_replay_bundle(self.kernel_root, self.topic_slug)
        payload = result["payload"]
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")

        self.assertEqual(payload["current_position"]["l0_source_handoff_summary"], "Start with discovery, then fall back to direct arXiv registration when an id is known.")
        self.assertEqual(payload["l0_source_handoff"]["primary_path"], "source-layer/scripts/discover_and_register.py")
        self.assertEqual(payload["l0_source_handoff"]["alternate_entries"][0]["path"], "source-layer/scripts/register_arxiv_source.py")
        self.assertEqual(payload["l0_source_handoff"]["alternate_entries"][1]["path"], "intake/ARXIV_FIRST_SOURCE_INTAKE.md")
        self.assertIn("## L0 source handoff", markdown)
        self.assertIn("source-layer/scripts/discover_and_register.py", markdown)
        self.assertIn("source-layer/scripts/register_arxiv_source.py", markdown)
        self.assertIn("intake/ARXIV_FIRST_SOURCE_INTAKE.md", markdown)
