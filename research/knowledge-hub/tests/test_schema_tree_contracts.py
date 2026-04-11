from __future__ import annotations

import json
from pathlib import Path
import unittest

import jsonschema


class SchemaTreeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kernel_root = Path(__file__).resolve().parents[1]
        cls.repo_root = Path(__file__).resolve().parents[3]

    def test_promotion_or_reject_schema_is_valid_and_mirrored(self) -> None:
        public_path = self.repo_root / "schemas" / "promotion-or-reject.schema.json"
        kernel_path = self.kernel_root / "schemas" / "promotion-or-reject.schema.json"

        self.assertTrue(public_path.exists())
        self.assertTrue(kernel_path.exists())

        public_payload = json.loads(public_path.read_text(encoding="utf-8"))
        kernel_payload = json.loads(kernel_path.read_text(encoding="utf-8"))

        jsonschema.Draft202012Validator.check_schema(public_payload)
        self.assertEqual(public_payload, kernel_payload)
        self.assertIn("follow_up_actions", public_payload["properties"])
        self.assertIn("follow_up_actions", public_payload["required"])

    def test_schema_tree_docs_explain_public_and_runtime_boundaries(self) -> None:
        root_readme_path = self.repo_root / "schemas" / "README.md"
        kernel_readme_path = self.kernel_root / "schemas" / "README.md"
        architecture_path = self.repo_root / "docs" / "architecture.md"

        self.assertTrue(root_readme_path.exists())
        self.assertTrue(kernel_readme_path.exists())

        root_readme = root_readme_path.read_text(encoding="utf-8")
        kernel_readme = kernel_readme_path.read_text(encoding="utf-8")
        architecture_doc = architecture_path.read_text(encoding="utf-8")

        self.assertIn("public protocol schemas", root_readme)
        self.assertIn("mirrored into `research/knowledge-hub/schemas/`", root_readme)
        self.assertIn("runtime-local schemas", kernel_readme)
        self.assertIn("must match the root copy", kernel_readme)
        self.assertIn("public schema tree lives in `schemas/`", architecture_doc)
        self.assertIn(
            "installable runtime mirrors shared schemas in `research/knowledge-hub/schemas/`",
            architecture_doc,
        )


if __name__ == "__main__":
    unittest.main()
