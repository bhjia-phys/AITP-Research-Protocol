"""Tests for L4 physics adjudication (six outcomes) and global L2 memory."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import (
    L4_OUTCOMES,
    PHYSICS_CHECK_FIELDS,
)
from tests.test_l3_subplanes import _bootstrap_l1_complete


def _bootstrap_with_candidate(tmp: str) -> tuple[Path, str]:
    """Bootstrap topic with a submitted candidate ready for validation."""
    repo_root = _bootstrap_l1_complete(tmp)
    mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
    tr = repo_root / "topics" / "demo-topic"
    # Fill ideation and advance through to distillation for completeness
    for sp, artifact_name, fields, headings in [
        ("ideation", "active_idea.md",
         {"idea_statement": "Idea", "motivation": "Motivation"},
         ["## Idea Statement", "## Motivation"]),
        ("planning", "active_plan.md",
         {"plan_statement": "Plan", "derivation_route": "Route"},
         ["## Plan Statement", "## Derivation Route"]),
        ("analysis", "active_analysis.md",
         {"analysis_statement": "Analysis", "method": "Method"},
         ["## Analysis Statement", "## Method"]),
        ("result_integration", "active_integration.md",
         {"integration_statement": "Integration", "findings": "Findings"},
         ["## Integration Statement", "## Findings"]),
        ("distillation", "active_distillation.md",
         {"distilled_claim": "Claim", "evidence_summary": "Evidence"},
         ["## Distilled Claim", "## Evidence Summary"]),
    ]:
        mcp_server._write_md(
            tr / "L3" / sp / artifact_name,
            {"artifact_kind": f"l3_active_{sp}", "subplane": sp, **fields},
            "# Active\n\n" + "\n".join(f"{h}\nContent" for h in headings) + "\n",
        )
        if sp != "distillation":
            next_sp = ["planning", "analysis", "result_integration", "distillation"][
                ["ideation", "planning", "analysis", "result_integration"].index(sp)
            ]
            mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", next_sp)

    # Submit candidate
    mcp_server.aitp_submit_candidate(
        tmp, "demo-topic", "cand-1", "Test Claim", "Test Evidence",
    )
    return repo_root, "cand-1"


class L4ReviewTests(unittest.TestCase):
    def test_review_can_end_in_partial_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            result = mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "partial_pass",
                "Dimensional check passed but symmetry check inconclusive.",
            )
            self.assertIn("partial_pass", result)
            tr = repo_root / "topics" / "demo-topic"
            review_path = tr / "L4" / "reviews" / "cand-1.md"
            self.assertTrue(review_path.exists())
            fm, _ = mcp_server._parse_md(review_path)
            self.assertEqual(fm["outcome"], "partial_pass")

    def test_review_can_end_in_contradiction(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            result = mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "contradiction",
                "Claim contradicts eq.12 in source.",
            )
            self.assertIn("contradiction", result)

    def test_review_can_end_in_stuck(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            result = mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "stuck",
                "Cannot resolve sign ambiguity without further data.",
            )
            self.assertIn("stuck", result)

    def test_six_outcomes_are_all_valid(self):
        expected = {"pass", "partial_pass", "fail", "contradiction", "stuck", "timeout"}
        self.assertEqual(set(L4_OUTCOMES), expected)


class PhysicsChecksTests(unittest.TestCase):
    def test_physics_check_fields_are_known(self):
        expected = {
            "dimensional_consistency", "symmetry_compatibility",
            "limiting_case_check", "conservation_check", "correspondence_check",
        }
        self.assertEqual(set(PHYSICS_CHECK_FIELDS), expected)


class GlobalL2MemoryTests(unittest.TestCase):
    def test_promote_writes_to_global_l2_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass", "All checks passed.",
                devils_advocate="Test fixture review.",
            )
            # Advance candidate through promotion gate
            tr = repo_root / "topics" / "demo-topic"
            cand_path = tr / "L3" / "candidates" / f"{cand_id}.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", cand_id)
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", cand_id, "approve")
            result = mcp_server.aitp_promote_candidate(tmp, "demo-topic", cand_id)
            self.assertIn("L2", result)

            # Should exist in global L2
            global_l2 = Path(tmp).parent / "L2" if Path(tmp).name == "topics" else Path(tmp) / "L2"
            # The actual path depends on _global_l2_path
            from brain.mcp_server import _global_l2_path
            g2 = _global_l2_path(tmp)
            self.assertTrue((g2 / "cand-1.md").exists(), "Must exist in global L2")

    def test_conflicting_existing_unit_creates_conflict_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass", "All checks passed.",
                devils_advocate="Test fixture review.",
            )
            # Fast-forward promotion
            tr = repo_root / "topics" / "demo-topic"
            cand_path = tr / "L3" / "candidates" / f"{cand_id}.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", cand_id)
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", cand_id, "approve")
            # Promote once
            mcp_server.aitp_promote_candidate(tmp, "demo-topic", cand_id)
            # Submit same candidate again and try to promote again
            mcp_server.aitp_submit_candidate(
                tmp, "demo-topic", "cand-1", "Conflicting Claim", "Different Evidence",
            )
            cand_path = tr / "L3" / "candidates" / "cand-1.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", "cand-1")
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", "cand-1", "approve")
            result = mcp_server.aitp_promote_candidate(tmp, "demo-topic", "cand-1")
            # Should detect conflict (different claim vs existing)
            self.assertIn("conflict", result.lower() + " detected")

    def test_repeat_promotion_creates_version_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass", "All checks passed.",
                devils_advocate="Test fixture review.",
            )
            tr = repo_root / "topics" / "demo-topic"
            cand_path = tr / "L3" / "candidates" / f"{cand_id}.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            fm["claim"] = "Same claim text"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", cand_id)
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", cand_id, "approve")
            mcp_server.aitp_promote_candidate(tmp, "demo-topic", cand_id)
            # Same claim, promote again
            mcp_server.aitp_submit_candidate(
                tmp, "demo-topic", "cand-1", "Same Claim", "Same Evidence",
            )
            cand_path = tr / "L3" / "candidates" / "cand-1.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            fm["claim"] = "Same claim text"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", "cand-1")
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", "cand-1", "approve")
            result = mcp_server.aitp_promote_candidate(tmp, "demo-topic", "cand-1")
            self.assertTrue("v2" in result.lower() or "version" in result.lower() or "reuse" in result.lower())


class TrustClassificationTests(unittest.TestCase):
    def test_promoted_unit_has_2d_trust(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass", "All checks passed.",
                devils_advocate="Test fixture review.",
            )
            tr = repo_root / "topics" / "demo-topic"
            cand_path = tr / "L3" / "candidates" / f"{cand_id}.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            mcp_server._write_md(cand_path, fm, body)
            mcp_server.aitp_request_promotion(tmp, "demo-topic", cand_id)
            mcp_server.aitp_resolve_promotion_gate(tmp, "demo-topic", cand_id, "approve")
            mcp_server.aitp_promote_candidate(tmp, "demo-topic", cand_id)
            from brain.mcp_server import _global_l2_path
            g2 = _global_l2_path(tmp)
            l2_fm, _ = mcp_server._parse_md(g2 / "cand-1.md")
            self.assertIn("trust_basis", l2_fm)
            self.assertIn("trust_scope", l2_fm)
            self.assertEqual(l2_fm["trust_basis"], "validated")
            self.assertEqual(l2_fm["trust_scope"], "bounded_reusable")


if __name__ == "__main__":
    unittest.main()
