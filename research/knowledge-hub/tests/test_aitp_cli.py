from __future__ import annotations

import unittest
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

        status_args = parser.parse_args(["status", "--topic-slug", "demo-topic"])
        self.assertEqual(status_args.command, "status")

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

        verify_args = parser.parse_args(["verify", "--topic-slug", "demo-topic", "--mode", "proof"])
        self.assertEqual(verify_args.command, "verify")
        self.assertEqual(verify_args.mode, "proof")

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

        topics_args = parser.parse_args(["topics"])
        self.assertEqual(topics_args.command, "topics")

        current_topic_args = parser.parse_args(["current-topic"])
        self.assertEqual(current_topic_args.command, "current-topic")

        collaborator_memory_args = parser.parse_args(["collaborator-memory", "--topic-slug", "demo-topic"])
        self.assertEqual(collaborator_memory_args.command, "collaborator-memory")
        self.assertEqual(collaborator_memory_args.topic_slug, "demo-topic")

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
                "stage_provisional_l2_entry",
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
            ["approve-promotion", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo"]
        )
        self.assertEqual(approve_args.command, "approve-promotion")

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

    def test_install_agent_accepts_claude_code(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["install-agent", "--agent", "claude-code"])
        self.assertEqual(args.command, "install-agent")
        self.assertEqual(args.agent, "claude-code")

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


if __name__ == "__main__":
    unittest.main()
