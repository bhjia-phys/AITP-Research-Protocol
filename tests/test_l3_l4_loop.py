"""Tests for the L3↔L4 iterative loop — the core research cycle."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import L3_SUBPLANES
from tests.test_l4_l2_memory import _bootstrap_with_candidate


class L3L4SingleLoopTests(unittest.TestCase):
    """Test one complete L3→L4→L3 cycle."""

    def test_l4_return_to_l3_sets_analysis_subplane(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            # L4: create contract and review with pass
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass", "OK",
            )
            # Return to L3
            result = mcp_server.aitp_return_to_l3_from_l4(
                tmp, "demo-topic", reason="post_l4_analysis",
            )
            self.assertIn("L3", result["message"])

            # Verify state
            fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(fm["stage"], "L3")
            self.assertEqual(fm["l3_subplane"], "analysis")
            self.assertEqual(fm["l4_return_reason"], "post_l4_analysis")

    def test_l4_fail_then_return_to_l3(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "fail", "Dimensional mismatch.",
            )
            result = mcp_server.aitp_return_to_l3_from_l4(
                tmp, "demo-topic", reason="post_l4_revision",
            )
            self.assertIn("L3", result["message"])

            fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(fm["stage"], "L3")
            self.assertEqual(fm["l3_subplane"], "analysis")

            # Candidate should have l4_outcome recorded
            cand_fm, _ = mcp_server._parse_md(tr / "L3" / "candidates" / f"{cand_id}.md")
            self.assertEqual(cand_fm.get("l4_outcome"), "fail")

    def test_l4_contradiction_then_return_to_l3(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)

            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "contradiction",
                "Contradicts eq.12.",
            )
            result = mcp_server.aitp_return_to_l3_from_l4(
                tmp, "demo-topic", reason="post_l4_revision",
            )
            self.assertIn("L3", result["message"])

    def test_l4_partial_pass_then_return_to_l3(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency", "limiting_case_check"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "partial_pass",
                "Dimensional OK, limiting case inconclusive.",
            )
            result = mcp_server.aitp_return_to_l3_from_l4(
                tmp, "demo-topic", reason="post_l4_revision",
            )
            self.assertIn("L3", result["message"])

            # Candidate should be partial_validated
            cand_fm, _ = mcp_server._parse_md(tr / "L3" / "candidates" / f"{cand_id}.md")
            self.assertEqual(cand_fm.get("status"), "partial_validated")


class L3L4MultiLoopTests(unittest.TestCase):
    """Test multiple L3→L4→L3 cycles — the iterative refinement loop."""

    def test_two_cycle_loop_fail_then_pass(self):
        """Cycle 1: L3→L4 fail→L3 revise→L4 pass."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            # === Cycle 1: fail ===
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "fail",
                "Sign error in derivation step 3.",
            )
            mcp_server.aitp_return_to_l3_from_l4(
                tmp, "demo-topic", reason="post_l4_revision",
            )

            # Verify back at L3 analysis
            fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(fm["stage"], "L3")
            self.assertEqual(fm["l3_subplane"], "analysis")

            # Revise: re-do analysis artifact
            mcp_server._write_md(
                tr / "L3" / "analysis" / "active_analysis.md",
                {"artifact_kind": "l3_active_analysis", "subplane": "analysis",
                 "analysis_statement": "Fixed sign error", "method": "Corrected method"},
                "# Active Analysis\n\n## Analysis Statement\nFixed sign error\n\n## Method\nCorrected method\n",
            )

            # Advance through remaining subplanes and resubmit
            mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "result_integration")
            mcp_server._write_md(
                tr / "L3" / "result_integration" / "active_integration.md",
                {"artifact_kind": "l3_active_integration", "subplane": "result_integration",
                 "integration_statement": "Integrated", "findings": "Sign corrected"},
                "# Active Integration\n\n## Integration Statement\nIntegrated\n\n## Findings\nSign corrected\n",
            )
            mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "distillation")
            mcp_server._write_md(
                tr / "L3" / "distillation" / "active_distillation.md",
                {"artifact_kind": "l3_active_distillation", "subplane": "distillation",
                 "distilled_claim": "Corrected claim", "evidence_summary": "Fixed evidence"},
                "# Active Distillation\n\n## Distilled Claim\nCorrected claim\n\n## Evidence Summary\nFixed evidence\n",
            )

            # Resubmit same candidate (new version)
            mcp_server.aitp_submit_candidate(
                tmp, "demo-topic", cand_id,
                "Revised Claim", "Fixed sign error in derivation.",
            )

            # === Cycle 2: pass ===
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            result = mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass",
                "All checks passed after revision.",
            )
            self.assertIn("pass", result["message"])

            # Verify candidate is now validated
            cand_fm, _ = mcp_server._parse_md(tr / "L3" / "candidates" / f"{cand_id}.md")
            self.assertEqual(cand_fm["status"], "validated")

            # Log should have both reviews
            log_text = (tr / "runtime" / "log.md").read_text(encoding="utf-8")
            self.assertIn("fail", log_text)
            self.assertIn("pass", log_text)

    def test_three_cycle_loop_with_stuck(self):
        """Cycle 1: partial_pass → Cycle 2: stuck → Cycle 3: pass."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            # === Cycle 1: partial_pass ===
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency", "limiting_case_check"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "partial_pass",
                "Dimensional OK, limiting case inconclusive.",
            )
            mcp_server.aitp_return_to_l3_from_l4(tmp, "demo-topic", reason="post_l4_revision")

            # === Cycle 2: stuck ===
            # Revise and resubmit
            self._revise_and_resubmit(tr, tmp, repo_root, cand_id,
                                      "Attempted fix", "Still investigating")
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency", "limiting_case_check"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "stuck",
                "Cannot resolve ambiguity without further data.",
            )
            mcp_server.aitp_return_to_l3_from_l4(tmp, "demo-topic", reason="post_l4_revision")

            # === Cycle 3: pass ===
            self._revise_and_resubmit(tr, tmp, repo_root, cand_id,
                                      "Final fix", "Resolved with additional data")
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency", "limiting_case_check"],
            )
            result = mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "pass",
                "All checks passed.",
            )
            self.assertIn("pass", result["message"])

            # Verify final state
            cand_fm, _ = mcp_server._parse_md(tr / "L3" / "candidates" / f"{cand_id}.md")
            self.assertEqual(cand_fm["status"], "validated")

            # Log should record all 3 reviews
            log_text = (tr / "runtime" / "log.md").read_text(encoding="utf-8")
            self.assertEqual(log_text.count("L4 review"), 3)

    def _revise_and_resubmit(self, tr, tmp, repo_root, cand_id, claim, evidence):
        """Helper: revise analysis through distillation and resubmit."""
        mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "analysis")
        mcp_server._write_md(
            tr / "L3" / "analysis" / "active_analysis.md",
            {"artifact_kind": "l3_active_analysis", "subplane": "analysis",
             "analysis_statement": claim, "method": "Revised"},
            f"# Active Analysis\n\n## Analysis Statement\n{claim}\n\n## Method\nRevised\n",
        )
        mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "result_integration")
        mcp_server._write_md(
            tr / "L3" / "result_integration" / "active_integration.md",
            {"artifact_kind": "l3_active_integration", "subplane": "result_integration",
             "integration_statement": "Integrated", "findings": evidence},
            f"# Active Integration\n\n## Integration Statement\nIntegrated\n\n## Findings\n{evidence}\n",
        )
        mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "distillation")
        mcp_server._write_md(
            tr / "L3" / "distillation" / "active_distillation.md",
            {"artifact_kind": "l3_active_distillation", "subplane": "distillation",
             "distilled_claim": claim, "evidence_summary": evidence},
            f"# Active Distillation\n\n## Distilled Claim\n{claim}\n\n## Evidence Summary\n{evidence}\n",
        )
        mcp_server.aitp_submit_candidate(tmp, "demo-topic", cand_id, claim, evidence)


class L3L4LoopEdgeCases(unittest.TestCase):
    """Edge cases in the L3↔L4 loop."""

    def test_cannot_return_to_l3_from_l1(self):
        """aitp_return_to_l3_from_l4 should reject if not at L3/L4."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, _ = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"
            # Ensure at L1 by not advancing
            fm, body = mcp_server._parse_md(tr / "state.md")
            fm["stage"] = "L1"
            mcp_server._write_md(tr / "state.md", fm, body)

            result = mcp_server.aitp_return_to_l3_from_l4(tmp, "demo-topic")
            self.assertIn("Cannot return", result["message"])

    def test_l4_review_preserves_evidence_across_cycles(self):
        """Evidence from cycle 1 should still be in review file after cycle 2."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            tr = repo_root / "topics" / "demo-topic"

            # Cycle 1: fail with specific notes
            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "fail",
                "Step 3 sign error.",
                check_results={"dimensional_consistency": "fail: unit mismatch"},
            )
            mcp_server.aitp_return_to_l3_from_l4(tmp, "demo-topic", reason="post_l4_revision")

            # The review file from cycle 1 should exist
            review_path = tr / "L4" / "reviews" / f"{cand_id}.md"
            self.assertTrue(review_path.exists())
            rev_fm, _ = mcp_server._parse_md(review_path)
            self.assertEqual(rev_fm["outcome"], "fail")
            self.assertIn("dimensional_consistency", rev_fm.get("check_results", {}))

    def test_execution_brief_after_l4_return_shows_l3(self):
        """After returning from L4, execution brief should show L3 status."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)

            mcp_server.aitp_create_validation_contract(
                tmp, "demo-topic", cand_id,
                mandatory_checks=["dimensional_consistency"],
            )
            mcp_server.aitp_submit_l4_review(
                tmp, "demo-topic", cand_id, "fail", "Error found.",
            )
            mcp_server.aitp_return_to_l3_from_l4(tmp, "demo-topic", reason="post_l4_revision")

            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["stage"], "L3")
            self.assertEqual(brief["l3_subplane"], "analysis")

    def test_l4_review_outcome_updates_candidate_status(self):
        """Each outcome should set the correct candidate status."""
        with tempfile.TemporaryDirectory() as tmp:
            outcomes_expected = {
                "pass": "validated",
                "partial_pass": "partial_validated",
                "fail": None,       # keeps submitted, adds l4_outcome
                "contradiction": None,
                "stuck": None,
                "timeout": None,
            }
            for outcome, expected_status in outcomes_expected.items():
                with self.subTest(outcome=outcome):
                    repo_root, cand_id = _bootstrap_with_candidate(tmp)
                    tr = repo_root / "topics" / "demo-topic"

                    mcp_server.aitp_create_validation_contract(
                        tmp, "demo-topic", cand_id,
                        mandatory_checks=["dimensional_consistency"],
                    )
                    mcp_server.aitp_submit_l4_review(
                        tmp, "demo-topic", cand_id, outcome, f"Review: {outcome}",
                    )

                    cand_fm, _ = mcp_server._parse_md(
                        tr / "L3" / "candidates" / f"{cand_id}.md"
                    )
                    if expected_status:
                        self.assertEqual(cand_fm.get("status"), expected_status,
                                         f"Outcome '{outcome}' should set status to '{expected_status}'")
                    else:
                        # Non-pass outcomes record l4_outcome
                        self.assertEqual(cand_fm.get("l4_outcome"), outcome)


if __name__ == "__main__":
    unittest.main()
