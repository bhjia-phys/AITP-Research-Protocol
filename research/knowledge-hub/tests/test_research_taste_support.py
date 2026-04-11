from __future__ import annotations

import sys
import unittest
from pathlib import Path


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.research_taste_support import build_research_taste_payload


class ResearchTasteSupportTests(unittest.TestCase):
    def test_build_research_taste_payload_aggregates_structured_entries(self) -> None:
        payload = build_research_taste_payload(
            topic_slug="demo-topic",
            taste_rows=[
                {
                    "taste_entry_id": "taste:1",
                    "taste_kind": "formalism",
                    "summary": "Prefer operator-algebra notation before widening the route.",
                    "formalisms": ["operator_algebra", "functional_analysis"],
                },
                {
                    "taste_entry_id": "taste:2",
                    "taste_kind": "elegance",
                    "summary": "Prefer the shortest source-backed argument that preserves regime honesty.",
                    "formalisms": [],
                },
                {
                    "taste_entry_id": "taste:3",
                    "taste_kind": "intuition",
                    "summary": "Keep the bounded weak-coupling picture as intuition, not as a proof surrogate.",
                    "formalisms": [],
                },
            ],
            collaborator_preference_rows=[],
            research_judgment={
                "surprise": {
                    "status": "active",
                    "latest_summary": "The weak-coupling route unexpectedly preserved the target symmetry.",
                }
            },
            updated_by="test",
        )

        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["formalism_preferences"], ["operator_algebra", "functional_analysis"])
        self.assertEqual(payload["elegance_signal_count"], 1)
        self.assertEqual(payload["intuition_signal_count"], 1)
        self.assertEqual(payload["surprise_handling"]["status"], "active")

    def test_build_research_taste_payload_reuses_collaborator_preferences_when_no_structured_rows_exist(self) -> None:
        payload = build_research_taste_payload(
            topic_slug="demo-topic",
            taste_rows=[],
            collaborator_preference_rows=[
                {
                    "memory_id": "collab-pref-1",
                    "summary": "Prefer theorem-facing operator-algebra routes before broader numerical detours.",
                    "tags": ["operator-algebra", "theorem-facing"],
                }
            ],
            research_judgment={
                "surprise": {
                    "status": "none",
                    "latest_summary": "No durable surprise signal is currently recorded.",
                }
            },
            updated_by="test",
        )

        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["route_taste_count"], 1)
        self.assertIn("operator-algebra", payload["preferred_tags"])
        self.assertIn("theorem-facing", payload["summary"])


if __name__ == "__main__":
    unittest.main()
