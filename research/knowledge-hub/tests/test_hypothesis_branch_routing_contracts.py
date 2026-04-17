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


class HypothesisBranchRoutingContractTests(unittest.TestCase):
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
                "summary": "One hypothesis stays local while others route to parked surfaces.",
                "pointers": {
                    "innovation_direction_path": "topics/demo-topic/runtime/innovation_direction.md",
                    "innovation_decisions_path": "topics/demo-topic/runtime/innovation_decisions.jsonl",
                },
            },
        )
        self._write_json(
            "topics/demo-topic/runtime/interaction_state.json",
            {
                "human_request": "Keep the weak-coupling route local, park one route, and branch one route outward.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:route-hypotheses",
                    "decision_source": "heuristic",
                },
            },
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/action_queue.jsonl",
            [
                {
                    "action_id": "action:demo-topic:route-hypotheses",
                    "status": "pending",
                    "action_type": "manual_followup",
                    "summary": "Review the current hypothesis routing and keep the weak-coupling route on the active topic.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                }
            ],
        )
        (self.kernel_root / "topics" / "demo-topic" / "runtime" / "innovation_direction.md").parent.mkdir(
            parents=True, exist_ok=True
        )
        (self.kernel_root / "topics" / "demo-topic" / "runtime" / "innovation_direction.md").write_text(
            "# Innovation direction\n\nKeep the weak-coupling route on the active topic.\n",
            encoding="utf-8",
        )
        self._write_jsonl(
            "topics/demo-topic/runtime/innovation_decisions.jsonl",
            [
                {
                    "decision": "continue",
                    "summary": "Keep the weak-coupling route on the active topic and route neighboring hypotheses explicitly.",
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
                "question": "Which bounded route should remain local, which should park, and which should branch?",
                "scope": ["Keep the routing decision bounded to the current topic family."],
                "assumptions": ["Only durable runtime artifacts count as progress."],
                "non_goals": ["Do not auto-spawn or auto-adjudicate branches."],
                "context_intake": ["Human request: keep branch intent explicit per hypothesis."],
                "source_basis_refs": ["paper:demo-source"],
                "interpretation_focus": ["Route each live hypothesis explicitly."],
                "open_ambiguities": ["The neighboring routes remain relevant but should not all stay on the same active branch."],
                "competing_hypotheses": [
                    {
                        "hypothesis_id": "hypothesis:weak-coupling",
                        "label": "Weak-coupling route",
                        "status": "leading",
                        "summary": "The weak-coupling explanation remains the active local route.",
                        "route_kind": "current_topic",
                        "route_target_summary": "Keep the weak-coupling route on the current topic branch under the current steering note.",
                        "route_target_ref": "topics/demo-topic/runtime/innovation_direction.md",
                        "evidence_refs": ["paper:demo-source", "note:demo-weak-coupling-check"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:symmetry-breaking",
                        "label": "Symmetry-breaking route",
                        "status": "active",
                        "summary": "The symmetry-breaking route should stay parked until broader evidence arrives.",
                        "route_kind": "deferred_buffer",
                        "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                        "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                        "evidence_refs": ["note:demo-symmetry-gap"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:prior-work",
                        "label": "Prior-work distinction route",
                        "status": "watch",
                        "summary": "A prior-work distinction should stay live on a separate follow-up branch.",
                        "route_kind": "followup_subtopic",
                        "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic rather than widening the current topic.",
                        "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                        "evidence_refs": ["note:demo-prior-work-gap"],
                        "exclusion_notes": [],
                    },
                    {
                        "hypothesis_id": "hypothesis:strong-closure",
                        "label": "Immediate strong-closure route",
                        "status": "excluded",
                        "summary": "The stronger closure claim is currently ruled out.",
                        "route_kind": "excluded",
                        "route_target_summary": "Keep the stronger closure route excluded with no active branch.",
                        "route_target_ref": "",
                        "evidence_refs": [],
                        "exclusion_notes": ["Contradicted by the bounded validation note."],
                    },
                ],
                "formalism_and_notation": ["Stay with the bounded demo notation."],
                "observables": ["Hypothesis route kind and target summary."],
                "target_claims": ["candidate:demo-claim"],
                "deliverables": ["Keep hypothesis routing durable on the active topic surface."],
                "acceptance_tests": ["Runtime status and replay expose the route of each live hypothesis."],
                "forbidden_proxies": ["Do not infer branch routing from prose-only context."],
                "uncertainty_markers": ["Only one route should stay local on the active branch."],
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

    def test_docs_and_schemas_expose_hypothesis_branch_routing(self) -> None:
        kernel_readme = (self.package_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.package_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.package_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")
        research_schema = json.loads(
            (self.workspace_repo_root / "schemas" / "research-question.schema.json").read_text(encoding="utf-8")
        )
        runtime_schema = json.loads(
            (self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(encoding="utf-8")
        )

        self.assertIn("run_hypothesis_branch_routing_acceptance.py", kernel_readme)
        self.assertIn("run_hypothesis_branch_routing_acceptance.py", runtime_readme)
        self.assertIn("run_hypothesis_branch_routing_acceptance.py", runbook)
        self.assertIn("route_kind", research_schema["properties"]["competing_hypotheses"]["items"]["properties"])
        self.assertIn("route_target_summary", research_schema["properties"]["competing_hypotheses"]["items"]["properties"])
        self.assertIn("active_branch_hypothesis_id", runtime_schema["properties"]["active_research_contract"]["properties"])
        self.assertIn("deferred_branch_hypothesis_ids", runtime_schema["properties"]["active_research_contract"]["properties"])
        self.assertIn("followup_branch_hypothesis_ids", runtime_schema["properties"]["active_research_contract"]["properties"])

    def test_status_and_replay_surface_branch_routing_explicitly(self) -> None:
        self._seed_demo_topic()

        status_payload = self.service.topic_status(topic_slug="demo-topic")
        replay_result = materialize_topic_replay_bundle(self.kernel_root, "demo-topic")
        replay_payload = replay_result["payload"]

        active_research = status_payload["active_research_contract"]
        self.assertEqual(active_research["active_branch_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertEqual(active_research["deferred_branch_hypothesis_ids"], ["hypothesis:symmetry-breaking"])
        self.assertEqual(active_research["followup_branch_hypothesis_ids"], ["hypothesis:prior-work"])
        self.assertEqual(replay_payload["current_position"]["active_branch_hypothesis_id"], "hypothesis:weak-coupling")
        self.assertEqual(replay_payload["conclusions"]["deferred_branch_hypothesis_count"], 1)
        self.assertEqual(replay_payload["conclusions"]["followup_branch_hypothesis_count"], 1)
        self.assertEqual(status_payload["topic_completion"]["followup_subtopic_count"], 1)
        self.assertTrue((self.kernel_root / "topics" / "demo-topic" / "runtime" / "deferred_candidates.json").exists())

        research_note = (
            self.kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
        ).read_text(encoding="utf-8")
        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"]).read_text(encoding="utf-8")
        replay_note = Path(replay_result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("route=`current_topic`", research_note)
        self.assertIn("route=`deferred_buffer`", research_note)
        self.assertIn("route=`followup_subtopic`", research_note)
        self.assertIn("innovation_direction.md", research_note)
        self.assertIn("Active branch hypothesis", runtime_protocol_note)
        self.assertIn("Deferred branch hypotheses", runtime_protocol_note)
        self.assertIn("Follow-up-route count", replay_note)
        self.assertIn("hypothesis:prior-work", replay_note)


if __name__ == "__main__":
    unittest.main()
