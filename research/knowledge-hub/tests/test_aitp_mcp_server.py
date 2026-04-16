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

from knowledge_hub import aitp_mcp_server


def _parse(result: str) -> dict:
    payload = json.loads(result)
    if not isinstance(payload, dict):
        raise AssertionError("MCP result must be a JSON object")
    return payload


READ_ONLY_PROFILE_TOOLS = {
    "aitp_describe_mcp_profile",
    "aitp_get_runtime_state",
    "aitp_get_topic_interaction",
    "aitp_get_required_read_gate",
    "aitp_list_pending_decisions",
    "aitp_list_tool_manifest",
    "aitp_get_popup",
    "aitp_get_topic_popup",
}

WRITE_PROFILE_TOOLS = {
    "aitp_bootstrap_topic",
    "aitp_resume_topic",
    "aitp_scaffold_baseline",
    "aitp_scaffold_atomic_understanding",
    "aitp_scaffold_operation",
    "aitp_update_operation",
    "aitp_audit_operation_trust",
    "aitp_audit_capability",
    "aitp_audit_theory_coverage",
    "aitp_audit_formal_theory",
    "aitp_complete_topic",
    "aitp_update_followup_return",
    "aitp_reintegrate_followup",
    "aitp_resolve_pending_decision",
    "aitp_resolve_operator_checkpoint",
    "aitp_resolve_popup",
    "aitp_resolve_popup_choice",
    "aitp_prepare_lean_bridge",
    "aitp_request_promotion",
    "aitp_approve_promotion",
    "aitp_reject_promotion",
    "aitp_promote_candidate",
    "aitp_auto_promote_candidate",
    "aitp_ack_required_reads",
    "aitp_run_topic_loop",
    "aitp_install_agent_wrapper",
}


class _AITPStubSuccess:
    kernel_root = Path(".")

    def orchestrate(self, **kwargs):  # noqa: ANN003
        return {"topic_slug": kwargs.get("topic_slug") or "demo-topic"}

    def get_runtime_state(self, topic_slug: str):
        return {"topic_slug": topic_slug, "resume_stage": "L3"}

    def topic_interaction(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "requires_human_input_now": True,
            "primary_interaction": {
                "kind": "operator_checkpoint",
                "question": "Clarify the bounded route.",
                "options": [{"key": "clarify_now", "label": "Clarify now"}],
                "default_option_index": 0,
            },
        }

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "phase": phase,
            "updated_by": updated_by,
            "conformance_state": {"overall_status": "pass"},
        }

    def resolve_operator_checkpoint(self, *, topic_slug: str, option_index: int, comment: str | None = None, resolved_by: str = "human"):
        return {
            "operator_checkpoint": {
                "topic_slug": topic_slug,
                "status": "answered",
                "resolution": {
                    "chosen_option_index": option_index,
                    "human_comment": comment or "",
                    "resolved_by": resolved_by,
                },
            }
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

    def audit_theory_coverage(self, **kwargs):  # noqa: ANN003
        return {"coverage_status": "pass", "candidate_id": kwargs.get("candidate_id")}

    def audit_formal_theory(self, **kwargs):  # noqa: ANN003
        return {"overall_status": "ready", "candidate_id": kwargs.get("candidate_id")}

    def request_promotion(self, **kwargs):  # noqa: ANN003
        return {"status": "pending_human_approval", "candidate_id": kwargs.get("candidate_id")}

    def approve_promotion(self, **kwargs):  # noqa: ANN003
        return {"status": "approved", "candidate_id": kwargs.get("candidate_id")}

    def reject_promotion(self, **kwargs):  # noqa: ANN003
        return {"status": "rejected", "candidate_id": kwargs.get("candidate_id")}

    def promote_candidate(self, **kwargs):  # noqa: ANN003
        return {"target_unit_id": "concept:demo", "candidate_id": kwargs.get("candidate_id")}

    def auto_promote_candidate(self, **kwargs):  # noqa: ANN003
        return {"target_unit_id": "concept:demo", "candidate_id": kwargs.get("candidate_id")}

    def run_topic_loop(self, **kwargs):  # noqa: ANN003
        return {"topic_slug": kwargs.get("topic_slug") or "demo-topic", "loop_state": {"exit_conformance": "pass"}}

    def install_agent(self, **kwargs):  # noqa: ANN003
        return {"installed": [{"path": "/tmp/demo", "kind": "skill"}]}

    def topic_popup(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "needs_popup": True,
            "popup_kind": "promotion_gate",
            "popup": {
                "popup_kind": "promotion_gate",
                "title": "Promotion Review Gate",
                "message": "Candidate ready for L2.",
                "choices": [
                    {"index": 1, "key": "approve", "label": "Approve", "description": "Promote to L2."},
                    {"index": 2, "key": "reject", "label": "Reject", "description": "Keep in L3."},
                ],
            },
            "markdown": "╔═...",
        }

    def topic_required_read_gate(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "blocked": False,
            "needs_ack": False,
            "gate_kind": "must_read_ack",
            "missing_paths": [],
        }

    def acknowledge_required_reads(self, *, topic_slug: str, paths: list[str] | None = None, all_current: bool = False, updated_by: str = "aitp-mcp"):
        return {
            "topic_slug": topic_slug,
            "acknowledged_count": 2 if all_current else len(paths or []),
            "remaining_missing_count": 0,
        }

    def resolve_popup_choice(self, *, topic_slug: str, choice_index: int, comment: str | None = None, resolved_by: str = "human"):
        return {"status": "resolved", "topic_slug": topic_slug, "choice_index": choice_index}


class _AITPStubFailure:
    kernel_root = Path(".")

    def orchestrate(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("orchestrate boom")

    def get_runtime_state(self, topic_slug: str):
        raise RuntimeError("state boom")

    def topic_interaction(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        raise RuntimeError("interaction boom")

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp"):
        raise RuntimeError("audit boom")

    def resolve_operator_checkpoint(self, *, topic_slug: str, option_index: int, comment: str | None = None, resolved_by: str = "human"):
        raise RuntimeError("checkpoint boom")

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

    def audit_theory_coverage(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("coverage boom")

    def audit_formal_theory(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("formal theory boom")

    def request_promotion(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("promotion request boom")

    def approve_promotion(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("promotion approve boom")

    def reject_promotion(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("promotion reject boom")

    def promote_candidate(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("promotion run boom")

    def auto_promote_candidate(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("auto promotion boom")

    def run_topic_loop(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("loop boom")

    def install_agent(self, **kwargs):  # noqa: ANN003
        raise RuntimeError("install boom")

    def topic_popup(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        raise RuntimeError("popup boom")

    def topic_required_read_gate(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
        raise RuntimeError("required read boom")

    def acknowledge_required_reads(self, *, topic_slug: str, paths: list[str] | None = None, all_current: bool = False, updated_by: str = "aitp-mcp"):
        raise RuntimeError("ack read boom")

    def resolve_popup_choice(self, *, topic_slug: str, choice_index: int, comment: str | None = None, resolved_by: str = "human"):
        raise RuntimeError("resolve popup boom")


class AITPMCPServerTests(unittest.TestCase):
    def test_review_and_skeptic_profiles_register_only_read_only_tools(self) -> None:
        full_server = aitp_mcp_server.build_mcp_server("full")
        review_server = aitp_mcp_server.build_mcp_server("review")
        skeptic_server = aitp_mcp_server.build_mcp_server("skeptic")

        full_tools = set(full_server._tool_manager._tools)
        review_tools = set(review_server._tool_manager._tools)
        skeptic_tools = set(skeptic_server._tool_manager._tools)

        self.assertTrue(READ_ONLY_PROFILE_TOOLS.issubset(full_tools))
        self.assertTrue(WRITE_PROFILE_TOOLS.issubset(full_tools))
        self.assertEqual(review_tools, READ_ONLY_PROFILE_TOOLS)
        self.assertEqual(skeptic_tools, READ_ONLY_PROFILE_TOOLS)
        self.assertFalse(review_tools & WRITE_PROFILE_TOOLS)
        self.assertFalse(skeptic_tools & WRITE_PROFILE_TOOLS)

    def test_aitp_tools_return_success_payloads(self) -> None:
        with patch.object(aitp_mcp_server, "service", _AITPStubSuccess()):
            with patch.object(aitp_mcp_server, "list_pending_decision_points", return_value=[{"id": "dp:demo"}]):
                with patch.object(
                    aitp_mcp_server,
                    "resolve_decision_point",
                    return_value={"decision_point": {"id": "dp:demo", "resolution": {"chosen_option_index": 0}}},
                ):
                    bootstrap = _parse(aitp_mcp_server.aitp_bootstrap_topic(topic_slug="demo-topic"))
                    state = _parse(aitp_mcp_server.aitp_get_runtime_state("demo-topic"))
                    interaction = _parse(aitp_mcp_server.aitp_get_topic_interaction("demo-topic"))
                    decisions = _parse(aitp_mcp_server.aitp_list_pending_decisions("demo-topic"))
                    resolved = _parse(aitp_mcp_server.aitp_resolve_pending_decision("demo-topic", "dp:demo", 0))
                    resolved_checkpoint = _parse(
                        aitp_mcp_server.aitp_resolve_operator_checkpoint(
                            "demo-topic",
                            0,
                            comment="Focus on the theorem-facing route first.",
                        )
                    )
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
                    coverage = _parse(
                        aitp_mcp_server.aitp_audit_theory_coverage(
                            "demo-topic",
                            "candidate:demo",
                            source_sections=["sec:intro"],
                            covered_sections=["sec:intro"],
                        )
                    )
                    formal_theory = _parse(
                        aitp_mcp_server.aitp_audit_formal_theory(
                            "demo-topic",
                            "candidate:demo",
                            formal_theory_role="trusted_target",
                            statement_graph_role="target_statement",
                            faithfulness_status="reviewed",
                            faithfulness_strategy="bounded source-to-target map",
                            comparator_audit_status="passed",
                            attribution_requirements=["Preserve source citation."],
                            prerequisite_closure_status="closed",
                        )
                    )
                    request_promotion = _parse(
                        aitp_mcp_server.aitp_request_promotion(
                            "demo-topic",
                            "candidate:demo",
                            backend_id="backend:theoretical-physics-knowledge-network",
                        )
                    )
                    approve_promotion = _parse(
                        aitp_mcp_server.aitp_approve_promotion(
                            "demo-topic",
                            "candidate:demo",
                        )
                    )
                    reject_promotion = _parse(
                        aitp_mcp_server.aitp_reject_promotion(
                            "demo-topic",
                            "candidate:demo",
                        )
                    )
                    promote_candidate = _parse(
                        aitp_mcp_server.aitp_promote_candidate(
                            "demo-topic",
                            "candidate:demo",
                            target_backend_root="/tmp/tpkn",
                        )
                    )
                    auto_promote_candidate = _parse(
                        aitp_mcp_server.aitp_auto_promote_candidate(
                            "demo-topic",
                            "candidate:demo",
                            target_backend_root="/tmp/tpkn",
                        )
                    )
                    popup = _parse(aitp_mcp_server.aitp_get_popup("demo-topic"))
                    required_read = _parse(aitp_mcp_server.aitp_get_required_read_gate("demo-topic"))
                    ack_read = _parse(aitp_mcp_server.aitp_ack_required_reads("demo-topic", all_current=True))
                    resolved_popup = _parse(aitp_mcp_server.aitp_resolve_popup("demo-topic", 1))
                    popup = _parse(aitp_mcp_server.aitp_get_popup("demo-topic"))
                    resolved_popup = _parse(aitp_mcp_server.aitp_resolve_popup("demo-topic", 1))
                    loop = _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic"))
                    install = _parse(aitp_mcp_server.aitp_install_agent_wrapper("codex"))

        self.assertEqual(bootstrap["status"], "success")
        self.assertEqual(bootstrap["topic_slug"], "demo-topic")
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["topic_state"]["resume_stage"], "L3")
        self.assertEqual(interaction["status"], "success")
        self.assertEqual(interaction["primary_interaction"]["kind"], "operator_checkpoint")
        self.assertEqual(decisions["status"], "success")
        self.assertEqual(decisions["decision_points"][0]["id"], "dp:demo")
        self.assertEqual(resolved["status"], "success")
        self.assertEqual(resolved["decision_point"]["id"], "dp:demo")
        self.assertEqual(resolved_checkpoint["status"], "success")
        self.assertEqual(
            resolved_checkpoint["operator_checkpoint"]["resolution"][
                "chosen_option_index"
            ],
            0,
        )
        self.assertEqual(audit["status"], "success")
        self.assertEqual(audit["conformance_state"]["overall_status"], "pass")
        self.assertEqual(baseline["status"], "success")
        self.assertEqual(atomize["status"], "success")
        self.assertEqual(operation["status"], "success")
        self.assertEqual(update["status"], "success")
        self.assertEqual(trust["status"], "success")
        self.assertEqual(capability["status"], "success")
        self.assertEqual(coverage["status"], "success")
        self.assertEqual(formal_theory["status"], "success")
        self.assertEqual(request_promotion["status"], "success")
        self.assertEqual(approve_promotion["status"], "success")
        self.assertEqual(reject_promotion["status"], "success")
        self.assertEqual(promote_candidate["status"], "success")
        self.assertEqual(auto_promote_candidate["status"], "success")
        self.assertEqual(popup["status"], "success")
        self.assertTrue(popup["needs_popup"])
        self.assertEqual(popup["popup_kind"], "promotion_gate")
        self.assertEqual(required_read["status"], "success")
        self.assertFalse(required_read["needs_ack"])
        self.assertEqual(ack_read["status"], "success")
        self.assertEqual(ack_read["acknowledged_count"], 2)
        self.assertEqual(resolved_popup["status"], "resolved")
        self.assertEqual(loop["status"], "success")
        self.assertEqual(install["status"], "success")

    def test_aitp_tools_return_error_shape_when_exceptions_occur(self) -> None:
        with patch.object(aitp_mcp_server, "service", _AITPStubFailure()):
            with patch.object(aitp_mcp_server, "list_pending_decision_points", side_effect=RuntimeError("decisions boom")):
                with patch.object(aitp_mcp_server, "resolve_decision_point", side_effect=RuntimeError("resolve boom")):
                    results = [
                        _parse(aitp_mcp_server.aitp_bootstrap_topic(topic_slug="demo-topic")),
                        _parse(aitp_mcp_server.aitp_get_runtime_state("demo-topic")),
                        _parse(aitp_mcp_server.aitp_get_topic_interaction("demo-topic")),
                        _parse(aitp_mcp_server.aitp_list_pending_decisions("demo-topic")),
                        _parse(aitp_mcp_server.aitp_resolve_pending_decision("demo-topic", "dp:demo", 0)),
                        _parse(aitp_mcp_server.aitp_resolve_operator_checkpoint("demo-topic", 0)),
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
                        _parse(aitp_mcp_server.aitp_audit_theory_coverage("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_audit_formal_theory("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_request_promotion("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_approve_promotion("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_reject_promotion("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_promote_candidate("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_auto_promote_candidate("demo-topic", "candidate:demo")),
                        _parse(aitp_mcp_server.aitp_get_popup("demo-topic")),
                        _parse(aitp_mcp_server.aitp_get_required_read_gate("demo-topic")),
                        _parse(aitp_mcp_server.aitp_ack_required_reads("demo-topic", all_current=True)),
                        _parse(aitp_mcp_server.aitp_resolve_popup("demo-topic", 1)),
                        _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic")),
                        _parse(aitp_mcp_server.aitp_install_agent_wrapper("codex")),
                    ]

        for result in results:
            self.assertEqual(result["status"], "error")
            self.assertIn("boom", result["error"])
            self.assertIn("Traceback", result["traceback"])

    def test_bootstrap_and_loop_tools_return_compact_operator_facing_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_protocol_path = Path(tmp) / "runtime_protocol.generated.json"
            runtime_protocol_path.write_text(
                json.dumps(
                    {
                        "human_interaction_posture": {
                            "requires_human_input_now": False,
                            "summary": "No active human checkpoint is blocking work.",
                        },
                        "autonomy_posture": {
                            "mode": "continuous_bounded_loop",
                            "can_continue_without_human": True,
                            "summary": "Continue bounded work.",
                        },
                    }
                ),
                encoding="utf-8",
            )

            class _CompactStub:
                def orchestrate(self, **kwargs):  # noqa: ANN003
                    return {
                        "topic_slug": kwargs.get("topic_slug") or "demo-topic",
                        "runtime_root": "/tmp/runtime/demo-topic",
                        "command": ["python", "orchestrate"],
                        "conformance_state": {"overall_status": "pass"},
                        "files": {
                            "topic_state": "/tmp/runtime/demo-topic/topic_state.json",
                            "runtime_protocol": "/tmp/runtime/demo-topic/runtime_protocol.generated.json",
                        },
                        "topic_state": {
                            "resume_stage": "L3",
                            "last_materialized_stage": "L3",
                            "research_mode": "exploratory_general",
                            "load_profile": "light",
                            "summary": "Resume at L3.",
                            "status_explainability": {
                                "current_status_summary": "Resume at L3.",
                            },
                        },
                        "stdout": "very large bootstrap payload omitted",
                    }

                def run_topic_loop(self, **kwargs):  # noqa: ANN003
                    return {
                        "topic_slug": kwargs.get("topic_slug") or "demo-topic",
                        "run_id": "2026-04-13-demo",
                        "load_profile": "light",
                        "loop_state_path": "/tmp/runtime/demo-topic/loop_state.json",
                        "loop_history_path": "/tmp/runtime/demo-topic/loop_history.jsonl",
                        "loop_state": {
                            "entry_conformance": "pass",
                            "exit_conformance": "pass",
                            "capability_status": "missing_trust",
                            "trust_status": "missing",
                            "auto_actions_executed": 0,
                        },
                        "runtime_protocol": {
                            "runtime_protocol_path": str(runtime_protocol_path),
                            "runtime_protocol_note_path": "/tmp/runtime/demo-topic/runtime_protocol.generated.md",
                        },
                        "current_topic_memory": {
                            "topic_slug": "demo-topic",
                            "summary": "Stage L3; next source expansion.",
                            "current_topic_path": "/tmp/runtime/current_topic.json",
                        },
                        "bootstrap": {
                            "topic_state": {
                                "status_explainability": {
                                    "next_bounded_action": {
                                        "action_id": "action:demo-topic:01",
                                        "action_type": "l0_source_expansion",
                                        "summary": "Start with source-layer/scripts/discover_and_register.py when you have a topic query; if you already know the arXiv id, use source-layer/scripts/register_arxiv_source.py and intake/ARXIV_FIRST_SOURCE_INTAKE.md.",
                                        "auto_runnable": False,
                                    }
                                }
                            }
                        },
                        "entry_audit": {
                            "conformance_state": {"overall_status": "pass"},
                            "conformance_report_path": "/tmp/runtime/demo-topic/entry.md",
                        },
                        "exit_audit": {
                            "conformance_state": {"overall_status": "pass"},
                            "conformance_report_path": "/tmp/runtime/demo-topic/exit.md",
                        },
                        "capability_audit": {
                            "overall_status": "missing_trust",
                            "capability_report_path": "/tmp/runtime/demo-topic/capability.md",
                        },
                        "trust_audit": {
                            "overall_status": "missing",
                            "trust_audit_path": "/tmp/runtime/demo-topic/trust.json",
                            "trust_report_path": "/tmp/runtime/demo-topic/trust.md",
                        },
                        "steering_artifacts": {},
                        "auto_actions": [],
                    }

            with patch.object(aitp_mcp_server, "service", _CompactStub()):
                bootstrap = _parse(aitp_mcp_server.aitp_bootstrap_topic(topic_slug="demo-topic"))
                loop = _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic"))

        self.assertEqual(bootstrap["status"], "success")
        self.assertIn("topic_state_summary", bootstrap)
        self.assertNotIn("topic_state", bootstrap)
        self.assertEqual(bootstrap["topic_state_summary"]["resume_stage"], "L3")
        self.assertEqual(bootstrap["conformance"]["overall_status"], "pass")

        self.assertEqual(loop["status"], "success")
        self.assertIn("selected_action", loop)
        self.assertEqual(loop["selected_action"]["action_type"], "l0_source_expansion")
        self.assertIn("discover_and_register.py", loop["selected_action"]["summary"])
        self.assertIn("register_arxiv_source.py", loop["selected_action"]["summary"])
        self.assertIn("ARXIV_FIRST_SOURCE_INTAKE.md", loop["selected_action"]["summary"])
        self.assertIn("human_interaction_posture", loop)
        self.assertIn("autonomy_posture", loop)
        self.assertEqual(loop["autonomy_posture"]["mode"], "continuous_bounded_loop")
        self.assertIn("audits", loop)
        self.assertNotIn("bootstrap", loop)
        self.assertNotIn("entry_audit", loop)
        self.assertNotIn("exit_audit", loop)

    def test_run_topic_loop_returns_required_read_gate_before_loop_when_reads_are_missing(self) -> None:
        class _GateStub:
            def topic_required_read_gate(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
                return {
                    "topic_slug": topic_slug,
                    "blocked": False,
                    "needs_ack": True,
                    "gate_kind": "must_read_ack",
                    "missing_paths": ["topics/demo-topic/runtime/session_start.generated.md"],
                }

            def run_topic_loop(self, **kwargs):  # noqa: ANN003
                raise AssertionError("run_topic_loop should not execute while required reads are missing")

        with patch.object(aitp_mcp_server, "service", _GateStub()):
            payload = _parse(aitp_mcp_server.aitp_run_topic_loop(topic_slug="demo-topic"))

        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["needs_ack"])
        self.assertEqual(payload["gate_kind"], "must_read_ack")

    def test_resume_topic_returns_required_read_gate_before_orchestrate_when_reads_are_missing(self) -> None:
        class _GateStub:
            def topic_required_read_gate(self, *, topic_slug: str, updated_by: str = "aitp-mcp"):
                return {
                    "topic_slug": topic_slug,
                    "blocked": False,
                    "needs_ack": True,
                    "gate_kind": "must_read_ack",
                    "missing_paths": ["topics/demo-topic/runtime/session_start.generated.md"],
                }

            def orchestrate(self, **kwargs):  # noqa: ANN003
                raise AssertionError("orchestrate should not execute while required reads are missing")

        with patch.object(aitp_mcp_server, "service", _GateStub()):
            payload = _parse(aitp_mcp_server.aitp_resume_topic(topic_slug="demo-topic"))

        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["needs_ack"])
        self.assertEqual(payload["gate_kind"], "must_read_ack")
