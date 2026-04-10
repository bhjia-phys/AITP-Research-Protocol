from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()


class TheoreticalPhysicsBackendPairingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.backends_root = self.kernel_root / "canonical" / "backends"
        self.schema = json.loads(
            (self.kernel_root / "schemas" / "l2-backend.schema.json").read_text(encoding="utf-8")
        )
        self.validator = Draft202012Validator(self.schema)

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_theoretical_physics_brain_card_conforms_and_is_active(self) -> None:
        payload = self._read_json(self.backends_root / "theoretical-physics-brain.json")
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "human_note_library")
        self.assertEqual(payload["status"], "active")
        self.assertTrue(payload["source_policy"]["allows_auto_canonical_promotion"])
        self.assertIn("claim_card", payload["canonical_targets"])
        self.assertIn("validation_pattern", payload["canonical_targets"])
        self.assertIn("backend:theoretical-physics-knowledge-network", payload["notes"])

    def test_tpkn_card_declares_paired_backend_semantics(self) -> None:
        payload = self._read_json(self.backends_root / "theoretical-physics-knowledge-network.json")
        self.validator.validate(payload)
        self.assertEqual(payload["status"], "active")
        self.assertIn("claim_card", payload["canonical_targets"])
        self.assertIn("workflow", payload["canonical_targets"])
        self.assertIn("validation_pattern", payload["canonical_targets"])
        self.assertIn("backend:theoretical-physics-brain", "\n".join(payload["retrieval_hints"]))

    def test_backend_index_contains_both_theoretical_physics_backends(self) -> None:
        rows = [
            json.loads(line)
            for line in (self.backends_root / "backend_index.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ids = {row["backend_id"] for row in rows}
        self.assertIn("backend:theoretical-physics-brain", ids)
        self.assertIn("backend:theoretical-physics-knowledge-network", ids)

    def test_pairing_note_documents_downstream_l2_relationship(self) -> None:
        note = (self.backends_root / "THEORETICAL_PHYSICS_BACKEND_PAIRING.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("paired downstream implementations", note)
        self.assertIn("downstream L2", note)
        self.assertIn("backend debt", note)

    def test_paired_backend_contract_locks_operator_and_machine_primary_roles(self) -> None:
        contract = (
            self.backends_root / "THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("operator-primary", contract)
        self.assertIn("machine-primary", contract)
        self.assertIn("no silent hierarchy", contract)
        self.assertIn("canonical / compiled / staging", contract)


if __name__ == "__main__":
    unittest.main()
