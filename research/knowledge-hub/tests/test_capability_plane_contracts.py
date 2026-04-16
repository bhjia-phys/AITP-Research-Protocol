from __future__ import annotations

import json
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

from knowledge_hub.aitp_service import AITPService


class CapabilityPlaneContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.kernel_root = self.root / "kernel"
        self.repo_root = self.root / "repo"
        self.package_root = Path(__file__).resolve().parents[1]
        self.kernel_root.mkdir(parents=True)
        self.repo_root.mkdir(parents=True)
        (self.kernel_root / "canonical").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "schemas").mkdir(parents=True, exist_ok=True)
        (self.kernel_root / "runtime" / "schemas").mkdir(parents=True, exist_ok=True)
        for schema_path in (self.package_root / "schemas").glob("*.json"):
            shutil.copyfile(schema_path, self.kernel_root / "schemas" / schema_path.name)
        runtime_bundle_schema = self.package_root / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json"
        shutil.copyfile(
            runtime_bundle_schema,
            self.kernel_root / "runtime" / "schemas" / runtime_bundle_schema.name,
        )
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_write_runtime_capability_card_materializes_registry_and_markdown(self) -> None:
        payload = self.service.write_runtime_capability_card(
            capability_kind="server",
            capability_id="server:el",
            title="EL HPC server",
            summary="Remote Slurm host for backend-heavy numerical runs.",
            declaration_source="human_text",
            properties={
                "host_alias": "el",
                "scheduler": "slurm",
                "allowed_workloads": ["first_principles", "code_method"],
            },
            updated_by="test",
        )

        self.assertEqual(payload["card"]["capability_kind"], "server")
        self.assertEqual(payload["card"]["capability_id"], "server:el")
        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertTrue(Path(payload["registry_path"]).exists())

        registry_payload = json.loads(Path(payload["registry_path"]).read_text(encoding="utf-8"))
        ids = {row["capability_id"] for row in registry_payload["cards"]}
        self.assertIn("server:el", ids)

    def test_record_runtime_capability_declaration_preserves_human_text_and_normalizes_card(self) -> None:
        payload = self.service.record_runtime_capability_declaration(
            capability_kind="server",
            declaration_text="EL can run LibRPA/QSGW via slurm and should be used for backend-heavy numerical jobs.",
            capability_id="server:el",
            title="EL HPC server",
            updated_by="test",
        )

        self.assertEqual(payload["card"]["declaration_source"], "natural_language")
        self.assertIn("slurm", payload["card"]["declaration_text"].lower())
        self.assertTrue(Path(payload["json_path"]).exists())
        self.assertTrue(Path(payload["markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()
