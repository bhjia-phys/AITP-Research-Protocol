from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import sys
from unittest.mock import MagicMock, patch


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub import aitp_cli


class AITPCLITests(unittest.TestCase):
    def test_ci_check_command_is_registered(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["ci-check", "--topic-slug", "demo-topic"])
        self.assertEqual(args.command, "ci-check")
        self.assertEqual(args.phase, "exit")

    def test_loop_and_operation_commands_are_registered(self) -> None:
        parser = aitp_cli.build_parser()

        loop_args = parser.parse_args(["loop", "--topic-slug", "demo-topic", "--max-auto-steps", "2"])
        self.assertEqual(loop_args.command, "loop")
        self.assertEqual(loop_args.max_auto_steps, 2)

        init_args = parser.parse_args(
            [
                "operation-init",
                "--topic-slug",
                "demo-topic",
                "--title",
                "Small-system validation backend",
                "--kind",
                "numerical",
                "--baseline-required",
            ]
        )
        self.assertEqual(init_args.command, "operation-init")
        self.assertEqual(init_args.kind, "numerical")
        self.assertTrue(init_args.baseline_required)

        trust_args = parser.parse_args(["trust-audit", "--topic-slug", "demo-topic"])
        self.assertEqual(trust_args.command, "trust-audit")

        capability_args = parser.parse_args(["capability-audit", "--topic-slug", "demo-topic"])
        self.assertEqual(capability_args.command, "capability-audit")

        paired_backend_args = parser.parse_args(["paired-backend-audit", "--topic-slug", "demo-topic"])
        self.assertEqual(paired_backend_args.command, "paired-backend-audit")

        h_plane_args = parser.parse_args(["h-plane-audit", "--topic-slug", "demo-topic"])
        self.assertEqual(h_plane_args.command, "h-plane-audit")

        bridge_args = parser.parse_args(
            [
                "sync-l1-graph-export-to-theoretical-physics-brain",
                "--topic-slug",
                "demo-topic",
                "--target-root",
                "D:/brain",
            ]
        )
        self.assertEqual(bridge_args.command, "sync-l1-graph-export-to-theoretical-physics-brain")
        self.assertEqual(bridge_args.target_root, "D:/brain")

    def test_topic_shell_commands_are_registered(self) -> None:
        parser = aitp_cli.build_parser()

        new_topic_args = parser.parse_args(
            [
                "new-topic",
                "--topic",
                "Topological phases",
                "--question",
                "What is the active bounded question?",
                "--mode",
                "formal_theory",
            ]
        )
        self.assertEqual(new_topic_args.command, "new-topic")
        self.assertEqual(new_topic_args.mode, "formal_theory")

        hello_args = parser.parse_args(["hello"])
        self.assertEqual(hello_args.command, "hello")
        self.assertEqual(hello_args.topic, "Demo topic")

        help_args = parser.parse_args(["help"])
        self.assertEqual(help_args.command, "help")
        self.assertFalse(help_args.all)

        help_all_args = parser.parse_args(["help", "--all"])
        self.assertEqual(help_all_args.command, "help")
        self.assertTrue(help_all_args.all)

        status_args = parser.parse_args(["status", "--topic-slug", "demo-topic"])
        self.assertEqual(status_args.command, "status")
        status_verbose_args = parser.parse_args(["status", "--topic-slug", "demo-topic", "--verbose"])
        self.assertTrue(status_verbose_args.verbose)
        status_full_args = parser.parse_args(["status", "--topic-slug", "demo-topic", "--full"])
        self.assertTrue(status_full_args.full)

        layer_graph_args = parser.parse_args(["layer-graph", "--topic-slug", "demo-topic"])
        self.assertEqual(layer_graph_args.command, "layer-graph")

        next_args = parser.parse_args(["next", "--topic-slug", "demo-topic"])
        self.assertEqual(next_args.command, "next")

        work_args = parser.parse_args(
            [
                "work",
                "--topic-slug",
                "demo-topic",
                "--question",
                "Check the next proof obligation",
                "--max-auto-steps",
                "0",
            ]
        )
        self.assertEqual(work_args.command, "work")
        self.assertEqual(work_args.max_auto_steps, 0)

        steer_text_args = parser.parse_args(
            [
                "steer-topic",
                "--topic-slug",
                "demo-topic",
                "--text",
                "继续这个 topic，方向改成 modular bootstrap constraints",
            ]
        )
        self.assertEqual(steer_text_args.command, "steer-topic")
        self.assertEqual(steer_text_args.text, "继续这个 topic，方向改成 modular bootstrap constraints")

        verify_args = parser.parse_args(["verify", "--topic-slug", "demo-topic", "--mode", "proof"])
        self.assertEqual(verify_args.command, "verify")
        self.assertEqual(verify_args.mode, "proof")
        analytical_verify_args = parser.parse_args(["verify", "--topic-slug", "demo-topic", "--mode", "analytical"])
        self.assertEqual(analytical_verify_args.command, "verify")
        self.assertEqual(analytical_verify_args.mode, "analytical")

        complete_args = parser.parse_args(["complete-topic", "--topic-slug", "demo-topic"])
        self.assertEqual(complete_args.command, "complete-topic")

        reintegrate_args = parser.parse_args(
            ["reintegrate-followup", "--topic-slug", "demo-topic", "--child-topic-slug", "demo-topic--followup--x"]
        )
        self.assertEqual(reintegrate_args.command, "reintegrate-followup")
        self.assertEqual(reintegrate_args.child_topic_slug, "demo-topic--followup--x")

        update_return_args = parser.parse_args(
            [
                "update-followup-return",
                "--topic-slug",
                "demo-topic--followup--x",
                "--return-status",
                "recovered_units",
                "--accepted-return-shape",
                "recovered_units",
                "--return-artifact-path",
                "validation/topics/demo-topic/runs/demo/candidate_ledger.jsonl",
            ]
        )
        self.assertEqual(update_return_args.command, "update-followup-return")
        self.assertEqual(update_return_args.return_status, "recovered_units")
        self.assertEqual(update_return_args.accepted_return_shape, "recovered_units")

        lean_args = parser.parse_args(["lean-bridge", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo"])
        self.assertEqual(lean_args.command, "lean-bridge")
        self.assertEqual(lean_args.candidate_id, "candidate:demo")

        statement_compilation_args = parser.parse_args(
            ["statement-compilation", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo"]
        )
        self.assertEqual(statement_compilation_args.command, "statement-compilation")
        self.assertEqual(statement_compilation_args.candidate_id, "candidate:demo")

        topics_args = parser.parse_args(["topics"])
        self.assertEqual(topics_args.command, "topics")

        current_topic_args = parser.parse_args(["current-topic"])
        self.assertEqual(current_topic_args.command, "current-topic")

        collaborator_memory_args = parser.parse_args(["collaborator-memory", "--topic-slug", "demo-topic"])
        self.assertEqual(collaborator_memory_args.command, "collaborator-memory")
        self.assertEqual(collaborator_memory_args.topic_slug, "demo-topic")

        scratch_log_args = parser.parse_args(["scratch-log", "--topic-slug", "demo-topic"])
        self.assertEqual(scratch_log_args.command, "scratch-log")
        self.assertEqual(scratch_log_args.topic_slug, "demo-topic")

        record_scratch_args = parser.parse_args(
            [
                "record-scratch-note",
                "--topic-slug",
                "demo-topic",
                "--kind",
                "route_comparison",
                "--summary",
                "Compare the theorem-facing and benchmark-first routes.",
            ]
        )
        self.assertEqual(record_scratch_args.command, "record-scratch-note")
        self.assertEqual(record_scratch_args.kind, "route_comparison")

        negative_result_args = parser.parse_args(
            [
                "record-negative-result",
                "--topic-slug",
                "demo-topic",
                "--summary",
                "The portability extrapolation failed.",
                "--failure-kind",
                "regime_mismatch",
            ]
        )
        self.assertEqual(negative_result_args.command, "record-negative-result")
        self.assertEqual(negative_result_args.failure_kind, "regime_mismatch")

        taste_profile_args = parser.parse_args(["taste-profile", "--topic-slug", "demo-topic"])
        self.assertEqual(taste_profile_args.command, "taste-profile")
        self.assertEqual(taste_profile_args.topic_slug, "demo-topic")

        record_taste_args = parser.parse_args(
            [
                "record-taste",
                "--topic-slug",
                "demo-topic",
                "--kind",
                "formalism",
                "--summary",
                "Prefer operator-algebra notation first.",
                "--formalism",
                "operator_algebra",
            ]
        )
        self.assertEqual(record_taste_args.command, "record-taste")
        self.assertEqual(record_taste_args.kind, "formalism")
        self.assertEqual(record_taste_args.formalism, ["operator_algebra"])

        record_collaborator_args = parser.parse_args(
            [
                "record-collaborator-memory",
                "--memory-kind",
                "preference",
                "--summary",
                "Prefer theorem-facing routes first.",
                "--topic-slug",
                "demo-topic",
                "--tag",
                "formal-theory",
            ]
        )
        self.assertEqual(record_collaborator_args.command, "record-collaborator-memory")
        self.assertEqual(record_collaborator_args.memory_kind, "preference")
        self.assertEqual(record_collaborator_args.tag, ["formal-theory"])

        replay_args = parser.parse_args(["replay-topic", "--topic-slug", "demo-topic"])
        self.assertEqual(replay_args.command, "replay-topic")
        self.assertEqual(replay_args.topic_slug, "demo-topic")

        stage_args = parser.parse_args(
            [
                "stage-l2-provisional",
                "--topic-slug",
                "demo-topic",
                "--entry-kind",
                "workflow_draft",
                "--title",
                "Demo draft",
                "--summary",
                "A provisional reusable workflow draft.",
            ]
        )
        self.assertEqual(stage_args.command, "stage-l2-provisional")
        self.assertEqual(stage_args.entry_kind, "workflow_draft")

        seed_args = parser.parse_args(["seed-l2-direction", "--direction", "tfim-benchmark-first"])
        self.assertEqual(seed_args.command, "seed-l2-direction")
        self.assertEqual(seed_args.direction, "tfim-benchmark-first")

        consult_args = parser.parse_args(
            [
                "consult-l2",
                "--query-text",
                "TFIM exact diagonalization benchmark workflow",
                "--retrieval-profile",
                "l3_candidate_formation",
                "--max-primary-hits",
                "2",
                "--include-staging",
            ]
        )
        self.assertEqual(consult_args.command, "consult-l2")
        self.assertEqual(consult_args.retrieval_profile, "l3_candidate_formation")
        self.assertTrue(consult_args.include_staging)

        consult_record_args = parser.parse_args(
            [
                "consult-l2",
                "--query-text",
                "Benchmark-first validation",
                "--retrieval-profile",
                "l1_provisional_understanding",
                "--topic-slug",
                "demo-topic",
                "--stage",
                "L3",
                "--run-id",
                "run-001",
                "--record-consultation",
            ]
        )
        self.assertEqual(consult_record_args.topic_slug, "demo-topic")
        self.assertEqual(consult_record_args.stage, "L3")
        self.assertTrue(consult_record_args.record_consultation)

        compile_args = parser.parse_args(["compile-l2-map"])
        self.assertEqual(compile_args.command, "compile-l2-map")

        graph_report_args = parser.parse_args(["compile-l2-graph-report"])
        self.assertEqual(graph_report_args.command, "compile-l2-graph-report")

        knowledge_report_args = parser.parse_args(["compile-l2-knowledge-report"])
        self.assertEqual(knowledge_report_args.command, "compile-l2-knowledge-report")

        source_catalog_args = parser.parse_args(["compile-source-catalog"])
        self.assertEqual(source_catalog_args.command, "compile-source-catalog")

        trace_source_args = parser.parse_args(
            ["trace-source-citations", "--canonical-source-id", "source_identity:doi:10-1000-shared-paper"]
        )
        self.assertEqual(trace_source_args.command, "trace-source-citations")
        self.assertEqual(trace_source_args.canonical_source_id, "source_identity:doi:10-1000-shared-paper")

        source_family_args = parser.parse_args(["compile-source-family", "--source-type", "paper"])
        self.assertEqual(source_family_args.command, "compile-source-family")
        self.assertEqual(source_family_args.source_type, "paper")

        export_bibtex_args = parser.parse_args(
            [
                "export-source-bibtex",
                "--canonical-source-id",
                "source_identity:doi:10-1000-shared-paper",
                "--include-neighbors",
            ]
        )
        self.assertEqual(export_bibtex_args.command, "export-source-bibtex")
        self.assertTrue(export_bibtex_args.include_neighbors)

        import_bibtex_args = parser.parse_args(
            [
                "import-bibtex-sources",
                "--topic-slug",
                "demo-topic",
                "--bibtex-path",
                "demo-import.bib",
            ]
        )
        self.assertEqual(import_bibtex_args.command, "import-bibtex-sources")
        self.assertEqual(import_bibtex_args.topic_slug, "demo-topic")
        self.assertEqual(import_bibtex_args.bibtex_path, "demo-import.bib")

        hygiene_args = parser.parse_args(["audit-l2-hygiene"])
        self.assertEqual(hygiene_args.command, "audit-l2-hygiene")

        focus_args = parser.parse_args(["focus-topic", "--topic-slug", "demo-topic"])
        self.assertEqual(focus_args.command, "focus-topic")
        self.assertEqual(focus_args.topic_slug, "demo-topic")

        pause_args = parser.parse_args(["pause-topic", "--topic-slug", "demo-topic"])
        self.assertEqual(pause_args.command, "pause-topic")
        self.assertEqual(pause_args.topic_slug, "demo-topic")

        resume_topic_args = parser.parse_args(["resume-topic", "--topic-slug", "demo-topic"])
        self.assertEqual(resume_topic_args.command, "resume-topic")
        self.assertEqual(resume_topic_args.topic_slug, "demo-topic")

        block_args = parser.parse_args(["block-topic", "--topic-slug", "demo-topic", "--blocked-by", "other-topic", "--reason", "Need prerequisite"])
        self.assertEqual(block_args.command, "block-topic")
        self.assertEqual(block_args.blocked_by, "other-topic")

        unblock_args = parser.parse_args(["unblock-topic", "--topic-slug", "demo-topic", "--blocked-by", "other-topic"])
        self.assertEqual(unblock_args.command, "unblock-topic")
        self.assertEqual(unblock_args.blocked_by, "other-topic")

        clear_deps_args = parser.parse_args(["clear-topic-dependencies", "--topic-slug", "demo-topic"])
        self.assertEqual(clear_deps_args.command, "clear-topic-dependencies")

        session_start_args = parser.parse_args(["session-start", "继续这个 topic，方向改成 X"])
        self.assertEqual(session_start_args.command, "session-start")
        self.assertEqual(session_start_args.task, "继续这个 topic，方向改成 X")
        self.assertFalse(session_start_args.current_topic)
        self.assertEqual(session_start_args.load_profile, "auto")

        explore_args = parser.parse_args(["explore", "Sketch a speculative route without full topic bootstrap"])
        self.assertEqual(explore_args.command, "explore")
        self.assertEqual(explore_args.task, "Sketch a speculative route without full topic bootstrap")

        promote_exploration_args = parser.parse_args(["promote-exploration", "--exploration-id", "explore-demo", "--current-topic"])
        self.assertEqual(promote_exploration_args.command, "promote-exploration")
        self.assertEqual(promote_exploration_args.exploration_id, "explore-demo")
        self.assertTrue(promote_exploration_args.current_topic)

        loop_with_profile = parser.parse_args(
            ["loop", "--topic-slug", "demo-topic", "--load-profile", "light", "--max-auto-steps", "1"]
        )
        self.assertEqual(loop_with_profile.load_profile, "light")

        resume_with_profile = parser.parse_args(
            ["resume", "--topic-slug", "demo-topic", "--load-profile", "full"]
        )
        self.assertEqual(resume_with_profile.load_profile, "full")

        work_with_profile = parser.parse_args(
            ["work", "--topic-slug", "demo-topic", "--question", "continue the topic", "--load-profile", "light"]
        )
        self.assertEqual(work_with_profile.load_profile, "light")

    def test_phase6_commands_are_registered(self) -> None:
        parser = aitp_cli.build_parser()

        emit_args = parser.parse_args(
            [
                "emit-decision",
                "--topic-slug",
                "demo-topic",
                "--question",
                "Clarify the validation route?",
                "--options",
                '[{"label":"small-system","description":"Use the smallest exact lane first"},{"label":"larger-system","description":"Defer to a larger finite-size lane"}]',
                "--blocking",
                "false",
                "--default-option-index",
                "0",
                "--trigger-rule",
                "direction_ambiguity",
            ]
        )
        self.assertEqual(emit_args.command, "emit-decision")
        self.assertFalse(emit_args.blocking)
        self.assertEqual(emit_args.options[0]["label"], "small-system")
        self.assertEqual(emit_args.default_option_index, 0)

        resolve_args = parser.parse_args(
            ["resolve-decision", "--topic-slug", "demo-topic", "--decision-id", "dp:demo", "--option", "1"]
        )
        self.assertEqual(resolve_args.command, "resolve-decision")
        self.assertEqual(resolve_args.option, 1)

        list_args = parser.parse_args(["list-decisions", "--topic-slug", "demo-topic", "--pending-only"])
        self.assertEqual(list_args.command, "list-decisions")
        self.assertTrue(list_args.pending_only)

        trace_args = parser.parse_args(
            [
                "trace-decision",
                "--topic-slug",
                "demo-topic",
                "--summary",
                "Selected the small-system lane first.",
                "--chosen",
                "small-system",
                "--rationale",
                "It closes the exact benchmark gap first.",
                "--input-refs",
                '["runtime/topics/demo-topic/operator_console.md"]',
                "--output-refs",
                '["runtime/topics/demo-topic/chronicles/chronicle__demo.md"]',
            ]
        )
        self.assertEqual(trace_args.command, "trace-decision")
        self.assertEqual(trace_args.input_refs[0], "runtime/topics/demo-topic/operator_console.md")
        self.assertEqual(trace_args.output_refs[0], "runtime/topics/demo-topic/chronicles/chronicle__demo.md")

        chronicle_args = parser.parse_args(
            [
                "chronicle",
                "--topic-slug",
                "demo-topic",
                "--finalize",
                "--ending-state",
                "Ready for the next bounded validation step.",
                "--next-step",
                "Run the larger-system lane.",
                "--next-step",
                "Write back the operator note.",
                "--summary",
                "Closed the current bounded session.",
            ]
        )
        self.assertEqual(chronicle_args.command, "chronicle")
        self.assertTrue(chronicle_args.finalize)
        self.assertEqual(len(chronicle_args.next_step), 2)

    def test_main_dispatches_update_followup_return(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.update_followup_return_packet.return_value = {"status": "success"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", [
                "aitp",
                "update-followup-return",
                "--topic-slug",
                "demo-topic--followup--x",
                "--return-status",
                "resolved_gap_update",
                "--accepted-return-shape",
                "resolved_gap_update",
                "--return-summary",
                "Recovered the cited prerequisite and updated the parent gap surface.",
                "--return-artifact-path",
                "validation/topics/demo-topic/runs/demo/candidate_ledger.jsonl",
            ]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.update_followup_return_packet.assert_called_once()

    def test_main_dispatches_current_topic(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.get_current_topic_memory.return_value = {"topic_slug": "demo-topic"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "current-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.get_current_topic_memory.assert_called_once()

    def test_main_dispatches_paired_backend_audit(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.paired_backend_audit.return_value = {"pairing_status": "paired_active"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "paired-backend-audit", "--topic-slug", "demo-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.paired_backend_audit.assert_called_once_with(
            topic_slug="demo-topic",
            backend_id="backend:theoretical-physics-knowledge-network",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_h_plane_audit(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.h_plane_audit.return_value = {"overall_status": "active_human_control"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "h-plane-audit", "--topic-slug", "demo-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.h_plane_audit.assert_called_once_with(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_layer_graph(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.topic_layer_graph.return_value = {"topic_slug": "demo-topic", "layer_graph": {"current_node_id": "L3-R"}}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "layer-graph", "--topic-slug", "demo-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.topic_layer_graph.assert_called_once_with(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_taste_profile(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.topic_research_taste.return_value = {"topic_slug": "demo-topic", "research_taste": {"status": "available"}}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "taste-profile", "--topic-slug", "demo-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.topic_research_taste.assert_called_once_with(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_record_taste(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.record_research_taste.return_value = {"topic_slug": "demo-topic", "research_taste_entry": {"taste_kind": "formalism"}}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "record-taste",
                    "--topic-slug",
                    "demo-topic",
                    "--kind",
                    "formalism",
                    "--summary",
                    "Prefer operator-algebra notation first.",
                    "--formalism",
                    "operator_algebra",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.record_research_taste.assert_called_once()

    def test_main_dispatches_scratch_log(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.topic_scratchpad.return_value = {"topic_slug": "demo-topic", "scratchpad": {"status": "active"}}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "scratch-log", "--topic-slug", "demo-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.topic_scratchpad.assert_called_once_with(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_record_scratch_note(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.record_scratch_note.return_value = {"topic_slug": "demo-topic", "scratchpad_entry": {"entry_kind": "route_comparison"}}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "record-scratch-note",
                    "--topic-slug",
                    "demo-topic",
                    "--kind",
                    "route_comparison",
                    "--summary",
                    "Compare the theorem-facing and benchmark-first routes.",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.record_scratch_note.assert_called_once()

    def test_main_dispatches_record_negative_result(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.record_negative_result.return_value = {"topic_slug": "demo-topic", "scratchpad_entry": {"entry_kind": "negative_result"}}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "record-negative-result",
                    "--topic-slug",
                    "demo-topic",
                    "--summary",
                    "The portability extrapolation failed.",
                    "--failure-kind",
                    "regime_mismatch",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.record_negative_result.assert_called_once()

    def test_main_dispatches_seed_l2_direction(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.seed_l2_direction.return_value = {"direction": "tfim-benchmark-first"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "seed-l2-direction", "--direction", "tfim-benchmark-first"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.seed_l2_direction.assert_called_once_with(
            direction="tfim-benchmark-first",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_consult_l2(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.consult_l2.return_value = {"retrieval_profile": "l3_candidate_formation"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "consult-l2",
                    "--query-text",
                    "TFIM exact diagonalization benchmark workflow",
                    "--retrieval-profile",
                    "l3_candidate_formation",
                    "--max-primary-hits",
                    "2",
                    "--include-staging",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.consult_l2.assert_called_once_with(
            query_text="TFIM exact diagonalization benchmark workflow",
            retrieval_profile="l3_candidate_formation",
            max_primary_hits=2,
            include_staging=True,
            topic_slug=None,
            stage="L3",
            run_id=None,
            updated_by="aitp-cli",
            record_consultation=False,
        )

    def test_main_dispatches_consult_l2_with_recorded_consultation(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.consult_l2.return_value = {"consultation": {"consultation_index_path": "x"}}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "consult-l2",
                    "--query-text",
                    "Benchmark-first validation",
                    "--retrieval-profile",
                    "l1_provisional_understanding",
                    "--topic-slug",
                    "demo-topic",
                    "--stage",
                    "L3",
                    "--run-id",
                    "run-001",
                    "--record-consultation",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.consult_l2.assert_called_once_with(
            query_text="Benchmark-first validation",
            retrieval_profile="l1_provisional_understanding",
            max_primary_hits=None,
            include_staging=False,
            topic_slug="demo-topic",
            stage="L3",
            run_id="run-001",
            updated_by="aitp-cli",
            record_consultation=True,
        )

    def test_main_dispatches_compile_l2_map(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.compile_l2_workspace_map.return_value = {"json_path": "compiled/map.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "compile-l2-map"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.compile_l2_workspace_map.assert_called_once_with()

    def test_main_dispatches_compile_l2_graph_report(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.compile_l2_graph_report.return_value = {"json_path": "compiled/graph-report.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "compile-l2-graph-report"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.compile_l2_graph_report.assert_called_once_with()

    def test_main_dispatches_compile_l2_knowledge_report(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.compile_l2_knowledge_report.return_value = {"json_path": "compiled/knowledge-report.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "compile-l2-knowledge-report"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.compile_l2_knowledge_report.assert_called_once_with()

    def test_main_dispatches_compile_source_catalog(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.compile_source_catalog.return_value = {"json_path": "source-layer/compiled/source_catalog.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "compile-source-catalog"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.compile_source_catalog.assert_called_once_with()

    def test_main_dispatches_trace_source_citations(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.trace_source_citations.return_value = {"json_path": "source-layer/compiled/citation_traversals/shared.json"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                ["aitp", "trace-source-citations", "--canonical-source-id", "source_identity:doi:10-1000-shared-paper"],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.trace_source_citations.assert_called_once_with(
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
        )

    def test_main_dispatches_compile_source_family(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.compile_source_family.return_value = {"json_path": "source-layer/compiled/source_families/paper.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "compile-source-family", "--source-type", "paper"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.compile_source_family.assert_called_once_with(source_type="paper")

    def test_main_dispatches_export_source_bibtex(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.export_source_bibtex.return_value = {"bibtex_path": "source-layer/compiled/bibtex_exports/shared.bib"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "export-source-bibtex",
                    "--canonical-source-id",
                    "source_identity:doi:10-1000-shared-paper",
                    "--include-neighbors",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.export_source_bibtex.assert_called_once_with(
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            include_neighbors=True,
        )

    def test_main_dispatches_import_bibtex_sources(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.import_bibtex_sources.return_value = {"source_index_path": "source-layer/topics/demo-topic/source_index.jsonl"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "import-bibtex-sources",
                    "--topic-slug",
                    "demo-topic",
                    "--bibtex-path",
                    "demo-import.bib",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.import_bibtex_sources.assert_called_once_with(
            topic_slug="demo-topic",
            bibtex_path="demo-import.bib",
            updated_by="aitp-cli",
        )

    def test_main_dispatches_sync_l1_graph_export_to_theoretical_physics_brain(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.sync_l1_graph_export_to_theoretical_physics_brain.return_value = {
                "target_root": "D:/brain/90 AITP Imports/concept-graphs/demo-topic"
            }
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "sync-l1-graph-export-to-theoretical-physics-brain",
                    "--topic-slug",
                    "demo-topic",
                    "--target-root",
                    "D:/brain",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.sync_l1_graph_export_to_theoretical_physics_brain.assert_called_once_with(
            topic_slug="demo-topic",
            updated_by="aitp-cli",
            target_root="D:/brain",
        )

    def test_main_dispatches_audit_l2_hygiene(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.audit_l2_hygiene.return_value = {"json_path": "hygiene/report.json"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "audit-l2-hygiene"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.audit_l2_hygiene.assert_called_once_with()

    def test_main_dispatches_collaborator_memory_commands(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.get_collaborator_memory.return_value = {"status": "available", "entries": []}
            mock_service.record_collaborator_memory.return_value = {"memory_domain": "collaborator"}
            mock_factory.return_value = mock_service

            with patch.object(sys, "argv", ["aitp", "collaborator-memory", "--topic-slug", "demo-topic"]):
                read_exit = aitp_cli.main()
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "record-collaborator-memory",
                    "--memory-kind",
                    "preference",
                    "--summary",
                    "Prefer theorem-facing routes first.",
                    "--topic-slug",
                    "demo-topic",
                    "--tag",
                    "formal-theory",
                ],
            ):
                write_exit = aitp_cli.main()

        self.assertEqual(read_exit, 0)
        self.assertEqual(write_exit, 0)
        mock_service.get_collaborator_memory.assert_called_once_with(topic_slug="demo-topic", limit=10)
        mock_service.record_collaborator_memory.assert_called_once()
        self.assertEqual(mock_service.record_collaborator_memory.call_args.kwargs["memory_kind"], "preference")
        self.assertEqual(mock_service.record_collaborator_memory.call_args.kwargs["tags"], ["formal-theory"])

    def test_main_dispatches_replay_topic(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.kernel_root = Path("D:/demo/kernel")
            mock_factory.return_value = mock_service
            with patch.object(
                aitp_cli,
                "materialize_topic_replay_bundle",
                return_value={"payload": {"kind": "topic_replay_bundle"}, "json_path": "a", "markdown_path": "b"},
            ) as mock_replay:
                with patch.object(sys, "argv", ["aitp", "replay-topic", "--topic-slug", "demo-topic"]):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_replay.assert_called_once_with(mock_service.kernel_root, "demo-topic")

    def test_main_dispatches_stage_l2_provisional(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.kernel_root = Path("D:/demo/kernel")
            mock_factory.return_value = mock_service
            with patch.object(
                aitp_cli,
                "dispatch_l2_graph_command",
                return_value={"entry": {"entry_id": "staging:demo"}},
            ) as mock_stage:
                with patch.object(
                    sys,
                    "argv",
                    [
                        "aitp",
                        "stage-l2-provisional",
                        "--topic-slug",
                        "demo-topic",
                        "--entry-kind",
                        "workflow_draft",
                        "--title",
                        "Demo draft",
                        "--summary",
                        "A provisional reusable workflow draft.",
                    ],
                ):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_stage.assert_called_once()

    def test_main_dispatches_topics(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.list_active_topics.return_value = {"topic_count": 1, "topics": [{"topic_slug": "demo-topic"}]}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "topics"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.list_active_topics.assert_called_once()

    def test_main_dispatches_focus_pause_resume_topic(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.focus_topic.return_value = {"topic_slug": "demo-topic", "status": "focused"}
            mock_service.pause_topic.return_value = {"topic_slug": "demo-topic", "status": "paused"}
            mock_service.resume_topic.return_value = {"topic_slug": "demo-topic", "status": "ready"}
            mock_factory.return_value = mock_service

            with patch.object(sys, "argv", ["aitp", "focus-topic", "--topic-slug", "demo-topic"]):
                focus_exit = aitp_cli.main()
            with patch.object(sys, "argv", ["aitp", "pause-topic", "--topic-slug", "demo-topic"]):
                pause_exit = aitp_cli.main()
            with patch.object(sys, "argv", ["aitp", "resume-topic", "--topic-slug", "demo-topic"]):
                resume_exit = aitp_cli.main()

        self.assertEqual(focus_exit, 0)
        self.assertEqual(pause_exit, 0)
        self.assertEqual(resume_exit, 0)
        mock_service.focus_topic.assert_called_once()
        mock_service.pause_topic.assert_called_once()
        mock_service.resume_topic.assert_called_once()

    def test_main_dispatches_dependency_commands(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.set_topic_dependency.return_value = {"topic_slug": "demo-topic", "status": "dependency_blocked"}
            mock_service.clear_topic_dependency.return_value = {"topic_slug": "demo-topic", "status": "dependency_cleared"}
            mock_service.clear_all_topic_dependencies.return_value = {"topic_slug": "demo-topic", "status": "dependencies_cleared"}
            mock_factory.return_value = mock_service

            with patch.object(sys, "argv", ["aitp", "block-topic", "--topic-slug", "demo-topic", "--blocked-by", "other-topic", "--reason", "Need prerequisite"]):
                block_exit = aitp_cli.main()
            with patch.object(sys, "argv", ["aitp", "unblock-topic", "--topic-slug", "demo-topic", "--blocked-by", "other-topic"]):
                unblock_exit = aitp_cli.main()
            with patch.object(sys, "argv", ["aitp", "clear-topic-dependencies", "--topic-slug", "demo-topic"]):
                clear_exit = aitp_cli.main()

        self.assertEqual(block_exit, 0)
        self.assertEqual(unblock_exit, 0)
        self.assertEqual(clear_exit, 0)
        mock_service.set_topic_dependency.assert_called_once()
        mock_service.clear_topic_dependency.assert_called_once()
        mock_service.clear_all_topic_dependencies.assert_called_once()

    def test_main_dispatches_session_start(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.start_chat_session.return_value = {"topic_slug": "demo-topic", "routing": {"route": "implicit_current_topic"}}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "session-start", "--load-profile", "light", "继续这个 topic，方向改成 X"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.start_chat_session.assert_called_once()
        self.assertEqual(mock_service.start_chat_session.call_args.kwargs["load_profile"], "light")

    def test_main_dispatches_text_based_steer_topic(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.steer_topic_from_text.return_value = {
                "detected": True,
                "decision": "redirect",
                "direction": "modular bootstrap constraints",
            }
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "steer-topic",
                    "--topic-slug",
                    "demo-topic",
                    "--text",
                    "继续这个 topic，方向改成 modular bootstrap constraints",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.steer_topic_from_text.assert_called_once_with(
            topic_slug="demo-topic",
            text="继续这个 topic，方向改成 modular bootstrap constraints",
            run_id=None,
            updated_by="aitp-cli",
            topic_state=None,
            control_note=None,
        )

    def test_main_dispatches_explore(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.explore.return_value = {"status": "lightweight_open"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "explore", "Sketch a speculative route without full topic bootstrap"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.explore.assert_called_once()

    def test_main_dispatches_promote_exploration(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.promote_exploration.return_value = {"target_mode": "current_topic"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "promote-exploration", "--exploration-id", "explore-demo", "--current-topic"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.promote_exploration.assert_called_once()

    def test_main_renders_human_friendly_runtime_error_without_traceback(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.install_agent.side_effect = RuntimeError(
                "AITP could not finish install-agent.\n"
                "Command: python -m pip install aitp-kernel\n"
                "Exit code: 23\n"
                "Error: access denied\n"
                "Try:\n"
                "- Check that Python and pip can write to the target environment.\n"
            )
            mock_factory.return_value = mock_service

            stdout_stream = io.StringIO()
            stderr_stream = io.StringIO()
            with patch.object(sys, "argv", ["aitp", "install-agent", "--agent", "codex"]):
                with redirect_stdout(stdout_stream), redirect_stderr(stderr_stream):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout_stream.getvalue(), "")
        stderr_output = stderr_stream.getvalue()
        self.assertIn("AITP could not finish install-agent.", stderr_output)
        self.assertIn("Check that Python and pip can write to the target environment.", stderr_output)
        self.assertNotIn("Traceback", stderr_output)

    def test_main_dispatches_resume_with_load_profile(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.orchestrate.return_value = {"topic_slug": "demo-topic"}
            mock_service.remember_current_topic.return_value = {"topic_slug": "demo-topic"}
            mock_service.refresh_runtime_context.return_value = {"load_profile": "full"}
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "resume", "--topic-slug", "demo-topic", "--load-profile", "full"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.refresh_runtime_context.assert_called_once()
        self.assertEqual(mock_service.refresh_runtime_context.call_args.kwargs["load_profile"], "full")

    def test_main_dispatches_emit_decision_without_service(self) -> None:
        with patch.object(aitp_cli, "emit_decision_point", return_value={"decision_point": {"id": "dp:demo"}}) as mock_emit:
            with patch.object(aitp_cli, "_service_from_args") as mock_factory:
                with patch.object(
                    sys,
                    "argv",
                    [
                        "aitp",
                        "emit-decision",
                        "--topic-slug",
                        "demo-topic",
                        "--question",
                        "Clarify the validation route?",
                        "--options",
                        '[{"label":"small-system","description":"Use exact diagonalization"},{"label":"larger-system","description":"Use a larger finite-size lane"}]',
                        "--blocking",
                        "false",
                    ],
                ):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_emit.assert_called_once()
        mock_factory.assert_not_called()

    def test_main_dispatches_resolve_decision_without_service(self) -> None:
        with patch.object(aitp_cli, "resolve_decision_point", return_value={"decision_point": {"id": "dp:demo"}}) as mock_resolve:
            with patch.object(aitp_cli, "_service_from_args") as mock_factory:
                with patch.object(
                    sys,
                    "argv",
                    ["aitp", "resolve-decision", "--topic-slug", "demo-topic", "--decision-id", "dp:demo", "--option", "0"],
                ):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_resolve.assert_called_once()
        mock_factory.assert_not_called()

    def test_main_dispatches_list_decisions_without_service(self) -> None:
        with patch.object(aitp_cli, "list_pending_decision_points", return_value=[{"id": "dp:demo"}]) as mock_list:
            with patch.object(aitp_cli, "_service_from_args") as mock_factory:
                with patch.object(sys, "argv", ["aitp", "list-decisions", "--topic-slug", "demo-topic", "--pending-only"]):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_list.assert_called_once()
        mock_factory.assert_not_called()

    def test_main_dispatches_trace_decision_without_service(self) -> None:
        with patch.object(aitp_cli, "record_decision_trace", return_value={"decision_trace": {"id": "dt:demo"}}) as mock_trace:
            with patch.object(aitp_cli, "_service_from_args") as mock_factory:
                with patch.object(
                    sys,
                    "argv",
                    [
                        "aitp",
                        "trace-decision",
                        "--topic-slug",
                        "demo-topic",
                        "--summary",
                        "Selected the smaller benchmark lane.",
                        "--chosen",
                        "small-system",
                        "--rationale",
                        "It closes the benchmark gap first.",
                    ],
                ):
                    exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_trace.assert_called_once()
        mock_factory.assert_not_called()

    def test_main_dispatches_chronicle_finalize_without_service(self) -> None:
        latest = {"id": "chronicle:demo-topic-20260328010101", "topic_slug": "demo-topic"}
        with patch.object(aitp_cli, "get_latest_chronicle", return_value=latest) as mock_latest:
            with patch.object(
                aitp_cli,
                "finalize_chronicle",
                return_value={"chronicle": {"id": "chronicle:demo-topic-20260328010101", "session_end": "2026-03-28T00:00:00+00:00"}},
            ) as mock_finalize:
                with patch.object(aitp_cli, "_service_from_args") as mock_factory:
                    with patch.object(
                        sys,
                        "argv",
                        [
                            "aitp",
                            "chronicle",
                            "--topic-slug",
                            "demo-topic",
                            "--finalize",
                            "--ending-state",
                            "Ready for the next bounded action.",
                            "--next-step",
                            "Run the larger-system lane.",
                            "--summary",
                            "Closed the current session.",
                        ],
                    ):
                        exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_latest.assert_called_once()
        mock_finalize.assert_called_once()
        mock_factory.assert_not_called()

    def test_promotion_commands_are_registered(self) -> None:
        parser = aitp_cli.build_parser()

        request_args = parser.parse_args(
            [
                "request-promotion",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--route",
                "L3->L4_auto->L2_auto",
                "--backend-id",
                "backend:theoretical-physics-knowledge-network",
            ]
        )
        self.assertEqual(request_args.command, "request-promotion")
        self.assertEqual(request_args.backend_id, "backend:theoretical-physics-knowledge-network")
        self.assertEqual(request_args.route, "L3->L4_auto->L2_auto")

        approve_args = parser.parse_args(
            [
                "approve-promotion",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--human-modification",
                "statement=Narrowed to weak coupling only:The original candidate overstated the regime.",
            ]
        )
        self.assertEqual(approve_args.command, "approve-promotion")
        self.assertEqual(approve_args.human_modification[0]["field"], "statement")

        reject_args = parser.parse_args(
            ["reject-promotion", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo"]
        )
        self.assertEqual(reject_args.command, "reject-promotion")

        promote_args = parser.parse_args(
            [
                "promote",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--target-backend-root",
                "/tmp/tpkn",
            ]
        )
        self.assertEqual(promote_args.command, "promote")
        self.assertEqual(promote_args.target_backend_root, "/tmp/tpkn")

        coverage_args = parser.parse_args(
            [
                "coverage-audit",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--source-section",
                "sec:intro",
                "--covered-section",
                "sec:intro",
                "--notation-binding",
                "H=Hamiltonian",
                "--agent-vote",
                "skeptic=no_major_gap",
                "--supporting-regression-question-id",
                "regression_question:demo",
                "--supporting-oracle-id",
                "question_oracle:demo",
                "--supporting-regression-run-id",
                "regression_run:demo",
                "--promotion-blocker",
                "Need cited recovery",
                "--followup-gap-id",
                "open_gap:demo",
                "--split-required",
                "--cited-recovery-required",
                "--topic-completion-status",
                "promotion-blocked",
            ]
        )
        self.assertEqual(coverage_args.command, "coverage-audit")
        self.assertEqual(coverage_args.notation_binding[0]["symbol"], "H")
        self.assertEqual(coverage_args.agent_vote[0]["role"], "skeptic")
        self.assertEqual(coverage_args.supporting_regression_question_id[0], "regression_question:demo")
        self.assertTrue(coverage_args.split_required)
        self.assertTrue(coverage_args.cited_recovery_required)

        formal_theory_args = parser.parse_args(
            [
                "formal-theory-audit",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--formal-theory-role",
                "trusted_target",
                "--statement-graph-role",
                "target_statement",
                "--faithfulness-status",
                "reviewed",
                "--faithfulness-strategy",
                "bounded source-to-target map",
                "--comparator-audit-status",
                "passed",
                "--attribution-requirement",
                "Preserve source citation.",
                "--prerequisite-closure-status",
                "closed",
            ]
        )
        self.assertEqual(formal_theory_args.command, "formal-theory-audit")
        self.assertEqual(formal_theory_args.formal_theory_role, "trusted_target")
        self.assertEqual(formal_theory_args.attribution_requirement[0], "Preserve source citation.")

        analytical_review_args = parser.parse_args(
            [
                "analytical-review",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--check",
                "limiting_case=weak-coupling:passed:Matches the known free limit.",
                "--check",
                "source_cross_reference=intro-vs-appendix:passed:Cross-referenced source sections agree on the bounded limit.",
                "--source-anchor",
                "paper:demo-source#sec:intro",
                "--assumption",
                "assumption:weak-coupling-regime",
                "--regime-note",
                "Restricted to the weak-coupling regime declared in the source.",
                "--reading-depth",
                "targeted",
            ]
        )
        self.assertEqual(analytical_review_args.command, "analytical-review")
        self.assertEqual(analytical_review_args.check[0]["kind"], "limiting_case")
        self.assertEqual(analytical_review_args.check[0]["status"], "passed")
        self.assertEqual(analytical_review_args.check[1]["kind"], "source_cross_reference")
        self.assertEqual(analytical_review_args.source_anchor[0], "paper:demo-source#sec:intro")
        self.assertEqual(analytical_review_args.reading_depth, "targeted")

        auto_promote_args = parser.parse_args(
            [
                "auto-promote",
                "--topic-slug",
                "demo-topic",
                "--candidate-id",
                "candidate:demo",
                "--target-backend-root",
                "/tmp/tpkn",
            ]
        )
        self.assertEqual(auto_promote_args.command, "auto-promote")
        self.assertEqual(auto_promote_args.target_backend_root, "/tmp/tpkn")

    def test_main_dispatches_formal_theory_audit(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.audit_formal_theory.return_value = {"overall_status": "ready"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "formal-theory-audit",
                    "--topic-slug",
                    "demo-topic",
                    "--candidate-id",
                    "candidate:demo",
                    "--formal-theory-role",
                    "trusted_target",
                    "--statement-graph-role",
                    "target_statement",
                    "--faithfulness-status",
                    "reviewed",
                    "--faithfulness-strategy",
                    "bounded source-to-target map",
                    "--comparator-audit-status",
                    "passed",
                    "--attribution-requirement",
                    "Preserve source citation.",
                    "--prerequisite-closure-status",
                    "closed",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.audit_formal_theory.assert_called_once()

    def test_main_dispatches_statement_compilation(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.prepare_statement_compilation.return_value = {"status": "needs_repair"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "statement-compilation",
                    "--topic-slug",
                    "demo-topic",
                    "--candidate-id",
                    "candidate:demo",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.prepare_statement_compilation.assert_called_once()

    def test_main_dispatches_analytical_review(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.audit_analytical_review.return_value = {"overall_status": "ready"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "analytical-review",
                    "--topic-slug",
                    "demo-topic",
                    "--candidate-id",
                    "candidate:demo",
                    "--check",
                    "limiting_case=weak-coupling:passed:Matches the known free limit.",
                    "--check",
                    "dimensional_consistency=gap-scaling:passed:Units remain dimensionless after rescaling.",
                    "--source-anchor",
                    "paper:demo-source#sec:intro",
                    "--assumption",
                    "assumption:weak-coupling-regime",
                    "--regime-note",
                    "Bounded to the weak-coupling regime recorded in the source.",
                    "--reading-depth",
                    "targeted",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.audit_analytical_review.assert_called_once()

    def test_main_dispatches_approve_promotion_with_human_modification(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.approve_promotion.return_value = {"status": "approved"}
            mock_factory.return_value = mock_service
            with patch.object(
                sys,
                "argv",
                [
                    "aitp",
                    "approve-promotion",
                    "--topic-slug",
                    "demo-topic",
                    "--candidate-id",
                    "candidate:demo",
                    "--human-modification",
                    "statement=Narrowed to weak coupling only:The original candidate overstated the regime.",
                ],
            ):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.approve_promotion.assert_called_once()
        kwargs = mock_service.approve_promotion.call_args.kwargs
        self.assertEqual(kwargs["human_modifications"][0]["field"], "statement")

    def test_install_agent_accepts_claude_code(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["install-agent", "--agent", "claude-code"])
        self.assertEqual(args.command, "install-agent")
        self.assertEqual(args.agent, "claude-code")

    def test_install_agent_accepts_mcp_profile(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["install-agent", "--agent", "claude-code", "--mcp-profile", "review"])
        self.assertEqual(args.command, "install-agent")
        self.assertEqual(args.agent, "claude-code")
        self.assertEqual(args.mcp_profile, "review")

    def test_version_flag_reports_package_version(self) -> None:
        stream = io.StringIO()
        with patch.object(sys, "argv", ["aitp", "--version"]):
            with redirect_stdout(stream):
                with self.assertRaises(SystemExit) as exc_info:
                    aitp_cli.main()

        self.assertEqual(exc_info.exception.code, 0)
        self.assertIn("0.4.1", stream.getvalue())

    def test_doctor_human_output_summarizes_front_door_runtimes(self) -> None:
        doctor_payload = {
            "overall_status": "mixed_install",
            "package": {"name": "aitp", "status": "canonical_editable_install", "version": "0.4.1"},
            "layer_roots": {"L0": {"status": "present"}},
            "protocol_contracts": {"layer_map": {"status": "present"}},
            "runtime_convergence": {
                "front_door_runtimes": ["codex", "claude_code", "opencode"],
                "front_door_runtimes_converged": False,
                "front_door_ready_runtimes": ["codex"],
                "front_door_non_ready_runtimes": ["claude_code", "opencode"],
            },
            "full_convergence_repair": {
                "status": "recommended",
                "command": 'aitp migrate-local-install --workspace-root "D:\\Theoretical-Physics" --json',
            },
            "runtime_support_matrix": {
                "specialized_lanes": ["openclaw"],
                "deep_execution_parity": {
                    "baseline_runtime": "codex",
                    "parity_targets": ["claude_code", "opencode"],
                    "deferred_lanes": ["openclaw"],
                    "runtimes": {
                        "codex": {
                            "display_name": "Codex",
                            "status": "baseline_ready",
                            "maturity_class": "baseline",
                            "baseline_relationship": "baseline",
                            "acceptance_command": "python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime codex --json",
                            "blockers": [],
                        },
                        "claude_code": {
                            "display_name": "Claude Code",
                            "status": "probe_available",
                            "maturity_class": "parity_target",
                            "baseline_relationship": "parity_target",
                            "acceptance_command": "python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime claude_code --json",
                            "blockers": [],
                        },
                        "opencode": {
                            "display_name": "OpenCode",
                            "status": "front_door_blocked",
                            "maturity_class": "parity_target",
                            "baseline_relationship": "parity_target",
                            "acceptance_command": "python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime opencode --json",
                            "blockers": ["front_door_status:partial", "runtime_specific_probe_not_implemented"],
                        },
                        "openclaw": {
                            "display_name": "OpenClaw",
                            "status": "deferred",
                            "maturity_class": "specialized_lane",
                            "baseline_relationship": "deferred_specialized_lane",
                            "acceptance_command": "",
                            "blockers": ["deferred_from_v1.67_scope"],
                        },
                    },
                },
                "runtimes": {
                    "codex": {
                        "display_name": "Codex",
                        "status": "ready",
                        "maturity_class": "baseline",
                        "preferred_entry": "native `using-aitp` skill discovery",
                        "issues": [],
                        "remediation": {"status": "none_required", "issue_hints": []},
                    },
                    "claude_code": {
                        "display_name": "Claude Code",
                        "status": "stale",
                        "maturity_class": "parity_target",
                        "preferred_entry": "Claude SessionStart bootstrap",
                        "issues": ["runtime_skill_missing"],
                        "remediation": {
                            "status": "required",
                            "command": "aitp install-agent --agent claude-code --scope user",
                            "doc_path": "docs/INSTALL_CLAUDE_CODE.md",
                            "issue_hints": [
                                {
                                    "issue": "runtime_skill_missing",
                                    "hint": "Run `aitp install-agent --agent claude-code --scope user` to refresh Claude Code SessionStart assets.",
                                }
                            ],
                        },
                    },
                    "opencode": {
                        "display_name": "OpenCode",
                        "status": "partial",
                        "maturity_class": "parity_target",
                        "preferred_entry": "OpenCode plugin bootstrap",
                        "issues": ["opencode_config_missing"],
                        "remediation": {
                            "status": "required",
                            "command": 'aitp migrate-local-install --workspace-root "D:\\Theoretical-Physics" --agent opencode --json',
                            "doc_path": "docs/INSTALL_OPENCODE.md",
                            "issue_hints": [
                                {
                                    "issue": "opencode_config_missing",
                                    "hint": 'Run `aitp migrate-local-install --workspace-root "D:\\Theoretical-Physics" --json` to enable the canonical OpenCode plugin path.',
                                }
                            ],
                        },
                    },
                    "openclaw": {
                        "display_name": "OpenClaw",
                        "status": "ready",
                        "maturity_class": "specialized_lane",
                        "preferred_entry": 'aitp loop --topic-slug <topic_slug> --human-request "<task>"',
                        "issues": [],
                        "remediation": {"status": "none_required", "issue_hints": []},
                    },
                },
            },
            "deep_execution_parity": {
                "baseline_runtime": "codex",
                "baseline_status": "baseline_ready",
                "parity_targets": ["claude_code", "opencode"],
                "parity_targets_converged": False,
                "verified_targets": [],
                "pending_targets": ["claude_code", "opencode"],
                "blocked_targets": ["opencode"],
            },
        }

        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.ensure_cli_installed.return_value = doctor_payload
            mock_factory.return_value = mock_service
            stream = io.StringIO()
            with patch.object(sys, "argv", ["aitp", "doctor"]):
                with redirect_stdout(stream):
                    exit_code = aitp_cli.main()

        output = stream.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("AITP Doctor", output)
        self.assertIn("Package: canonical_editable_install (aitp 0.4.1)", output)
        self.assertIn("Front-door convergence: no", output)
        self.assertIn("Deep-execution parity: no", output)
        self.assertIn("Codex: baseline_ready", output)
        self.assertIn("Acceptance: python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime codex --json", output)
        self.assertIn("Claude Code: probe_available", output)
        self.assertIn("OpenCode: front_door_blocked", output)
        self.assertIn("Full repair: aitp migrate-local-install", output)
        self.assertIn("Claude Code: stale", output)
        self.assertIn("Repair: aitp install-agent --agent claude-code --scope user", output)
        self.assertIn("Machine view: aitp doctor --json", output)
        self.assertNotIn("runtime support matrix:", output.lower())

    def test_migrate_local_install_and_doctor_workspace_flags_are_registered(self) -> None:
        parser = aitp_cli.build_parser()
        migrate_args = parser.parse_args(
            ["migrate-local-install", "--workspace-root", "D:\\BaiduSyncdisk\\Theoretical-Physics", "--agent", "codex"]
        )
        self.assertEqual(migrate_args.command, "migrate-local-install")
        self.assertEqual(migrate_args.workspace_root, "D:\\BaiduSyncdisk\\Theoretical-Physics")
        self.assertEqual(migrate_args.agent, ["codex"])

        doctor_args = parser.parse_args(["doctor", "--workspace-root", "D:\\BaiduSyncdisk\\Theoretical-Physics"])
        self.assertEqual(doctor_args.command, "doctor")
        self.assertEqual(doctor_args.workspace_root, "D:\\BaiduSyncdisk\\Theoretical-Physics")

    def test_main_renders_compact_human_status_and_next_and_full_dashboard(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            runtime_root = Path("D:/demo-kernel/runtime/topics/demo-topic")
            status_payload = {
                "topic_slug": "demo-topic",
                "title": "Demo Topic",
                "current_stage": "L1",
                "research_mode": "formal_derivation",
                "selected_action_summary": "Inspect the graph export before continuing.",
                "next_action_hint": "Run 'aitp next --topic-slug demo-topic' to inspect the bounded action queue.",
                "runtime_protocol_note_path": str(runtime_root / "runtime_protocol.generated.md"),
                "must_read_now": [
                    {"path": "runtime/topics/demo-topic/topic_dashboard.md"},
                    {"path": "runtime/topics/demo-topic/research_question.contract.md"},
                ],
                "open_gap_summary": {"status": "clear"},
                "promotion_readiness": {"status": "not_requested"},
                "topic_completion": {"status": "not_assessed"},
                "statement_compilation": {"status": "empty"},
                "lean_bridge": {"status": "empty"},
                "primary_runtime_surfaces": {
                    "primary": {
                        "runtime_human": "runtime/topics/demo-topic/topic_dashboard.md",
                    }
                },
            }
            next_payload = {
                "topic_slug": "demo-topic",
                "selected_action_summary": "Inspect the graph export before continuing.",
                "open_next": "runtime/topics/demo-topic/topic_dashboard.md",
                "must_read_now": [
                    {"path": "runtime/topics/demo-topic/topic_dashboard.md"},
                    {"path": "runtime/topics/demo-topic/research_question.contract.md"},
                ],
                "open_gap_summary": {"status": "clear"},
            }
            mock_service.topic_status.return_value = status_payload
            mock_service.topic_next.return_value = next_payload
            mock_service.kernel_root = Path("D:/demo-kernel")
            mock_factory.return_value = mock_service

            with patch("pathlib.Path.exists", return_value=True), patch(
                "pathlib.Path.read_text",
                return_value="# Demo Dashboard\n\nFull dashboard body.\n",
            ):
                status_stream = io.StringIO()
                with patch.object(sys, "argv", ["aitp", "status", "--topic-slug", "demo-topic"]):
                    with redirect_stdout(status_stream):
                        status_exit = aitp_cli.main()

                verbose_stream = io.StringIO()
                with patch.object(sys, "argv", ["aitp", "status", "--topic-slug", "demo-topic", "--verbose"]):
                    with redirect_stdout(verbose_stream):
                        verbose_exit = aitp_cli.main()

                next_stream = io.StringIO()
                with patch.object(sys, "argv", ["aitp", "next", "--topic-slug", "demo-topic"]):
                    with redirect_stdout(next_stream):
                        next_exit = aitp_cli.main()

                full_stream = io.StringIO()
                with patch.object(sys, "argv", ["aitp", "status", "--topic-slug", "demo-topic", "--full"]):
                    with redirect_stdout(full_stream):
                        full_exit = aitp_cli.main()

        self.assertEqual(status_exit, 0)
        self.assertEqual(verbose_exit, 0)
        self.assertEqual(next_exit, 0)
        self.assertEqual(full_exit, 0)
        status_output = status_stream.getvalue()
        verbose_output = verbose_stream.getvalue()
        next_output = next_stream.getvalue()
        full_output = full_stream.getvalue()
        self.assertIn("AITP Status", status_output)
        self.assertIn("Topic: Demo Topic", status_output)
        self.assertIn("Topic slug: demo-topic", status_output)
        self.assertIn("Stage: L1", status_output)
        self.assertIn("Status: active", status_output)
        self.assertIn("Next: Inspect the graph export before continuing.", status_output)
        self.assertIn("Machine view: aitp status --topic-slug demo-topic --json", status_output)
        self.assertIn("Key sections", verbose_output)
        self.assertIn("Mode: formal_derivation", verbose_output)
        self.assertIn("Promotion readiness: not_requested", verbose_output)
        self.assertIn("Topic completion: not_assessed", verbose_output)
        self.assertIn("AITP Next", next_output)
        self.assertIn("Do: Inspect the graph export before continuing.", next_output)
        self.assertIn("Read now: runtime/topics/demo-topic/topic_dashboard.md", next_output)
        self.assertIn("Machine view: aitp next --topic-slug demo-topic --json", next_output)
        self.assertIn("# Demo Dashboard", full_output)
        self.assertIn("Full dashboard body.", full_output)

    def test_main_dispatches_hello(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            mock_service = MagicMock()
            mock_service.hello_topic.return_value = {
                "topic_slug": "demo-topic",
                "install": {"overall_status": "pass"},
                "topic": {"topic_slug": "demo-topic"},
                "status": {"selected_action_summary": "Read the topic dashboard."},
            }
            mock_factory.return_value = mock_service
            with patch.object(sys, "argv", ["aitp", "hello", "--topic", "Demo topic", "--question", "What is the first bounded question?"]):
                exit_code = aitp_cli.main()

        self.assertEqual(exit_code, 0)
        mock_service.hello_topic.assert_called_once_with(
            topic="Demo topic",
            question="What is the first bounded question?",
            mode="formal_theory",
            updated_by="aitp-cli",
            arxiv_ids=[],
            local_note_paths=[],
        )

    def test_main_renders_progressive_help_surfaces(self) -> None:
        with patch.object(aitp_cli, "_service_from_args") as mock_factory:
            core_stream = io.StringIO()
            with patch.object(sys, "argv", ["aitp", "help"]):
                with redirect_stdout(core_stream):
                    core_exit = aitp_cli.main()

            all_stream = io.StringIO()
            with patch.object(sys, "argv", ["aitp", "help", "--all"]):
                with redirect_stdout(all_stream):
                    all_exit = aitp_cli.main()

        self.assertEqual(core_exit, 0)
        self.assertEqual(all_exit, 0)
        mock_factory.assert_not_called()

        core_output = core_stream.getvalue()
        all_output = all_stream.getvalue()

        self.assertIn("AITP Help", core_output)
        self.assertIn("Core commands", core_output)
        self.assertIn("session-start", core_output)
        self.assertIn("consult-l2", core_output)
        self.assertIn("See everything: aitp help --all", core_output)
        self.assertNotIn("new-topic", core_output)

        self.assertIn("AITP Help", all_output)
        self.assertIn("All registered commands", all_output)
        self.assertIn("Core commands", all_output)
        self.assertIn("Topic lifecycle", all_output)
        self.assertIn("new-topic", all_output)
        self.assertIn("doctor", all_output)


if __name__ == "__main__":
    unittest.main()
