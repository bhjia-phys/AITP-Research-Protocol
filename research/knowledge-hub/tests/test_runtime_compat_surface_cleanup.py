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

from knowledge_hub.aitp_service import AITPService


class RuntimeCompatSurfaceCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name) / "kernel"
        self.kernel_root.mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "scripts").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "scripts" / "orchestrate_topic.py").write_text(
            "# compat fixture\n",
            encoding="utf-8",
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _topic_root(self, topic_slug: str) -> Path:
        root = self.kernel_root / "topics" / topic_slug / "runtime"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def test_prune_compat_surfaces_removes_compatibility_files_when_primary_surfaces_exist(self) -> None:
        topic_slug = "demo-topic"
        topic_root = self._topic_root(topic_slug)
        (topic_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": topic_slug, "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (topic_root / "topic_dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        (topic_root / "runtime_protocol.generated.md").write_text("# Runtime protocol\n", encoding="utf-8")
        (topic_root / "agent_brief.md").write_text("# Brief\n", encoding="utf-8")
        (topic_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")
        runtime_root = self.kernel_root / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "current_topic.json").write_text(
            json.dumps({"topic_slug": topic_slug}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (runtime_root / "current_topic.md").write_text("# Current topic\n", encoding="utf-8")

        payload = self.service.prune_compat_surfaces(topic_slug=topic_slug, updated_by="test")

        self.assertEqual(payload["status"], "pruned")
        self.assertEqual(
            {row["surface"] for row in payload["removed_surfaces"]},
            {"agent_brief", "operator_console", "current_topic_note"},
        )
        self.assertFalse((topic_root / "agent_brief.md").exists())
        self.assertFalse((topic_root / "operator_console.md").exists())
        self.assertFalse((runtime_root / "current_topic.md").exists())
        self.assertTrue((topic_root / "topic_dashboard.md").exists())
        self.assertTrue((topic_root / "runtime_protocol.generated.md").exists())
        self.assertTrue((runtime_root / "current_topic.json").exists())

    def test_prune_compat_surfaces_blocks_when_primary_surfaces_are_missing(self) -> None:
        topic_slug = "demo-topic"
        topic_root = self._topic_root(topic_slug)
        (topic_root / "topic_state.json").write_text(
            json.dumps({"topic_slug": topic_slug, "resume_stage": "L3"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (topic_root / "agent_brief.md").write_text("# Brief\n", encoding="utf-8")
        (topic_root / "operator_console.md").write_text("# Console\n", encoding="utf-8")

        payload = self.service.prune_compat_surfaces(topic_slug=topic_slug, updated_by="test")

        self.assertEqual(payload["status"], "blocked_missing_primary_surfaces")
        self.assertEqual(
            {row["surface"] for row in payload["blocking_surfaces"]},
            {"topic_dashboard", "runtime_protocol"},
        )
        self.assertTrue((topic_root / "agent_brief.md").exists())
        self.assertTrue((topic_root / "operator_console.md").exists())


if __name__ == "__main__":
    unittest.main()
