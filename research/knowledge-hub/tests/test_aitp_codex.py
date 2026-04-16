from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
                        "innovation_direction_path": "/tmp/innovation-direction.md",
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
            "runtime_protocol": {
                "runtime_protocol_note_path": "/tmp/runtime/demo-topic/runtime_protocol.generated.md",
            },
            "session_start": {
                "session_start_contract_path": "/tmp/runtime/demo-topic/session_start.contract.json",
                "session_start_note_path": "/tmp/runtime/demo-topic/session_start.generated.md",
                "human_interaction_posture": {
                    "requires_human_input_now": False,
                    "summary": "No active human checkpoint is currently blocking the bounded loop.",
                    "next_action": "AITP may continue bounded work autonomously until a real checkpoint or blocker appears.",
                },
                "autonomy_posture": {
                    "mode": "continuous_iterative_verify",
                    "summary": "Keep the bounded L3-L4 loop running until validation succeeds, or until a real blocker, contradiction, or human checkpoint appears.",
                    "applied_max_auto_steps": 16,
                },
                "artifacts": {
                    "runtime_protocol_note_path": "/tmp/runtime/demo-topic/runtime_protocol.generated.md",
                },
                "theory_context_injection": {
                    "status": "active",
                    "fragments": [
                        {
                            "fragment_id": "theory-context:notation:demo-topic",
                            "kind": "notation_bindings",
                            "summary": "Notation bindings for the bounded theorem packet: H = Hamiltonian.",
                            "path": "/tmp/runtime/demo-topic/context_fragments/theory-context-notation.md",
                            "delivery_status": "inject_now",
                        }
                    ],
                },
            },
        }
        prompt = aitp_codex.build_codex_prompt(payload)
        self.assertIn("Use the installed `aitp-runtime` skill", prompt)
        self.assertIn("/tmp/runtime/demo-topic/session_start.generated.md", prompt)
        self.assertIn("/tmp/runtime/demo-topic/agent_brief.md", prompt)
        self.assertIn("/tmp/innovation-direction.md", prompt)
        self.assertIn("trust: `blocked`", prompt)
        self.assertIn("Human interaction posture", prompt)
        self.assertIn("No active human checkpoint is currently blocking the bounded loop.", prompt)
        self.assertIn("Autonomous continuation", prompt)
        self.assertIn("continuous_iterative_verify", prompt)
        self.assertIn("applied auto-step budget: `16`", prompt)
        self.assertIn("/tmp/runtime/demo-topic/context_fragments/theory-context-notation.md", prompt)
        self.assertIn("Theory context injection", prompt)
        self.assertIn("Continue the topic", prompt)

    def test_parser_accepts_topic_slug_and_task(self) -> None:
        parser = aitp_codex.build_parser()
        args = parser.parse_args(["--topic-slug", "demo-topic", "Continue demo"])
        self.assertEqual(args.topic_slug, "demo-topic")
        self.assertEqual(args.task, "Continue demo")

    def test_write_codex_bootstrap_receipt_materializes_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            payload = {
                "topic_slug": "demo-topic",
                "run_id": "2026-03-13-demo",
                "routing": {"route": "implicit_current_topic"},
                "session_start_contract_path": "/tmp/runtime/demo-topic/session_start.contract.json",
                "session_start_note_path": "/tmp/runtime/demo-topic/session_start.generated.md",
            }

            with patch("knowledge_hub.aitp_codex.Path.home", return_value=home):
                receipt_path = aitp_codex.write_codex_bootstrap_receipt(
                    payload=payload,
                    repo_root="D:/repo",
                    kernel_root="D:/repo/research/knowledge-hub",
                    updated_by="aitp-codex",
                )

            self.assertTrue(receipt_path.exists())
            rendered = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(rendered["receipt_kind"], "codex_bootstrap_receipt")
            self.assertEqual(rendered["entrypoint"], "aitp-codex")
            self.assertEqual(rendered["bootstrap_mode"], "aitp_codex_entrypoint")
            self.assertEqual(rendered["topic_slug"], "demo-topic")
            self.assertEqual(rendered["run_id"], "2026-03-13-demo")
            self.assertEqual(rendered["routing_route"], "implicit_current_topic")
            self.assertEqual(rendered["session_start_note_path"], payload["session_start_note_path"])

    def test_extract_topic_direction_change_supports_english_and_chinese(self) -> None:
        self.assertEqual(
            aitp_codex.extract_topic_direction_change(
                "continue this topic, direction changed to concrete Jones realization"
            ),
            "concrete Jones realization",
        )
        self.assertEqual(
            aitp_codex.extract_topic_direction_change("继续这个 topic，方向改成 concrete Jones realization"),
            "concrete Jones realization",
        )
        self.assertEqual(
            aitp_codex.extract_topic_direction_change(
                "继续这个 topic，方向改成 modular tensor category consistency checks，并先补验证路线。"
            ),
            "modular tensor category consistency checks",
        )

    def test_apply_topic_steering_translates_direction_change_into_service_call(self) -> None:
        calls: list[dict] = []

        class _FakeService:
            def steer_topic(self, **kwargs):  # noqa: ANN003
                calls.append(kwargs)
                return {"control_note_path": "runtime/topics/demo-topic/control_note.md"}

        normalized_task, payload, control_note = aitp_codex.apply_topic_steering(
            _FakeService(),  # type: ignore[arg-type]
            topic_slug="demo-topic",
            task="continue this topic, direction changed to concrete Jones realization",
            run_id="2026-03-13-demo",
            updated_by="aitp-codex",
            innovation_direction=None,
            steering_decision="continue",
        )

        self.assertEqual(
            normalized_task,
            "Continue the topic under updated innovation direction: concrete Jones realization",
        )
        self.assertEqual(control_note, "runtime/topics/demo-topic/control_note.md")
        self.assertIsNotNone(payload)
        self.assertEqual(calls[0]["topic_slug"], "demo-topic")
        self.assertEqual(calls[0]["innovation_direction"], "concrete Jones realization")


if __name__ == "__main__":
    unittest.main()
