from __future__ import annotations

import importlib.util
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module(module_name: str, relative_path: str):
    kernel_root = Path(__file__).resolve().parents[1]
    target_path = kernel_root / relative_path
    if str(target_path.parent) not in sys.path:
        sys.path.insert(0, str(target_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {target_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.knowledge_root = Path(self._tmpdir.name)
        (self.knowledge_root / "runtime").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "feedback").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "validation").mkdir(parents=True, exist_ok=True)
        (self.knowledge_root / "source-layer").mkdir(parents=True, exist_ok=True)
        self.orchestrate_topic = _load_module(
            "aitp_orchestrate_topic_test",
            "runtime/scripts/orchestrate_topic.py",
        )
        self.decide_next_action = _load_module(
            "aitp_decide_next_action_test",
            "runtime/scripts/decide_next_action.py",
        )
        self.closed_loop_v1 = _load_module(
            "aitp_closed_loop_v1_test",
            "runtime/scripts/closed_loop_v1.py",
        )
        self.sync_topic_state = _load_module(
            "aitp_sync_topic_state_test",
            "runtime/scripts/sync_topic_state.py",
        )
        self.l2_knowledge_report_acceptance = _load_module(
            "aitp_l2_knowledge_report_acceptance_test",
            "runtime/scripts/run_l2_knowledge_report_acceptance.py",
        )
        self.l1_vault_acceptance = _load_module(
            "aitp_l1_vault_acceptance_test",
            "runtime/scripts/run_l1_vault_acceptance.py",
        )
        self.statement_compilation_acceptance = _load_module(
            "aitp_statement_compilation_acceptance_test",
            "runtime/scripts/run_statement_compilation_acceptance.py",
        )
        self.l0_source_discovery_acceptance = _load_module(
            "aitp_l0_source_discovery_acceptance_test",
            "runtime/scripts/run_l0_source_discovery_acceptance.py",
        )
        self.l0_source_enrichment_acceptance = _load_module(
            "aitp_l0_source_enrichment_acceptance_test",
            "runtime/scripts/run_l0_source_enrichment_acceptance.py",
        )
        self.l0_source_concept_graph_acceptance = _load_module(
            "aitp_l0_source_concept_graph_acceptance_test",
            "runtime/scripts/run_l0_source_concept_graph_acceptance.py",
        )
        self.l1_concept_graph_acceptance = _load_module(
            "aitp_l1_concept_graph_acceptance_test",
            "runtime/scripts/run_l1_concept_graph_acceptance.py",
        )
        self.l1_assumption_depth_acceptance = _load_module(
            "aitp_l1_assumption_depth_acceptance_test",
            "runtime/scripts/run_l1_assumption_depth_acceptance.py",
        )
        self.l1_progressive_reading_acceptance = _load_module(
            "aitp_l1_progressive_reading_acceptance_test",
            "runtime/scripts/run_l1_progressive_reading_acceptance.py",
        )
        self.l1_graph_analysis_staging_acceptance = _load_module(
            "aitp_l1_graph_analysis_staging_acceptance_test",
            "runtime/scripts/run_l1_graph_analysis_staging_acceptance.py",
        )
        self.l1_graph_diff_runtime_acceptance = _load_module(
            "aitp_l1_graph_diff_runtime_acceptance_test",
            "runtime/scripts/run_l1_graph_diff_runtime_acceptance.py",
        )
        self.l1_graph_diff_staging_acceptance = _load_module(
            "aitp_l1_graph_diff_staging_acceptance_test",
            "runtime/scripts/run_l1_graph_diff_staging_acceptance.py",
        )
        self.l1_graph_community_bridge_acceptance = _load_module(
            "aitp_l1_graph_community_bridge_acceptance_test",
            "runtime/scripts/run_l1_graph_community_bridge_acceptance.py",
        )
        self.l1_graph_hyperedge_pattern_acceptance = _load_module(
            "aitp_l1_graph_hyperedge_pattern_acceptance_test",
            "runtime/scripts/run_l1_graph_hyperedge_pattern_acceptance.py",
        )
        self.l1_graph_obsidian_export_acceptance = _load_module(
            "aitp_l1_graph_obsidian_export_acceptance_test",
            "runtime/scripts/run_l1_graph_obsidian_export_acceptance.py",
        )
        self.l1_graph_obsidian_multicommunity_acceptance = _load_module(
            "aitp_l1_graph_obsidian_multicommunity_acceptance_test",
            "runtime/scripts/run_l1_graph_obsidian_multicommunity_acceptance.py",
        )
        self.l1_graph_obsidian_brain_bridge_acceptance = _load_module(
            "aitp_l1_graph_obsidian_brain_bridge_acceptance_test",
            "runtime/scripts/run_l1_graph_obsidian_brain_bridge_acceptance.py",
        )
        self.mode_enforcement_acceptance = _load_module(
            "aitp_mode_enforcement_acceptance_test",
            "runtime/scripts/run_mode_enforcement_acceptance.py",
        )
        self.transition_history_acceptance = _load_module(
            "aitp_transition_history_acceptance_test",
            "runtime/scripts/run_transition_history_acceptance.py",
        )
        self.human_modification_record_acceptance = _load_module(
            "aitp_human_modification_record_acceptance_test",
            "runtime/scripts/run_human_modification_record_acceptance.py",
        )
        self.competing_hypotheses_acceptance = _load_module(
            "aitp_competing_hypotheses_acceptance_test",
            "runtime/scripts/run_competing_hypotheses_acceptance.py",
        )
        self.hypothesis_branch_routing_acceptance = _load_module(
            "aitp_hypothesis_branch_routing_acceptance_test",
            "runtime/scripts/run_hypothesis_branch_routing_acceptance.py",
        )
        self.hypothesis_route_activation_acceptance = _load_module(
            "aitp_hypothesis_route_activation_acceptance_test",
            "runtime/scripts/run_hypothesis_route_activation_acceptance.py",
        )
        self.hypothesis_route_reentry_acceptance = _load_module(
            "aitp_hypothesis_route_reentry_acceptance_test",
            "runtime/scripts/run_hypothesis_route_reentry_acceptance.py",
        )
        self.hypothesis_route_handoff_acceptance = _load_module(
            "aitp_hypothesis_route_handoff_acceptance_test",
            "runtime/scripts/run_hypothesis_route_handoff_acceptance.py",
        )
        self.hypothesis_route_choice_acceptance = _load_module(
            "aitp_hypothesis_route_choice_acceptance_test",
            "runtime/scripts/run_hypothesis_route_choice_acceptance.py",
        )
        self.hypothesis_route_transition_gate_acceptance = _load_module(
            "aitp_hypothesis_route_transition_gate_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_gate_acceptance.py",
        )
        self.hypothesis_route_transition_intent_acceptance = _load_module(
            "aitp_hypothesis_route_transition_intent_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_intent_acceptance.py",
        )
        self.hypothesis_route_transition_receipt_acceptance = _load_module(
            "aitp_hypothesis_route_transition_receipt_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_receipt_acceptance.py",
        )
        self.hypothesis_route_transition_resolution_acceptance = _load_module(
            "aitp_hypothesis_route_transition_resolution_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_resolution_acceptance.py",
        )
        self.hypothesis_route_transition_discrepancy_acceptance = _load_module(
            "aitp_hypothesis_route_transition_discrepancy_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_discrepancy_acceptance.py",
        )
        self.hypothesis_route_transition_repair_acceptance = _load_module(
            "aitp_hypothesis_route_transition_repair_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_repair_acceptance.py",
        )
        self.hypothesis_route_transition_escalation_acceptance = _load_module(
            "aitp_hypothesis_route_transition_escalation_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_escalation_acceptance.py",
        )
        self.hypothesis_route_transition_clearance_acceptance = _load_module(
            "aitp_hypothesis_route_transition_clearance_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_clearance_acceptance.py",
        )
        self.hypothesis_route_transition_followthrough_acceptance = _load_module(
            "aitp_hypothesis_route_transition_followthrough_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_followthrough_acceptance.py",
        )
        self.hypothesis_route_transition_resumption_acceptance = _load_module(
            "aitp_hypothesis_route_transition_resumption_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_resumption_acceptance.py",
        )
        self.hypothesis_route_transition_commitment_acceptance = _load_module(
            "aitp_hypothesis_route_transition_commitment_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_commitment_acceptance.py",
        )
        self.hypothesis_route_transition_authority_acceptance = _load_module(
            "aitp_hypothesis_route_transition_authority_acceptance_test",
            "runtime/scripts/run_hypothesis_route_transition_authority_acceptance.py",
        )
        self.first_run_topic_acceptance = _load_module(
            "aitp_first_run_topic_acceptance_test",
            "runtime/scripts/run_first_run_topic_acceptance.py",
        )
        self.first_source_followthrough_acceptance = _load_module(
            "aitp_first_source_followthrough_acceptance_test",
            "runtime/scripts/run_first_source_followthrough_acceptance.py",
        )
        self.staged_l2_reentry_acceptance = _load_module(
            "aitp_staged_l2_reentry_acceptance_test",
            "runtime/scripts/run_staged_l2_reentry_acceptance.py",
        )
        self.staged_l2_advancement_acceptance = _load_module(
            "aitp_staged_l2_advancement_acceptance_test",
            "runtime/scripts/run_staged_l2_advancement_acceptance.py",
        )

    def test_ensure_topic_shell_seeds_concrete_l0_source_handoff_after_bootstrap(self) -> None:
        self.orchestrate_topic.ensure_topic_shell(
            self.knowledge_root,
            "demo-topic",
            "Recover the missing source chain for the topic.",
            "Demo Topic",
        )

        run_root = self.knowledge_root / "feedback" / "topics" / "demo-topic" / "runs"
        next_actions_files = sorted(run_root.glob("*-bootstrap/next_actions.md"))
        self.assertEqual(len(next_actions_files), 1)
        next_actions_text = next_actions_files[0].read_text(encoding="utf-8")

        self.assertIn("source-layer/scripts/discover_and_register.py", next_actions_text)
        self.assertIn("source-layer/scripts/register_arxiv_source.py", next_actions_text)
        self.assertIn("intake/ARXIV_FIRST_SOURCE_INTAKE.md", next_actions_text)

    def test_first_run_acceptance_parser_supports_registration_continuation(self) -> None:
        parser = self.first_run_topic_acceptance.build_parser()
        args = parser.parse_args(
            [
                "--topic-slug",
                "fresh-demo-topic",
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                "metadata.json",
                "--use-package-root-as-kernel",
            ]
        )

        self.assertEqual(args.topic_slug, "fresh-demo-topic")
        self.assertEqual(args.register_arxiv_id, "2401.00001v2")
        self.assertEqual(args.registration_metadata_json, "metadata.json")
        self.assertTrue(args.use_package_root_as_kernel)

    def test_first_run_acceptance_script_runs_registration_and_refreshes_status(self) -> None:
        work_root = Path(self._tmpdir.name) / "first-run-registration-acceptance"
        tar_path = Path(self._tmpdir.name) / "source.tar"
        tex_path = Path(self._tmpdir.name) / "paper.tex"
        metadata_path = Path(self._tmpdir.name) / "metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch.object(
            sys,
            "argv",
            [
                "run_first_run_topic_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = self.first_run_topic_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics").exists())

    def test_first_source_followthrough_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "first-source-followthrough-acceptance"
        tar_path = Path(self._tmpdir.name) / "followthrough-source.tar"
        tex_path = Path(self._tmpdir.name) / "followthrough-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "followthrough-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch.object(
            sys,
            "argv",
            [
                "run_first_source_followthrough_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = self.first_source_followthrough_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics").exists())

    def test_staged_l2_reentry_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "staged-l2-reentry-acceptance"
        tar_path = Path(self._tmpdir.name) / "reentry-source.tar"
        tex_path = Path(self._tmpdir.name) / "reentry-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "reentry-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch.object(
            sys,
            "argv",
            [
                "run_staged_l2_reentry_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = self.staged_l2_reentry_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics").exists())

    def test_staged_l2_advancement_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "staged-l2-advancement-acceptance"
        tar_path = Path(self._tmpdir.name) / "advancement-source.tar"
        tex_path = Path(self._tmpdir.name) / "advancement-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "advancement-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch.object(
            sys,
            "argv",
            [
                "run_staged_l2_advancement_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = self.staged_l2_advancement_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics").exists())

    def test_consultation_followup_selection_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "consultation-followup-selection-acceptance"
        tar_path = Path(self._tmpdir.name) / "consultation-followup-source.tar"
        tex_path = Path(self._tmpdir.name) / "consultation-followup-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "consultation-followup-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        module = _load_module(
            "aitp_consultation_followup_selection_acceptance_test",
            "runtime/scripts/run_consultation_followup_selection_acceptance.py",
        )
        with patch.object(
            sys,
            "argv",
            [
                "run_consultation_followup_selection_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics").exists())
        self.assertTrue(
            (
                work_root
                / "kernel"
                / "runtime"
                / "topics"
                / "jones-chapter-4-finite-dimensional-backbone"
                / "consultation_followup_selection.active.json"
            ).exists()
        )

    def test_selected_candidate_route_choice_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "selected-candidate-route-choice-acceptance"
        tar_path = Path(self._tmpdir.name) / "selected-candidate-route-choice-source.tar"
        tex_path = Path(self._tmpdir.name) / "selected-candidate-route-choice-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "selected-candidate-route-choice-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        module = _load_module(
            "aitp_selected_candidate_route_choice_acceptance_test",
            "runtime/scripts/run_selected_candidate_route_choice_acceptance.py",
        )
        with patch.object(
            sys,
            "argv",
            [
                "run_selected_candidate_route_choice_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "kernel"
                / "runtime"
                / "topics"
                / "jones-chapter-4-finite-dimensional-backbone"
                / "selected_candidate_route_choice.active.json"
            ).exists()
        )

    def test_promotion_review_gate_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "promotion-review-gate-acceptance"
        tar_path = Path(self._tmpdir.name) / "promotion-review-gate-source.tar"
        tex_path = Path(self._tmpdir.name) / "promotion-review-gate-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "promotion-review-gate-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        module = _load_module(
            "aitp_promotion_review_gate_acceptance_test",
            "runtime/scripts/run_promotion_review_gate_acceptance.py",
        )
        with patch.object(
            sys,
            "argv",
            [
                "run_promotion_review_gate_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "kernel"
                / "runtime"
                / "topics"
                / "jones-chapter-4-finite-dimensional-backbone"
                / "promotion_gate.json"
            ).exists()
        )

    def test_selected_candidate_promotion_writeback_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "scpw"
        tar_path = Path(self._tmpdir.name) / "selected-candidate-promotion-writeback-source.tar"
        tex_path = Path(self._tmpdir.name) / "selected-candidate-promotion-writeback-paper.tex"
        metadata_path = Path(self._tmpdir.name) / "selected-candidate-promotion-writeback-metadata.json"

        tex_path.write_text(
            "\\documentclass{article}\n\\begin{document}demo\\end{document}\n",
            encoding="utf-8",
        )
        with tarfile.open(tar_path, "w") as archive:
            archive.add(tex_path, arcname="paper.tex")
        metadata_path.write_text(
            json.dumps(
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A direct match for topological order and anyon condensation discovery.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": tar_path.as_uri(),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        module = _load_module(
            "aitp_selected_candidate_promotion_writeback_acceptance_test",
            "runtime/scripts/run_selected_candidate_promotion_writeback_acceptance.py",
        )
        with patch.object(
            sys,
            "argv",
            [
                "run_selected_candidate_promotion_writeback_acceptance.py",
                "--work-root",
                str(work_root),
                "--register-arxiv-id",
                "2401.00001v2",
                "--registration-metadata-json",
                str(metadata_path),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "kernel"
                / "runtime"
                / "topics"
                / "jones-chapter-4-finite-dimensional-backbone"
                / "promotion_gate.json"
            ).exists()
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write_json(self, relative_path: str, payload: dict) -> None:
        path = self.knowledge_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    def _write_jsonl(self, relative_path: str, rows: list[dict]) -> None:
        path = self.knowledge_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_infer_resume_state_handles_accepted_and_needs_revision(self) -> None:
        accepted = self.sync_topic_state.infer_resume_state(
            intake_status=None,
            feedback_status=None,
            latest_decision={"verdict": "accepted", "fallback_targets": []},
            closed_loop_decision=None,
        )
        needs_revision = self.sync_topic_state.infer_resume_state(
            intake_status=None,
            feedback_status=None,
            latest_decision={
                "verdict": "needs_revision",
                "fallback_targets": ["feedback/topics/demo-topic/runs/2026-03-13-demo"],
            },
            closed_loop_decision=None,
        )

        self.assertEqual(accepted[0], "L2")
        self.assertEqual(needs_revision[0], "L3")

    def test_pending_split_contract_action_detects_unapplied_contract(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "candidate_split_policy": {
                    "enabled": True,
                    "auto_apply_contracts": True,
                    "contract_filename": "candidate_split.contract.json",
                    "receipt_filename": "candidate_split_receipts.jsonl",
                }
            },
        )
        self._write_json(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_split.contract.json",
            {
                "contract_version": 1,
                "splits": [
                    {
                        "source_candidate_id": "candidate:demo",
                        "reason": "Split one wide candidate into smaller units.",
                        "child_candidates": [],
                        "deferred_fragments": [],
                    }
                ],
            },
        )

        actions = self.orchestrate_topic.pending_split_contract_action(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "apply_candidate_split_contract")

    def test_auto_promotion_actions_detect_ready_candidate(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "auto_promotion_policy": {
                    "enabled": True,
                    "default_backend_id": "backend:theoretical-physics-knowledge-network",
                    "trigger_candidate_statuses": ["ready_for_validation"],
                    "theory_formal_candidate_types": ["definition_card"],
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "title": "Demo Definition",
                    "summary": "A bounded definition.",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "origin_refs": [],
                    "question": "Can the definition be promoted?",
                    "assumptions": [],
                    "proposed_validation_route": "bounded-smoke",
                    "intended_l2_targets": ["definition:demo-definition"],
                    "status": "ready_for_validation",
                }
            ],
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/coverage_ledger.json",
            {"status": "pass"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/agent_consensus.json",
            {"status": "ready"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/regression_gate.json",
            {"status": "pass", "split_clearance_status": "clear", "promotion_blockers": []},
        )

        actions = self.orchestrate_topic.auto_promotion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "auto_promote_candidate")
        self.assertEqual(actions[0]["handler_args"]["candidate_id"], "candidate:demo-definition")

    def test_auto_promotion_actions_block_split_and_blockers(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "auto_promotion_policy": {
                    "enabled": True,
                    "default_backend_id": "backend:theoretical-physics-knowledge-network",
                    "trigger_candidate_statuses": ["ready_for_validation"],
                    "theory_formal_candidate_types": ["definition_card"],
                    "require_regression_gate_pass": True,
                    "block_when_split_required": True,
                    "block_when_promotion_blockers_present": True,
                    "block_when_cited_recovery_required": True,
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "title": "Demo Definition",
                    "summary": "A bounded definition.",
                    "topic_slug": "demo-topic",
                    "run_id": "2026-03-13-demo",
                    "origin_refs": [],
                    "question": "Can the definition be promoted?",
                    "assumptions": [],
                    "proposed_validation_route": "bounded-smoke",
                    "intended_l2_targets": ["definition:demo-definition"],
                    "status": "ready_for_validation",
                    "split_required": True,
                    "promotion_blockers": ["Still too wide."],
                }
            ],
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/coverage_ledger.json",
            {"status": "pass"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/agent_consensus.json",
            {"status": "ready"},
        )
        self._write_json(
            "validation/topics/demo-topic/runs/2026-03-13-demo/theory-packets/candidate-demo-definition/regression_gate.json",
            {
                "status": "pass",
                "split_required": True,
                "split_clearance_status": "blocked",
                "promotion_blockers": ["Still too wide."],
                "cited_recovery_required": True,
            },
        )

        actions = self.orchestrate_topic.auto_promotion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(actions, [])

    def test_followup_reintegration_actions_detect_returned_child_topic(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "followup_subtopic_policy": {
                    "enabled": True,
                    "unresolved_return_statuses": [
                        "pending_reentry",
                        "returned_with_gap",
                        "returned_unresolved"
                    ]
                }
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/followup_subtopics.jsonl",
            [
                {
                    "child_topic_slug": "demo-topic--followup--x",
                    "parent_topic_slug": "demo-topic",
                    "status": "spawned",
                    "return_packet_path": str(
                        self.knowledge_root / "runtime" / "topics" / "demo-topic--followup--x" / "followup_return_packet.json"
                    ),
                }
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic--followup--x/followup_return_packet.json",
            {
                "return_packet_version": 1,
                "child_topic_slug": "demo-topic--followup--x",
                "parent_topic_slug": "demo-topic",
                "parent_run_id": "2026-03-13-demo",
                "receipt_id": "receipt:demo",
                "query": "recover missing definition",
                "parent_gap_ids": ["open_gap:demo-gap"],
                "parent_followup_task_ids": ["followup_source_task:demo-gap"],
                "reentry_targets": ["definition:demo"],
                "supporting_regression_question_ids": ["regression_question:demo"],
                "source_id": "paper:demo",
                "arxiv_id": "1510.07698v1",
                "expected_return_route": "L0->L1->L3->L4->L2",
                "acceptable_return_shapes": ["recovered_units", "resolved_gap_update", "still_unresolved_packet"],
                "required_output_artifacts": ["candidate_ledger_or_recovered_units"],
                "unresolved_return_statuses": ["pending_reentry", "returned_with_gap", "returned_unresolved"],
                "return_status": "recovered_units",
                "accepted_return_shape": "recovered_units",
                "return_summary": "Recovered the missing definition.",
                "return_artifact_paths": ["feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl"],
                "reintegration_requirements": {
                    "must_write_back_parent_gaps": True,
                    "must_update_reentry_targets": True,
                    "must_not_patch_parent_directly": True,
                    "requires_child_topic_summary": True
                },
                "updated_at": "2026-03-13T00:00:00+08:00",
                "updated_by": "test"
            },
        )

        actions = self.orchestrate_topic.followup_reintegration_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "reintegrate_followup_subtopic")
        self.assertEqual(actions[0]["handler_args"]["child_topic_slug"], "demo-topic--followup--x")

    def test_topic_completion_actions_detect_missing_completion_surface(self) -> None:
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "ready_for_validation",
                }
            ],
        )

        actions = self.orchestrate_topic.topic_completion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "assess_topic_completion")

    def test_topic_completion_actions_refresh_when_gate_promoted_but_completion_is_stale(self) -> None:
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "auto_promoted",
                }
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic/promotion_gate.json",
            {
                "status": "promoted",
                "candidate_id": "candidate:demo-definition",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/topic_completion.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "promotion-ready",
                "candidate_count": 1,
                "followup_subtopic_count": 0,
            },
        )

        actions = self.orchestrate_topic.topic_completion_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "assess_topic_completion")

    def test_materialize_action_queue_prunes_stale_promotion_review_after_gate_promoted(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/promotion_gate.json",
            {
                "status": "promoted",
                "candidate_id": "candidate:demo-definition",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/topic_completion.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "promoted",
                "candidate_count": 1,
                "followup_subtopic_count": 0,
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L2",
                "pending_actions": [
                    "Review Layer 2 promotion for `candidate:demo-definition` now that coverage, formal-theory review, topic completion, and Lean bridge are all ready.",
                    "Keep the abstract/concrete equivalence route as a separate follow-up lane instead of widening the current concrete bicommutant bridge candidate.",
                    "Keep the multiplication-operator / masa example as its own follow-up lane after the concrete theorem-level package stabilizes.",
                ],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        summaries = [str(row.get("summary") or "") for row in queue]
        self.assertFalse(any(summary.startswith("Review Layer 2 promotion") for summary in summaries))
        self.assertTrue(
            any(summary.startswith("Keep the abstract/concrete equivalence route") for summary in summaries)
        )

    def test_materialize_action_queue_prefers_skill_discovery_for_capability_gap_contract(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "explore",
                "transition_posture": {
                    "transition_kind": "backedge_transition",
                    "triggered_by": ["capability_gap_blocker"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L3",
                "pending_actions": [
                    "Continue a manual follow-up on the current lane.",
                    "Review whether a new backend or workflow capability is needed.",
                ],
            },
            ["bounded capability gap"],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "skill_discovery")

    def test_materialize_action_queue_appends_literature_intake_stage_in_literature_submode(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "explore",
                "active_submode": "literature",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": [],
                },
                "active_research_contract": {
                    "l1_source_intake": {
                        "source_count": 1,
                        "method_specificity_rows": [
                            {
                                "source_id": "paper:weak-coupling",
                                "source_title": "Weak coupling closure",
                                "source_type": "paper",
                                "method_family": "formal_derivation",
                                "specificity_tier": "high",
                                "reading_depth": "full_read",
                                "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                            }
                        ],
                        "contradiction_candidates": [],
                    }
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "pending_actions": [
                    "Continue a bounded manual literature follow-up.",
                ],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "literature_intake_stage")
        self.assertEqual(queue[0]["queue_source"], "runtime_appended")
        self.assertTrue(queue[0]["auto_runnable"])

    def test_materialize_action_queue_advances_to_staging_review_after_matching_literature_stage(self) -> None:
        runtime_payload = {
            "runtime_mode": "explore",
            "active_submode": "literature",
            "transition_posture": {
                "transition_kind": "boundary_hold",
                "triggered_by": [],
            },
            "active_research_contract": {
                "l1_source_intake": {
                    "source_count": 1,
                    "method_specificity_rows": [
                        {
                            "source_id": "paper:weak-coupling",
                            "source_title": "Weak coupling closure",
                            "source_type": "paper",
                            "method_family": "formal_derivation",
                            "specificity_tier": "high",
                            "reading_depth": "full_read",
                            "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                        }
                    ],
                    "contradiction_candidates": [],
                }
            },
        }
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            runtime_payload,
        )
        signature = self.orchestrate_topic.compute_literature_intake_stage_signature(runtime_payload)
        self._write_json(
            "canonical/staging/entries/staging--demo-topic-existing.json",
            {
                "entry_id": "staging:demo-topic-existing",
                "topic_slug": "demo-topic",
                "entry_kind": "claim_card",
                "candidate_unit_type": "claim_card",
                "title": "Existing staged literature unit",
                "summary": "Existing staged literature unit.",
                "status": "staged",
                "authoritative": False,
                "path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "note_path": "canonical/staging/entries/staging--demo-topic-existing.md",
                "provenance": {
                    "literature_stage_signature": signature,
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertFalse(any(row["action_type"] == "literature_intake_stage" for row in queue))
        self.assertEqual(queue[0]["action_type"], "inspect_resume_state")
        self.assertEqual(queue[0]["summary"], "Inspect the current L2 staging manifest before continuing.")

    def test_materialize_action_queue_advances_past_staged_l2_review_after_later_continue(self) -> None:
        runtime_payload = {
            "runtime_mode": "explore",
            "active_submode": "literature",
            "transition_posture": {
                "transition_kind": "boundary_hold",
                "triggered_by": [],
            },
            "active_research_contract": {
                "l1_source_intake": {
                    "source_count": 1,
                    "method_specificity_rows": [
                        {
                            "source_id": "paper:weak-coupling",
                            "source_title": "Weak coupling closure",
                            "source_type": "paper",
                            "method_family": "formal_derivation",
                            "specificity_tier": "high",
                            "reading_depth": "full_read",
                            "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                        }
                    ],
                    "contradiction_candidates": [],
                }
            },
        }
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            runtime_payload,
        )
        signature = self.orchestrate_topic.compute_literature_intake_stage_signature(runtime_payload)
        self._write_json(
            "canonical/staging/entries/staging--demo-topic-existing.json",
            {
                "entry_id": "staging:demo-topic-existing",
                "topic_slug": "demo-topic",
                "entry_kind": "claim_card",
                "candidate_unit_type": "claim_card",
                "title": "Existing staged literature unit",
                "summary": "Existing staged literature unit.",
                "status": "staged",
                "authoritative": False,
                "updated_at": "2026-04-14T06:00:00+08:00",
                "path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "note_path": "canonical/staging/entries/staging--demo-topic-existing.md",
                "provenance": {
                    "literature_stage_signature": signature,
                },
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/innovation_decisions.jsonl",
            [
                {
                    "decision_id": "innovation-decision:demo-topic:continue",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:05:00+08:00",
                    "decision": "continue",
                    "summary": "Continue the active topic under the current operator steering.",
                }
            ],
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "consultation_followup")
        self.assertEqual(
            queue[0]["summary"],
            "Consult the topic-local staged L2 memory and choose one bounded candidate before deeper execution.",
        )

    def test_materialize_action_queue_advances_to_selected_consultation_candidate_when_selection_exists(self) -> None:
        runtime_payload = {
            "runtime_mode": "explore",
            "active_submode": "literature",
            "transition_posture": {
                "transition_kind": "boundary_hold",
                "triggered_by": [],
            },
            "active_research_contract": {
                "l1_source_intake": {
                    "source_count": 1,
                    "method_specificity_rows": [
                        {
                            "source_id": "paper:weak-coupling",
                            "source_title": "Weak coupling closure",
                            "source_type": "paper",
                            "method_family": "formal_derivation",
                            "specificity_tier": "high",
                            "reading_depth": "full_read",
                            "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                        }
                    ],
                    "contradiction_candidates": [],
                }
            },
        }
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            runtime_payload,
        )
        signature = self.orchestrate_topic.compute_literature_intake_stage_signature(runtime_payload)
        self._write_json(
            "canonical/staging/entries/staging--demo-topic-existing.json",
            {
                "entry_id": "staging:demo-topic-existing",
                "topic_slug": "demo-topic",
                "entry_kind": "claim_card",
                "candidate_unit_type": "claim_card",
                "title": "Existing staged literature unit",
                "summary": "Existing staged literature unit.",
                "status": "staged",
                "authoritative": False,
                "updated_at": "2026-04-14T06:00:00+08:00",
                "path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "note_path": "canonical/staging/entries/staging--demo-topic-existing.md",
                "provenance": {
                    "literature_stage_signature": signature,
                },
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/innovation_decisions.jsonl",
            [
                {
                    "decision_id": "innovation-decision:demo-topic:continue",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:05:00+08:00",
                    "decision": "continue",
                    "summary": "Continue the active topic under the current operator steering.",
                }
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic/consultation_followup_selection.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selection_reason": "Selected the first topic-local staged hit from the bounded consultation result.",
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "selected_consultation_candidate_followup")
        self.assertIn("Review the selected staged candidate", queue[0]["summary"])
        self.assertEqual(queue[0]["handler_args"]["candidate_id"], "staging:demo-topic-existing")

    def test_materialize_action_queue_advances_beyond_selected_consultation_candidate_after_later_continue(self) -> None:
        runtime_payload = {
            "runtime_mode": "explore",
            "active_submode": "literature",
            "transition_posture": {
                "transition_kind": "boundary_hold",
                "triggered_by": [],
            },
            "active_research_contract": {
                "l1_source_intake": {
                    "source_count": 1,
                    "method_specificity_rows": [
                        {
                            "source_id": "paper:weak-coupling",
                            "source_title": "Weak coupling closure",
                            "source_type": "paper",
                            "method_family": "formal_derivation",
                            "specificity_tier": "high",
                            "reading_depth": "full_read",
                            "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                        }
                    ],
                    "contradiction_candidates": [],
                }
            },
        }
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            runtime_payload,
        )
        signature = self.orchestrate_topic.compute_literature_intake_stage_signature(runtime_payload)
        self._write_json(
            "canonical/staging/entries/staging--demo-topic-existing.json",
            {
                "entry_id": "staging:demo-topic-existing",
                "topic_slug": "demo-topic",
                "entry_kind": "concept",
                "candidate_unit_type": "concept",
                "title": "Existing staged literature unit",
                "summary": "Existing staged literature unit.",
                "status": "staged",
                "authoritative": False,
                "updated_at": "2026-04-14T06:00:00+08:00",
                "path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "note_path": "canonical/staging/entries/staging--demo-topic-existing.md",
                "provenance": {
                    "literature_stage_signature": signature,
                },
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/innovation_decisions.jsonl",
            [
                {
                    "decision_id": "innovation-decision:demo-topic:continue-01",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:05:00+08:00",
                    "decision": "continue",
                    "summary": "Continue after staged review.",
                },
                {
                    "decision_id": "innovation-decision:demo-topic:continue-02",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:06:00+08:00",
                    "decision": "continue",
                    "summary": "Continue into consultation follow-up.",
                },
                {
                    "decision_id": "innovation-decision:demo-topic:continue-03",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:07:00+08:00",
                    "decision": "continue",
                    "summary": "Continue beyond selected candidate summary.",
                },
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic/next_action_decision.json",
            {
                "topic_slug": "demo-topic",
                "updated_at": "2026-04-14T06:06:00+08:00",
                "selected_action": {
                    "action_type": "selected_consultation_candidate_followup",
                },
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/consultation_followup_selection.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_title": "Existing staged literature unit",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selected_candidate_trust_surface": "staging",
                "selected_candidate_topic_slug": "demo-topic",
                "selection_reason": "Selected the first topic-local staged hit from the bounded consultation result.",
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "l2_promotion_review")
        self.assertIn("Review Layer 2 promotion", queue[0]["summary"])
        self.assertEqual(queue[0]["handler_args"]["candidate_id"], "staging:demo-topic-existing")

    def test_materialize_action_queue_materializes_promotion_review_gate_after_later_continue(self) -> None:
        runtime_payload = {
            "runtime_mode": "explore",
            "active_submode": "literature",
            "transition_posture": {
                "transition_kind": "boundary_hold",
                "triggered_by": [],
            },
            "active_research_contract": {
                "l1_source_intake": {
                    "source_count": 1,
                    "method_specificity_rows": [
                        {
                            "source_id": "paper:weak-coupling",
                            "source_title": "Weak coupling closure",
                            "source_type": "paper",
                            "method_family": "formal_derivation",
                            "specificity_tier": "high",
                            "reading_depth": "full_read",
                            "evidence_excerpt": "Derives the bounded closure in weak coupling.",
                        }
                    ],
                    "contradiction_candidates": [],
                }
            },
        }
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            runtime_payload,
        )
        signature = self.orchestrate_topic.compute_literature_intake_stage_signature(runtime_payload)
        self._write_json(
            "canonical/staging/entries/staging--demo-topic-existing.json",
            {
                "entry_id": "staging:demo-topic-existing",
                "topic_slug": "demo-topic",
                "entry_kind": "concept",
                "candidate_unit_type": "concept",
                "title": "Existing staged literature unit",
                "summary": "Existing staged literature unit.",
                "status": "staged",
                "authoritative": False,
                "updated_at": "2026-04-14T06:00:00+08:00",
                "path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "note_path": "canonical/staging/entries/staging--demo-topic-existing.md",
                "provenance": {
                    "literature_stage_signature": signature,
                },
            },
        )
        self._write_jsonl(
            "runtime/topics/demo-topic/innovation_decisions.jsonl",
            [
                {
                    "decision_id": "innovation-decision:demo-topic:continue-01",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:05:00+08:00",
                    "decision": "continue",
                    "summary": "Continue after staged review.",
                },
                {
                    "decision_id": "innovation-decision:demo-topic:continue-02",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:06:00+08:00",
                    "decision": "continue",
                    "summary": "Continue into consultation follow-up.",
                },
                {
                    "decision_id": "innovation-decision:demo-topic:continue-03",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:07:00+08:00",
                    "decision": "continue",
                    "summary": "Continue beyond selected candidate summary.",
                },
                {
                    "decision_id": "innovation-decision:demo-topic:continue-04",
                    "topic_slug": "demo-topic",
                    "updated_at": "2026-04-14T06:08:00+08:00",
                    "decision": "continue",
                    "summary": "Continue from promotion-review summary into the first explicit gate.",
                },
            ],
        )
        self._write_json(
            "runtime/topics/demo-topic/next_action_decision.json",
            {
                "topic_slug": "demo-topic",
                "updated_at": "2026-04-14T06:07:00+08:00",
                "selected_action": {
                    "action_type": "l2_promotion_review",
                },
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/consultation_followup_selection.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_title": "Existing staged literature unit",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selected_candidate_trust_surface": "staging",
                "selected_candidate_topic_slug": "demo-topic",
                "selection_reason": "Selected the first topic-local staged hit from the bounded consultation result.",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/selected_candidate_route_choice.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selected_candidate_title": "Existing staged literature unit",
                "selected_candidate_unit_type": "concept",
                "chosen_action_type": "l2_promotion_review",
                "chosen_action_summary": "Review Layer 2 promotion for selected staged candidate `staging:demo-topic-existing` before deeper execution.",
                "route_choice_reason": "Selected staged reusable units should first enter bounded Layer 2 promotion review.",
            },
        )

        queue, queue_meta = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L1",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "approve_promotion")
        self.assertIn("promotion gate", queue[0]["summary"].lower())
        self.assertEqual(queue[0]["handler_args"]["candidate_id"], "staging:demo-topic-existing")
        gate_payload = queue_meta.get("selected_candidate_promotion_gate_payload")
        self.assertIsInstance(gate_payload, dict)
        self.assertEqual(gate_payload["status"], "pending_human_approval")
        self.assertEqual(gate_payload["candidate_id"], "staging:demo-topic-existing")

    def test_materialize_action_queue_does_not_repeat_completion_refresh_when_completion_is_current(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/consultation_followup_selection.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_title": "Existing staged literature unit",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selected_candidate_trust_surface": "staging",
                "selected_candidate_topic_slug": "demo-topic",
                "selection_reason": "Selected the first topic-local staged hit from the bounded consultation result.",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/selected_candidate_route_choice.active.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "selected",
                "selected_candidate_id": "staging:demo-topic-existing",
                "selected_candidate_path": "canonical/staging/entries/staging--demo-topic-existing.json",
                "selected_candidate_title": "Existing staged literature unit",
                "selected_candidate_unit_type": "concept",
                "chosen_action_type": "l2_promotion_review",
                "chosen_action_summary": "Review Layer 2 promotion for selected staged candidate `staging:demo-topic-existing` before deeper execution.",
                "route_choice_reason": "Selected staged reusable units should first enter bounded Layer 2 promotion review.",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/promotion_gate.json",
            {
                "status": "promoted",
                "candidate_id": "staging:demo-topic-existing",
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/topic_completion.json",
            {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "status": "promoted",
                "candidate_count": 1,
                "followup_subtopic_count": 0,
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "staging:demo-topic-existing",
                    "candidate_type": "concept",
                    "status": "promoted",
                    "summary": "Existing staged literature unit.",
                    "title": "Existing staged literature unit",
                }
            ],
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L2",
                "source_count": 1,
                "pending_actions": [],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertNotEqual(queue[0]["action_type"], "assess_topic_completion")

    def test_materialize_action_queue_prefers_promotion_review_in_promote_mode(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "promote",
                "transition_posture": {
                    "transition_kind": "forward_transition",
                    "triggered_by": ["promotion_intent"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L4",
                "pending_actions": [
                    "Keep a manual follow-up lane open for later.",
                    "Review Layer 2 promotion for the bounded candidate.",
                ],
            },
            [],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertEqual(queue[0]["action_type"], "l2_promotion_review")

    def test_materialize_action_queue_skips_runtime_execution_append_for_consultation_backedge(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "explore",
                "transition_posture": {
                    "transition_kind": "backedge_transition",
                    "triggered_by": ["non_trivial_consultation"],
                },
            },
        )

        with patch.object(
            self.orchestrate_topic,
            "compute_closed_loop_status",
            return_value={
                "next_transition": "select_route",
                "awaiting_external_result": False,
                "execution_task": None,
                "literature_followups": [],
                "paths": {},
            },
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pending_actions": [
                        "Consult memory before reshaping the candidate.",
                    ],
                },
                [],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        self.assertFalse(any(row["action_type"] == "select_validation_route" for row in queue))

    def test_materialize_action_queue_skips_skill_append_in_promote_mode(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "promote",
                "transition_posture": {
                    "transition_kind": "forward_transition",
                    "triggered_by": ["promotion_intent"],
                },
            },
        )

        queue, _ = self.orchestrate_topic.materialize_action_queue(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "2026-03-13-demo",
                "resume_stage": "L4",
                "pending_actions": [
                    "Resolve backend parity before doing anything else.",
                    "Review Layer 2 promotion for the bounded candidate.",
                ],
            },
            ["backend parity"],
            self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
            self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
            self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
            self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
            self.knowledge_root,
        )

        self.assertFalse(any(row["action_type"] == "skill_discovery" for row in queue))

    def test_materialize_action_queue_skips_runtime_appends_when_human_checkpoint_required(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "verify",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": ["verification_route_selection"],
                    "requires_human_checkpoint": True,
                },
            },
        )

        with patch.object(
            self.orchestrate_topic,
            "compute_closed_loop_status",
            return_value={
                "next_transition": "select_route",
                "awaiting_external_result": False,
                "execution_task": None,
                "literature_followups": [
                    {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                ],
                "paths": {},
            },
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                ["backend parity"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        self.assertFalse(any(row["action_type"] == "skill_discovery" for row in queue))
        self.assertFalse(any(row["action_type"] == "select_validation_route" for row in queue))
        self.assertFalse(any(row["action_type"] == "literature_followup_search" for row in queue))

    def test_materialize_action_queue_skips_helper_runtime_appends_when_human_checkpoint_required(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/runtime_protocol.generated.json",
            {
                "runtime_mode": "verify",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "triggered_by": ["verification_route_selection"],
                    "requires_human_checkpoint": True,
                },
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": None,
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
            patch.object(
                self.orchestrate_topic,
                "topic_completion_actions",
                return_value=[helper_action("action:demo-topic:completion", "assess_topic_completion")],
            ),
            patch.object(
                self.orchestrate_topic,
                "auto_promotion_actions",
                return_value=[helper_action("action:demo-topic:auto-promote", "auto_promote_candidate")],
            ),
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                [],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertNotIn("assess_topic_completion", action_types)
        self.assertNotIn("auto_promote_candidate", action_types)

    def test_materialize_action_queue_skips_runtime_and_helper_appends_when_operator_checkpoint_is_requested(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/operator_checkpoint.active.json",
            {
                "checkpoint_id": "checkpoint:demo-topic:execution-lane-confirmation",
                "topic_slug": "demo-topic",
                "checkpoint_kind": "execution_lane_confirmation",
                "status": "requested",
                "active": True,
                "question": "Confirm the execution lane before deeper runtime expansion.",
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": None,
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "compute_closed_loop_status",
                return_value={
                    "next_transition": "select_route",
                    "awaiting_external_result": False,
                    "execution_task": None,
                    "literature_followups": [
                        {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                    ],
                    "paths": {},
                },
            ),
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
        ):
            queue, queue_meta = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L4",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                },
                ["bounded capability gap"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertNotIn("skill_discovery", action_types)
        self.assertNotIn("select_validation_route", action_types)
        self.assertNotIn("literature_followup_search", action_types)
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertEqual(
            queue_meta["operator_checkpoint_path"],
            "runtime/topics/demo-topic/operator_checkpoint.active.json",
        )
        self.assertIn("operator checkpoint", str(queue_meta["append_policy_reason"]).lower())

    def test_materialize_action_queue_declared_contract_can_disable_runtime_appends_but_keep_skill_append(self) -> None:
        self._write_json(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.contract.json",
            {
                "contract_version": 1,
                "policy_note": "Keep only the declared queue plus capability-gap help.",
                "append_runtime_actions": False,
                "append_skill_action_if_needed": True,
                "actions": [
                    {
                        "action_id": "action:demo-topic:declared-01",
                        "summary": "Continue a bounded manual derivation follow-up.",
                        "action_type": "manual_followup",
                        "resume_stage": "L3",
                        "auto_runnable": False,
                    }
                ],
            },
        )

        helper_action = lambda action_id, action_type: {
            "action_id": action_id,
            "topic_slug": "demo-topic",
            "resume_stage": "L4",
            "status": "pending",
            "action_type": action_type,
            "summary": f"Helper-generated {action_type}.",
            "auto_runnable": True,
            "handler": None,
            "handler_args": {},
            "queue_source": "runtime_appended",
            "declared_contract_path": "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.contract.json",
        }

        with (
            patch.object(
                self.orchestrate_topic,
                "compute_closed_loop_status",
                return_value={
                    "next_transition": "select_route",
                    "awaiting_external_result": False,
                    "execution_task": None,
                    "literature_followups": [
                        {"query": "demo query", "target_source_type": "paper", "priority": "medium"}
                    ],
                    "paths": {},
                },
            ),
            patch.object(
                self.orchestrate_topic,
                "pending_split_contract_action",
                return_value=[helper_action("action:demo-topic:split", "apply_candidate_split_contract")],
            ),
            patch.object(
                self.orchestrate_topic,
                "followup_subtopic_actions",
                return_value=[helper_action("action:demo-topic:subtopic", "spawn_followup_subtopics")],
            ),
            patch.object(
                self.orchestrate_topic,
                "topic_completion_actions",
                return_value=[helper_action("action:demo-topic:completion", "assess_topic_completion")],
            ),
            patch.object(
                self.orchestrate_topic,
                "auto_promotion_actions",
                return_value=[helper_action("action:demo-topic:auto-promote", "auto_promote_candidate")],
            ),
        ):
            queue, _ = self.orchestrate_topic.materialize_action_queue(
                {
                    "topic_slug": "demo-topic",
                    "latest_run_id": "2026-03-13-demo",
                    "resume_stage": "L3",
                    "pending_actions": [
                        "Continue a bounded manual derivation follow-up.",
                    ],
                    "pointers": {
                        "next_actions_path": "feedback/topics/demo-topic/runs/2026-03-13-demo/next_actions.md",
                    },
                },
                ["backend parity"],
                self.knowledge_root / "runtime" / "scripts" / "discover_external_skills.py",
                self.knowledge_root / "runtime" / "scripts" / "advance_closed_loop.py",
                self.knowledge_root / "runtime" / "scripts" / "handoff_execution.py",
                self.knowledge_root / "runtime" / "scripts" / "run_literature_followup.py",
                self.knowledge_root,
            )

        action_types = {row["action_type"] for row in queue}
        self.assertIn("manual_followup", action_types)
        self.assertIn("skill_discovery", action_types)
        self.assertNotIn("apply_candidate_split_contract", action_types)
        self.assertNotIn("select_validation_route", action_types)
        self.assertNotIn("literature_followup_search", action_types)
        self.assertNotIn("spawn_followup_subtopics", action_types)
        self.assertNotIn("assess_topic_completion", action_types)
        self.assertNotIn("auto_promote_candidate", action_types)

    def test_decide_next_action_prefers_skill_discovery_for_capability_gap_backedge(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "runtime_protocol.generated.json").write_text(
            json.dumps(
                {
                    "runtime_mode": "explore",
                    "transition_posture": {
                        "transition_kind": "backedge_transition",
                        "triggered_by": ["capability_gap_blocker"],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        topic_state = {
            "topic_slug": "demo-topic",
            "updated_by": "test",
            "resume_stage": "L3",
            "pointers": {},
        }
        queue_rows = [
            {
                "action_id": "action:demo:1",
                "action_type": "manual_followup",
                "summary": "Keep probing the current manual lane.",
                "status": "pending",
                "auto_runnable": False,
            },
            {
                "action_id": "action:demo:2",
                "action_type": "skill_discovery",
                "summary": "Search for the bounded missing capability.",
                "status": "pending",
                "auto_runnable": True,
            },
        ]
        control_note = {"directive": None}
        runtime_contract = self.decide_next_action.load_runtime_contract(topic_runtime_root)

        unfinished = self.decide_next_action.build_unfinished_work(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )
        decision = self.decide_next_action.build_next_action_decision(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )

        self.assertEqual(unfinished["queue_head_action_id"], "action:demo:2")
        self.assertEqual(decision["selected_action"]["action_id"], "action:demo:2")
        self.assertEqual(decision["decision_basis"], "runtime_contract_preferred:skill_discovery")

    def test_decide_next_action_prefers_literature_intake_stage_in_literature_submode(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "runtime_protocol.generated.json").write_text(
            json.dumps(
                {
                    "runtime_mode": "explore",
                    "active_submode": "literature",
                    "transition_posture": {
                        "transition_kind": "boundary_hold",
                        "triggered_by": [],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        topic_state = {
            "topic_slug": "demo-topic",
            "resume_stage": "L1",
            "latest_run_id": "2026-03-13-demo",
        }
        queue_rows = [
            {
                "action_id": "action:demo:1",
                "action_type": "manual_followup",
                "summary": "Keep a manual follow-up open.",
                "status": "pending",
                "auto_runnable": False,
            },
            {
                "action_id": "action:demo:2",
                "action_type": "literature_intake_stage",
                "summary": "Stage bounded literature-intake units from the current L1 vault into L2 staging.",
                "status": "pending",
                "auto_runnable": True,
            },
        ]
        control_note = {"status": "missing", "directive": None, "allow_override_decision_contract": False}
        runtime_contract = self.decide_next_action.load_runtime_contract(topic_runtime_root)

        unfinished = self.decide_next_action.build_unfinished_work(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )
        decision = self.decide_next_action.build_next_action_decision(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )

        self.assertEqual(unfinished["queue_head_action_id"], "action:demo:2")
        self.assertEqual(decision["selected_action"]["action_id"], "action:demo:2")
        self.assertEqual(decision["decision_basis"], "runtime_contract_preferred:literature_intake_stage")

    def test_decide_next_action_prefers_promotion_review_in_promote_mode(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "runtime_protocol.generated.json").write_text(
            json.dumps(
                {
                    "runtime_mode": "promote",
                    "transition_posture": {
                        "transition_kind": "forward_transition",
                        "triggered_by": ["promotion_intent"],
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        topic_state = {
            "topic_slug": "demo-topic",
            "updated_by": "test",
            "resume_stage": "L4",
            "pointers": {},
        }
        queue_rows = [
            {
                "action_id": "action:demo:1",
                "action_type": "manual_followup",
                "summary": "Continue a non-promotion manual lane.",
                "status": "pending",
                "auto_runnable": False,
            },
            {
                "action_id": "action:demo:2",
                "action_type": "l2_promotion_review",
                "summary": "Review Layer 2 promotion for the bounded candidate.",
                "status": "pending",
                "auto_runnable": False,
            },
        ]
        control_note = {"directive": None}
        runtime_contract = self.decide_next_action.load_runtime_contract(topic_runtime_root)

        unfinished = self.decide_next_action.build_unfinished_work(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )
        decision = self.decide_next_action.build_next_action_decision(
            topic_state,
            queue_rows,
            control_note,
            runtime_contract,
        )

        self.assertEqual(unfinished["queue_head_action_id"], "action:demo:2")
        self.assertEqual(decision["selected_action"]["action_id"], "action:demo:2")
        self.assertEqual(decision["decision_basis"], "runtime_contract_preferred:l2_promotion_review")

    def test_lean_bridge_actions_detect_missing_candidate_packet(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "lean_bridge_policy": {
                    "enabled": True,
                    "trigger_candidate_types": ["definition_card"]
                }
            },
        )
        self._write_jsonl(
            "feedback/topics/demo-topic/runs/2026-03-13-demo/candidate_ledger.jsonl",
            [
                {
                    "candidate_id": "candidate:demo-definition",
                    "candidate_type": "definition_card",
                    "status": "ready_for_validation",
                }
            ],
        )

        actions = self.orchestrate_topic.lean_bridge_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "prepare_lean_bridge")

    def test_deferred_reactivation_actions_detect_ready_entry(self) -> None:
        self._write_json(
            "runtime/closed_loop_policies.json",
            {
                "deferred_buffer_policy": {
                    "enabled": True,
                    "auto_reactivate": True,
                }
            },
        )
        self._write_json(
            "runtime/topics/demo-topic/deferred_candidates.json",
            {
                "buffer_version": 1,
                "topic_slug": "demo-topic",
                "updated_at": "2026-03-17T00:00:00+08:00",
                "updated_by": "aitp-cli",
                "entries": [
                    {
                        "entry_id": "deferred:demo",
                        "source_candidate_id": "candidate:demo",
                        "title": "Deferred Demo",
                        "summary": "Deferred until a follow-up source appears.",
                        "reason": "Missing source.",
                        "status": "buffered",
                        "reactivation_conditions": {
                            "source_ids_any": ["paper:followup-source"]
                        },
                        "reactivation_candidate": {
                            "candidate_id": "candidate:demo-reactivated"
                        },
                    }
                ],
            },
        )
        self._write_jsonl(
            "source-layer/topics/demo-topic/source_index.jsonl",
            [
                {
                    "source_id": "paper:followup-source",
                    "title": "Follow-up Source",
                    "summary": "Contains the missing resolution.",
                }
            ],
        )

        actions = self.orchestrate_topic.deferred_reactivation_actions(
            self.knowledge_root,
            {"topic_slug": "demo-topic", "latest_run_id": "2026-03-13-demo"},
            {"declared_contract_path": None},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "reactivate_deferred_candidate")
        self.assertEqual(actions[0]["handler_args"]["entry_id"], "deferred:demo")

    def test_build_operator_console_starts_with_immediate_execution_contract(self) -> None:
        topic_state = {
            "topic_slug": "demo-topic",
            "promotion_gate": {"status": "approved"},
            "status_explainability": {
                "why_this_topic_is_here": "AITP is waiting on a bounded capability-gap step.",
                "current_route_choice": {
                    "next_action_summary": "Find the missing bounded workflow.",
                },
                "last_evidence_return": {
                    "summary": "No durable evidence-return artifact is currently recorded for this topic.",
                },
                "active_human_need": {
                    "summary": "No active human checkpoint is currently blocking the bounded loop.",
                },
            },
            "pointers": {
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
            },
        }
        interaction_state = {
            "topic_slug": "demo-topic",
            "human_request": "Continue bounded validation",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "human_edit_surfaces": [
                {
                    "surface": "runtime_queue_contract",
                    "path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                    "role": "editable queue contract snapshot",
                }
            ],
            "action_queue_surface": {
                "queue_source": "heuristic",
                "generated_contract_path": "runtime/topics/demo-topic/action_queue_contract.generated.json",
                "generated_contract_note_path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
            },
            "decision_surface": {
                "decision_mode": "continue_unfinished",
                "decision_source": "heuristic",
                "decision_basis": "fallback queue selection",
                "selected_action_id": "action:demo:1",
                "selected_action_type": "skill_discovery",
                "selected_action_auto_runnable": True,
                "pending_count": 1,
                "manual_pending_count": 0,
                "auto_pending_count": 1,
                "reason": "Bounded capability gap remains.",
                "control_note_status": "missing",
                "decision_contract_status": "missing",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "unfinished_work_note_path": "runtime/topics/demo-topic/unfinished_work.md",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
                "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
            },
            "capability_adaptation": {
                "protocol_path": "research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md",
                "discovery_script": "research/adapters/openclaw/scripts/discover_external_skills.py",
                "auto_install_allowed": False,
                "discovery_artifacts": [],
            },
            "delivery_contract": {
                "rule": "Outputs must cite exact artifact paths and justify the chosen layer."
            },
        }
        queue = [
            {
                "action_id": "action:demo:1",
                "action_type": "skill_discovery",
                "summary": "Find the missing bounded workflow.",
                "auto_runnable": True,
                "handler": "discover_external_skills",
            }
        ]

        rendered = self.orchestrate_topic.build_operator_console(topic_state, interaction_state, queue)

        self.assertIn("## Immediate execution contract", rendered)
        self.assertIn("### Do now", rendered)
        self.assertIn("### Escalate when", rendered)
        self.assertIn("## Topic explainability", rendered)
        self.assertIn("AITP is waiting on a bounded capability-gap step.", rendered)
        self.assertIn("`promotion_intent` status=`active`", rendered)
        self.assertIn("## Deferred surfaces and human edit areas", rendered)

    def test_build_resume_markdown_renders_status_explainability(self) -> None:
        state = {
            "topic_slug": "demo-topic",
            "updated_at": "2026-03-28T10:00:00+08:00",
            "updated_by": "codex",
            "last_materialized_stage": "L4",
            "resume_stage": "L3",
            "latest_run_id": "2026-03-20-demo",
            "research_mode": "formal_derivation",
            "active_executor_kind": "codex",
            "active_reasoning_profile": "bounded",
            "resume_reason": "Latest closed-loop decision is revise; resume exploratory work in Layer 3.",
            "source_count": 2,
            "pending_actions": ["Inspect the returned result and continue the bounded proof review."],
            "deferred_candidate_count": 0,
            "reactivable_deferred_count": 0,
            "followup_subtopic_count": 0,
            "research_mode_profile": {
                "profile_path": "runtime/research_modes/formal_derivation.json",
                "label": "Formal derivation",
                "description": "Formal derivation profile.",
                "reproducibility_expectations": ["Keep derivation anchors explicit."],
                "note_expectations": ["Write a human-readable derivation note."],
            },
            "backend_bridges": [],
            "promotion_gate": {"status": "not_requested"},
            "layer_status": {
                "L0": {"status": "present"},
                "L1": {"status": "present"},
                "L3": {"status": "active"},
                "L4": {"status": "revise"},
            },
            "closed_loop": {
                "status": "revise",
                "selected_route_id": "route:demo",
                "task_id": "task:demo",
                "result_id": "result:demo",
                "latest_decision": "revise",
                "literature_followup_count": 0,
                "followup_gap_count": 0,
            },
            "status_explainability": {
                "why_this_topic_is_here": "The topic is currently following `Inspect the returned result and continue the bounded proof review.` at stage `L3`.",
                "current_route_choice": {
                    "selected_route_id": "route:demo",
                    "execution_task_id": "task:demo",
                    "next_action_summary": "Inspect the returned result and continue the bounded proof review.",
                    "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
                    "selected_validation_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                },
                "last_evidence_return": {
                    "status": "present",
                    "kind": "result_manifest",
                    "record_id": "result:demo",
                    "recorded_at": "2026-03-28T09:00:00+08:00",
                    "path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                    "summary": "Closed-loop result manifest is `partial`.",
                },
                "active_human_need": {
                    "status": "none",
                    "kind": "none",
                    "path": "",
                    "summary": "No active human checkpoint is currently blocking the bounded loop.",
                },
                "blocker_summary": [],
            },
            "pointers": {
                "l0_source_index_path": "source-layer/topics/demo-topic/source_index.jsonl",
                "intake_status_path": "intake/topics/demo-topic/status.json",
                "feedback_status_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/status.json",
                "next_actions_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.md",
                "next_actions_contract_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.contract.json",
                "promotion_decision_path": "validation/topics/demo-topic/runs/2026-03-20-demo/promotion_decisions.jsonl",
                "consultation_index_path": "consultation/topics/demo-topic/consultation_index.jsonl",
                "control_note_path": "",
                "innovation_direction_path": "",
                "innovation_decisions_path": "",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "unfinished_work_note_path": "runtime/topics/demo-topic/unfinished_work.md",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
                "next_action_decision_note_path": "runtime/topics/demo-topic/next_action_decision.md",
                "next_action_decision_contract_path": "runtime/topics/demo-topic/next_action_decision.contract.json",
                "next_action_decision_contract_note_path": "runtime/topics/demo-topic/next_action_decision.contract.md",
                "action_queue_contract_generated_path": "runtime/topics/demo-topic/action_queue_contract.generated.json",
                "action_queue_contract_generated_note_path": "runtime/topics/demo-topic/action_queue_contract.generated.md",
                "selected_validation_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                "execution_task_path": "runtime/topics/demo-topic/execution_task.json",
                "execution_notes_path": "validation/topics/demo-topic/runs/2026-03-20-demo/execution_notes",
                "returned_execution_result_path": "validation/topics/demo-topic/runs/2026-03-20-demo/returned_execution_result.json",
                "result_manifest_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                "trajectory_log_path": "validation/topics/demo-topic/runs/2026-03-20-demo/trajectory_log.jsonl",
                "trajectory_note_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_summary.md",
                "failure_classification_path": "validation/topics/demo-topic/runs/2026-03-20-demo/failure_classification.json",
                "failure_classification_note_path": "validation/topics/demo-topic/runs/2026-03-20-demo/failure_classification.md",
                "decision_ledger_path": "validation/topics/demo-topic/runs/2026-03-20-demo/decision_ledger.jsonl",
                "literature_followup_queries_path": "",
                "literature_followup_receipts_path": "",
                "followup_gap_writeback_path": "",
                "followup_gap_writeback_note_path": "",
                "deferred_buffer_path": "",
                "deferred_buffer_note_path": "",
                "followup_subtopics_path": "",
                "followup_subtopics_note_path": "",
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
            },
        }

        rendered = self.sync_topic_state.build_resume_markdown(state)

        self.assertIn("## Why this topic is here", rendered)
        self.assertIn("## Current route choice", rendered)
        self.assertIn("## Last evidence return", rendered)
        self.assertIn("## Active human need", rendered)
        self.assertIn("result:demo", rendered)

    def test_derive_status_explainability_prioritizes_operator_checkpoint(self) -> None:
        topic_runtime_root = self.knowledge_root / "runtime" / "topics" / "demo-topic"
        topic_runtime_root.mkdir(parents=True, exist_ok=True)
        (topic_runtime_root / "operator_checkpoint.active.json").write_text(
            json.dumps(
                {
                    "status": "requested",
                    "checkpoint_kind": "promotion_approval",
                    "question": "Should the current candidate be promoted?",
                    "blocker_summary": ["Promotion is waiting for an explicit human decision."],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        explainability = self.sync_topic_state.derive_status_explainability(
            topic_slug="demo-topic",
            resume_stage="L3",
            resume_reason="Latest closed-loop decision is revise; resume exploratory work in Layer 3.",
            pending_actions=["Inspect the returned result and continue the bounded proof review."],
            topic_runtime_root=topic_runtime_root,
            feedback_status=None,
            closed_loop={
                "result_manifest": {
                    "result_id": "result:demo",
                    "status": "partial",
                },
                "paths": {
                    "result_manifest_path": "validation/topics/demo-topic/runs/2026-03-20-demo/result_manifest.json",
                },
                "selected_route": {
                    "route_id": "route:demo",
                },
                "execution_task": {
                    "task_id": "task:demo",
                },
                "latest_decision": {
                    "reason": "The returned result still needs bounded manual review.",
                },
            },
            next_action_decision_note_path=topic_runtime_root / "next_action_decision.md",
        )

        self.assertEqual(explainability["active_human_need"]["kind"], "promotion_approval")
        self.assertEqual(explainability["last_evidence_return"]["kind"], "result_manifest")
        self.assertEqual(explainability["last_evidence_return"]["record_id"], "result:demo")
        self.assertIn("Promotion is waiting for an explicit human decision.", explainability["why_this_topic_is_here"])

    def test_build_agent_brief_starts_with_immediate_execution_contract(self) -> None:
        topic_state = {
            "topic_slug": "demo-topic",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "source_count": 2,
            "latest_run_id": "2026-03-20-demo",
            "research_mode": "formal_derivation",
            "active_executor_kind": "codex",
            "active_reasoning_profile": "bounded",
            "research_mode_profile": {
                "profile_path": "runtime/research_modes/formal_derivation.json",
                "label": "Formal derivation",
                "reproducibility_expectations": ["Keep derivation anchors explicit."],
                "note_expectations": ["Write a human-readable derivation note."],
            },
            "backend_bridges": [],
            "promotion_gate": {"status": "not_requested", "promoted_units": []},
            "pointers": {
                "l0_source_index_path": "source-layer/topics/demo-topic/source_index.jsonl",
                "intake_status_path": "source-layer/topics/demo-topic/intake_status.json",
                "feedback_status_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/feedback_status.json",
                "promotion_decision_path": "validation/topics/demo-topic/runs/2026-03-20-demo/promotion_decision.json",
                "promotion_gate_path": "runtime/topics/demo-topic/promotion_gate.json",
                "promotion_gate_note_path": "runtime/topics/demo-topic/promotion_gate.md",
                "consultation_index_path": "runtime/topics/demo-topic/consultation_index.json",
            },
        }
        interaction_state = {
            "decision_surface": {
                "decision_source": "heuristic",
                "decision_mode": "continue_unfinished",
                "selected_action_id": "action:demo:2",
                "control_note_status": "present",
                "decision_contract_status": "missing",
                "unfinished_work_path": "runtime/topics/demo-topic/unfinished_work.json",
                "next_action_decision_path": "runtime/topics/demo-topic/next_action_decision.json",
            },
            "action_queue_surface": {
                "queue_source": "declared_contract",
                "declared_contract_path": "feedback/topics/demo-topic/runs/2026-03-20-demo/next_actions.contract.json",
            },
            "closed_loop": {
                "selected_route_path": "runtime/topics/demo-topic/selected_validation_route.json",
                "execution_task_path": "runtime/topics/demo-topic/execution_task.json",
                "returned_result_path": "validation/topics/demo-topic/runs/2026-03-20-demo/returned_execution_result.json",
                "trajectory_log_path": "runtime/topics/demo-topic/loop_history.jsonl",
                "failure_classification_path": "runtime/topics/demo-topic/failure_classification.json",
            },
        }
        queue = [
            {
                "action_id": "action:demo:2",
                "action_type": "consultation_followup",
                "summary": "Consult memory before reshaping the candidate.",
                "auto_runnable": False,
            }
        ]

        rendered = self.orchestrate_topic.build_agent_brief(topic_state, queue, interaction_state)

        self.assertIn("## Immediate execution contract", rendered)
        self.assertIn("### Do now", rendered)
        self.assertIn("### Escalate when", rendered)
        self.assertIn("`decision_override_present` status=`active`", rendered)
        self.assertIn("`non_trivial_consultation` status=`active`", rendered)
        self.assertIn("## Deferred surfaces and exact pointers", rendered)

    def test_materialize_execution_task_defaults_to_human_confirmation_for_inferred_route(self) -> None:
        self._write_json(
            "runtime/topics/demo-topic/selected_validation_route.json",
            {
                "route_id": "route:demo-topic:benchmark",
                "objective": "Run the bounded benchmark lane in the current execution environment.",
                "input_artifacts": ["feedback/topics/demo-topic/runs/run-001/result_summary.md"],
                "expected_outputs": ["validation/topics/demo-topic/runs/run-001/results/benchmark.json"],
                "success_criterion": ["Benchmark output is materialized."],
                "failure_signals": ["Benchmark run does not produce the declared artifact."],
                "run_id": "run-001",
                "surface": "numerical",
            },
        )

        payload = self.closed_loop_v1.materialize_execution_task(
            self.knowledge_root,
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "research_mode": "first_principles",
                "updated_by": "test",
            },
            updated_by="test",
        )

        self.assertTrue(payload["needs_human_confirm"])
        self.assertFalse(payload["auto_dispatch_allowed"])
        task_note = (
            self.knowledge_root / "runtime" / "topics" / "demo-topic" / "execution_task.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Human confirmation is required before dispatch", task_note)

    def test_l2_knowledge_report_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "knowledge-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l2_knowledge_report_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l2_knowledge_report_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "compiled" / "workspace_knowledge_report.json").exists())
        self.assertTrue((work_root / "kernel" / "canonical" / "compiled" / "workspace_knowledge_report.md").exists())

    def test_l1_vault_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-vault-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_vault_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_vault_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "vault_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "home.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "output" / "flowback.jsonl").exists())

    def test_statement_compilation_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "statement-compilation-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_statement_compilation_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.statement_compilation_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "statement_compilation.active.json").exists())
        self.assertTrue((work_root / "kernel" / "validation" / "topics" / "demo-topic" / "runs" / "run-001" / "statement-compilation" / "candidate-demo-candidate" / "statement_compilation.json").exists())
        self.assertTrue((work_root / "kernel" / "validation" / "topics" / "demo-topic" / "runs" / "run-001" / "statement-compilation" / "candidate-demo-candidate" / "proof_repair_plan.json").exists())

    def test_l0_source_discovery_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l0-source-discovery-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l0_source_discovery_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l0_source_discovery_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "discoveries").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "source_index.jsonl").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "global_index.jsonl").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "sources").exists())

    def test_l0_source_enrichment_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l0-source-enrichment-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l0_source_enrichment_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l0_source_enrichment_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "source_index.jsonl").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "sources").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "sources").exists())

    def test_l0_source_concept_graph_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l0-source-concept-graph-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l0_source_concept_graph_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l0_source_concept_graph_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "source_index.jsonl").exists())
        self.assertTrue((work_root / "kernel" / "source-layer" / "topics" / "demo-topic" / "sources").exists())

    def test_l1_concept_graph_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-concept-graph-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_concept_graph_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_concept_graph_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").exists())

    def test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-assumption-depth-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_assumption_depth_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_assumption_depth_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_dashboard.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").exists())

    def test_l1_contradiction_surface_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_l1_contradiction_surface_acceptance_test",
            "runtime/scripts/run_l1_contradiction_surface_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "l1-contradiction-surface-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_contradiction_surface_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_dashboard.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").exists())

    def test_analytical_cross_check_surface_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_analytical_cross_check_surface_acceptance_test",
            "runtime/scripts/run_analytical_cross_check_surface_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "analytical-cross-check-surface-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_analytical_cross_check_surface_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "validation_review_bundle.active.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())

    def test_analytical_judgment_surface_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_analytical_judgment_surface_acceptance_test",
            "runtime/scripts/run_analytical_judgment_surface_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "analytical-judgment-surface-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_analytical_judgment_surface_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "validation_review_bundle.active.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())

    def test_formal_positive_l2_acceptance_parser_supports_fresh_topic_inputs(self) -> None:
        module = _load_module(
            "aitp_formal_positive_l2_acceptance_test",
            "runtime/scripts/run_formal_positive_l2_acceptance.py",
        )

        parser = module.build_parser()
        args = parser.parse_args(
            [
                "--topic",
                "Fresh Jones finite-dimensional factor closure",
                "--question",
                "Promote one bounded Jones finite-dimensional factor result into authoritative L2.",
                "--reference-topic-slug",
                "jones-von-neumann-algebras",
                "--json",
            ]
        )

        self.assertEqual(args.topic, "Fresh Jones finite-dimensional factor closure")
        self.assertEqual(
            args.question,
            "Promote one bounded Jones finite-dimensional factor result into authoritative L2.",
        )
        self.assertEqual(args.reference_topic_slug, "jones-von-neumann-algebras")
        self.assertTrue(args.json)

    def test_positive_negative_l2_coexistence_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_positive_negative_l2_coexistence_acceptance_test",
            "runtime/scripts/run_positive_negative_l2_coexistence_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "pnco"
        with patch.object(
            sys,
            "argv",
            [
                "run_positive_negative_l2_coexistence_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "compiled" / "workspace_knowledge_report.json").exists())
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "theorem-cards" / "theorem_card--jones-ch4-finite-product.json").exists())
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "staging" / "entries").exists())

    def test_hs_toy_model_target_contract_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_hs_toy_model_target_contract_acceptance_test",
            "runtime/scripts/run_hs_toy_model_target_contract_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "hsct"
        with patch.object(
            sys,
            "argv",
            [
                "run_hs_toy_model_target_contract_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "knowledge-hub" / "runtime" / "topics").exists())
        self.assertTrue((work_root / "knowledge-hub" / "source-layer" / "topics").exists())

    def test_hs_positive_l2_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_hs_positive_l2_acceptance_test",
            "runtime/scripts/run_hs_positive_l2_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "hsp"
        with patch.object(
            sys,
            "argv",
            [
                "run_hs_positive_l2_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "claim-cards" / "claim_card--hs-like-chaos-window-finite-size-core.json").exists())
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "compiled" / "workspace_knowledge_report.json").exists())

    def test_hs_positive_negative_coexistence_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_hs_positive_negative_coexistence_acceptance_test",
            "runtime/scripts/run_hs_positive_negative_coexistence_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "hspn"
        with patch.object(
            sys,
            "argv",
            [
                "run_hs_positive_negative_coexistence_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "compiled" / "workspace_knowledge_report.json").exists())
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "claim-cards" / "claim_card--hs-like-chaos-window-finite-size-core.json").exists())
        self.assertTrue((work_root / "knowledge-hub" / "canonical" / "staging" / "entries" / "staging--hs-model-otoc-lyapunov-exponent-regime-mismatch.json").exists())

    def test_librpa_qsgw_target_contract_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_librpa_qsgw_target_contract_acceptance_test",
            "runtime/scripts/run_librpa_qsgw_target_contract_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "lqtc"
        with patch.object(
            sys,
            "argv",
            [
                "run_librpa_qsgw_target_contract_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        runtime_topics_root = work_root / "knowledge-hub" / "runtime" / "topics"
        source_topics_root = work_root / "knowledge-hub" / "source-layer" / "topics"
        feedback_root = work_root / "knowledge-hub" / "feedback" / "topics"
        self.assertTrue(runtime_topics_root.exists())
        self.assertTrue(source_topics_root.exists())
        self.assertTrue(any(runtime_topics_root.glob("*/librpa_qsgw_target_contract.json")))
        self.assertTrue(any(source_topics_root.glob("*/source_index.jsonl")))
        self.assertTrue(any(feedback_root.glob("*/runs/*/candidate_ledger.jsonl")))

    def test_librpa_qsgw_positive_l2_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_librpa_qsgw_positive_l2_acceptance_test",
            "runtime/scripts/run_librpa_qsgw_positive_l2_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "lqpl2"
        with patch.object(
            sys,
            "argv",
            [
                "run_librpa_qsgw_positive_l2_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "knowledge-hub"
                / "canonical"
                / "claim-cards"
                / "claim_card--librpa-qsgw-deterministic-reduction-consistency-core.json"
            ).exists()
        )
        self.assertTrue(
            (
                work_root
                / "knowledge-hub"
                / "canonical"
                / "compiled"
                / "workspace_knowledge_report.json"
            ).exists()
        )

    def test_first_principles_real_topic_dialogue_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_first_principles_real_topic_dialogue_acceptance_test",
            "runtime/scripts/run_first_principles_real_topic_dialogue_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "fprtd"
        with patch.object(
            sys,
            "argv",
            [
                "run_first_principles_real_topic_dialogue_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "knowledge-hub"
                / "canonical"
                / "claim-cards"
                / "claim_card--librpa-qsgw-deterministic-reduction-consistency-core.json"
            ).exists()
        )
        self.assertTrue(
            any(
                (
                    work_root
                    / "knowledge-hub"
                    / "runtime"
                    / "topics"
                ).glob("*/interaction_state.json")
            )
        )

    def test_formal_real_topic_dialogue_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_formal_real_topic_dialogue_acceptance_test",
            "runtime/scripts/run_formal_real_topic_dialogue_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "frtd"
        with patch.object(
            sys,
            "argv",
            [
                "run_formal_real_topic_dialogue_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "knowledge-hub"
                / "canonical"
                / "theorem-cards"
                / "theorem_card--jones-ch4-finite-product.json"
            ).exists()
        )
        self.assertTrue(
            any(
                (
                    work_root
                    / "knowledge-hub"
                    / "runtime"
                    / "topics"
                ).glob("*/interaction_state.json")
            )
        )

    def test_toy_model_real_topic_dialogue_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_toy_model_real_topic_dialogue_acceptance_test",
            "runtime/scripts/run_toy_model_real_topic_dialogue_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "trtd"
        with patch.object(
            sys,
            "argv",
            [
                "run_toy_model_real_topic_dialogue_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue(
            (
                work_root
                / "knowledge-hub"
                / "canonical"
                / "claim-cards"
                / "claim_card--hs-like-chaos-window-finite-size-core.json"
            ).exists()
        )
        self.assertTrue(
            any(
                (
                    work_root
                    / "knowledge-hub"
                    / "runtime"
                    / "topics"
                ).glob("*/interaction_state.json")
            )
        )

    def test_l1_progressive_reading_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-progressive-reading-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_progressive_reading_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_progressive_reading_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").exists())

    def test_l1_graph_analysis_staging_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-analysis-staging-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_analysis_staging_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_analysis_staging_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "source-intake.md").exists())

    def test_l1_graph_diff_runtime_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-diff-runtime-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_diff_runtime_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_diff_runtime_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis_history.jsonl").exists())

    def test_l1_graph_diff_staging_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-diff-staging-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_diff_staging_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_diff_staging_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis_history.jsonl").exists())

    def test_l1_graph_community_bridge_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-community-bridge-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_community_bridge_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_community_bridge_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.md").exists())

    def test_l1_graph_hyperedge_pattern_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-hyperedge-pattern-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_hyperedge_pattern_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_hyperedge_pattern_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "graph_analysis.md").exists())

    def test_multi_paper_l2_relevance_acceptance_script_runs_on_isolated_work_root(self) -> None:
        module = _load_module(
            "aitp_multi_paper_l2_relevance_acceptance_test",
            "runtime/scripts/run_multi_paper_l2_relevance_acceptance.py",
        )
        work_root = Path(self._tmpdir.name) / "multi-paper-l2-relevance-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_multi_paper_l2_relevance_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "canonical" / "compiled" / "workspace_knowledge_report.json").exists())

    def test_l1_graph_obsidian_export_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-obsidian-export-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_obsidian_export_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_obsidian_export_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph" / "manifest.json").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph" / "index.md").exists())

    def test_l1_graph_obsidian_multicommunity_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-obsidian-multicommunity-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_obsidian_multicommunity_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_obsidian_multicommunity_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph" / "category-theory-cluster" / "index.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph" / "topological-order-cluster" / "index.md").exists())

    def test_l1_graph_obsidian_brain_bridge_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "l1-graph-obsidian-brain-bridge-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_l1_graph_obsidian_brain_bridge_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.l1_graph_obsidian_brain_bridge_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "brain" / "90 AITP Imports" / "concept-graphs" / "demo-topic" / "index.md").exists())
        self.assertTrue((work_root / "kernel" / "intake" / "topics" / "demo-topic" / "vault" / "wiki" / "concept-graph" / "theoretical_physics_brain_sync.receipt.json").exists())

    def test_mode_enforcement_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "mode-enforcement-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_mode_enforcement_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.mode_enforcement_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-discussion" / "runtime_protocol.generated.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-explore" / "runtime_protocol.generated.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-verify" / "runtime_protocol.generated.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-promote" / "runtime_protocol.generated.json").exists())
        self.assertTrue((work_root / "kernel" / "canonical" / "staging" / "workspace_staging_manifest.json").exists())

    def test_transition_history_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "transition-history-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_transition_history_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.transition_history_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "transition_history.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "transition_history.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())

    def test_human_modification_record_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "human-modification-record-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_human_modification_record_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.human_modification_record_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "promotion_gate.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "promotion_gate.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())

    def test_competing_hypotheses_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "competing-hypotheses-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_competing_hypotheses_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.competing_hypotheses_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())

    def test_hypothesis_branch_routing_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-branch-routing-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_branch_routing_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_branch_routing_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "research_question.contract.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())

    def test_hypothesis_route_activation_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-activation-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_activation_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_activation_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").exists())

    def test_hypothesis_route_reentry_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-reentry-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_reentry_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_reentry_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").exists())

    def test_hypothesis_route_handoff_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-handoff-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_handoff_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_handoff_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").exists())

    def test_hypothesis_route_choice_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-choice-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_choice_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_choice_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic" / "followup_subtopics.jsonl").exists())

    def test_hypothesis_route_transition_gate_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-gate-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_gate_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_gate_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-blocked" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-available" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-checkpoint" / "operator_checkpoint.active.md").exists())

    def test_hypothesis_route_transition_intent_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-intent-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_intent_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_intent_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-proposed" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-ready" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-checkpoint-held" / "operator_checkpoint.active.md").exists())

    def test_hypothesis_route_transition_receipt_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-receipt-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_receipt_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_receipt_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-pending-receipt" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-recorded-receipt" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-receipt" / "transition_history.md").exists())

    def test_hypothesis_route_transition_resolution_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-resolution-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_resolution_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_resolution_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-pending-resolution" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-resolved-resolution" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-resolution" / "transition_history.md").exists())

    def test_hypothesis_route_transition_discrepancy_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-discrepancy-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_discrepancy_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_discrepancy_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-discrepancy-pending" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-discrepancy-present" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-discrepancy-none" / "transition_history.md").exists())

    def test_hypothesis_route_transition_repair_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-repair-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_repair_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_repair_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-repair-pending" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-repair-needed" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-repair-none" / "transition_history.md").exists())

    def test_hypothesis_route_transition_escalation_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-escalation-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_escalation_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_escalation_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-escalation" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-escalation-recommended" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-escalation-active" / "operator_checkpoint.active.md").exists())

    def test_hypothesis_route_transition_clearance_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-clearance-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_clearance_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_clearance_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-clearance" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-clearance-awaiting" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-clearance-blocked" / "operator_checkpoint.active.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-clearance-cleared" / "operator_checkpoint.active.md").exists())

    def test_hypothesis_route_transition_followthrough_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-followthrough-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_followthrough_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_followthrough_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-followthrough" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-followthrough-awaiting" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-followthrough-blocked" / "operator_checkpoint.active.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-followthrough-ready" / "operator_checkpoint.active.md").exists())

    def test_hypothesis_route_transition_resumption_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-resumption-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_resumption_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_resumption_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-resumption" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-resumption-waiting" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-resumption-pending" / "operator_checkpoint.active.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-resumption-resumed" / "transition_history.md").exists())

    def test_hypothesis_route_transition_commitment_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-commitment-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_commitment_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_commitment_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-commitment" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-commitment-waiting" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-commitment-pending" / "transition_history.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-commitment-committed" / "transition_history.md").exists())

    def test_hypothesis_route_transition_authority_acceptance_script_runs_on_isolated_work_root(self) -> None:
        work_root = Path(self._tmpdir.name) / "hypothesis-route-transition-authority-acceptance"
        with patch.object(
            sys,
            "argv",
            [
                "run_hypothesis_route_transition_authority_acceptance.py",
                "--work-root",
                str(work_root),
                "--json",
            ],
        ):
            exit_code = self.hypothesis_route_transition_authority_acceptance.main()

        self.assertEqual(exit_code, 0)
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-no-authority" / "runtime_protocol.generated.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-authority-waiting" / "topic_replay_bundle.json").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-authority-pending" / "transition_history.md").exists())
        self.assertTrue((work_root / "kernel" / "runtime" / "topics" / "demo-topic-authority-authoritative" / "transition_history.md").exists())


if __name__ == "__main__":
    unittest.main()
