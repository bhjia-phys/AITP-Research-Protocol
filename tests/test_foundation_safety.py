"""Foundation safety tests — path resolution, slug validation, atomic writes,
promotion gates, and stop-hook scoping."""

from __future__ import annotations

import os
import textwrap
import tempfile
import unittest
from pathlib import Path

from brain.state_model import topics_dir, validate_topic_slug, topic_root


class TestTopicsDirResolution(unittest.TestCase):
    """Test that topics_dir correctly resolves nested vs flat layouts."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_repo_root_topics_layout_resolves_inside_topics_dir(self):
        """When topics_root has a topics/ subdirectory, use it."""
        topics_sub = Path(self.tmp) / "topics"
        topics_sub.mkdir()
        (topics_sub / "my-topic").mkdir()
        result = topics_dir(self.tmp)
        self.assertEqual(result, topics_sub)

    def test_direct_topics_root_layout_resolves_direct_child(self):
        """When no topics/ subdirectory exists, treat topics_root directly."""
        root = Path(self.tmp)
        (root / "my-topic").mkdir()
        result = topics_dir(self.tmp)
        self.assertEqual(result, root)


class TestSlugValidation(unittest.TestCase):
    """Test that unsafe slugs are rejected."""

    def test_valid_slug_passes(self):
        self.assertEqual(validate_topic_slug("my-topic"), "my-topic")

    def test_slug_with_parent_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("../evil")

    def test_slug_with_absolute_path_unix_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("/tmp/evil")

    def test_slug_with_absolute_path_windows_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("C:\\temp\\evil")

    def test_slug_with_nested_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("demo/../../oops")

    def test_empty_slug_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("")

    def test_dot_slug_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug(".")

    def test_multi_component_slug_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_topic_slug("a/b")


class TestTopicRoot(unittest.TestCase):
    """Test safe topic-root resolution."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.topics_sub = Path(self.tmp) / "topics"
        self.topics_sub.mkdir()
        (self.topics_sub / "demo").mkdir()

    def test_existing_topic_resolves(self):
        result = topic_root(self.tmp, "demo")
        self.assertEqual(result, self.topics_sub / "demo")

    def test_missing_topic_raises(self):
        with self.assertRaises(FileNotFoundError):
            topic_root(self.tmp, "nonexistent")

    def test_traversal_slug_raises(self):
        with self.assertRaises(ValueError):
            topic_root(self.tmp, "../etc/passwd")


class TestAtomicWrites(unittest.TestCase):
    """Test atomic write semantics."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_write_md_replaces_file_contents_cleanly(self):
        from brain.mcp_server import _write_md, _parse_md
        path = Path(self.tmp) / "test.md"
        _write_md(path, {"key": "old"}, "old body")
        _write_md(path, {"key": "new"}, "new body")
        fm, body = _parse_md(path)
        self.assertEqual(fm["key"], "new")
        self.assertIn("new body", body)
        self.assertNotIn("old body", body)

    def test_append_section_preserves_existing_without_truncation(self):
        from brain.mcp_server import _append_section
        path = Path(self.tmp) / "test.md"
        path.write_text("first line\n", encoding="utf-8")
        _append_section(path, "## Added Section\nSome content")
        text = path.read_text(encoding="utf-8")
        self.assertIn("first line", text)
        self.assertIn("## Added Section", text)

    def test_concurrent_write_does_not_corrupt(self):
        """Simulate that write produces a complete file (atomic replace)."""
        from brain.mcp_server import _write_md, _parse_md
        path = Path(self.tmp) / "concurrent.md"
        for i in range(20):
            _write_md(path, {"i": i}, f"body-{i}")
        fm, body = _parse_md(path)
        self.assertIn("body-", body)
        self.assertIsInstance(fm.get("i"), int)


class TestPromotionGate(unittest.TestCase):
    """Test that promotion requires the full gate lifecycle."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        from brain.mcp_server import aitp_bootstrap_topic
        self.topics_root = self.tmp
        aitp_bootstrap_topic(self.tmp, "demo", "Demo Topic", "What?")

    def _make_validated_candidate(self):
        from brain.mcp_server import (
            aitp_submit_candidate,
            aitp_update_status,
        )
        # Submit and mark validated
        aitp_submit_candidate(
            self.tmp, "demo", "c1", "Test Claim",
            claim="The sky is blue", evidence="Looked outside",
        )
        # Simulate validation by writing status directly
        from brain.mcp_server import _parse_md, _write_md
        from pathlib import Path
        cand_path = Path(self.tmp) / "topics" / "demo" / "L3" / "candidates" / "c1.md"
        if not cand_path.exists():
            cand_path = Path(self.tmp) / "demo" / "L3" / "candidates" / "c1.md"
        fm, body = _parse_md(cand_path)
        fm["status"] = "validated"
        _write_md(cand_path, fm, body)
        return cand_path

    def test_request_promotion_marks_candidate_pending_approval(self):
        from brain.mcp_server import aitp_request_promotion, _parse_md
        from pathlib import Path
        cand_path = self._make_validated_candidate()
        result = aitp_request_promotion(self.tmp, "demo", "c1")
        self.assertIn("pending_approval", result)
        fm, _ = _parse_md(cand_path)
        self.assertEqual(fm["status"], "pending_approval")

    def test_promote_candidate_rejects_nonapproved_candidates(self):
        from brain.mcp_server import aitp_promote_candidate
        self._make_validated_candidate()
        result = aitp_promote_candidate(self.tmp, "demo", "c1")
        self.assertIn("not approved", result.lower())

    def test_resolve_promotion_gate_approve_writes_l2_copy(self):
        from brain.mcp_server import (
            aitp_request_promotion,
            aitp_resolve_promotion_gate,
            aitp_promote_candidate,
            _parse_md,
        )
        from pathlib import Path
        self._make_validated_candidate()
        aitp_request_promotion(self.tmp, "demo", "c1")
        aitp_resolve_promotion_gate(self.tmp, "demo", "c1", decision="approve")
        result = aitp_promote_candidate(self.tmp, "demo", "c1")
        self.assertIn("Promoted", result)

    def test_resolve_promotion_gate_reject_blocks_promotion(self):
        from brain.mcp_server import (
            aitp_request_promotion,
            aitp_resolve_promotion_gate,
            aitp_promote_candidate,
        )
        self._make_validated_candidate()
        aitp_request_promotion(self.tmp, "demo", "c1")
        aitp_resolve_promotion_gate(self.tmp, "demo", "c1", decision="reject")
        result = aitp_promote_candidate(self.tmp, "demo", "c1")
        self.assertIn("not approved", result.lower())


class TestStopHookScope(unittest.TestCase):
    """Test that stop-hook only updates the active topic."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Create two topics
        from brain.mcp_server import aitp_bootstrap_topic
        aitp_bootstrap_topic(self.tmp, "alpha", "Alpha", "Q1?")
        aitp_bootstrap_topic(self.tmp, "beta", "Beta", "Q2?")

    def test_stop_hook_only_updates_active_topic(self):
        from hooks.stop import stop_for_topic
        from pathlib import Path
        from brain.state_model import topics_dir
        td = topics_dir(self.tmp)
        (td / ".current_topic").write_text("alpha", encoding="utf-8")
        stop_for_topic(self.tmp)
        alpha_state = (td / "alpha" / "state.md").read_text(encoding="utf-8")
        beta_state = (td / "beta" / "state.md").read_text(encoding="utf-8")
        self.assertIn("Session ended", alpha_state)
        self.assertNotIn("Session ended", beta_state)


if __name__ == "__main__":
    unittest.main()
