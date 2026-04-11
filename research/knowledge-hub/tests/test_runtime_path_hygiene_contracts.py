from __future__ import annotations

import json
from pathlib import Path
import unittest


class RuntimePathHygieneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def test_checked_in_current_topic_uses_repo_relative_runtime_root(self) -> None:
        current_topic_path = self.repo_root / "research" / "knowledge-hub" / "runtime" / "current_topic.json"
        current_topic_note_path = self.repo_root / "research" / "knowledge-hub" / "runtime" / "current_topic.md"

        payload = json.loads(current_topic_path.read_text(encoding="utf-8"))
        note_text = current_topic_note_path.read_text(encoding="utf-8")

        self.assertEqual(
            payload["runtime_root"],
            f"runtime/topics/{payload['topic_slug']}",
        )
        self.assertIn(f"Runtime root: `runtime/topics/{payload['topic_slug']}`", note_text)
        self.assertNotIn("D:\\", payload["runtime_root"])
        self.assertNotIn("D:\\", note_text)


if __name__ == "__main__":
    unittest.main()
