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
from knowledge_hub.l2_compiler import materialize_workspace_knowledge_report
from knowledge_hub.l2_graph import consult_canonical_l2, materialize_canonical_index, seed_l2_demo_direction, stage_l2_insight
from knowledge_hub.l2_staging import stage_negative_result_entry


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
            (self.kernel_root / "canonical" / "physical-pictures" / "physical_picture--tfim-weak-coupling-benchmark-intuition.json").exists()
        )
        self.assertTrue(
            (self.kernel_root / "canonical" / "topic-skill-projections" / "topic_skill_projection--tfim-benchmark-first-route.json").exists()
        )
        self.assertIn("topic_skill_projection", {row["unit_type"] for row in index_rows})
        self.assertIn("physical_picture", {row["unit_type"] for row in index_rows})
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
        self.assertIn("physical_picture:tfim-weak-coupling-benchmark-intuition", expanded_ids | ids)
        self.assertIn("warning_note:tfim-dense-ed-finite-size-limit", expanded_ids | ids)
        self.assertIn("uses_method", payload["expanded_edge_types"])
        self.assertGreaterEqual(payload["traversal_summary"]["max_depth_reached"], 1)

    def test_l1_consultation_exposes_bounded_multi_hop_traversal_paths(self) -> None:
        seed_l2_demo_direction(
            self.kernel_root,
            direction="tfim-benchmark-first",
            updated_by="test-suite",
        )

        payload = consult_canonical_l2(
            self.kernel_root,
            query_text="Benchmark-first validation",
            retrieval_profile="l1_provisional_understanding",
            max_primary_hits=1,
        )

        expanded_ids = {row["id"] for row in payload["expanded_hits"]}
        paths_by_target = {row["target_id"]: row for row in payload["traversal_paths"]}
        warning_path = paths_by_target["warning_note:tfim-dense-ed-finite-size-limit"]
        self.assertIn("warning_note:tfim-dense-ed-finite-size-limit", expanded_ids)
        self.assertEqual(warning_path["path_depth"], 2)
        self.assertEqual(warning_path["path_relations"], ["supports", "warned_by"])
        self.assertEqual(payload["traversal_summary"]["max_depth_reached"], 2)

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

    def test_topic_local_staged_hit_can_win_primary_surface_when_staging_is_included(self) -> None:
        unrelated_unit_path = self.kernel_root / "canonical" / "concepts" / "concept--observer-algebra-carryover.json"
        unrelated_unit_path.parent.mkdir(parents=True, exist_ok=True)
        unrelated_unit_path.write_text(
            """
{
  "id": "concept:observer-algebra-carryover",
  "unit_type": "concept",
  "title": "Observer algebra carryover concept",
  "summary": "Older canonical material about observer algebra bridge structure from an unrelated topic.",
  "maturity": "human_promoted",
  "created_at": "2026-04-14T00:00:00+00:00",
  "updated_at": "2026-04-14T00:00:00+00:00",
  "topic_completion_status": "regression-stable",
  "tags": ["observer-algebra", "bridge", "carryover"],
  "assumptions": [],
  "regime": {
    "domain": "unrelated canonical topic",
    "approximations": [],
    "scale": "bounded",
    "boundary_conditions": [],
    "exclusions": []
  },
  "scope": {
    "applies_to": ["unrelated canonical carryover"],
    "out_of_scope": ["fresh local topic routing"]
  },
  "provenance": {
    "source_ids": ["source:older-topic"],
    "l1_artifacts": [],
    "l3_runs": [],
    "l4_checks": [],
    "citations": []
  },
  "promotion": {
    "route": "L3->L4->L2",
    "review_mode": "human",
    "canonical_layer": "L2",
    "promoted_by": "test-suite",
    "promoted_at": "2026-04-14T00:00:00+00:00",
    "review_status": "accepted",
    "rationale": "Seed unrelated canonical carryover."
  },
  "dependencies": [],
  "related_units": [],
  "payload": {}
}
""".strip()
            + "\n",
            encoding="utf-8",
        )
        materialize_canonical_index(self.kernel_root)
        stage_payload = stage_l2_insight(
            self.kernel_root,
            title="Measurement-induced observer algebra bridge note",
            summary="Fresh local staged note connecting measurement-induced transitions and observer algebras.",
            candidate_unit_type="concept",
            tags=["measurement-induced", "observer-algebra", "bridge"],
            source_refs=["source:measurement-induced-bridge-paper"],
            created_by="test-suite",
            topic_slug="measurement-induced-observer-algebras",
            provenance={
                "source_id": "source:measurement-induced-bridge-paper",
                "source_slug": "measurement-induced-bridge-paper",
                "source_title": "Measurement-induced observer algebra bridge paper",
            },
        )

        payload = consult_canonical_l2(
            self.kernel_root,
            query_text="measurement induced observer algebra bridge",
            retrieval_profile="l1_provisional_understanding",
            include_staging=True,
            topic_slug="measurement-induced-observer-algebras",
            max_primary_hits=1,
        )

        self.assertEqual(payload["primary_hits"][0]["id"], stage_payload["entry_id"])
        self.assertEqual(payload["primary_hits"][0]["trust_surface"], "staging")
        self.assertEqual(payload["primary_hits"][0]["topic_slug"], "measurement-induced-observer-algebras")

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

    def test_materialize_canonical_index_includes_negative_result_units(self) -> None:
        unit_path = self.kernel_root / "canonical" / "negative-results" / "negative_result--tfim-portability-failure.json"
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path.write_text(
            """
{
  "id": "negative_result:tfim-portability-failure",
  "unit_type": "negative_result",
  "title": "TFIM portability failure",
  "summary": "The bounded benchmark did not justify a broader portability claim.",
  "maturity": "validated",
  "created_at": "2026-04-14T00:00:00+00:00",
  "updated_at": "2026-04-14T00:00:00+00:00",
  "topic_completion_status": "promotion-blocked",
  "tags": ["tfim", "negative-result"],
  "assumptions": ["The failed extrapolation is still reusable knowledge."],
  "regime": {
    "domain": "tfim benchmark route",
    "approximations": ["tiny-system exact diagonalization"],
    "scale": "bounded benchmark",
    "boundary_conditions": ["small finite-size run"],
    "exclusions": ["broad portability claim"]
  },
  "scope": {
    "applies_to": ["bounded benchmark critique"],
    "out_of_scope": ["full solver invalidation"]
  },
  "provenance": {
    "source_ids": ["source:demo"],
    "l1_artifacts": ["intake/topics/demo-topic/vault/wiki/source-intake.md"],
    "l3_runs": ["run:demo"],
    "l4_checks": ["check:demo"],
    "citations": ["demo citation"]
  },
  "promotion": {
    "route": "L3->L4->L2",
    "promoted_by": "test-suite",
    "promoted_at": "2026-04-14T00:00:00+00:00",
    "review_status": "accepted",
    "rationale": "Negative results need a canonical home."
  },
  "dependencies": [],
  "related_units": [],
  "payload": {
    "failure_kind": "regime_mismatch",
    "failed_route": "benchmark-first portability extrapolation",
    "next_implication": "Return to a narrower bounded claim."
  }
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        payload = materialize_canonical_index(self.kernel_root)
        index_rows = read_jsonl(self.kernel_root / "canonical" / "index.jsonl")

        self.assertGreaterEqual(payload["row_count"], 1)
        self.assertIn("negative_result", {row["unit_type"] for row in index_rows})
        self.assertIn("negative_result:tfim-portability-failure", {row["id"] for row in index_rows})

    def test_materialize_canonical_index_and_consultation_include_theorem_card_units(self) -> None:
        unit_path = self.kernel_root / "canonical" / "theorem-cards" / "theorem_card--jones-ch4-finite-product.json"
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path.write_text(
            """
{
  "id": "theorem:jones-ch4-finite-product",
  "unit_type": "theorem_card",
  "title": "Jones Chapter 4 finite-product theorem packet",
  "summary": "Bounded theorem packet for the finite-dimensional block-centralizer finite-product result.",
  "maturity": "auto_validated",
  "created_at": "2026-04-14T00:00:00+00:00",
  "updated_at": "2026-04-14T00:00:00+00:00",
  "topic_completion_status": "promotion-ready",
  "tags": ["jones", "theorem", "operator-algebra"],
  "assumptions": ["Finite-dimensional only."],
  "regime": {
    "domain": "finite-dimensional von Neumann algebras",
    "approximations": ["bounded theorem packet"],
    "scale": "bounded formal lane",
    "boundary_conditions": ["fresh public front door"],
    "exclusions": ["whole-book closure"]
  },
  "scope": {
    "applies_to": ["bounded Chapter 4 theorem packet"],
    "out_of_scope": ["full type-I classification"]
  },
  "provenance": {
    "source_ids": ["local_note:jones-von-neumann-algebras-definition-packet"],
    "backend_refs": ["backend:theoretical-physics-knowledge-network"],
    "l1_artifacts": ["topics/fresh-jones/L0/source_index.jsonl"],
    "l3_runs": ["feedback/topics/fresh-jones/runs/run-001/candidate_ledger.jsonl"],
    "l4_checks": ["validation/topics/fresh-jones/runs/run-001/theory-packets/candidate-demo/formal_theory_review.json"],
    "citations": ["chapter-4/multiplicity-and-finite-dimensional-von-neumann-algebras"]
  },
  "promotion": {
    "route": "L3->L4_auto->L2_auto",
    "review_mode": "ai_auto",
    "canonical_layer": "L2_auto",
    "promoted_by": "test-suite",
    "promoted_at": "2026-04-14T00:00:00+00:00",
    "review_status": "accepted",
    "rationale": "Fresh formal theorem packet mirrored into repo-local canonical L2."
  },
  "dependencies": [],
  "related_units": [],
  "payload": {
    "backend_unit_type": "theorem",
    "backend_unit_path": "external/theorems/jones-ch4-finite-product.json"
  }
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        payload = materialize_canonical_index(self.kernel_root)
        index_rows = read_jsonl(self.kernel_root / "canonical" / "index.jsonl")
        consult_payload = consult_canonical_l2(
            self.kernel_root,
            query_text="Jones finite product theorem packet",
            retrieval_profile="l3_candidate_formation",
            max_primary_hits=5,
        )

        ids = {row["id"] for row in consult_payload["primary_hits"]} | {
            row["id"] for row in consult_payload["expanded_hits"]
        }
        self.assertGreaterEqual(payload["row_count"], 1)
        self.assertIn("theorem_card", {row["unit_type"] for row in index_rows})
        self.assertIn("theorem:jones-ch4-finite-product", {row["id"] for row in index_rows})
        self.assertIn("theorem:jones-ch4-finite-product", ids)

    def test_positive_authoritative_rows_and_negative_contradiction_rows_coexist_on_l2_surfaces(self) -> None:
        shutil.rmtree(self.kernel_root / "canonical" / "staging" / "entries", ignore_errors=True)
        (self.kernel_root / "canonical" / "staging" / "entries").mkdir(parents=True, exist_ok=True)

        unit_path = self.kernel_root / "canonical" / "theorem-cards" / "theorem_card--jones-ch4-finite-product.json"
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path.write_text(
            """
{
  "id": "theorem:jones-ch4-finite-product",
  "unit_type": "theorem_card",
  "title": "Jones Chapter 4 finite-product theorem packet",
  "summary": "Bounded theorem packet for the finite-dimensional block-centralizer finite-product result.",
  "maturity": "auto_validated",
  "created_at": "2026-04-14T00:00:00+00:00",
  "updated_at": "2026-04-14T00:00:00+00:00",
  "topic_completion_status": "promotion-ready",
  "tags": ["jones", "theorem", "operator-algebra"],
  "assumptions": ["Finite-dimensional only."],
  "regime": {
    "domain": "finite-dimensional von Neumann algebras",
    "approximations": ["bounded theorem packet"],
    "scale": "bounded formal lane",
    "boundary_conditions": ["fresh public front door"],
    "exclusions": ["whole-book closure"]
  },
  "scope": {
    "applies_to": ["bounded Chapter 4 theorem packet"],
    "out_of_scope": ["full type-I classification"]
  },
  "provenance": {
    "source_ids": ["local_note:jones-von-neumann-algebras-definition-packet"],
    "backend_refs": ["backend:theoretical-physics-knowledge-network"],
    "l1_artifacts": ["topics/fresh-jones/L0/source_index.jsonl"],
    "l3_runs": ["feedback/topics/fresh-jones/runs/run-001/candidate_ledger.jsonl"],
    "l4_checks": ["validation/topics/fresh-jones/runs/run-001/theory-packets/candidate-demo/formal_theory_review.json"],
    "citations": ["chapter-4/multiplicity-and-finite-dimensional-von-neumann-algebras"]
  },
  "promotion": {
    "route": "L3->L4_auto->L2_auto",
    "review_mode": "ai_auto",
    "canonical_layer": "L2_auto",
    "promoted_by": "test-suite",
    "promoted_at": "2026-04-14T00:00:00+00:00",
    "review_status": "accepted",
    "rationale": "Fresh formal theorem packet mirrored into repo-local canonical L2."
  },
  "dependencies": [],
  "related_units": [],
  "payload": {
    "backend_unit_type": "theorem",
    "backend_unit_path": "external/theorems/jones-ch4-finite-product.json"
  }
}
""".strip()
            + "\n",
            encoding="utf-8",
        )

        negative_payload = stage_negative_result_entry(
            self.kernel_root,
            title="Jones finite product theorem classification failure",
            summary="The Jones finite product theorem packet does not justify a full type-I classification claim.",
            failure_kind="scope_overreach",
            staged_by="test-suite",
        )

        materialize_canonical_index(self.kernel_root)
        report_payload = materialize_workspace_knowledge_report(self.kernel_root)
        knowledge_rows = {
            row["knowledge_id"]: row for row in report_payload["payload"]["knowledge_rows"]
        }
        theorem_row = knowledge_rows["theorem:jones-ch4-finite-product"]
        negative_row = knowledge_rows[negative_payload["entry"]["entry_id"]]

        self.assertEqual(theorem_row["authority_level"], "authoritative_canonical")
        self.assertEqual(theorem_row["knowledge_state"], "trusted")
        self.assertIn(
            "canonical/theorem-cards/theorem_card--jones-ch4-finite-product.json",
            theorem_row["provenance_refs"],
        )
        self.assertEqual(negative_row["authority_level"], "non_authoritative_staging")
        self.assertEqual(negative_row["knowledge_state"], "contradiction_watch")
        self.assertTrue(
            any("canonical/staging/entries/" in ref for ref in negative_row["provenance_refs"])
        )
        self.assertGreaterEqual(
            report_payload["payload"]["summary"]["contradiction_row_count"],
            1,
        )

        consult_payload = consult_canonical_l2(
            self.kernel_root,
            query_text="Jones finite product theorem classification failure",
            retrieval_profile="l4_adjudication",
            include_staging=True,
            max_primary_hits=8,
        )
        canonical_ids = {row["id"] for row in consult_payload["primary_hits"]} | {
            row["id"] for row in consult_payload["expanded_hits"]
        }
        staged_ids = {row["entry_id"] for row in consult_payload["staged_hits"]}
        self.assertIn("theorem:jones-ch4-finite-product", canonical_ids)
        self.assertIn(negative_payload["entry"]["entry_id"], staged_ids)


if __name__ == "__main__":
    unittest.main()
