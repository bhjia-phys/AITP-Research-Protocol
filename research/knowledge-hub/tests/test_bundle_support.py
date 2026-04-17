from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.bundle_support import build_bundle_tree, ensure_materialized_kernel_root, iter_bundle_source_files


class BundleSupportTests(unittest.TestCase):
    def test_iter_bundle_source_files_excludes_dynamic_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "runtime" / "scripts").mkdir(parents=True, exist_ok=True)
            (root / "topics" / "demo-topic" / "runtime").mkdir(parents=True, exist_ok=True)
            (root / "validation" / "topics" / "demo-topic").mkdir(parents=True, exist_ok=True)
            (root / "knowledge_hub").mkdir(parents=True, exist_ok=True)
            (root / "runtime" / "scripts" / "orchestrate_topic.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
            (root / "runtime" / "current_topic.json").write_text("{}\n", encoding="utf-8")
            (root / "topics" / "demo-topic" / "runtime" / "topic_state.json").write_text("{}\n", encoding="utf-8")
            (root / "validation" / "topics" / "demo-topic" / "run.json").write_text("{}\n", encoding="utf-8")
            (root / "knowledge_hub" / "__init__.py").write_text("", encoding="utf-8")
            (root / "LAYER_MAP.md").write_text("# Layer map\n", encoding="utf-8")

            bundle_rows = {relative.as_posix() for _, relative in iter_bundle_source_files(root)}

        self.assertIn("LAYER_MAP.md", bundle_rows)
        self.assertIn("runtime/scripts/orchestrate_topic.py", bundle_rows)
        self.assertNotIn("runtime/current_topic.json", bundle_rows)
        self.assertNotIn("topics/demo-topic/runtime/topic_state.json", bundle_rows)
        self.assertNotIn("validation/topics/demo-topic/run.json", bundle_rows)
        self.assertNotIn("knowledge_hub/__init__.py", bundle_rows)

    def test_ensure_materialized_kernel_root_copies_bundle_and_creates_dynamic_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle_root = root / "bundle"
            target_root = root / "materialized"
            (bundle_root / "runtime" / "scripts").mkdir(parents=True, exist_ok=True)
            (bundle_root / "schemas").mkdir(parents=True, exist_ok=True)
            (bundle_root / "runtime" / "scripts" / "orchestrate_topic.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
            (bundle_root / "schemas" / "decision-point.schema.json").write_text("{\"type\": \"object\"}\n", encoding="utf-8")
            (bundle_root / "LAYER_MAP.md").write_text("# Layer map\n", encoding="utf-8")

            ensure_materialized_kernel_root(target_root, bundle_root=bundle_root)

            self.assertTrue((target_root / "runtime" / "scripts" / "orchestrate_topic.py").exists())
            self.assertTrue((target_root / "schemas" / "decision-point.schema.json").exists())
            self.assertTrue((target_root / "runtime" / "topics").exists())
            self.assertTrue((target_root / "feedback" / "topics").exists())
            self.assertTrue((target_root / ".aitp_bundle_install.json").exists())

    def test_build_bundle_tree_creates_minimal_runtime_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_root = root / "source"
            destination_root = root / "bundle"
            (source_root / "runtime" / "scripts").mkdir(parents=True, exist_ok=True)
            (source_root / "runtime" / "scripts" / "orchestrate_topic.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")
            (source_root / "schemas").mkdir(parents=True, exist_ok=True)
            (source_root / "schemas" / "session-chronicle.schema.json").write_text("{\"type\": \"object\"}\n", encoding="utf-8")
            (source_root / "README.md").write_text("# Kernel\n", encoding="utf-8")

            build_bundle_tree(source_root, destination_root)

            self.assertTrue((destination_root / "runtime" / "scripts" / "orchestrate_topic.py").exists())
            self.assertTrue((destination_root / "schemas" / "session-chronicle.schema.json").exists())
            self.assertTrue((destination_root / "consultation" / "topics").exists())


if __name__ == "__main__":
    unittest.main()
