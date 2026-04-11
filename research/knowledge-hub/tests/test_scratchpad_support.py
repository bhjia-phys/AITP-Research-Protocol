from __future__ import annotations

import sys
import unittest
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.scratchpad_support import build_scratchpad_payload


class ScratchpadSupportTests(unittest.TestCase):
    def test_build_scratchpad_payload_counts_scratch_and_negative_results(self) -> None:
        payload = build_scratchpad_payload(
            topic_slug="demo-topic",
            rows=[
                {
                    "entry_id": "scratch:1",
                    "entry_kind": "route_comparison",
                    "summary": "Compare the theorem-facing and benchmark-first routes.",
                },
                {
                    "entry_id": "scratch:2",
                    "entry_kind": "negative_result",
                    "summary": "The portability extrapolation failed outside the bounded regime.",
                    "failure_kind": "regime_mismatch",
                },
                {
                    "entry_id": "scratch:3",
                    "entry_kind": "open_question",
                    "summary": "Decide whether the contradiction is notation-only or physical.",
                },
            ],
            updated_by="test",
        )

        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["entry_count"], 3)
        self.assertEqual(payload["negative_result_count"], 1)
        self.assertEqual(payload["route_comparison_count"], 1)
        self.assertEqual(payload["open_question_count"], 1)
        self.assertIn("portability extrapolation failed", payload["latest_negative_result_summary"])

    def test_build_scratchpad_payload_is_absent_when_no_rows_exist(self) -> None:
        payload = build_scratchpad_payload(
            topic_slug="demo-topic",
            rows=[],
            updated_by="test",
        )

        self.assertEqual(payload["status"], "absent")
        self.assertEqual(payload["entry_count"], 0)
        self.assertEqual(payload["negative_result_count"], 0)


if __name__ == "__main__":
    unittest.main()
