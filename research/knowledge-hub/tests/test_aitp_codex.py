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

from knowledge_hub import aitp_codex


class AITPCodexTests(unittest.TestCase):
    def test_build_prompt_includes_runtime_and_trust_paths(self) -> None:
        payload = {
            "topic_slug": "demo-topic",
            "run_id": "2026-03-13-demo",
            "bootstrap": {
                "runtime_root": "/tmp/runtime/demo-topic",
                "files": {
                    "agent_brief": "/tmp/runtime/demo-topic/agent_brief.md",
                    "operator_console": "/tmp/runtime/demo-topic/operator_console.md",
                    "conformance_report": "/tmp/runtime/demo-topic/conformance_report.md",
                },
                "topic_state": {
                    "pointers": {
                        "control_note_path": "/tmp/control-note.md",
                    }
                },
            },
            "loop_state_path": "/tmp/runtime/demo-topic/loop_state.json",
            "loop_state": {
                "human_request": "Continue the topic",
                "exit_conformance": "pass",
                "capability_status": "ready",
                "trust_status": "blocked",
            },
            "capability_audit": {
                "capability_report_path": "/tmp/runtime/demo-topic/capability_report.md",
            },
            "trust_audit": {
                "trust_report_path": "/tmp/validation/demo-topic/trust_audit.md",
            },
        }
        prompt = aitp_codex.build_codex_prompt(payload)
        self.assertIn("Use the installed `aitp-runtime` skill", prompt)
        self.assertIn("/tmp/runtime/demo-topic/agent_brief.md", prompt)
        self.assertIn("trust: `blocked`", prompt)
        self.assertIn("Continue the topic", prompt)

    def test_parser_accepts_topic_slug_and_task(self) -> None:
        parser = aitp_codex.build_parser()
        args = parser.parse_args(["--topic-slug", "demo-topic", "Continue demo"])
        self.assertEqual(args.topic_slug, "demo-topic")
        self.assertEqual(args.task, "Continue demo")


if __name__ == "__main__":
    unittest.main()
