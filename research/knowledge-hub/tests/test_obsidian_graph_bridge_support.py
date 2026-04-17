from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.obsidian_graph_bridge_support import sync_concept_graph_export_to_theoretical_physics_brain


class ObsidianGraphBridgeSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.brain_root = self.root / "obsidian-markdown" / "01 Theoretical Physics"
        self.source_kernel = Path(__file__).resolve().parents[1]
        shutil.copytree(self.source_kernel / "canonical", self.kernel_root / "canonical", dirs_exist_ok=True)
        export_root = self.kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph"
        export_root.mkdir(parents=True, exist_ok=True)
        (export_root / "manifest.json").write_text(
            json.dumps(
                {
                    "kind": "obsidian_concept_graph_export",
                    "topic_slug": "demo-topic",
                    "root_path": "topics/demo-topic/L1/vault/wiki/concept-graph",
                    "index_path": "topics/demo-topic/L1/vault/wiki/concept-graph/index.md",
                    "summary": {
                        "node_note_count": 1,
                        "community_folder_count": 1,
                    },
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (export_root / "index.md").write_text("# Concept Graph\n", encoding="utf-8")
        note_dir = export_root / "topological-order-cluster"
        note_dir.mkdir(parents=True, exist_ok=True)
        (note_dir / "index.md").write_text("# Cluster\n", encoding="utf-8")
        (note_dir / "topological-order.md").write_text("# Topological order\n", encoding="utf-8")
        backends_root = self.kernel_root / "canonical" / "backends"
        backends_root.mkdir(parents=True, exist_ok=True)
        (backends_root / "theoretical-physics-brain.json").write_text(
            json.dumps(
                {
                    "backend_id": "backend:theoretical-physics-brain",
                    "title": "Theoretical Physics Brain",
                    "backend_type": "human_note_library",
                    "status": "active",
                    "root_paths": [str(self.brain_root)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (backends_root / "backend_index.jsonl").write_text(
            json.dumps(
                {
                    "backend_id": "backend:theoretical-physics-brain",
                    "title": "Theoretical Physics Brain",
                    "backend_type": "human_note_library",
                    "status": "active",
                    "card_path": "canonical/backends/theoretical-physics-brain.json",
                },
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_sync_concept_graph_export_to_theoretical_physics_brain_mirrors_export_and_writes_receipt(self) -> None:
        payload = sync_concept_graph_export_to_theoretical_physics_brain(
            kernel_root=self.kernel_root,
            repo_root=self.repo_root,
            topic_slug="demo-topic",
            updated_by="test-suite",
        )

        target_root = self.brain_root / "90 AITP Imports" / "concept-graphs" / "demo-topic"
        self.assertTrue((target_root / "index.md").exists())
        self.assertTrue((target_root / "topological-order-cluster" / "topological-order.md").exists())
        self.assertTrue(Path(payload["receipt_path"]).exists())
        self.assertEqual(payload["summary"]["mirrored_file_count"], 4)
        self.assertEqual(payload["target_root"], str(target_root))


if __name__ == "__main__":
    unittest.main()
