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


class HypothesisRouteTransitionIntentContractTests(unittest.TestCase):
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

    def _seed_demo_topic(
        self,
        *,
        topic_slug: str,
        include_current_topic: bool,
        request_checkpoint: bool,
    ) -> None:
        next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
        if include_current_topic:
            action_type = "manual_followup"
            action_summary = (
                "Stay on the weak-coupling route for the current bounded step while keeping the "
                "symmetry-breaking route visible."
            )
            question = "What source-to-target transition intent should remain visible while the local route stays active?"
            observables = ["Proposed local-to-handoff transition intent."]
        elif request_checkpoint:
            action_type = "select_validation_route"
            action_summary = "Choose the validation route before yielding to the symmetry-breaking handoff candidate."
            question = "What transition intent is waiting behind the current validation-route checkpoint?"
            observables = ["Checkpoint-held route transition intent."]
        else:
            action_type = "manual_followup"
            action_summary = "Yield to the symmetry-breaking route now that no active local route remains."
            question = "What transition intent should be executed now that the local route is absent?"
            observables = ["Ready route transition intent."]

        competing_hypotheses: list[dict] = []
        if include_current_topic:
            competing_hypotheses.append(
                {
                    "hypothesis_id": "hypothesis:weak-coupling",
                    "label": "Weak-coupling route",
                    "status": "leading",
                    "summary": "The weak-coupling route remains the active local branch.",
                    "route_kind": "current_topic",
                    "route_target_summary": "Keep the weak-coupling route on the current topic branch.",
                    "route_target_ref": f"topics/{topic_slug}/runtime/action_queue.jsonl",
                    "evidence_refs": ["paper:demo-source"],
                    "exclusion_notes": [],
                }
            )
            symmetry_status = "active"
        else:
            symmetry_status = "leading"
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": symmetry_status,
                "summary": "The symmetry-breaking route is parked until the cited comparison source lands.",
                "route_kind": "deferred_buffer",
                "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                "evidence_refs": ["paper:demo-source-b"],
                "exclusion_notes": [],
            }
        )

        self._write_json(
            f"topics/{topic_slug}/runtime/topic_state.json",
            {
                "topic_slug": topic_slug,
                "latest_run_id": "run-001",
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "research_mode": "formal_derivation",
                "summary": "The active topic should surface route transition intent explicitly.",
                "pointers": {
                    "next_action_decision_note_path": next_action_note
                },
            },
        )
        next_action_path = self.kernel_root / next_action_note
        next_action_path.parent.mkdir(parents=True, exist_ok=True)
        next_action_path.write_text(
            "# Next action\n\n" + action_summary + "\n",
            encoding="utf-8",
        )
        self._write_json(
            f"topics/{topic_slug}/runtime/interaction_state.json",
            {
                "human_request": "Show the bounded route transition intent.",
                "decision_surface": {
                    "selected_action_id": f"action:{topic_slug}:route-transition-intent",
                    "decision_source": "heuristic",
                    "next_action_decision_note_path": next_action_note,
                },
                "action_queue_surface": {
                    "queue_source": "heuristic"
                },
            },
        )
        self._write_jsonl(
            f"topics/{topic_slug}/runtime/action_queue.jsonl",
            [
                {
                    "action_id": f"action:{topic_slug}:route-transition-intent",
                    "status": "pending",
                    "action_type": action_type,
                    "summary": action_summary,
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                }
            ],
        )
        self._write_json(
            f"topics/{topic_slug}/runtime/research_question.contract.json",
            {
                "contract_version": 1,
                "question_id": f"research_question:{topic_slug}",
                "title": "Demo Topic",
                "topic_slug": topic_slug,
                "status": "active",
                "template_mode": "formal_theory",
                "research_mode": "formal_derivation",
                "question": question,
                "scope": ["Keep route transition intent bounded to explicit route choice and transition-gate artifacts."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-reactivate, auto-reintegrate, or auto-mutate route state."],
                "context_intake": ["Human request: surface the bounded route transition intent."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep transition intent explicit without mutating runtime state."],
                "open_ambiguities": ["The active intent may be proposed, ready, or checkpoint-held."],
                "competing_hypotheses": competing_hypotheses,
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": observables,
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep route transition intent durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route transition intent directly."],
                "forbidden_proxies": ["Do not infer route transition intent from prose-only notes."],
                "uncertainty_markers": ["The bounded route may still keep the transition intent deferred behind a gate."],
                "target_layers": ["L1", "L3", "L4", "L2"],
            },
        )
        self._write_json(
            f"topics/{topic_slug}/runtime/deferred_candidates.json",
            {
                "buffer_version": 1,
                "topic_slug": topic_slug,
                "updated_at": "2026-04-12T00:00:00+00:00",
                "updated_by": "test",
                "entries": [
                    {
                        "entry_id": f"deferred:{topic_slug}:symmetry",
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
            f"topics/{topic_slug}/L0/source_index.jsonl",
            [
                {
                    "source_id": "paper:demo-source-b",
                    "title": "Demo Source B",
                    "summary": "The cited comparison source required for the symmetry-breaking route is now present.",
                }
            ],
        )

    def test_proposed_transition_intent_surfaces_source_and_target(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-proposed",
            include_current_topic=True,
            request_checkpoint=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-proposed")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-proposed")
        replay_payload = replay_result["payload"]

        route_intent = status_payload["active_research_contract"]["route_transition_intent"]
        self.assertEqual(route_intent["intent_status"], "proposed")
        self.assertEqual(route_intent["gate_status"], "blocked")
        self.assertEqual(route_intent["source_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertEqual(route_intent["target_hypothesis_id"], "hypothesis:symmetry-breaking")
        self.assertIn("next_action_decision.md", route_intent["source_route_ref"])
        self.assertIn("deferred_candidates.json", route_intent["target_route_ref"])

        self.assertEqual(replay_payload["route_transition_intent"]["intent_status"], "proposed")
        self.assertEqual(replay_payload["current_position"]["route_transition_intent_status"], "proposed")
        self.assertEqual(replay_payload["conclusions"]["route_transition_intent_status"], "proposed")

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Route transition intent", runtime_protocol_note)
        self.assertIn("Intent status: `proposed`", runtime_protocol_note)
        self.assertIn("## Route Transition Intent", replay_note)

    def test_ready_transition_intent_surfaces_target_lane(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-ready",
            include_current_topic=False,
            request_checkpoint=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-ready")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-ready")
        replay_payload = replay_result["payload"]

        route_intent = status_payload["active_research_contract"]["route_transition_intent"]
        self.assertEqual(route_intent["intent_status"], "ready")
        self.assertEqual(route_intent["gate_status"], "available")
        self.assertEqual(route_intent["source_hypothesis_id"], "")
        self.assertEqual(route_intent["target_hypothesis_id"], "hypothesis:symmetry-breaking")
        self.assertIn("deferred_candidates.json", route_intent["target_route_ref"])
        self.assertIn("no_active_local_route", route_intent["intent_summary"])

        self.assertEqual(replay_payload["route_transition_intent"]["intent_status"], "ready")
        self.assertEqual(replay_payload["current_position"]["route_transition_intent_status"], "ready")
        self.assertEqual(replay_payload["conclusions"]["route_transition_intent_status"], "ready")

    def test_checkpoint_held_transition_intent_surfaces_gate_artifact(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-checkpoint-held",
            include_current_topic=False,
            request_checkpoint=True,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-checkpoint-held")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-checkpoint-held")
        replay_payload = replay_result["payload"]

        route_intent = status_payload["active_research_contract"]["route_transition_intent"]
        self.assertEqual(route_intent["intent_status"], "checkpoint_held")
        self.assertEqual(route_intent["gate_status"], "checkpoint_required")
        self.assertEqual(route_intent["target_hypothesis_id"], "hypothesis:symmetry-breaking")
        self.assertIn("operator_checkpoint.active.md", route_intent["gate_artifact_ref"])

        self.assertEqual(replay_payload["route_transition_intent"]["intent_status"], "checkpoint_held")
        self.assertEqual(replay_payload["current_position"]["route_transition_intent_status"], "checkpoint_held")
        self.assertEqual(replay_payload["conclusions"]["route_transition_intent_status"], "checkpoint_held")


if __name__ == "__main__":
    unittest.main()
