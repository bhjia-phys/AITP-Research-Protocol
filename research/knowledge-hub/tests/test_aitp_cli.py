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

    def test_install_agent_accepts_claude_code(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["install-agent", "--agent", "claude-code"])
        self.assertEqual(args.command, "install-agent")
        self.assertEqual(args.agent, "claude-code")


if __name__ == "__main__":
    unittest.main()
