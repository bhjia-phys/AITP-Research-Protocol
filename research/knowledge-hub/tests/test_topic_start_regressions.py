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
        runtime_root = self.kernel_root / "topics" / topic_slug / "runtime"
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

        source_root = self.kernel_root / "topics" / topic_slug / "L0"
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
        source_root = self.kernel_root / "topics" / topic_slug / "L0"
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
        self.assertEqual(l1_source_intake["method_specificity_rows"][0]["method_family"], "formal_derivation")
        self.assertEqual(l1_source_intake["method_specificity_rows"][0]["specificity_tier"], "high")

    def test_distill_from_sources_uses_deepxiv_brief_only_in_discussion_mode(self) -> None:
        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "paper:bounded-closure-2401-00001",
                    "source_type": "paper",
                    "title": "Bounded Closure Route",
                    "summary": "Summary fallback should stay deferred in discussion mode because it only mentions strong coupling.",
                    "provenance": {
                        "abs_url": "https://example.org/bounded-closure",
                        "deepxiv_tldr": "We assume the bounded closure remains valid in the weak coupling limit.",
                        "deepxiv_sections": [
                            {
                                "name": "Introduction",
                                "idx": 0,
                                "tldr": "At zero temperature, the paper becomes theorem-facing.",
                                "token_count": 120,
                            },
                            {
                                "name": "Results",
                                "idx": 4,
                                "tldr": "A proof sketch closes the first theorem route.",
                                "token_count": 180,
                            },
                        ],
                    },
                }
            ],
            "demo-topic",
            runtime_mode="discussion",
        )

        self.assertIn("bounded closure remains valid", distilled["distilled_initial_idea"])
        self.assertNotIn("zero temperature", distilled["distilled_initial_idea"])
        self.assertNotIn("strong coupling", distilled["distilled_initial_idea"])
        l1_source_intake = distilled["distilled_l1_source_intake"]
        self.assertEqual(l1_source_intake["reading_depth_rows"][0]["reading_depth"], "abstract_only")
        self.assertEqual(l1_source_intake["reading_depth_rows"][0]["basis"], "deepxiv_brief")
        self.assertIn("weak coupling", json.dumps(l1_source_intake["regime_rows"]))
        self.assertNotIn("zero temperature", json.dumps(l1_source_intake["regime_rows"]))
        self.assertNotIn("strong coupling", json.dumps(l1_source_intake["regime_rows"]))

    def test_distill_from_sources_uses_deepxiv_head_and_relevant_sections_in_verify_mode(self) -> None:
        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "paper:bounded-closure-2401-00002",
                    "source_type": "paper",
                    "title": "Bounded Closure Route",
                    "summary": "Summary fallback should stay deferred in verify mode when section TLDRs are available.",
                    "provenance": {
                        "abs_url": "https://example.org/bounded-closure-verify",
                        "deepxiv_tldr": "This paper studies the bounded closure route.",
                        "deepxiv_sections": [
                            {
                                "name": "Introduction",
                                "idx": 0,
                                "tldr": "The paper frames the theorem-facing route.",
                                "token_count": 120,
                            },
                            {
                                "name": "Setup",
                                "idx": 1,
                                "tldr": "We assume the closure remains valid in the weak coupling limit.",
                                "token_count": 160,
                            },
                            {
                                "name": "Results",
                                "idx": 4,
                                "tldr": "At zero temperature, the proof closes the first bounded theorem route.",
                                "token_count": 180,
                            },
                        ],
                    },
                }
            ],
            "demo-topic",
            runtime_mode="verify",
        )

        self.assertIn("[Results]", distilled["distilled_initial_idea"])
        self.assertNotIn("Summary fallback should stay deferred", distilled["distilled_initial_idea"])
        l1_source_intake = distilled["distilled_l1_source_intake"]
        self.assertEqual(l1_source_intake["reading_depth_rows"][0]["reading_depth"], "skim")
        self.assertEqual(l1_source_intake["reading_depth_rows"][0]["basis"], "deepxiv_sections")
        self.assertIn("weak coupling", json.dumps(l1_source_intake["regime_rows"]))
        self.assertIn("zero temperature", json.dumps(l1_source_intake["regime_rows"]))
        self.assertEqual(l1_source_intake["method_specificity_rows"][0]["method_family"], "formal_derivation")

    def test_distill_from_sources_collects_source_concept_graph_into_l1_source_intake(self) -> None:
        topic_slug = "demo-topic-graph"
        source_root = self.kernel_root / "topics" / topic_slug / "L0"
        source_root.mkdir(parents=True, exist_ok=True)
        source_slug = "paper-topological-order-and-anyon-condensation-2401-00001"
        source_dir = source_root / "sources" / source_slug
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "snapshot.md").write_text(
            "# Snapshot\n\n"
            "## Preview\n"
            "Topological order supports the bounded condensation route.\n",
            encoding="utf-8",
        )
        (source_dir / "concept_graph.json").write_text(
            json.dumps(
                {
                    "kind": "source_concept_graph",
                    "graph_version": 1,
                    "topic_slug": topic_slug,
                    "source_id": "paper:topological-order-and-anyon-condensation-2401-00001",
                    "source_json_path": f"topics/{topic_slug}/L0/sources/{source_slug}/source.json",
                    "generated_at": "2026-04-13T00:00:00+08:00",
                    "generated_by": "test",
                    "provider": "override_json",
                    "nodes": [
                        {
                            "node_id": "concept:topological-order",
                            "label": "Topological order",
                            "node_type": "concept",
                            "confidence_tier": "EXTRACTED",
                            "confidence_score": 0.95,
                            "evidence_refs": [f"topics/{topic_slug}/L0/sources/{source_slug}/source.json"],
                            "notes": "",
                        }
                    ],
                    "edges": [],
                    "hyperedges": [],
                    "communities": [
                        {
                            "community_id": "community-topological-order",
                            "label": "Topological order cluster",
                            "node_ids": ["concept:topological-order"],
                        }
                    ],
                    "god_nodes": ["concept:topological-order"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        distilled = self.service._distill_from_sources(
            [
                {
                    "source_id": "paper:topological-order-and-anyon-condensation-2401-00001",
                    "source_type": "paper",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "Topological order supports the bounded condensation route.",
                    "locator": {
                        "concept_graph_path": f"topics/{topic_slug}/L0/sources/{source_slug}/concept_graph.json",
                    },
                    "provenance": {
                        "abs_url": "https://example.org/topological-order",
                    },
                }
            ],
            topic_slug,
        )

        concept_graph = distilled["distilled_l1_source_intake"]["concept_graph"]
        self.assertEqual(concept_graph["nodes"][0]["node_id"], "concept:topological-order")
        self.assertEqual(concept_graph["communities"][0]["label"], "Topological order cluster")
        self.assertEqual(concept_graph["god_nodes"][0]["node_id"], "concept:topological-order")

    def test_source_backed_topic_start_surfaces_contradiction_and_notation_tension(self) -> None:
        topic_slug = "demo-topic"
        runtime_root, thesis_path = self._write_source_backed_topic(topic_slug=topic_slug)
        source_root = self.kernel_root / "topics" / topic_slug / "L0"
        second_path = self.root / "inputs" / "demo-note.md"
        second_path.write_text(
            "# Conflicting follow-up note\n\n"
            "We assume the same closure target only in the strong coupling limit.\n"
            "K denotes the diagonal generator.\n",
            encoding="utf-8",
        )
        source_rows = [
            {
                "source_id": "thesis:demo-source",
                "source_type": "thesis",
                "title": "Diagonal Gauge Freedom in scRPA",
                "summary": (
                    "We assume fractional occupations remain bounded in the weak coupling limit at zero temperature. "
                    "H denotes the diagonal generator."
                ),
                "provenance": {
                    "absolute_path": str(thesis_path),
                },
            },
            {
                "source_id": "local_note:demo-conflict",
                "source_type": "local_note",
                "title": "Conflicting diagonal-generator note",
                "summary": (
                    "We assume the same closure target only in the strong coupling limit. "
                    "K denotes the diagonal generator."
                ),
                "provenance": {
                    "absolute_path": str(second_path),
                },
            },
        ]
        (source_root / "source_index.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in source_rows) + "\n",
            encoding="utf-8",
        )
        conflict_snapshot_root = source_root / "sources" / "local_note-demo-conflict"
        conflict_snapshot_root.mkdir(parents=True, exist_ok=True)
        conflict_snapshot_root.joinpath("snapshot.md").write_text(
            "# Snapshot\n\n"
            "## Preview\n"
            "We assume the same closure target only in the strong coupling limit.\n"
            "K denotes the diagonal generator.\n",
            encoding="utf-8",
        )

        payload = self.service.ensure_topic_shell_surfaces(
            topic_slug=topic_slug,
            updated_by="aitp-cli",
        )

        l1_source_intake = payload["research_question_contract"]["l1_source_intake"]
        self.assertTrue(l1_source_intake["contradiction_candidates"])
        self.assertTrue(l1_source_intake["notation_tension_candidates"])
        self.assertTrue(l1_source_intake["method_specificity_rows"])
        self.assertTrue(any(row["detail"] == "strong coupling vs weak coupling" for row in l1_source_intake["contradiction_candidates"]))
        self.assertTrue(any(row["existing_symbol"] == "H" and row["incoming_symbol"] == "K" for row in l1_source_intake["notation_tension_candidates"]))
        note_text = Path(payload["research_question_contract_note_path"]).read_text(encoding="utf-8")
        self.assertIn("## Contradiction candidates", note_text)
        self.assertIn("## Notation-alignment tension", note_text)
        self.assertIn("## Method specificity", note_text)


if __name__ == "__main__":
    unittest.main()
