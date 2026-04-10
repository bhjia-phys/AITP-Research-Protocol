from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import AITPService


class TopicStartRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.kernel_root.mkdir(parents=True)
        self.repo_root.mkdir(parents=True)
        (self.kernel_root / "canonical").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, self.kernel_root / "schemas" / schema_path.name)
        runtime_bundle_schema = (
            self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        )
        shutil.copyfile(
            runtime_bundle_schema,
            self.kernel_root / "runtime" / "schemas" / runtime_bundle_schema.name,
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_source_backed_topic(
        self,
        *,
        topic_slug: str = "demo-topic",
        human_request: str = "Please inspect this thesis and take it from there.",
    ) -> tuple[Path, Path]:
        runtime_root = self.kernel_root / "runtime" / "topics" / topic_slug
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "interaction_state.json").write_text(
            json.dumps(
                {
                    "human_request": human_request,
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "topic_state.json").write_text(
            json.dumps(
                {
                    "topic_slug": topic_slug,
                    "latest_run_id": "2026-03-31-demo",
                    "resume_stage": "L3",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime_root / "action_queue.jsonl").write_text(
            json.dumps(
                {
                    "action_id": "action:demo-topic:thesis",
                    "status": "pending",
                    "action_type": "proof_review",
                    "summary": "Extract the first bounded proof obligation from the thesis source.",
                    "auto_runnable": False,
                    "queue_source": "heuristic",
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        source_root = self.kernel_root / "source-layer" / "topics" / topic_slug
        source_root.mkdir(parents=True, exist_ok=True)
        thesis_path = self.root / "inputs" / "demo-thesis.tex"
        thesis_path.parent.mkdir(parents=True, exist_ok=True)
        thesis_path.write_text(
            "% Comment-only preamble\n"
            "% Another ignored line\n"
            "\\section{Diagonal gauge freedom}\n"
            "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature.\n"
            "We analyze whether fractional occupations give a bounded closure for diagonal gauge redundancy in scRPA.\n",
            encoding="utf-8",
        )

        source_row = {
            "source_id": "thesis:demo-source",
            "source_type": "thesis",
            "title": "Diagonal Gauge Freedom in scRPA",
            "summary": (
                "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature. "
                "We derive a bounded closure target and outline the first proof obligation for diagonal gauge redundancy."
            ),
            "provenance": {
                "absolute_path": str(thesis_path),
            },
        }
        (source_root / "source_index.jsonl").write_text(
            json.dumps(source_row, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

        snapshot_root = source_root / "sources" / "thesis-demo-source"
        snapshot_root.mkdir(parents=True, exist_ok=True)
        snapshot_root.joinpath("snapshot.md").write_text(
            "# Snapshot\n\n"
            "## Preview\n"
            "% Comment-only preview line\n"
            "% [REV] [Novel diagonal closure target]\n",
            encoding="utf-8",
        )
        return runtime_root, thesis_path

    def test_source_backed_topic_start_prefers_distilled_idea_packet(self) -> None:
        self._write_source_backed_topic()

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        idea_packet = payload["idea_packet"]
        explainability = payload["topic_state_explainability"]
        research_question_contract = payload["research_question_contract"]
        validation_contract = payload["validation_contract"]

        self.assertEqual(idea_packet["status"], "approved_for_execution")
        self.assertIn("Diagonal gauge freedom", idea_packet["initial_idea"])
        self.assertNotEqual(
            idea_packet["initial_idea"],
            "Please inspect this thesis and take it from there.",
        )
        self.assertIn("Novel diagonal closure target", idea_packet["novelty_target"])
        self.assertIn("Extract the core thesis claim", idea_packet["first_validation_route"])
        self.assertIn("Diagonal gauge freedom", research_question_contract["question"])
        self.assertNotEqual(
            research_question_contract["question"],
            "Please inspect this thesis and take it from there.",
        )
        self.assertIn("Extract the core thesis claim", validation_contract["verification_focus"])
        self.assertEqual(
            explainability["current_route_choice"]["selected_action_summary"],
            "Extract the first bounded proof obligation from the thesis source.",
        )
        self.assertIn("l1_source_intake", research_question_contract)
        self.assertTrue(research_question_contract["l1_source_intake"]["assumption_rows"])
        self.assertTrue(research_question_contract["l1_source_intake"]["regime_rows"])
        self.assertTrue(research_question_contract["l1_source_intake"]["reading_depth_rows"])
        self.assertIn(
            "Extract the first bounded proof obligation from the thesis source.",
            explainability["why_this_topic_is_here"],
        )
        self.assertEqual(explainability["active_human_need"]["status"], "none")

    def test_explicit_idea_packet_fields_override_source_distillation(self) -> None:
        runtime_root, _ = self._write_source_backed_topic(
            human_request="Continue with the thesis topic.",
        )
        (runtime_root / "idea_packet.json").write_text(
            json.dumps(
                {
                    "initial_idea": "Human-defined idea statement.",
                    "novelty_target": "Human-defined novelty target.",
                    "non_goals": ["Do not enter numerics yet."],
                    "first_validation_route": "Human-defined first validation route.",
                    "initial_evidence_bar": "Human-defined evidence bar.",
                    "status": "approved_for_execution",
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

        idea_packet = payload["idea_packet"]
        self.assertEqual(idea_packet["initial_idea"], "Human-defined idea statement.")
        self.assertEqual(idea_packet["novelty_target"], "Human-defined novelty target.")
        self.assertEqual(
            idea_packet["first_validation_route"],
            "Human-defined first validation route.",
        )
        self.assertEqual(idea_packet["status"], "approved_for_execution")

    def test_distill_from_sources_uses_summary_fallback_for_numerical_sources(self) -> None:
        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "code:tfim-benchmark",
                    "source_type": "code",
                    "title": "Tiny TFIM Benchmark",
                    "summary": (
                        "We show the exact diagonalization baseline reproduces the first finite-size benchmark. "
                        "This establishes the observable normalization before larger runs."
                    ),
                    "provenance": {
                        "absolute_path": str(self.root / "inputs" / "missing-benchmark.md"),
                    },
                }
            ],
            "demo-topic",
        )

        self.assertEqual(distilled["distilled_lane"], "numerical")
        self.assertIn("Tiny TFIM Benchmark", distilled["distilled_initial_idea"])
        self.assertIn("exact diagonalization baseline", distilled["distilled_initial_idea"])
        self.assertIn("exact diagonalization baseline reproduces", distilled["distilled_novelty_target"])
        self.assertIn("baseline benchmark", distilled["distilled_first_validation_route"])

    def test_distill_from_sources_prefers_snapshot_preview_over_original_and_summary(self) -> None:
        topic_slug = "demo-topic"
        source_root = self.kernel_root / "source-layer" / "topics" / topic_slug
        source_root.mkdir(parents=True, exist_ok=True)

        original_path = self.root / "inputs" / "snapshot-priority.tex"
        original_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_text(
            "\\section{Original fallback}\n"
            "Original fallback text should not win when snapshot preview is available.\n",
            encoding="utf-8",
        )

        snapshot_root = source_root / "sources" / "paper-demo-source"
        snapshot_root.mkdir(parents=True, exist_ok=True)
        snapshot_root.joinpath("snapshot.md").write_text(
            "# Snapshot\n\n"
            "## Preview\n"
            "Snapshot preview text should win over original and summary fallbacks.\n\n"
            "## Notes\n"
            "The snapshot preview is already usable.\n",
            encoding="utf-8",
        )

        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "paper:demo-source",
                    "source_type": "paper",
                    "title": "Snapshot Priority Paper",
                    "summary": "Summary fallback text should lose to the snapshot preview.",
                    "provenance": {
                        "absolute_path": str(original_path),
                    },
                }
            ],
            topic_slug,
        )

        self.assertEqual(distilled["distilled_lane"], "formal_theory")
        self.assertIn("Snapshot preview text should win", distilled["distilled_initial_idea"])
        self.assertNotIn("Original fallback text should not win", distilled["distilled_initial_idea"])
        self.assertNotIn("Summary fallback text should lose", distilled["distilled_initial_idea"])

    def test_distill_from_sources_extracts_l1_assumption_regime_and_reading_depth_structure(self) -> None:
        topic_slug = "demo-topic"
        self._write_source_backed_topic(topic_slug=topic_slug)

        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "thesis:demo-source",
                    "source_type": "thesis",
                    "title": "Diagonal Gauge Freedom in scRPA",
                    "summary": (
                        "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature. "
                        "We derive a bounded closure target and outline the first proof obligation."
                    ),
                    "provenance": {
                        "absolute_path": str(self.root / "inputs" / "demo-thesis.tex"),
                    },
                }
            ],
            topic_slug,
        )

        l1_source_intake = distilled["distilled_l1_source_intake"]
        self.assertEqual(l1_source_intake["source_count"], 1)
        self.assertEqual(l1_source_intake["assumption_rows"][0]["source_id"], "thesis:demo-source")
        self.assertIn("fractional occupations remain bounded", l1_source_intake["assumption_rows"][0]["assumption"])
        self.assertIn("weak coupling", json.dumps(l1_source_intake["regime_rows"]))
        self.assertIn("zero temperature", json.dumps(l1_source_intake["regime_rows"]))
        self.assertEqual(l1_source_intake["reading_depth_rows"][0]["reading_depth"], "full_read")


if __name__ == "__main__":
    unittest.main()
