from __future__ import annotations

import unittest
from pathlib import Path

import sys


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

    def test_install_agent_accepts_claude_code(self) -> None:
        parser = aitp_cli.build_parser()
        args = parser.parse_args(["install-agent", "--agent", "claude-code"])
        self.assertEqual(args.command, "install-agent")
        self.assertEqual(args.agent, "claude-code")


if __name__ == "__main__":
    unittest.main()
