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


class HypothesisRouteActivationContractTests(unittest.TestCase):
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
                "summary": "The active route stays local while parked routes remain explicit.",
            },
        )
        self._write_json(
            "topics/demo-topic/runtime/interaction_state.json",
            {
                "human_request": "Keep the weak-coupling route local while the parked routes stay explicit.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:active-route",
                    "decision_source": "heuristic",
                },
            },
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/action_queue.jsonl",
            [
                {
                    "action_id": "action:demo-topic:active-route",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Continue the weak-coupling route on the active topic and keep parked routes visible.",
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
                "question": "How should the current local route and parked routes activate on the active topic?",
                "scope": ["Keep route activation bounded to the current topic family."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-spawn or auto-schedule branches."],
                "context_intake": ["Human request: make route activation explicit."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep current-route action and parked-route obligations explicit."],
                "open_ambiguities": ["The parked routes remain relevant but should not replace the active local route."],
                "competing_hypotheses": [
                    {
                        "hypothesis_id": "hypothesis:weak-coupling",
                        "label": "Weak-coupling route",
                        "status": "leading",
                        "summary": "The weak-coupling route remains the active local branch.",
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
                        "summary": "The symmetry-breaking route stays parked in deferred storage.",
                        "route_kind": "deferred_buffer",
                        "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                        "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                        "evidence_refs": ["note:demo-symmetry-gap"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:prior-work",
                        "label": "Prior-work route",
                        "status": "watch",
                        "summary": "The prior-work route stays parked on a follow-up branch.",
                        "route_kind": "followup_subtopic",
                        "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic.",
                        "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                        "evidence_refs": ["note:demo-prior-work-gap"],
                        "exclusion_notes": [],
                    },
                ],
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": ["Current-route action and parked-route obligations."],
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep route activation durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route activation directly."],
                "forbidden_proxies": ["Do not infer route activation from prose-only context."],
                "uncertainty_markers": ["Only one route should stay local."],
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
                        "entry_id": "buffer:demo-symmetry",
                        "candidate_id": "candidate:demo-symmetry",
                        "status": "buffered",
                        "summary": "The symmetry-breaking route stays parked until broader evidence arrives.",
                    }
                ],
            },
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/followup_subtopics.jsonl",
            [
                {
                    "child_topic_slug": "demo-topic--followup--prior-work",
                    "parent_topic_slug": "demo-topic",
                    "status": "spawned",
                    "query": "Recover the missing prior-work distinction on a bounded child route.",
                }
            ],
        )

    def test_status_and_replay_surface_route_activation(self) -> None:
        self._seed_demo_topic()

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic")
        replay_payload = replay_result["payload"]

        route_activation = status_payload["active_research_contract"]["route_activation"]
        self.assertEqual(route_activation["active_local_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertIn("Continue the weak-coupling route", route_activation["active_local_action_summary"])
        self.assertTrue(route_activation["active_local_action_ref"].endswith("action_queue.jsonl"))
        self.assertEqual(route_activation["parked_route_count"], 2)
        self.assertEqual(len(route_activation["deferred_obligations"]), 1)
        self.assertEqual(len(route_activation["followup_obligations"]), 1)

        self.assertEqual(replay_payload["route_activation"]["active_local_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertEqual(replay_payload["conclusions"]["parked_route_count"], 2)
        self.assertIn("Continue the weak-coupling route", replay_payload["current_position"]["active_local_action_summary"])

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Route activation", runtime_protocol_note)
        self.assertIn("Active local action", runtime_protocol_note)
        self.assertIn("## Route Activation", replay_note)
        self.assertIn("Deferred obligations", replay_note)


if __name__ == "__main__":
    unittest.main()
