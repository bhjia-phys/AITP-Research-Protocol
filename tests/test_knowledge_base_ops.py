"""Tests for knowledge-base operations: index and log surface checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from tests.test_l3_subplanes import _bootstrap_l1_complete


def _bootstrap_with_l3(tmp: str) -> Path:
    """Bootstrap a topic through L1 complete and into L3 ideation."""
    repo_root = _bootstrap_l1_complete(tmp)
    mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
    return repo_root


class TopicRuntimeSurfaceTests(unittest.TestCase):
    def test_topic_runtime_index_is_materialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            tr = Path(tmp) / "topics" / "demo-topic"
            idx = tr / "runtime" / "index.md"
            self.assertTrue(idx.exists(), "runtime/index.md must exist after bootstrap")

    def test_topic_runtime_log_is_materialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            tr = Path(tmp) / "topics" / "demo-topic"
            log = tr / "runtime" / "log.md"
            self.assertTrue(log.exists(), "runtime/log.md must exist after bootstrap")

    def test_topic_index_links_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            tr = Path(tmp) / "topics" / "demo-topic"
            idx_text = (tr / "runtime" / "index.md").read_text(encoding="utf-8")
            for section in ["Source Basis", "Research Notebook", "Validation", "Reusable Results", "Writing"]:
                self.assertIn(section, idx_text, f"Missing section in index: {section}")


class GlobalL2SurfaceTests(unittest.TestCase):
    def test_global_l2_index_is_materialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            l2_idx = Path(tmp) / "L2" / "index.md"
            self.assertTrue(l2_idx.exists(), "L2/index.md must exist")

    def test_global_l2_log_is_materialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            l2_log = Path(tmp) / "L2" / "log.md"
            self.assertTrue(l2_log.exists(), "L2/log.md must exist")

    def test_global_l2_index_groups_by_family_and_regime(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            l2_idx = (Path(tmp) / "L2" / "index.md").read_text(encoding="utf-8")
            for section in ["Family", "Regime", "Warning", "Negative"]:
                self.assertIn(section, l2_idx, f"Missing grouping in L2 index: {section}")


if __name__ == "__main__":
    unittest.main()
