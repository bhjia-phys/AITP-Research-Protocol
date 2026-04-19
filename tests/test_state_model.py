"""Tests for brain stage/posture state model, L1 gates, and execution brief."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from brain import mcp_server
from brain.state_model import topics_dir, topic_root, validate_topic_slug


class TopicRootResolutionTests(unittest.TestCase):
    def test_repo_root_with_topics_dir_resolves_topic_inside_topics_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "topics" / "demo-topic").mkdir(parents=True)
            resolved = topic_root(repo_root, "demo-topic")
            self.assertEqual(resolved, repo_root / "topics" / "demo-topic")

    def test_direct_topics_root_still_resolves_existing_topic(self):
        with tempfile.TemporaryDirectory() as tmp:
            topics_root = Path(tmp)
            (topics_root / "demo-topic").mkdir()
            resolved = topic_root(topics_root, "demo-topic")
            self.assertEqual(resolved, topics_root / "demo-topic")


class BootstrapL1ScaffoldTests(unittest.TestCase):
    def test_bootstrap_topic_creates_l1_artifacts_and_new_state_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "topics").mkdir()
            mcp_server.aitp_bootstrap_topic(
                str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
            )
            tr = repo_root / "topics" / "demo-topic"
            for name in [
                "question_contract.md", "source_basis.md", "convention_snapshot.md",
                "derivation_anchor_map.md", "contradiction_register.md",
            ]:
                self.assertTrue((tr / "L1" / name).exists(), f"Missing L1/{name}")
            fm, _ = mcp_server._parse_md(tr / "state.md")
            self.assertEqual(fm["status"], "new")
            self.assertEqual(fm["stage"], "L1")
            self.assertEqual(fm["posture"], "read")
            self.assertEqual(fm["lane"], "unspecified")


class L1GateTests(unittest.TestCase):
    def _bootstrap(self, tmp):
        repo_root = Path(tmp)
        (repo_root / "topics").mkdir()
        mcp_server.aitp_bootstrap_topic(
            str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
        )
        return repo_root

    def test_execution_brief_blocks_on_first_missing_l1_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._bootstrap(tmp)
            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["stage"], "L1")
            self.assertEqual(brief["posture"], "read")
            self.assertEqual(brief["gate_status"], "blocked_missing_field")
            self.assertTrue(brief["required_artifact_path"].endswith("question_contract.md"))
            self.assertIn("bounded_question", brief["missing_requirements"])

    def test_execution_brief_turns_ready_after_all_l1_artifacts_are_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = self._bootstrap(tmp)
            tr = repo_root / "topics" / "demo-topic"

            mcp_server._write_md(
                tr / "L1" / "question_contract.md",
                {"artifact_kind": "l1_question_contract", "stage": "L1",
                 "bounded_question": "What quantity is bounded here?",
                 "scope_boundaries": "One model, one regime.",
                 "target_quantities": "Gap and symmetry sector."},
                "# Question Contract\n\n## Bounded Question\nWhat quantity is bounded here?\n\n## Scope Boundaries\nOne model, one regime.\n\n## Target Quantities Or Claims\nGap and symmetry sector.\n\n## Non-Success Conditions\nNo broad universality claim.\n\n## Uncertainty Markers\nFinite-size risk.\n",
            )
            mcp_server._write_md(
                tr / "L1" / "source_basis.md",
                {"artifact_kind": "l1_source_basis", "stage": "L1",
                 "core_sources": "paper-a", "peripheral_sources": "note-b"},
                "# Source Basis\n\n## Core Sources\npaper-a\n\n## Peripheral Sources\nnote-b\n\n## Source Roles\npaper-a is the main derivation source.\n\n## Reading Depth\nfull_read for paper-a.\n\n## Why Each Source Matters\npaper-a defines the bounded route.\n",
            )
            mcp_server._write_md(
                tr / "L1" / "convention_snapshot.md",
                {"artifact_kind": "l1_convention_snapshot", "stage": "L1",
                 "notation_choices": "Use source-a symbols.",
                 "unit_conventions": "Natural units."},
                "# Convention Snapshot\n\n## Notation Choices\nUse source-a symbols.\n\n## Unit Conventions\nNatural units.\n\n## Sign Conventions\nHamiltonian sign fixed.\n\n## Metric Or Coordinate Conventions\nEuclidean.\n\n## Unresolved Tensions\nNone blocking.\n",
            )
            mcp_server._write_md(
                tr / "L1" / "derivation_anchor_map.md",
                {"artifact_kind": "l1_derivation_anchor_map", "stage": "L1",
                 "starting_anchors": "eq-12"},
                "# Derivation Anchor Map\n\n## Source Anchors\neq-12\n\n## Missing Steps\nOne omitted algebra step.\n\n## Candidate Starting Points\neq-12 to eq-14.\n",
            )
            mcp_server._write_md(
                tr / "L1" / "contradiction_register.md",
                {"artifact_kind": "l1_contradiction_register", "stage": "L1",
                 "blocking_contradictions": "none"},
                "# Contradiction Register\n\n## Unresolved Source Conflicts\nNone.\n\n## Regime Mismatches\nNone blocking.\n\n## Notation Collisions\nTracked and resolved.\n\n## Blocking Status\nnone\n",
            )

            brief = mcp_server.aitp_get_execution_brief(tmp, "demo-topic")
            self.assertEqual(brief["stage"], "L1")
            self.assertEqual(brief["posture"], "frame")
            self.assertEqual(brief["gate_status"], "ready")
            self.assertEqual(brief["next_allowed_transition"], "L3")
            self.assertEqual(brief["skill"], "skill-frame")


class HookOutputTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_session_start_prints_stage_posture_and_required_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "topics").mkdir()
            mcp_server.aitp_bootstrap_topic(
                str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
            )
            completed = subprocess.run(
                [sys.executable, str(self.REPO_ROOT / "hooks" / "session_start.py")],
                cwd=repo_root, text=True, capture_output=True, check=True,
            )
            self.assertIn("stage: L1", completed.stdout)
            self.assertIn("posture: read", completed.stdout)
            self.assertIn("question_contract.md", completed.stdout)
            self.assertIn("skill-read.md", completed.stdout)

    def test_compact_prints_same_stage_posture_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "topics").mkdir()
            mcp_server.aitp_bootstrap_topic(
                str(repo_root), "demo-topic", "Demo Topic", "What is the bounded question?",
            )
            completed = subprocess.run(
                [sys.executable, str(self.REPO_ROOT / "hooks" / "compact.py")],
                cwd=repo_root, text=True, capture_output=True, check=True,
            )
            self.assertIn("stage: L1", completed.stdout)
            self.assertIn("posture: read", completed.stdout)
            self.assertIn("skill-read.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
