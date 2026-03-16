from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub import aitp_mcp_server


def _parse(result: str) -> dict:
    payload = json.loads(result)
    if not isinstance(payload, dict):
        raise AssertionError("MCP result must be a JSON object")
    return payload


class _AITPStubSuccess:
    def orchestrate(self, **kwargs):  # noqa: ANN003
        return {"topic_slug": kwargs.get("topic_slug") or "demo-topic"}

    def get_runtime_state(self, topic_slug: str):
        return {"topic_slug": topic_slug, "resume_stage": "L3"}

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "phase": phase,
            "updated_by": updated_by,
            "conformance_state": {"overall_status": "pass"},
        }

    def scaffold_baseline(self, **kwargs):  # noqa: ANN003
        return {"baseline_id": "baseline:demo"}

    def scaffold_atomic_understanding(self, **kwargs):  # noqa: ANN003
        return {"method_id": "method-understanding:demo"}

    def scaffold_operation(self, **kwargs):  # noqa: ANN003
        return {"operation_id": "operation:demo"}

    def update_operation(self, **kwargs):  # noqa: ANN003
        return {"operation_id": "operation:demo", "baseline_status": "passed"}

    def audit_operation_trust(self, **kwargs):  # noqa: ANN003
        return {"overall_status": "pass", "operations": []}

    def capability_audit(self, **kwargs):  # noqa: ANN003
        return {"overall_status": "ready", "sections": {}, "recommendations": []}

    def run_topic_loop(self, **kwargs):  # noqa: ANN003
        return {"topic_slug": kwargs.get("topic_slug") or "demo-topic", "loop_state": {"exit_conformance": "pass"}}

    def install_agent(self, **kwargs):  # noqa: ANN003
        return {"installed": [{"path": "/tmp/demo", "kind": "skill"}]}


class _AITPStubFailure:
    def orchestrate(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("orchestrate boom")

    def get_runtime_state(self, topic_slug: str):
        raise RuntimeError("state boom")

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp"):
        raise RuntimeError("audit boom")

    def scaffold_baseline(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("baseline boom")

    def scaffold_atomic_understanding(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("atomize boom")

    def scaffold_operation(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("operation boom")

    def update_operation(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("update boom")

    def audit_operation_trust(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("trust boom")

    def capability_audit(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("capability boom")

    def run_topic_loop(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("loop boom")

    def install_agent(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("install boom")


class AITPMCPServerTests(unittest.TestCase):
    def test_aitp_tools_return_success_payloads(self) -> None:
        with patch.object(aitp_mcp_server, "service", _AITPStubSuccess()):
            bootstrap = _parse(aitp_mcp_server.aitp_bootstrap_topic(topic_slug="demo-topic"))
            state = _parse(aitp_mcp_server.aitp_get_runtime_state("demo-topic"))
            audit = _parse(aitp_mcp_server.aitp_audit_conformance("demo-topic", phase="exit"))
            baseline = _parse(
                aitp_mcp_server.aitp_scaffold_baseline(
                    "demo-topic",
                    "2026-03-13-demo",
                    "Public baseline",
                    "arXiv:0000.00000",
                    "qualitative agreement",
                )
            )
            atomize = _parse(
                aitp_mcp_server.aitp_scaffold_atomic_understanding(
                    "demo-topic",
                    "2026-03-13-demo",
                    "Finite-size spectral diagnostic",
                )
            )
            operation = _parse(
                aitp_mcp_server.aitp_scaffold_operation(
                    "demo-topic",
                    "2026-03-13-demo",
                    "Small-system validation backend",
                    "numerical",
                )
            )
            update = _parse(
                aitp_mcp_server.aitp_update_operation(
                    "demo-topic",
                    "2026-03-13-demo",
                    "Small-system validation backend",
                    baseline_status="passed",
                )
            )
            trust = _parse(aitp_mcp_server.aitp_audit_operation_trust("demo-topic", "2026-03-13-demo"))
            capability = _parse(aitp_mcp_server.aitp_audit_capability("demo-topic"))
            loop = _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic"))
            install = _parse(aitp_mcp_server.aitp_install_agent_wrapper("codex"))

        self.assertEqual(bootstrap["status"], "success")
        self.assertEqual(bootstrap["topic_slug"], "demo-topic")
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["topic_state"]["resume_stage"], "L3")
        self.assertEqual(audit["status"], "success")
        self.assertEqual(audit["conformance_state"]["overall_status"], "pass")
        self.assertEqual(baseline["status"], "success")
        self.assertEqual(atomize["status"], "success")
        self.assertEqual(operation["status"], "success")
        self.assertEqual(update["status"], "success")
        self.assertEqual(trust["status"], "success")
        self.assertEqual(capability["status"], "success")
        self.assertEqual(loop["status"], "success")
        self.assertEqual(install["status"], "success")

    def test_aitp_tools_return_error_shape_when_exceptions_occur(self) -> None:
        with patch.object(aitp_mcp_server, "service", _AITPStubFailure()):
            results = [
                _parse(aitp_mcp_server.aitp_bootstrap_topic(topic_slug="demo-topic")),
                _parse(aitp_mcp_server.aitp_get_runtime_state("demo-topic")),
                _parse(aitp_mcp_server.aitp_audit_conformance("demo-topic")),
                _parse(
                    aitp_mcp_server.aitp_scaffold_baseline(
                        "demo-topic",
                        "2026-03-13-demo",
                        "Public baseline",
                        "arXiv:0000.00000",
                        "qualitative agreement",
                    )
                ),
                _parse(
                    aitp_mcp_server.aitp_scaffold_atomic_understanding(
                        "demo-topic",
                        "2026-03-13-demo",
                        "Finite-size spectral diagnostic",
                    )
                ),
                _parse(
                    aitp_mcp_server.aitp_scaffold_operation(
                        "demo-topic",
                        "2026-03-13-demo",
                        "Small-system validation backend",
                        "numerical",
                    )
                ),
                _parse(
                    aitp_mcp_server.aitp_update_operation(
                        "demo-topic",
                        "2026-03-13-demo",
                        "Small-system validation backend",
                    )
                ),
                _parse(aitp_mcp_server.aitp_audit_operation_trust("demo-topic")),
                _parse(aitp_mcp_server.aitp_audit_capability("demo-topic")),
                _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic")),
                _parse(aitp_mcp_server.aitp_install_agent_wrapper("codex")),
            ]

        for result in results:
            self.assertEqual(result["status"], "error")
            self.assertIn("boom", result["error"])
            self.assertIn("Traceback", result["traceback"])
