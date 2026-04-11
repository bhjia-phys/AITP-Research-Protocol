from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import jsonschema


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from tests_support import copy_kernel_schema_files, make_temp_kernel  # noqa: E402


class Phase6SchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package_root = Path(__file__).resolve().parents[1]
        self.repo_root = Path(__file__).resolve().parents[3]
        self.fixture = make_temp_kernel("aitp-phase6-schema-")
        self.temp_root = self.fixture.temp_root
        self.kernel_root = self.fixture.kernel_root
        copy_kernel_schema_files(
            self.package_root,
            self.kernel_root,
            "decision-point.schema.json",
            "decision-trace.schema.json",
            "session-chronicle.schema.json",
        )

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_phase6_schemas_are_valid_and_mirrored(self) -> None:
        root_names = (
            "decision-point.schema.json",
            "decision-trace.schema.json",
            "session-chronicle.schema.json",
        )
        for name in root_names:
            public_path = self.repo_root / "schemas" / name
            kernel_path = self.package_root / "schemas" / name
            public_payload = json.loads(public_path.read_text(encoding="utf-8"))
            kernel_payload = json.loads(kernel_path.read_text(encoding="utf-8"))
            jsonschema.Draft7Validator.check_schema(public_payload)
            self.assertEqual(public_payload, kernel_payload)

        valid_payload = {
            "id": "dp:demo-route-choice",
            "topic_slug": "demo-topic",
            "phase": "routing",
            "layer_context": {"current_layer": "L3"},
            "question": "Which bounded route should run first?",
            "options": [
                {"label": "small-system", "description": "Close the exact benchmark first."},
                {"label": "larger-system", "description": "Push directly to larger finite-size scans."},
            ],
            "blocking": False,
            "created_at": "2026-03-28T00:00:00+00:00",
        }
        jsonschema.validate(
            instance=valid_payload,
            schema=json.loads((self.repo_root / "schemas" / "decision-point.schema.json").read_text(encoding="utf-8")),
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(
                instance={"id": "dp:bad", "blocking": "not-a-bool"},
                schema=json.loads((self.repo_root / "schemas" / "decision-point.schema.json").read_text(encoding="utf-8")),
            )

    def test_pre_commit_validator_accepts_valid_and_rejects_invalid_phase6_json(self) -> None:
        validator = self.repo_root / "hooks" / "pre-commit-validate-schemas"
        valid_dir = self.temp_root / "decision_points"
        valid_dir.mkdir(parents=True, exist_ok=True)
        valid_path = valid_dir / "dp__demo.json"
        valid_path.write_text(
            json.dumps(
                {
                    "id": "dp:demo-route-choice",
                    "topic_slug": "demo-topic",
                    "phase": "routing",
                    "layer_context": {"current_layer": "L3"},
                    "question": "Which bounded route should run first?",
                    "options": [
                        {"label": "small-system", "description": "Close the exact benchmark first."},
                        {"label": "larger-system", "description": "Push directly to larger finite-size scans."},
                    ],
                    "blocking": False,
                    "created_at": "2026-03-28T00:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        invalid_path = valid_dir / "dp__bad.json"
        invalid_path.write_text(
            json.dumps(
                {
                    "id": "dp:demo-bad",
                    "topic_slug": "demo-topic",
                    "phase": "routing",
                    "layer_context": {"current_layer": "L3"},
                    "question": "Broken decision point",
                    "options": [{"label": "only", "description": "Too few options"}],
                    "blocking": "not-a-bool",
                    "created_at": "2026-03-28T00:00:00+00:00",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        good = subprocess.run([sys.executable, str(validator), str(valid_path)], capture_output=True, text=True)
        bad = subprocess.run([sys.executable, str(validator), str(invalid_path)], capture_output=True, text=True)

        self.assertEqual(good.returncode, 0, msg=good.stderr)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("pre-commit-validate-schemas", bad.stderr)


if __name__ == "__main__":
    unittest.main()
