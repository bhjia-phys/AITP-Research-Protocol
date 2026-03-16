from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys

from jsonschema import Draft202012Validator


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()


class L2BackendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.schema = json.loads(
            (self.kernel_root / "schemas" / "l2-backend.schema.json").read_text(encoding="utf-8")
        )
        self.validator = Draft202012Validator(self.schema)

    def test_backend_template_conforms_to_schema(self) -> None:
        payload = json.loads(
            (self.kernel_root / "canonical" / "backends" / "backend.template.json").read_text(encoding="utf-8")
        )
        self.validator.validate(payload)

    def test_formal_theory_example_card_conforms_to_schema(self) -> None:
        payload = json.loads(
            (
                self.kernel_root
                / "canonical"
                / "backends"
                / "examples"
                / "formal-theory-note-library.example.json"
            ).read_text(encoding="utf-8")
        )
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "human_note_library")
        self.assertEqual(payload["source_policy"]["default_source_type"], "local_note")
        self.assertIn("derivation_object", payload["canonical_targets"])
        self.assertEqual(
            payload["l0_registration"]["script"],
            "source-layer/scripts/register_local_note_source.py",
        )

    def test_formal_theory_starter_references_smoke_script(self) -> None:
        starter = (
            self.kernel_root / "canonical" / "backends" / "FORMAL_THEORY_BACKEND_STARTER.md"
        ).read_text(encoding="utf-8")
        smoke_script = self.kernel_root / "runtime" / "scripts" / "run_formal_theory_backend_smoke.sh"
        self.assertTrue(smoke_script.exists())
        self.assertIn("run_formal_theory_backend_smoke.sh", starter)

    def test_toy_model_numeric_example_card_conforms_to_schema(self) -> None:
        payload = json.loads(
            (
                self.kernel_root
                / "canonical"
                / "backends"
                / "examples"
                / "toy-model-numeric-workspace.example.json"
            ).read_text(encoding="utf-8")
        )
        self.validator.validate(payload)
        self.assertEqual(payload["backend_type"], "mixed_local_library")
        self.assertIn("validation_pattern", payload["canonical_targets"])
        self.assertEqual(
            payload["l0_registration"]["script"],
            "source-layer/scripts/register_local_note_source.py",
        )

    def test_toy_model_numeric_starter_references_public_tool_and_smoke_script(self) -> None:
        starter = (
            self.kernel_root / "canonical" / "backends" / "TOY_MODEL_NUMERIC_BACKEND_STARTER.md"
        ).read_text(encoding="utf-8")
        smoke_script = self.kernel_root / "runtime" / "scripts" / "run_toy_model_numeric_backend_smoke.sh"
        tool_path = self.kernel_root / "validation" / "tools" / "tfim_exact_diagonalization.py"
        self.assertTrue(smoke_script.exists())
        self.assertTrue(tool_path.exists())
        self.assertIn("run_toy_model_numeric_backend_smoke.sh", starter)
        self.assertIn("tfim_exact_diagonalization.py", starter)


if __name__ == "__main__":
    unittest.main()
