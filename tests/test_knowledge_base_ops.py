"""Tests for knowledge-base operations: index, log, ingest, query, lint, writeback."""

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


class IngestQueryTests(unittest.TestCase):
    def test_ingest_updates_l1_source_basis_and_topic_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_ingest_knowledge(
                tmp, "demo-topic", "paper-x",
                "paper", "Paper X Title", "arxiv-id-x",
                "core", "This is a core source about the gap.",
            )
            self.assertIn("paper-x", result)

            tr = repo_root / "topics" / "demo-topic"
            # Source should be registered in L0
            src_dir = tr / "L0" / "sources"
            self.assertTrue(any("paper-x" in p.name for p in src_dir.glob("*.md")))

            # Topic log should have an ingest event
            log_text = (tr / "runtime" / "log.md").read_text(encoding="utf-8")
            self.assertIn("ingest", log_text.lower())

    def test_query_returns_layer_aware_answer_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_query_knowledge(
                tmp, "demo-topic", "What is the bounded question?",
            )
            self.assertIn("basis_layer", result)
            self.assertIn("artifact_refs", result)
            self.assertIn("authority_warning", result)

    def test_query_does_not_promote_material_across_authority_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_query_knowledge(
                tmp, "demo-topic", "Is this confirmed?",
            )
            self.assertNotEqual(result.get("basis_layer"), "L2",
                                "Query should not claim L2 authority from L1 data")


class LintTests(unittest.TestCase):
    def test_lint_finds_unresolved_contradiction_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_with_l3(tmp)
            tr = repo_root / "topics" / "demo-topic"
            # Reset contradiction register to have empty blocking_contradictions
            mcp_server._write_md(
                tr / "L1" / "contradiction_register.md",
                {"artifact_kind": "l1_contradiction_register", "stage": "L1",
                 "blocking_contradictions": ""},
                "# Contradiction Register\n\n## Unresolved Source Conflicts\n\n"
                "## Regime Mismatches\n\n## Notation Collisions\n\n## Blocking Status\n",
            )
            findings = mcp_server.aitp_lint_knowledge(tmp, "demo-topic")
            contradiction_findings = [
                f for f in findings
                if f.get("kind") == "unresolved_contradiction"
            ]
            self.assertTrue(len(contradiction_findings) > 0,
                            "Lint should flag empty contradiction register")

    def test_lint_finds_missing_regime_or_nonclaims(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_with_l3(tmp)
            # Promote a candidate to L2 to have a reusable unit to lint
            mcp_server.aitp_submit_candidate(
                tmp, "demo-topic", "cand-1", "Claim 1", "Evidence",
            )
            # Fast-forward candidate through gate
            tr = repo_root / "topics" / "demo-topic"
            cand_path = tr / "L3" / "candidates" / "cand-1.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", "cand-1")
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", "cand-1", "approve")
            mcp_server.aitp_promote_candidate(tmp, "demo-topic", "cand-1")

            findings = mcp_server.aitp_lint_knowledge(tmp, "demo-topic")
            regime_findings = [
                f for f in findings
                if f.get("kind") in ("missing_regime", "missing_nonclaims")
            ]
            self.assertTrue(len(regime_findings) > 0,
                            "Lint should flag missing regime in promoted unit")

    def test_lint_returns_structured_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            findings = mcp_server.aitp_lint_knowledge(tmp, "demo-topic")
            for f in findings:
                self.assertIn("severity", f)
                self.assertIn("kind", f)
                self.assertIn("artifact_path", f)
                self.assertIn("message", f)


class WritebackTests(unittest.TestCase):
    def test_source_grounded_query_writes_back_only_to_l1(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_writeback_query_result(
                tmp, "demo-topic", "L1", "Note about source scope", "source-scope-note",
            )
            self.assertIn("L1", result)
            tr = Path(tmp) / "topics" / "demo-topic"
            note_path = tr / "L1" / "source-scope-note.md"
            self.assertTrue(note_path.exists(), "Writeback should create L1 note")

    def test_derivational_query_writes_back_only_to_l3(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_writeback_query_result(
                tmp, "demo-topic", "L3", "Note about derivation route", "deriv-note",
            )
            self.assertIn("L3", result)
            tr = Path(tmp) / "topics" / "demo-topic"
            note_path = tr / "L3" / "deriv-note.md"
            self.assertTrue(note_path.exists(), "Writeback should create L3 note")

    def test_reusable_writeback_still_requires_l2_promotion_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            _bootstrap_with_l3(tmp)
            result = mcp_server.aitp_writeback_query_result(
                tmp, "demo-topic", "L2", "Attempted direct write", "bad-note",
            )
            self.assertIn("promotion", result.lower() + " not allowed")
            tr = Path(tmp) / "topics" / "demo-topic"
            self.assertFalse((tr / "L2" / "bad-note.md").exists(),
                             "Direct L2 writeback should be blocked")


if __name__ == "__main__":
    unittest.main()
