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


class HypothesisRouteTransitionGateContractTests(unittest.TestCase):
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
            question = "Should the current local route stay local or yield to the primary handoff candidate?"
            observables = ["Stay-local versus yield-to-handoff transition gate."]
        elif request_checkpoint:
            action_type = "select_validation_route"
            action_summary = "Choose the validation route before yielding to the symmetry-breaking handoff candidate."
            question = "Which validation route should be confirmed before yielding to the primary handoff candidate?"
            observables = ["Checkpoint-gated yield-to-handoff transition."]
        else:
            action_type = "manual_followup"
            action_summary = "Yield to the symmetry-breaking route now that no active local route remains."
            question = "Should the runtime yield directly to the primary handoff candidate now that the local route is absent?"
            observables = ["Direct yield-to-handoff transition gate."]

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
                "summary": "The active topic should surface whether yielding is blocked, available, or checkpoint-gated.",
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
                "human_request": "Show the bounded route transition gate.",
                "decision_surface": {
                    "selected_action_id": f"action:{topic_slug}:route-transition-gate",
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
                    "action_id": f"action:{topic_slug}:route-transition-gate",
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
                "scope": ["Keep route transition gating bounded to explicit route choice and checkpoint artifacts."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-reactivate, auto-reintegrate, or auto-mutate route state."],
                "context_intake": ["Human request: surface the bounded route transition gate."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep transition-gate visibility explicit without mutating runtime state."],
                "open_ambiguities": ["The active gate may be blocked, available, or checkpoint-gated."],
                "competing_hypotheses": competing_hypotheses,
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": observables,
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep route transition gating durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route transition gating directly."],
                "forbidden_proxies": ["Do not infer route transition gating from prose-only notes."],
                "uncertainty_markers": ["The bounded route may still require an explicit checkpoint or remain blocked."],
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

    def test_blocked_transition_gate_surfaces_current_route_choice_gate(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-blocked",
            include_current_topic=True,
            request_checkpoint=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-blocked")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-blocked")
        replay_payload = replay_result["payload"]

        route_gate = status_payload["active_research_contract"]["route_transition_gate"]
        self.assertEqual(route_gate["transition_status"], "blocked")
        self.assertEqual(route_gate["choice_status"], "stay_local")
        self.assertEqual(route_gate["checkpoint_status"], "cancelled")
        self.assertEqual(route_gate["gate_kind"], "current_route_choice")
        self.assertEqual(route_gate["primary_handoff_candidate_id"], "hypothesis:symmetry-breaking")
        self.assertIn("next_action_decision.md", route_gate["gate_artifact_ref"])
        self.assertIn("stays local", route_gate["transition_summary"])

        self.assertEqual(replay_payload["route_transition_gate"]["transition_status"], "blocked")
        self.assertEqual(replay_payload["current_position"]["route_transition_gate_status"], "blocked")
        self.assertEqual(replay_payload["conclusions"]["route_transition_gate_status"], "blocked")

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Route transition gate", runtime_protocol_note)
        self.assertIn("Transition status: `blocked`", runtime_protocol_note)
        self.assertIn("## Route Transition Gate", replay_note)

    def test_available_transition_gate_surfaces_direct_yield_lane(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-available",
            include_current_topic=False,
            request_checkpoint=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-available")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-available")
        replay_payload = replay_result["payload"]

        route_choice = status_payload["active_research_contract"]["route_choice"]
        route_gate = status_payload["active_research_contract"]["route_transition_gate"]
        self.assertEqual(route_choice["choice_status"], "yield_to_handoff")
        self.assertEqual(route_gate["transition_status"], "available")
        self.assertEqual(route_gate["choice_status"], "yield_to_handoff")
        self.assertEqual(route_gate["gate_kind"], "handoff_candidate_ready")
        self.assertEqual(route_gate["primary_handoff_candidate_id"], "hypothesis:symmetry-breaking")
        self.assertIn("deferred_candidates.json", route_gate["transition_target_ref"])

        self.assertEqual(replay_payload["route_transition_gate"]["transition_status"], "available")
        self.assertEqual(replay_payload["current_position"]["route_transition_gate_status"], "available")
        self.assertEqual(replay_payload["conclusions"]["route_transition_gate_status"], "available")

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        self.assertIn("Transition status: `available`", runtime_protocol_note)

    def test_checkpoint_required_transition_gate_surfaces_operator_checkpoint_artifact(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-checkpoint",
            include_current_topic=False,
            request_checkpoint=True,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-checkpoint")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-checkpoint")
        replay_payload = replay_result["payload"]

        self.assertEqual(status_payload["operator_checkpoint"]["status"], "requested")
        route_gate = status_payload["active_research_contract"]["route_transition_gate"]
        self.assertEqual(route_gate["transition_status"], "checkpoint_required")
        self.assertEqual(route_gate["choice_status"], "yield_to_handoff")
        self.assertEqual(route_gate["checkpoint_status"], "requested")
        self.assertEqual(route_gate["gate_kind"], "operator_checkpoint")
        self.assertIn("operator_checkpoint.active.md", route_gate["gate_artifact_ref"])

        self.assertEqual(replay_payload["route_transition_gate"]["transition_status"], "checkpoint_required")
        self.assertEqual(replay_payload["current_position"]["route_transition_gate_status"], "checkpoint_required")
        self.assertEqual(replay_payload["conclusions"]["route_transition_gate_status"], "checkpoint_required")

        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Transition status: `checkpoint_required`", replay_note)


if __name__ == "__main__":
    unittest.main()
