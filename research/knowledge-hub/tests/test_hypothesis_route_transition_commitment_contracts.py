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


class HypothesisRouteTransitionCommitmentContractTests(unittest.TestCase):
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

    def _write_text(self, relative_path: str, text: str) -> None:
        path = self.kernel_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _write_jsonl(self, relative_path: str, rows: list[dict]) -> None:
        path = self.kernel_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n",
            encoding="utf-8",
        )

    def _seed_demo_topic(self, *, topic_slug: str, route_mode: str) -> None:
        next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
        if route_mode == "current_weak":
            action_summary = (
                "Stay on the weak-coupling route for the current bounded step while keeping the "
                "symmetry-breaking route visible."
            )
            question = "Is any route transition commitment currently applicable?"
            observables = ["No route transition commitment is required."]
            resume_reason = "Hold the current weak-coupling route while the intended handoff remains unresolved."
            seed_recorded_receipt = False
        else:
            action_summary = "Yield to the symmetry-breaking route now that the bounded handoff has been enacted."
            question = "Has the resumed route become the durable committed bounded lane yet?"
            observables = ["Route transition commitment should stay explicit on the active topic surface."]
            resume_reason = "Activated hypothesis:symmetry-breaking from the deferred buffer after the bounded handoff."
            seed_recorded_receipt = True

        competing_hypotheses: list[dict] = []
        if route_mode == "current_weak":
            competing_hypotheses.extend(
                [
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
                    },
                    {
                        "hypothesis_id": "hypothesis:symmetry-breaking",
                        "label": "Symmetry-breaking route",
                        "status": "active",
                        "summary": "The symmetry-breaking route is the bounded handoff target.",
                        "route_kind": "deferred_buffer",
                        "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                        "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                        "evidence_refs": ["paper:demo-source-b"],
                        "exclusion_notes": [],
                    },
                ]
            )
        elif route_mode == "deferred_target":
            competing_hypotheses.append(
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "leading",
                    "summary": "The symmetry-breaking route is the bounded handoff target.",
                    "route_kind": "deferred_buffer",
                    "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                    "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                    "evidence_refs": ["paper:demo-source-b"],
                    "exclusion_notes": [],
                }
            )
        elif route_mode == "active_target_deferred":
            competing_hypotheses.append(
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "The symmetry-breaking route is active but its durable target still points through the deferred buffer lane.",
                    "route_kind": "current_topic",
                    "route_target_summary": "The route is locally active, but its durable target ref still points through the deferred buffer projection.",
                    "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                    "evidence_refs": ["paper:demo-source-b"],
                    "exclusion_notes": [],
                }
            )
        else:
            competing_hypotheses.append(
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "The symmetry-breaking route is already the committed local lane.",
                    "route_kind": "current_topic",
                    "route_target_summary": "Keep the symmetry-breaking route on the current topic branch.",
                    "route_target_ref": f"topics/{topic_slug}/runtime/action_queue.jsonl",
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
                "summary": "The active topic should surface route transition commitment explicitly.",
                "resume_reason": resume_reason,
                "pointers": {"next_action_decision_note_path": next_action_note},
            },
        )
        self._write_text(next_action_note, "# Next action\n\n" + action_summary + "\n")
        self._write_json(
            f"topics/{topic_slug}/runtime/interaction_state.json",
            {
                "human_request": "Show the bounded route transition commitment.",
                "decision_surface": {
                    "selected_action_id": f"action:{topic_slug}:route-transition-commitment",
                    "decision_source": "heuristic",
                    "next_action_decision_note_path": next_action_note,
                },
                "action_queue_surface": {"queue_source": "heuristic"},
            },
        )
        self._write_jsonl(
            f"topics/{topic_slug}/runtime/action_queue.jsonl",
            [
                {
                    "action_id": f"action:{topic_slug}:route-transition-commitment",
                    "status": "pending",
                    "action_type": "manual_followup",
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
                "scope": ["Keep route transition commitment bounded to explicit resumption and route-state artifacts."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-commit or auto-dispatch route state in this slice."],
                "context_intake": ["Human request: surface the bounded route transition commitment."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep transition commitment explicit without mutating runtime state."],
                "open_ambiguities": ["The bounded route handoff may still need explicit durable commitment after resumption."],
                "competing_hypotheses": competing_hypotheses,
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": observables,
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep route transition commitment durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route transition commitment directly."],
                "forbidden_proxies": ["Do not infer route transition commitment from prose-only notes."],
                "uncertainty_markers": ["The bounded route handoff may still need explicit durable commitment after resumption."],
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
                        "reactivation_conditions": {"source_ids_any": ["paper:demo-source-b"]},
                        "reactivation_candidate": {
                            "candidate_id": "candidate:demo-symmetry-reactivated",
                            "summary": "Reactivated symmetry-breaking candidate.",
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
        if seed_recorded_receipt:
            target_ref = (
                f"topics/{topic_slug}/runtime/action_queue.jsonl"
                if route_mode == "current_target"
                else f"topics/{topic_slug}/runtime/deferred_candidates.json"
            )
            self._write_json(
                f"topics/{topic_slug}/runtime/transition_history.json",
                {
                    "topic_slug": topic_slug,
                    "status": "recorded",
                    "transition_count": 1,
                    "forward_count": 0,
                    "backtrack_count": 0,
                    "hold_count": 1,
                    "demotion_count": 0,
                    "latest_transition": {
                        "transition_id": f"transition:{topic_slug}:route-handoff",
                        "event_kind": "route_handoff_recorded",
                        "from_layer": "L3",
                        "to_layer": "L3",
                        "transition_kind": "boundary_hold",
                        "reason": "Recorded enactment of hypothesis:symmetry-breaking on the bounded route handoff.",
                        "evidence_refs": [target_ref],
                        "candidate_id": "",
                        "recorded_at": "2026-04-12T00:00:00+00:00",
                        "recorded_by": "test",
                    },
                    "latest_demotion": {},
                    "rows": [
                        {
                            "transition_id": f"transition:{topic_slug}:route-handoff",
                            "event_kind": "route_handoff_recorded",
                            "from_layer": "L3",
                            "to_layer": "L3",
                            "transition_kind": "boundary_hold",
                            "reason": "Recorded enactment of hypothesis:symmetry-breaking on the bounded route handoff.",
                            "evidence_refs": [target_ref],
                            "candidate_id": "",
                            "recorded_at": "2026-04-12T00:00:00+00:00",
                            "recorded_by": "test",
                        }
                    ],
                    "log_path": f"topics/{topic_slug}/runtime/transition_history.jsonl",
                    "path": f"topics/{topic_slug}/runtime/transition_history.json",
                    "note_path": f"topics/{topic_slug}/runtime/transition_history.md",
                },
            )
            self._write_text(
                f"topics/{topic_slug}/runtime/transition_history.md",
                "# Transition history\n\nRecorded enactment of hypothesis:symmetry-breaking.\n",
            )

    def test_no_commitment_when_no_resumption_is_active(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-no-commitment", route_mode="current_weak")
        status_payload = self.service.topic_status(topic_slug="demo-topic-no-commitment")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-no-commitment")["payload"]

        commitment = status_payload["active_research_contract"]["route_transition_commitment"]
        self.assertEqual(commitment["commitment_status"], "none")
        self.assertEqual(commitment["commitment_kind"], "none")
        self.assertEqual(replay_payload["route_transition_commitment"]["commitment_status"], "none")
        self.assertEqual(replay_payload["current_position"]["route_transition_commitment_status"], "none")
        self.assertEqual(replay_payload["conclusions"]["route_transition_commitment_status"], "none")

    def test_commitment_waits_while_resumption_is_not_ready(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-commitment-waiting", route_mode="deferred_target")
        status_payload = self.service.topic_status(topic_slug="demo-topic-commitment-waiting")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-commitment-waiting")["payload"]

        commitment = status_payload["active_research_contract"]["route_transition_commitment"]
        self.assertEqual(commitment["commitment_status"], "waiting_resumption")
        self.assertEqual(commitment["commitment_kind"], "resumption_not_ready")
        self.assertEqual(replay_payload["route_transition_commitment"]["commitment_status"], "waiting_resumption")

    def test_commitment_pending_when_route_is_active_but_still_deferred(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-commitment-pending", route_mode="active_target_deferred")
        status_payload = self.service.topic_status(topic_slug="demo-topic-commitment-pending")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-commitment-pending")["payload"]

        commitment = status_payload["active_research_contract"]["route_transition_commitment"]
        self.assertEqual(commitment["commitment_status"], "pending_commitment")
        self.assertEqual(commitment["commitment_kind"], "active_route_not_yet_committed")
        self.assertEqual(commitment["route_kind"], "current_topic")
        self.assertIn("deferred_candidates.json", commitment["route_target_ref"])
        self.assertEqual(replay_payload["route_transition_commitment"]["commitment_status"], "pending_commitment")

    def test_commitment_visible_when_route_is_current_topic(self) -> None:
        self._seed_demo_topic(topic_slug="demo-topic-commitment-committed", route_mode="current_target")
        status_payload = self.service.topic_status(topic_slug="demo-topic-commitment-committed")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-commitment-committed")["payload"]

        commitment = status_payload["active_research_contract"]["route_transition_commitment"]
        self.assertEqual(commitment["commitment_status"], "committed")
        self.assertEqual(commitment["commitment_kind"], "current_topic_committed")
        self.assertEqual(commitment["route_kind"], "current_topic")
        self.assertEqual(replay_payload["route_transition_commitment"]["commitment_status"], "committed")
        self.assertEqual(replay_payload["current_position"]["route_transition_commitment_status"], "committed")
        self.assertEqual(replay_payload["conclusions"]["route_transition_commitment_status"], "committed")


if __name__ == "__main__":
    unittest.main()
