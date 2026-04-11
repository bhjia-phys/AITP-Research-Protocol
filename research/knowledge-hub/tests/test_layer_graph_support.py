from __future__ import annotations

import sys
import unittest
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.layer_graph_support import build_layer_graph_payload, render_layer_graph_markdown


class LayerGraphSupportTests(unittest.TestCase):
    def test_build_layer_graph_defaults_to_analysis_subplane_for_l3_candidate_work(self) -> None:
        payload = build_layer_graph_payload(
            topic_slug="demo-topic",
            topic_state={
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
            },
            runtime_focus={
                "resume_stage": "L3",
                "last_materialized_stage": "L3",
                "next_action_summary": "Run the smallest exact benchmark first.",
                "last_evidence_kind": "none",
            },
            runtime_mode_payload={
                "runtime_mode": "explore",
                "active_submode": None,
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "transition_reason": "Current work remains inside the explore envelope.",
                    "allowed_targets": ["L1", "L3"],
                },
            },
            promotion_readiness={"status": "not_ready"},
            validation_review_bundle={"status": "not_materialized"},
        )

        self.assertEqual(payload["current_node_id"], "L3-A")
        self.assertEqual(payload["current_node"]["macro_layer"], "L3")
        self.assertIn("L4", payload["available_macro_targets"])

    def test_build_layer_graph_uses_result_integration_after_l4_return(self) -> None:
        payload = build_layer_graph_payload(
            topic_slug="demo-topic",
            topic_state={
                "resume_stage": "L3",
                "last_materialized_stage": "L4",
            },
            runtime_focus={
                "resume_stage": "L3",
                "last_materialized_stage": "L4",
                "next_action_summary": "Inspect the returned result and continue the bounded proof review.",
                "last_evidence_kind": "result_manifest",
            },
            runtime_mode_payload={
                "runtime_mode": "verify",
                "active_submode": "iterative_verify",
                "transition_posture": {
                    "transition_kind": "boundary_hold",
                    "transition_reason": "Validation returned a bounded result that must be integrated before distillation.",
                    "allowed_targets": ["L3", "L4"],
                },
            },
            promotion_readiness={"status": "not_ready"},
            validation_review_bundle={"status": "revise"},
        )

        self.assertEqual(payload["current_node_id"], "L3-R")
        self.assertEqual(payload["return_law"]["required_return_node"], "L3-R")
        self.assertFalse(payload["return_law"]["direct_l4_to_l2_promotion_allowed"])
        markdown = render_layer_graph_markdown(payload)
        self.assertIn("L4 -> L3-R", markdown)

    def test_build_layer_graph_uses_distillation_subplane_when_promotion_boundary_is_active(self) -> None:
        payload = build_layer_graph_payload(
            topic_slug="demo-topic",
            topic_state={
                "resume_stage": "L3",
                "last_materialized_stage": "L4",
            },
            runtime_focus={
                "resume_stage": "L3",
                "last_materialized_stage": "L4",
                "next_action_summary": "Prepare the candidate for bounded Layer 2 writeback.",
                "last_evidence_kind": "validation_review_bundle",
            },
            runtime_mode_payload={
                "runtime_mode": "promote",
                "active_submode": None,
                "transition_posture": {
                    "transition_kind": "forward_transition",
                    "transition_reason": "The current bounded task is explicitly reviewing or executing the L4 -> L2 boundary.",
                    "allowed_targets": ["L2", "L4", "L0"],
                },
            },
            promotion_readiness={"status": "ready"},
            validation_review_bundle={"status": "ready_for_promotion"},
        )

        self.assertEqual(payload["current_node_id"], "L3-D")
        self.assertIn("L2", payload["available_macro_targets"])
        self.assertTrue(any(edge["to_node"] == "L2" and edge["status"] == "available" for edge in payload["edges"]))


if __name__ == "__main__":
    unittest.main()
