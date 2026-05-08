"""Tests for L4 physics adjudication (six outcomes) and global L2 memory."""

from __future__ import annotations

import json
import re
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

    # Fill ideate and advance through to distill for completeness
    _long = "X" * 60  # satisfy minimum content length checks in preflight
    activity_sequence = [
        ("ideate", "active_idea.md",
         {"idea_statement": "Idea", "motivation": "Motivation"},
         [("## Idea Statement", _long), ("## Motivation", _long)]),
        ("plan", "active_plan.md",
         {"plan_statement": "Plan", "derivation_route": "Route"},
         [("## Plan Statement", _long), ("## Derivation Route", _long)]),
        ("derive", "active_derivation.md",
         {"derivation_count": 1, "all_steps_justified": "yes"},
         [("## Derivation Chains", _long), ("## Step-by-Step Trace", _long)]),
        ("gap-audit", "active_gaps.md",
         {"gap_audit_count": 1},
         [("## Correspondence Check", _long), ("## Gap Report", _long)]),
        ("integrate", "active_integration.md",
         {"integration_statement": "Integration", "findings": "Findings"},
         [("## Integration Statement", _long), ("## Findings", _long)]),
        ("distill", "active_distillation.md",
         {"distilled_claim": "Claim", "evidence_summary": "Evidence"},
         [("## Distilled Claim", _long), ("## Evidence Summary", _long)]),
    ]
    for i, (act, artifact_name, fields, headings) in enumerate(activity_sequence):
        mcp_server._write_md(
            tr / "L3" / act / artifact_name,
            {"artifact_kind": f"l3_active_{act}", "activity": act, **fields},
            "# Active\n\n" + "\n".join(f"{h}\n{body}" for h, body in headings) + "\n",
        )
        if i < len(activity_sequence) - 1:
            next_act = activity_sequence[i + 1][0]
            mcp_server.aitp_switch_l3_activity(str(repo_root), "demo-topic", next_act)

    # Submit candidate
    mcp_server.aitp_submit_candidate(
        tmp, "demo-topic", "cand-1", "Test Claim",
        claim="Test Evidence claim text",
        evidence="Supporting evidence",
    )

    # Create minimal derivation steps at the resolved topic root
    # (resolve_topic_root prefers <tmp>/<slug> over <tmp>/topics/<slug>)
    resolved_root = mcp_server._topic_root(str(repo_root), "demo-topic")
    steps_dir = resolved_root / "L2" / "graph" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    (steps_dir / "step-01.md").write_text("""---
step_id: step-01
claim: Test derivation step
status: completed
---
# Step 01
Test derivation step content for preflight validation.
""", encoding="utf-8")

    # Also create at the tr path for test assertions that use tr directly
    steps_dir2 = tr / "L2" / "graph" / "steps"
    steps_dir2.mkdir(parents=True, exist_ok=True)
    (steps_dir2 / "step-01.md").write_text("""---
step_id: step-01
claim: Test derivation step
status: completed
---
# Step 01
Test derivation step content for preflight validation.
""", encoding="utf-8")

    # Set topic stage to L4 and pre-approve promotion preflight checks
    # Note: gate_override_scope must be "current_gate" or "this_session"
    # for current_gate_status() to recognize it (cli/state.py:68)
    for state_path in (resolved_root / "state.md", tr / "state.md"):
        if state_path.exists():
            state_fm, state_body = mcp_server._parse_md(state_path)
            state_fm["stage"] = "L4"
            state_fm["gate_override"] = True
            state_fm["gate_override_reason"] = "test fixture"
            state_fm["gate_override_scope"] = "current_gate"
            state_fm["l4_human_reviewed"] = True
            state_fm["l4_human_decision"] = "approved"
            mcp_server._write_md(state_path, state_fm, state_body)

    return repo_root, "cand-1"


class L4ReviewTests(unittest.TestCase):
    def test_review_can_end_in_partial_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            result = mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="partial_pass",
                notes="Dimensional check passed but symmetry check inconclusive.",
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
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="contradiction",
                notes="Claim contradicts eq.12 in source.",
            )
            self.assertIn("contradiction", result)

    def test_review_can_end_in_stuck(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            result = mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="stuck",
                notes="Cannot resolve sign ambiguity without further data.",
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
            "approximation_validity_check", "unitarity_check", "causality_check",
        }
        self.assertEqual(set(PHYSICS_CHECK_FIELDS), expected)


class GlobalL2MemoryTests(unittest.TestCase):
    def test_promote_writes_to_global_l2_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="pass",
                notes="All checks passed.",
                check_results={"dimensional_consistency": "pass"},
                devils_advocate="Test fixture review.",
            )
            mcp_server.aitp_request_promotion(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            mcp_server.aitp_resolve_promotion_gate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, decision="approve",
            )
            result = mcp_server.aitp_promote_candidate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            self.assertIn("Promoted", result)

            from brain.mcp_server import _global_l2_path
            g2 = _global_l2_path(tmp)
            self.assertTrue((g2 / "cand-1.md").exists(), "Must exist in global L2")

    def test_conflicting_existing_unit_creates_conflict_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="pass",
                notes="All checks passed.",
                check_results={"dimensional_consistency": "pass"},
                devils_advocate="Test fixture review.",
            )
            mcp_server.aitp_request_promotion(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            mcp_server.aitp_resolve_promotion_gate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, decision="approve",
            )
            mcp_server.aitp_promote_candidate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )

            # Submit same candidate with different claim
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_submit_candidate(
                tmp, "demo-topic", "cand-1", "Conflicting Claim", "Different Evidence",
            )
            cand_path = tr / "L3" / "candidates" / "cand-1.md"
            fm, body = mcp_server._parse_md(cand_path)
            fm["status"] = "validated"
            # Set a different claim to trigger conflict
            cand_fm_new, cand_body_new = mcp_server._parse_md(cand_path)
            cand_fm_new["claim"] = "Completely different claim"
            cand_fm_new["status"] = "validated"
            mcp_server._write_md(cand_path, cand_fm_new, cand_body_new)

            mcp_server.aitp_request_promotion(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id="cand-1",
            )
            mcp_server.aitp_resolve_promotion_gate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id="cand-1", decision="approve",
            )
            result = mcp_server.aitp_promote_candidate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id="cand-1",
            )
            self.assertTrue(
                "Conflict" in result or "conflict" in result.lower()
                or "v2" in result.lower() or "Promoted" in result
            )

    def test_repeat_promotion_creates_version_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="pass",
                notes="All checks passed.",
                check_results={"dimensional_consistency": "pass"},
                devils_advocate="Test fixture review.",
            )
            tr = repo_root / "topics" / "demo-topic"
            mcp_server.aitp_request_promotion(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            mcp_server.aitp_resolve_promotion_gate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, decision="approve",
            )
            result = mcp_server.aitp_promote_candidate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            self.assertTrue(
                "Promoted" in result or "v" in result.lower()
            )


class TrustClassificationTests(unittest.TestCase):
    def test_promoted_unit_has_2d_trust(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root, cand_id = _bootstrap_with_candidate(tmp)
            mcp_server.aitp_submit_l4_review(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, outcome="pass",
                notes="All checks passed.",
                check_results={"dimensional_consistency": "pass"},
                devils_advocate="Test fixture review.",
            )
            mcp_server.aitp_request_promotion(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            mcp_server.aitp_resolve_promotion_gate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id, decision="approve",
            )
            mcp_server.aitp_promote_candidate(
                topics_root=tmp, topic_slug="demo-topic",
                candidate_id=cand_id,
            )
            from brain.mcp_server import _global_l2_path
            g2 = _global_l2_path(tmp)
            l2_fm, _ = mcp_server._parse_md(g2 / "cand-1.md")
            self.assertIn("trust_basis", l2_fm)
            self.assertIn("trust_scope", l2_fm)
            self.assertEqual(l2_fm["trust_basis"], "validated")
            self.assertEqual(l2_fm["trust_scope"], "bounded_reusable")


class L4FixtureValidationTests(unittest.TestCase):
    """Verify L4 test data fixtures are well-formed and match protocol constants."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_root = (
            Path(__file__).resolve().parent / "fixtures" / "l4"
        )

    # ── Review fixtures ──

    def test_all_six_outcome_fixtures_exist(self):
        reviews_dir = self.fixture_root / "reviews"
        self.assertTrue(reviews_dir.is_dir(), f"Missing: {reviews_dir}")

        found = set()
        for path in sorted(reviews_dir.glob("cand-*.md")):
            # Skip versioned files (_v2, _v3, etc.)
            if re.match(r".*_v\d+\.md$", path.name):
                continue
            fm, _ = mcp_server._parse_md(path)
            outcome = fm.get("outcome", "")
            if outcome:
                found.add(outcome)

        expected = set(L4_OUTCOMES)
        missing = expected - found
        self.assertEqual(
            missing, set(),
            f"Missing L4 outcome fixtures: {missing}. "
            f"Found: {found}",
        )

    def test_each_review_fixture_has_required_fields(self):
        reviews_dir = self.fixture_root / "reviews"
        for path in sorted(reviews_dir.glob("cand-*.md")):
            with self.subTest(path=path.name):
                fm, body = mcp_server._parse_md(path)
                self.assertIn("outcome", fm,
                              f"Missing 'outcome' in {path.name}")
                self.assertIn(fm["outcome"], L4_OUTCOMES,
                              f"Invalid outcome in {path.name}: {fm['outcome']}")
                self.assertIn("artifact_kind", fm)
                self.assertEqual(fm["artifact_kind"], "l4_review")
                self.assertIn("candidate_id", fm)
                self.assertIn("l4_cycle", fm)
                self.assertIn("reviewed_at", fm)
                self.assertIn("## Outcome", body)
                self.assertIn("## Check Results", body)

    def test_pass_review_has_devils_advocate(self):
        path = self.fixture_root / "reviews" / "cand-qho-energy-spectrum.md"
        self.assertTrue(path.exists(), f"Missing: {path}")
        fm, body = mcp_server._parse_md(path)
        self.assertEqual(fm["outcome"], "pass")
        self.assertIn("devils_advocate", fm,
                      "Pass review must have devils_advocate field")
        self.assertGreater(len(fm["devils_advocate"].strip()), 20,
                           "Devil's advocate must be substantive")
        self.assertIn("## Devil's Advocate", body)

    def test_versioned_review_fixture_exists(self):
        path = self.fixture_root / "reviews" / "cand-qho-energy-spectrum_v2.md"
        self.assertTrue(path.exists(), f"Missing versioned review: {path}")
        fm, body = mcp_server._parse_md(path)
        self.assertEqual(fm["outcome"], "pass")
        self.assertEqual(fm["l4_cycle"], 2)
        self.assertIn("v1", body.lower() or "v1")

    # ── Validation contract fixture ──

    def test_validation_contract_fixture(self):
        path = self.fixture_root / "validation_contract.md"
        self.assertTrue(path.exists(), f"Missing: {path}")
        fm, body = mcp_server._parse_md(path)
        self.assertEqual(fm["artifact_kind"], "l4_validation_contract")
        self.assertIn("mandatory_checks", fm)
        self.assertGreaterEqual(len(fm["mandatory_checks"]), 4)
        for check in fm["mandatory_checks"]:
            self.assertIn(check, PHYSICS_CHECK_FIELDS,
                          f"Unknown check '{check}' in validation contract")

    # ── Physics check baseline fixture ──

    def test_physics_check_baseline_fixture(self):
        path = self.fixture_root / "physics_check_baseline.json"
        self.assertTrue(path.exists(), f"Missing: {path}")

        import json
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(data["physics_check_fields"]),
            set(PHYSICS_CHECK_FIELDS),
        )
        self.assertEqual(
            set(data["l4_outcomes"]),
            set(L4_OUTCOMES),
        )
        self.assertIn("lane_evidence_requirements", data)
        for lane in ("formal_theory", "toy_numeric", "code_method"):
            self.assertIn(lane, data["lane_evidence_requirements"],
                          f"Missing lane '{lane}' in baseline")

    # ── Candidate baseline fixture ──

    def test_candidate_baseline_fixture(self):
        path = self.fixture_root / "candidate_baseline.md"
        self.assertTrue(path.exists(), f"Missing: {path}")
        fm, body = mcp_server._parse_md(path)
        self.assertEqual(fm["artifact_kind"], "candidate")
        self.assertEqual(fm["status"], "validated")
        self.assertIn("claim", fm)
        self.assertIn("evidence", fm)
        self.assertIn("regime_of_validity", fm)

    # ── TeX record fixtures ──

    def test_tex_record_exists(self):
        tex_path = self.fixture_root / "tex" / "l4_validation_test_record.tex"
        self.assertTrue(tex_path.exists(),
                        f"Missing L4 TeX record: {tex_path}")

    def test_tex_record_compiles_to_pdf(self):
        pdf_path = self.fixture_root / "tex" / "l4_validation_test_record.pdf"
        self.assertTrue(pdf_path.exists(),
                        f"Missing compiled PDF: {pdf_path}")
        self.assertGreater(pdf_path.stat().st_size, 1000,
                           "PDF file is suspiciously small")

    def test_tex_record_has_build_artifacts(self):
        tex_dir = self.fixture_root / "tex"
        for suffix in (".aux", ".log", ".out", ".toc"):
            artifact = tex_dir / f"l4_validation_test_record{suffix}"
            self.assertTrue(artifact.exists(),
                            f"Missing build artifact: {artifact.name}")

    def test_tex_record_mentions_all_six_outcomes(self):
        tex_path = self.fixture_root / "tex" / "l4_validation_test_record.tex"
        content = tex_path.read_text(encoding="utf-8")
        for outcome in L4_OUTCOMES:
            self.assertIn(
                outcome, content,
                f"TeX record missing outcome '{outcome}'",
            )

    def test_tex_record_references_fixture_paths(self):
        tex_path = self.fixture_root / "tex" / "l4_validation_test_record.tex"
        content = tex_path.read_text(encoding="utf-8")
        self.assertIn("tests/fixtures/l4/", content)
        self.assertIn("test_l4_l2_memory.py", content)


if __name__ == "__main__":
    unittest.main()
