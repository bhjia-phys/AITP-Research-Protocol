from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import read_jsonl
from knowledge_hub.l2_graph import consult_canonical_l2, seed_l2_demo_direction, stage_l2_insight


class L2GraphActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name)
        source_kernel = Path(__file__).resolve().parents[1]
        shutil.copytree(source_kernel / "canonical", self.kernel_root / "canonical", dirs_exist_ok=True)
        shutil.copytree(source_kernel / "schemas", self.kernel_root / "schemas", dirs_exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_seed_direction_populates_index_edges_and_unit_files(self) -> None:
        payload = seed_l2_demo_direction(
            self.kernel_root,
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        index_rows = read_jsonl(self.kernel_root / "canonical" / "index.jsonl")
        edge_rows = read_jsonl(self.kernel_root / "canonical" / "edges.jsonl")

        self.assertEqual(payload["direction"], "tfim-benchmark-first")
        self.assertGreaterEqual(payload["unit_count"], 8)
        self.assertGreaterEqual(payload["edge_count"], 8)
        self.assertTrue(index_rows)
        self.assertTrue(edge_rows)
        self.assertTrue(
            (self.kernel_root / "canonical" / "topic-skill-projections" / "topic_skill_projection--tfim-benchmark-first-route.json").exists()
        )
        self.assertIn("topic_skill_projection", {row["unit_type"] for row in index_rows})
        self.assertIn("uses_method", {row["relation"] for row in edge_rows})

    def test_profile_guided_consultation_returns_seeded_hits_and_neighbors(self) -> None:
        seed_l2_demo_direction(
            self.kernel_root,
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = consult_canonical_l2(
            self.kernel_root,
            query_text="TFIM exact diagonalization benchmark workflow",
            retrieval_profile="l3_candidate_formation",
            max_primary_hits=2,
        )

        ids = {row["id"] for row in payload["primary_hits"]}
        expanded_ids = {row["id"] for row in payload["expanded_hits"]}
        self.assertEqual(payload["retrieval_profile"], "l3_candidate_formation")
        self.assertIn("method:tfim-exact-diagonalization-helper", ids)
        self.assertIn("workflow:tfim-benchmark-workflow", expanded_ids | ids)
        self.assertIn("topic_skill_projection:tfim-benchmark-first-route", expanded_ids | ids)
        self.assertIn("warning_note:tfim-dense-ed-finite-size-limit", expanded_ids | ids)
        self.assertIn("uses_method", payload["expanded_edge_types"])

    def test_staging_entry_is_recorded_and_can_be_optionally_retrieved(self) -> None:
        seed_l2_demo_direction(
            self.kernel_root,
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        stage_payload = stage_l2_insight(
            self.kernel_root,
            title="Weak-coupling physical picture for the TFIM benchmark route",
            summary="Use the tiny TFIM benchmark only as weak-coupling intuition for the first route choice, not as a final theory claim.",
            candidate_unit_type="concept",
            tags=["tfim", "physical-picture", "weak-coupling"],
            source_refs=["discussion:demo-session"],
            created_by="test-suite",
            linked_unit_ids=["topic_skill_projection:tfim-benchmark-first-route"],
            contradicts_unit_ids=["claim_card:tfim-benchmark-before-portability-claim"],
            integration_summary="Added a weak-coupling route intuition and marked that it should not be confused with the broader portability claim.",
            )
        consult_payload = consult_canonical_l2(
            self.kernel_root,
            query_text="TFIM weak coupling physical picture",
            retrieval_profile="l1_provisional_understanding",
            include_staging=True,
        )

        staging_rows = read_jsonl(self.kernel_root / "canonical" / "staging" / "staging_index.jsonl")
        staged_ids = {row["entry_id"] for row in consult_payload["staged_hits"]}

        self.assertEqual(stage_payload["status"], "staged")
        self.assertTrue(staging_rows)
        self.assertIn(stage_payload["entry_id"], {row["entry_id"] for row in staging_rows})
        self.assertIn(stage_payload["entry_id"], staged_ids)
        self.assertEqual(stage_payload["linked_unit_ids"], ["topic_skill_projection:tfim-benchmark-first-route"])
        self.assertEqual(stage_payload["contradicts_unit_ids"], ["claim_card:tfim-benchmark-before-portability-claim"])
        self.assertIn("weak-coupling route intuition", stage_payload["integration_summary"])

    def test_negative_result_staging_is_recorded_with_failure_metadata(self) -> None:
        stage_payload = stage_l2_insight(
            self.kernel_root,
            title="TFIM portability claim failed on larger-system extrapolation",
            summary="The bounded benchmark route did not justify the broader portability claim.",
            candidate_unit_type="negative_result",
            tags=["tfim", "negative-result"],
            source_refs=["discussion:demo-session"],
            created_by="test-suite",
            failure_kind="regime_mismatch",
            failed_route="benchmark-first portability extrapolation",
            next_implication="Return to a narrower bounded benchmark claim before widening the route.",
            topic_slug="demo-topic",
        )
        consult_payload = consult_canonical_l2(
            self.kernel_root,
            query_text="TFIM negative result portability extrapolation",
            retrieval_profile="l1_provisional_understanding",
            include_staging=True,
        )

        staged_row = next(row for row in consult_payload["staged_hits"] if row["entry_id"] == stage_payload["entry_id"])
        self.assertEqual(stage_payload["candidate_unit_type"], "negative_result")
        self.assertEqual(stage_payload["failure_kind"], "regime_mismatch")
        self.assertIn("portability extrapolation", stage_payload["failed_route"])
        self.assertIn("narrower bounded benchmark claim", stage_payload["next_implication"])
        self.assertEqual(staged_row["failure_kind"], "regime_mismatch")


if __name__ == "__main__":
    unittest.main()
