from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys
from jsonschema import Draft202012Validator


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.l2_graph import read_jsonl
from knowledge_hub.proof_engineering_bootstrap import (
    JONES_PROOF_FRAGMENT_ID,
    JONES_STRATEGY_MEMORY_SEEDS,
    build_jones_codrestrict_proof_fragment,
    materialize_jones_proof_engineering_seed,
)


class ProofEngineeringBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name)
        self.source_kernel = Path(__file__).resolve().parents[1]
        shutil.copytree(self.source_kernel / "canonical", self.kernel_root / "canonical", dirs_exist_ok=True)
        shutil.copytree(self.source_kernel / "schemas", self.kernel_root / "schemas", dirs_exist_ok=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_shipped_proof_fragment_schema_and_index_entry_exist(self) -> None:
        proof_fragment_path = (
            self.source_kernel
            / "canonical"
            / "proof-fragments"
            / "proof_fragment--jones-codrestrict-comp-subtype-construction-recipe.json"
        )
        self.assertTrue(proof_fragment_path.exists())

        proof_fragment = json.loads(proof_fragment_path.read_text(encoding="utf-8"))
        canonical_validator = Draft202012Validator(
            json.loads((self.source_kernel / "canonical" / "canonical-unit.schema.json").read_text(encoding="utf-8"))
        )
        payload_validator = Draft202012Validator(
            json.loads((self.source_kernel / "schemas" / "proof-fragment.schema.json").read_text(encoding="utf-8"))
        )
        canonical_validator.validate(proof_fragment)
        payload_validator.validate(proof_fragment["payload"])
        self.assertEqual(proof_fragment["id"], JONES_PROOF_FRAGMENT_ID)
        self.assertIn("construction_steps", proof_fragment["payload"])
        self.assertIn("common_pitfalls", proof_fragment["payload"])

        index_rows = read_jsonl(self.source_kernel / "canonical" / "index.jsonl")
        self.assertIn(JONES_PROOF_FRAGMENT_ID, {row["id"] for row in index_rows})

    def test_materialize_jones_proof_engineering_seed_writes_rows_and_indexes_proof_fragment(self) -> None:
        payload = materialize_jones_proof_engineering_seed(self.kernel_root, updated_by="test-suite")

        strategy_rows = read_jsonl(Path(payload["strategy_memory_path"]))
        self.assertEqual(len(strategy_rows), len(JONES_STRATEGY_MEMORY_SEEDS))
        self.assertIn("formal_derivation", {row["lane"] for row in strategy_rows})
        strategy_types = {row["strategy_type"] for row in strategy_rows}
        self.assertIn("proof_engineering", strategy_types)
        self.assertIn("api_workaround", strategy_types)
        self.assertIn("failure_pattern", strategy_types)
        self.assertTrue(any("codRestrict" in row["summary"] for row in strategy_rows))
        self.assertTrue(any("goal shape" in row["summary"] or "show" in row["summary"] for row in strategy_rows))

        proof_fragment_path = Path(payload["proof_fragment_path"])
        self.assertTrue(proof_fragment_path.exists())
        proof_fragment = json.loads(proof_fragment_path.read_text(encoding="utf-8"))
        self.assertEqual(proof_fragment["id"], JONES_PROOF_FRAGMENT_ID)
        self.assertEqual(proof_fragment["payload"]["verification_status"], "remotely_validated")

        index_rows = read_jsonl(self.kernel_root / "canonical" / "index.jsonl")
        self.assertIn(JONES_PROOF_FRAGMENT_ID, {row["id"] for row in index_rows})

    def test_build_jones_proof_fragment_matches_new_payload_contract(self) -> None:
        payload = build_jones_codrestrict_proof_fragment(updated_by="test-suite")
        self.assertEqual(payload["unit_type"], "proof_fragment")
        self.assertIn("common_pitfalls", payload["payload"])
        self.assertIn("do_not_apply_when", payload["payload"])
        self.assertGreaterEqual(len(payload["payload"]["construction_steps"]), 3)


if __name__ == "__main__":
    unittest.main()
