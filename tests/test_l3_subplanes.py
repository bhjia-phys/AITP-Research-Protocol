"""Tests for L3 subplane gates, micro-skill dispatch, and flow TeX output."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import (
    evaluate_l1_stage,
    evaluate_l3_stage,
    L3_SUBPLANES,
    L3_ARTIFACT_TEMPLATES,
    topics_dir,
)
from tests.test_state_model import BootstrapL1ScaffoldTests


def _bootstrap_l1_complete(tmp: str) -> Path:
    """Bootstrap a topic with all L1 artifacts filled so it can advance to L3."""
    repo_root = Path(tmp)
    (repo_root / "topics").mkdir(exist_ok=True)
    mcp_server.aitp_bootstrap_topic(
        str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
    )
    tr = repo_root / "topics" / "demo-topic"
    filled = {
        "question_contract.md": (
            {"artifact_kind": "l1_question_contract", "stage": "L1",
             "bounded_question": "What quantity is bounded here?",
             "scope_boundaries": "One model, one regime.",
             "target_quantities": "Gap and symmetry sector."},
            "# Question Contract\n\n## Bounded Question\nWhat quantity is bounded here?\n\n"
            "## Scope Boundaries\nOne model, one regime.\n\n"
            "## Target Quantities Or Claims\nGap and symmetry sector.\n\n"
            "## Non-Success Conditions\nNo broad universality claim.\n\n"
            "## Uncertainty Markers\nFinite-size risk.\n",
        ),
        "source_basis.md": (
            {"artifact_kind": "l1_source_basis", "stage": "L1",
             "core_sources": "paper-a", "peripheral_sources": "note-b"},
            "# Source Basis\n\n## Core Sources\npaper-a\n\n## Peripheral Sources\nnote-b\n\n"
            "## Source Roles\npaper-a is the main derivation source.\n\n"
            "## Reading Depth\nfull_read for paper-a.\n\n"
            "## Why Each Source Matters\npaper-a defines the bounded route.\n",
        ),
        "convention_snapshot.md": (
            {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
             "notation_choices": "Use source-a symbols.",
             "unit_conventions": "Natural units."},
            "# Convention Snapshot\n\n## Notation Choices\nUse source-a symbols.\n\n"
            "## Unit Conventions\nNatural units.\n\n"
            "## Sign Conventions\nHamiltonian sign fixed.\n\n"
            "## Metric Or Coordinate Conventions\nEuclidean.\n\n"
            "## Unresolved Tensions\nNone blocking.\n",
        ),
        "derivation_anchor_map.md": (
            {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
             "starting_anchors": "eq-12"},
            "# Derivation Anchor Map\n\n## Source Anchors\neq-12\n\n"
            "## Missing Steps\nOne omitted algebra step.\n\n"
            "## Candidate Starting Points\neq-12 to eq-14.\n",
        ),
        "contradiction_register.md": (
            {"artifact_kind": "l1_contradiction_register", "stage": "L1",
             "blocking_contradictions": "none"},
            "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n"
            "## Regime Mismatches\nNone blocking.\n\n"
            "## Notation Collisions\nTracked and resolved.\n\n"
            "## Blocking Status\nnone\n",
        ),
        "source_toc_map.md": (
            {"artifact_kind": "l1_source_toc_map", "stage": "L1",
             "sources_with_toc": "paper-a", "total_sections": 1,
             "coverage_status": "complete"},
            "# Source TOC Map\n\n## Per-Source TOC\n\n"
            "### paper-a (TOC confidence: high)\n\n"
            "- [s1] Main Content — status: extracted  → intake: L1/intake/paper-a/s1.md\n\n"
            "## Coverage Summary\n\n## Deferred Sections\n\n## Extraction Notes\n",
        ),
    }
    for name, (fm, body) in filled.items():
        mcp_server._write_md(tr / "L1" / name, fm, body)
    # Create intake note for extracted section (required by L1 quality gate)
    intake_dir = tr / "L1" / "intake" / "paper-a"
    intake_dir.mkdir(parents=True, exist_ok=True)
    mcp_server._write_md(
        intake_dir / "s1.md",
        {"artifact_kind": "l1_section_intake", "source_id": "paper-a",
         "section_id": "s1", "section_title": "Main Content",
         "extraction_status": "extracted", "completeness_confidence": "high",
         "updated_at": "2025-01-01T00:00:00Z"},
        "# Main Content\n\n## Section Summary (skim)\nContent.\n\n"
        "## Key Concepts\nConcept.\n\n## Equations Found\neq.\n\n"
        "## Physical Claims\nClaim.\n\n## Prerequisites\nNone.\n\n"
        "## Cross-References\nNone.\n\n## Completeness Self-Assessment\nConfidence: **high**\n",
    )
    return repo_root


class L3SubplaneGateTests(unittest.TestCase):
    def test_new_l3_topic_starts_in_ideation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["stage"], "L3")
            self.assertEqual(brief["l3_subplane"], "ideation")
            self.assertIn("blocked", brief["gate_status"])

    def test_l3_cannot_skip_from_ideation_to_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            result = mcp_server.aitp_advance_l3_subplane(
                str(repo_root), "demo-topic", "analysis",
            )
            self.assertIn("not allowed", result.lower())

    def test_l3_requires_active_artifact_per_subplane(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertIn("active_idea", brief.get("required_artifact_path", ""))

    def test_l3_subplane_advance_sequential(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill ideation
            mcp_server._write_md(
                tr / "L3" / "ideation" / "active_idea.md",
                {"artifact_kind": "l3_active_idea", "subplane": "ideation",
                 "idea_statement": "Test idea", "motivation": "Why this matters"},
                "# Active Idea\n\n## Idea Statement\nTest idea\n\n## Motivation\nWhy this matters\n",
            )
            result = mcp_server.aitp_advance_l3_subplane(
                str(repo_root), "demo-topic", "planning",
            )
            self.assertIn("planning", result.lower())
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["l3_subplane"], "planning")

    def test_l3_backedge_from_analysis_to_ideation_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            tr = repo_root / "topics" / "demo-topic"
            # Fill ideation and advance to planning, then analysis
            mcp_server._write_md(
                tr / "L3" / "ideation" / "active_idea.md",
                {"artifact_kind": "l3_active_idea", "subplane": "ideation",
                 "idea_statement": "Idea", "motivation": "Motivation"},
                "# Active Idea\n\n## Idea Statement\nIdea\n\n## Motivation\nMotivation\n",
            )
            mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "planning")
            mcp_server._write_md(
                tr / "L3" / "planning" / "active_plan.md",
                {"artifact_kind": "l3_active_plan", "subplane": "planning",
                 "plan_statement": "Plan", "derivation_route": "Route"},
                "# Active Plan\n\n## Plan Statement\nPlan\n\n## Derivation Route\nRoute\n",
            )
            mcp_server.aitp_advance_l3_subplane(str(repo_root), "demo-topic", "analysis")
            # Backedge to ideation is allowed
            result = mcp_server.aitp_advance_l3_subplane(
                str(repo_root), "demo-topic", "ideation",
            )
            self.assertIn("ideation", result.lower())

    def test_l3_cannot_skip_distillation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            result = mcp_server.aitp_advance_l3_subplane(
                str(repo_root), "demo-topic", "distillation",
            )
            self.assertIn("not allowed", result.lower() + " denied")


class L3SubplaneSkillTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_session_start_mentions_l3_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = _bootstrap_l1_complete(tmp)
            mcp_server.aitp_advance_to_l3(str(repo_root), "demo-topic")
            completed = subprocess.run(
                [sys.executable, str(self.REPO_ROOT / "hooks" / "session_start.py")],
                cwd=repo_root, text=True, capture_output=True, check=True,
            )
            self.assertIn("stage: L3", completed.stdout)
            self.assertIn("ideation", completed.stdout)
            self.assertIn("skill-l3-ideate", completed.stdout)



if __name__ == "__main__":
    unittest.main()
