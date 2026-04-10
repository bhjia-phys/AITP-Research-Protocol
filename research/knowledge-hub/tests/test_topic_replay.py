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
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.topic_root / "research_question.contract.md").write_text("# Research question\n", encoding="utf-8")
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

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_materialize_topic_replay_bundle_writes_outputs(self) -> None:
        result = materialize_topic_replay_bundle(self.kernel_root, self.topic_slug)
        payload = result["payload"]

        self.assertEqual(payload["kind"], "topic_replay_bundle")
        self.assertEqual(payload["overview"]["title"], "Demo Topic")
        self.assertEqual(payload["current_position"]["resume_stage"], "L2")
        self.assertEqual(payload["conclusions"]["topic_completion_status"], "promoted")
        self.assertEqual(payload["conclusions"]["promoted_units"], ["theorem:demo-result"])
        self.assertTrue(any(step["label"] == "Current dashboard" for step in payload["reading_path"]))
        self.assertIn("topic_dashboard_path", payload["authoritative_artifacts"])
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())

        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("# Topic Replay Bundle", markdown)
        self.assertIn("## Reading Path", markdown)
        self.assertIn("theorem:demo-result", markdown)

    def test_materialize_topic_replay_bundle_reports_missing_artifacts_honestly(self) -> None:
        (self.topic_root / "validation_review_bundle.active.md").unlink()
        (self.topic_root / "topic_skill_projection.active.md").unlink()

        result = materialize_topic_replay_bundle(self.kernel_root, self.topic_slug)
        missing = set(result["payload"]["missing_artifacts"])
        self.assertIn("validation_review_bundle_path", missing)
        self.assertIn("topic_skill_projection_path", missing)
