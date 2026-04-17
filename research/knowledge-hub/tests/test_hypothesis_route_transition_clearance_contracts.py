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


class HypothesisRouteTransitionClearanceContractTests(unittest.TestCase):
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

    def _seed_demo_topic(
        self,
        *,
        topic_slug: str,
        include_current_topic: bool,
        checkpoint_trigger: bool,
    ) -> None:
        next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
        if include_current_topic:
            action_summary = (
                "Stay on the weak-coupling route for the current bounded step while keeping the "
                "symmetry-breaking route visible."
            )
            question = "Is any route transition clearance currently applicable?"
            observables = ["No route transition clearance is required."]
            resume_reason = "Hold the current weak-coupling route while the intended handoff remains unresolved."
            seed_recorded_receipt = False
        else:
            action_summary = "Yield to the symmetry-breaking route now that the bounded handoff has been enacted."
            if checkpoint_trigger:
                action_summary = (
                    "A contradiction remains unresolved, so yield to the symmetry-breaking route only after"
                    " explicit operator adjudication."
                )
            question = "Has the bounded route transition escalation been cleared yet?"
            observables = ["Route transition clearance should stay explicit on the active topic surface."]
            resume_reason = "Activated hypothesis:symmetry-breaking from the deferred buffer after the bounded handoff."
            seed_recorded_receipt = True

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
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": "active" if include_current_topic else "leading",
                "summary": "The symmetry-breaking route is the bounded handoff target.",
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
                "summary": "The active topic should surface route transition clearance explicitly.",
                "resume_reason": resume_reason,
                "pointers": {
                    "next_action_decision_note_path": next_action_note
                },
            },
        )
        self._write_text(next_action_note, "# Next action\n\n" + action_summary + "\n")
        self._write_json(
            f"topics/{topic_slug}/runtime/interaction_state.json",
            {
                "human_request": "Show the bounded route transition clearance.",
                "decision_surface": {
                    "selected_action_id": f"action:{topic_slug}:route-transition-clearance",
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
                    "action_id": f"action:{topic_slug}:route-transition-clearance",
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
                "scope": ["Keep route transition clearance bounded to explicit escalation and checkpoint artifacts."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-open, auto-answer, or auto-close checkpoints in this slice."],
                "context_intake": ["Human request: surface the bounded route transition clearance."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Keep transition clearance explicit without mutating runtime state."],
                "open_ambiguities": ["The bounded route handoff may still require checkpoint-mediated release."],
                "competing_hypotheses": competing_hypotheses,
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": observables,
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep route transition clearance durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose route transition clearance directly."],
                "forbidden_proxies": ["Do not infer route transition clearance from prose-only notes."],
                "uncertainty_markers": ["The bounded route handoff may still need explicit checkpoint release."],
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
        if seed_recorded_receipt:
            target_ref = f"topics/{topic_slug}/runtime/deferred_candidates.json"
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

    def _mark_checkpoint_answered(self, topic_slug: str) -> None:
        first_status = self.service.topic_status(topic_slug=topic_slug)
        checkpoint = first_status["operator_checkpoint"]
        self.assertEqual(checkpoint["status"], "requested")
        checkpoint_path = self.kernel_root / "topics" / topic_slug / "runtime" / "operator_checkpoint.active.json"
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        payload["status"] = "answered"
        payload["active"] = False
        payload["answer"] = "Proceed with bounded route follow-through."
        payload["answered_at"] = "2026-04-12T00:05:00+00:00"
        payload["answered_by"] = "test"
        payload["updated_at"] = "2026-04-12T00:05:00+00:00"
        payload["updated_by"] = "test"
        checkpoint_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    def test_no_clearance_when_no_escalation_is_active(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-no-clearance",
            include_current_topic=True,
            checkpoint_trigger=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-no-clearance")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-no-clearance")["payload"]

        clearance = status_payload["active_research_contract"]["route_transition_clearance"]
        self.assertEqual(clearance["clearance_status"], "none")
        self.assertEqual(clearance["clearance_kind"], "none")
        self.assertEqual(replay_payload["route_transition_clearance"]["clearance_status"], "none")
        self.assertEqual(replay_payload["current_position"]["route_transition_clearance_status"], "none")
        self.assertEqual(replay_payload["conclusions"]["route_transition_clearance_status"], "none")

    def test_clearance_awaits_checkpoint_when_escalation_is_only_recommended(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-clearance-awaiting",
            include_current_topic=False,
            checkpoint_trigger=False,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-clearance-awaiting")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-clearance-awaiting")["payload"]

        clearance = status_payload["active_research_contract"]["route_transition_clearance"]
        self.assertEqual(clearance["clearance_status"], "awaiting_checkpoint")
        self.assertEqual(clearance["clearance_kind"], "checkpoint_not_opened")
        self.assertEqual(clearance["escalation_status"], "checkpoint_recommended")
        self.assertEqual(replay_payload["route_transition_clearance"]["clearance_status"], "awaiting_checkpoint")

    def test_clearance_blocks_while_checkpoint_is_requested(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-clearance-blocked",
            include_current_topic=False,
            checkpoint_trigger=True,
        )

        status_payload = self.service.topic_status(topic_slug="demo-topic-clearance-blocked")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-clearance-blocked")["payload"]

        clearance = status_payload["active_research_contract"]["route_transition_clearance"]
        self.assertEqual(clearance["clearance_status"], "blocked_on_checkpoint")
        self.assertEqual(clearance["clearance_kind"], "checkpoint_requested")
        self.assertEqual(clearance["checkpoint_status"], "requested")
        self.assertEqual(clearance["checkpoint_kind"], "contradiction_adjudication")
        self.assertEqual(replay_payload["route_transition_clearance"]["clearance_status"], "blocked_on_checkpoint")

    def test_clearance_releases_after_checkpoint_is_answered(self) -> None:
        self._seed_demo_topic(
            topic_slug="demo-topic-clearance-cleared",
            include_current_topic=False,
            checkpoint_trigger=True,
        )
        self._mark_checkpoint_answered("demo-topic-clearance-cleared")

        status_payload = self.service.topic_status(topic_slug="demo-topic-clearance-cleared")
        replay_payload = materialize_topic_replay_bundle(self.kernel_root, "demo-topic-clearance-cleared")["payload"]

        clearance = status_payload["active_research_contract"]["route_transition_clearance"]
        self.assertEqual(clearance["clearance_status"], "cleared")
        self.assertEqual(clearance["clearance_kind"], "checkpoint_answered")
        self.assertEqual(clearance["checkpoint_status"], "answered")
        self.assertIn("transition_history", clearance["followthrough_ref"])
        self.assertEqual(replay_payload["route_transition_clearance"]["clearance_status"], "cleared")
        self.assertEqual(replay_payload["current_position"]["route_transition_clearance_status"], "cleared")
        self.assertEqual(replay_payload["conclusions"]["route_transition_clearance_status"], "cleared")


if __name__ == "__main__":
    unittest.main()
