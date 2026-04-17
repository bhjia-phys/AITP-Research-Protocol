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
from knowledge_hub.topic_replay import materialize_topic_replay_bundle


class HypothesisRouteReentryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.kernel_root.mkdir(parents=True)
        self.repo_root.mkdir(parents=True)
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, self.kernel_root / "schemas" / schema_path.name)
        shutil.copyfile(
            self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json",
            self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json",
        )
        shutil.copytree(
            self.package_root / "runtime" / "scripts",
            self.kernel_root / "runtime" / "scripts",
            dirs_exist_ok=True,
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_json(self, relative_path: str, payload: dict) -> None:
        path = self.kernel_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    def _write_jsonl(self, relative_path: str, rows: list[dict]) -> None:
        path = self.kernel_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n",
            encoding="utf-8",
        )

    def _seed_demo_topic(self) -> None:
        self._write_json(
            "topics/demo-topic/runtime/topic_state.json",
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "research_mode": "formal_derivation",
                "summary": "Parked routes should expose re-entry conditions instead of staying opaque.",
            },
        )
        self._write_json(
            "topics/demo-topic/runtime/interaction_state.json",
            {
                "human_request": "Show when parked routes can come back and when a child route still owes a return packet.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:route-reentry",
                    "decision_source": "heuristic",
                },
            },
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/action_queue.jsonl",
            [
                {
                    "action_id": "action:demo-topic:route-reentry",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Keep the active route local while reviewing parked-route re-entry conditions.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                }
            ],
        )
        self._write_json(
            "topics/demo-topic/runtime/research_question.contract.json",
            {
                "contract_version": 1,
                "question_id": "research_question:demo-topic",
                "title": "Demo Topic",
                "topic_slug": "demo-topic",
                "status": "active",
                "template_mode": "formal_theory",
                "research_mode": "formal_derivation",
                "question": "When should parked routes re-enter the active topic?",
                "scope": ["Keep route re-entry bounded to explicit deferred and follow-up contracts."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-reactivate candidates or patch the parent topic."],
                "context_intake": ["Human request: surface parked-route re-entry conditions."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep deferred reactivation and follow-up return readiness explicit."],
                "open_ambiguities": ["A parked route may still be waiting even when it remains scientifically relevant."],
                "competing_hypotheses": [
                    {
                        "hypothesis_id": "hypothesis:weak-coupling",
                        "label": "Weak-coupling route",
                        "status": "leading",
                        "summary": "The weak-coupling route remains active on the parent topic.",
                        "route_kind": "current_topic",
                        "route_target_summary": "Keep the weak-coupling route on the current topic branch.",
                        "route_target_ref": "topics/demo-topic/runtime/research_question.contract.md",
                        "evidence_refs": ["paper:demo-source"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:symmetry-breaking",
                        "label": "Symmetry-breaking route",
                        "status": "active",
                        "summary": "The symmetry-breaking route is parked in the deferred buffer until a cited source lands.",
                        "route_kind": "deferred_buffer",
                        "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                        "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                        "evidence_refs": ["paper:demo-source-b"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:prior-work",
                        "label": "Prior-work route",
                        "status": "watch",
                        "summary": "The prior-work route stays on a child follow-up lane until it returns bounded evidence.",
                        "route_kind": "followup_subtopic",
                        "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic.",
                        "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                        "evidence_refs": ["note:demo-prior-work-gap"],
                        "exclusion_notes": [],
                    },
                ],
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": ["Deferred reactivation and follow-up return readiness."],
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep parked-route re-entry durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route re-entry directly."],
                "forbidden_proxies": ["Do not infer re-entry state from prose-only notes."],
                "uncertainty_markers": ["Only parked routes with explicit contracts can be treated as re-entry-ready."],
                "target_layers": ["L1", "L3", "L4", "L2"],
            },
        )
        self._write_json(
            "topics/demo-topic/runtime/deferred_candidates.json",
            {
                "buffer_version": 1,
                "topic_slug": "demo-topic",
                "updated_at": "2026-04-12T00:00:00+00:00",
                "updated_by": "test",
                "entries": [
                    {
                        "entry_id": "deferred:demo-symmetry",
                        "source_candidate_id": "candidate:demo-symmetry",
                        "title": "Symmetry-breaking route",
                        "summary": "Park the symmetry-breaking route until the cited comparison source lands.",
                        "reason": "Current evidence is still too thin for parent-topic reintegration.",
                        "status": "buffered",
                        "reactivation_conditions": {
                            "source_ids_any": ["paper:demo-source-b"]
                        },
                        "reactivation_candidate": {
                            "candidate_id": "candidate:demo-symmetry-reactivated",
                            "summary": "Reactivated symmetry-breaking candidate."
                        },
                    }
                ],
            },
        )
        self._write_jsonl(
            "topics/demo-topic/L0/source_index.jsonl",
            [
                {
                    "source_id": "paper:demo-source-b",
                    "title": "Demo Source B",
                    "summary": "The cited comparison source required for the symmetry-breaking route is now present.",
                }
            ],
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/followup_subtopics.jsonl",
            [
                {
                    "child_topic_slug": "demo-topic--followup--prior-work",
                    "parent_topic_slug": "demo-topic",
                    "status": "spawned",
                    "query": "Recover the missing prior-work distinction on a bounded child route.",
                    "return_packet_path": str(
                        self.kernel_root
                        / "topics"
                        / "demo-topic--followup--prior-work"
                        / "runtime"
                        / "followup_return_packet.json"
                    ),
                }
            ],
        )
        self._write_json(
            "topics/demo-topic--followup--prior-work/runtime/followup_return_packet.json",
            {
                "return_packet_version": 1,
                "child_topic_slug": "demo-topic--followup--prior-work",
                "parent_topic_slug": "demo-topic",
                "parent_run_id": "run-001",
                "receipt_id": "receipt:demo-prior-work",
                "query": "Recover the missing prior-work distinction on a bounded child route.",
                "parent_gap_ids": ["open_gap:prior-work"],
                "parent_followup_task_ids": ["followup_source_task:prior-work"],
                "reentry_targets": ["definition:demo-prior-work"],
                "supporting_regression_question_ids": ["regression_question:prior-work"],
                "source_id": "paper:demo-prior-work",
                "arxiv_id": "1234.56789",
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
        )

    def test_status_and_replay_surface_route_reentry(self) -> None:
        self._seed_demo_topic()

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic")
        replay_payload = replay_result["payload"]

        route_reentry = status_payload["active_research_contract"]["route_reentry"]
        self.assertEqual(route_reentry["reentry_ready_count"], 1)
        self.assertEqual(len(route_reentry["deferred_routes"]), 1)
        self.assertEqual(len(route_reentry["followup_routes"]), 1)
        self.assertEqual(route_reentry["deferred_routes"][0]["reentry_status"], "reentry_ready")
        self.assertIn("source ids any", route_reentry["deferred_routes"][0]["condition_summary"])
        self.assertEqual(route_reentry["followup_routes"][0]["reentry_status"], "waiting")
        self.assertIn("expected return route", route_reentry["followup_routes"][0]["condition_summary"])

        self.assertEqual(replay_payload["route_reentry"]["reentry_ready_count"], 1)
        self.assertEqual(replay_payload["conclusions"]["reentry_ready_count"], 1)
        self.assertEqual(replay_payload["current_position"]["reentry_ready_count"], 1)

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Route re-entry", runtime_protocol_note)
        self.assertIn("reentry_status=`reentry_ready`", runtime_protocol_note)
        self.assertIn("## Route Re-entry", replay_note)
        self.assertIn("expected return route", replay_note)


if __name__ == "__main__":
    unittest.main()
