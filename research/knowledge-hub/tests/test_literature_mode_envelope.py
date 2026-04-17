from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.mode_envelope_support import build_runtime_mode_contract, refocus_context_for_active_submode


class LiteratureModeEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]

    def test_build_runtime_mode_contract_detects_literature_submode(self) -> None:
        contract = build_runtime_mode_contract(
            resume_stage="L1",
            load_profile="light",
            idea_packet_status="approved_for_execution",
            operator_checkpoint_status="cancelled",
            selected_action_type="inspect_source_intake",
            selected_action_summary="Read and extract reusable knowledge from this paper.",
            must_read_now=[
                {"path": "topics/demo-topic/runtime/topic_dashboard.md", "reason": "dashboard"},
                {"path": "topics/demo-topic/runtime/research_question.contract.md", "reason": "contract"},
            ],
            may_defer_until_trigger=[],
            escalation_triggers=[],
            human_request="Read and extract reusable knowledge from this paper",
        )

        self.assertEqual(contract["runtime_mode"], "explore")
        self.assertEqual(contract["active_submode"], "literature")
        self.assertIn("stage them into L2", contract["mode_envelope"]["local_task"])
        self.assertIn(
            "l2_staging_entries_with_literature_intake_fast_path",
            contract["mode_envelope"]["required_writeback"],
        )

    def test_refocus_context_for_literature_submode_promotes_l1_and_defers_validation(self) -> None:
        runtime_mode_payload = {
            **build_runtime_mode_contract(
                resume_stage="L1",
                load_profile="full",
                idea_packet_status="approved_for_execution",
                operator_checkpoint_status="cancelled",
                selected_action_type="inspect_source_intake",
                selected_action_summary="Read and extract reusable knowledge from this paper.",
                must_read_now=[],
                may_defer_until_trigger=[],
                escalation_triggers=[],
                human_request="Read and extract reusable knowledge from this paper",
            )
        }
        refocused = refocus_context_for_active_submode(
            runtime_mode_payload=runtime_mode_payload,
            must_read_now=[
                {"path": "topics/demo-topic/runtime/topic_dashboard.md", "reason": "dashboard"},
                {"path": "topics/demo-topic/runtime/research_question.contract.md", "reason": "contract"},
                {"path": "topics/demo-topic/runtime/validation_contract.active.md", "reason": "validation"},
                {"path": "topics/demo-topic/runtime/validation_review_bundle.active.md", "reason": "review"},
                {"path": "topics/demo-topic/runtime/promotion_gate.md", "reason": "gate"},
            ],
            may_defer_until_trigger=[],
            l1_vault={
                "topic_slug": "demo-topic",
                "wiki": {
                    "page_paths": [
                        "intake/topics/demo-topic/vault/wiki/home.md",
                        "intake/topics/demo-topic/vault/wiki/source-intake.md",
                    ]
                },
            },
            canonical_index_path="canonical/index.jsonl",
            workspace_staging_manifest_path="canonical/staging/workspace_staging_manifest.json",
            validation_contract_path="topics/demo-topic/runtime/validation_contract.active.md",
            validation_review_bundle_path="topics/demo-topic/runtime/validation_review_bundle.active.md",
            promotion_readiness_path="topics/demo-topic/runtime/promotion_readiness.json",
            promotion_gate_path="topics/demo-topic/runtime/promotion_gate.md",
        )

        focused_paths = [row["path"] for row in refocused["must_read_now"]]
        deferred_paths = [row["path"] for row in refocused["may_defer_until_trigger"]]

        self.assertIn("intake/topics/demo-topic/vault/wiki/home.md", focused_paths)
        self.assertIn("intake/topics/demo-topic/vault/wiki/source-intake.md", focused_paths)
        self.assertIn("canonical/staging/workspace_staging_manifest.json", focused_paths)
        self.assertIn("canonical/index.jsonl", focused_paths)
        self.assertNotIn("topics/demo-topic/runtime/validation_contract.active.md", focused_paths)
        self.assertNotIn("topics/demo-topic/runtime/validation_review_bundle.active.md", focused_paths)
        self.assertNotIn("topics/demo-topic/runtime/promotion_gate.md", focused_paths)
        self.assertIn("topics/demo-topic/runtime/validation_contract.active.md", deferred_paths)
        self.assertIn("topics/demo-topic/runtime/validation_review_bundle.active.md", deferred_paths)
        self.assertIn("topics/demo-topic/runtime/promotion_gate.md", deferred_paths)

    def test_runtime_bundle_schema_allows_literature_submode(self) -> None:
        payload = json.loads(
            (self.kernel_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("literature", payload["properties"]["active_submode"]["enum"])
        self.assertIn("literature", payload["properties"]["mode_envelope"]["properties"]["active_submode"]["enum"])
        self.assertIn("literature", payload["properties"]["autonomy_posture"]["properties"]["active_submode"]["enum"])


if __name__ == "__main__":
    unittest.main()
