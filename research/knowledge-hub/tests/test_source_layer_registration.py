from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def _load_registration_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "source-layer"
        / "scripts"
        / "register_local_note_source.py"
    )
    spec = importlib.util.spec_from_file_location("register_local_note_source_module", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceLayerRegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.knowledge_root = self.root / "kernel"
        self.backend_root = self.root / "external-formal-theory-backend"
        self.note_path = self.backend_root / "notes" / "modular-flow-outline.md"
        self.card_path = self.root / "formal-theory-note-library.json"

        self.note_path.parent.mkdir(parents=True, exist_ok=True)
        self.note_path.write_text(
            "# Modular Flow Outline\n\nThis is a backend-backed formal theory note.\n",
            encoding="utf-8",
        )
        self.card_path.write_text(
            json.dumps({"backend_id": "backend:formal-theory-note-library"}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        self.module = _load_registration_module()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_register_local_note_source_writes_backend_aware_artifacts(self) -> None:
        result = self.module.register_local_note_source(
            knowledge_root=self.knowledge_root,
            topic_slug="demo-topic",
            note_path=self.note_path,
            registered_by="unit-test",
            backend_id="backend:formal-theory-note-library",
            backend_root=str(self.backend_root),
            backend_artifact_kind="formal_theory_note",
            backend_relative_path="notes/modular-flow-outline.md",
            backend_card_path=str(self.card_path),
        )

        layer0_source = json.loads(result["layer0_source_json"].read_text(encoding="utf-8"))
        self.assertEqual(layer0_source["provenance"]["backend_id"], "backend:formal-theory-note-library")
        self.assertEqual(
            layer0_source["provenance"]["backend_root"],
            str(self.backend_root.resolve()),
        )
        self.assertEqual(layer0_source["provenance"]["backend_artifact_kind"], "formal_theory_note")
        self.assertEqual(
            layer0_source["provenance"]["backend_card_path"],
            str(self.card_path.resolve()),
        )
        self.assertEqual(
            layer0_source["locator"]["backend_relative_path"],
            "notes/modular-flow-outline.md",
        )

        intake_source = json.loads(
            (result["intake_projection_root"] / "source.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            intake_source["locator"]["backend_relative_path"],
            "notes/modular-flow-outline.md",
        )

        global_index_rows = [
            json.loads(line)
            for line in (
                self.knowledge_root / "source-layer" / "global_index.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(global_index_rows[0]["backend_id"], "backend:formal-theory-note-library")
        self.assertEqual(global_index_rows[0]["backend_artifact_kind"], "formal_theory_note")
        self.assertEqual(global_index_rows[0]["backend_relative_path"], "notes/modular-flow-outline.md")

        layer0_snapshot = (result["layer0_snapshot"]).read_text(encoding="utf-8")
        intake_snapshot = (result["intake_projection_root"] / "snapshot.md").read_text(encoding="utf-8")
        self.assertIn("## Backend bridge", layer0_snapshot)
        self.assertIn("Backend bridge:", intake_snapshot)


if __name__ == "__main__":
    unittest.main()
