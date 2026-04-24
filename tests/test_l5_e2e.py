"""Tests for L5 writing provenance, flow TeX gate, and real-topic E2E."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import L3_SUBPLANES, L3_ACTIVE_ARTIFACT_NAMES
from tests.test_l4_l2_memory import _bootstrap_with_candidate


def _bootstrap_full_flow(tmp: str, lane: str = "formal_theory") -> Path:
    """Full L1->L3->L4->promote flow returning repo_root."""
    repo_root, cand_id = _bootstrap_with_candidate(tmp)
    tr = repo_root / "topics" / "demo-topic"

    # Update lane
    state_fm, state_body = mcp_server._parse_md(tr / "state.md")
    state_fm["lane"] = lane
    mcp_server._write_md(tr / "state.md", state_fm, state_body)

    # Submit review
    mcp_server.aitp_submit_l4_review(
        tmp, "demo-topic", cand_id, "pass", "All checks passed.",
    )

    # Fast-forward promotion
    cand_path = tr / "L3" / "candidates" / "cand-1.md"
    fm, body = mcp_server._parse_md(cand_path)
    fm["status"] = "validated"
    fm["claim"] = "Test claim for e2e"
    mcp_server._write_md(cand_path, fm, body)
    mcp_server.aitp_request_promotion(tmp, "demo-topic", cand_id)
    mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", cand_id, "approve")
    mcp_server.aitp_promote_candidate(tmp, "demo-topic", cand_id)

    # Create minimal flow_notebook.tex (agent-generated in production)
    tex_dir = tr / "L3" / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "flow_notebook.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}\n",
        encoding="utf-8",
    )
    return repo_root


class L5ScaffoldTests(unittest.TestCase):
    def test_l5_scaffolds_created_on_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            for name in [
                "outline.md", "claim_evidence_map.md",
                "equation_provenance.md", "figure_provenance.md", "limitations.md",
            ]:
                self.assertTrue(
                    (tr / "L5_writing" / name).exists(),
                    f"L5_writing/{name} must exist after advance to L5",
                )

    def test_l5_scaffolds_have_required_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            outline = (tr / "L5_writing" / "outline.md").read_text(encoding="utf-8")
            self.assertIn("## Claims", outline)
            self.assertIn("## Structure", outline)


class FlowTeXGateTests(unittest.TestCase):
    def test_l5_advance_without_flow_notebook(self):
        """L5 advance succeeds even without flow notebook (v3: no busy-work gate)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"
            result = mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            self.assertIn("l5", result.lower())
            # Scaffolds should still be created
            for name in ["outline.md", "claim_evidence_map.md",
                         "equation_provenance.md", "figure_provenance.md", "limitations.md"]:
                self.assertTrue(
                    (tr / "L5_writing" / name).exists(),
                    f"L5_writing/{name} must exist after advance to L5",
                )

    def test_l5_write_unblocks_after_flow_notebook_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            result = mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            self.assertIn("L5", result)
            self.assertNotIn("blocked", result.lower())


class RealTopicE2ETests(unittest.TestCase):
    def test_formal_theory_lane_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp, lane="formal_theory")
            tr = repo_root / "topics" / "demo-topic"
            state_fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(state_fm["lane"], "formal_theory")

    def test_toy_numeric_lane_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp, lane="toy_numeric")
            tr = repo_root / "topics" / "demo-topic"
            state_fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(state_fm["lane"], "toy_numeric")

    def test_code_method_lane_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp, lane="code_method")
            tr = repo_root / "topics" / "demo-topic"
            state_fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(state_fm["lane"], "code_method")


class PaperProvenanceTests(unittest.TestCase):
    def test_claim_evidence_map_links_to_earlier_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            cem_path = tr / "L5_writing" / "claim_evidence_map.md"
            self.assertTrue(cem_path.exists())
            text = cem_path.read_text(encoding="utf-8")
            # Should have sections for claims and evidence links
            self.assertIn("## Claims", text)
            self.assertIn("## Evidence Links", text)

    def test_equation_provenance_has_source_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            ep_path = tr / "L5_writing" / "equation_provenance.md"
            self.assertTrue(ep_path.exists())
            text = ep_path.read_text(encoding="utf-8")
            self.assertIn("## Equations", text)
            self.assertIn("## Source Classification", text)

    def test_limitations_contains_non_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_full_flow(tmp)
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_advance_to_l5(tmp, "demo-topic")
            lim_path = tr / "L5_writing" / "limitations.md"
            self.assertTrue(lim_path.exists())
            text = lim_path.read_text(encoding="utf-8")
            self.assertIn("## Non-Claims", text)
            self.assertIn("## Unresolved Issues", text)


if __name__ == "__main__":
    unittest.main()
