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


class CompetingHypothesesContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.workspace_repo_root = self.package_root.parents[1]
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
                "summary": "Two bounded explanations remain live.",
            },
        )
        self._write_json(
            "topics/demo-topic/runtime/interaction_state.json",
            {
                "human_request": "Keep the competing hypotheses explicit while the bounded review continues.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:compare-hypotheses",
                    "decision_source": "heuristic",
                },
            },
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/action_queue.jsonl",
            [
                {
                    "action_id": "action:demo-topic:compare-hypotheses",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Compare the weak-coupling and symmetry-breaking explanations without collapsing the question yet.",
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
                "question": "Which bounded explanation currently leads for the demo topic?",
                "scope": ["Keep the comparison bounded to the current topic."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not overclaim whole-topic closure."],
                "context_intake": ["Human request: keep multiple explanations visible."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Track the bounded explanations explicitly."],
                "open_ambiguities": ["The two main explanations remain live."],
                "competing_hypotheses": [
                    {
                        "hypothesis_id": "hypothesis:weak-coupling",
                        "label": "Weak-coupling route",
                        "status": "leading",
                        "summary": "The weak-coupling explanation currently has the strongest bounded support.",
                        "evidence_refs": ["paper:demo-source", "note:demo-weak-coupling-check"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:symmetry-breaking",
                        "label": "Symmetry-breaking route",
                        "status": "active",
                        "summary": "A symmetry-breaking explanation remains plausible enough to stay live.",
                        "evidence_refs": ["note:demo-symmetry-gap"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:strong-closure",
                        "label": "Immediate strong-closure route",
                        "status": "excluded",
                        "summary": "The stronger closure claim is currently ruled out.",
                        "evidence_refs": [],
                        "exclusion_notes": ["Contradicted by the bounded validation note."],
                    },
                ],
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": ["Hypothesis status and evidence refs."],
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep the competing-hypotheses surface durable."],
                "acceptance_tests": ["Runtime status and replay expose the competing hypotheses."],
                "forbidden_proxies": ["Do not flatten the question into one prose-only answer."],
                "uncertainty_markers": ["More than one plausible answer remains live."],
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
                        "entry_id": "buffer:demo-wide-route",
                        "candidate_id": "candidate:demo-wide-route",
                        "status": "buffered",
                        "summary": "A wider route stays parked while the current question remains bounded.",
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
                    "query": "Recover one missing prior-work distinction before collapsing the active question.",
                }
            ],
        )

    def test_contract_docs_and_schemas_expose_competing_hypotheses(self) -> None:
        root_readme = (self.workspace_repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.package_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.package_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.package_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")
        research_schema = json.loads(
            (self.workspace_repo_root / "schemas" / "research-question.schema.json").read_text(encoding="utf-8")
        )
        runtime_schema = json.loads(
            (self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(encoding="utf-8")
        )

        self.assertIn("run_competing_hypotheses_acceptance.py", root_readme)
        self.assertIn("run_competing_hypotheses_acceptance.py", kernel_readme)
        self.assertIn("run_competing_hypotheses_acceptance.py", runtime_readme)
        self.assertIn("run_competing_hypotheses_acceptance.py", runbook)
        self.assertIn("competing_hypotheses", research_schema["properties"])
        self.assertIn(
            "competing_hypotheses",
            runtime_schema["properties"]["active_research_contract"]["properties"],
        )
        self.assertIn(
            "competing_hypothesis_count",
            runtime_schema["properties"]["active_research_contract"]["properties"],
        )

    def test_status_and_replay_surface_competing_hypotheses_without_hiding_other_lanes(self) -> None:
        self._seed_demo_topic()

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic")
        replay_payload = replay_result["payload"]

        self.assertEqual(status_payload["active_research_contract"]["competing_hypothesis_count"], 3)
        self.assertEqual(status_payload["active_research_contract"]["leading_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertTrue((self.kernel_root / "topics" / "demo-topic" / "runtime" / "deferred_candidates.json").exists())
        self.assertEqual(status_payload["topic_completion"]["followup_subtopic_count"], 1)
        self.assertEqual(replay_payload["conclusions"]["competing_hypothesis_count"], 3)
        self.assertEqual(replay_payload["conclusions"]["excluded_competing_hypothesis_count"], 1)
        self.assertEqual(
            replay_payload["current_position"]["leading_competing_hypothesis_id"],
            "hypothesis:weak-coupling",
        )
        self.assertTrue(any(step["label"] == "Question contract" for step in replay_payload["reading_path"]))

        research_note = (
            self.kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
        ).read_text(encoding="utf-8")
        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("## Competing hypotheses", research_note)
        self.assertIn("Weak-coupling route", research_note)
        self.assertIn("## Competing hypotheses", runtime_protocol_note)
        self.assertIn("## Competing Hypotheses", replay_note)
        self.assertIn("Immediate strong-closure route", replay_note)


if __name__ == "__main__":
    unittest.main()
