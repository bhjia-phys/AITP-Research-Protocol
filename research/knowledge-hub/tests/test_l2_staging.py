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

from knowledge_hub.l2_staging import materialize_workspace_staging_manifest, stage_provisional_l2_entry


class L2StagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_materialize_workspace_staging_manifest_handles_empty_store(self) -> None:
        result = materialize_workspace_staging_manifest(self.kernel_root)
        payload = result["payload"]
        self.assertEqual(payload["summary"]["total_entries"], 0)
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        markdown = Path(result["markdown_path"]).read_text(encoding="utf-8")
        self.assertIn("Total entries: `0`", markdown)

    def test_stage_provisional_l2_entry_writes_entry_and_manifest(self) -> None:
        result = stage_provisional_l2_entry(
            self.kernel_root,
            topic_slug="demo-topic",
            entry_kind="workflow_draft",
            title="Demo draft",
            summary="A provisional reusable workflow draft.",
            source_artifact_paths=["topics/demo-topic/runtime/topic_dashboard.md"],
            staged_by="test",
        )

        entry = result["entry"]
        self.assertEqual(entry["status"], "staged")
        self.assertFalse(entry["authoritative"])
        self.assertEqual(entry["topic_slug"], "demo-topic")
        self.assertEqual(entry["entry_kind"], "workflow_draft")
        self.assertTrue(Path(result["entry_json_path"]).exists())
        self.assertTrue(Path(result["entry_markdown_path"]).exists())
        self.assertTrue(Path(result["manifest_json_path"]).exists())
        self.assertTrue(Path(result["manifest_markdown_path"]).exists())

        entry_path = Path(result["entry_json_path"])
        self.assertIn(str(self.kernel_root / "canonical" / "staging" / "entries"), str(entry_path))
        manifest_payload = json.loads(Path(result["manifest_json_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest_payload["summary"]["total_entries"], 1)
        self.assertEqual(manifest_payload["entries"][0]["entry_kind"], "workflow_draft")
